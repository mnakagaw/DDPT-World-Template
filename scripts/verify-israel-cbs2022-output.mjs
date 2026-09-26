#!/usr/bin/env node
// Check actual diagnostic/planning exports against selected CBS workbook rows.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/israel-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='ISR')throw new Error('Expected Israel project');
if(data.analysis?.population_context)throw new Error('Unreviewed WDI/CBS cross-source population difference configured');
if(data.boundaries?.features?.length!==0)throw new Error('2006 six-shape map silently joined to seven CBS 2022 rows');
const cases=[
  {area:'ISR',indicator:'ISR_CBS22_POP_APPROX',value:9601720,row:4,children:7},
  {area:'ISR:CBS22:DIST:1',indicator:'ISR_CBS22_POP_APPROX',value:1252940,row:5,children:0},
  {area:'ISR:CBS22:DIST:6',indicator:'ISR_CBS22_POP_APPROX',value:1420360,row:64,children:0},
  {area:'ISR:CBS22:AREA:7',indicator:'ISR_CBS22_POP_APPROX',value:481940,row:78,children:0},
  {area:'ISR:CBS22:DIST:1',indicator:'ISR_CBS22_HOUSING_DENSITY_2PLUS_PCT',value:15,row:5,children:0},
  {area:'ISR:CBS22:DIST:5',indicator:'ISR_CBS22_OWNER_OCCUPIED_PCT',value:49.1,row:59,children:0},
  {area:'ISR',indicator:'ISR_CBS22_HOUSEHOLDS_APPROX',value:3053450,row:4,children:7},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function parseCsv(input){
  let rows=[],row=[],cell='',quoted=false;
  for(let i=input.charCodeAt(0)===0xfeff?1:0;i<input.length;i++){
    const ch=input[i];
    if(quoted){if(ch==='"'&&input[i+1]==='"'){cell+='"';i++;}else if(ch==='"')quoted=false;else cell+=ch;}
    else if(ch==='"')quoted=true;else if(ch===','){row.push(cell);cell='';}
    else if(ch==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(x=>x!==''))rows.push(row);row=[];cell='';}
    else cell+=ch;
  }
  if(cell||row.length)rows.push([...row,cell]);
  return rows;
}
const out=path.join(project,'evidence','output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const area=data.territories.find(x=>x.id===item.area);
  if(!area)throw new Error('Missing source area '+item.area);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2022'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2022'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2022'),
    'planning.html':planningHtml(data,item.area,'2022','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2022'),
  };
  const stem=`ISR-${sha(item.area+item.indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Source URL','Source locator'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=(scope)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===item.indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!=='2022')
    throw new Error('CBS source value/period mismatch for '+area.name);
  if(within.length!==item.children)throw new Error('Incomplete or extra CBS comparison rows for '+area.name);
  if(!overall[0][col('Source locator')].includes('Excel row '+item.row+', column '))
    throw new Error('CBS source locator absent for '+area.name);
  if(!overall[0][col('Source URL')].includes('cbs.gov.il'))throw new Error('Official CBS URL absent');
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error('Wrong selected area in '+suffix);
  checks.push({area:area.name,area_id:item.area,indicator:item.indicator,period:'2022',value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'ISR',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['CBS reporting area 7 counts Israeli localities in Judea and Samaria only',
    '2006 six-shape provider reference is not joined to 2022 CBS areas',
    'Only 8 of 454 fields in one of 14 acquired workbook sheets adopted',
    'Sub-district/natural-area and locality cover, legal planning units and actual plans remain unresolved',
    'Whole-table print, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,indicator,value,internal_rows,total_csv_rows})=>({area,indicator,value,internal_rows,total_csv_rows})),null,2));

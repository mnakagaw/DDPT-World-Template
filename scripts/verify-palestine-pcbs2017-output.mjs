#!/usr/bin/env node
// Compare actual candidate exports against representative PCBS Table 2/29 rows.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/palestine-areadata-20260926-pse');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='PSE'||data.country.name!=='State of Palestine')throw new Error('Expected PCBS candidate');
if(data.analysis?.population_context)throw new Error('Unreviewed WDI/PCBS population comparison configured');
if(data.boundaries?.features?.length!==0)throw new Error('2021 reference polygon silently joined to 2017 census');
const pop='PSE_PCBS17_ADJ_POP',hh='PSE_PCBS17_HOUSEHOLDS';
const cases=[
  {area:'PSE',indicator:pop,value:4781248,source:'Table 2',children:2},
  {area:'PSE:PCBS17:REGION:WEST-BANK',indicator:pop,value:2881957,source:'Table 2',children:11},
  {area:'PSE:PCBS17:REGION:GAZA-STRIP',indicator:pop,value:1899291,source:'Table 2',children:5},
  {area:'PSE:PCBS17:GOV:JENIN',indicator:pop,value:314866,source:'Table 2',children:84},
  {area:'PSE:PCBS17:GOV:JERUSALEM',indicator:pop,value:435753,source:'Table 2',children:2},
  {area:'PSE:PCBS17:JERUSALEM:J1',indicator:pop,value:281163,source:'Table 29',children:0},
  {area:'PSE:PCBS17:JERUSALEM:J2',indicator:pop,value:154590,source:'Table 29',children:29},
  {area:'PSE:PCBS17:LOCALITY:401870',indicator:pop,value:2941,source:'Table 29',children:0},
  {area:'PSE:PCBS17:GOV:HEBRON',indicator:pop,value:711223,source:'Table 2',children:115},
  {area:'PSE:PCBS17:LOCALITY:753490',indicator:pop,value:171899,source:'Table 29',children:0},
  {area:'PSE',indicator:hh,value:929221,source:'Table 2',children:2},
  {area:'PSE:PCBS17:GOV:JENIN',indicator:hh,value:65495,source:'Table 2',children:84,observedChildren:0},
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
    'diagnostic.csv':diagnosticCsv(data,item.area,'2017'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2017'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2017'),
    'planning.html':planningHtml(data,item.area,'2017','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2017'),
  };
  const stem=`PSE-${sha(item.area+item.indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Source URL','Source locator'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=(scope)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===item.indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!=='2017')
    throw new Error('PCBS source value/period mismatch for '+area.name);
  if(within.length!==item.children)throw new Error('Incorrect PCBS internal comparison count for '+area.name+': '+within.length);
  if(item.observedChildren!==undefined&&within.filter(row=>row[col('Value')].trim()!=='').length!==item.observedChildren)
    throw new Error('Missing locality household values were filled for '+area.name);
  if(!overall[0][col('Source locator')].includes(item.source))throw new Error('PCBS source locator absent for '+area.name);
  if(!overall[0][col('Source URL')].includes('pcbs.gov.ps'))throw new Error('Official PCBS URL absent');
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error('Wrong selected area in '+suffix);
  checks.push({area:area.name,area_id:item.area,indicator:item.indicator,period:'2017',value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const j1='PSE:PCBS17:JERUSALEM:J1';
if(data.observations.some(x=>x.territory_id===j1&&x.indicator_id===hh))
  throw new Error('Jerusalem J1 household value invented from governorate');
const summary=data.sources.find(x=>x.id==='pse-pcbs2017-updated-final-summary');
if(!summary?.note?.includes('4,781,248'))throw new Error('Updated PCBS edition not documented');
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'PSE',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['Updated 2017 source includes 75,393 post-enumeration estimated people; older and counted editions are separate',
    'Jerusalem J1 is aggregate-only; 29 coded locality rows cover J2, not the whole governorate',
    'Eight locality codes appear in updated Table 29 but not the May 2017 code guide',
    'No 2021 reference polygon is joined to 2017 census rows; current official local geometry unverified',
    '2021-published 2026 projection is not adopted as observed present population',
    'Most source tables, planning documents, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,indicator,value,internal_rows,total_csv_rows})=>({area,indicator,value,internal_rows,total_csv_rows})),null,2));

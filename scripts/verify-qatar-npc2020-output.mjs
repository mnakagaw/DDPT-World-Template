#!/usr/bin/env node
// Verify actual Qatar candidate exports against independently pinned source cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/qatar-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='QAT'||data.boundaries?.features?.length!==0)
  throw new Error('Expected Qatar 2020 census candidate with unjoined reference geometry');
const prefix='QAT_NPC2020_';
const cases=[
  {area:'QAT',indicator:'POP_TOTAL',value:2846118,children:8,table:'1'},
  {area:'QAT',indicator:'AGE_0_14',value:449314,children:8,table:'3',calculated:true},
  {area:'QAT',indicator:'EDU_UNIVERSITY_PLUS',value:766682,children:8,table:'31'},
  {area:'QAT',indicator:'HOUSEHOLDS',value:281136,children:8,table:'7'},
  {area:'QAT',indicator:'OPERATING_ESTABLISHMENTS',value:74366,children:8,table:'149'},
  {area:'QAT:NPC2020:MUNICIPALITY:DOHA',indicator:'POP_TOTAL',value:1186023,children:59,table:'1'},
  {area:'QAT:NPC2020:MUNICIPALITY:DOHA',indicator:'RESIDENTIAL_BUILDINGS_SEWER_NOT_CONNECTED',value:0,children:59,table:'139'},
  {area:'QAT:NPC2020:MUNICIPALITY:AL-RAYYAN',indicator:'BUSINESS_PERSONS_ENGAGED',value:380282,children:10,table:'152'},
  {area:'QAT:NPC2020:MUNICIPALITY:AL-SHAMAL',indicator:'POP_TOTAL',value:16730,children:3,table:'1'},
  {area:'QAT:NPC2020:ZONE:01',indicator:'POP_TOTAL',value:132,children:0,table:'2'},
  {area:'QAT:NPC2020:ZONE:10',indicator:'POP_TOTAL',value:null,children:0,table:'2'},
  {area:'QAT:NPC2020:ZONE:55',indicator:'POP_TOTAL',value:226747,children:0,table:'2'},
  {area:'QAT:NPC2020:ZONE:98',indicator:'POP_TOTAL',value:4,children:0,table:'2'},
  {area:'QAT:NPC2020:ZONE:98',indicator:'EDU_ILLITERATE',value:null,children:0,table:'31'},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function parseCsv(input){
  const rows=[];let row=[],cell='',quoted=false;
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
  const territory=data.territories.find(x=>x.id===item.area);
  if(!territory)throw new Error('Missing territory '+item.area);
  const indicator=prefix+item.indicator,period='2020';
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,period),
    'diagnostic.html':diagnosticHtml(data,item.area,period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,period),
    'planning.html':planningHtml(data,item.area,period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,period),
  };
  const stem=`QAT-${sha(item.area+indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Value provenance','Territory ID'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||overall[0][col('Period')]!==period)
    throw new Error('Wrong overall row/period for '+territory.name+' '+indicator);
  if(item.value===null){
    if(overall[0][col('Value')]!==''||overall[0][col('Status')]==='observed')
      throw new Error('Unreported Qatar zone value was silently filled from parent');
  }else if(Number(overall[0][col('Value')])!==item.value||
            overall[0][col('Status')]!==(item.calculated?'calculated':'observed'))
    throw new Error('NPC value/status mismatch for '+territory.name+' '+indicator);
  if(within.length!==item.children)throw new Error('Wrong internal row count for '+territory.name+' '+indicator+': '+within.length);
  if(item.area==='QAT'&&(within[0]?.[col('Territory ID')]!=='QAT:NPC2020:MUNICIPALITY:DOHA'||
      within.at(-1)?.[col('Territory ID')]!=='QAT:NPC2020:MUNICIPALITY:AL-SHEEHANIYA'))
    throw new Error('National comparison membership/order changed');
  if(item.area==='QAT:NPC2020:MUNICIPALITY:DOHA'&&item.indicator==='POP_TOTAL'){
    const missing=within.filter(row=>['QAT:NPC2020:ZONE:10','QAT:NPC2020:ZONE:11',
       'QAT:NPC2020:ZONE:19','QAT:NPC2020:ZONE:60','QAT:NPC2020:ZONE:62'].includes(row[col('Territory ID')]));
    if(missing.length!==5||missing.some(row=>row[col('Value')]!==''||row[col('Status')]==='observed'))
      throw new Error('The five unreported official Doha zones must remain missing');
  }
  if(item.value!==null&&(!overall[0][col('Source locator')].includes(`Table ${item.table}`)||
      !overall[0][col('Source URL')].includes('npc.qa')))
    throw new Error('NPC source locator/URL missing for '+territory.name);
  if(item.calculated&&item.value!==null&&!overall[0][col('Value provenance')].includes('calculated'))
    throw new Error('Calculated age count was not labelled for '+territory.name);
  if(item.children>0){
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error('Printable internal table missing for '+territory.name+' '+indicator);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(x=>x[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(printed)!==JSON.stringify(expected))
      throw new Error('Printable first/last/full internal rows differ from CSV for '+territory.name+' '+indicator);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(territory.name))throw new Error('Wrong selected territory in '+suffix);
  if(item.area==='QAT:NPC2020:MUNICIPALITY:AL-SHAMAL'){
    const plan=outputs['planning.html'];
    for(const expected of ['Historical Al Shamal Municipality Vision and Development Strategy (December 2017)',
      'Reference materials','Institutional state: unverified','Acquisition: Body acquired'])
      if(!plan.includes(expected))throw new Error('Historical Al Shamal plan scope missing: '+expected);
  }
  checks.push({territory:territory.name,territory_id:item.area,indicator,period,value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const wdi=data.observations.find(x=>x.territory_id==='QAT'&&x.indicator_id==='SP.POP.TOTL'&&x.period==='2020');
if(!wdi||wdi.value===2846118)throw new Error('WDI and NPC census populations were silently harmonized');
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'QAT',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  source_geography:{national:2846118,municipalities:8,listed_zones:92,populated_zones:87,
    unreported_zones:5,official_code_for_zones:true,official_municipality_code_and_polygon_join:false},
  separate_wdi_2020_value:wdi.value,
  limitations:['209-sheet original XLSX mechanically inventoried; 144 numbered table bodies not semantically adopted',
    'Current official municipality and zone polygon editions not acquired or joined',
    'Current municipal plans, budgets, implementation and evaluations unverified',
    'No rendered print/PDF, full 42 scenarios or independent acceptance']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory,indicator,value,internal_rows,total_csv_rows})=>({territory,indicator,value,internal_rows,total_csv_rows})),null,2));

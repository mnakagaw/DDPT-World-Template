#!/usr/bin/env node
// Inspect actual country exports against pinned CSB 2021 census cells and scope.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/kuwait-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='KWT'||data.boundaries?.features?.length!==0)
  throw new Error('Expected unjoined Kuwait 2021 census candidate');
if(data.analysis?.population_context)throw new Error('WDI and census population contexts were merged');
const prefix='KWT_CSB21_';
const cases=[
  {area:'KWT',indicator:'POP_TOTAL',value:4385717,children:6,table:1},
  {area:'KWT',indicator:'POP_NONKUWAITI',value:2897001,children:6,table:1},
  {area:'KWT',indicator:'AGE_0_14',value:859845,children:6,table:2,calculated:true},
  {area:'KWT',indicator:'EDU_10PLUS_ILLITERATE',value:69052,children:6,table:10},
  {area:'KWT',indicator:'LABOUR_15PLUS',value:2570091,children:6,table:22},
  {area:'KWT',indicator:'UNEMPLOYED_15PLUS',value:23992,children:6,table:26},
  {area:'KWT',indicator:'UNEMPLOYMENT_RATE',value:0.93,children:6,table:26,calculated:true},
  {area:'KWT',indicator:'DISABILITY_TOTAL',value:55232,children:6,table:42},
  {area:'KWT:CSB2021:GOV:CAPITAL',indicator:'POP_TOTAL',value:574839,children:33,table:1},
  {area:'KWT:CSB2021:GOV:AL-FARWANIYA',indicator:'POP_TOTAL',value:1109819,children:20,table:1},
  {area:'KWT:CSB2021:GOV:MUBARAK-AL-KABEER',indicator:'UNEMPLOYMENT_RATE',value:1.86,children:13,table:26,calculated:true},
  {area:'KWT:CSB2021:AREA:DASMAN',indicator:'POP_TOTAL',value:1942,children:0,table:52},
  {area:'KWT:CSB2021:AREA:AL-SHARQ',indicator:'POP_NONKUWAITI',value:31952,children:0,table:52},
  {area:'KWT:CSB2021:GEOGRAPHY-NOT-STATED',indicator:'POP_TOTAL',value:4578,children:0,table:1},
  {area:'KWT:CSB2021:GEOGRAPHY-NOT-STATED',indicator:'DISABILITY_TOTAL',value:2,children:0,table:42},
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
  const area=data.territories.find(x=>x.id===item.area);
  if(!area)throw new Error('Missing area '+item.area);
  const indicator=prefix+item.indicator,period='2021';
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,period),
    'diagnostic.html':diagnosticHtml(data,item.area,period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,period),
    'planning.html':planningHtml(data,item.area,period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,period),
  };
  const stem=`KWT-${sha(item.area+indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Value provenance','Territory ID'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!==period)
    throw new Error('CSB source value/period mismatch for '+area.name+' '+indicator);
  if(within.length!==item.children)throw new Error('Wrong internal comparison row count for '+area.name+' '+indicator+': '+within.length);
  if(item.area==='KWT'&&(within[0]?.[col('Territory ID')]!=='KWT:CSB2021:GOV:CAPITAL'||
      within.at(-1)?.[col('Territory ID')]!=='KWT:CSB2021:GOV:MUBARAK-AL-KABEER'))
    throw new Error('National six-governorate comparison order or residual exclusion changed');
  if(!overall[0][col('Source locator')].includes(`Table ${item.table}`)||
     !overall[0][col('Source URL')].includes('census.csb.gov.kw'))
    throw new Error('Official CSB source locator/URL missing for '+area.name);
  if(item.calculated&&!overall[0][col('Value provenance')].includes('calculated'))
    throw new Error('Calculated value was not labelled for '+area.name+' '+indicator);
  if(item.calculated&&within.some(row=>row[col('Status')]==='observed'&&!row[col('Value provenance')].includes('calculated')))
    throw new Error('Calculated comparison rows lost provenance for '+indicator);
  if(item.calculated&&item.children>0&&!outputs['diagnostic.html'].includes('AreaData calculated'))
    throw new Error('Calculated comparison rows shown as source reported in HTML');
  if(item.children>0){
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error('Printable internal table missing for '+area.name+' '+indicator);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(x=>x[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(printed)!==JSON.stringify(expected))
      throw new Error('Printable first/last/full internal rows differ from CSV for '+area.name+' '+indicator);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error('Wrong selected area in '+suffix);
  checks.push({area:area.name,area_id:item.area,indicator,period,value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const wdi=data.observations.find(x=>x.territory_id==='KWT'&&x.indicator_id==='SP.POP.TOTL'&&x.period==='2021');
if(!wdi||wdi.value===4385717)throw new Error('WDI midyear and CSB census series were silently harmonized');
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'KWT',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  source_geography:{national:4385717,six_governorates_sum:4381139,unassigned_residual:4578,
    residual_is_not_a_seventh_governorate:true},
  separate_wdi_2021_value:wdi.value,
  limitations:['Eight selected CSB tables audited, remaining 110 table IDs in the acquired six-category catalog not yet assessed',
    'The 2021 registration-census population scope is distinct from annual population estimates and WDI midyear values',
    'No official current code or boundary polygon joined to the six governorate reporting names',
    'Lawful local planning unit, actual plans, budgets, execution and evaluation unverified',
    'Full-table print, Word/PDF, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,indicator,value,internal_rows,total_csv_rows})=>({area,indicator,value,internal_rows,total_csv_rows})),null,2));

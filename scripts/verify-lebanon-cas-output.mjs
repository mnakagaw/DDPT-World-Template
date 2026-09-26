#!/usr/bin/env node
// Check actual diagnostic/planning exports against selected CAS printed rows.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/lebanon-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='LBN')throw new Error('Expected Lebanon project');
if(data.analysis?.population_context)throw new Error('Unreviewed WDI/CAS population comparison configured');
if(data.boundaries?.features?.length!==0)throw new Error('2017 nine-shape reference silently joined to 2018 survey rows');
if(data.observations.some(x=>x.source_id==='lbn-cas-mics2023-equitable-chance-ch11'))throw new Error('Incomplete-coverage MICS promoted to observations');
const cases=[
  {area:'LBN',indicator:'LBN_CAS18_RESIDENTS',value:4842500,locator:'Table 1.1',children:8},
  {area:'LBN:CAS18:GOV:MOUNT-LEBANON',indicator:'LBN_CAS18_RESIDENTS',value:2032600,locator:'Table 1.1',children:6},
  {area:'LBN:CAS18:GOV:BEIRUT',indicator:'LBN_CAS18_RESIDENTS',value:341700,locator:'Table 1.1',children:0},
  {area:'LBN:CAS18:CAZA:MOUNT-LEBANON:BAABDA',indicator:'LBN_CAS18_RESIDENTS',value:553800,locator:'Table 1.1',children:0},
  {area:'LBN:CAS18:GOV:AKKAR',indicator:'LBN_CAS18_RESIDENTS',value:324000,locator:'Table 1.1',children:0},
  {area:'LBN:CAS18:CAZA:NABATIEH:NABATIEH',indicator:'LBN_CAS18_RESIDENTS',value:180200,locator:'Table 1.1',children:0},
  {area:'LBN:CAS18:GOV:SOUTH-LEBANON',indicator:'LBN_CAS18_HOUSEHOLDS',value:147800,locator:'Table 1.1',children:3},
  {area:'LBN',indicator:'LBN_CAS18_WOMEN',value:2499400,locator:'Excel row 41, column C',children:8},
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
    'diagnostic.csv':diagnosticCsv(data,item.area,'2018'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2018'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2018'),
    'planning.html':planningHtml(data,item.area,'2018','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2018'),
  };
  const stem=`LBN-${sha(item.area+item.indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Source URL','Source locator'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=(scope)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===item.indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!=='2018')
    throw new Error('CAS source value/period mismatch for '+area.name);
  if(within.length!==item.children)throw new Error('Incorrect CAS internal comparison count for '+area.name+': '+within.length);
  if(!overall[0][col('Source locator')].includes(item.locator))throw new Error('CAS source locator absent for '+area.name);
  if(!overall[0][col('Source URL')].includes('cas.gov.lb'))throw new Error('Official CAS URL absent');
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error('Wrong selected area in '+suffix);
  checks.push({area:area.name,area_id:item.area,indicator:item.indicator,period:'2018',value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'LBN',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['LFHLCS is a 2018-19 household survey with mid-2018 estimates, not a census',
    'Residential dwellings only: camps, adjacent gatherings and informal settlements are outside source scope',
    'Two coextensive source caza/governorate pairs are separate types; no additive use',
    '2017 nine-shape reference is not joined to eight CAS survey governorate rows',
    '2023 MICS has five governorates and separate displaced/refugee domains, no adopted national result',
    'Most source tables, legal planning units, plans, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,indicator,value,internal_rows,total_csv_rows})=>({area,indicator,value,internal_rows,total_csv_rows})),null,2));

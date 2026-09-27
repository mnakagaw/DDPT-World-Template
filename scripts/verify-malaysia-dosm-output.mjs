#!/usr/bin/env node
// Check produced exports against the pinned original DOSM CSV cells, not a prior export.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/malaysia-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/MYS_DOSM_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
if(data.country.id!=='MYS'||data.territories.length!==173||
  data.boundaries?.features?.length!==0||audit.adopted_observation_slots!==1282)
  fail('Malaysia source scope changed');

function csvRows(input){
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
function originalRows(content){
  const [header,...body]=content.trim().split(/\r?\n/).map(line=>line.split(','));
  return body.map((cells,i)=>Object.fromEntries([...header.map((h,j)=>[h,cells[j]]),['_row',i+2]]));
}
const raw={};
for(const filename of ['population_malaysia.csv','population_state.csv','population_district.csv',
  'hies_state.csv','hh_access_amenities.csv'])
  raw[filename]=originalRows(await readFile(path.join(project,'raw',filename),'utf8'));
const cases=[
  {id:'MYS',population:'population_malaysia.csv'},
  {id:'MYS:DOSM:STATE:SELANGOR',population:'population_state.csv',state:'Selangor'},
  {id:'MYS:DOSM:DISTRICT:SELANGOR:PETALING',population:'population_district.csv',state:'Selangor',district:'Petaling'},
  {id:'MYS:DOSM:STATE:W-P-KUALA-LUMPUR',population:'population_state.csv',state:'W.P. Kuala Lumpur'},
  {id:'MYS:DOSM:DISTRICT:PAHANG:CAMERON-HIGHLAND',population:'population_district.csv',state:'Pahang',district:'Cameron Highland'},
];
const findSource=(filename,match)=>{
  const hits=raw[filename].filter(row=>Object.entries(match).every(([key,value])=>row[key]===value));
  if(hits.length!==1)fail(`Expected one source row in ${filename}: ${JSON.stringify(match)}; got ${hits.length}`);
  return hits[0];
};
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const test of cases){
  const area=data.territories.find(t=>t.id===test.id);
  if(!area)fail(`Missing source reporting unit ${test.id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,test.id,'2024'),
    'diagnostic.html':diagnosticHtml(data,test.id,'2024'),
    'diagnostic.md':diagnosticMarkdown(data,test.id,'2024'),
    'planning.html':planningHtml(data,test.id,'2024','en'),
    'evidence.csv':evidenceCsv(data,test.id,'2024'),
  };
  const stem=`MYS-${sha(test.id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(out,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL',
    'Source locator','Territory ID','Value provenance'])
    if(col(key)<0)fail(`Missing output CSV column ${key}`);
  const selected=indicator=>rows.filter(row=>row[col('Record scope')]==='overall'&&
    row[col('Indicator ID')]===indicator);
  for(const sex of ['both','male','female']){
    const source=findSource(test.population,{...test.state&&{state:test.state},
      ...test.district&&{district:test.district},date:'2024-01-01',sex,age:'overall',ethnicity:'overall'});
    const indicator=`MYS_DOSM_POP_2024_${sex.toUpperCase()}`;
    const exported=selected(indicator);
    if(exported.length!==1||Number(exported[0][col('Value')])!==Math.round(Number(source.population)*1000)||
       exported[0][col('Status')]!=='calculated'||
       exported[0][col('Value provenance')]!=='calculated'||
       exported[0][col('Territory ID')]!==test.id||
       !exported[0][col('Source URL')].includes('storage.dosm.gov.my/')||
       !exported[0][col('Source locator')].includes(`line ${source._row}`))
      fail(`2024 population output/source mismatch: ${test.id}/${sex}`);
  }
  if(test.population==='population_state.csv'){
    const hies=findSource('hies_state.csv',{state:test.state,date:'2024-01-01'});
    for(const field of ['income_mean','income_median','expenditure_mean','gini','poverty']){
      const exported=selected(`MYS_DOSM_HIES_${field.toUpperCase()}`);
      if(exported.length!==1||Number(exported[0][col('Value')])!==Number(hies[field])||
         exported[0][col('Status')]!=='observed'||
         !exported[0][col('Source locator')].includes(`line ${hies._row}`))
        fail(`2024 HIES state source/output mismatch: ${test.id}/${field}`);
    }
    const amenity=findSource('hh_access_amenities.csv',{state:test.state,
      district:test.state==='W.P. Kuala Lumpur'?test.state:'All Districts',date:'2024-01-01'});
    for(const field of ['piped_water','sanitation','electricity']){
      const exported=selected(`MYS_DOSM_AMENITY_${field.toUpperCase()}`),rawValue=amenity[field];
      if(exported.length!==1||exported[0][col('Status')]!==(rawValue?'observed':'missing')||
         (rawValue?Number(exported[0][col('Value')])!==Number(rawValue):exported[0][col('Value')]!=='')||
         !exported[0][col('Source locator')].includes(`line ${amenity._row}`))
        fail(`2024 amenity source/output mismatch: ${test.id}/${field}`);
    }
  }
  for(const [suffix,content] of Object.entries(outputs)){
    if(content.includes('undefined')||content.includes('NaN'))fail(`Invalid ${suffix}: ${test.id}`);
    if(suffix.endsWith('.html')&&!content.includes(area.name))fail(`Area lost in ${suffix}: ${test.id}`);
  }
  if(test.id==='MYS'){
    const compared=rows.filter(row=>row[col('Record scope')]==='within_area'&&
      row[col('Indicator ID')]==='MYS_DOSM_POP_2024_BOTH');
    if(compared.length!==16)fail(`Expected all 16 state rows, got ${compared.length}`);
    for(const row of compared){
      const stateName=row[col('Territory')];
      const source=findSource('population_state.csv',{state:stateName,date:'2024-01-01',
        sex:'both',age:'overall',ethnicity:'overall'});
      if(Number(row[col('Value')])!==Math.round(Number(source.population)*1000))
        fail(`National comparison differs: ${stateName}`);
      if(!outputs['diagnostic.html'].includes(stateName))
        fail(`National print HTML omits ${stateName}`);
    }
  }
  if(test.state==='W.P. Kuala Lumpur'&&
     (!outputs['planning.html'].includes('Kuala Lumpur Local Plan 2040')||
      !outputs['planning.html'].includes('DBKL Budget 2025')||
      !outputs['planning.html'].includes('2450000000')))
    fail('Kuala Lumpur official plan/budget or evidence export missing');
  checks.push({id:test.id,name:area.name,files:Object.keys(outputs)});
}
// The 2020 Cameron Highlands source row is retained, but no name-only join is allowed.
const old=diagnosticCsv(data,'MYS:DOSM:DISTRICT:PAHANG:CAMERON-HIGHLAND','2020');
const [oldHead,...oldRows]=csvRows(old),idIndex=oldHead.indexOf('Indicator ID'),
  scopeIndex=oldHead.indexOf('Record scope'),statusIndex=oldHead.indexOf('Status');
const oldPop=oldRows.find(row=>row[scopeIndex]==='overall'&&
  row[idIndex]==='MYS_DOSM_POP_2020_BOTH');
if(!oldPop||oldPop[statusIndex]==='observed'||oldPop[statusIndex]==='calculated')
  fail('2020 Cameron Highlands was silently joined to the renamed 2024 area');
const report={dataset_sha256:sha(bytes),checked_cases:checks,
  national_population_comparison_rows:16,
  observed_new:1258,source_blank_amenity_slots:24,
  independent_acceptance:false};
await writeFile(path.join(project,'evidence/MYS_OUTPUT_VERIFICATION.json'),
  JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({checked_cases:checks.length,
  national_population_comparison_rows:16,dataset_sha256:report.dataset_sha256}));

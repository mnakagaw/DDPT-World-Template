#!/usr/bin/env node
// Saves representative generator outputs; browser downloads remain a separate test.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';
import {comparisonSet} from '../scaffold/site/analysis.mjs';

const project=path.resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const datasetBytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(datasetBytes);
const hash=value=>createHash('sha256').update(value).digest('hex');
const datasetHash=hash(datasetBytes);
if(data.country?.id!=='PHL')throw Error('Expected Philippines');
const census='PHL_POPCEN_2024_DOMESTIC';
const regions=data.territories.filter(t=>t.level==='region');
if(regions.length!==18||regions.reduce((s,t)=>s+(data.observations.find(o=>o.territory_id===t.id&&o.indicator_id===census)?.value||0),0)!==112727776)
  throw Error('Regional coverage/reconciliation failed');
if(comparisonSet(data,'PHL').members.length!==18)throw Error('National comparison lacks 18 regions');
if(comparisonSet(data,'PHL:PSGC:0600000000').members.length!==0)throw Error('Incomplete Region VI city comparison was exposed');
const cases=[
  {id:'PHL',stem:'national',expected:112727776,children:18},
  {id:'PHL:PSGC:0600000000',stem:'western-visayas',expected:4861911,children:0},
  {id:'PHL:PSGC:0631000000',stem:'iloilo-city',expected:473728,children:0}
];
const out=path.join(project,'evidence','output-verification',datasetHash.slice(0,12));
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const area=data.territories.find(t=>t.id===item.id);
  const products={
    'diagnostic.csv':diagnosticCsv(data,item.id,'2024'),
    'diagnostic.html':diagnosticHtml(data,item.id,'2024'),
    'planning.html':planningHtml(data,item.id,'2024','en'),
    'evidence.csv':evidenceCsv(data,item.id,'2024')
  };
  const files={};
  for(const [suffix,body] of Object.entries(products)){
    const file=path.join(out,item.stem+'-'+suffix);
    await writeFile(file,body);
    const bytes=await readFile(file);
    if(hash(bytes)!==hash(body))throw Error('Saved generator mismatch: '+file);
    files[suffix]={path:path.relative(project,file).replaceAll('\\','/'),bytes:bytes.length,sha256:hash(bytes)};
  }
  const csv=products['diagnostic.csv'];
  if(!csv.includes(item.id)||!csv.includes(String(item.expected))||!csv.includes('psa.gov.ph'))
    throw Error('Diagnostic CSV identity/source/value mismatch for '+item.id);
  if(!products['diagnostic.html'].includes(area.name)||!products['planning.html'].includes(area.name))
    throw Error('HTML area mismatch for '+item.id);
  if(item.stem==='iloilo-city'&&!products['planning.html'].includes('CDP2023-2028_4-13_Final-Document.pdf'))
    throw Error('Iloilo link absent from planning output');
  const childSet=comparisonSet(data,item.id);
  if(childSet.members.length!==item.children)throw Error('Unexpected comparison members for '+item.id);
  checks.push({territory_id:item.id,expected_population:item.expected,comparison_members:childSet.members.length,
    first_csv_line:csv.split(/\r?\n/)[1]?.slice(0,500),last_csv_line:csv.trimEnd().split(/\r?\n/).at(-1)?.slice(0,500),files});
}
const receipt={status:'partial_saved_generator_output_check',checked_at:new Date().toISOString(),
  dataset_sha256:datasetHash,checks,
  limitations:['Browser download and physical print were not verified.','Current official polygons and complete municipal/city catalogue were not acquired.','Iloilo plan body and approval are unverified; link only.']};
const receiptPath=path.join(project,'evidence','PHL_OUTPUT_VERIFICATION_'+datasetHash.slice(0,12)+'.json');
await writeFile(receiptPath,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({dataset_sha256:datasetHash,receipt:path.relative(project,receiptPath),checks:checks.map(c=>({territory_id:c.territory_id,expected_population:c.expected_population,comparison_members:c.comparison_members}))},null,2));

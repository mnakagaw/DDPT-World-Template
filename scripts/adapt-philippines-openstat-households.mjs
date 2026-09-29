#!/usr/bin/env node
// Adopt 2024 POPCEN household measures only after exact PSGC reconciliation.
import {readFile,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw');
const dataPath=join(project,'data','dashboard.json');
const stem='psa-openstat-popcen-households-2024';
const [metadataBytes,dataBytes,receiptText,dashboardText]=await Promise.all([
  readFile(join(raw,stem+'-metadata.json')),readFile(join(raw,stem+'-data.json')),
  readFile(join(raw,stem+'-receipt.json'),'utf8'),readFile(dataPath,'utf8')
]);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const receipt=JSON.parse(receiptText);
if(sha(metadataBytes)!==receipt.metadata_sha256 || sha(dataBytes)!==receipt.data_sha256)
  throw Error('OpenSTAT raw response changed after receipt');
const metadata=JSON.parse(metadataBytes.toString('utf8').replace(/^\uFEFF/,''));
const response=JSON.parse(dataBytes.toString('utf8').replace(/^\uFEFF/,''));
const dashboard=JSON.parse(dashboardText);
if(dashboard.country?.id!=='PHL' || response.data.length!==548 ||
  metadata.variables?.[0]?.code!=='Geographic Location' ||
  metadata.variables?.[1]?.code!=='Parameter' ||
  JSON.stringify(metadata.variables[1].valueTexts)!==JSON.stringify([
    'Total Population','Household Population','Number of Households','Average Household Size']))
  throw Error('Unexpected OpenSTAT 2024 household table structure');
const byCode=new Map(dashboard.territories.filter(row=>row.official_code).map(row=>[row.official_code,row]));
const popById=new Map(dashboard.observations.filter(row=>row.indicator_id==='PHL_POPCEN_2024_DOMESTIC')
  .map(row=>[row.territory_id,row.value]));
const rowByCode=new Map();
for(const row of response.data){
  if(row.key.length!==2 || !/^\d{10}$/.test(row.key[0]) || !/^[0-3]$/.test(row.key[1]) ||
     row.values.length!==1 || !/^\d+(?:\.\d+)?$/.test(row.values[0]))
    throw Error('Unexpected OpenSTAT 2024 household row');
  const [code,parameter]=row.key;
  if(!rowByCode.has(code))rowByCode.set(code,new Map());
  if(rowByCode.get(code).has(parameter))throw Error('Repeated OpenSTAT code/parameter '+code+'/'+parameter);
  rowByCode.get(code).set(parameter,Number(row.values[0]));
}
if(rowByCode.size!==137 || [...rowByCode.values()].some(rows=>rows.size!==4))
  throw Error('Incomplete OpenSTAT household response');
const mapped=[];
for(const [sourceCode,values] of rowByCode){
  if(sourceCode==='1999900000'){
    const special=dashboard.territories.filter(row=>row.official_code?.startsWith('19999') && row.level==='municipality');
    if(special.length!==8 || special.reduce((total,row)=>total+popById.get(row.id),0)!==values.get('0'))
      throw Error('Special Geographic Area aggregate failed reconciliation');
    continue; // A statistical aggregate, not a provincial or local planning authority.
  }
  const code=sourceCode==='0990100000'?'0990101000':sourceCode;
  const territory=sourceCode==='0000000000'?dashboard.territories.find(row=>row.id==='PHL'):byCode.get(code);
  if(!territory)throw Error('No reviewed PSGC match for OpenSTAT code '+sourceCode);
  const expected=sourceCode==='0000000000'
    ? dashboard.observations.find(row=>row.territory_id==='PHL' && row.indicator_id==='PHL_POPCEN_2024_TOTAL')?.value
    : popById.get(territory.id);
  if(values.get('0')!==expected)throw Error('OpenSTAT population checksum mismatch for '+sourceCode);
  if(sourceCode==='0990100000' && (territory.name!=='City of Isabela' || expected!==151297))
    throw Error('Isabela City explicit crosswalk no longer valid');
  mapped.push({sourceCode,territory,values});
}
if(mapped.length!==136 || mapped.filter(row=>row.territory.level==='region').length!==18)
  throw Error('Unexpected number of household geography joins');
const sourceId='psa-openstat-popcen-households-2024';
const indicators=[
  {id:'PHL_POPCEN_2024_HOUSEHOLD_POP',name:'2024 census household population',theme:'Population',unit:'people',
   definition:'2024 POPCEN household population in private households. It differs from total population and should not be used as a total-persons substitute.',
   source_id:sourceId,aggregation:'none',measurement_method:'source_reported',population:'household population',metadata_status:'ready',parameter_code:'1'},
  {id:'PHL_POPCEN_2024_HOUSEHOLDS',name:'2024 census number of households',theme:'Housing',unit:'households',
   definition:'Number of households reported in PSA 2024 POPCEN OpenSTAT table 019.',
   source_id:sourceId,aggregation:'none',measurement_method:'source_reported',population:'households',metadata_status:'ready',parameter_code:'2'},
  {id:'PHL_POPCEN_2024_AVG_HH_SIZE',name:'2024 census average household size',theme:'Housing',unit:'persons per household',
   definition:'PSA-published average household size rounded to one decimal; it must not be summed or averaged across areas.',
   source_id:sourceId,aggregation:'none',measurement_method:'source_reported',population:'households',metadata_status:'ready',parameter_code:'3'}
];
const indicatorIds=new Set(indicators.map(row=>row.id));
dashboard.indicators=dashboard.indicators.filter(row=>!indicatorIds.has(row.id));
dashboard.indicators.push(...indicators);
dashboard.observations=dashboard.observations.filter(row=>!indicatorIds.has(row.indicator_id));
for(const {sourceCode,territory,values} of mapped){
  for(const indicator of indicators){
    dashboard.observations.push({territory_id:territory.id,indicator_id:indicator.id,
      period:'2024',value:values.get(indicator.parameter_code),status:'observed',
      source_id:sourceId,reference_date:'2024-07-01',
      source_geography_code:sourceCode});
  }
}
dashboard.sources=dashboard.sources.filter(row=>row.id!==sourceId);
dashboard.sources.push({id:sourceId,name:'PSA OpenSTAT 2024 POPCEN household measures',
  publisher:'Philippine Statistics Authority',url:receipt.source_url,
  reference_period:'1 July 2024',status:'ready',retrieved_at:receipt.retrieved_at,
  raw_path:'raw/'+stem+'-data.json',sha256:receipt.data_sha256,bytes:receipt.data_bytes,
  license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
  note:'Original API JSON and metadata retained with SHA-256 receipt. Exact PSGC join for 134 subnational areas; Isabela City table code 0990100000 is explicitly crosswalked to PSGC city 0990101000 after name and 151,297 population check. Special Geographic Area aggregate 1999900000 is withheld as a statistical aggregate, with its eight municipality counts separately reconciled.'});
dashboard.collection.adapters=[...new Set([...dashboard.collection.adapters,'psa-openstat-popcen-households-2024'])];
dashboard.collection.notes=[...new Set([...dashboard.collection.notes,
  'PSA OpenSTAT original JSON adds household population, household count and published household size for 136 targets; the BARMM Special Geographic Area aggregate remains source-only.'])];
await writeFile(dataPath,JSON.stringify(dashboard,null,2)+'\n');
console.log(JSON.stringify({joined_targets:mapped.length,observations_added:mapped.length*3,
  excluded_source_code:'1999900000',sha256:receipt.data_sha256},null,2));

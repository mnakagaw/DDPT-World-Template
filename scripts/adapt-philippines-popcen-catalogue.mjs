#!/usr/bin/env node
// Adopt reviewed 2024 POPCEN local household and urban/density observations.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const dir=join(project,'raw','popcen-catalogue-2024');
const path=join(project,'data','dashboard.json');
const parse=bytes=>JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const [dashboardBytes,receiptBytes]=await Promise.all([readFile(path),readFile(join(dir,'receipt.json'))]);
const dashboard=parse(dashboardBytes),receipt=parse(receiptBytes);
if(dashboard.country?.id!=='PHL'||receipt.tables.length!==24)throw Error('Wrong Philippine dataset or incomplete POPCEN catalogue');
const tables=new Map(receipt.tables.map(table=>[table.id,table]));
const load=async id=>{
  const table=tables.get(id);
  if(!table||table.slices.length!==1)throw Error('Expected one source slice: '+id);
  const slice=table.slices[0];
  const bytes=await readFile(join(dir,slice.file));
  if(sha(bytes)!==slice.sha256)throw Error('Original PSA slice changed: '+id);
  const rows=parse(bytes).data;
  if(rows.length!==slice.rows)throw Error('Original PSA row count changed: '+id);
  return {table,rows,slice};
};
const indexed=(rows,param)=>{
  const result=new Map();
  for(const row of rows){
    if(row.key.length!==2||row.key[1]!==param)continue;
    const code=row.key[0],value=Number(row.values[0]);
    if(!/^\d{10}$/.test(code)||!Number.isFinite(value)||result.has(code))
      throw Error('Invalid or duplicate PSA code/value '+code+'/'+param);
    result.set(code,value);
  }
  return result;
};
const table22=await load('0221A6DLPD0.px');
const table24=await load('0241A6DPUP1.px');
const table21=await load('0211A6DAPG0.px');
const area=indexed(table22.rows,'3'),density=indexed(table22.rows,'6');
const urban=indexed(table24.rows,'1'),urbanPercent=indexed(table24.rows,'2');
const growth=indexed(table21.rows,'7'),growthPopulation=indexed(table21.rows,'3');
const localByCode=new Map();
for(const table of receipt.tables.slice(0,18)){
  const {rows}=await load(table.id);
  const tableRegionCode=rows[0]?.key?.[0];
  if(!/^\d{2}0{8}$/.test(tableRegionCode))throw Error('Regional table lacks opening region code '+table.id);
  for(const row of rows){
    const [code,param]=row.key;
    if(!/^\d{10}$/.test(code)||!['0','1','2'].includes(param))throw Error('Unexpected region row '+table.id);
    const value=Number(row.values[0]);
    if(!Number.isInteger(value)||value<0)throw Error('Invalid regional count '+table.id+'/'+code+'/'+param);
    if(!localByCode.has(code))localByCode.set(code,new Map());
    const byParameter=localByCode.get(code);
    if(!byParameter.has(param))byParameter.set(param,[]);
    byParameter.get(param).push({value,table_id:table.id,table_region_code:tableRegionCode});
  }
}
const chosen=(code,param)=>{
  const options=localByCode.get(code)?.get(param)||[];
  if(!options.length||options.some(option=>option.value!==options[0].value))
    throw Error('Missing or conflicting regional source '+code+'/'+param);
  return options.find(option=>option.table_region_code.slice(0,2)===code.slice(0,2))||options[0];
};
const pop=new Map(dashboard.observations.filter(row=>row.indicator_id==='PHL_POPCEN_2024_DOMESTIC')
  .map(row=>[row.territory_id,row.value]));
const nationalExisting=new Map(dashboard.observations.filter(row=>row.territory_id==='PHL'&&
  ['PHL_POPCEN_2024_HOUSEHOLD_POP','PHL_POPCEN_2024_HOUSEHOLDS'].includes(row.indicator_id))
  .map(row=>[row.indicator_id,row]));
if(nationalExisting.size!==2)throw Error('Earlier verified national household observations missing');
const householdIds=['PHL_POPCEN_2024_HOUSEHOLD_POP','PHL_POPCEN_2024_HOUSEHOLDS'];
for(const indicator of dashboard.indicators){
  if(householdIds.includes(indicator.id)){
    indicator.source_id='psa-openstat-popcen-local-2024';
    indicator.definition=indicator.id===householdIds[0]
      ? '2024 POPCEN household population in private households, published in all 18 PSA regional tables; separate from total population.'
      : 'Number of households in the 2024 POPCEN, published in all 18 PSA regional tables; household counts are not population counts.';
  }
}
const newIndicators=[
  {id:'PHL_POPCEN_2024_URBAN_POP',name:'2024 urban population',theme:'Population',unit:'people',
    definition:'Population classified as urban in PSA 2024 POPCEN Table 024; official urban classification is separate from administrative city status.',
    source_id:'psa-openstat-popcen-urban-2024',aggregation:'none',measurement_method:'source_reported',population:'2024 POPCEN persons in the coded area',metadata_status:'ready'},
  {id:'PHL_POPCEN_2024_PERCENT_URBAN',name:'2024 percent urban',theme:'Population',unit:'percent',
    definition:'PSA-reported urban-population percentage for 2024 POPCEN; published rounding is retained and rates are not averaged.',
    source_id:'psa-openstat-popcen-urban-2024',aggregation:'none',measurement_method:'source_reported',population:'2024 POPCEN persons in the coded area',metadata_status:'ready'},
  {id:'PHL_POPCEN_LAND_AREA_KM2',name:'Land area used for 2024 population density',theme:'Geography',unit:'square kilometers',
    definition:'Land area reported in PSA OpenSTAT density Table 022, mainly using the 2019 LMB masterlist with stated later certifications. It is not a verified 2024 legal polygon area.',
    source_id:'psa-openstat-popcen-density-2024',aggregation:'none',measurement_method:'source_reported',population:'land area',metadata_status:'ready'},
  {id:'PHL_POPCEN_2024_DENSITY',name:'2024 census population density',theme:'Population',unit:'people per square kilometer',
    definition:'PSA-reported 2024 POPCEN persons per square kilometer in density Table 022, using its published land-area method and rounding.',
    source_id:'psa-openstat-popcen-density-2024',aggregation:'none',measurement_method:'source_reported',population:'2024 POPCEN persons in the coded area',metadata_status:'ready'},
  {id:'PHL_POPCEN_2020_2024_ANNUAL_GROWTH',name:'Annual population growth rate, 2020–2024',theme:'Population',unit:'percent per year',
    definition:'PSA-reported annual population growth rate from the 1 May 2020 CPH to the 1 July 2024 POPCEN; 2024 is the end period, and the rate is not averaged across areas.',
    source_id:'psa-openstat-popcen-growth-2024',aggregation:'none',measurement_method:'source_reported',population:'census total population',metadata_status:'ready'}
];
const newIds=new Set(newIndicators.map(row=>row.id));
dashboard.indicators=dashboard.indicators.filter(row=>!newIds.has(row.id));
dashboard.indicators.push(...newIndicators);
dashboard.observations=dashboard.observations.filter(row=>!newIds.has(row.indicator_id)&&!householdIds.includes(row.indicator_id));
dashboard.observations.push(...nationalExisting.values());
const expectedTerritories=dashboard.territories.filter(row=>row.id!=='PHL');
if(expectedTerritories.length!==1742)throw Error('Current PSGC target count changed');
for(const territory of expectedTerritories){
  const code=territory.official_code;
  const officialPopulation=chosen(code,'0');
  if(officialPopulation.value!==pop.get(territory.id))throw Error('Official local total population mismatch '+code);
  const household=chosen(code,'1'),households=chosen(code,'2');
  if(household.value>officialPopulation.value||households.value>household.value)
    throw Error('Invalid household relationship '+code);
  for(const [id,result] of [[householdIds[0],household],[householdIds[1],households]]){
    dashboard.observations.push({territory_id:territory.id,indicator_id:id,period:'2024',
      value:result.value,status:'observed',source_id:'psa-openstat-popcen-local-2024',
      source_table_id:result.table_id,source_geography_code:code,reference_date:'2024-07-01'});
  }
  const urbanCode=code==='0990101000'?'0990100000':code;
  if(code==='0990101000' && pop.get(territory.id)!==151297)throw Error('Isabela City crosswalk checksum changed');
  if(growthPopulation.get(urbanCode)!==officialPopulation.value)
    throw Error('Growth table population crosswalk differs from adopted count '+code);
  const values=[urban.get(urbanCode),urbanPercent.get(urbanCode),area.get(code),density.get(code),growth.get(urbanCode)];
  if(values.some(value=>!Number.isFinite(value))||values[0]<0||values[0]>officialPopulation.value||
    values[1]<0||values[1]>100||values[2]<=0||values[3]<0||values[4]<-100||values[4]>100)
    throw Error('Invalid urban/land/density/growth value '+code);
  for(let index=0;index<newIndicators.length;index++){
    const indicator=newIndicators[index],sourceCode=index<2||index===4?urbanCode:code;
    dashboard.observations.push({territory_id:territory.id,indicator_id:indicator.id,period:'2024',
      value:values[index],status:'observed',source_id:indicator.source_id,
      source_table_id:index<2?'0241A6DPUP1.px':index===4?'0211A6DAPG0.px':'0221A6DLPD0.px',source_geography_code:sourceCode,
      reference_date:'2024-07-01'});
  }
}
for(let index=0;index<newIndicators.length;index++){
  const indicator=newIndicators[index],sourceCode='0000000000';
  const value=[urban.get(sourceCode),urbanPercent.get(sourceCode),area.get(sourceCode),density.get(sourceCode),growth.get(sourceCode)][index];
  if(!Number.isFinite(value))throw Error('Missing national source value '+indicator.id);
  dashboard.observations.push({territory_id:'PHL',indicator_id:indicator.id,period:'2024',value,
    status:'observed',source_id:indicator.source_id,source_table_id:index<2?'0241A6DPUP1.px':index===4?'0211A6DAPG0.px':'0221A6DLPD0.px',
    source_geography_code:sourceCode,reference_date:'2024-07-01'});
}
const localId='psa-openstat-popcen-local-2024';
const sources=[
  {id:localId,name:'PSA OpenSTAT 2024 POPCEN regional household tables',publisher:'Philippine Statistics Authority',
    url:'https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__1A__PO_2024/',reference_period:'1 July 2024',
    raw_path:'raw/popcen-catalogue-2024/receipt.json',sha256:sha(receiptBytes),bytes:receiptBytes.length,
    note:'Eighteen official regional API tables; each observation retains its exact table ID and PSGC code. Identical cross-table repeats are deduplicated by PSGC code. Raw responses, metadata and hashes are listed in the receipt.'},
  ...[['psa-openstat-popcen-density-2024',table22,'Population, land area and density'],
      ['psa-openstat-popcen-urban-2024',table24,'Urban population and percentage'],
      ['psa-openstat-popcen-growth-2024',table21,'Population and annual growth rate']].map(([id,table,name])=>({
    id,name:'PSA OpenSTAT 2024 POPCEN '+name,publisher:'Philippine Statistics Authority',
    url:table.table.source_url,reference_period:'1 July 2024',
    raw_path:'raw/popcen-catalogue-2024/'+table.slice.file,sha256:table.slice.sha256,bytes:table.slice.bytes,
    note:id.includes('urban')?'Table 024; Isabela City source code 0990100000 is explicitly crosswalked to PSGC 0990101000 after population verification. Special Geographic Area aggregate remains source-only.':id.includes('growth')?'Table 021; 2020–2024 annual population growth as reported, with Isabela City source code crosswalk verified against 2024 population. Rates are not averaged.':'Table 022; land area method cites 2019 LMB masterlist and later certifications; source values are not verified legal polygon areas.'
  }))
];
for(const source of sources){source.status='ready';source.retrieved_at=receipt.retrieved_at;source.license='CC BY 4.0 unless otherwise stated (PSA site footer)';}
const replaceIds=new Set(sources.map(row=>row.id));
dashboard.sources=dashboard.sources.filter(row=>!replaceIds.has(row.id));
dashboard.sources.push(...sources);
dashboard.collection.adapters=[...new Set([...dashboard.collection.adapters,'psa-openstat-popcen-catalogue-2024'])];
dashboard.collection.notes=[...new Set([...dashboard.collection.notes.filter(note=>
  !note.startsWith('PSA OpenSTAT original JSON adds household population, household count and published household size for 136 targets')),
  'All 24 PSA 2024 POPCEN OpenSTAT catalogue tables are archived with metadata and SHA receipts. Regional table household population and household counts now cover all 1,742 PSGC subnational targets. Urbanization, density and 2020–2024 population growth are distinct source-reported indicators; no boundary polygons are inferred.'])];
for(const gap of dashboard.gaps){
  if(gap.category==='subnational_statistics'){
    gap.status='partial';
    gap.detail='2024 POPCEN total population, household population and household counts cover all 1,742 registered subnational areas; urban population, percent urban, reported land area, density and 2020–2024 annual growth also cover these areas. Other local thematic tables remain partly collected or unjoined.';
    gap.next_action='Audit and adopt additional official local themes by code, period, method and completeness; keep source-only fields and non-comparable geography explicit.';
  }
}
await writeFile(path,JSON.stringify(dashboard,null,2)+'\n');
console.log(JSON.stringify({territories:expectedTerritories.length,indicators_added:newIndicators.length,
  household_observations:expectedTerritories.length*2+2,other_observations:(expectedTerritories.length+1)*5,
  total_observations:dashboard.observations.length},null,2));

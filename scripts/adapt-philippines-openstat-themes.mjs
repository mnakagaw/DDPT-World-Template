#!/usr/bin/env node
// Adopt source-defined thematic observations only at reviewed matching geography.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw');
const dataPath=join(project,'data','dashboard.json');
const dashboard=JSON.parse(await readFile(dataPath,'utf8'));
if(dashboard.country?.id!=='PHL')throw Error('Expected PHL country edition');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const load=async id=>{
  const stem='psa-openstat-'+id;
  const [metadataBytes,dataBytes,receiptText]=await Promise.all([
    readFile(join(raw,stem+'-metadata.json')),readFile(join(raw,stem+'-data.json')),
    readFile(join(raw,stem+'-receipt.json'),'utf8')
  ]);
  const receipt=JSON.parse(receiptText);
  if(sha(metadataBytes)!==receipt.metadata_sha256 || sha(dataBytes)!==receipt.data_sha256)
    throw Error('OpenSTAT receipt mismatch: '+id);
  return {metadata:JSON.parse(metadataBytes.toString('utf8').replace(/^\uFEFF/,'')),
    response:JSON.parse(dataBytes.toString('utf8').replace(/^\uFEFF/,'')),receipt,stem};
};
const regionCodes=['1300000000','1400000000','0100000000','0200000000','0300000000',
  '0400000000','1700000000','0500000000','0600000000','1800000000',
  '0700000000','0800000000','0900000000','1000000000','1100000000',
  '1200000000','1600000000','1900000000'];
const regionLabels=['National Capital Region','Cordillera Administrative Region','Region I','Region II',
  'Region III','Region IV-A','MIMAROPA Region','Region V','Region VI','Negros Island Region',
  'Region VII','Region VIII','Region IX','Region X','Region XI','Region XII','Region XIII',
  'Bangsamoro Autonomous Region'];
const expectedGeoId=new Map(regionCodes.map(code=>[code,'PHL:PSGC:'+code]));
if(regionCodes.some(code=>!dashboard.territories.some(row=>row.id===expectedGeoId.get(code))))
  throw Error('Current 18-region PSGC register is absent');
const mapGeos=(metadata,variableName,includeOther=false)=>{
  const variable=metadata.variables.find(row=>row.code===variableName);
  if(!variable || variable.values.length<(includeOther?19:19) ||
     !variable.valueTexts[0].toUpperCase().startsWith('PHILIPPINES'))
    throw Error('Unexpected OpenSTAT regional geography metadata');
  const map=new Map([[variable.values[0],'PHL']]);
  for(let i=0;i<18;i++){
    const label=variable.valueTexts[i+1].replace(/^\.\./,'');
    const expected=regionLabels[i];
    const boundary=label.slice(expected.length);
    if(!label.startsWith(expected) ||
       (expected.startsWith('Region ') && boundary && !/^[\s(]/.test(boundary)))
      throw Error('OpenSTAT regional label/order mismatch: '+label+' expected '+expected);
    map.set(variable.values[i+1],expectedGeoId.get(regionCodes[i]));
  }
  return map;
};
const code=(metadata,variableName,label)=>{
  const variable=metadata.variables.find(row=>row.code===variableName);
  const index=variable?.valueTexts.indexOf(label)??-1;
  if(index<0)throw Error('OpenSTAT dimension value missing: '+variableName+' '+label);
  return variable.values[index];
};
const observed=(territory_id,indicator_id,period,value,source_id)=>({
  territory_id,indicator_id,period,value,status:'observed',source_id
});
const indicators=[];const observations=[];const sources=[];
const source=(id,label,loaded,note)=>({id,name:label,publisher:'Philippine Statistics Authority',
  url:loaded.receipt.source_url,reference_period:label.includes('2025')?'2025':'2024',
  status:'ready',retrieved_at:loaded.receipt.retrieved_at,
  raw_path:'raw/'+loaded.stem+'-data.json',sha256:loaded.receipt.data_sha256,
  bytes:loaded.receipt.data_bytes,license:'CC BY 4.0 unless otherwise stated (PSA site footer)',note});

const edu=await load('sdg-education-completion');
const eduGeo=mapGeos(edu.metadata,'Geolocation');
const edu2024=code(edu.metadata,'Year','2024');
const both=code(edu.metadata,'Sex','Both Sexes');
const eduLevels=[
  {label:'Elementary',id:'PHL_EDU_COMPLETION_ELEMENTARY_2024',name:'Elementary completion rate, both sexes'},
  {label:'Secondary (Junior High School)',id:'PHL_EDU_COMPLETION_JHS_2024',name:'Junior high school completion rate, both sexes'},
  {label:'Secondary (Senior High School)  4/',id:'PHL_EDU_COMPLETION_SHS_2024',name:'Senior high school completion rate, both sexes'}
];
const eduLevelByCode=new Map(eduLevels.map(row=>[code(edu.metadata,'Level of Education',row.label),row]));
for(const level of eduLevels)indicators.push({id:level.id,name:level.name,theme:'Education',unit:'percent',
  definition:'PSA OpenSTAT SDG 4.1.2, '+level.label+' completion rate for both sexes, 2024; reconstructed cohort method. The 2024 regional series uses the new grouping of provinces.',
  source_id:'psa-openstat-sdg-education-2024',aggregation:'none',measurement_method:'source_reported',
  population:'school cohort',metadata_status:'ready'});
for(const row of edu.response.data){
  if(row.key[4]!==edu2024 || row.key[3]!==both)continue;
  const territory=eduGeo.get(row.key[1]),level=eduLevelByCode.get(row.key[2]);
  if(!territory || !level || !/^\d+(?:\.\d+)?$/.test(row.values[0]))
    throw Error('Incomplete 2024 regional education row');
  observations.push(observed(territory,level.id,'2024',Number(row.values[0]),'psa-openstat-sdg-education-2024'));
}
if(observations.length!==57)throw Error('2024 education matrix is incomplete');
sources.push(source('psa-openstat-sdg-education-2024','PSA/DepEd 2024 SDG education completion rates',edu,
  'Original API metadata/JSON retained. 2024 footnote states the new group of provinces; all 18 regional values and the national value are published. Both sexes only adopted for three distinct school levels. 2025 cells are unpublished.'));

const health=await load('sdg-under-five-mortality');
const healthGeo=mapGeos(health.metadata,'Geolocation',true);
const health2025=code(health.metadata,'Year','2025');
const healthId='PHL_NDHS_UNDER5_MORTALITY_2025';
indicators.push({id:healthId,name:'Under-five mortality, 2025 NDHS',theme:'Health',
  unit:'deaths per 1,000 live births',
  definition:'Probability of death before age five per 1,000 live births as published from the 2025 National Demographic and Health Survey; retrospective pregnancy histories cover the ten years preceding the survey.',
  source_id:'psa-openstat-ndhs-u5m-2025',aggregation:'none',measurement_method:'survey_reported',
  population:'live births in retrospective survey histories',metadata_status:'ready'});
for(const row of health.response.data){
  const territory=healthGeo.get(row.key[0]);
  if(row.key[1]!==health2025 || !territory)continue;
  if(!/^\d+(?:\.\d+)?$/.test(row.values[0]))throw Error('2025 NDHS regional value absent: '+territory);
  observations.push(observed(territory,healthId,'2025',Number(row.values[0]),'psa-openstat-ndhs-u5m-2025'));
}
if(observations.filter(row=>row.indicator_id===healthId).length!==19)
  throw Error('2025 NDHS regional matrix is incomplete');
sources.push(source('psa-openstat-ndhs-u5m-2025','PSA 2025 NDHS under-five mortality',health,
  'Original API metadata/JSON retained. All 18 regional values and the national value published. The 2024 column is unavailable. 2025 NDHS regional releases explain the retrospective-history method.'));

const grdp=await load('grdp-2025');
const grdpGeo=grdp.metadata.variables.find(row=>row.code==='Region');
if(grdpGeo?.values.length!==19 || grdpGeo.values[18]!=='0000000000')
  throw Error('2025 GRDP geography is not 18 regions plus nation');
const grdp2025=code(grdp.metadata,'Year','2025');
const valuations=[
  {label:'At Current Prices',id:'PHL_GRDP_2025_CURRENT',name:'2025 regional GDP, current prices'},
  {label:'At Constant 2018 Prices',id:'PHL_GRDP_2025_CONSTANT2018',name:'2025 regional GDP, constant 2018 prices'}
];
const valuationByCode=new Map(valuations.map(row=>[code(grdp.metadata,'Type of Valuation',row.label),row]));
for(const val of valuations)indicators.push({id:val.id,name:val.name,theme:'Economy',
  unit:'thousand Philippine pesos',
  definition:'PSA 2025 Gross Regional Domestic Product, '+val.label.toLowerCase()+'. The 2023–2025 series includes Sulu in Zamboanga Peninsula and NIR as a distinct region. Current and constant-price values are separate measures.',
  source_id:'psa-openstat-grdp-2025',aggregation:'none',measurement_method:'source_reported',
  population:'regional economy',metadata_status:'ready'});
const grdpByValuation=new Map(valuations.map(row=>[row.id,[]]));
for(const row of grdp.response.data){
  const territory=row.key[0]==='0000000000'?'PHL':expectedGeoId.get(row.key[0]);
  const valuation=valuationByCode.get(row.key[1]);
  if(!territory || !valuation || row.key[2]!==grdp2025 || !/^\d+$/.test(row.values[0]))
    throw Error('2025 GRDP row failed geography/unit review');
  const value=Number(row.values[0]);
  observations.push(observed(territory,valuation.id,'2025',value,'psa-openstat-grdp-2025'));
  grdpByValuation.get(valuation.id).push({territory,value});
}
for(const [id,rows] of grdpByValuation){
  if(rows.length!==19)throw Error('2025 GRDP region coverage incomplete: '+id);
  const total=rows.find(row=>row.territory==='PHL').value;
  const sub=rows.filter(row=>row.territory!=='PHL').reduce((sum,row)=>sum+row.value,0);
  if(Math.abs(total-sub)>1)throw Error('2025 GRDP regional total mismatch: '+id);
}
sources.push(source('psa-openstat-grdp-2025','PSA 2025 Gross Regional Domestic Product',grdp,
  'Original API metadata/JSON retained. 18 regional observations and national published values for each valuation reconcile within one thousand pesos of rounding. Unit follows the official Regional Accounts publication: thousand Philippine pesos.'));

const water=await load('sdg-basic-drinking-water');
const waterGeo=mapGeos(water.metadata,'Geolocation');
const water2024=code(water.metadata,'Year','2024 p');
const waterRows=water.response.data.filter(row=>row.key[1]===water2024);
const waterNational=waterRows.find(row=>waterGeo.get(row.key[0])==='PHL');
const waterNir=waterRows.find(row=>waterGeo.get(row.key[0])===expectedGeoId.get('1800000000'));
if(waterRows.length!==19 || waterNational?.values[0]!=='97.5' || waterNir?.values[0]!=='..')
  throw Error('2024 provisional drinking-water source availability changed');
const waterId='PHL_BASIC_DRINKING_WATER_FAMILIES_2024P';
indicators.push({id:waterId,name:'Families with basic drinking water, provisional 2024',theme:'Water',unit:'percent',
  definition:'PSA OpenSTAT SDG 6.1.1.p1 provisional 2024 proportion of families with basic drinking-water services. Regional values are withheld pending NIR boundary and source-definition reconciliation.',
  source_id:'psa-openstat-water-2024p',aggregation:'none',measurement_method:'source_reported',
  population:'families',metadata_status:'partial'});
observations.push(observed('PHL',waterId,'2024',97.5,'psa-openstat-water-2024p'));
sources.push(source('psa-openstat-water-2024p','PSA provisional 2024 basic drinking-water access',water,
  'Original API metadata/JSON retained. National 97.5 percent adopted. NIR 2024 p is explicitly unpublished; 17 other regional cells are withheld until post-NIR coverage is confirmed. 2025 cells are unpublished.'));

const newIds=new Set(indicators.map(row=>row.id));
const sourceIds=new Set(sources.map(row=>row.id));
dashboard.indicators=dashboard.indicators.filter(row=>!newIds.has(row.id));
dashboard.indicators.push(...indicators);
dashboard.observations=dashboard.observations.filter(row=>!newIds.has(row.indicator_id));
dashboard.observations.push(...observations);
dashboard.sources=dashboard.sources.filter(row=>!sourceIds.has(row.id));
dashboard.sources.push(...sources);
dashboard.collection.adapters=[...new Set([...dashboard.collection.adapters,'psa-openstat-2024-2025-themes'])];
dashboard.collection.notes=[...new Set([...dashboard.collection.notes,
  'Original OpenSTAT API values add complete 18-region 2024 school-completion rates, 2025 under-five mortality, and 2025 GRDP. Provisional drinking-water access is national only because NIR is blank.'])];
await writeFile(dataPath,JSON.stringify(dashboard,null,2)+'\n');
console.log(JSON.stringify({indicators:indicators.length,observations:observations.length,
  education:57,health:19,grdp:38,water_national:1},null,2));

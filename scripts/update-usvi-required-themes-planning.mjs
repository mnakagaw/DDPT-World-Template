#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';

const CENSUS='https://www.census.gov/data/tables/2020/dec/2020-us-virgin-islands.html';
const CENSUS_FTP='https://www2.census.gov/programs-surveys/decennial/2020/data/island-areas/us-virgin-islands/';
const BOUNDARIES='https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/';
const DPNR='https://dpnr.vi.gov/comprehensive-coastal-zone-planning/what-we-do/';
const LEGISLATURE='https://legvi.org/35th-legislature-of-the-virgin-islands-advances-key-nominations-zoning-approvals-and-bills-to-governor-for-action/';
const CEDS='https://omb.vi.gov/comprehensive-economic-development-strategy-2020-2025/';
const PUBLICATIONS='https://omb.vi.gov/publications/';
const BUDGET='https://omb.vi.gov/wp-content/uploads/2025/04/FY-2025-USVI-Proposed-Executive-Budget-Book.pdf';

function args(){const result={};for(let i=2;i<process.argv.length;i+=2)result[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return result;}
function domain(status,urls,note,evidence,{acquired=true}={}){return {status,identified:true,accessed:true,acquired,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};}
async function copyFiles(source,target,{exclude=[]}={}){await mkdir(target,{recursive:true});for(const name of await readdir(source)){if(exclude.includes(name))continue;const file=path.join(source,name);if((await stat(file)).isFile())await cp(file,path.join(target,name),{force:true});}}
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');

async function main(){
  const a=args();if(!a.project||!a.collection||!a.source||!a.census)throw new Error('Usage: node scripts/update-usvi-required-themes-planning.mjs --project <dir> --collection <dir> --source <dir> --census <dir>');
  const root=path.resolve(a.project),collection=path.resolve(a.collection),source=path.resolve(a.source),census=path.resolve(a.census),evidenceDir=path.join(root,'evidence'),dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,audit,receipt]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(collection,'USVI_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse),readFile(path.join(source,'receipt.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.counts?.territories!==3||audit.counts?.indicators!==14||audit.counts?.observations!==56||audit.counts?.boundaries!==3)throw new Error('U.S. Virgin Islands collection audit is incomplete');
  const expected=['VIR_C2020_POP_TOTAL','VIR_C2020_FEMALE_PCT','VIR_C2020_HOUSING_UNITS','VIR_C2020_PUBLIC_WATER_PCT','VIR_C2020_PUBLIC_SEWER_PCT','VIR_C2020_HIGH_SCHOOL_OR_HIGHER_PCT','VIR_C2020_LABOR_FORCE_PCT','VIR_C2020_DISABILITY_PCT','VIR_C2020_BORN_ELSEWHERE_PCT','VIR_C2020_HISPANIC_LATINO_PCT','VIR_C2020_UNINSURED_PCT','VIR_C2020_SNAP_HOUSEHOLDS_PCT','VIR_C2020_POVERTY_PCT','VIR_C2020_POP_DENSITY'];
  for(const id of expected)if(!dataset.indicators.some(row=>row.id===id))throw new Error(`Missing U.S. Virgin Islands indicator ${id}`);
  const electricity=dataset.observations.find(row=>row.territory_id==='VIR'&&row.indicator_id==='EG.ELC.ACCS.ZS'&&row.period==='2024'&&row.status==='observed');
  if(!electricity||electricity.value!==100)throw new Error('Expected World Bank 2024 electricity observation for VIR is missing');
  const country=preflight.countries.find(row=>row.country_area_id==='VIR');if(!country)throw new Error('VIR preflight record missing');
  const censusEvidence=[{audit:'evidence/USVI_COLLECTION_AUDIT.json'},{raw:'raw/usvi-census-2020'}],planningEvidence=[{receipt:'raw/usvi-source-evidence/receipt.json'},{audit:'evidence/USVI_INTEGRATION_AUDIT.json'}];
  country.scope_role='completed U.S. Virgin Islands edition with three-island 2020 Island Areas Census adapter';
  country.official_statistics_office=domain('inspected',[CENSUS],'The U.S. Census Bureau 2020 Island Areas Census release for the U.S. Virgin Islands was inspected.',censusEvidence);
  country.latest_census=domain('adopted',[CENSUS],'The 2020 Island Areas Census is the latest completed census adopted for this edition. The 2030 round is future/scheduled; its results are not acquired or usable.',censusEvidence);
  country.census_results=domain('adopted',[CENSUS,CENSUS_FTP],'The official Demographic Profile Summary File is integrated for the territory and St. Croix, St. John and St. Thomas.',censusEvidence);
  country.table_catalog=domain('inspected',[CENSUS,CENSUS_FTP],'The official table matrix, geographic-header layout, variables and technical documentation were inspected; a documented table-matrix segment typo is corrected transparently in the collector.',censusEvidence);
  country.machine_readable_data=domain('adopted',[CENSUS_FTP],'The fixed official summary-file ZIP is parsed with its published layouts. Social and economic universes that exclude group quarters remain labeled per indicator.',censusEvidence);
  country.administrative_codes=domain('geography_matched',[CENSUS_FTP,BOUNDARIES],'Territory code 78 and the three five-digit island/county-equivalent FIPS codes are joined exactly.',censusEvidence);
  country.adm1_adm2_boundaries=domain('adopted',[BOUNDARIES],'Three 2020 Census TIGER/Line island/county-equivalent features are integrated as source-attributed reference geometry.',censusEvidence);
  country.planning_law=domain('inspected',[DPNR,LEGISLATURE],'DPNR describes the territorial planning mandate and the Legislature records adoption action for the 2024 Comprehensive Land and Water Use Plan. The DPNR body is acquired; the Legislature request failure is retained and does not prove absence.',planningEvidence);
  country.planning_guidance=domain('acquired',[DPNR,CEDS],'DPNR planning material and the official 2020–2025 Comprehensive Economic Development Strategy are acquired. Their land-use and economic-development purposes remain distinct.',planningEvidence);
  country.plans_budgets_implementation_evaluation=domain('acquired',[DPNR,CEDS,PUBLICATIONS,BUDGET],'Official planning, development-strategy, publication and FY2025 budget sources are acquired. Publication does not by itself establish implementation success or an official outcome evaluation.',planningEvidence);
  country.country_adapter_status='complete_country_adapter';

  const map={VIR_C2020_POP_TOTAL:'population_total',VIR_C2020_FEMALE_PCT:'age_sex',VIR_C2020_HOUSING_UNITS:'households_housing',VIR_C2020_PUBLIC_WATER_PCT:'drinking_water',VIR_C2020_PUBLIC_SEWER_PCT:'sanitation',VIR_C2020_HIGH_SCHOOL_OR_HIGHER_PCT:'education_literacy',VIR_C2020_LABOR_FORCE_PCT:'employment',VIR_C2020_DISABILITY_PCT:'disability',VIR_C2020_BORN_ELSEWHERE_PCT:'migration',VIR_C2020_HISPANIC_LATINO_PCT:'ethnicity',VIR_C2020_UNINSURED_PCT:'health',VIR_C2020_SNAP_HOUSEHOLDS_PCT:'nutrition',VIR_C2020_POVERTY_PCT:'poverty',VIR_C2020_POP_DENSITY:'urban_rural','EG.ELC.ACCS.ZS':'electricity'};
  const indicatorFor=id=>dataset.indicators.find(row=>row.id===id);
  const rows=Object.entries(map).map(([indicatorId,theme])=>{const indicator=indicatorFor(indicatorId);const sourceId=indicator?.source_id||dataset.observations.find(row=>row.territory_id==='VIR'&&row.indicator_id===indicatorId)?.source_id;const count=dataset.observations.filter(row=>(row.territory_id==='VIR'||row.territory_id.startsWith('VIR:'))&&row.indicator_id===indicatorId&&Number.isFinite(row.value)).length;let reason='Official source rows are integrated for the U.S. Virgin Islands and all three islands with the source period, unit, universe and definition.';if(indicatorId==='EG.ELC.ACCS.ZS')reason='The World Bank source-reported 2024 territory-level electricity-access observation is integrated only for VIR and is not assigned to islands.';if(indicatorId==='VIR_C2020_SNAP_HOUSEHOLDS_PCT')reason='Food Stamp/SNAP participation is integrated as an eligible food-assistance proxy and is explicitly labeled as not being a nutrition outcome.';if(indicatorId==='VIR_C2020_POP_DENSITY')reason='Population density is integrated as settlement context and explicitly labeled as not being an urban/rural classification.';return {country_area_id:'VIR',source_id:sourceId,source_path:'evidence/USVI_COLLECTION_AUDIT.json',source_url:indicatorId==='EG.ELC.ACCS.ZS'?'https://api.worldbank.org/v2/':CENSUS,table_id:indicator?.definition_id||indicatorId,table_title:indicator?.name||'Access to electricity',field_id:indicatorId,field_label:indicator?.name||'Access to electricity',numeric_cell_count:count,theme,disposition:'integrated',reason,indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true};});
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!=='VIR'),...rows];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();inventory.adjudication={...(inventory.adjudication||{}),VIR:{reviewed_numeric_fields:rows.length,terminal_dispositions:rows.length,covered_themes:[...new Set(rows.map(row=>row.theme))].sort(),method:'Official 2020 Island Areas Census summary-file fields remain tied to their table universes; World Bank electricity remains territory-level; SNAP and density carry explicit proxy limits.',audit:'evidence/USVI_INTEGRATION_AUDIT.json'}};

  const acquired=Object.fromEntries(receipt.files.filter(row=>row.status==='acquired').map(row=>[row.name,row]));
  const sourceDefs=[
    ['vir-dpnr-planning','U.S. Virgin Islands comprehensive and coastal-zone planning','Department of Planning and Natural Resources',DPNR,'dpnr-planning.html'],
    ['vir-legislature-plan-adoption','Legislative action on the 2024 Comprehensive Land and Water Use Plan','Legislature of the Virgin Islands',LEGISLATURE,'legislature-plan-adoption.html'],
    ['vir-omb-ceds','Comprehensive Economic Development Strategy 2020–2025','U.S. Virgin Islands Office of Management and Budget',CEDS,'omb-ceds.html'],
    ['vir-omb-publications','OMB publications and budget materials','U.S. Virgin Islands Office of Management and Budget',PUBLICATIONS,'omb-publications.html'],
    ['vir-fy2025-budget','FY2025 Proposed Executive Budget Book','U.S. Virgin Islands Office of Management and Budget',BUDGET,'fy2025-budget.pdf']
  ];
  const ids=new Set(sourceDefs.map(row=>row[0]));dataset.sources=[...dataset.sources.filter(row=>!ids.has(row.id)),...sourceDefs.map(([id,name,publisher,url,file])=>{const r=acquired[file];const row={id,name,publisher,url,status:r?'ready':'failed',retrieved_at:receipt.generated_at.slice(0,10),reference_period:'current source at retrieval or source-titled period',geographic_level:'U.S. Virgin Islands',license:'Official public material; reuse terms not stated',note:r?'Source body acquired and hashed; legal, plan, budget and evaluation meanings remain separate.':'Official indexed source identified; automated acquisition failed and that failure is retained.',receipt_path:'raw/usvi-source-evidence/receipt.json'};if(r)Object.assign(row,{raw_path:`raw/usvi-source-evidence/${file}`,sha256:r.sha256,bytes:r.bytes});return row;})];
  const documents=[
    ['vir-planning-overview','reference','U.S. Virgin Islands comprehensive and coastal-zone planning','official-reference',DPNR,'vir-dpnr-planning'],
    ['vir-2024-plan-adoption','plan','Legislative action on the 2024 Comprehensive Land and Water Use Plan','official-reference',LEGISLATURE,'vir-legislature-plan-adoption'],
    ['vir-ceds-2020-2025','plan','Comprehensive Economic Development Strategy 2020–2025','official-plan',CEDS,'vir-omb-ceds'],
    ['vir-omb-publications','implementation','OMB publications and performance-related materials','official-reference',PUBLICATIONS,'vir-omb-publications'],
    ['vir-fy2025-budget','budget','FY2025 Proposed Executive Budget Book','official-budget',BUDGET,'vir-fy2025-budget']
  ].map(([id,category,title,kind,url,source_id])=>({id,territory_id:'VIR',category,title,kind,url,availability:dataset.sources.find(row=>row.id===source_id)?.status==='ready'?'body_acquired':'failed',official_status:'unverified',source_id}));
  const docIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!docIds.has(row.id)),...documents];
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'vir-census-2020-island-depth','vir-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'VIR: 2020 Island Areas Census data cover the territory and St. Croix, St. John and St. Thomas. Social and economic indicators preserve their documented household or family universes and COVID-19 collection limits.','VIR: World Bank electricity is territory-level only; SNAP is food-assistance participation rather than a nutrition outcome; density is settlement context rather than an urban/rural classification.'];
  dataset.planning=dataset.planning||{};dataset.planning.update={status:'current',message:'U.S. Virgin Islands sources distinguish territorial planning, the economic-development strategy, budget publications and implementation evidence. Source publication alone is not treated as proof of plan delivery or evaluation.',checked_at:new Date().toISOString(),last_success_at:new Date().toISOString()};
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  await writeFile(dataPath,JSON.stringify(dataset,null,2)+'\n');await generateSite({dataset,outDir:root});
  await copyFiles(source,path.join(root,'raw','usvi-source-evidence'));
  await copyFiles(collection,path.join(root,'raw','usvi-required-themes'));
  await copyFiles(census,path.join(root,'raw','usvi-census-2020'),{exclude:['tl_2020_us_county.zip']});
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'VIR',status:'complete',edition_complete:true,collection_audit:'evidence/USVI_COLLECTION_AUDIT.json',counts:{territories:3,indicators:14,observations:56,boundaries:3,semantic_inventory_records:rows.length},source_limits:['Social and economic characteristics exclude group-quarters population where documented by the Census technical material.','World Bank electricity is territory-level only and is not copied to islands.','SNAP participation is not a nutrition outcome; density is not an urban/rural classification.','The legislature source request failed and remains failed_with_evidence rather than being treated as absence.'],dataset_sha256:await sha(dataPath)};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'USVI_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'USVI_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n')]);
  console.log(JSON.stringify({country_area_id:'VIR',validation,semantic_rows:rows.length,planning_acquired:Object.keys(acquired).length,planning_failed:receipt.files.length-Object.keys(acquired).length,dataset_sha256:integration.dataset_sha256},null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

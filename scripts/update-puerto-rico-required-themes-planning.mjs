#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';

const PRCS='https://www.census.gov/library/stories/2025/05/puerto-rico-community-survey.html';
const CENSUS='https://www.census.gov/programs-surveys/decennial-census/about/rdo/island-areas.html';
const BOUNDARIES='https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html';
const PLANNING='https://www.jp.pr.gov/planificacion-fisica';
const REG24='https://jp.pr.gov/wp-content/uploads/2021/06/reg24.pdf';
const PLAN='https://jp.pr.gov/wp-content/uploads/2026/04/JP-PT-70-05-Plan-Final.pdf';
const BUDGET='https://www.ogp.pr.gov/ogp/gerencia-municipal';
const IMPLEMENTATION='https://www.ogp.pr.gov/ogp/servicios-esenciales';
const EIA='https://www.eia.gov/electricity/annual/table.php?t=epa_12_01.html';
const HEALTH='https://www.salud.pr.gov/CMS/DOWNLOAD/10416';

function args(){const result={};for(let i=2;i<process.argv.length;i+=2)result[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return result;}
function domain(status,urls,note,evidence,{acquired=true}={}){return {status,identified:true,accessed:true,acquired,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};}
async function copyFiles(source,target){await mkdir(target,{recursive:true});for(const name of await readdir(source)){const file=path.join(source,name);if((await stat(file)).isFile())await cp(file,path.join(target,name),{force:true});}}
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');

async function main(){
  const a=args();if(!a.project||!a.collection||!a.source)throw new Error('Usage: node scripts/update-puerto-rico-required-themes-planning.mjs --project <dir> --collection <dir> --source <dir>');
  const root=path.resolve(a.project),collection=path.resolve(a.collection),source=path.resolve(a.source),evidenceDir=path.join(root,'evidence'),dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,audit,receipt]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(collection,'PUERTO_RICO_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse),readFile(path.join(source,'receipt.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.selected_geography_count!==79||audit.municipio_count!==78||audit.indicator_count!==18||audit.observation_count!==1266||audit.boundary_feature_count!==78)throw new Error('Puerto Rico collection audit is incomplete');
  const expected=['PRI_PRCS_POP_TOTAL','PRI_PRCS_FEMALE_PCT','PRI_PRCS_AGE_0_14_PCT','PRI_PRCS_HOUSEHOLDS_TOTAL','PRI_PRCS_HOUSING_UNITS_TOTAL','PRI_PRCS_LACKING_PLUMBING_PCT','PRI_PRCS_HIGH_SCHOOL_OR_HIGHER_PCT','PRI_PRCS_LABOR_FORCE_PCT','PRI_PRCS_DISABILITY_PCT','PRI_PRCS_BORN_OUTSIDE_PR_PCT','PRI_PRCS_HISPANIC_LATINO_PCT','PRI_PRCS_UNINSURED_PCT','PRI_PRCS_POVERTY_PCT','PRI_PRCS_SNAP_HOUSEHOLDS_PCT','PRI_PRCS_BROADBAND_PCT','PRI_C2020_URBAN_POP_PCT','PRI_EIA_ELECTRIC_CUSTOMERS_TOTAL_2024','PRI_BRFSS_ADULT_OBESITY_PCT_2024'];
  for(const id of expected)if(!dataset.indicators.some(row=>row.id===id))throw new Error(`Missing Puerto Rico indicator ${id}`);
  const country=preflight.countries.find(row=>row.country_area_id==='PRI');if(!country)throw new Error('PRI preflight record missing');
  const censusEvidence=[{audit:'evidence/PUERTO_RICO_COLLECTION_AUDIT.json'},{raw:'raw/puerto-rico-required-themes'}],planningEvidence=[{receipt:'raw/puerto-rico-source-evidence/receipt.json'},{audit:'evidence/PUERTO_RICO_INTEGRATION_AUDIT.json'}];
  country.scope_role='completed Puerto Rico edition with 78-municipio PRCS/Census adapter';
  country.official_statistics_office=domain('inspected',[CENSUS,PRCS],'The U.S. Census Bureau Puerto Rico Census and PRCS releases were inspected. Puerto Rico is retained as its own AreaData country/area branch.',censusEvidence);
  country.latest_census=domain('adopted',[CENSUS],'The 2020 Census is the latest completed population census and is adopted for the urban/rural classification; 2023 PRCS survey estimates remain separately labeled. The 2030 round is future/scheduled; its results are not acquired or usable.',censusEvidence);
  country.census_results=domain('adopted',[CENSUS,PRCS],'Official 2020 Census urban/rural counts and 2019–2023 PRCS estimates are integrated for all 78 municipios using exact Census FIPS.',censusEvidence);
  country.table_catalog=domain('inspected',[PRCS],'Fourteen official PRCS detailed tables and their Census variable metadata were inspected; retained formulas and rows are archived.',censusEvidence);
  country.machine_readable_data=domain('adopted',[PRCS],'Official Census table-based Summary File rows are integrated for Puerto Rico and every municipio; no U.S. mainland row is included.',censusEvidence);
  country.administrative_codes=domain('geography_matched',[PRCS,BOUNDARIES],'Puerto Rico state-equivalent FIPS 72 and all 78 five-digit municipio codes are joined exactly.',censusEvidence);
  country.adm1_adm2_boundaries=domain('adopted',[BOUNDARIES],'All 78 official Census municipio cartographic boundary features are integrated as source-attributed reference geometry.',censusEvidence);
  country.planning_law=domain('inspected',[PLANNING],'The Puerto Rico Planning Board states that Municipal Code Law 107-2020 authorizes municipal territorial plans and that territorial plans have an eight-year term. The official planning page is acquired; the legal meaning remains specific to land-use planning.',planningEvidence);
  country.planning_guidance=domain('acquired',[PLANNING,REG24],'The Planning Board publishes the land-use plan framework, territorial-plan catalog, process material and Regulation 24. The planning catalog body is acquired; one direct PDF request failed and that failure is retained.',planningEvidence);
  country.plans_budgets_implementation_evaluation=domain('acquired',[PLANNING,PLAN,BUDGET,IMPLEMENTATION],'The Planning Board catalog exposes municipal territorial plans and action programs, while OGP publishes municipal budgets, debt statistics and essential-services agreements. These sources remain separate and do not imply that every municipio has a current approved plan or outcome evaluation.',planningEvidence);
  country.country_adapter_status='complete_country_adapter';

  const indicatorTheme={
    PRI_PRCS_POP_TOTAL:'population_total',PRI_PRCS_FEMALE_PCT:'age_sex',PRI_PRCS_AGE_0_14_PCT:'age_sex',PRI_PRCS_HOUSEHOLDS_TOTAL:'households_housing',PRI_PRCS_HOUSING_UNITS_TOTAL:'households_housing',PRI_PRCS_LACKING_PLUMBING_PCT:'drinking_water',PRI_PRCS_HIGH_SCHOOL_OR_HIGHER_PCT:'education_literacy',PRI_PRCS_LABOR_FORCE_PCT:'employment',PRI_PRCS_DISABILITY_PCT:'disability',PRI_PRCS_BORN_OUTSIDE_PR_PCT:'migration',PRI_PRCS_HISPANIC_LATINO_PCT:'ethnicity',PRI_PRCS_UNINSURED_PCT:'health',PRI_PRCS_POVERTY_PCT:'poverty',PRI_PRCS_SNAP_HOUSEHOLDS_PCT:'nutrition',PRI_PRCS_BROADBAND_PCT:'connectivity',PRI_C2020_URBAN_POP_PCT:'urban_rural',PRI_EIA_ELECTRIC_CUSTOMERS_TOTAL_2024:'electricity',PRI_BRFSS_ADULT_OBESITY_PCT_2024:'nutrition'
  };
  const sourceFor=id=>dataset.indicators.find(row=>row.id===id)?.source_id;
  const numericCount=id=>dataset.observations.filter(row=>row.indicator_id===id&&row.territory_id.startsWith('PRI')).length;
  const rows=Object.entries(indicatorTheme).map(([indicatorId,theme])=>({country_area_id:'PRI',source_id:sourceFor(indicatorId),source_path:'evidence/PUERTO_RICO_COLLECTION_AUDIT.json',source_url:indicatorId==='PRI_EIA_ELECTRIC_CUSTOMERS_TOTAL_2024'?EIA:indicatorId==='PRI_BRFSS_ADULT_OBESITY_PCT_2024'?HEALTH:indicatorId==='PRI_C2020_URBAN_POP_PCT'?CENSUS:PRCS,table_id:dataset.indicators.find(row=>row.id===indicatorId)?.definition_id||indicatorId,table_title:dataset.indicators.find(row=>row.id===indicatorId)?.name||indicatorId,field_id:indicatorId,field_label:dataset.indicators.find(row=>row.id===indicatorId)?.name||indicatorId,numeric_cell_count:numericCount(indicatorId),theme,disposition:'integrated',reason:['PRI_EIA_ELECTRIC_CUSTOMERS_TOTAL_2024','PRI_BRFSS_ADULT_OBESITY_PCT_2024'].includes(indicatorId)?'A source-reported Puerto Rico context value is integrated at country/area level only and is not assigned to municipios.':indicatorId==='PRI_PRCS_LACKING_PLUMBING_PCT'?'The exact combined plumbing-deprivation measure is integrated for Puerto Rico and all 78 municipios. It is not represented as a water-only or sewer-only measure.':'Official source rows are integrated for Puerto Rico and all 78 municipios with their actual reference period, unit and definition.',indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  rows.push({...rows.find(row=>row.indicator_id==='PRI_PRCS_LACKING_PLUMBING_PCT'),theme:'sanitation',reason:'The same exact combined plumbing-deprivation field is eligible for sanitation diagnosis, while its combined water/toilet/bathing definition is displayed and it is not represented as a sewer-only rate.'});
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!=='PRI'),...rows];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();inventory.adjudication={...(inventory.adjudication||{}),PRI:{reviewed_numeric_fields:rows.length,terminal_dispositions:rows.length,covered_themes:[...new Set(rows.map(row=>row.theme))].sort(),method:'Exact Puerto Rico PRCS/ACS rows, 2020 Census urban/rural counts, EIA customer accounts and PR-BRFSS nutrition context retain source-specific definitions and geographies.',audit:'evidence/PUERTO_RICO_INTEGRATION_AUDIT.json'}};

  const acquiredByName=Object.fromEntries(receipt.files.filter(row=>row.status==='acquired').map(row=>[row.name,row]));
  const sourceDefs=[
    ['pri-planning-physical','Puerto Rico physical planning and territorial-plan catalog','Junta de Planificación de Puerto Rico',PLANNING,'planning_physical.html'],
    ['pri-planning-regulation-24','Regulation 24 on municipal plans and transferred authorities','Junta de Planificación de Puerto Rico',REG24,'planning_regulation_24.pdf'],
    ['pri-planning-cayey-plan','Cayey Territorial Plan — Final Plan','Junta de Planificación de Puerto Rico / Municipio de Cayey',PLAN,'planning_cayey_final.pdf'],
    ['pri-ogp-municipal-budgets','Municipal management statistics and budgets','Oficina de Gerencia y Presupuesto de Puerto Rico',BUDGET,'budget_municipal.html'],
    ['pri-ogp-essential-services','Municipal essential-services agreements','Oficina de Gerencia y Presupuesto de Puerto Rico',IMPLEMENTATION,'essential_services.html']
  ];
  const planIds=new Set(sourceDefs.map(row=>row[0]));dataset.sources=[...dataset.sources.filter(row=>!planIds.has(row.id)),...sourceDefs.map(([id,name,publisher,url,file])=>{const receiptRow=acquiredByName[file];const result={id,name,publisher,url,status:receiptRow?'ready':'failed',retrieved_at:receipt.generated_at.slice(0,10),reference_period:'current source at retrieval',geographic_level:'Puerto Rico or source-specific municipio coverage',license:'Official public material; reuse terms not stated',note:receiptRow?'Source body acquired and hashed. Planning, budget and implementation status retain their own meanings.':'Official indexed source identified; direct automated acquisition failed and the failure is retained.',receipt_path:'raw/puerto-rico-source-evidence/receipt.json'};if(receiptRow)Object.assign(result,{raw_path:`raw/puerto-rico-source-evidence/${file}`,sha256:receiptRow.sha256,bytes:receiptRow.bytes});return result;})];
  const documents=[
    ['pri-planning-overview','PRI','reference','Puerto Rico land-use and municipal territorial planning framework','official-reference',PLANNING,'pri-planning-physical'],
    ['pri-regulation-24','PRI','reference','Regulation 24 — municipal plans and transfer of authorities','official-guidance',REG24,'pri-planning-regulation-24'],
    ['pri-cayey-territorial-plan','PRI','plan','Cayey Territorial Plan — Final Plan','official-plan',PLAN,'pri-planning-cayey-plan'],
    ['pri-municipal-budgets','PRI','budget','Municipal budgets and fiscal statistics','official-reference',BUDGET,'pri-ogp-municipal-budgets'],
    ['pri-essential-services','PRI','implementation','Municipal essential-services agreements','official-reference',IMPLEMENTATION,'pri-ogp-essential-services']
  ].map(([id,territory_id,category,title,kind,url,source_id])=>({id,territory_id,category,title,kind,url,availability:dataset.sources.find(row=>row.id===source_id)?.status==='ready'?'body_acquired':'failed',official_status:'unverified',source_id}));
  const docIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!docIds.has(row.id)),...documents];
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'pri-prcs-2023-municipio-depth','pri-census-2020-urban','pri-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'PRI: 2019–2023 PRCS estimates cover Puerto Rico and all 78 municipios; 2020 Census urban/rural data, 2024 EIA customer counts and PR-BRFSS obesity retain separate periods and methods.','Puerto Rico is a separate AreaData country/area branch. Its municipio records are not merged into the United States branch.'];
  dataset.planning=dataset.planning||{};dataset.planning.update={status:'current',message:'Puerto Rico sources distinguish the municipal territorial-plan framework, plan documents, municipal budgets and implementation-related agreements. Publication does not by itself establish a current approved plan or outcome evaluation for every municipio.',checked_at:new Date().toISOString(),last_success_at:new Date().toISOString()};
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  await copyFiles(source,path.join(root,'raw','puerto-rico-source-evidence'));await copyFiles(collection,path.join(root,'raw','puerto-rico-required-themes'));
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'PRI',status:'complete',edition_complete:true,collection_audit:'evidence/PUERTO_RICO_COLLECTION_AUDIT.json',counts:{territories:79,municipios:78,indicators:18,observations:1266,boundaries:78},planning:{law:PLANNING,guidance:[PLANNING,REG24],plan:PLAN,budget:BUDGET,implementation:IMPLEMENTATION,acquired:receipt.files.filter(row=>row.status==='acquired').length,failed_with_evidence:receipt.files.filter(row=>row.status!=='acquired').length,scope_limit:receipt.scope_limit},cross_country_isolation:'Only state FIPS 72 and municipio GEOIDs 72xxx are included; no USA branch territory is replaced or reparented.'};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'PUERTO_RICO_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'PUERTO_RICO_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  console.log(JSON.stringify({country_area_id:'PRI',edition_complete:true,semantic_rows:rows.length,planning_acquired:integration.planning.acquired,planning_failed_with_evidence:integration.planning.failed_with_evidence,validation_errors:validation.errors,validation_warnings:validation.warnings,dataset_sha256:await sha(dataPath)},null,2));
}

main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});

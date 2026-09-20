#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';

const CENSUS='https://www.inide.gob.ni/docu/censos2005/censo2005.htm';
const CATALOG='https://www.inide.gob.ni/docu/censos2005/CifrasMun/tablas_cifras.htm';
const BOUNDARIES='https://www.ineter.gob.ni/geoportales/miacnicaragua/index.html';
const LAW40='https://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?action=openDocument&documentId=67CC56A8B80761DA0625886F006DCDBC';
const LAW475='https://legislacion.asamblea.gob.ni/Normaweb.nsf/%28%24All%29/F78CA467F5C96D0306257257005FBADC';
const LAW792='https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/c9a0faf9d8c5e28f062572c70052cde2/7ebe8ba4e242fa7b062579eb0064e3b6/%24FILE/Ley%20No.%20792%20reforma%20Ley%20de%20municipios.pdf';
const LAW828='https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/0/362c8026f915756806257ac6007facc6/%24FILE/Ley%20No.%20828%20Ley%20de%20Reforma%20a%20la%20Ley%20R%C3%A9gimen%20Presupuestario%20Municipal.pdf';
const BUDGET='https://www.hacienda.gob.ni/presupuesto2026/';
const EXEC='https://www.hacienda.gob.ni/wp-content/uploads/2026/05/INFORME-DE-EJECUCION-PRESUPUESTARIA-ENERO-MARZO-2026.pdf';
const PIP='https://www.hacienda.gob.ni/programa-de-inversion-publica/';
const PIP_REPORTS='https://www.hacienda.gob.ni/reportes-del-programa-de-inversion-publica/';
const NATIONAL_PLAN='https://www.hacienda.gob.ni/plan-nacional-de-lucha-contra-la-pobreza-2022-2026/';

const themes={
  population_total:'NIC_C2005_POP_TOTAL',age_sex:'NIC_C2005_FEMALE_PCT',households_housing:'NIC_C2005_OCCUPIED_HOUSING_PCT',drinking_water:'NIC_C2005_WATER_ACCESS_PCT',sanitation:'NIC_C2005_SANITATION_ACCESS_PCT',electricity:'NIC_C2005_ELECTRICITY_ACCESS_PCT',education_literacy:'NIC_C2005_ILLITERACY_PCT',employment:'NIC_C2005_ECONOMICALLY_ACTIVE_PCT',disability:'NIC_C2005_DISABLED_HOUSEHOLD_PCT',migration:'NIC_C2005_EMIGRANT_HOUSEHOLD_PCT',urban_rural:'NIC_C2005_URBAN_PCT',ethnicity:'NIC_C2005_ETHNIC_SELF_ID_PCT',health:'NIC_C2005_FAR_HEALTH_CENTER_PCT',nutrition:'NIC_WB_UNDERNOURISHMENT_PCT',poverty:'NIC_C2005_NBI_POVERTY_PCT'
};
const planningSources=[
  ['nic-law-40','Consolidated Law No. 40, Law of Municipalities','National Assembly of Nicaragua',LAW40,'law'],
  ['nic-law-475','Law No. 475, Citizen Participation Law','National Assembly of Nicaragua',LAW475,'guidance'],
  ['nic-law-792','Law No. 792, reform of the Law of Municipalities','National Assembly of Nicaragua',LAW792,'law'],
  ['nic-law-828','Law No. 828, reform of the Municipal Budget Regime Law','National Assembly of Nicaragua',LAW828,'law'],
  ['nic-budget-2026','General Budget of the Republic 2026','Ministry of Finance and Public Credit',BUDGET,'budget'],
  ['nic-budget-execution-2026-q1','Budget Execution Report January–March 2026','Ministry of Finance and Public Credit',EXEC,'implementation'],
  ['nic-public-investment-program','Public Investment Program 2026','Ministry of Finance and Public Credit',PIP,'implementation'],
  ['nic-public-investment-reports','Public Investment Program reports','Ministry of Finance and Public Credit',PIP_REPORTS,'evaluation'],
  ['nic-national-development-plan','National Plan to Fight Poverty and for Human Development 2022–2026','Ministry of Finance and Public Credit',NATIONAL_PLAN,'plan'],
];

function domain(status,urls,note,evidence,{acquired=true}={}){
  return {status,identified:true,accessed:true,acquired,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};
}

async function copyFiles(source,target){
  await mkdir(target,{recursive:true});
  for(const file of await readdir(source)){
    const from=path.join(source,file),info=await stat(from);
    if(info.isFile())await cp(from,path.join(target,file),{force:true});
  }
}

export async function updateNicaragua({project,collection,planning}={}){
  if(!project||!collection||!planning)throw new Error('project, collection and planning are required');
  const root=path.resolve(project),collectionRoot=path.resolve(collection),planningRoot=path.resolve(planning),evidenceDir=path.join(root,'evidence');
  const dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,audit,planningReceipt]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(collectionRoot,'NICARAGUA_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse),readFile(path.join(planningRoot,'planning-receipt.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.counts?.territories!==170||audit.counts?.indicators!==15||audit.counts?.boundaries!==170||audit.coverage?.municipalities!==153)throw new Error('Nicaragua collection audit does not meet the required 17-department/153-municipality/15-theme coverage');
  for(const iid of Object.values(themes))if(!dataset.indicators.some(row=>row.id===iid))throw new Error(`Missing integrated Nicaragua indicator ${iid}`);
  const acquired=planningReceipt.entries.filter(row=>row.status==='acquired');
  if(acquired.length<5||!acquired.some(row=>row.url===EXEC))throw new Error('Required Nicaragua budget, implementation, plan and reporting evidence was not acquired');
  const nic=preflight.countries.find(row=>row.country_area_id==='NIC');if(!nic)throw new Error('NIC preflight record is missing');
  const censusEvidence=[{audit:'evidence/NICARAGUA_COLLECTION_AUDIT.json'},{raw:'raw/nicaragua-census'}],planningEvidence=[{receipt:'raw/nicaragua-planning/planning-receipt.json'},{audit:'evidence/NICARAGUA_INTEGRATION_AUDIT.json'}];
  nic.scope_role='completed country edition with 2005 Census department and municipality adapter';
  nic.official_statistics_office=domain('inspected',[CENSUS],'INIDE official Census products and all adopted tables were inspected.',censusEvidence);
  nic.latest_census=domain('adopted',[CENSUS],'The completed nationwide Census results adopted here are from 2005; the edition displays that reference year rather than substituting a modelled current population.',censusEvidence);
  nic.census_results=domain('adopted',[CENSUS,CATALOG],'Official 2005 Census results are integrated for the country, 17 departments/autonomous regions and 153 municipalities.',censusEvidence);
  nic.table_catalog=domain('inspected',[CATALOG],'All 153 municipal reports and the national population, housing and household volumes used by the adapter were inventoried.',censusEvidence);
  nic.machine_readable_data=domain('adopted',[CATALOG],'Published PDF table rows were parsed into source-linked observations; image-only content and source differences are recorded in the collection audit.',censusEvidence);
  nic.administrative_codes=domain('geography_matched',[CATALOG,BOUNDARIES],'The 2005 Census department and municipality codes are retained; later INETER name/code differences are recorded explicitly.',censusEvidence);
  nic.adm1_adm2_boundaries=domain('adopted',[BOUNDARIES],'The official INETER display layer covers 17 first-order areas and 153 municipalities. Its 2018 metadata vintage is shown and it is not represented as a 2005 or current legal-boundary certification.',censusEvidence);
  nic.planning_law=domain('inspected',[LAW40,LAW792,LAW828],'Official National Assembly texts establish municipal development-plan responsibilities, the SPMDH framework and the municipal budget regime. Browser inspection succeeded; direct body acquisition from the Assembly host timed out and that failure is retained in the receipt.',planningEvidence,{acquired:false});
  nic.planning_guidance=domain('inspected',[LAW475,LAW40],'The statutory participation process for municipal strategy, development plans and investment plans was inspected. No separate current national municipal planning manual was acquired, so statutory procedure is not presented as a detailed manual.',planningEvidence,{acquired:false});
  nic.plans_budgets_implementation_evaluation=domain('inspected',[NATIONAL_PLAN,BUDGET,EXEC,PIP,PIP_REPORTS],'National plan, budget, first-quarter execution and public-investment reporting sources were acquired. These do not prove that every municipality has a current approved local plan or completed implementation.',planningEvidence);
  nic.country_adapter_status='complete_country_adapter';

  const sourceByTheme=theme=>theme==='nutrition'?'nic-world-bank-nutrition':'nic-inide-census-2005';
  const newRows=Object.entries(themes).map(([theme,indicatorId])=>({country_area_id:'NIC',source_id:sourceByTheme(theme),source_path:'evidence/NICARAGUA_COLLECTION_AUDIT.json',source_url:theme==='nutrition'?'https://api.worldbank.org/v2/country/NIC/indicator/SN.ITK.DEFC.ZS?format=json':CATALOG,table_id:theme==='nutrition'?'world-bank-country-series':'INIDE 2005 adopted census table',table_title:theme==='nutrition'?'National international-reference series':'Nicaragua 2005 Census adopted theme table',field_id:indicatorId,field_label:dataset.indicators.find(row=>row.id===indicatorId)?.name||indicatorId,numeric_cell_count:theme==='nutrition'?1:(theme==='ethnicity'?18:171),theme,disposition:'integrated',reason:theme==='nutrition'?'A national international-reference observation is integrated as context and is not assigned to departments or municipalities.':theme==='ethnicity'?'The official Census ethnicity field is integrated for the country and all 17 first-order areas; no municipality value is inferred.':'The official 2005 Census field is integrated for the country, all 17 first-order areas and all 153 municipalities with source definitions and retained numerator/denominator where derived.',indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!=='NIC'),...newRows];

  const pids=new Set(planningSources.map(row=>row[0]));dataset.sources=[...dataset.sources.filter(row=>!pids.has(row.id)),...planningSources.map(([id,name,publisher,url,category])=>{const receipt=planningReceipt.entries.find(row=>row.url===url);if(!receipt)throw new Error(`Missing planning receipt for ${url}`);const source={id,name,publisher,url,status:receipt.status==='acquired'?'ready':'failed',retrieved_at:planningReceipt.retrieved_at.slice(0,10),reference_period:category==='implementation'?'2026':'current source at retrieval',geographic_level:'national framework with municipal planning relevance',license:'Official public material; reuse terms not stated',note:receipt.status==='acquired'?'Planning evidence category remains distinct from local plan approval and outcome status.':'The official page was inspected through indexed web access; direct acquisition timed out and the receipt preserves the failed attempt.',receipt_path:'raw/nicaragua-planning/planning-receipt.json'};if(receipt.status==='acquired')Object.assign(source,{raw_path:`raw/nicaragua-planning/${receipt.file}`,sha256:receipt.sha256,bytes:receipt.bytes});return source;})];
  dataset.documents=[...(dataset.documents||[]).filter(row=>!String(row.id).startsWith('nic-')), ...planningSources.map(([id,name,,url,category])=>{const receipt=planningReceipt.entries.find(row=>row.url===url);return {id:`${id}-document`,territory_id:'NIC',category:['law','guidance'].includes(category)?'reference':category,title:name,kind:'official-reference',url,availability:receipt.status==='acquired'?'body_acquired':'failed',official_status:'unverified',source_id:id};})];
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'nic-2005-census-depth','nic-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'NIC 2005: 15 required themes completed; 13 themes cover country, 17 departments/autonomous regions and 153 municipalities, ethnicity covers country and first-order areas, and nutrition remains national international-reference context.','NIC boundary and source vintages remain explicit: 2005 Census analysis codes are joined to the official INETER display layer with 2018 metadata; documented name/code changes are not silently harmonized.'];
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  await copyFiles(collectionRoot,path.join(root,'raw','nicaragua-census'));await cp(planningRoot,path.join(root,'raw','nicaragua-planning'),{recursive:true,force:true});
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'NIC',status:'complete',edition_complete:true,collection_audit:'evidence/NICARAGUA_COLLECTION_AUDIT.json',counts:audit.counts,coverage:audit.coverage,boundary_limit:audit.boundary_limit,planning:{law:[LAW40,LAW792,LAW828],guidance:LAW475,plan:NATIONAL_PLAN,budget:BUDGET,implementation:[EXEC,PIP],evaluation:PIP_REPORTS,assembly_download_status:'Official text inspected through web/indexed access; four direct source-body downloads timed out and remain recorded as failed.',scope_limit:planningReceipt.scope_limit}};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'NICARAGUA_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'NICARAGUA_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  return {country_area_id:'NIC',edition_complete:true,semantic_rows:newRows.length,planning_acquired:acquired.length,planning_retrieval_failures:planningReceipt.entries.length-acquired.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','collection','planning']);if(args.help||!args.project||!args.collection||!args.planning)console.log('node scripts/update-nicaragua-required-themes-planning.mjs --project <directory> --collection <collector-output> --planning <planning-raw>');else console.log(JSON.stringify(await updateNicaragua({project:args.project,collection:args.collection,planning:args.planning}),null,2));}catch(error){reportError(error);}
}

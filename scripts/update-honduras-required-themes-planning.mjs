#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';

const CENSUS='https://ine.gob.hn/censo-de-poblacion-y-vivienda-2013/';
const REDATAM='http://181.115.7.199/binhnd/RpWebEngine.exe/Portal';
const HDX='https://data.humdata.org/dataset/cod-ab-hnd';
const LAW='https://www.tsc.gob.hn/biblioteca/index.php/leyes/4-ley-de-municipalidades';
const LOT='https://sinit.hn/download/29/marco-legal/6045/ley-ordenamiento-territorial-honduras.pdf';
const GUIDE='https://sinit.hn/download/28/recursos-digitales/10908/lineamientos-ot-final-version.pdf';
const PLANS='https://sinit.hn/planes-municipales/';
const RENOT='https://sinit.hn/renot/';
const SAMI='https://www.sefin.gob.hn/sami/';
const EXEC='https://www.sefin.gob.hn/wp-content/uploads/2026/04/Informe-de-Gobiernos-Locales-a-diciembre-2025.pdf';
const FOLLOW='https://www.sefin.gob.hn/ejecucion-y-seguimiento/';

const themes={
  population_total:'HND_C2013_POP_TOTAL',age_sex:'HND_C2013_FEMALE_PCT',households_housing:'HND_C2013_PRESENT_DWELLINGS_PCT',drinking_water:'HND_C2013_PIPED_WATER_PCT',sanitation:'HND_C2013_SANITATION_NBI_PCT',electricity:'HND_C2013_ELECTRIC_SOLAR_LIGHT_PCT',education_literacy:'HND_C2013_ILLITERACY_PCT',employment:'HND_C2013_EMPLOYED_PCT',disability:'HND_C2013_WALKING_LIMITATION_PCT',migration:'HND_C2013_FOREIGN_BORN_PCT',urban_rural:'HND_C2013_URBAN_PCT',ethnicity:'HND_C2013_INDIGENOUS_AFRO_PCT',health:'HND_WB_LIFE_EXPECTANCY',nutrition:'HND_WB_UNDERNOURISHMENT_PCT',poverty:'HND_C2013_NBI_POVERTY_PCT'
};
const planningSources=[
  ['hnd-municipalities-law','Ley de Municipalidades','Tribunal Superior de Cuentas',LAW,'law'],
  ['hnd-territorial-planning-law','Ley de Ordenamiento Territorial','Sistema Nacional de Información Territorial',LOT,'law'],
  ['hnd-territorial-planning-guidance','Lineamientos de ordenamiento territorial','Sistema Nacional de Información Territorial',GUIDE,'guidance'],
  ['hnd-municipal-plan-catalog','Planes municipales (PMOT) catalogue','Sistema Nacional de Información Territorial',PLANS,'plan'],
  ['hnd-renot','Registro de Normativas de Ordenamiento Territorial','Sistema Nacional de Información Territorial',RENOT,'plan'],
  ['hnd-sami','Sistema de Administración Municipal Integrado','Secretaría de Finanzas',SAMI,'budget'],
  ['hnd-local-execution-2025','Informe de Gobiernos Locales a diciembre de 2025','Secretaría de Finanzas',EXEC,'implementation'],
  ['hnd-execution-monitoring','Ejecución y seguimiento','Secretaría de Finanzas',FOLLOW,'evaluation']
];
const domain=(status,urls,note,evidence)=>({status,identified:true,accessed:true,acquired:true,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence});

async function copySelectedRaw(source,target){
  await mkdir(target,{recursive:true});
  for(const file of await readdir(source)){
    const from=path.join(source,file),info=await stat(from);
    if(info.isFile()&&info.size<=12_000_000)await cp(from,path.join(target,file),{force:true});
  }
}

export async function updateHonduras({project,collection,planning}={}){
  if(!project||!collection||!planning)throw new Error('project, collection and planning are required');
  const root=path.resolve(project),collectionRoot=path.resolve(collection),planningRoot=path.resolve(planning),evidenceDir=path.join(root,'evidence');
  const dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,audit,planningReceipt]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(collectionRoot,'HONDURAS_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse),readFile(path.join(planningRoot,'planning-receipt.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.counts?.territories!==316||audit.counts?.indicators!==15||audit.counts?.boundaries!==316)throw new Error('Honduras collection audit does not meet the required 18-department/298-municipality/15-theme coverage');
  if(planningReceipt.entries.some(row=>row.status!=='acquired'))throw new Error('One or more Honduras planning sources were not acquired');
  for(const iid of Object.values(themes))if(!dataset.indicators.some(row=>row.id===iid))throw new Error(`Missing integrated Honduras indicator ${iid}`);
  const hnd=preflight.countries.find(row=>row.country_area_id==='HND');if(!hnd)throw new Error('HND preflight record is missing');
  const censusEvidence=[{audit:'evidence/HONDURAS_COLLECTION_AUDIT.json'},{raw:'raw/honduras-census'}],planningEvidence=[{receipt:'raw/honduras-planning/planning-receipt.json'},{audit:'evidence/HONDURAS_INTEGRATION_AUDIT.json'}];
  hnd.scope_role='completed country edition with 2013 Census department and municipality adapter';
  hnd.official_statistics_office=domain('inspected',[CENSUS],'INE Honduras Census and Redatam products were accessed and their adopted tables were inspected.',censusEvidence);
  hnd.latest_census=domain('adopted',[CENSUS],'The completed results edition is the 2013 Census. A later census announcement is not substituted for published results.',censusEvidence);
  hnd.census_results=domain('adopted',[CENSUS,REDATAM],'Official 2013 Census Redatam tables were adopted for the country, 18 departments and 298 municipalities.',censusEvidence);
  hnd.table_catalog=domain('inspected',[CENSUS,REDATAM],'The Redatam field/category outputs used by the adapter were retained and inventoried.',censusEvidence);
  hnd.machine_readable_data=domain('adopted',[REDATAM],'The official Redatam query output is machine parsed; category counts remain attached to source locators.',censusEvidence);
  hnd.administrative_codes=domain('geography_matched',[CENSUS,REDATAM],'Official two-digit department and four-digit municipality Census codes were matched exactly.',censusEvidence);
  hnd.adm1_adm2_boundaries=domain('adopted',[HDX],'COD-AB contains all 18 departments and 298 municipalities and attributes the source to SINIT/SEPLAN. The 2010/2015/2016 vintage is displayed and is not presented as current legal certification.',censusEvidence);
  hnd.planning_law=domain('inspected',[LAW,LOT],'Municipalities and territorial-planning laws were acquired and inspected. Municipal legal responsibilities are kept separate from evidence that a particular local plan is current.',planningEvidence);
  hnd.planning_guidance=domain('inspected',[GUIDE],'Official territorial-planning guidance was acquired and inspected; its structure is not forced on other countries.',planningEvidence);
  hnd.plans_budgets_implementation_evaluation=domain('inspected',[PLANS,RENOT,SAMI,EXEC,FOLLOW],'Plan catalogues, the municipal financial system, a local-government execution report and monitoring entry point were acquired. Presence in a catalogue is not treated as proof that every municipality has a current approved plan.',planningEvidence);
  hnd.country_adapter_status='complete_country_adapter';

  const sourceByTheme=theme=>theme==='health'?'hnd-world-bank-life':theme==='nutrition'?'hnd-world-bank-nutrition':'hnd-ine-redatam-2013';
  const newRows=Object.entries(themes).map(([theme,indicatorId])=>({country_area_id:'HND',source_id:sourceByTheme(theme),source_path:'evidence/HONDURAS_COLLECTION_AUDIT.json',source_url:theme==='health'?'https://api.worldbank.org/v2/country/HND/indicator/SP.DYN.LE00.IN?format=json':theme==='nutrition'?'https://api.worldbank.org/v2/country/HND/indicator/SN.ITK.DEFC.ZS?format=json':REDATAM,table_id:theme==='health'||theme==='nutrition'?'world-bank-country-series':'CPVHND2013NAC Redatam adopted table',table_title:theme==='health'||theme==='nutrition'?'National international-reference series':'Honduras 2013 Census adopted theme table',field_id:indicatorId,field_label:dataset.indicators.find(row=>row.id===indicatorId)?.name||indicatorId,numeric_cell_count:theme==='health'||theme==='nutrition'?1:317,theme,disposition:'integrated',reason:theme==='health'||theme==='nutrition'?'A national international-reference observation is integrated as context and is not assigned to departments or municipalities.':'The official 2013 Census field is integrated for the country, all 18 departments and all 298 municipalities with source definition, numerator/denominator where derived, and exact Census codes.',indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!=='HND'),...newRows];

  const pids=new Set(planningSources.map(row=>row[0]));dataset.sources=[...dataset.sources.filter(row=>!pids.has(row.id)),...planningSources.map(([id,name,publisher,url,category])=>{const receipt=planningReceipt.entries.find(row=>row.url===url);if(!receipt)throw new Error(`Missing planning receipt for ${url}`);return {id,name,publisher,url,status:'ready',retrieved_at:planningReceipt.retrieved_at.slice(0,10),reference_period:category==='implementation'?'through December 2025':'current source at retrieval',geographic_level:'national system with municipal planning relevance',license:'Official public material; reuse terms not stated',note:category==='plan'?'Catalogue or registry access does not establish that every municipality has a current approved plan.':'Planning evidence category is kept distinct from plan approval and implementation status.',raw_path:`raw/honduras-planning/${receipt.file}`,receipt_path:'raw/honduras-planning/planning-receipt.json',sha256:receipt.sha256,bytes:receipt.bytes};})];
  dataset.documents=[...(dataset.documents||[]).filter(row=>!String(row.id).startsWith('hnd-')), ...planningSources.map(([id,name,,url,category])=>({id:`${id}-document`,territory_id:'HND',category:['law','guidance'].includes(category)?'reference':category,title:name,kind:'official-reference',url,availability:'body_acquired',official_status:'unverified',source_id:id}))];
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'hnd-2013-redatam-depth','hnd-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'HND 2013: 15 required themes completed; 13 Census themes cover the country, 18 departments and 298 municipalities, while health and nutrition remain national international-reference context.','HND boundaries: COD-AB display geometry derived from SINIT/SEPLAN, with its 2010/2015/2016 vintage shown; no current legal-boundary certification is asserted.'];
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  const censusTarget=path.join(root,'raw','honduras-census'),planningTarget=path.join(root,'raw','honduras-planning');
  await copySelectedRaw(path.join(collectionRoot,'raw'),censusTarget);await cp(path.join(collectionRoot,'HONDURAS_COLLECTION_AUDIT.json'),path.join(censusTarget,'HONDURAS_COLLECTION_AUDIT.json'),{force:true});await cp(planningRoot,planningTarget,{recursive:true,force:true});
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'HND',status:'complete',edition_complete:true,collection_audit:'evidence/HONDURAS_COLLECTION_AUDIT.json',counts:audit.counts,coverage:audit.coverage,boundary_limit:audit.boundary_limit,planning:{law:[LAW,LOT],guidance:GUIDE,plans:[PLANS,RENOT],budget:SAMI,implementation:EXEC,evaluation:FOLLOW,scope_limit:'The national sources identify municipal planning and financial systems. Municipality-specific current-plan, approval and implementation status remains document-specific and is not inferred from catalogue presence.'}};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'HONDURAS_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'HONDURAS_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  return {country_area_id:'HND',edition_complete:true,semantic_rows:newRows.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','collection','planning']);if(args.help||!args.project||!args.collection||!args.planning)console.log('node scripts/update-honduras-required-themes-planning.mjs --project <directory> --collection <collector-output> --planning <planning-raw>');else console.log(JSON.stringify(await updateHonduras({project:args.project,collection:args.collection,planning:args.planning}),null,2));}catch(error){reportError(error);}
}

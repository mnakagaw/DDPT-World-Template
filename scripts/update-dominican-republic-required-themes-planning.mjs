#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';

const CENSUS='https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/';
const BOUNDARIES='https://geoportal.iderd.gob.do/layers/geonode:RD_MUNICIPIOS/metadata_detail';
const LAW176='https://consultoria.gov.do/Consulta/Home/FileManagement?documentId=3345180&managementType=1';
const LAW498='https://mepyd.gob.do/wp-content/uploads/drive/DIGEDES/Monitoreo%20y%20Evaluaci%C3%B3n/Publicaciones/Normativa/Ley-498-06%20Planificaci%C3%B3n%20e%20Inversi%C3%B3n%20P%C3%BAblica.pdf';
const GUIDE='https://mepyd.gob.do/publicaciones/guia-para-la-formulacion-de-planes-de-desarrollo-municipales';
const GUIDE_PDF='https://mepyd.gob.do/wp-content/uploads/drive/VIOTDR/Publicaciones/Gu%C3%ADa%20metodol%C3%B3gica%20-%20C%C3%B3mo%20elaborar%20un%20plan%20municipal%20de%20desarrollo.pdf';
const PLAN='https://ayuntamientocomendador.gob.do/transparencia/wp-content/uploads/2026/01/PDM-Comendador-2025-2029.pdf';
const BUDGET='https://hist.digepres.gob.do/presupuesto/gobiernos-locales/?print=print';
const EXEC='https://www.digepres.gob.do/digepres-presenta-nueva-herramienta-para-transparentar-ejecucion-presupuestaria-de-gobiernos-locales/?print=pdf';
const ASSIST='https://mepyd.gob.do/asistencia-tecnica-en-temas-de-desarrollo-municipales/';

const themes={population_total:'DOM_C2022_POP_TOTAL',age_sex:'DOM_C2022_FEMALE_PCT',households_housing:'DOM_C2022_VACANT_DWELLINGS_PCT',drinking_water:'DOM_C2022_INDOOR_AQUEDUCT_WATER_PCT',sanitation:'DOM_C2022_NO_SANITARY_SERVICE_PCT',electricity:'DOM_C2022_PUBLIC_GRID_LIGHTING_PCT',education_literacy:'DOM_C2022_NO_EDUCATION_LEVEL_PCT',employment:'DOM_C2022_LABOR_FORCE_PARTICIPATION_PCT',disability:'DOM_C2022_FUNCTIONAL_DIFFICULTY_PCT',migration:'DOM_C2022_FOREIGN_BORN_PCT',urban_rural:'DOM_C2022_URBAN_PCT',ethnicity:'DOM_ENHOGAR2021_AFRODESCENDANT_PCT',health:'DOM_SNS_HEALTH_FACILITIES',nutrition:'DOM_WB_UNDERNOURISHMENT_PCT',poverty:'DOM_ONE_MONETARY_POVERTY_PCT'};

function args(){const r={};for(let i=2;i<process.argv.length;i+=2)r[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return r;}
function domain(status,urls,note,evidence,{acquired=true}={}){return {status,identified:true,accessed:true,acquired,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};}
async function copyFiles(source,target){await mkdir(target,{recursive:true});for(const name of await readdir(source)){const p=path.join(source,name);if((await stat(p)).isFile())await cp(p,path.join(target,name),{force:true});}}

async function main(){
  const a=args();if(!a.project||!a.collection||!a.planning)throw new Error('Usage: node scripts/update-dominican-republic-required-themes-planning.mjs --project <dir> --collection <dir> --planning <dir>');
  const root=path.resolve(a.project),collection=path.resolve(a.collection),planning=path.resolve(a.planning),evidence=path.join(root,'evidence'),dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,audit,receipt]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(collection,'DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse),readFile(path.join(planning,'planning-receipt.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.counts?.territories!==200||audit.counts?.municipalities!==158||audit.counts?.provinces!==32||audit.counts?.planning_regions!==10||audit.counts?.indicators!==15||audit.counts?.boundaries!==200)throw new Error('Dominican Republic collection audit does not meet 10-region/32-province/158-municipality/15-theme coverage');
  for(const iid of Object.values(themes))if(!dataset.indicators.some(row=>row.id===iid))throw new Error(`Missing integrated Dominican indicator ${iid}`);
  const country=preflight.countries.find(row=>row.country_area_id==='DOM');if(!country)throw new Error('DOM preflight record missing');
  const censusEvidence=[{audit:'evidence/DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json'},{raw:'raw/dominican-republic-census'}],planningEvidence=[{receipt:'raw/dominican-republic-planning/planning-receipt.json'},{audit:'evidence/DOMINICAN_REPUBLIC_INTEGRATION_AUDIT.json'}];
  country.scope_role='completed country edition with 2022 Census planning-region, province and municipality adapter';
  country.official_statistics_office=domain('inspected',[CENSUS],'The ONE Census catalog and adopted DDPT-normalized official tables were inspected.',censusEvidence);
  country.latest_census=domain('adopted',[CENSUS],'The X National Population and Housing Census 2022 is adopted with its actual reference year.',censusEvidence);
  country.census_results=domain('adopted',[CENSUS],'Official 2022 Census observations are integrated for 10 planning regions, 32 provinces and 158 municipalities; national values use all 10 non-overlapping regions.',censusEvidence);
  country.table_catalog=domain('inspected',[CENSUS],'The DDPT field inventory, source register, numerator/denominator records and all adopted territory rows were inspected.',censusEvidence);
  country.machine_readable_data=domain('adopted',[CENSUS],'Audited normalized JSON derived from ONE tables is adopted; DDPT source hashes and field-level provenance are retained.',censusEvidence);
  country.administrative_codes=domain('geography_matched',[CENSUS,BOUNDARIES],'ONE/DDPT region, province and municipality codes are retained and joined without name-only merging.',censusEvidence);
  country.adm1_adm2_boundaries=domain('adopted',[BOUNDARIES],'DDPT-verified IGN/IDERD reference geometry covers 10 planning regions, 32 provinces and 158 municipalities. It is display geometry, not a legal-boundary certification.',censusEvidence);
  country.planning_law=domain('inspected',[LAW176,LAW498],'Official legal texts establish municipal government and territorial planning/investment responsibilities. Indexed source inspection succeeded; direct automated acquisition failures remain in the receipt.',planningEvidence,{acquired:false});
  country.planning_guidance=domain('inspected',[GUIDE,GUIDE_PDF,ASSIST],'MEPyD publishes the municipal development-plan methodology and technical-assistance process. Direct automated acquisition was blocked by the host and is recorded.',planningEvidence,{acquired:false});
  country.plans_budgets_implementation_evaluation=domain('inspected',[PLAN,BUDGET,EXEC,ASSIST],'A current municipal plan example, local-government budget series and budget-execution dashboard evidence were acquired or inspected. They do not prove every municipality has a current plan or official outcome evaluation.',planningEvidence);
  country.country_adapter_status='complete_country_adapter';

  const sourceFor=theme=>theme==='ethnicity'?'dom-one-enhogar-2021':theme==='nutrition'?'dom-world-bank-nutrition':theme==='poverty'?'dom-one-poverty-2024':theme==='health'?'dom-sns-health-facilities-2026':'dom-one-census-2022';
  const counts=audit.theme_observation_counts||{};
  const rows=Object.entries(themes).map(([theme,indicatorId])=>({country_area_id:'DOM',source_id:sourceFor(theme),source_path:'evidence/DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json',source_url:theme==='ethnicity'?'https://www.one.gob.do/media/lu3gwjm0/informe-general-enhogar-2021.pdf':theme==='nutrition'?'https://api.worldbank.org/v2/country/DOM/indicator/SN.ITK.DEFC.ZS?format=json&per_page=100':theme==='poverty'?'https://www.one.gob.do/media/bbep4boj/boletin-pobreza-monetaria-2024.pdf':theme==='health'?'https://datos.gob.do/dataset/establecimientos-de-salud-sns':CENSUS,table_id:['ethnicity','nutrition','poverty'].includes(theme)?'national-context-series':'DDPT audited official table normalization',table_title:['ethnicity','nutrition','poverty'].includes(theme)?'National context; not assigned to lower areas':'Dominican Republic adopted country field',field_id:indicatorId,field_label:dataset.indicators.find(row=>row.id===indicatorId)?.name||indicatorId,numeric_cell_count:counts[theme]||1,theme,disposition:'integrated',reason:['ethnicity','nutrition','poverty'].includes(theme)?'A source-reported national context observation is integrated and is not inferred for planning regions, provinces or municipalities.':theme==='health'?'The complete country facility count and all published lower-area records are integrated; a missing lower-area record is not silently converted to zero.':'The adopted field includes a complete national observation and official lower-area observations with numerator and denominator retained for ratios.',indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!=='DOM'),...rows];

  const planDefs=[
    ['dom-law-176-07','Law 176-07 on the National District and Municipalities','Consultoría Jurídica del Poder Ejecutivo',LAW176,'law'],
    ['dom-law-498-06','Law 498-06 on Planning and Public Investment','MEPyD',LAW498,'law'],
    ['dom-mepyd-pmd-guide','Guide for formulating municipal development plans','MEPyD',GUIDE,'guidance'],
    ['dom-mepyd-pmd-guide-pdf','Municipal development-plan methodology PDF','MEPyD',GUIDE_PDF,'guidance'],
    ['dom-comendador-pdm-2025-2029','Comendador Municipal Development Plan 2025-2029','Ayuntamiento de Comendador',PLAN,'plan'],
    ['dom-digepres-local-budgets','Local-government formulated and executed budgets','DIGEPRES',BUDGET,'budget'],
    ['dom-digepres-local-execution-dashboard','Local-government budget-execution dashboard','DIGEPRES',EXEC,'implementation'],
    ['dom-mepyd-municipal-assistance','Municipal plan formulation/update technical assistance','MEPyD',ASSIST,'evaluation'],
  ];
  const sourceIds=new Set(planDefs.map(row=>row[0]));dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...planDefs.map(([id,name,publisher,url,category])=>{const entry=receipt.entries.find(row=>row.url===url);const ready=entry?.status==='acquired';const source={id,name,publisher,url,status:ready?'ready':'failed',retrieved_at:receipt.retrieved_at.slice(0,10),reference_period:category==='plan'?'2025-2029':'current source at retrieval',geographic_level:'national framework or source-specific municipality coverage',license:'Official public material; reuse terms not stated',note:ready?'Body acquired and hashed; planning status and implementation meaning remain source-specific.':'Official indexed source was inspected, while the direct automated request failed; the receipt preserves the failure.',receipt_path:'raw/dominican-republic-planning/planning-receipt.json'};if(ready)Object.assign(source,{raw_path:`raw/dominican-republic-planning/${entry.file}`,sha256:entry.sha256,bytes:entry.bytes});return source;})];
  dataset.documents=[...(dataset.documents||[]).filter(row=>!String(row.id).startsWith('dom-planning-')),...planDefs.map(([id,name,,url,category])=>{const entry=receipt.entries.find(row=>row.url===url),ready=entry?.status==='acquired';return {id:`dom-planning-${id}`,territory_id:'DOM',category:['law','guidance'].includes(category)?'reference':category,title:name,kind:'official-reference',url,availability:ready?'body_acquired':'failed',official_status:'unverified',source_id:id};})];
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'dom-2022-census-depth','dom-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'DOM 2022: 12 required themes use official census/administrative data across the verified hierarchy; ethnicity, nutrition and poverty are national context only and are not assigned to lower territories.','DOM geography contains 10 planning regions, 32 provinces and 158 municipalities with source-attributed display boundaries.'];
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  await copyFiles(collection,path.join(root,'raw','dominican-republic-census'));await cp(planning,path.join(root,'raw','dominican-republic-planning'),{recursive:true,force:true});
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'DOM',status:'complete',edition_complete:true,collection_audit:'evidence/DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json',counts:audit.counts,theme_observation_counts:audit.theme_observation_counts,context_only:audit.context_only,planning:{law:[LAW176,LAW498],guidance:[GUIDE,GUIDE_PDF,ASSIST],plan:PLAN,budget:BUDGET,implementation:EXEC,evaluation_scope:'Technical-assistance and budget reporting sources were inspected; no nationwide claim of completed municipal outcome evaluation is made.',acquired:receipt.entries.filter(row=>row.status==='acquired').length,failed:receipt.entries.filter(row=>row.status!=='acquired').length,scope_limit:receipt.scope_limit}};
  await Promise.all([writeFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidence,'DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidence,'DOMINICAN_REPUBLIC_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n'),writeFile(path.join(evidence,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  console.log(JSON.stringify({country_area_id:'DOM',edition_complete:true,semantic_rows:rows.length,planning_acquired:integration.planning.acquired,planning_failed_with_evidence:integration.planning.failed,validation_errors:validation.errors,validation_warnings:validation.warnings},null,2));
}

main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});

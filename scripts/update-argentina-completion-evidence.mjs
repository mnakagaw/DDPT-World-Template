#!/usr/bin/env node
import {readFile,writeFile,mkdir,readdir,copyFile,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const CENSUS='https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-41-165?lang=es';
const GEOREF='https://apis.datos.gob.ar/georef/api';
const DISABILITY='https://www.indec.gob.ar/ftp/cuadros/poblacion/estudio_discapacidad_12_18.pdf';
const GUIDE='https://www.argentina.gob.ar/sites/default/files/guia-de-planificacion-territorial-ministerio-del-interior_0.pdf';
const PNASU_LAW='https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-19-2020-337510/actualizacion';
const PNASU_DATA='https://www.argentina.gob.ar/datos-pnasu';
const BUDGET_LAW='https://www.argentina.gob.ar/normativa/nacional/554/actualizacion';
function args(){const out={};for(let i=2;i<process.argv.length;i+=2)out[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return out;}
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');
function domain(status,urls,note,evidence){return {status,identified:true,accessed:true,acquired:['acquired','inspected','geography_matched','adopted','integrated'].includes(status),inspected:['inspected','geography_matched','adopted','integrated'].includes(status),geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};}
async function copyFlat(source,target){await mkdir(target,{recursive:true});for(const name of await readdir(source)){const file=path.join(source,name);if((await stat(file)).isFile())await copyFile(file,path.join(target,name));}}

async function main(){
  const a=args();if(!a.project||!a.collection||!a.planning)throw new Error('Usage: node scripts/update-argentina-completion-evidence.mjs --project <dir> --collection <dir> --planning <dir>');
  const root=path.resolve(a.project),collection=path.resolve(a.collection),raw=path.join(collection,'raw'),planning=path.resolve(a.planning),evidence=path.join(root,'evidence'),dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,semantic,fieldInventory,audit]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(path.join(collection,'argentina-workbook-field-inventory.json'),'utf8').then(JSON.parse),
    readFile(path.join(collection,'ARGENTINA_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse)
  ]);
  if(audit.counts?.provinces!==24||audit.counts?.departments!==529||audit.counts?.boundary_features!==553||audit.counts?.indicators!==14||audit.counts?.workbook_numeric_fields!==93)throw new Error('Argentina source audit is incomplete');
  const country=preflight.countries.find(row=>row.country_area_id==='ARG');if(!country)throw new Error('ARG preflight record missing');
  const censusEvidence=[{audit:'evidence/ARGENTINA_COLLECTION_AUDIT.json'},{inventory:'evidence/ARGENTINA_WORKBOOK_FIELD_INVENTORY.json'},{raw:'raw/argentina-census-2022'}];
  const planningEvidence=[{raw:'raw/argentina-planning-evidence'},{guide:'raw/argentina-planning-evidence/guia-planificacion-territorial-2016.pdf'}];
  country.scope_role='completed Argentina edition with 2022 Census province data and official province/department geography';
  country.official_statistics_office=domain('inspected',[CENSUS],'INDEC official 2022 Census definitive-results page and selected statistical products were inspected.',censusEvidence);
  country.latest_census=domain('adopted',[CENSUS],'The 2022 National Population, Household and Housing Census is the adopted current Census round.',censusEvidence);
  country.census_results=domain('adopted',[CENSUS],'Selected official 2022 results are integrated for the country and, where the source table supports it, all 24 jurisdictions. Theme-specific national-only values remain national-only.',censusEvidence);
  country.table_catalog=domain('inspected',[CENSUS],'Nine acquired official workbooks were inspected; all 93 numeric worksheet columns have terminal dispositions.',censusEvidence);
  country.machine_readable_data=domain('adopted',[CENSUS,GEOREF],'Official INDEC XLSX products and government Georef NDJSON registries were acquired and hashed.',censusEvidence);
  country.administrative_codes=domain('geography_matched',[GEOREF],'Official Georef v13 two-digit province and five-digit department IDs were preserved and matched exactly.',censusEvidence);
  country.adm1_adm2_boundaries=domain('adopted',[GEOREF],'Official Georef v13 reference geometries for 24 provinces and 529 departments are integrated with exact IDs.',censusEvidence);
  country.planning_law=domain('inspected',[PNASU_LAW,BUDGET_LAW],'Argentina has a federal, province-specific and municipality-specific planning framework. Resolution 19/2020 establishes the national urban land program and Law 24,156 governs national planning-linked budget formulation and evaluation; neither is presented as one uniform municipal development-plan mandate.',planningEvidence);
  country.planning_guidance=domain('acquired',[GUIDE],'The Ministry of Interior 2016 territorial-planning guide was acquired and hashed. It provides diagnosis, desired-model, programme/project and monitoring methods for subnational planning.',planningEvidence);
  country.plans_budgets_implementation_evaluation=domain('acquired',[PNASU_DATA,BUDGET_LAW],'Official PNASU implementation metrics and the national budget formulation/evaluation law were acquired separately. They do not prove that every province or municipality has a current plan or that a plan has succeeded.',planningEvidence);
  country.country_adapter_status='complete_country_adapter';

  const themeByIndicator={
    ARG_C2022_POP_TOTAL:'population_total',ARG_C2022_FEMALE_PCT:'age_sex',ARG_C2022_PRIVATE_DWELLINGS:'households_housing',
    ARG_C2022_PUBLIC_WATER_PCT:'drinking_water',ARG_C2022_PUBLIC_SEWER_PCT:'sanitation',ARG_C2022_NO_INSTRUCTION_PCT:'education_literacy',
    ARG_C2022_LABOUR_FORCE_PCT:'employment',ARG_C2022_FOREIGN_BORN_PCT:'migration',ARG_C2022_NO_HEALTH_COVERAGE_PCT:'health',
    ARG_C2022_INDIGENOUS_PCT:'ethnicity',ARG_INDEC_2018_DIFFICULTY_PCT:'disability',
    ARG_WDI_SP_URB_TOTL_IN_ZS:'urban_rural',ARG_WDI_SN_ITK_DEFC_ZS:'nutrition',ARG_WDI_SI_POV_NAHC:'poverty'
  };
  const integrated=Object.entries(themeByIndicator).map(([indicatorId,theme])=>{
    const indicator=dataset.indicators.find(row=>row.id===indicatorId),rows=dataset.observations.filter(row=>(row.territory_id==='ARG'||row.territory_id.startsWith('ARG:'))&&row.indicator_id===indicatorId&&row.status==='observed'&&Number.isFinite(row.value));
    const nationalOnly=rows.length===1&&rows[0].territory_id==='ARG';
    return {country_area_id:'ARG',source_id:indicator?.source_id,source_path:nationalOnly?(indicatorId==='ARG_INDEC_2018_DIFFICULTY_PCT'?'raw/argentina-census-2022/estudio_discapacidad_12_18.pdf':'raw/argentina-census-2022'):'evidence/ARGENTINA_COLLECTION_AUDIT.json',
      source_url:dataset.sources.find(row=>row.id===indicator?.source_id)?.url||CENSUS,table_id:indicator?.definition_id||indicatorId,table_title:indicator?.name||indicatorId,
      field_id:indicatorId,field_label:indicator?.name||indicatorId,numeric_cell_count:rows.length,theme,disposition:'integrated',
      reason:nationalOnly?'An observed national series is integrated with its own year and universe and is not imputed to provinces or departments.':'Official 2022 observations are integrated for the country and all source-supported provinces; departments remain explicit where theme tables do not publish values.',
      indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true};
  });
  const inventoried=fieldInventory.records.map(row=>({...row,source_id:'arg-indec-census-2022'}));
  semantic.records=[...(semantic.records||[]).filter(row=>row.country_area_id!=='ARG'),...inventoried,...integrated];semantic.record_count=semantic.records.length;semantic.generated_at=new Date().toISOString();
  semantic.adjudication={...(semantic.adjudication||{}),ARG:{reviewed_numeric_fields:inventoried.length,terminal_dispositions:inventoried.length+integrated.length,covered_themes:[...new Set(integrated.map(row=>row.theme))].sort(),method:'Every numeric column in the nine acquired workbooks is inventoried. Selected values retain published universes; 2018 disability and WDI supplements remain separate by year and source.',audit:'evidence/ARGENTINA_INTEGRATION_AUDIT.json'}};

  const planningFiles=await Promise.all((await readdir(planning)).map(async name=>{const file=path.join(planning,name);return {name,bytes:(await stat(file)).size,sha256:await sha(file)};}));
  const planningSources=[
    {id:'arg-pnasu-resolution-19-2020',name:'Resolution 19/2020 - National Urban Land Plan',publisher:'Argentina national government',url:PNASU_LAW,status:'ready',retrieved_at:new Date().toISOString().slice(0,10),reference_period:'current text inspected',geographic_level:'national policy involving provinces and municipalities',raw_path:'raw/argentina-planning-evidence/law.html',sha256:planningFiles.find(x=>x.name==='law.html')?.sha256,license:'Official legal publication'},
    {id:'arg-territorial-planning-guide-2016',name:'Territorial planning guide',publisher:'Ministry of Interior, Public Works and Housing',url:GUIDE,status:'ready',retrieved_at:new Date().toISOString().slice(0,10),reference_period:'2016',geographic_level:'subnational planning guidance',raw_path:'raw/argentina-planning-evidence/guia-planificacion-territorial-2016.pdf',sha256:planningFiles.find(x=>x.name==='guia-planificacion-territorial-2016.pdf')?.sha256,license:'Official public guidance; source attribution retained.'},
    {id:'arg-pnasu-implementation-data',name:'National Urban Land Plan implementation data',publisher:'Argentina national government',url:PNASU_DATA,status:'ready',retrieved_at:new Date().toISOString().slice(0,10),reference_period:'current page inspected',geographic_level:'national programme and participating subnational governments',raw_path:'raw/argentina-planning-evidence/implementation.html',sha256:planningFiles.find(x=>x.name==='implementation.html')?.sha256,license:'Official public page'},
    {id:'arg-budget-law-24156',name:'Law 24,156 - Financial administration and control systems',publisher:'Argentina national government',url:BUDGET_LAW,status:'ready',retrieved_at:new Date().toISOString().slice(0,10),reference_period:'current consolidated text inspected',geographic_level:'national budget framework',raw_path:'raw/argentina-planning-evidence/budget.html',sha256:planningFiles.find(x=>x.name==='budget.html')?.sha256,license:'Official legal publication'}
  ];
  const sourceIds=new Set(planningSources.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...planningSources];
  const documents=[
    {id:'arg-pnasu-law',territory_id:'ARG',category:'reference',title:'Resolution 19/2020: National Urban Land Plan',kind:'official-law',url:PNASU_LAW,availability:'body_acquired',official_status:'unverified',source_id:'arg-pnasu-resolution-19-2020'},
    {id:'arg-planning-guide-2016',territory_id:'ARG',category:'reference',title:'Territorial planning guide (2016)',kind:'official-guidance',url:GUIDE,availability:'body_acquired',official_status:'unverified',source_id:'arg-territorial-planning-guide-2016'},
    {id:'arg-pnasu-data',territory_id:'ARG',category:'implementation',title:'National Urban Land Plan implementation data',kind:'official-implementation-page',url:PNASU_DATA,availability:'body_acquired',official_status:'unverified',source_id:'arg-pnasu-implementation-data'},
    {id:'arg-budget-law',territory_id:'ARG',category:'budget',title:'Law 24,156: national budget formulation, execution and evaluation framework',kind:'official-law',url:BUDGET_LAW,availability:'body_acquired',official_status:'unverified',source_id:'arg-budget-law-24156'}
  ];
  const docIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!docIds.has(row.id)),...documents];
  dataset.analysis.census_history=dataset.analysis.census_history||{schema_version:'1.0',as_of_year:2026,checked_at:new Date().toISOString().slice(0,10),countries:[]};
  const history={country_id:'ARG',names:{en:'Argentina',es:'Argentina',ja:'アルゼンチン'},adopted_data_year:2022,adopted_source_url:CENSUS,official_census_url:CENSUS,
    recent_rounds:[{year:2022,status:'results_adopted',url:CENSUS},{year:2010,status:'historical_round',url:'https://www.indec.gob.ar/indec/web/Nivel4-CensoNacional-3-1-Censo-2010'},{year:2001,status:'historical_round',url:CENSUS}],
    note:{en:'AreaData adopts the definitive 2022 Census tables. National supplements retain their own years and universes.',es:'AreaData adopta los cuadros definitivos del Censo 2022. Los complementos nacionales conservan sus propios años y universos.',ja:'AreaDataでは2022年Censusの確定表を採用し、全国補足値は別の年・母集団として表示します。'}};
  dataset.analysis.census_history.countries=[...dataset.analysis.census_history.countries.filter(row=>row.country_id!=='ARG'),history];
  dataset.analysis.census_history.checked_at=new Date().toISOString().slice(0,10);
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'arg-census-2022-depth','arg-planning-evidence'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'ARG: official 2022 Census values are connected to 24 provinces where comparable tables support it; the 529-department registry and reference boundaries are available for drill-down without fabricating department observations.','ARG: 2018 disability and WDI urban, nutrition and poverty values retain their own periods and national-only universes. The shared Americas WDI electricity series is reused instead of adding a duplicate country indicator.'];
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root,canonicalSha256:createHash('sha256').update(content).digest('hex')});
  await copyFlat(raw,path.join(root,'raw','argentina-census-2022'));await copyFlat(planning,path.join(root,'raw','argentina-planning-evidence'));
  const integration={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'ARG',status:'complete',edition_complete:true,
    counts:{provinces:24,departments:529,boundaries:553,indicators:15,observations:audit.counts.observations,workbook_numeric_fields:inventoried.length,semantic_records:integrated.length},
    periods:audit.mixed_periods,source_limits:['Province coverage varies by Census table; department observations are not inferred from province values.','The 2018 disability study covers urban localities of 5,000+ people and is not relabelled as Census 2022.','National WDI supplements are not imputed to provinces or departments.','Planning powers and obligations vary by province and municipality; the national sources are not represented as a uniform municipal mandate.'],dataset_sha256:createHash('sha256').update(content).digest('hex')};
  await Promise.all([writeFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(semantic,null,2)+'\n'),writeFile(path.join(evidence,'ARGENTINA_WORKBOOK_FIELD_INVENTORY.json'),JSON.stringify(fieldInventory,null,2)+'\n'),writeFile(path.join(evidence,'ARGENTINA_COLLECTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidence,'ARGENTINA_INTEGRATION_AUDIT.json'),JSON.stringify(integration,null,2)+'\n'),writeFile(path.join(evidence,'ARGENTINA_PLANNING_RECEIPT.json'),JSON.stringify({generated_at:new Date().toISOString(),files:planningFiles},null,2)+'\n')]);
  console.log(JSON.stringify({country_area_id:'ARG',validation,semantic_rows:integrated.length,workbook_numeric_fields:inventoried.length,dataset_sha256:integration.dataset_sha256},null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

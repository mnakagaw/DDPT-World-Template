import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const CENSUS='https://censo2024.bcr.gob.sv/';
const GEOPORTAL='https://geoportal.bcr.gob.sv/';
const BOUNDARIES='https://services8.arcgis.com/xSn1Pefr3M9zkw7Z/arcgis/rest/services/Selector_Distritos/FeatureServer/0';
const LAW_PAGE='https://www.asamblea.gob.sv/leyes-y-decretos/view/3896';
const LAW_PDF='https://www.asamblea.gob.sv/sites/default/files/documents/decretos/81D2CE2F-EAF0-48D8-8C7B-10A8C9E84F65.pdf';
const RESTRUCTURING='https://www.asamblea.gob.sv/node/12819';
const MINDEL='https://www.transparencia.gob.sv/perfil/371';
const FISCAL_PORTAL='https://www.transparenciafiscal.gob.sv/ptf/es/PTF2-Gastos.html';
const BUDGET='https://www.transparenciafiscal.gob.sv/downloads/pdf/SumLey2026GC001.pdf';
const IMPLEMENTATION='https://www.transparenciafiscal.gob.sv/ptf/es/PresupuestosPublicos/PresupuestosEjecutados/Anio2025/';
const EVALUATION='https://www.transparenciafiscal.gob.sv/ptf/es/PresupuestosPublicos/ReformadelSistemadePresupuestoPblico/';
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');
const state=(status,note,urls,evidence)=>({status,identified:true,accessed:true,acquired:true,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls,note,evidence});

async function inventoryFiles(root,prefix=''){
  const result={};
  for(const name of await readdir(root)){
    const file=path.join(root,name),info=await stat(file),relative=prefix?`${prefix}/${name}`:name;
    if(info.isDirectory())Object.assign(result,await inventoryFiles(file,relative));
    else result[relative]={sha256:await sha(file),bytes:info.size};
  }
  return result;
}

export async function updateElSalvadorRequiredThemesPlanning({project,censusBundle,censusRaw,planningRaw}={}){
  if(!project||!censusBundle||!censusRaw||!planningRaw)throw new Error('project, censusBundle, censusRaw and planningRaw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),bundlePath=path.resolve(censusBundle),censusRawDir=path.resolve(censusRaw),planningRawDir=path.resolve(planningRaw);
  const [dataset,preflight,inventory,bundle,collectionAudit]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(bundlePath,'utf8').then(JSON.parse),
    readFile(path.join(path.dirname(bundlePath),'EL_SALVADOR_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse)
  ]);
  const counts=collectionAudit?.hierarchy||{};
  if(bundle.country_area_id!=='SLV'||counts.department!==14||counts.municipality!==44||counts.district!==262)throw new Error('El Salvador hierarchy audit is incomplete.');
  if(bundle.indicators?.length!==15||bundle.observations?.length!==4175||bundle.boundaries?.features?.length!==320)throw new Error('El Salvador Census bundle counts are incomplete.');
  if(collectionAudit.indicators?.SLV_C2024_POP_TOTAL?.observed!==321)throw new Error('El Salvador population total is not complete at all adopted geographies.');
  const lowerIds=new Set(dataset.territories.filter(row=>row.country_id==='SLV'&&row.id!=='SLV').map(row=>row.id));
  if(lowerIds.size!==320)throw new Error(`Expected 320 El Salvador lower territories, found ${lowerIds.size}.`);
  for(const iid of bundle.indicators.filter(row=>!row.id.startsWith('SLV_WB_')).map(row=>row.id)){
    const observed=dataset.observations.filter(row=>row.indicator_id===iid&&row.status==='observed');
    if(observed.length!==321)throw new Error(`${iid} is not integrated for all 321 adopted geographies.`);
  }

  const [censusReceipts,planningReceipts]=await Promise.all([inventoryFiles(censusRawDir),inventoryFiles(planningRawDir)]);
  const acquired=(name)=>planningReceipts[name]?{raw_path:`raw/el-salvador-planning/${name}`,...planningReceipts[name]}:{};
  const planningSources=[
    {id:'SLV_PLANNING_MUNICIPAL_CODE',name:'Código Municipal, Decreto Legislativo No. 274',publisher:'Asamblea Legislativa de El Salvador',url:LAW_PDF,status:'ready',retrieved_at:'2026-09-18',reference_period:'consolidated official text inspected 2026-09-18',geographic_level:'44 municipalities',license:'Official legal text',...acquired('municipal-code-decree-274.pdf'),note:'Article 4 assigns municipalities responsibility to prepare, approve and execute local development plans. Articles 72–85 separately regulate the annual municipal budget and execution reporting.'},
    {id:'SLV_PLANNING_RESTRUCTURING',name:'Ley Especial para la Reestructuración Municipal — official legislative summary',publisher:'Asamblea Legislativa de El Salvador',url:RESTRUCTURING,status:'ready',retrieved_at:'2026-09-18',reference_period:'2023 reform effective for the 2024 structure',geographic_level:'44 municipalities and 262 districts',license:'Official legislative publication',...acquired('municipal-restructuring-2023.html'),note:'Official legislative evidence distinguishes 44 municipalities, whose councils and mayors are elected, from 262 districts retained as service and identity subdivisions.'},
    {id:'SLV_PLANNING_MINDEL',name:'Ministerio de Desarrollo Local institutional profile',publisher:'Government of El Salvador transparency portal',url:MINDEL,status:'partial',retrieved_at:'2026-09-18',reference_period:'current institutional location inspected 2026-09-18',geographic_level:'El Salvador',license:'Official government page',note:'The official institutional location is linked. The portal blocked automated acquisition, so no drafting manual or uniform plan cycle is claimed from it.'},
    {id:'SLV_PLANNING_BUDGET_2026',name:'Ley de Presupuesto 2026 — General State Budget summary',publisher:'Ministerio de Hacienda de El Salvador',url:BUDGET,status:'ready',retrieved_at:'2026-09-18',reference_period:'2026',geographic_level:'national budget',license:'Official fiscal publication',...acquired('budget-2026-summary.pdf'),note:'Approved national budget summary. It is fiscal context and is not represented as a municipal development plan.'},
    {id:'SLV_PLANNING_EXECUTION_2025',name:'Presupuestos Ejecutados — 2025',publisher:'Ministerio de Hacienda de El Salvador',url:IMPLEMENTATION,status:'ready',retrieved_at:'2026-09-18',reference_period:'2025',geographic_level:'national public budget execution',license:'Official fiscal portal',...acquired('executed-budget-2025.html'),note:'Official executed-budget catalogue. Budget execution is kept distinct from plan achievement.'},
    {id:'SLV_PLANNING_BUDGET_EVALUATION',name:'Reforma del Sistema de Presupuesto Público',publisher:'Ministerio de Hacienda de El Salvador',url:EVALUATION,status:'ready',retrieved_at:'2026-09-18',reference_period:'current framework inspected 2026-09-18',geographic_level:'national public budgeting system',license:'Official fiscal portal',...acquired('budget-reform-evaluation.html'),note:'Official results-oriented budget reform and evaluation material. It is not reclassified as an independent evaluation of a municipal plan.'},
    {id:'SLV_PLANNING_FISCAL_PORTAL',name:'Portal de Transparencia Fiscal — Gastos',publisher:'Ministerio de Hacienda de El Salvador',url:FISCAL_PORTAL,status:'ready',retrieved_at:'2026-09-18',reference_period:'current portal inspected 2026-09-18',geographic_level:'national public expenditure',license:'Official fiscal portal',...acquired('fiscal-spending-portal.html'),note:'Official expenditure gateway retained as a catalogue for further budget and execution acquisition.'}
  ];
  const planningIds=new Set(planningSources.map(row=>row.id));
  dataset.sources=[...dataset.sources.filter(row=>!planningIds.has(row.id)),...planningSources];
  const documents=[
    {id:'el-salvador-municipal-code',territory_id:'SLV',category:'reference',title:'Código Municipal — Decreto Legislativo No. 274',kind:'official-law',url:LAW_PDF,availability:'body_acquired',official_status:'unverified',source_id:'SLV_PLANNING_MUNICIPAL_CODE'},
    {id:'el-salvador-municipal-restructuring',territory_id:'SLV',category:'reference',title:'44 municipalities and 262 districts — official restructuring summary',kind:'official-reference',url:RESTRUCTURING,period:'2023–2024',availability:'body_acquired',official_status:'unverified',source_id:'SLV_PLANNING_RESTRUCTURING'},
    {id:'el-salvador-budget-2026',territory_id:'SLV',category:'budget',title:'Ley de Presupuesto 2026 — General State Budget summary',kind:'official-budget',url:BUDGET,period:'2026',availability:'body_acquired',official_status:'unverified',source_id:'SLV_PLANNING_BUDGET_2026'},
    {id:'el-salvador-executed-budget-2025',territory_id:'SLV',category:'implementation',title:'Presupuestos Ejecutados — 2025',kind:'official-implementation-catalogue',url:IMPLEMENTATION,period:'2025',availability:'body_acquired',official_status:'unverified',source_id:'SLV_PLANNING_EXECUTION_2025'},
    {id:'el-salvador-budget-reform-evaluation',territory_id:'SLV',category:'evaluation',title:'Reforma del Sistema de Presupuesto Público',kind:'official-evaluation-framework',url:EVALUATION,availability:'body_acquired',official_status:'unverified',source_id:'SLV_PLANNING_BUDGET_EVALUATION'}
  ];
  const documentIds=new Set(documents.map(row=>row.id));
  dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...documents];
  const checkedAt=new Date().toISOString();
  dataset.planning.update={status:'current',message:'Country planning evidence is refreshed independently. Laws, plans, budgets, implementation reports and evaluations retain their own scope and evidence status; missing local documents remain explicit.',checked_at:checkedAt,last_success_at:checkedAt};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'el-salvador-bcr-census-2024-boundaries-planning'])];
  dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),'El Salvador uses the published 2024 Census hierarchy: 14 departments, 44 municipalities and 262 districts. Municipalities are the local planning authorities; districts are retained for within-municipality diagnosis. The national total retains 107,055 people whose residence was not allocated and never distributes them to lower areas.'])];

  const evidence=[{audit:'evidence/EL_SALVADOR_INTEGRATION_AUDIT.json'},{collection_audit:'evidence/EL_SALVADOR_COLLECTION_AUDIT.json'},{raw_path:'raw/el-salvador-census-2024',note:'Official BCR Census tables, World Bank national supplements and official BCR geometry receipts'},{raw_path:'raw/el-salvador-planning',note:'Official municipal law, restructuring and fiscal evidence'}];
  const slv=preflight.countries.find(row=>row.country_area_id==='SLV');if(!slv)throw new Error('SLV preflight row missing.');
  slv.official_statistics_office=state('inspected','The Banco Central de Reserva hosts the 2024 Census portal, downloadable tabulations and official geographic services used by this adapter.',[CENSUS,GEOPORTAL],evidence);
  slv.latest_census=state('adopted','The 2024 VII Population Census and VI Housing Census is adopted for the country, 14 departments, 44 municipalities and 262 districts.',[CENSUS],evidence);
  slv.recent_census_rounds=[{round:'2024',date_text:'2024',year:2024,url:CENSUS,source:'Banco Central de Reserva de El Salvador'},{round:'2007',date_text:'2007',year:2007,url:'https://censo2024.bcr.gob.sv/quienessomos/',source:'Banco Central de Reserva de El Salvador'},{round:'1992',date_text:'1992',year:1992,url:'https://censo2024.bcr.gob.sv/quienessomos/',source:'Banco Central de Reserva de El Salvador'}];
  slv.census_results=state('adopted','Official 2024 tabulations provide all adopted domestic indicators for the country plus 320 named administrative territories. The published national population is preserved; 107,055 unallocated-residence persons are not invented as a territory or spread downward.',[CENSUS,GEOPORTAL],evidence);
  slv.table_catalog=state('inspected','Eighty official Census workbooks were acquired and inspected. Every workbook has a recorded title, dimensions, hash and integrated or not-adopted disposition in the collection audit.',[CENSUS,GEOPORTAL],evidence);
  slv.machine_readable_data=state('adopted','Official XLSX tables were acquired. Fifteen indicators are integrated; domestic indicators use published rows or same-universe source counts, while poverty and undernourishment remain national international references.',[CENSUS],evidence);
  slv.administrative_codes=state('geography_matched','Census department, municipality and district codes match the official BCR selector services exactly for 14, 44 and 262 named territories. Department code 15 residence-not-specified rows are excluded from selectors.',[GEOPORTAL,BOUNDARIES],evidence);
  slv.adm1_adm2_boundaries=state('adopted','Official BCR department, municipality and district FeatureServices were acquired and joined by exact official codes. Selector summary geometries are excluded.',[BOUNDARIES],evidence);
  slv.planning_law=state('inspected','The official Municipal Code assigns municipalities preparation, approval and execution of local development plans and separately establishes annual municipal budgeting and execution reporting. The 2023 reform leaves 44 municipalities and 262 districts.',[LAW_PAGE,LAW_PDF,RESTRUCTURING],evidence);
  slv.planning_guidance=state('inspected','The Municipal Code provides legal responsibilities, budget timing and participatory mechanisms. No single current nationwide municipal drafting manual or uniform development-plan cycle was verified, so none is invented.',[LAW_PDF,MINDEL],evidence);
  slv.plans_budgets_implementation_evaluation=state('inspected','The 2026 national budget, 2025 executed-budget catalogue and results-oriented budget reform material are linked as separate evidence types. Municipality-specific plans, budgets and evaluations still require municipality-by-municipality acquisition.',[BUDGET,IMPLEMENTATION,EVALUATION,FISCAL_PORTAL],evidence);
  slv.scope_role='regional_gateway_member; complete 2024 Census country-department-municipality-district adapter with national poverty/nutrition context and municipal planning-law evidence';
  slv.country_adapter_status='official_2024_census_14_department_44_municipality_262_district_and_planning_evidence_integrated';

  const themeRows=[
    ['population_total','SLV_C2024_POP_TOTAL','Official Census population','Published total population covers the country and every adopted department, municipality and district. The national unallocated-residence residual is not spread to lower areas.'],
    ['age_sex','SLV_C2024_FEMALE_PCT','Female population','Derived from female and total population counts in the same published geography.'],
    ['households_housing','SLV_C2024_AVG_HOUSEHOLD_SIZE','Average persons per household','Published household-size measure at all adopted Census geographies.'],
    ['drinking_water','SLV_C2024_ORGANIZED_WATER_SUPPLY_PCT','Public, community or private-company water supply','This measures the listed supply source and is not relabelled as drinking-water quality.'],
    ['sanitation','SLV_C2024_SANITATION_ACCESS_PCT','Dwellings with a toilet or latrine','Derived from source counts for occupied private dwellings.'],
    ['electricity','SLV_C2024_ELECTRICITY_ACCESS_PCT','Dwellings with an electricity source','Derived from the listed Census electricity sources; unknown and no-electricity responses are not counted as access.'],
    ['education_literacy','SLV_C2024_LITERACY_10PLUS_PCT','Literacy, population age 10+','Uses published age-specific source counts for the age 10+ universe.'],
    ['employment','SLV_C2024_EMPLOYED_EAP_PCT','Employed among economically active population age 10+','Employment and economically active counts share the same geography and universe.'],
    ['disability','SLV_C2024_DISABILITY_3PLUS_PCT','At least one severe activity limitation, age 3+','Retains the Census severe-activity-limitation definition and age 3+ denominator.'],
    ['migration','SLV_C2024_RECENT_MIGRATION_PCT','Living in another municipality or country in May 2019','Known previous-residence responses only; it is not represented as all lifetime migration.'],
    ['urban_rural','SLV_C2024_URBAN_POP_PCT','Urban population','Uses the official 2024 Census urban-rural classification.'],
    ['ethnicity','SLV_C2024_INDIGENOUS_IDENTIFICATION_PCT','Population identifying with an Indigenous people','Retains the Census self-identification question and response universe.'],
    ['health','SLV_C2024_HOUSEHOLD_DEATH_LAST12M_PCT','Households reporting a death in the last 12 months','This is household mortality exposure, not a general health-status or service-access indicator.'],
    ['nutrition','SLV_WB_UNDERNOURISHMENT_PCT','Prevalence of undernourishment','FAO-modeled national reference distributed through the World Bank API; no department, municipality or district value is inferred.'],
    ['poverty','SLV_WB_NATIONAL_POVERTY_HEADCOUNT_PCT','National poverty headcount ratio','World Bank national reference only; no department, municipality or district value is inferred.']
  ];
  const sourceByIndicator=new Map(dataset.indicators.map(row=>[row.id,row.source_id]));
  const newRows=themeRows.map(([theme,indicatorId,title,reason])=>({country_area_id:'SLV',source_id:sourceByIndicator.get(indicatorId),source_path:'evidence/EL_SALVADOR_INTEGRATION_AUDIT.json',source_url:dataset.sources.find(row=>row.id===sourceByIndicator.get(indicatorId))?.url||CENSUS,table_id:indicatorId.startsWith('SLV_WB_')?'World Bank API latest non-null national observation':'BCR 2024 Census tabulations',table_title:title,field_id:indicatorId,field_label:title,numeric_cell_count:dataset.observations.filter(row=>row.indicator_id===indicatorId&&row.status==='observed').length,theme,disposition:'integrated',reason,indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...inventory.records.filter(row=>row.country_area_id!=='SLV'),...newRows];
  inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
  inventory.adjudication={...inventory.adjudication,SLV:{reviewed_numeric_fields:newRows.length,terminal_dispositions:newRows.length,covered_themes:newRows.map(row=>row.theme).sort(),method:'Official 2024 Census totals and same-universe source-count ratios cover the country, 14 departments, 44 municipalities and 262 districts. Poverty and nutrition are explicitly national references only.',audit:'evidence/EL_SALVADOR_INTEGRATION_AUDIT.json'}};

  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'SLV',status:'complete_country_adapter_pending_matrix_rebuild',edition_complete:true,collection_audit:'evidence/EL_SALVADOR_COLLECTION_AUDIT.json',counts:{territories:321,lower_territories:320,departments:14,municipalities:44,districts:262,indicators:15,observations:4175,boundaries:320,source_workbooks:collectionAudit.workbook_inventory.length},population_reconciliation:collectionAudit.unallocated_population,planning:{law:LAW_PDF,restructuring:RESTRUCTURING,budget:BUDGET,implementation:IMPLEMENTATION,evaluation:EVALUATION,scope_limit:'The 44 municipalities are planning authorities. The 262 districts are diagnostic subdivisions. Municipality-specific current plans, budgets and evaluations require separate acquisition and are not inferred from national fiscal sources.'},receipts:{census:censusReceipts,planning:planningReceipts}};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const censusTarget=path.join(root,'raw','el-salvador-census-2024'),planningTarget=path.join(root,'raw','el-salvador-planning');
  await Promise.all([mkdir(censusTarget,{recursive:true}),mkdir(planningTarget,{recursive:true})]);
  await Promise.all([cp(censusRawDir,censusTarget,{recursive:true,force:true}),cp(planningRawDir,planningTarget,{recursive:true,force:true})]);
  dataset.generated_at=new Date().toISOString();
  const content=JSON.stringify(dataset,null,2)+'\n';
  await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([
    writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'EL_SALVADOR_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'EL_SALVADOR_COLLECTION_AUDIT.json'),JSON.stringify(collectionAudit,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')
  ]);
  return {country_area_id:'SLV',territories:321,indicators:15,observations:4175,semantic_rows:newRows.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{
    const args=parseArgs(process.argv.slice(2),['project','census-bundle','census-raw','planning-raw']);
    if(args.help||!args.project||!args['census-bundle']||!args['census-raw']||!args['planning-raw'])console.log('node scripts/update-el-salvador-required-themes-planning.mjs --project <directory> --census-bundle <bundle.json> --census-raw <raw-dir> --planning-raw <raw-dir>');
    else console.log(JSON.stringify(await updateElSalvadorRequiredThemesPlanning({project:args.project,censusBundle:args['census-bundle'],censusRaw:args['census-raw'],planningRaw:args['planning-raw']}),null,2));
  }catch(error){reportError(error);}
}

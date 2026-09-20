import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const ITER='https://www.inegi.org.mx/programas/ccpv/2020/#Datos_abiertos';
const ITER_DOWNLOAD='https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip';
const BOUNDARIES='https://www.inegi.org.mx/servicios/catalogounico.html';
const LAW='https://www.diputados.gob.mx/LeyesBiblio/pdf/LPlan.pdf';
const PND='https://sidof.segob.gob.mx/notas/5755162';
const BUDGET='https://www.pef.hacienda.gob.mx/ae/';
const IMPLEMENTATION='https://www.gob.mx/presidencia/articulos/version-estenografica-primer-informe-de-gobierno-de-la-presidenta-claudia-sheinbaum-pardo-palacio-nacional';
const EVALUATION='https://www.transparenciapresupuestaria.gob.mx/Sistema-Evaluacion-Desempeno';
const CONEVAL='https://www.coneval.org.mx/EvaluacionDS/PP/Programas/Paginas/Evaluacion_Programas.aspx';
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

export async function updateMexicoRequiredThemesPlanning({project,censusBundle,supplementBundle,censusRaw,raw}={}){
  if(!project||!censusBundle||!supplementBundle||!censusRaw||!raw)throw new Error('project, censusBundle, supplementBundle, censusRaw and raw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),censusRawDir=path.resolve(censusRaw),rawDir=path.resolve(raw);
  const [dataset,preflight,inventory,census,supplement]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(path.resolve(censusBundle),'utf8').then(JSON.parse),
    readFile(path.resolve(supplementBundle),'utf8').then(JSON.parse)
  ]);
  if(census.country_area_id!=='MEX'||census.audit?.counts?.municipalities!==2469||census.audit?.locality_reconciliation?.municipalities_exact_to_published_total!==2469)throw new Error('Mexico Census audit is incomplete.');
  if(supplement.country_area_id!=='MEX'||supplement.audit?.counts?.observations!==5004||supplement.audit?.counts?.municipalities!==2469)throw new Error('Mexico CONEVAL supplement audit is incomplete.');
  const censusMunicipalities=new Set(census.territories.filter(row=>row.level==='municipality').map(row=>row.id));
  const supplementMunicipalities=new Set(supplement.observations.filter(row=>row.territory_id.startsWith('MEX:MUN:')).map(row=>row.territory_id));
  if(censusMunicipalities.size!==2469||supplementMunicipalities.size!==2469||[...censusMunicipalities].some(id=>!supplementMunicipalities.has(id)))throw new Error('Mexico Census and CONEVAL municipality codes do not match exactly.');

  const indicatorIds=new Set(supplement.indicators.map(row=>row.id)),sourceIds=new Set(supplement.sources.map(row=>row.id));
  dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...supplement.indicators];
  dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...supplement.sources];
  dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...supplement.observations];
  dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries(supplement.indicators.map(row=>[row.id,'2020']))};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'mexico-inegi-iter-coneval-poverty-and-federal-planning'])];
  dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),'Mexico keeps official 2020 Census observations at country, federal-entity and municipality/territorial-demarcation level. CONEVAL poverty and food-access deprivation retain three explicit n.d. municipality cells. Current December 2025 municipal geometry is display-only and never changes a 2020 observation.'])];

  const [censusReceipts,supplementReceipts]=await Promise.all([inventoryFiles(censusRawDir),inventoryFiles(rawDir)]);
  const acquired=(name)=>supplementReceipts[name]?{raw_path:`raw/mexico-required-themes-planning/${name}`,...supplementReceipts[name]}:{};
  const planningSources=[
    {id:'MEX_PLANNING_LAW',name:'Ley de Planeación',publisher:'Cámara de Diputados del H. Congreso de la Unión',url:LAW,status:'ready',retrieved_at:'2026-09-18',reference_period:'current federal law inspected 2026-09-18',geographic_level:'Federal planning system',license:'Official legal text',note:'Federal national planning law. State and municipal planning obligations also depend on each state constitution and planning/municipal legislation; this source is not represented as one uniform municipal plan rule.'},
    {id:'MEX_PLANNING_PND_2025_2030',name:'Plan Nacional de Desarrollo 2025–2030',publisher:'Diario Oficial de la Federación / Gobierno de México',url:PND,status:'ready',retrieved_at:'2026-09-18',reference_period:'2025–2030',geographic_level:'Mexico',license:'Official publication',...acquired('mexico-pnd-gobmx.html'),note:'Current national plan approved and published in the Diario Oficial. National scope is kept distinct from state and municipal plans.'},
    {id:'MEX_PLANNING_PEF_2026',name:'Presupuesto de Egresos de la Federación 2026',publisher:'Secretaría de Hacienda y Crédito Público',url:BUDGET,status:'ready',retrieved_at:'2026-09-18',reference_period:'2026',geographic_level:'Federal budget',license:'Official publication',...acquired('mexico-pef-2026.html'),note:'Approved federal expenditure budget and linked analytical products. Budget evidence remains separate from plan targets and achieved results.'},
    {id:'MEX_PLANNING_FIRST_REPORT_2025',name:'Primer Informe de Gobierno 2024–2025',publisher:'Presidencia de la República',url:IMPLEMENTATION,status:'ready',retrieved_at:'2026-09-18',reference_period:'2024–2025',geographic_level:'Federal government',license:'Government of Mexico website',...acquired('mexico-first-government-report-gobmx.html'),note:'Government implementation report. Reported achievements are not reclassified as independent evaluation findings.'},
    {id:'MEX_PLANNING_SED',name:'Sistema de Evaluación del Desempeño',publisher:'Secretaría de Hacienda y Crédito Público',url:EVALUATION,status:'ready',retrieved_at:'2026-09-18',reference_period:'current system inspected 2026-09-18',geographic_level:'Federal programs and policies',license:'Government of Mexico website',...acquired('mexico-performance-evaluation-system.html'),note:'Official performance-monitoring and evaluation system, including annual evaluation programs, evaluations and improvement actions.'},
    {id:'MEX_PLANNING_CONEVAL_EVALUATION',name:'Evaluación de programas sociales',publisher:'CONEVAL',url:CONEVAL,status:'ready',retrieved_at:'2026-09-18',reference_period:'current catalogue inspected 2026-09-18',geographic_level:'Federal social programs',license:'Official public information',...acquired('mexico-coneval-evaluation.html'),note:'Official evaluation catalogue for social-development programs; kept separate from government implementation reporting.'}
  ];
  const planningIds=new Set(planningSources.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!planningIds.has(row.id)),...planningSources];
  const documents=[
    {id:'mexico-ley-planeacion',territory_id:'MEX',category:'reference',title:'Ley de Planeación',kind:'official-law',url:LAW,availability:'link_verified',official_status:'unverified',source_id:'MEX_PLANNING_LAW'},
    {id:'mexico-pnd-2025-2030',territory_id:'MEX',category:'plan',title:'Plan Nacional de Desarrollo 2025–2030',kind:'official-plan',url:PND,period:'2025–2030',availability:'body_acquired',official_status:'unverified',source_id:'MEX_PLANNING_PND_2025_2030'},
    {id:'mexico-pef-2026',territory_id:'MEX',category:'budget',title:'Presupuesto de Egresos de la Federación 2026',kind:'official-budget',url:BUDGET,period:'2026',availability:'body_acquired',official_status:'unverified',source_id:'MEX_PLANNING_PEF_2026'},
    {id:'mexico-first-government-report-2025',territory_id:'MEX',category:'implementation',title:'Primer Informe de Gobierno 2024–2025',kind:'official-implementation-report',url:IMPLEMENTATION,period:'2024–2025',availability:'body_acquired',official_status:'unverified',source_id:'MEX_PLANNING_FIRST_REPORT_2025'},
    {id:'mexico-performance-evaluation-system',territory_id:'MEX',category:'evaluation',title:'Sistema de Evaluación del Desempeño',kind:'official-evaluation-system',url:EVALUATION,availability:'body_acquired',official_status:'unverified',source_id:'MEX_PLANNING_SED'}
  ];
  const documentIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...documents];
  const checkedAt=new Date().toISOString();dataset.planning.update={status:'current',message:'Mexico evidence distinguishes the federal planning law, the 2025–2030 national plan, the 2026 federal budget, implementation reporting and evaluation systems. State and municipal plan duties require state-specific legal and document adapters and are not inferred from the federal sources.',checked_at:checkedAt,last_success_at:checkedAt};

  const evidence=[{audit:'evidence/MEXICO_INTEGRATION_AUDIT.json'},{raw_path:'raw/mexico-census-2020',note:'INEGI ITER 2020 and official current boundary API receipts'},{raw_path:'raw/mexico-required-themes-planning',note:'CONEVAL and federal planning evidence'}];
  const mex=preflight.countries.find(row=>row.country_area_id==='MEX');if(!mex)throw new Error('MEX preflight row missing.');
  mex.official_statistics_office=state('inspected','INEGI is the official national statistics and geography institute. Its 2020 Census ITER data and official geography service were acquired and inspected.',['https://www.inegi.org.mx/'],evidence);
  mex.latest_census=state('adopted','The 2020 Censo de Población y Vivienda is the latest completed census adopted here. Official totals are integrated for Mexico, 32 federal entities and all 2,469 municipalities/territorial demarcations.',[ITER],evidence);
  mex.recent_census_rounds=[{round:'2020',date_text:'2–27 March 2020',year:2020,url:ITER,source:'INEGI'},{round:'2010',date_text:'31 May–25 June 2010',year:2010,url:'https://www.inegi.org.mx/programas/ccpv/2010/',source:'INEGI'},{round:'2000',date_text:'7–18 February 2000',year:2000,url:'https://www.inegi.org.mx/programas/ccpv/2000/',source:'INEGI'}];
  mex.census_results=state('adopted','Thirteen ITER indicators are integrated from official total rows. Ratios retain their exact numerator and denominator; suppressed cells remain missing. Urban share excludes duplicate special summary rows and reconciles to every published municipality total.',[ITER],evidence);
  mex.table_catalog=state('inspected','The official ITER 2020 CSV and its data dictionary were inspected. All 286 source columns were inventoried during extraction; the 13 adopted fields and formula inputs are recorded in the integration audit.',[ITER,'https://www.inegi.org.mx/contenidos/programas/ccpv/2020/doc/fd_iter_cpv2020.pdf'],evidence);
  mex.machine_readable_data=state('adopted','The official nationwide ITER CSV was acquired. Published country, state and municipality total rows are used directly; locality rows are used only for the documented urban population derivation.',[ITER_DOWNLOAD],evidence);
  mex.administrative_codes=state('geography_matched','Official CVE_ENT and CVE_MUN codes identify all adopted federal entities and municipalities. The 2020 statistical codes match 2,469 current official geometry records exactly; nine later/current codes are recorded and excluded.',[BOUNDARIES],evidence);
  mex.adm1_adm2_boundaries=state('adopted','INEGI current municipal geometry was acquired from the official catalogue API and joined only on exact 2020 codes. The December 2025 boundary edition is explicitly display-only; it is not represented as the 2020 census boundary.',[BOUNDARIES],evidence);
  mex.planning_law=state('inspected','The federal Ley de Planeación establishes the national democratic planning system and the content and coordination of the national plan. State and municipal duties remain subject to state-specific law and are not generalized here.',[LAW],evidence);
  mex.planning_guidance=state('inspected','The 2025–2030 PND and the federal performance-evaluation system provide the current federal objectives, indicators, monitoring and evaluation framework. Municipal drafting guidance requires a state-specific adapter.',[PND,EVALUATION],evidence);
  mex.plans_budgets_implementation_evaluation=state('inspected','The current PND, 2026 federal budget, 2024–2025 implementation report, SHCP performance-evaluation system and CONEVAL program evaluations are linked as separate evidence types.',[PND,BUDGET,IMPLEMENTATION,EVALUATION,CONEVAL],evidence);
  mex.scope_role='regional_gateway_member; complete 2020 Census country-state-municipality adapter with CONEVAL poverty/nutrition and federal planning evidence';
  mex.country_adapter_status='official_2020_census_32_state_2469_municipality_coneval_and_federal_planning_integrated';

  const themeRows=[
    ['population_total','MEX_C2020_POP_TOTAL','Population, 2020 Census','Published total population is retained for Mexico, every federal entity and every municipality.'],
    ['age_sex','MEX_C2020_FEMALE_PCT','Female population','Derived only from same-row female and total population counts.'],
    ['households_housing','MEX_C2020_AVG_OCCUPANTS','Average occupants per inhabited private dwelling','Exact published ITER housing measure.'],
    ['drinking_water','MEX_C2020_PIPED_WATER_PCT','Dwellings with piped water on the premises','Derived from same-row source counts and the published housing-characteristics denominator.'],
    ['sanitation','MEX_C2020_DRAINAGE_PCT','Dwellings with drainage','Derived from same-row source counts and the published housing-characteristics denominator.'],
    ['electricity','MEX_C2020_ELECTRICITY_PCT','Dwellings with electricity','Derived from same-row source counts and the published housing-characteristics denominator.'],
    ['education_literacy','MEX_C2020_ILLITERACY_15PLUS_PCT','Population age 15+ unable to read and write a message','The age 15+ numerator and denominator are retained.'],
    ['employment','MEX_C2020_EMPLOYED_EAP_PCT','Employed among economically active population age 12+','Employment and economically active population counts share the same source row and universe.'],
    ['disability','MEX_C2020_DISABILITY_PCT','Population with disability','The INEGI functional-difficulty definition is retained and is not harmonized to another disability measure.'],
    ['migration','MEX_C2020_BORN_OTHER_STATE_PCT','Population born in another state','This is an internal-migration measure; its national meaning is kept explicit.'],
    ['urban_rural','MEX_C2020_URBAN_POP_PCT','Population in localities of 2,500 or more inhabitants','Individual locality rows reconcile to all 2,469 municipality totals after duplicate summary rows are excluded.'],
    ['ethnicity','MEX_C2020_INDIGENOUS_LANGUAGE_3PLUS_PCT','Population age 3+ speaking an Indigenous language','The source language measure and age 3+ population are retained.'],
    ['health','MEX_C2020_HEALTH_AFFILIATION_PCT','Population affiliated with health services','The census affiliation measure is retained and not represented as service use or health outcome.'],
    ['nutrition','MEX_CONEVAL_FOOD_ACCESS_DEPRIVATION_PCT_2020','Food-access deprivation','Official CONEVAL 2020 percentages cover every state and all municipalities; three published n.d. municipality cells remain explicit missing.'],
    ['poverty','MEX_CONEVAL_POVERTY_PCT_2020','Population in multidimensional poverty','Official CONEVAL 2020 percentages cover every state and all municipalities; three published n.d. municipality cells remain explicit missing.']
  ];
  const sourceByIndicator=new Map(dataset.indicators.map(row=>[row.id,row.source_id]));
  const newRows=themeRows.map(([theme,indicatorId,title,reason])=>({country_area_id:'MEX',source_id:sourceByIndicator.get(indicatorId),source_path:'evidence/MEXICO_INTEGRATION_AUDIT.json',source_url:dataset.sources.find(row=>row.id===sourceByIndicator.get(indicatorId))?.url||ITER,table_id:indicatorId.startsWith('MEX_CONEVAL')?'CONEVAL municipal poverty statistical annex 2020':'INEGI ITER 2020',table_title:title,field_id:indicatorId,field_label:title,numeric_cell_count:dataset.observations.filter(row=>row.indicator_id===indicatorId&&row.status==='observed').length,theme,disposition:'integrated',reason,indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...inventory.records.filter(row=>row.country_area_id!=='MEX'),...newRows];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();inventory.adjudication={...inventory.adjudication,MEX:{reviewed_numeric_fields:newRows.length,terminal_dispositions:newRows.length,covered_themes:newRows.map(row=>row.theme).sort(),method:'Official 2020 INEGI totals and source-count ratios cover Mexico, 32 federal entities and 2,469 municipalities. CONEVAL poverty and food-access deprivation retain three explicit n.d. municipal cells.',audit:'evidence/MEXICO_INTEGRATION_AUDIT.json'}};

  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'MEX',status:'complete_country_adapter_pending_matrix_rebuild',edition_complete:true,census:census.audit,supplements:supplement.audit,planning:{law:LAW,plan:PND,budget:BUDGET,implementation:IMPLEMENTATION,evaluation:[EVALUATION,CONEVAL],scope_limit:'Federal framework only; state and municipal planning requirements need state-specific law and documents.'},geography_crosswalk:{census_municipality_ids:censusMunicipalities.size,coneval_municipality_ids:supplementMunicipalities.size,exact_match:true},receipts:{census:censusReceipts,supplement_and_planning:supplementReceipts}};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const censusTarget=path.join(root,'raw','mexico-census-2020'),rawTarget=path.join(root,'raw','mexico-required-themes-planning');
  await Promise.all([mkdir(censusTarget,{recursive:true}),mkdir(rawTarget,{recursive:true})]);
  await Promise.all([cp(censusRawDir,censusTarget,{recursive:true,force:true}),cp(rawDir,rawTarget,{recursive:true,force:true})]);
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'MEXICO_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  return {country_area_id:'MEX',census_observations:census.observations.length,supplement_observations:supplement.observations.length,semantic_rows:newRows.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){try{const args=parseArgs(process.argv.slice(2),['project','census-bundle','supplement-bundle','census-raw','raw']);if(args.help||!args.project||!args['census-bundle']||!args['supplement-bundle']||!args['census-raw']||!args.raw)console.log('node scripts/update-mexico-required-themes-planning.mjs --project <directory> --census-bundle <bundle.json> --supplement-bundle <bundle.json> --census-raw <raw-dir> --raw <raw-dir>');else console.log(JSON.stringify(await updateMexicoRequiredThemesPlanning({project:args.project,censusBundle:args['census-bundle'],supplementBundle:args['supplement-bundle'],censusRaw:args['census-raw'],raw:args.raw}),null,2));}catch(error){reportError(error);}}

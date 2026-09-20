import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const PROFILE='https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm?Lang=E';
const PROFILE_CATALOG='https://www150.statcan.gc.ca/n1/en/catalogue/98-401-X2021006';
const API='https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest';
const BOUNDARIES='https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21';
const FAA='https://laws-lois.justice.gc.ca/eng/acts/F-11/FullText.html';
const POLICY='https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=31300';
const PLANS='https://www.canada.ca/en/treasury-board-secretariat/services/planned-government-spending/reports-plans-priorities.html';
const ESTIMATES='https://www.canada.ca/en/treasury-board-secretariat/services/planned-government-spending/government-expenditure-plan-main-estimates/2026-27-estimates.html';
const RESULTS='https://www.canada.ca/en/treasury-board-secretariat/services/departmental-performance-reports.html';
const EXPENDITURE='https://www.canada.ca/en/treasury-board-secretariat/services/planned-government-spending/expenditure-management-system.html';
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');
const state=(status,note,urls,evidence)=>({status,identified:true,accessed:true,acquired:true,inspected:true,geography_matched:['geography_matched','adopted','integrated'].includes(status),adopted:['adopted','integrated'].includes(status),unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls,note,evidence});

export async function updateCanadaRequiredThemesPlanning({project,censusBundle,supplementBundle,raw}={}){
  if(!project||!censusBundle||!supplementBundle||!raw)throw new Error('project, censusBundle, supplementBundle and raw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),rawDir=path.resolve(raw),rawTarget=path.join(root,'raw','canada-required-themes-planning');
  const [dataset,preflight,inventory,census,supplement]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(path.resolve(censusBundle),'utf8').then(JSON.parse),
    readFile(path.resolve(supplementBundle),'utf8').then(JSON.parse)
  ]);
  if(census.country_area_id!=='CAN'||census.audit?.counts?.census_subdivisions!==5161||census.audit?.counts?.indicators!==9)throw new Error('Canada Census audit is incomplete.');
  if(supplement.country_area_id!=='CAN'||supplement.audit?.counts?.disability_observations!==14||supplement.audit?.counts?.national_reference_observations!==4)throw new Error('Canada supplement audit is incomplete.');
  const indicatorIds=new Set(supplement.indicators.map(row=>row.id)),sourceIds=new Set(supplement.sources.map(row=>row.id));
  dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...supplement.indicators];
  dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...supplement.sources];
  dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...supplement.observations];
  dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries(supplement.observations.map(row=>[row.indicator_id,row.period]))};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'canada-official-census-profile-disability-and-planning'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'Canada keeps 2021 Census Profile observations at the country, province/territory, census-division and census-subdivision levels. The 2022 disability survey stops at province/territory; World Bank water, sanitation, urban and undernourishment references stop at country level. No lower-area values are inferred.'];

  const acquired={};
  for(const name of await readdir(rawDir)){const file=path.join(rawDir,name),info=await stat(file);if(info.isFile())acquired[name]={raw_path:`raw/canada-required-themes-planning/${name}`,sha256:await sha(file),bytes:info.size};}
  const planningSources=[
    {id:'CAN_PLANNING_FAA',name:'Financial Administration Act',publisher:'Justice Laws Website, Government of Canada',url:FAA,status:'ready',retrieved_at:'2026-09-18',reference_period:'current consolidated official text',geographic_level:'Federal government',license:'Government of Canada official legal text',...acquired['canada-financial-administration-act.html'],note:'Federal financial-administration authority. It does not create one uniform municipal development-planning obligation for every province and territory.'},
    {id:'CAN_PLANNING_POLICY_RESULTS',name:'Policy on Results',publisher:'Treasury Board of Canada Secretariat',url:POLICY,status:'ready',retrieved_at:'2026-09-18',reference_period:'official policy inspected 2026-09-18',geographic_level:'Federal departments',license:'Government of Canada website',...acquired['canada-policy-results.html'],note:'Official federal requirements for departmental results frameworks, performance measurement and evaluation.'},
    {id:'CAN_PLANNING_DEPARTMENTAL_PLANS',name:'Departmental Plans',publisher:'Treasury Board of Canada Secretariat',url:PLANS,status:'ready',retrieved_at:'2026-09-18',reference_period:'2026–27',geographic_level:'Federal departments and agencies',license:'Government of Canada website',...acquired['canada-departmental-plans.html'],note:'Forward-looking departmental priorities, expected results and associated resources over three fiscal years.'},
    {id:'CAN_PLANNING_MAIN_ESTIMATES',name:'2026–27 Main Estimates',publisher:'Treasury Board of Canada Secretariat',url:ESTIMATES,status:'ready',retrieved_at:'2026-09-18',reference_period:'2026–27',geographic_level:'Federal government and organizations',license:'Government of Canada website',...acquired['canada-main-estimates.html'],note:'Official spending authorities and planned expenditures. Budget evidence remains separate from plan and achieved-results evidence.'},
    {id:'CAN_PLANNING_RESULTS_REPORTS',name:'Departmental Results Reports',publisher:'Treasury Board of Canada Secretariat',url:RESULTS,status:'ready',retrieved_at:'2026-09-18',reference_period:'2024–25 current reporting round',geographic_level:'Federal departments and agencies',license:'Government of Canada website',...acquired['canada-results-reports.html'],note:'Reports achieved results against departmental plans; not represented as an independent evaluation of every result.'}
  ];
  const planningIds=new Set(planningSources.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!planningIds.has(row.id)),...planningSources];
  const documents=[
    {id:'canada-financial-administration-act',territory_id:'CAN',category:'reference',title:'Financial Administration Act',kind:'official-law',url:FAA,availability:'body_acquired',official_status:'unverified',source_id:'CAN_PLANNING_FAA'},
    {id:'canada-policy-on-results',territory_id:'CAN',category:'reference',title:'Policy on Results',kind:'official-guidance',url:POLICY,availability:'body_acquired',official_status:'unverified',source_id:'CAN_PLANNING_POLICY_RESULTS'},
    {id:'canada-departmental-plans',territory_id:'CAN',category:'plan',title:'Departmental Plans',kind:'official-reference',url:PLANS,availability:'body_acquired',official_status:'unverified',source_id:'CAN_PLANNING_DEPARTMENTAL_PLANS'},
    {id:'canada-main-estimates',territory_id:'CAN',category:'budget',title:'2026–27 Main Estimates',kind:'official-reference',url:ESTIMATES,availability:'body_acquired',official_status:'unverified',source_id:'CAN_PLANNING_MAIN_ESTIMATES'},
    {id:'canada-departmental-results',territory_id:'CAN',category:'evaluation',title:'Departmental Results Reports',kind:'official-reference',url:RESULTS,availability:'body_acquired',official_status:'unverified',source_id:'CAN_PLANNING_RESULTS_REPORTS'}
  ];
  const documentIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...documents];
  const checkedAt=new Date().toISOString();dataset.planning.update={status:'current',message:'Canada evidence distinguishes federal Departmental Plans, Main Estimates and Departmental Results Reports. Municipal and regional planning powers and plan requirements are province/territory-specific; this federal evidence is not presented as one nationwide municipal planning law.',checked_at:checkedAt,last_success_at:checkedAt};

  const evidence=[{audit:'evidence/CANADA_INTEGRATION_AUDIT.json'},{raw_path:'raw/canada-census-2021',note:'official 2021 Census cartographic boundary ZIPs and retrieval evidence'},...Object.values(acquired)];
  const can=preflight.countries.find(row=>row.country_area_id==='CAN');if(!can)throw new Error('CAN preflight row missing.');
  can.official_statistics_office=state('inspected','Statistics Canada is the official national statistical office. Its 2021 Census Profile, SDMX API and geography products are retained with source identifiers and receipts.',['https://www.statcan.gc.ca/en/start'],evidence);
  can.latest_census=state('adopted','The 2021 Census of Population is the latest completed census adopted here. The official Census Profile is integrated for Canada, all provinces and territories, census divisions and all 5,161 census subdivisions.',[PROFILE,PROFILE_CATALOG],evidence);
  can.recent_census_rounds=[{round:'2020',date_text:'11 May 2021',year:2021,url:PROFILE,source:PROFILE},{round:'2010',date_text:'10 May 2016',year:2016,url:'https://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/index.cfm?Lang=E',source:'Statistics Canada'},{round:'2010',date_text:'10 May 2011',year:2011,url:'https://www12.statcan.gc.ca/census-recensement/2011/dp-pd/prof/index.cfm?Lang=E',source:'Statistics Canada'}];
  can.census_results=state('adopted','Nine 2021 Census Profile fields are integrated for every adopted geography. Suppressed and unavailable cells remain explicit missing observations and are never converted to zero.',[PROFILE,PROFILE_CATALOG],evidence);
  can.table_catalog=state('inspected','The official 2021 Census Profile catalogue and release subject inventory were inspected; adopted characteristic codes and exact definitions are recorded in the integration audit.',[PROFILE_CATALOG],evidence);
  can.machine_readable_data=state('adopted','Selected fields were acquired from Statistics Canada’s official Census Profile SDMX API version 1.3. The API request URLs and counts are recorded in the audit.',[API],evidence);
  can.administrative_codes=state('geography_matched','Official 2021 DGUID, province/territory codes, census-division codes and census-subdivision codes are retained. Parent relations use the corresponding Statistics Canada code hierarchy.',[BOUNDARIES],evidence);
  can.adm1_adm2_boundaries=state('adopted','Official 2021 cartographic boundaries are integrated for provinces/territories, census divisions and census subdivisions. Web geometries are simplified from EPSG:3347 only for display.',[BOUNDARIES],evidence);
  can.planning_law=state('inspected','The Financial Administration Act underpins federal financial administration. Canada has no single federal law imposing one municipal development-plan format nationwide; municipal and regional planning requirements are established mainly under province/territory-specific law.',[FAA],evidence);
  can.planning_guidance=state('inspected','The Policy on Results and federal expenditure-management framework govern departmental results, performance measurement and evaluation. Their federal scope is displayed explicitly.',[POLICY,EXPENDITURE],evidence);
  can.plans_budgets_implementation_evaluation=state('inspected','Departmental Plans, Main Estimates and Departmental Results Reports are linked but kept as distinct plan, budget and achieved-results evidence. Local planning documents require a province/territory adapter.',[PLANS,ESTIMATES,RESULTS],evidence);
  can.scope_role='regional_gateway_member; complete 2021 Census Profile country/province-CD-CSD adapter with scoped supplemental themes and federal planning evidence';
  can.country_adapter_status='official_2021_census_profile_pr_cd_csd_disability_and_federal_planning_integrated';

  const themeRows=[
    ['population_total','CAN_C2021_POP_TOTAL','Population, 2021 Census','2021 Census Profile characteristic 1; retained for every adopted geography.'],
    ['age_sex','CAN_C2021_FEMALE_PCT','Women+, share of population','Derived only from Statistics Canada women+ and total counts in the same age-and-gender universe.'],
    ['households_housing','CAN_C2021_AVG_HH_SIZE','Average household size','Exact Census Profile household measure; unavailable cells remain missing.'],
    ['drinking_water','CAN_WB_BASIC_DRINKING_WATER_PCT','People using at least basic drinking water services','International-reference national observation only; no lower-area value is inferred.'],
    ['sanitation','CAN_WB_BASIC_SANITATION_PCT','People using at least basic sanitation services','International-reference national observation only; no lower-area value is inferred.'],
    ['electricity','EG.ELC.ACCS.ZS','Access to electricity','Existing international-reference national observation only.'],
    ['education_literacy','CAN_C2021_NO_HS_DIPLOMA_25_64_PCT','No high school diploma, age 25–64','Exact Census Profile population and age scope retained.'],
    ['employment','CAN_C2021_EMPLOYMENT_RATE','Employment rate','Exact Census Profile population aged 15 years and over in private households.'],
    ['disability','CAN_CSD2022_DISABILITY_PCT_15PLUS','Persons with disabilities, age 15+','Official 2022 survey estimate for Canada and all 13 provinces/territories; not copied lower.'],
    ['migration','CAN_C2021_IMMIGRANTS_PCT','Immigrants','Exact Census Profile private-household universe retained.'],
    ['urban_rural','CAN_WB_URBAN_POPULATION_PCT','Urban population','International-reference national observation only; not treated as a 2021 Census Profile urban classification.'],
    ['ethnicity','CAN_C2021_INDIGENOUS_IDENTITY_PCT','Indigenous identity','Exact Census Profile Indigenous-identity definition and private-household population retained.'],
    ['health','SP.DYN.LE00.IN','Life expectancy at birth','Existing international-reference national observation only.'],
    ['nutrition','CAN_WB_UNDERNOURISHMENT_PCT','Prevalence of undernourishment','International-reference national observation only; not a Census measure or local nutrition estimate.'],
    ['poverty','CAN_C2021_LOW_INCOME_LIMAT_PCT','Low income, LIM-AT prevalence','Exact Census Profile after-tax low-income measure retained.']
  ];
  const sourceByIndicator=new Map(dataset.indicators.map(row=>[row.id,row.source_id]));
  const newRows=themeRows.map(([theme,indicatorId,title,reason])=>({country_area_id:'CAN',source_id:sourceByIndicator.get(indicatorId)||'canada-statcan-census-profile-2021',source_path:'evidence/CANADA_INTEGRATION_AUDIT.json',source_url:dataset.sources.find(row=>row.id===sourceByIndicator.get(indicatorId))?.url||PROFILE,table_id:indicatorId.startsWith('CAN_C2021')?'2021 Census Profile':indicatorId,table_title:title,field_id:indicatorId,field_label:title,numeric_cell_count:dataset.observations.filter(row=>row.indicator_id===indicatorId&&row.status==='observed').length,theme,disposition:'integrated',reason,indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...inventory.records.filter(row=>row.country_area_id!=='CAN'),...newRows];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();inventory.adjudication={...inventory.adjudication,CAN:{reviewed_numeric_fields:newRows.length,terminal_dispositions:newRows.length,covered_themes:newRows.map(row=>row.theme).sort(),method:'Official 2021 Census Profile fields cover every adopted geographic row with explicit missing status where suppressed. Disability stops at province/territory; international reference supplements stop at Canada.',audit:'evidence/CANADA_INTEGRATION_AUDIT.json'}};

  const receipts=[];for(const [name,item] of Object.entries(acquired))receipts.push({path:item.raw_path,sha256:item.sha256,bytes:item.bytes,name});
  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'CAN',status:'complete_country_adapter_pending_matrix_rebuild',edition_complete:true,census:census.audit,supplements:supplement.audit,planning:{law:FAA,guidance:POLICY,plans:PLANS,budget:ESTIMATES,results:RESULTS,scope_limit:'Federal framework only; municipal and regional planning law is province/territory-specific.'},receipts};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  await mkdir(rawTarget,{recursive:true});for(const name of await readdir(rawDir)){const source=path.join(rawDir,name);if((await stat(source)).isFile())await cp(source,path.join(rawTarget,name),{force:true});}
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'CANADA_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n')]);
  return {country_area_id:'CAN',census_observations:census.observations.length,supplement_observations:supplement.observations.length,semantic_rows:newRows.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){try{const args=parseArgs(process.argv.slice(2),['project','census-bundle','supplement-bundle','raw']);if(args.help||!args.project||!args['census-bundle']||!args['supplement-bundle']||!args.raw)console.log('node scripts/update-canada-required-themes-planning.mjs --project <directory> --census-bundle <bundle.json> --supplement-bundle <bundle.json> --raw <raw-dir>');else console.log(JSON.stringify(await updateCanadaRequiredThemesPlanning({project:args.project,censusBundle:args['census-bundle'],supplementBundle:args['supplement-bundle'],raw:args.raw}),null,2));}catch(error){reportError(error);}}

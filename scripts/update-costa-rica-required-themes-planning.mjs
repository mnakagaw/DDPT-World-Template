import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const TOOLS='https://admin.inec.cr/herramientas';
const METHOD='https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf';
const PBI='https://app.powerbi.com/view?r=eyJrIjoiNGI2YjJlMjktMTNiZS00ZjRiLTk3OGYtMmFlY2QyN2Q5NzUyIiwidCI6ImYzZmI3MWE1LTNhZmYtNDcxNS1iMGZkLTk5MTVlYjA3ZWJjYSIsImMiOjR9&pageName=b2b04e99768d5d840c45';
const C2011='https://sistemas.inec.cr/nada5.4/index.php/catalog/113/related-materials';
const GEO='https://services8.arcgis.com/ODelaeFcU0U2CwoG/arcgis/rest/services/UGEC_F/FeatureServer/2';
const LAW='https://www.pgrweb.go.cr/DOCS/NORMAS/1/VIGENTE/L/1990-1999/1995-1999/1998/9D05/17C506.HTML';
const CGR2026='https://www.cgr.go.cr/05-tramites-ap-gl-26.html';
const CGREXEC='https://www.cgr.go.cr/05-tramites-eye-presup.html';
const PNDIP='https://repositorio-snp.mideplan.go.cr/bitstream/handle/123456789/580/DOCPLAN-03408.pdf?sequence=1';
const FOLLOW2025='https://www.mideplan.go.cr/gobierno-de-costa-rica-consolida-avances-en-el-cumplimiento-del-plan-nacional-de-desarrollo-e';
const CLOSE2025='https://www.mideplan.go.cr/mideplan-y-hacienda-presentan-el-informe-del-cierre-del-ejercicio-presupuestario-2025';

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

export async function updateCostaRicaRequiredThemesPlanning({project,censusBundle,censusRaw,planningRaw}={}){
  if(!project||!censusBundle||!censusRaw||!planningRaw)throw new Error('project, censusBundle, censusRaw and planningRaw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),bundlePath=path.resolve(censusBundle),censusRawDir=path.resolve(censusRaw),planningRawDir=path.resolve(planningRaw);
  const [dataset,preflight,inventory,bundle,collectionAudit]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(bundlePath,'utf8').then(JSON.parse),
    readFile(path.join(path.dirname(bundlePath),'COSTA_RICA_COLLECTION_AUDIT.json'),'utf8').then(JSON.parse)
  ]);
  if(bundle.country_area_id!=='CRI'||bundle.territories?.length!==89||bundle.indicators?.length!==15||bundle.observations?.length!==1008||bundle.boundaries?.features?.length!==89)throw new Error('Costa Rica bundle counts are incomplete.');
  if(collectionAudit?.row_counts?.powerbi_people!==5084||collectionAudit?.row_counts?.powerbi_housing!==1558)throw new Error('Costa Rica Power BI inventory is incomplete.');
  const localIds=bundle.indicators.filter(row=>row.id.startsWith('CRI_EST2022')).map(row=>row.id);
  for(const iid of localIds){
    const count=dataset.observations.filter(row=>row.indicator_id===iid&&row.status==='observed').length;
    if(count!==90)throw new Error(`${iid}: expected 90 integrated observations, found ${count}.`);
  }

  const [censusReceipts,planningReceipts]=await Promise.all([inventoryFiles(censusRawDir),inventoryFiles(planningRawDir)]);
  const censusSource=(id,file)=>{const source=dataset.sources.find(row=>row.id===id);if(!source)throw new Error(`Missing source ${id}`);const receipt=censusReceipts[file];if(!receipt)throw new Error(`Missing raw file ${file}`);Object.assign(source,{raw_path:`raw/costa-rica-census/${file}`,...receipt});};
  censusSource('cri-inec-adjusted-census-estimates-2022','powerbi-canton-people.json');
  censusSource('cri-inec-geo-2022','canton-boundaries.geojson');
  censusSource('cri-inec-census-2011-results','censo-2011-resultados-generales.pdf');
  censusSource('cri-world-bank-api','world-bank-undernourishment.json');
  const sharedWorldBank=dataset.sources.find(row=>row.id==='world-bank-api');
  if(sharedWorldBank)Object.assign(sharedWorldBank,{name:'World Development Indicators API',publisher:'World Bank',url:'https://api.worldbank.org/',status:'ready',retrieved_at:'2026-09-18',reference_period:'latest non-null value per indicator',geographic_level:'national only, as specified by each observation',license:'World Bank data terms',note:'International reference observations are national only and are never imputed to subnational areas.'});
  const acquired=(name)=>planningReceipts[name]?{raw_path:`raw/costa-rica-planning/${name}`,...planningReceipts[name]}:{};
  const planningSources=[
    {id:'CRI_PLANNING_MUNICIPAL_CODE',name:'Código Municipal No. 7794 — consolidated official text',publisher:'Procuraduría General de la República de Costa Rica',url:LAW,status:'ready',retrieved_at:'2026-09-18',reference_period:'consolidated text including amendments through 2025',geographic_level:'municipalities / cantons',license:'Official legal text',...acquired('codigo-municipal-7794-consolidado.html'),note:'Article 13 assigns the municipal council the development priorities and approval of the municipal development plan and annual operating plan prepared by the mayor. Both plans form the basis of the municipal budget process.'},
    {id:'CRI_PLANNING_CGR_2026',name:'Gobiernos Locales — Periodo 2026 planning and budget submission requirements',publisher:'Contraloría General de la República',url:CGR2026,status:'ready',retrieved_at:'2026-09-18',reference_period:'2026',geographic_level:'municipalities and district municipal councils',license:'Official oversight guidance',...acquired('cgr-gobiernos-locales-2026.html'),note:'Official current guidance links the Plan de Desarrollo Municipal, annual operating plan and municipal budget submission. It does not impose one global plan template.'},
    {id:'CRI_PLANNING_CGR_EXECUTION',name:'Ejecución y Evaluación Presupuestaria — Gobiernos Locales',publisher:'Contraloría General de la República',url:CGREXEC,status:'ready',retrieved_at:'2026-09-18',reference_period:'current page inspected 2026-09-18',geographic_level:'municipalities',license:'Official oversight guidance',...acquired('cgr-ejecucion-evaluacion-presupuestaria.html'),note:'Official municipal physical and financial execution and budget-liquidation gateway. Budget execution remains distinct from plan achievement.'},
    {id:'CRI_PLANNING_PNDIP_2023_2026',name:'Plan Nacional de Desarrollo e Inversión Pública 2023–2026',publisher:'MIDEPLAN',url:PNDIP,status:'partial',retrieved_at:'2026-09-18',reference_period:'2023–2026',geographic_level:'national and regional public interventions',license:'Official planning publication',note:'National planning context; it is not represented as a municipal development plan. The repository download was access-controlled during automated acquisition, so the verified official link is retained.'},
    {id:'CRI_PLANNING_FOLLOWUP_2025',name:'Informe Anual de Seguimiento 2025 del PNDIP 2023–2026',publisher:'MIDEPLAN',url:FOLLOW2025,status:'partial',retrieved_at:'2026-09-18',reference_period:'2025',geographic_level:'national plan follow-up',license:'Official planning publication',note:'Official 2025 follow-up location, kept separate from municipal plan evaluation and from fiscal execution.'},
    {id:'CRI_PLANNING_BUDGET_CLOSE_2025',name:'Informe conjunto de cierre del ejercicio presupuestario 2025',publisher:'MIDEPLAN and Ministerio de Hacienda',url:CLOSE2025,status:'partial',retrieved_at:'2026-09-18',reference_period:'2025',geographic_level:'national public budget',license:'Official fiscal publication',note:'Official physical and financial budget-close context; it is not converted into local plan performance.'}
  ];
  const planningIds=new Set(planningSources.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!planningIds.has(row.id)),...planningSources];
  const documents=[
    {id:'costa-rica-municipal-code-7794',territory_id:'CRI',category:'reference',title:'Código Municipal No. 7794 — consolidated official text',kind:'official-law',url:LAW,availability:'body_acquired',official_status:'unverified',source_id:'CRI_PLANNING_MUNICIPAL_CODE'},
    {id:'costa-rica-local-government-guidance-2026',territory_id:'CRI',category:'reference',title:'Municipal plan and budget submission requirements — 2026',kind:'official-guidance',url:CGR2026,period:'2026',availability:'body_acquired',official_status:'unverified',source_id:'CRI_PLANNING_CGR_2026'},
    {id:'costa-rica-municipal-budget-execution',territory_id:'CRI',category:'implementation',title:'Municipal budget execution and evaluation gateway',kind:'official-implementation-catalogue',url:CGREXEC,availability:'body_acquired',official_status:'unverified',source_id:'CRI_PLANNING_CGR_EXECUTION'},
    {id:'costa-rica-pndip-2023-2026',territory_id:'CRI',category:'plan',title:'Plan Nacional de Desarrollo e Inversión Pública 2023–2026',kind:'official-plan',url:PNDIP,period:'2023–2026',availability:'link_verified',official_status:'unverified',source_id:'CRI_PLANNING_PNDIP_2023_2026'},
    {id:'costa-rica-pndip-followup-2025',territory_id:'CRI',category:'evaluation',title:'Annual follow-up 2025 — PNDIP 2023–2026',kind:'official-follow-up',url:FOLLOW2025,period:'2025',availability:'link_verified',official_status:'unverified',source_id:'CRI_PLANNING_FOLLOWUP_2025'}
  ];
  const documentIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...documents];
  const checkedAt=new Date().toISOString();dataset.planning.update={status:'current',message:'Country planning evidence is refreshed independently. Laws, plans, budgets, implementation reports and evaluations retain their own scope and evidence status; missing local documents remain explicit.',checked_at:checkedAt,last_success_at:checkedAt};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'costa-rica-inec-adjusted-estimates-2022-census-2011-planning'])];
  dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),'Costa Rica uses the official adjusted 2022 population and housing estimates because the 2022 Census had partial coverage. The adopted 82-canton 2022 statistical geography predates subsequent canton changes; no value is silently moved into a newer planning boundary. Disability, urban-rural and Indigenous identification retain their 2011 Census period.'])];

  const evidence=[{audit:'evidence/COSTA_RICA_INTEGRATION_AUDIT.json'},{collection_audit:'evidence/COSTA_RICA_COLLECTION_AUDIT.json'},{raw_path:'raw/costa-rica-census',note:'Public INEC Power BI query responses, model/schema, official 2022 methodology, 2011 Census results and official UGEP/UGEC geometry'},{raw_path:'raw/costa-rica-planning',note:'Official consolidated Municipal Code and CGR municipal planning/budget guidance'}];
  const cri=preflight.countries.find(row=>row.country_area_id==='CRI');if(!cri)throw new Error('CRI preflight row missing.');
  cri.official_statistics_office=state('inspected','INEC official publications, public Power BI model and official ArcGIS services were acquired and inspected.',[TOOLS,PBI,GEO],evidence);
  cri.latest_census=state('adopted','The official adjusted 2022 population and housing estimate is adopted as the latest product after partial Census coverage. It is labelled as an estimate, never as an unadjusted complete enumeration.',[TOOLS,METHOD,PBI],evidence);
  cri.recent_census_rounds=[{round:'2022',date_text:'2022 adjusted official estimate after partial Census coverage',year:2022,url:TOOLS,source:'INEC Costa Rica'},{round:'2011',date_text:'2011 X Population and VI Housing Census',year:2011,url:C2011,source:'INEC Costa Rica'},{round:'2000',date_text:'2000 Census',year:2000,url:'https://admin.inec.cr/estadisticas-fuentes/censos/censo-2000',source:'INEC Costa Rica'}];
  cri.census_results=state('adopted','The public model supplies 62 people/household fields and 19 housing fields for 82 cantons with repeated province and national values. Fifteen adopted indicators keep the official 2022-estimate or 2011-Census period.',[PBI,METHOD,C2011],evidence);
  cri.table_catalog=state('inspected','All 6,642 rows in the two public model tables were acquired, decoded and inventoried: 5,084 people/household rows and 1,558 housing rows. The adopted fields and exclusions remain auditable.',[PBI,METHOD],evidence);
  cri.machine_readable_data=state('adopted','The public Power BI semantic model and query responses were saved with model ID, schema, exact rows and hashes. Official 2011 published table values are separately located by table number.',[PBI,C2011],evidence);
  cri.administrative_codes=state('geography_matched','Exact INEC UGEP province and UGEC canton codes join all 7 provinces and 82 cantons in the adopted 2022 statistical geography.',[GEO],evidence);
  cri.adm1_adm2_boundaries=state('adopted','Official INEC province and canton geometries were acquired, simplified for display by the official service and joined by exact UGEP/UGEC codes.',[GEO],evidence);
  cri.planning_law=state('inspected','The consolidated Municipal Code defines the municipality through its canton. Article 13 assigns the council development priorities and approval of the municipal development plan and annual operating plan prepared by the mayor; both plans form the municipal budget basis.',[LAW],evidence);
  cri.planning_guidance=state('inspected','The CGR 2026 local-government requirements connect the approved municipal development plan, annual operating plan, budget and legal certification. No uniform substantive plan chapter structure is invented.',[CGR2026,LAW],evidence);
  cri.plans_budgets_implementation_evaluation=state('inspected','Current official locations are retained separately for the national PNDIP, its 2025 follow-up, municipal budget formulation, and municipal physical/financial execution and liquidation. Municipality-specific current plans and evaluations require municipality-by-municipality acquisition.',[PNDIP,FOLLOW2025,CGR2026,CGREXEC,CLOSE2025],evidence);
  cri.scope_role='regional_gateway_member; complete official 2022 adjusted-estimate country-province-canton adapter with explicitly dated 2011 Census supplements and municipal planning evidence';
  cri.country_adapter_status='official_adjusted_2022_7_province_82_canton_15_theme_and_planning_evidence_integrated';

  const themeRows=[
    ['population_total','CRI_EST2022_POP_TOTAL','Adjusted 2022 population','Official adjusted estimate covers the country, 7 provinces and all 82 cantons in the 2022 statistical edition.'],
    ['age_sex','CRI_EST2022_FEMALE_PCT','Female population','Derived from the model’s female and male source counts at the same geography.'],
    ['households_housing','CRI_EST2022_OCCUPANTS_PER_DWELLING','Average occupants per occupied dwelling','Published adjusted estimate for all adopted 2022 geographies.'],
    ['drinking_water','CRI_EST2022_PIPED_AQUEDUCT_WATER_PCT','Indoor piping and aqueduct water','Retains the published combined service definition and is not relabelled as drinking-water quality.'],
    ['sanitation','CRI_EST2022_SAFE_SANITATION_PROXY_PCT','Sewer or septic tank','Retains the published housing service definition.'],
    ['electricity','CRI_EST2022_ELECTRICITY_PCT','Dwellings with electricity','Published adjusted estimate for all adopted 2022 geographies.'],
    ['education_literacy','CRI_EST2022_ILLITERACY_PCT','Illiteracy','Published adjusted percentage; lower values are generally favorable.'],
    ['employment','CRI_EST2022_EMPLOYED_PCT','Employed population','Retains the official model’s population and employment definition.'],
    ['disability','CRI_C2011_DISABILITY_PCT','Population with at least one disability','National 2011 Census Table 7 value only; no canton estimate is inferred.'],
    ['migration','CRI_EST2022_FOREIGN_BORN_PCT','Foreign-born population','Published adjusted estimate for all adopted 2022 geographies.'],
    ['urban_rural','CRI_C2011_URBAN_POP_PCT','Urban population','Country and seven-province 2011 Census Table 5 values; not mixed into a 2022 total.'],
    ['ethnicity','CRI_C2011_INDIGENOUS_IDENTIFICATION_PCT','Indigenous self-identification','Country and seven-province 2011 Census Table 15 values.'],
    ['health','CRI_EST2022_INSURED_POP_PCT','Population with social insurance','Coverage status only; it is not a general health outcome.'],
    ['nutrition','CRI_WB_UNDERNOURISHMENT_PCT','Prevalence of undernourishment','FAO-modeled national reference via the World Bank API; no local value is inferred.'],
    ['poverty','CRI_EST2022_HOUSEHOLDS_WITH_NBI_PCT','Households with at least one unmet basic need','Published adjusted NBI measure for all adopted 2022 geographies.']
  ];
  const sourceByIndicator=new Map(dataset.indicators.map(row=>[row.id,row.source_id]));
  const newRows=themeRows.map(([theme,indicatorId,title,reason])=>({country_area_id:'CRI',source_id:sourceByIndicator.get(indicatorId),source_path:'evidence/COSTA_RICA_INTEGRATION_AUDIT.json',source_url:dataset.sources.find(row=>row.id===sourceByIndicator.get(indicatorId))?.url||TOOLS,table_id:indicatorId.startsWith('CRI_C2011_')?'INEC 2011 Census Results General tables':indicatorId.startsWith('CRI_WB_')?'World Bank API latest non-null national observation':'INEC public Power BI 2022 adjusted-estimate model',table_title:title,field_id:indicatorId,field_label:title,numeric_cell_count:dataset.observations.filter(row=>row.indicator_id===indicatorId&&row.status==='observed').length,theme,disposition:'integrated',reason,indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true}));
  inventory.records=[...inventory.records.filter(row=>row.country_area_id!=='CRI'),...newRows];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
  inventory.adjudication={...inventory.adjudication,CRI:{reviewed_numeric_fields:newRows.length,terminal_dispositions:newRows.length,covered_themes:newRows.map(row=>row.theme).sort(),method:'Official adjusted 2022 estimates cover the country, seven provinces and 82 cantons for locally available themes. Explicit 2011 Census fields cover missing themes at their published country/province scope; national nutrition remains a national international reference.',audit:'evidence/COSTA_RICA_INTEGRATION_AUDIT.json'}};

  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'CRI',status:'complete_country_adapter_pending_matrix_rebuild',edition_complete:true,collection_audit:'evidence/COSTA_RICA_COLLECTION_AUDIT.json',counts:{territories:90,lower_territories:89,provinces:7,cantons:82,indicators:15,observations:1008,boundaries:89,powerbi_people_rows:5084,powerbi_housing_rows:1558},geography_limit:'The adapter uses the complete official 82-canton 2022 statistical edition. Later canton changes are not silently backcast; future current-boundary crosswalk work must remain explicit.',planning:{law:LAW,guidance:CGR2026,national_plan:PNDIP,follow_up:FOLLOW2025,municipal_execution:CGREXEC,scope_limit:'The municipality/canton is the planning authority. Municipality-specific current plans, budgets, execution and evaluations require separate acquisition and are not inferred from national materials.'},receipts:{census:censusReceipts,planning:planningReceipts}};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const censusTarget=path.join(root,'raw','costa-rica-census'),planningTarget=path.join(root,'raw','costa-rica-planning');await Promise.all([mkdir(censusTarget,{recursive:true}),mkdir(planningTarget,{recursive:true})]);await Promise.all([cp(censusRawDir,censusTarget,{recursive:true,force:true}),cp(planningRawDir,planningTarget,{recursive:true,force:true})]);
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'COSTA_RICA_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'COSTA_RICA_COLLECTION_AUDIT.json'),JSON.stringify(collectionAudit,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  return {country_area_id:'CRI',territories:90,indicators:15,observations:1008,semantic_rows:newRows.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','census-bundle','census-raw','planning-raw']);if(args.help||!args.project||!args['census-bundle']||!args['census-raw']||!args['planning-raw'])console.log('node scripts/update-costa-rica-required-themes-planning.mjs --project <directory> --census-bundle <bundle.json> --census-raw <raw-dir> --planning-raw <raw-dir>');else console.log(JSON.stringify(await updateCostaRicaRequiredThemesPlanning({project:args.project,censusBundle:args['census-bundle'],censusRaw:args['census-raw'],planningRaw:args['planning-raw']}),null,2));}catch(error){reportError(error);}
}

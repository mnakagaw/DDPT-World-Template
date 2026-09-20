import {cp,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const LAW_RECORD='https://www.congreso.gob.gt/detalle_pdf/decretos/252';
const LAW_PDF='https://www.congreso.gob.gt/assets/uploads/info_legislativo/decretos/12-02.pdf';

export async function updateGuatemalaSupplementEvidence({project,bundle,raw}={}){
  if(!project||!bundle||!raw)throw new Error('project, bundle and raw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),rawTarget=path.join(root,'raw','guatemala-supplements');
  const [dataset,preflight,inventory,depth]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(path.resolve(bundle),'utf8').then(JSON.parse)
  ]);
  if(depth.country_area_id!=='GTM')throw new Error('Bundle must target GTM.');
  const gtm=preflight.countries.find(row=>row.country_area_id==='GTM');if(!gtm)throw new Error('GTM preflight row missing.');
  const audit=depth.audit;if(!audit||audit.counts?.nutrition_municipalities!==340||audit.counts?.poverty_municipalities!==340||audit.counts?.health_source_geographies!==338)throw new Error('Guatemala supplement audit counts are incomplete.');
  const evidence=[{audit:'evidence/GTM_SUPPLEMENT_INTEGRATION_AUDIT.json'},...audit.receipts.map(row=>({source_id:row.source_id,path:`raw/guatemala-supplements/${path.basename(row.path)}`,sha256:row.sha256,bytes:row.bytes}))];
  gtm.semantic_table_column_inventory={...gtm.semantic_table_column_inventory,completion_verified:true,note:'Every inventoried Census field has a terminal disposition. Three separately sourced official local themes were integrated with exact definitions and geography evidence.',evidence};
  gtm.planning_law={status:'inspected',identified:true,accessed:true,acquired:false,inspected:true,geography_matched:false,adopted:false,unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls:[LAW_RECORD,LAW_PDF,'https://www.congreso.gob.gt/buscador_decretos/12-2002'],note:'The official Congress detailed register for Decreto 12-2002 was inspected. It identifies the Código Municipal, issue and publication dates, 178 articles, and scope including municipal planning offices, budgets, comprehensive development and territorial planning, and plan formulation and execution. Congress also lists later amendments, including Decreto 5-2026. Automated acquisition of the PDF body remains blocked, so AreaData does not claim that it holds a current consolidated law text.',evidence:[{official_record:LAW_RECORD,publication_date:'2002-05-13',article_count:178,collector_pdf_status:'access_restricted',amendment_register:'https://www.congreso.gob.gt/buscador_decretos/12-2002'}]};
  gtm.scope_role='regional_gateway_member; official Census 2018 municipality adapter plus official local health, school-height and poverty themes integrated';
  gtm.country_adapter_status='official_census_and_three_supplemental_local_themes_integrated; planning_record_inspected';

  const sourceByIndicator=new Map(depth.indicators.map(row=>[row.id,row.source_id]));
  const rows=[
    {theme:'health',indicator_id:'GTM_MSPAS_CHRONIC_MORBIDITY_CASES_2024',field_id:'Casos',field_label:'Reported chronic-disease morbidity case count',numeric_cell_count:audit.counts.health_source_rows,coverage:audit.counts.health_observed_municipalities,reason:'All 338 municipality geographies present in the official MSPAS 2024 source were reconciled to the adopted hierarchy. The two municipalities with no source row remain missing rather than zero; the value is a case-row total, not persons or prevalence.'},
    {theme:'nutrition',indicator_id:'GTM_SESAN_SCHOOL_STUNTING_PCT_2024',field_id:'Prevalencia de Retardo en Talla (%)',field_label:'Municipal height-for-age stunting prevalence',numeric_cell_count:340,coverage:340,reason:'All 340 municipality codes in the official 2024 school-height Census workbook matched the adopted INE municipality codes. The denominator is first-grade public-school children ages 6y0m to 9y11m, not all children.'},
    {theme:'poverty',indicator_id:'GTM_SEGEPLAN_GENERAL_POVERTY_PCT_2023',field_id:'Incidencia de pobreza general',field_label:'Municipal general poverty incidence',numeric_cell_count:340,coverage:340,reason:'All 340 published SEGEPLAN municipality codes matched the adopted INE hierarchy. The value is a 2023 small-area estimate using ENCOVI 2023 and Census 2018 inputs, not a direct Census count.'}
  ].map(row=>({country_area_id:'GTM',source_id:sourceByIndicator.get(row.indicator_id),source_path:'raw/guatemala-supplements/',source_url:depth.sources.find(source=>source.id===sourceByIndicator.get(row.indicator_id))?.url,table_id:sourceByIndicator.get(row.indicator_id),table_title:depth.sources.find(source=>source.id===sourceByIndicator.get(row.indicator_id))?.name,field_id:row.field_id,field_label:row.field_label,numeric_cell_count:row.numeric_cell_count,theme:row.theme,disposition:'integrated',reason:row.reason,indicator_id:row.indicator_id,coverage_complete:true,country_edition_eligible:true,geography_count:row.coverage}));
  const sourceIds=new Set(rows.map(row=>row.source_id));inventory.records=[...inventory.records.filter(row=>!(row.country_area_id==='GTM'&&sourceIds.has(row.source_id)&&row.disposition==='integrated')),...rows];
  inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();inventory.adjudication={...inventory.adjudication,GTM:{...(inventory.adjudication?.GTM||{}),reviewed_numeric_fields:inventory.records.filter(row=>row.country_area_id==='GTM').length,terminal_dispositions:inventory.records.filter(row=>row.country_area_id==='GTM').length,covered_themes:[...new Set(inventory.records.filter(row=>row.country_area_id==='GTM').map(row=>row.theme))].sort(),method:'Official Census themes plus exact-code SEGEPLAN poverty and SESAN school-height data, and a complete MSPAS source-geography reconciliation. Missing health municipalities remain missing.',audit:'evidence/GTM_SUPPLEMENT_INTEGRATION_AUDIT.json'}};

  const lawDetail=dataset.documents.find(row=>row.id==='gtm-municipal-code-detail');if(lawDetail)lawDetail.availability='link_verified';
  const lawSource=dataset.sources.find(row=>row.id==='GTM_PLANNING_MUNICIPAL_CODE_DETAIL');if(lawSource)lawSource.note='Official Congress decree record inspected for identity, dates, article count and planning scope. The PDF body remains access-restricted; no consolidated-text claim is made.';
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  await mkdir(rawTarget,{recursive:true});await cp(path.resolve(raw),rawTarget,{recursive:true,force:true});
  const now=new Date().toISOString();const auditDoc={...audit,generated_at:now,planning_law_record:{status:'metadata_inspected',url:LAW_RECORD,pdf_url:LAW_PDF,pdf_body_acquired:false,article_count:178,amendments_register:'https://www.congreso.gob.gt/buscador_decretos/12-2002',limitation:'No current consolidated law-body claim is made.'},edition_complete_after_matrix_rebuild:true};
  dataset.generated_at=now;const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([
    writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'GTM_SUPPLEMENT_INTEGRATION_AUDIT.json'),JSON.stringify(auditDoc,null,2)+'\n')
  ]);
  return {country_area_id:'GTM',integrated_theme_rows:rows.length,observations:depth.observations.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','bundle','raw']);if(args.help||!args.project||!args.bundle||!args.raw)console.log('node scripts/update-guatemala-supplement-evidence.mjs --project <directory> --bundle <bundle.json> --raw <raw-dir>');else console.log(JSON.stringify(await updateGuatemalaSupplementEvidence(args),null,2));}catch(error){reportError(error);}
}

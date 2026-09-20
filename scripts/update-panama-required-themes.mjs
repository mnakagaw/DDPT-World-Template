import {cp,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const themeRows={
  PAN_C2023_URBAN_POP_PCT:{theme:'urban_rural',field_id:'R / PAN_C2023_POP_TOTAL',field_label:'Urban-place population as percent of total Census population',coverage:'PAN plus 13 province/comarca, 82 district and 699 corregimiento areas',numeric_cell_count:795},
  PAN_C2023_RECENT_INTERPROVINCIAL_MIGRANTS_2018_2023:{theme:'migration',field_id:'C - Q - R',field_label:'Recent interprovincial migrants, excluding undeclared and foreign previous residence',coverage:'PAN plus all 13 province/comarca areas published by INEC',numeric_cell_count:14},
  PAN_MINSA_UNDER5_MALNUTRITION_PCT_2022:{theme:'nutrition',field_id:'D5',field_label:'National prevalence of malnutrition among children under five',coverage:'National total; health regions deliberately not equated to administrative provinces',numeric_cell_count:1},
  PAN_MIDES_MPI_INCIDENCE_PCT_2023:{theme:'poverty',field_id:'Incidencia (H)',field_label:'Multidimensional poverty incidence by corregimiento',coverage:'All 699 Census 2023 corregimientos; parent values deliberately not inferred',numeric_cell_count:699}
};

export async function updatePanamaRequiredThemes({project,bundle,raw}={}){
  if(!project||!bundle||!raw)throw new Error('project, bundle and raw are required.');
  const root=path.resolve(project),evidenceDir=path.join(root,'evidence'),rawTarget=path.join(root,'raw','panama-required-themes');
  const [dataset,preflight,inventory,depth,baseAudit]=await Promise.all([
    readFile(path.join(root,'data','dashboard.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
    readFile(path.resolve(bundle),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'PAN_INTEGRATION_AUDIT.json'),'utf8').then(JSON.parse)
  ]);
  if(depth.country_area_id!=='PAN')throw new Error('Bundle must target PAN.');
  const expected={urban_observations:795,migration_observations:14,nutrition_observations:1,poverty_observations:699,total_observations:1509};
  for(const [key,value] of Object.entries(expected))if(depth.audit?.counts?.[key]!==value)throw new Error(`Incomplete Panama ${key}: ${depth.audit?.counts?.[key]}/${value}`);
  if(depth.audit?.themes?.urban_rural?.all_hierarchy_totals_reconciled!==true||depth.audit?.themes?.migration?.province_comarca_sum_reconciled!==true||depth.audit?.themes?.poverty?.matched_corregimientos!==699)throw new Error('Panama thematic reconciliation evidence is incomplete.');

  const indicatorIds=new Set(depth.indicators.map(row=>row.id)),sourceIds=new Set(depth.sources.map(row=>row.id));
  dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...depth.indicators];
  dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...depth.sources];
  dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...depth.observations];
  dataset.analysis=dataset.analysis||{};
  dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries(depth.indicators.map(row=>[row.id,depth.observations.find(obs=>obs.indicator_id===row.id)?.period]))};
  dataset.analysis.coverage=dataset.analysis.coverage||{};
  dataset.analysis.coverage.census_theme_country_ids=[...new Set([...(dataset.analysis.coverage.census_theme_country_ids||[]),'PAN'])].sort();
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'pan-official-required-themes'])];
  dataset.collection.notes=[...(dataset.collection.notes||[]),'PAN supplemental official themes retain their published geographies: urban/rural 795 areas; migration 14 country/first-order areas; nutrition country only; poverty 699 corregimientos. No health-region/province substitution or poverty parent inference is made.'];

  const pan=preflight.countries.find(row=>row.country_area_id==='PAN');if(!pan)throw new Error('PAN preflight row missing.');
  const themeEvidence=[{audit:'evidence/PAN_REQUIRED_THEMES_AUDIT.json'},...depth.audit.receipts.map(row=>({label:row.label,path:`raw/panama-required-themes/${path.basename(row.path)}`,sha256:row.sha256,bytes:row.bytes}))];
  pan.semantic_table_column_inventory={status:'inspected',identified:true,accessed:true,acquired:true,inspected:true,geography_matched:true,adopted:true,unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls:depth.sources.map(row=>row.url),note:'All inventoried numeric fields retain terminal dispositions, and every required theme has at least one complete, definition-compatible integrated field at its exact official publication geography.',evidence:themeEvidence};
  pan.scope_role='regional_gateway_member; complete official Census 2023 country adapter with source-faithful supplemental themes and planning evidence';
  pan.country_adapter_status='official_census_2023_depth_required_themes_and_planning_evidence_integrated';

  const sourceById=new Map(depth.sources.map(row=>[row.id,row]));
  const integratedRows=depth.indicators.map(indicator=>{
    const spec=themeRows[indicator.id];if(!spec)throw new Error(`No semantic row specification for ${indicator.id}`);
    return {country_area_id:'PAN',source_id:indicator.source_id,source_path:'raw/panama-required-themes/',source_url:sourceById.get(indicator.source_id)?.url,table_id:indicator.source_id,table_title:sourceById.get(indicator.source_id)?.name,field_id:spec.field_id,field_label:spec.field_label,numeric_cell_count:spec.numeric_cell_count,theme:spec.theme,disposition:'integrated',reason:`Integrated at the exact official publication geography: ${spec.coverage}. Definition, period, denominator and non-transfer to other geographies are recorded on every observation.`,indicator_id:indicator.id,coverage_complete:true,country_edition_eligible:true,geography_coverage:spec.coverage};
  });
  inventory.records=[...inventory.records.filter(row=>!(row.country_area_id==='PAN'&&row.source_id==='pan-country-adapter-gap-register'&&Object.values(themeRows).some(spec=>spec.theme===row.theme))),...integratedRows];
  inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
  inventory.adjudication={...inventory.adjudication,PAN:{...(inventory.adjudication?.PAN||{}),reviewed_numeric_fields:inventory.records.filter(row=>row.country_area_id==='PAN').length,terminal_dispositions:inventory.records.filter(row=>row.country_area_id==='PAN').length,covered_themes:[...new Set(inventory.records.filter(row=>row.country_area_id==='PAN').map(row=>row.theme))].sort(),method:'Official Census tables and supplemental government publications were integrated only at their exact source geographies. All four previously open themes now have complete eligible fields; incompatible extra fields remain explicitly excluded.',audit:'evidence/PAN_REQUIRED_THEMES_AUDIT.json'}};

  const audit={...baseAudit,generated_at:new Date().toISOString(),status:'complete_country_adapter_pending_matrix_rebuild',edition_complete:true,unresolved_required_themes:[],unresolved_domains:[],supplemental_theme_counts:depth.audit.counts,supplemental_theme_geographies:{urban_rural:'country + 13 province/comarca + 82 district + 699 corregimiento',migration:'country + 13 province/comarca',nutrition:'country only',poverty:'699 corregimientos only'},supplemental_evidence_policy:depth.audit.geography_policy,supplemental_audit:'evidence/PAN_REQUIRED_THEMES_AUDIT.json'};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  await mkdir(rawTarget,{recursive:true});
  for(const receipt of depth.audit.receipts)await cp(path.resolve(receipt.path),path.join(rawTarget,path.basename(receipt.path)),{force:true});
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(path.join(root,'data','dashboard.json'),content);await generateSite({dataset,outDir:root});
  await Promise.all([
    writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'PAN_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'PAN_REQUIRED_THEMES_AUDIT.json'),JSON.stringify(depth.audit,null,2)+'\n')
  ]);
  return {country_area_id:'PAN',integrated_theme_rows:integratedRows.length,observations:depth.observations.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','bundle','raw']);if(args.help||!args.project||!args.bundle||!args.raw)console.log('node scripts/update-panama-required-themes.mjs --project <directory> --bundle <bundle.json> --raw <raw-dir>');else console.log(JSON.stringify(await updatePanamaRequiredThemes(args),null,2));}catch(error){reportError(error);}
}

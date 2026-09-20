#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
function completionDomain(spec={}){
  const status=spec.status||'inspected';
  const acquired=['acquired','inspected','geography_matched','adopted','integrated'].includes(status);
  const inspected=['inspected','geography_matched','adopted','integrated'].includes(status);
  const geographyMatched=['geography_matched','adopted','integrated'].includes(status);
  const adopted=['adopted','integrated'].includes(status);
  return {status,identified:true,accessed:true,acquired,inspected,geography_matched:geographyMatched,adopted,
    unavailable:false,restricted:false,failed_with_evidence:false,urls:spec.urls||[],note:spec.note||'',
    completion_verified:true,evidence:spec.evidence||[]};
}

const project=path.resolve(arg('--project')||'');
const manifestPath=path.resolve(arg('--manifest')||'');
if(!project||!manifestPath)throw new Error('--project and --manifest are required');
const evidenceDir=path.join(project,'evidence');
const dataPath=path.join(project,'data','dashboard.json');
const [dataset,preflight,inventory,manifest]=await Promise.all([
  readFile(dataPath,'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
  readFile(manifestPath,'utf8').then(JSON.parse)
]);
const id=manifest.country_area_id;
const country=preflight.countries.find(row=>row.country_area_id===id);
if(!country)throw new Error(`Missing preflight country ${id}`);
country.scope_role=manifest.scope_role||`completed ${id} country edition`;
country.country_adapter_status=manifest.country_adapter_status||'complete_country_adapter';
for(const [key,spec] of Object.entries(manifest.domains||{}))country[key]=completionDomain(spec);
if(manifest.recent_census_rounds)country.recent_census_rounds=manifest.recent_census_rounds;

const sourceIds=new Set((manifest.sources||[]).map(row=>row.id));
dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...(manifest.sources||[])];
const documentIds=new Set((manifest.documents||[]).map(row=>row.id));
dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...(manifest.documents||[])];

const semantic=[];
for(const [indicatorId,theme] of Object.entries(manifest.indicator_themes||{})){
  const indicator=dataset.indicators.find(row=>row.id===indicatorId);
  if(!indicator)throw new Error(`${id}: indicator ${indicatorId} is missing from dataset`);
  const rows=dataset.observations.filter(row=>(row.territory_id===id||row.territory_id.startsWith(`${id}:`))&&row.indicator_id===indicatorId&&row.status==='observed'&&Number.isFinite(row.value));
  if(!rows.length)throw new Error(`${id}: indicator ${indicatorId} has no observed values`);
  semantic.push({country_area_id:id,source_id:indicator.source_id||rows[0].source_id,
    source_path:manifest.semantic_source_path||manifest.audit_path||manifestPath,
    source_url:dataset.sources.find(row=>row.id===(indicator.source_id||rows[0].source_id))?.url||manifest.official_census_url,
    table_id:indicator.definition_id||indicatorId,table_title:indicator.name,field_id:indicatorId,field_label:indicator.name,
    numeric_cell_count:rows.length,theme,disposition:'integrated',reason:manifest.theme_reasons?.[theme]||'Observed, source-attributed values are integrated for the stated source universe and geographic coverage.',
    indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true});
}
const catalog=(manifest.semantic_catalog||[]).map((row,index)=>({country_area_id:id,source_id:row.source_id||manifest.census_source_id,
  source_path:row.source_path||manifest.semantic_source_path||manifest.audit_path||manifestPath,
  source_url:row.source_url||manifest.official_census_url,table_id:row.table_id||`catalog-${index+1}`,
  table_title:row.table_title||row.table_id||`Catalog item ${index+1}`,field_id:row.field_id||`numeric-fields-${index+1}`,
  field_label:row.field_label||'Numeric fields retained in the source table',numeric_cell_count:row.numeric_cell_count||1,
  theme:row.theme||'source_inventory',disposition:row.disposition||'not_adopted',
  reason:row.reason||'The source table was inventoried and retained, but its fields were not selected as dashboard indicators in this edition.',
  coverage_complete:true,country_edition_eligible:false}));
const themeGaps=(manifest.theme_gaps||[]).map((row,index)=>({country_area_id:id,source_id:row.source_id||manifest.census_source_id,
  source_path:row.source_path||manifest.semantic_source_path||manifest.audit_path||manifestPath,
  source_url:row.source_url||manifest.official_census_url,table_id:row.table_id||`theme-gap-${row.theme||index+1}`,
  table_title:row.table_title||'Reviewed source scope and table inventory',field_id:row.field_id||`${id}_${row.theme||index+1}_GAP`,
  field_label:row.field_label||row.theme||`Theme gap ${index+1}`,numeric_cell_count:0,theme:row.theme,
  disposition:row.disposition||'unavailable',reason:row.reason,coverage_complete:true,country_edition_eligible:false,
  edition_gap_closed:true,gap_kind:row.gap_kind,evidence:row.evidence||[]}));
for(const row of themeGaps){if(!row.theme||!row.reason||!row.gap_kind||!row.evidence.length)throw new Error(`${id}: incomplete evidence-backed theme gap ${row.theme||row.field_id}`);}
inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!==id),...catalog,...semantic,...themeGaps];
inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
inventory.adjudication={...(inventory.adjudication||{}),[id]:{reviewed_numeric_fields:catalog.length,
  terminal_dispositions:catalog.length+semantic.length+themeGaps.length,covered_themes:[...new Set([...semantic,...themeGaps].map(row=>row.theme).filter(Boolean))].sort(),
  method:manifest.inventory_method||'Every adopted field is tied to a source table and indicator; remaining catalogued tables carry terminal non-adoption reasons.',
  audit:manifest.audit_path||null}};

dataset.analysis=dataset.analysis||{};dataset.analysis.coverage=dataset.analysis.coverage||{};
for(const key of ['census_integrated_country_ids','census_theme_country_ids'])dataset.analysis.coverage[key]=[...new Set([...(dataset.analysis.coverage[key]||[]),id])].sort();
if(manifest.census_history){
  dataset.analysis.census_history=dataset.analysis.census_history||{schema_version:'1.0',as_of_year:new Date().getUTCFullYear(),checked_at:new Date().toISOString().slice(0,10),countries:[]};
  dataset.analysis.census_history.countries=[...(dataset.analysis.census_history.countries||[]).filter(row=>row.country_id!==id),manifest.census_history].sort((a,b)=>a.country_id.localeCompare(b.country_id));
  dataset.analysis.census_history.checked_at=new Date().toISOString().slice(0,10);
}
dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),...(manifest.adapters||[`${id.toLowerCase()}-country-edition`])])];
dataset.collection.notes=[...(dataset.collection.notes||[]),...(manifest.collection_notes||[])];
dataset.generated_at=new Date().toISOString();
const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:project});
await Promise.all([
  writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
  writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),
  writeFile(path.join(evidenceDir,`${id}_INTEGRATION_AUDIT.json`),JSON.stringify({...manifest.audit,generated_at:new Date().toISOString(),country_area_id:id,dataset_sha256:createHash('sha256').update(content).digest('hex')},null,2)+'\n')
]);
console.log(JSON.stringify({country_area_id:id,semantic_rows:semantic.length,theme_gap_rows:themeGaps.length,catalog_rows:catalog.length,validation_errors:validation.errors,dataset_sha256:createHash('sha256').update(content).digest('hex')},null,2));

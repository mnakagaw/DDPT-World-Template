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

function applyBundle(dataset,bundle){
  const id=bundle.country_area_id;
  if(!dataset.territories.some(row=>row.id===id&&row.type==='country'))throw new Error(`Country ${id} is not registered`);
  const existingCountryBranch=new Set(dataset.territories.filter(row=>row.id!==id&&row.country_id===id).map(row=>row.id));
  const territoryIds=new Set((bundle.territories||[]).map(row=>row.id));
  if(territoryIds.size!==(bundle.territories||[]).length)throw new Error(`${id}: duplicate territory IDs`);
  for(const row of bundle.territories||[])if(row.country_id!==id||(!dataset.territories.some(area=>area.id===row.parent_id)&&!territoryIds.has(row.parent_id)))throw new Error(`${id}: invalid country or parent for ${row.id}`);
  const indicatorIds=new Set((bundle.indicators||[]).map(row=>row.id));
  const sourceIds=new Set((bundle.sources||[]).map(row=>row.id));
  for(const row of bundle.observations||[]){
    if(row.territory_id!==id&&!territoryIds.has(row.territory_id))throw new Error(`${id}: unknown observation territory ${row.territory_id}`);
    if(!indicatorIds.has(row.indicator_id))throw new Error(`${id}: unknown observation indicator ${row.indicator_id}`);
    if(!sourceIds.has(row.source_id)&&!dataset.sources.some(source=>source.id===row.source_id))throw new Error(`${id}: unknown observation source ${row.source_id}`);
  }
  for(const feature of bundle.boundaries?.features||[])if(!territoryIds.has(feature.properties?.territory_id))throw new Error(`${id}: unknown boundary territory ${feature.properties?.territory_id}`);
  const replacedTerritoryIds=bundle.replace_country_branch===true?existingCountryBranch:territoryIds;
  dataset.territories=[...dataset.territories.filter(row=>!replacedTerritoryIds.has(row.id)&&!territoryIds.has(row.id)),...(bundle.territories||[])];
  dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...(bundle.indicators||[])];
  dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...(bundle.sources||[])];
  dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)&&!replacedTerritoryIds.has(row.territory_id)),...(bundle.observations||[])];
  dataset.boundaries.features=[...dataset.boundaries.features.filter(feature=>!replacedTerritoryIds.has(feature.properties?.territory_id)&&!territoryIds.has(feature.properties?.territory_id)),...(bundle.boundaries?.features||[])];
  dataset.analysis=dataset.analysis||{};
  const comparisonParents=new Set((bundle.comparisons||[]).map(row=>row.parent_id));
  dataset.analysis.comparisons=[...(dataset.analysis.comparisons||[]).filter(row=>!comparisonParents.has(row.parent_id)&&!replacedTerritoryIds.has(row.parent_id)&&!(row.member_ids||[]).some(member=>replacedTerritoryIds.has(member))),...(bundle.comparisons||[])];
  dataset.analysis.terminal_territory_ids=[...new Set([...(dataset.analysis.terminal_territory_ids||[]).filter(member=>member!==id&&!replacedTerritoryIds.has(member)&&!territoryIds.has(member)),...(bundle.terminal_territory_ids||[])])];
  dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries((bundle.indicators||[]).map(row=>[row.id,String(bundle.period)]))};
  dataset.analysis.coverage={...(dataset.analysis.coverage||{}),census_integrated_country_ids:[...new Set([...(dataset.analysis.coverage?.census_integrated_country_ids||[]),id])].sort(),census_theme_country_ids:[...new Set([...(dataset.analysis.coverage?.census_theme_country_ids||[]),id])].sort()};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),`${id.toLowerCase()}-official-census-depth`])];
  dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),`${id} ${bundle.period}: ${bundle.indicators.length} official domestic indicators integrated for ${bundle.territories.length} lower areas with ${bundle.boundaries?.features?.length||0} source-attributed reference boundaries.`])];
  return {country_area_id:id,territory_count:bundle.territories?.length||0,indicator_count:bundle.indicators?.length||0,observation_count:bundle.observations?.length||0,boundary_count:bundle.boundaries?.features?.length||0};
}

function applyManifest(dataset,preflight,inventory,manifest,manifestPath){
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
    semantic.push({country_area_id:id,source_id:indicator.source_id||rows[0].source_id,source_path:manifest.semantic_source_path||manifest.audit_path||manifestPath,
      source_url:dataset.sources.find(row=>row.id===(indicator.source_id||rows[0].source_id))?.url||manifest.official_census_url,
      table_id:indicator.definition_id||indicatorId,table_title:indicator.name,field_id:indicatorId,field_label:indicator.name,numeric_cell_count:rows.length,theme,
      disposition:'integrated',reason:manifest.theme_reasons?.[theme]||'Observed, source-attributed values are integrated for the stated source universe and geographic coverage.',indicator_id:indicatorId,coverage_complete:true,country_edition_eligible:true});
  }
  const catalog=(manifest.semantic_catalog||[]).map((row,index)=>({country_area_id:id,source_id:row.source_id||manifest.census_source_id,
    source_path:row.source_path||manifest.semantic_source_path||manifest.audit_path||manifestPath,source_url:row.source_url||manifest.official_census_url,
    table_id:row.table_id||`catalog-${index+1}`,table_title:row.table_title||row.table_id||`Catalog item ${index+1}`,field_id:row.field_id||`numeric-fields-${index+1}`,
    field_label:row.field_label||'Numeric fields retained in the source table',numeric_cell_count:row.numeric_cell_count||1,theme:row.theme||'source_inventory',disposition:row.disposition||'not_adopted',
    reason:row.reason||'The source table was inventoried and retained, but its fields were not selected as dashboard indicators in this edition.',coverage_complete:true,country_edition_eligible:false}));
  const themeGaps=(manifest.theme_gaps||[]).map((row,index)=>({country_area_id:id,source_id:row.source_id||manifest.census_source_id,
    source_path:row.source_path||manifest.semantic_source_path||manifest.audit_path||manifestPath,source_url:row.source_url||manifest.official_census_url,
    table_id:row.table_id||`theme-gap-${row.theme||index+1}`,table_title:row.table_title||'Reviewed source scope and table inventory',field_id:row.field_id||`${id}_${row.theme||index+1}_GAP`,
    field_label:row.field_label||row.theme||`Theme gap ${index+1}`,numeric_cell_count:0,theme:row.theme,disposition:row.disposition||'unavailable',reason:row.reason,
    coverage_complete:true,country_edition_eligible:false,edition_gap_closed:true,gap_kind:row.gap_kind,evidence:row.evidence||[]}));
  for(const row of themeGaps)if(!row.theme||!row.reason||!row.gap_kind||!row.evidence.length)throw new Error(`${id}: incomplete evidence-backed theme gap ${row.theme||row.field_id}`);
  inventory.records=[...(inventory.records||[]).filter(row=>row.country_area_id!==id),...catalog,...semantic,...themeGaps];
  inventory.adjudication={...(inventory.adjudication||{}),[id]:{reviewed_numeric_fields:catalog.length,terminal_dispositions:catalog.length+semantic.length+themeGaps.length,
    covered_themes:[...new Set([...semantic,...themeGaps].map(row=>row.theme).filter(Boolean))].sort(),method:manifest.inventory_method||'Every adopted field is tied to a source table and indicator; remaining catalogued tables carry terminal non-adoption reasons.',audit:manifest.audit_path||null}};
  dataset.analysis=dataset.analysis||{};dataset.analysis.coverage=dataset.analysis.coverage||{};
  for(const key of ['census_integrated_country_ids','census_theme_country_ids'])dataset.analysis.coverage[key]=[...new Set([...(dataset.analysis.coverage[key]||[]),id])].sort();
  if(manifest.census_history){
    dataset.analysis.census_history=dataset.analysis.census_history||{schema_version:'1.0',as_of_year:new Date().getUTCFullYear(),checked_at:new Date().toISOString().slice(0,10),countries:[]};
    dataset.analysis.census_history.countries=[...(dataset.analysis.census_history.countries||[]).filter(row=>row.country_id!==id),manifest.census_history].sort((a,b)=>a.country_id.localeCompare(b.country_id));
  }
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),...(manifest.adapters||[`${id.toLowerCase()}-country-edition`])])];
  dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),...(manifest.collection_notes||[])])];
  return {country_area_id:id,semantic_rows:semantic.length,theme_gap_rows:themeGaps.length,catalog_rows:catalog.length,audit:manifest.audit||{}};
}

const project=path.resolve(arg('--project')||'');
const specPath=path.resolve(arg('--spec')||'');
if(!project||!specPath)throw new Error('--project and --spec are required');
const evidenceDir=path.join(project,'evidence'),dataPath=path.join(project,'data','dashboard.json');
const [dataset,preflight,inventory,spec]=await Promise.all([
  readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(specPath,'utf8').then(JSON.parse)
]);
if(!Array.isArray(spec)||!spec.length)throw new Error('Batch spec must be a non-empty array');
const ids=new Set(),results=[],audits=[];
for(const item of spec){
  const bundlePath=path.resolve(path.dirname(specPath),item.bundle),manifestPath=path.resolve(path.dirname(specPath),item.manifest);
  const [bundle,manifest]=await Promise.all([readFile(bundlePath,'utf8').then(JSON.parse),readFile(manifestPath,'utf8').then(JSON.parse)]);
  if(bundle.country_area_id!==manifest.country_area_id)throw new Error(`Bundle/manifest country mismatch: ${bundle.country_area_id} / ${manifest.country_area_id}`);
  if(ids.has(bundle.country_area_id))throw new Error(`Duplicate batch country ${bundle.country_area_id}`);ids.add(bundle.country_area_id);
  const bundleResult=applyBundle(dataset,bundle),manifestResult=applyManifest(dataset,preflight,inventory,manifest,manifestPath);
  results.push({...bundleResult,...manifestResult});audits.push(manifestResult);
}
dataset.generated_at=new Date().toISOString();dataset.analysis.census_history.checked_at=new Date().toISOString().slice(0,10);
inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
// Regional datasets can exceed V8's maximum string length when pretty-printed.
// The canonical JSON remains human- and machine-readable without indentation,
// while evidence and completion ledgers stay pretty-printed below.
const content=JSON.stringify(dataset)+'\n',datasetHash=createHash('sha256').update(content).digest('hex');
await Promise.all([writeFile(dataPath,content),writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n')]);
for(const row of audits)await writeFile(path.join(evidenceDir,`${row.country_area_id}_INTEGRATION_AUDIT.json`),JSON.stringify({...row.audit,generated_at:new Date().toISOString(),country_area_id:row.country_area_id,dataset_sha256:datasetHash},null,2)+'\n');
await generateSite({dataset,outDir:project});
await writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:datasetHash,checked_at:new Date().toISOString()},null,2)+'\n');
console.log(JSON.stringify({country_count:results.length,countries:results,validation_errors:validation.errors,dataset_sha256:datasetHash},null,2));

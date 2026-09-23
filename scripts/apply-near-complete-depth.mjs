#!/usr/bin/env node
import {access,copyFile,mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
const projectArg=arg('--project');
if(!projectArg)throw new Error('--project is required');
const project=path.resolve(projectArg);
const staging=path.resolve(arg('--staging')||'.work/staging/americas-near-complete-depth');
const dryRun=process.argv.includes('--dry-run');
const packagePath=path.join(staging,'package','near-complete-depth-package.json');
const sha=body=>createHash('sha256').update(body).digest('hex');
const shaFile=async filename=>sha(await readFile(filename));
const readJson=filename=>readFile(filename,'utf8').then(JSON.parse);
const overlay=(baseRows,patchRows,key)=>{
  const rows=new Map((baseRows||[]).map(row=>[key(row),row]));
  for(const row of patchRows||[])rows.set(key(row),row);
  return [...rows.values()];
};
const installedRawPath=row=>{
  const parts=String(row.path).replaceAll('\\','/').split('/');
  if(parts.length<3||parts[0]!=='raw')throw new Error(`Unexpected staging raw path: ${row.path}`);
  return path.join('raw','near-complete-depth',parts[1],...parts.slice(2));
};

const dataPath=path.join(project,'data','dashboard.json');
const semanticPath=path.join(project,'evidence','COUNTRY_SEMANTIC_INVENTORY.json');
const preflightPath=path.join(project,'evidence','SOURCE_PREFLIGHT.json');
const [dataset,semantic,preflight,pkg]=await Promise.all([
  readJson(dataPath),readJson(semanticPath),readJson(preflightPath),readJson(packagePath)
]);
if(!Array.isArray(pkg.sources)||!Array.isArray(pkg.raw_manifest))throw new Error('Invalid near-complete depth package');
if(await shaFile(packagePath)!=='5c0f599b510dba81db1fda72454b722c1595fa0627a6f477a071fe8ad28fc9b8')throw new Error('Unexpected package hash');

for(const row of pkg.raw_manifest){
  const source=path.join(staging,row.path);
  if(await shaFile(source)!==row.sha256)throw new Error(`Staging source hash mismatch: ${row.path}`);
}
const sourceStates=new Set(['ready','partial','failed','unavailable','not_collected']);
const adaptedSources=pkg.sources.map(row=>{
  const source={...row};
  if(Array.isArray(source.sha256)){source.sha256s=source.sha256;delete source.sha256;}
  if(!sourceStates.has(source.status))source.status=source.id==='dom-siuben-disability-low-icv-registry-2026'?'partial':'ready';
  return source;
});
const adaptedIndicators=pkg.indicators.map(row=>({...row,series_family:row.series_family==='administrative_registry'?'administrative':row.series_family}));
dataset.sources=overlay(dataset.sources,adaptedSources,row=>row.id);
dataset.indicators=overlay(dataset.indicators,adaptedIndicators,row=>row.id);
dataset.observations=overlay(dataset.observations,pkg.observations,row=>[row.territory_id,row.indicator_id,row.period,row.source_id].join('|'));
semantic.records=overlay(semantic.records,pkg.semantic_records,row=>[row.country_area_id,row.source_id,row.table_id,row.field_id].join('|'));
semantic.record_count=semantic.records.length;
semantic.generated_at=new Date().toISOString();
for(const patch of pkg.preflight_patches||[]){
  const country=preflight.countries.find(row=>row.country_area_id===patch.country_area_id);
  if(!country)throw new Error(`Preflight country missing: ${patch.country_area_id}`);
  country[patch.domain]=patch.value;
}
dataset.generated_at=new Date().toISOString();
dataset.collection=dataset.collection||{};
dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'near-complete-depth-arg-dom-pry'])];
const validation=validateDataset(dataset);
if(validation.errors.length)throw new Error(validation.errors.join('; '));
const result={
  dry_run:dryRun,countries:['ARG','DOM','PRY'],package_sha256:await shaFile(packagePath),
  source_count:adaptedSources.length,indicator_count:adaptedIndicators.length,
  observation_count:pkg.observations.length,semantic_record_count:pkg.semantic_records.length,
  raw_file_count:pkg.raw_manifest.length,validation_errors:validation.errors,
  validation_warnings:validation.warnings
};
if(dryRun){console.log(JSON.stringify(result,null,2));process.exit(0);}

for(const row of pkg.raw_manifest){
  const source=path.join(staging,row.path),destination=path.join(project,installedRawPath(row));
  await mkdir(path.dirname(destination),{recursive:true});
  await copyFile(source,destination);
  if(await shaFile(destination)!==row.sha256)throw new Error(`Copied source hash mismatch: ${row.path}`);
}
for(const source of adaptedSources)if(source.raw_path)await access(path.join(project,source.raw_path));
const datasetBody=JSON.stringify(dataset)+'\n';
const audit={
  schema_version:'1.0',generated_at:new Date().toISOString(),countries:result.countries,
  package_path:path.relative(process.cwd(),packagePath).replaceAll('\\','/'),
  package_sha256:result.package_sha256,dataset_sha256_before_completion_sync:sha(datasetBody),
  counts:{sources:result.source_count,indicators:result.indicator_count,observations:result.observation_count,semantic_records:result.semantic_record_count,raw_files:result.raw_file_count},
  schema_adaptations:['Multi-file source hashes are retained as sha256s because dataset source sha256 is singular.','ready_from_existing_raw_inventory is represented as partial.','administrative_registry is represented by the schema 0.2 series_family administrative.'],
  caveats:pkg.caveats||[],validation
};
await Promise.all([
  writeFile(dataPath,datasetBody),
  writeFile(semanticPath,JSON.stringify(semantic,null,2)+'\n'),
  writeFile(preflightPath,JSON.stringify(preflight,null,2)+'\n'),
  writeFile(path.join(project,'evidence','NEAR_COMPLETE_DEPTH_ADJUDICATION.json'),JSON.stringify({schema_version:'1.0',generated_at:pkg.generated_at,scope:pkg.scope,records:pkg.adjudication},null,2)+'\n'),
  writeFile(path.join(project,'evidence','NEAR_COMPLETE_DEPTH_ADOPTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n')
]);
result.dataset_sha256_before_completion_sync=audit.dataset_sha256_before_completion_sync;
console.log(JSON.stringify(result,null,2));

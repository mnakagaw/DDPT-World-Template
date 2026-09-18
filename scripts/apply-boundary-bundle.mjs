#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
const project=path.resolve(arg('--project')||''),bundlePath=path.resolve(arg('--bundle')||'');
if(!project||!bundlePath)throw new Error('--project and --bundle are required');
const dataPath=path.join(project,'data','dashboard.json'),dataset=JSON.parse(await readFile(dataPath,'utf8')),bundle=JSON.parse(await readFile(bundlePath,'utf8'));
const territoryIds=new Set(dataset.territories.map(row=>row.id)),bundleIds=new Set();
for(const feature of bundle.features||[]){const id=feature.properties?.territory_id;if(!territoryIds.has(id))throw new Error(`Unknown territory in boundary bundle: ${id}`);if(bundleIds.has(id))throw new Error(`Duplicate boundary bundle territory: ${id}`);bundleIds.add(id);}
dataset.boundaries.features=[...dataset.boundaries.features.filter(feature=>!bundleIds.has(feature.properties?.territory_id)),...(bundle.features||[])];
const featureById=new Map((bundle.features||[]).map(feature=>[feature.properties?.territory_id,feature]));
if(Array.isArray(bundle.territory_updates)&&bundle.territory_updates.length){
  const updates=new Map(bundle.territory_updates.map(row=>[row.id,row]));
  for(const id of updates.keys())if(!territoryIds.has(id))throw new Error(`Unknown territory update: ${id}`);
  dataset.territories=dataset.territories.map(row=>updates.has(row.id)?{...row,...updates.get(row.id)}:row);
}
dataset.territories=dataset.territories.map(row=>{
  const feature=featureById.get(row.id);if(!feature)return row;
  const properties=feature.properties||{};
  return {...row,boundary_version:properties.geometry_edition||row.boundary_version,geography_note:`${properties.join_method}. The polygon is a source-attributed reference boundary${properties.reference_only?' and is not a legal-boundary certification':''}.`};
});
if(Array.isArray(dataset.analysis?.comparisons))dataset.analysis.comparisons=dataset.analysis.comparisons.map(comparison=>{
  if(!comparison.member_ids?.length||!comparison.member_ids.every(id=>bundleIds.has(id)))return comparison;
  const note=String(comparison.membership_note||'').replace(/\s*polygon boundaries are not yet joined\.?/i,'').replace(/\s*polygon edition remains unverified\.?/i,'').trim();
  return {...comparison,membership_note:`${note} Official ${bundle.source.publisher} reference polygons are joined to every member by exact numeric code; reuse terms and legal-boundary status remain separate.`,source_ids:[...new Set([...(comparison.source_ids||[]),bundle.source.id])]};
});
dataset.sources=[...dataset.sources.filter(source=>source.id!==bundle.source.id),bundle.source];
dataset.generated_at=new Date().toISOString();
dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),`${bundle.country_area_id.toLowerCase()}-official-boundaries`])];
dataset.collection.notes=[...(dataset.collection.notes||[]),`${bundle.country_area_id}: ${bundle.feature_count} official planning GeoServer features joined to Census geography by exact codes.`];
const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:project});
await writeFile(path.join(project,'evidence','validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
console.log(JSON.stringify({country_area_id:bundle.country_area_id,feature_count:bundle.feature_count,dataset_boundary_count:dataset.boundaries.features.length,validation_errors:validation.errors},null,2));

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
if(!dataset.territories.some(row=>row.id===bundle.country_area_id&&row.type==='country'))throw new Error(`Country ${bundle.country_area_id} is not registered`);
const existingCountryBranch=new Set(dataset.territories.filter(row=>row.id!==bundle.country_area_id&&row.country_id===bundle.country_area_id).map(row=>row.id));
const territoryIds=new Set((bundle.territories||[]).map(row=>row.id));if(territoryIds.size!==(bundle.territories||[]).length)throw new Error('Duplicate territory IDs in country-depth bundle');
for(const row of bundle.territories||[])if(row.country_id!==bundle.country_area_id||(!dataset.territories.some(area=>area.id===row.parent_id)&&!territoryIds.has(row.parent_id)))throw new Error(`Invalid country or parent for ${row.id}`);
const indicatorIds=new Set((bundle.indicators||[]).map(row=>row.id)),sourceIds=new Set((bundle.sources||[]).map(row=>row.id));
for(const row of bundle.observations||[])if(row.territory_id!==bundle.country_area_id&&!territoryIds.has(row.territory_id))throw new Error(`Unknown observation territory ${row.territory_id}`);
for(const feature of bundle.boundaries?.features||[])if(!territoryIds.has(feature.properties?.territory_id))throw new Error(`Unknown boundary territory ${feature.properties?.territory_id}`);
const replacedTerritoryIds=bundle.replace_country_branch===true?existingCountryBranch:territoryIds;
dataset.territories=[...dataset.territories.filter(row=>!replacedTerritoryIds.has(row.id)&&!territoryIds.has(row.id)),...(bundle.territories||[])];
dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...(bundle.indicators||[])];
dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...(bundle.sources||[])];
dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)&&!replacedTerritoryIds.has(row.territory_id)),...(bundle.observations||[])];
dataset.boundaries.features=[...dataset.boundaries.features.filter(feature=>!replacedTerritoryIds.has(feature.properties?.territory_id)&&!territoryIds.has(feature.properties?.territory_id)),...(bundle.boundaries?.features||[])];
dataset.analysis=dataset.analysis||{};
const comparisonParents=new Set((bundle.comparisons||[]).map(row=>row.parent_id));dataset.analysis.comparisons=[...(dataset.analysis.comparisons||[]).filter(row=>!comparisonParents.has(row.parent_id)&&!replacedTerritoryIds.has(row.parent_id)&&!(row.member_ids||[]).some(id=>replacedTerritoryIds.has(id))),...(bundle.comparisons||[])];
dataset.analysis.terminal_territory_ids=[...new Set([...(dataset.analysis.terminal_territory_ids||[]).filter(id=>id!==bundle.country_area_id&&!replacedTerritoryIds.has(id)&&!territoryIds.has(id)),...(bundle.terminal_territory_ids||[])])];
dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries((bundle.indicators||[]).map(row=>[row.id,String(bundle.period)]))};
dataset.analysis.coverage={...(dataset.analysis.coverage||{}),census_integrated_country_ids:[...new Set([...(dataset.analysis.coverage?.census_integrated_country_ids||[]),bundle.country_area_id])].sort(),census_theme_country_ids:[...new Set([...(dataset.analysis.coverage?.census_theme_country_ids||[]),bundle.country_area_id])].sort()};
dataset.generated_at=new Date().toISOString();dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),`${bundle.country_area_id.toLowerCase()}-official-census-depth`])];dataset.collection.notes=[...(dataset.collection.notes||[]),`${bundle.country_area_id} ${bundle.period}: ${bundle.indicators.length} official domestic indicators integrated for ${bundle.territories.length} lower areas with ${bundle.boundaries?.features?.length||0} source-attributed reference boundaries.`];
const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:project});
await writeFile(path.join(project,'evidence','validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
console.log(JSON.stringify({country_area_id:bundle.country_area_id,territory_count:bundle.territories.length,indicator_count:bundle.indicators.length,observation_count:bundle.observations.length,boundary_count:bundle.boundaries?.features?.length||0,validation_errors:validation.errors},null,2));

#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
const project=path.resolve(arg('--project')||'');
const bundlePath=path.resolve(arg('--bundle')||'');
if(!project||!bundlePath)throw new Error('--project and --bundle are required');
const dataPath=path.join(project,'data','dashboard.json');
const dataset=JSON.parse(await readFile(dataPath,'utf8'));
const bundle=JSON.parse(await readFile(bundlePath,'utf8'));
const territoryIds=new Set(dataset.territories.map(row=>row.id));
for(const row of bundle.observations||[])if(!territoryIds.has(row.territory_id))throw new Error(`Unknown territory in theme bundle: ${row.territory_id}`);
const indicatorIds=new Set((bundle.indicators||[]).map(row=>row.id));
const sourceIds=new Set((bundle.sources||[]).map(row=>row.id));
dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...(bundle.indicators||[])];
dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...(bundle.sources||[])];
dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...(bundle.observations||[])];
dataset.analysis=dataset.analysis||{};
dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries((bundle.indicators||[]).map(row=>[row.id,String(bundle.period)]))};
dataset.generated_at=new Date().toISOString();
dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),`${bundle.country_area_id.toLowerCase()}-census-theme-bundle`])];
dataset.collection.notes=[...(dataset.collection.notes||[]),`${bundle.country_area_id} ${bundle.period}: ${bundle.indicators.length} reviewed Census indicators added at national, first-order and municipality levels; AreaData ratios retain formula, numerator and denominator.`];
dataset.analysis.coverage={...(dataset.analysis.coverage||{}),census_theme_country_ids:[...new Set([...(dataset.analysis.coverage?.census_theme_country_ids||[]),bundle.country_area_id])].sort()};
const validation=validateDataset(dataset);
if(validation.errors.length)throw new Error(validation.errors.join('; '));
const content=JSON.stringify(dataset,null,2)+'\n';
await writeFile(dataPath,content);
await generateSite({dataset,outDir:project});
await writeFile(path.join(project,'evidence','validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
console.log(JSON.stringify({country_area_id:bundle.country_area_id,indicator_count:bundle.indicators.length,observation_count:bundle.observations.length,dataset_indicator_count:dataset.indicators.length,dataset_observation_count:dataset.observations.length,validation_errors:validation.errors},null,2));

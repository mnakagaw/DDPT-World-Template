#!/usr/bin/env node
// Replay every newly adopted Philippine POPCEN cell from saved official API bytes.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const root=join(project,'raw','popcen-catalogue-2024');
const parse=bytes=>JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const dataBytes=await readFile(join(project,'data','dashboard.json'));
const data=parse(dataBytes),receipt=parse(await readFile(join(root,'receipt.json')));
const parameters=new Map([
  ['PHL_POPCEN_2024_HOUSEHOLD_POP','1'],['PHL_POPCEN_2024_HOUSEHOLDS','2'],
  ['PHL_POPCEN_2024_URBAN_POP','1'],['PHL_POPCEN_2024_PERCENT_URBAN','2'],
  ['PHL_POPCEN_LAND_AREA_KM2','3'],['PHL_POPCEN_2024_DENSITY','6'],
  ['PHL_POPCEN_2020_2024_ANNUAL_GROWTH','7']
]);
const replayed=new Map();
const adoptedTableIds=new Set(data.observations.map(row=>row.source_table_id).filter(Boolean));
for(const table of receipt.tables){
  if(!adoptedTableIds.has(table.id))continue;
  const entries=new Map();
  for(const slice of table.slices){
    const bytes=await readFile(join(root,slice.file));
    if(sha(bytes)!==slice.sha256)throw Error('Changed official response: '+slice.file);
    for(const row of parse(bytes).data){
      const code=row.key[0],param=row.key[1];
      if(entries.has(code+'|'+param))throw Error('Duplicate source cell '+table.id+'/'+code+'/'+param);
      entries.set(code+'|'+param,Number(row.values[0]));
    }
  }
  replayed.set(table.id,entries);
}
const counts={},mismatches=[];
for(const row of data.observations){
  if(!row.source_table_id)continue;
  const parameter=parameters.get(row.indicator_id);
  const code=row.source_geography_code;
  const source=replayed.get(row.source_table_id);
  if(!parameter||!source||!/^\d{10}$/.test(code))throw Error('Unmapped adopted source cell '+row.indicator_id);
  const expected=source.get(code+'|'+parameter);
  counts[row.indicator_id]=(counts[row.indicator_id]||0)+1;
  if(expected!==row.value)mismatches.push({territory_id:row.territory_id,indicator_id:row.indicator_id,
    source_table_id:row.source_table_id,source_code:code,expected,adopted:row.value});
}
const expected={
  PHL_POPCEN_2024_HOUSEHOLD_POP:1742,PHL_POPCEN_2024_HOUSEHOLDS:1742,
  PHL_POPCEN_2024_URBAN_POP:1743,PHL_POPCEN_2024_PERCENT_URBAN:1743,
  PHL_POPCEN_LAND_AREA_KM2:1743,PHL_POPCEN_2024_DENSITY:1743,
  PHL_POPCEN_2020_2024_ANNUAL_GROWTH:1743
};
for(const [id,count] of Object.entries(expected))if(counts[id]!==count)throw Error('Incomplete source replay '+id+' '+counts[id]+'/'+count);
const result={dataset_sha256:sha(dataBytes),catalogue_sha256:receipt.catalogue_sha256,
  verified_source_cells:Object.values(counts).reduce((a,b)=>a+b,0),counts,mismatches:mismatches.slice(0,50),
  mismatch_count:mismatches.length,source_table_count:receipt.tables.length};
await writeFile(join(project,'evidence','PHL_POPCEN_ADOPTION_REPLAY.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
if(mismatches.length)process.exitCode=1;

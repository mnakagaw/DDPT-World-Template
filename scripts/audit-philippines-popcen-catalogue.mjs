#!/usr/bin/env node
// Compare every adopted 2024 POPCEN count with archived official PSA OpenSTAT tables.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw','popcen-catalogue-2024');
const readJson=async path=>JSON.parse((await readFile(path,'utf8')).replace(/^\uFEFF/,''));
const receipt=await readJson(join(raw,'receipt.json'));
const data=await readJson(join(project,'data','dashboard.json'));
if(receipt.tables.length!==24||data.country?.id!=='PHL')throw Error('Wrong catalogue or country');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const sourceMaps=new Map();
for(const table of receipt.tables){
  const maps=[];
  for(const slice of table.slices){
    const bytes=await readFile(join(raw,slice.file));
    if(sha(bytes)!==slice.sha256)throw Error('Changed archived response '+slice.file);
    const parsed=JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
    if(parsed.data.length!==slice.rows)throw Error('Archived row count mismatch '+slice.file);
    maps.push(parsed.data);
  }
  sourceMaps.set(table.id,maps.flat());
}
const census=new Map(data.observations.filter(row=>row.indicator_id==='PHL_POPCEN_2024_DOMESTIC')
  .map(row=>[row.territory_id==='PHL'?'0000000000':row.territory_id.slice(-10),row.value]));
const output={dataset_sha256:sha(await readFile(join(project,'data','dashboard.json'))),
  source_catalogue_sha256:receipt.catalogue_sha256,source_tables:receipt.tables.length,checks:[]};
for(const [id,parameter] of [['0211A6DAPG0.px','3'],['0221A6DLPD0.px','2'],['0241A6DPUP1.px','0']]){
  const rows=sourceMaps.get(id).filter(row=>row.key[1]===parameter);
  const values=new Map(rows.map(row=>[row.key[0],Number(row.values[0])]));
  const mismatches=[];
  for(const [code,population] of census){
    if(code==='0000000000')continue;
    if(values.get(code)!==population)mismatches.push({code,adopted:population,official:values.get(code)??null});
  }
  output.checks.push({table:id,parameter,source_rows:rows.length,adopted_local_codes:census.size-1,
    missing_adopted_codes:mismatches.filter(row=>row.official===null).length,
    value_mismatches:mismatches.filter(row=>row.official!==null).length,
    unmatched_source_codes:[...values.keys()].filter(code=>code!=='0000000000'&&!census.has(code)),
    national_value:values.get('0000000000'),examples:mismatches.slice(0,20)});
}
const regionTables=receipt.tables.slice(0,18);
const local=new Map();
const duplicateCodes=[];
const duplicateConflicts=[];
for(const table of regionTables){
  for(const row of sourceMaps.get(table.id)){
    const [code,parameter]=row.key;
    if(!/^[0-9]{10}$/.test(code)||!['0','1','2'].includes(parameter))throw Error('Unexpected local table key '+table.id);
    if(!local.has(code))local.set(code,{});
    const bucket=local.get(code);
    if(bucket[parameter]!==undefined){
      duplicateCodes.push({code,parameter,table:table.id});
      if(bucket[parameter]!==row.values[0])duplicateConflicts.push({code,parameter,table:table.id,previous:bucket[parameter],current:row.values[0]});
    }
    bucket[parameter]=row.values[0];
  }
}
const localMismatches=[];
const localMissing=[];
const householdReady=[];
for(const [code,population] of census){
  if(code==='0000000000')continue;
  const row=local.get(code);
  if(!row){localMissing.push(code);continue;}
  if(Number(row['0'])!==population)localMismatches.push({code,adopted:population,official:row['0']});
  if(/^\d+$/.test(row['1'])&&/^\d+$/.test(row['2']))householdReady.push(code);
}
output.regional_tables={tables:regionTables.length,rows:regionTables.reduce((n,t)=>n+sourceMaps.get(t.id).length,0),
  distinct_geographic_codes:local.size,duplicate_rows:duplicateCodes.length,
  duplicate_adopted_rows:duplicateCodes.filter(row=>census.has(row.code)).length,
  conflicting_duplicate_rows:duplicateConflicts.length,duplicate_codes:duplicateCodes.slice(0,20),
  adopted_population_mismatches:localMismatches.slice(0,20),adopted_population_mismatch_count:localMismatches.length,
  adopted_codes_missing:localMissing,adopted_codes_with_household_and_households:householdReady.length,
  source_local_codes_not_in_dataset:[...local.keys()].filter(code=>!census.has(code)).length};
const out=join(project,'evidence','PHL_POPCEN_CATALOGUE_AUDIT.json');
await writeFile(out,JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify(output,null,2));

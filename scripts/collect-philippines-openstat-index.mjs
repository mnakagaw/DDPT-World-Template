#!/usr/bin/env node
// Inventory PSA OpenSTAT table locations without treating them as acquired values.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const projectArg=process.argv.indexOf('--project');
if(projectArg<0||!process.argv[projectArg+1])throw Error('Usage: node scripts/collect-philippines-openstat-index.mjs --project <directory>');
const project=resolve(process.argv[projectArg+1]);
const root='https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/';
const raw=join(project,'raw','openstat-index-2026-09-29');
const evidence=join(project,'evidence');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const checkedAt=new Date().toISOString();
await mkdir(raw,{recursive:true});
await mkdir(evidence,{recursive:true});

const retryFailed=process.argv.includes('--retry-failed');
const previous=retryFailed?JSON.parse(await readFile(join(evidence,'PHL_OPENSTAT_INDEX_2026-09-29.json'),'utf8')):null;
const failedPaths=new Set(previous?previous.failures.map(row=>row.path):[]);
if(previous){
  for(const directory of previous.directories){
    const rows=JSON.parse((await readFile(join(raw,directory.file))).toString('utf8').replace(/^\uFEFF/,''));
    const expected=rows.filter(row=>row.type==='t').length;
    const recorded=previous.tables.filter(row=>row.path===directory.path).length;
    if(expected!==recorded)failedPaths.add(directory.path);
  }
}
const queue=previous?[...failedPaths]:[''];
const directories=previous?previous.directories.filter(row=>!failedPaths.has(row.path)):[];
const tables=previous?previous.tables.filter(row=>!failedPaths.has(row.path)):[];
const visited=new Set(directories.map(row=>row.path));
const failures=[];
for(let cursor=0;cursor<queue.length;cursor++){
  const path=queue[cursor];
  if(visited.has(path))continue;
  if(visited.size>=500)throw Error('Directory safety limit reached');
  visited.add(path);
  const url=root+path;
  try{
    if(retryFailed)await new Promise(done=>setTimeout(done,1200));
    const response=await fetch(url,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(20000)});
    if(!response.ok)throw Error(`HTTP ${response.status}`);
    const bytes=Buffer.from(await response.arrayBuffer());
    const rows=JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
    if(!Array.isArray(rows))throw Error('Index is not an array');
    const newPaths=[],newTables=[];
    for(const row of rows){
      if(typeof row.id!=='string'||typeof row.text!=='string')throw Error(`Invalid row in ${url}`);
      if(row.type==='l'){
        if(!/^[A-Za-z0-9_]+$/.test(row.id))throw Error(`Unsafe directory ID ${row.id}`);
        newPaths.push(path+row.id+'/');
      }else if(row.type==='t'){
        if(!/^[A-Za-z0-9_]+\.px$/i.test(row.id))throw Error(`Unsafe table ID ${row.id}`);
        newTables.push({path,id:row.id,title:row.text,updated:row.updated||null,url:root+path+row.id});
      }else throw Error(`Unexpected row type ${row.type}`);
    }
    if(tables.length+newTables.length>10000)throw Error('Table safety limit reached');
    const file=`index-${hash(Buffer.from(path)).slice(0,16)}.json`;
    await writeFile(join(raw,file),bytes);
    directories.push({path,url,file,sha256:hash(bytes),bytes:bytes.length,entries:rows.length});
    tables.push(...newTables);
    queue.push(...newPaths);
  }catch(error){failures.push({path,url,error:String(error.message||error)});}
  if((cursor+1)%25===0)console.log(JSON.stringify({directories:directories.length,tables:tables.length,failures:failures.length,queued:queue.length}));
}
const discoveredTables=new Set(),discoveredPaths=new Set();
for(const directory of directories){
  const bytes=await readFile(join(raw,directory.file));
  if(hash(bytes)!==directory.sha256)throw Error(`Index byte mismatch: ${directory.path}`);
  const rows=JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
  if(rows.length!==directory.entries)throw Error(`Index row mismatch: ${directory.path}`);
  for(const row of rows){
    if(row.type==='l')discoveredPaths.add(directory.path+row.id+'/');
    else if(row.type==='t')discoveredTables.add(directory.path+row.id);
  }
}
const recordedPaths=new Set(directories.map(row=>row.path));
const recordedTables=new Set(tables.map(row=>row.path+row.id));
if(discoveredTables.size!==tables.length||[...discoveredTables].some(id=>!recordedTables.has(id)))
  throw Error('Table-location inventory does not match archived directory bytes');
if([...discoveredPaths].some(id=>!recordedPaths.has(id)&&!failures.some(row=>row.path===id)))
  throw Error('Discovered directory absent from inventory and failures');
const receipt={source_root:root,checked_at:checkedAt,scope:'Table-location catalogue only; metadata, values, geography and adoption require separate checks',complete:failures.length===0,
  directory_count:directories.length,table_count:tables.length,directories,tables,failures};
await writeFile(join(evidence,'PHL_OPENSTAT_INDEX_2026-09-29.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({complete:receipt.complete,directories:receipt.directory_count,tables:receipt.table_count,failures:failures.length,receipt:'evidence/PHL_OPENSTAT_INDEX_2026-09-29.json'}));

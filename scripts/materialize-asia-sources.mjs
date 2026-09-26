import {createHash} from 'node:crypto';
import {createReadStream,createWriteStream} from 'node:fs';
import {readFile,writeFile,mkdir,copyFile,rename,rm,stat} from 'node:fs/promises';
import {pipeline} from 'node:stream/promises';
import {Readable} from 'node:stream';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const safe=name=>String(name).replace(/[^a-zA-Z0-9._-]/g,'_');
async function check(file,expectedHash,expectedBytes){
  const digest=createHash('sha256');let bytes=0;
  for await(const chunk of createReadStream(file)){digest.update(chunk);bytes+=chunk.length;}
  const actual=digest.digest('hex');
  if(actual!==expectedHash||expectedBytes!=null&&bytes!==expectedBytes)
    throw new Error(`Pinned source mismatch: ${file}; hash ${actual}, bytes ${bytes}`);
  return {sha256:actual,bytes};
}
async function acquire(entry,target,local){
  await mkdir(path.dirname(target),{recursive:true});
  const tmp=target+'.partial';
  try{
    if(local){await copyFile(local,tmp);}
    else{
      const response=await fetch(entry.url,{signal:AbortSignal.timeout(240000)});
      if(!response.ok||!response.body)throw new Error(`HTTP ${response.status} for ${entry.url}`);
      await pipeline(Readable.fromWeb(response.body),createWriteStream(tmp));
    }
    const verified=await check(tmp,entry.sha256,entry.bytes);
    await rename(tmp,target);
    return verified;
  }catch(error){await rm(tmp,{force:true});throw error;}
}
export async function materializeAsiaSources(project,{legacyWorldRaw,wppDir}={}){
  const root=path.resolve(project),bytes=await readFile(path.join(root,'data/dashboard.json')),
    data=JSON.parse(bytes.toString('utf8'));
  if(data.country?.id!=='ASI')throw new Error('Expected Asia candidate');
  const manifest={dataset_sha256:sha256(bytes),started_at:new Date().toISOString(),
    policy:'Private audit files only; original source files are excluded from the public site and Git.',files:[],failures:[]};
  for(const source of data.sources){
    for(const [index,entry] of [...(source.raw_files||[]),...(source.source_files||[])].entries()){
      if(!entry.sha256||!entry.url)continue;
      let filename=source.raw_files?.includes(entry)&&entry.raw_path?path.basename(entry.raw_path):path.basename(new URL(entry.url).pathname)||`source-${index}`;
      if(source.id==='unsd-ama-2024'&&!filename.includes('.'))filename+='.xlsx';
      const rel=`raw/asia-sources/${safe(source.id)}/${index}-${safe(filename)}`;
      const target=path.join(root,rel);
      let local=null;
      if(source.raw_files?.includes(entry)&&legacyWorldRaw&&entry.raw_path)local=path.join(path.resolve(legacyWorldRaw),path.basename(entry.raw_path));
      if(source.id==='un-wpp2024-global-rev1'&&wppDir)local=path.join(path.resolve(wppDir),filename);
      try{
        const existing=await stat(target).catch(()=>null);
        const verified=existing?await check(target,entry.sha256,entry.bytes):await acquire(entry,target,local);
        const receipt={source_id:source.id,url:entry.url,local_path:rel,local_origin:local||null,
          ...verified,original_locator:entry.source_title||source.name,verified_at:new Date().toISOString(),
          dataset_sha256:manifest.dataset_sha256};
        manifest.files.push(receipt);
        await writeFile(target+'.receipt.json',JSON.stringify(receipt,null,2)+'\n');
      }catch(error){manifest.failures.push({source_id:source.id,url:entry.url,error:String(error.message)});}
    }
  }
  manifest.completed_at=new Date().toISOString();
  await writeFile(path.join(root,'evidence/ASIA_SOURCE_RAW_MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n');
  if(manifest.failures.length)throw new Error(`${manifest.failures.length} source originals could not be verified; see ASIA_SOURCE_RAW_MANIFEST.json`);
  return manifest;
}
if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','legacy-world-raw','wpp-dir']);
    if(!args.project)throw new Error('Use --project <Asia project> [--legacy-world-raw <directory>] [--wpp-dir <directory>]');
    const result=await materializeAsiaSources(args.project,{legacyWorldRaw:args['legacy-world-raw'],wppDir:args['wpp-dir']});
    console.log(`Verified ${result.files.length} source files against pinned SHA-256 and size`);
  }catch(error){reportError(error);}
}

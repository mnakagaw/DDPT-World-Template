import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {importKitWorldSourcePreflight,KIT_WORLD_PREFLIGHT_URL} from '../lib/world-census-preflight.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const defaultOut=fileURLToPath(new URL('../data/census/world-census-listings-v1.8.1.json',import.meta.url));

export async function importKitCensusPreflight({input,out=defaultOut,fetchImpl=fetch}={}){
  let bytes;
  if(input)bytes=await readFile(path.resolve(input));
  else{
    const response=await fetchImpl(KIT_WORLD_PREFLIGHT_URL,{headers:{accept:'application/json'}});
    if(!response.ok)throw new Error(`Kit registry request failed: HTTP ${response.status}`);
    bytes=Buffer.from(await response.arrayBuffer());
  }
  const normalized=await importKitWorldSourcePreflight(bytes),target=path.resolve(out);
  await mkdir(path.dirname(target),{recursive:true});
  await writeFile(target,JSON.stringify(normalized,null,2)+'\n','utf8');
  console.log(`Imported ${normalized.records.length} Census source-listing records: ${target}`);
  return {target,normalized};
}

if(isMain(import.meta.url)){
  try{
    const args=parseArgs(process.argv.slice(2),['input','out']);
    if(args.help)console.log('node scripts/import-kit-world-census-preflight.mjs [--input pinned-world-source-preflight.json] [--out data/census/world-census-listings-v1.8.1.json]');
    else await importKitCensusPreflight({input:args.input,out:args.out});
  }catch(error){reportError(error);}
}

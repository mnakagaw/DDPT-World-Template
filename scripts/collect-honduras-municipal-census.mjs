import {writeFile,mkdir,lstat} from 'node:fs/promises';
import path from 'node:path';
import {collectHondurasMunicipalReports,discoverHondurasMunicipalReports} from '../lib/honduras-municipal-census.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

async function assertAbsent(target){try{await lstat(target);throw new Error(`Output already exists: ${target}`);}catch(error){if(error.code!=='ENOENT')throw error;}}

export async function run({root,indexOnly=false,reuse}={}){
  if(!root)throw new Error('--root is required');
  const index=await discoverHondurasMunicipalReports(),target=path.join(path.resolve(root),'HND','2013','municipal-report-index.json');
  if(indexOnly){await assertAbsent(target);await mkdir(path.dirname(target),{recursive:true});await writeFile(target,JSON.stringify(index,null,2)+'\n',{flag:'wx'});console.log(`Discovered ${index.report_count} municipal reports. Index: ${target}`);return;}
  const receipt=await collectHondurasMunicipalReports({rootDir:root,index,reuseDir:reuse});console.log(`Honduras municipal acquisition: ${receipt.summary.acquired}/${receipt.summary.requested} acquired.`);console.log(`Receipt: ${path.join(path.resolve(root),'HND','2013','municipal-receipt.json')}`);if(receipt.summary.failed)throw new Error('One or more Honduras municipal census reports failed; review the receipt.');
}

if(isMain(import.meta.url)){
  try{
    const argv=process.argv.slice(2),indexOnly=argv.includes('--index-only'),args=parseArgs(argv.filter(value=>value!=='--index-only'),['root','reuse']);
    if(args.help)console.log('node scripts/collect-honduras-municipal-census.mjs --root .work/census-acquisition-YYYY-MM-DD [--reuse .work/prior-acquisition] [--index-only]');else await run({root:args.root,indexOnly,reuse:args.reuse});
  }catch(error){reportError(error);}
}

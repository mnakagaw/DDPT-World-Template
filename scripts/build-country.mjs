import path from 'node:path';
import { readFile, writeFile, mkdir, mkdtemp, lstat, cp, rename, readdir, realpath } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import { generateSite } from '../lib/generate.mjs';
import { validateDataset } from '../lib/validate.mjs';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';
export async function buildCountry(project, {generate=generateSite}={}) {
  if (!project) throw new Error('Provide --project <country directory>');
  const outDir = await realpath(path.resolve(project));
  const within=value=>{const target=path.resolve(value);if(!target.startsWith(outDir+path.sep))throw new Error('Build path must stay inside the selected project');return target;};
  const site=within(path.join(outDir,'site')),evidence=within(path.join(outDir,'evidence'));
  let dataset, result={errors:[],warnings:[]},previous=false,backup,moved=false;
  try {
    const info=await lstat(site).catch(error=>{if(error.code==='ENOENT')return null;throw error;});
    if(info?.isSymbolicLink() || info&&!info.isDirectory())throw new Error('Existing site must be a normal directory');
    const checkTree=async directory=>{
      for(const entry of await readdir(directory,{withFileTypes:true})) {
        const item=within(path.join(directory,entry.name)),stat=await lstat(item);
        if(stat.isSymbolicLink())throw new Error('Existing site contains a symbolic link or junction; rebuild requires a self-contained site directory');
        if(stat.isDirectory())await checkTree(item);
      }
    };
    if(info)await checkTree(site);
    previous=Boolean(info);
    await mkdir(evidence,{recursive:true});
    const datasetContent=await readFile(path.join(outDir,'data','dashboard.json'));
    dataset=JSON.parse(datasetContent.toString('utf8'));
    result=validateDataset(dataset);
    if(!dataset.observations?.some(o=>o?.status==='observed'&&Number.isFinite(o.value)))result.errors.push('No usable numeric observations; an empty data build is not successful');
    if(dataset.collection?.status==='failed')result.errors.push('Collection failed; retain the last verified dataset instead of replacing the site');
    if(result.errors.length)throw new Error(result.errors.join('; '));
    // Generate in an owned staging directory. A write failure never leaves a mixed live site.
    const stage=within(await mkdtemp(path.join(outDir,'.build-')));
    if(previous)await cp(site,within(path.join(stage,'site')),{recursive:true,dereference:false});
    await generate({dataset,outDir:stage});
    // Finish ancillary writes before the site swap; a metadata failure cannot be reported as an old-site retention after a successful swap.
    await cp(path.join(stage,'SITE_README.md'),path.join(outDir,'SITE_README.md'));
    await writeFile(path.join(evidence,'validation.json'),JSON.stringify({...result,checked_at:new Date().toISOString(),dataset_sha256:createHash('sha256').update(datasetContent).digest('hex')},null,2)+'\n');
    if(previous) {
      await mkdir(within(path.join(outDir,'.build-backups')),{recursive:true});
      backup=within(path.join(outDir,'.build-backups',randomUUID()));
      await rename(site,backup);moved=true;
    }
    try {await rename(within(path.join(stage,'site')),site);}
    catch(error) {if(moved){await rename(backup,site);moved=false;}throw error;}
    console.log(`Built: ${site}`);return result;
  } catch(error) {
    if(!result.errors.length)result.errors.push(error.message);
    // A blocked receipt path must not prevent the independent last-good-site warning.
    await writeFile(path.join(evidence,'validation.json'),JSON.stringify({...result,checked_at:new Date().toISOString(),dataset_sha256:dataset?createHash('sha256').update(JSON.stringify(dataset)).digest('hex'):null,site_replaced:false},null,2)+'\n').catch(()=>{});
    if(previous) {
      let oldDataset,oldStatus;
      try {oldDataset=JSON.parse(await readFile(path.join(site,'data','dashboard.json'),'utf8'));}catch{}
      try {oldStatus=JSON.parse(await readFile(path.join(site,'data','update-status.json'),'utf8'));}catch{}
      await mkdir(path.join(site,'data'),{recursive:true});
      await writeFile(path.join(site,'data','update-status.json'),JSON.stringify({status:'stopped',checked_at:new Date().toISOString(),last_success_at:oldStatus?.last_success_at||null,data_edition:oldDataset?.generated_at||null,message:'The latest rebuild did not pass. The last verified site is retained; review the validation receipt before retrying.'},null,2)+'\n');
    }
    throw error;
  }
}
if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['project']);
    if (args.help) console.log('node scripts/build-country.mjs --project generated/uganda');
    else await buildCountry(args.project);
  } catch (error) { reportError(error); }
}

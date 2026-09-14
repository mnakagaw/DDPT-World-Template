import {mkdir,lstat,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {collectWorld} from '../lib/collect-world.mjs';
import {buildRegionalPilot,buildCensusPilotPreflight,renderCensusPilotPreflight} from '../lib/regional-pilot.mjs';
import {loadSourceCatalog} from '../lib/source-catalog.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {readTemplateReference} from './create-country.mjs';

export async function createCentralAmerica({out,sourceDir}={}) {
  if(!sourceDir)throw new Error('--source-dir must point to a verified world raw archive.');
  const outDir=path.resolve(out||'generated/central-america');
  try{await lstat(outDir);throw new Error(`Output already exists; choose a new directory: ${outDir}`);}catch(error){if(error.code!=='ENOENT')throw error;}
  await mkdir(path.join(outDir,'raw'),{recursive:true});
  try{
    const world=await collectWorld({rawDir:path.join(outDir,'raw'),sourceDir:path.resolve(sourceDir),onProgress:message=>console.log(message)});
    const dataset=buildRegionalPilot(world),validation=validateDataset(dataset),content=JSON.stringify(dataset,null,2)+'\n';
    const censusPlan=buildCensusPilotPreflight(await loadSourceCatalog());
    await mkdir(path.join(outDir,'data'));await mkdir(path.join(outDir,'evidence'));
    await writeFile(path.join(outDir,'data/dashboard.json'),content);
    await writeFile(path.join(outDir,'evidence/validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/CENSUS_SOURCE_PREFLIGHT.json'),JSON.stringify(censusPlan,null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/CENSUS_SOURCE_PREFLIGHT.md'),renderCensusPilotPreflight(censusPlan));
    if(validation.errors.length)throw new Error(`Central America pilot failed validation: ${validation.errors.join('; ')}`);
    await generateSite({dataset,outDir});
    await writeFile(path.join(outDir,'TEMPLATE_REFERENCE.json'),JSON.stringify(await readTemplateReference(),null,2)+'\n');
    await writeFile(path.join(outDir,'AREADATA_ARCHITECTURE.md'),await readFile(new URL('../docs/AREADATA_ARCHITECTURE.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'CENSUS_SERIES_CONTRACT.md'),await readFile(new URL('../docs/CENSUS_SERIES_CONTRACT.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'HANDOFF.md'),'# AreaData Central America pilot\n\nThis runtime covers the seven-country Central America pilot: Belize, Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica and Panama. Official census data are the primary intended series. The current generated values are a separate international-reference scaffold until the census source preflight is acquired, matched and accepted. Different census years are permitted only with every country year shown; missing country coverage never becomes a regional total.\n');
    console.log(`Created: ${outDir}`);return {outDir,dataset,validation};
  }catch(error){await writeFile(path.join(outDir,'COLLECTION_FAILED.txt'),`${new Date().toISOString()}\n${error.message}\n`);throw error;}
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['out','source-dir']);if(args.help)console.log('node scripts/create-central-america.mjs --source-dir previous-world/raw --out generated/central-america');else await createCentralAmerica({out:args.out,sourceDir:args['source-dir']});}catch(error){reportError(error);}
}

import {mkdir,lstat,writeFile,readFile,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {collectWorld} from '../lib/collect-world.mjs';
import {buildAmericas} from '../lib/americas-adapter.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {readTemplateReference} from './create-country.mjs';

export async function createAmericas({out,sourceDir,centralAmericaProject,startYear,endYear,collect=collectWorld,generate=generateSite}={}){
  const outDir=path.resolve(out||'generated/americas');
  try{await lstat(outDir);throw new Error(`Output already exists; choose a new directory: ${outDir}`);}catch(error){if(error.code!=='ENOENT')throw error;}
  await mkdir(path.join(outDir,'raw'),{recursive:true});
  try{
    const world=await collect({rawDir:path.join(outDir,'raw'),sourceDir:sourceDir?path.resolve(sourceDir):undefined,startYear,endYear,onProgress:message=>console.log(message)});
    const centralAmerica=centralAmericaProject?JSON.parse(await readFile(path.resolve(centralAmericaProject,'data/dashboard.json'),'utf8')):null;
    const dataset=buildAmericas(world,{centralAmerica}),validation=validateDataset(dataset),content=JSON.stringify(dataset,null,2)+'\n';
    await mkdir(path.join(outDir,'data'));await mkdir(path.join(outDir,'evidence'));
    await writeFile(path.join(outDir,'data/dashboard.json'),content);
    await writeFile(path.join(outDir,'evidence/validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/AMERICAS_SCOPE.json'),JSON.stringify({scope_id:'M49:019',country_area_count:dataset.analysis.coverage.country_area_count,census_integrated_country_ids:dataset.analysis.coverage.census_integrated_country_ids,census_integrated_territory_count:dataset.analysis.coverage.census_integrated_territory_count,generated_at:dataset.generated_at,world_source_dir:sourceDir?path.resolve(sourceDir):null,central_america_project:centralAmericaProject?path.resolve(centralAmericaProject):null},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/ACCEPTANCE.md'),await readFile(new URL('../templates/REGIONAL_ACCEPTANCE.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'evidence/INDEPENDENT_AUDIT.md'),await readFile(new URL('../templates/REGIONAL_INDEPENDENT_AUDIT.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'evidence/DELIVERY.json'),JSON.stringify({
      schema_version:'0.1',project:'AreaData Americas',build_status:'candidate',
      scope:{id:'M49:019',country_area_count:dataset.analysis.coverage.country_area_count,classification:'UN M49 Americas with a documented display-only Central America + Caribbean navigation group'},
      checks:Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'pending',evidence_file:'evidence/ACCEPTANCE.md'}])),
      independent_audit:{status:'pending',file:'evidence/INDEPENDENT_AUDIT.md'},
      release:{github_status:'pending',hosting_status:'blocked_by_audit',public_status:'not_published'}
    },null,2)+'\n');
    if(validation.errors.length)throw new Error(`Americas dataset failed validation: ${validation.errors.join('; ')}`);
    if(!dataset.observations.some(row=>row.status==='observed'))throw new Error('No numeric observations collected.');
    await generate({dataset,outDir});
    await writeFile(path.join(outDir,'TEMPLATE_REFERENCE.json'),JSON.stringify(await readTemplateReference(),null,2)+'\n');
    await copyFile(new URL('../docs/WORLD_ADAPTER.md',import.meta.url),path.join(outDir,'WORLD_ADAPTER.md'));
    await writeFile(path.join(outDir,'HANDOFF.md'),`# AreaData Americas\n\nThis candidate covers all ${dataset.analysis.coverage.country_area_count} countries and areas in UN M49 Americas (019). Navigation uses Northern America, South America and the documented Central America + Caribbean display group. Official census population and domestic hierarchy are integrated only for ${dataset.analysis.coverage.census_integrated_country_ids.join(', ') || 'no countries yet'}; missing integration does not mean no census exists.\n\nNo exact source-reported Americas total has been adopted. Country observations are not silently converted into a regional total. Planning laws and materials remain country-adapter work.\n\nComplete evidence/ACCEPTANCE.md, change only evidence-backed checks in evidence/DELIVERY.json to passed, and run:\n\n    node scripts/verify-regional-delivery.mjs --project ${outDir}\n\nIndependent audit status: PENDING. A separate task must inspect the actual sources, data, browser behavior and downloads without editing the candidate. Do not publish until it records ACCEPT and the publication gate passes:\n\n    node scripts/verify-regional-delivery.mjs --project ${outDir} --require-publishable\n`);
    console.log(`Created: ${outDir}`);return {outDir,dataset,validation};
  }catch(error){await writeFile(path.join(outDir,'COLLECTION_FAILED.txt'),`${new Date().toISOString()}\n${error.message}\n`);throw error;}
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['out','source-dir','central-america-project','start-year','end-year']);if(args.help)console.log('node scripts/create-americas.mjs --source-dir previous-world/raw --central-america-project previous-central-america --out generated/americas');else await createAmericas({out:args.out,sourceDir:args['source-dir'],centralAmericaProject:args['central-america-project'],startYear:args['start-year']===undefined?undefined:Number(args['start-year']),endYear:args['end-year']===undefined?undefined:Number(args['end-year'])});}catch(error){reportError(error);}
}

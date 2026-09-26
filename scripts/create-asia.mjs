import {readFile, writeFile, mkdir, lstat, copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {buildAsia} from '../lib/asia-adapter.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {readTemplateReference} from './create-country.mjs';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');

export async function createAsia({worldPortfolio,out,generate=generateSite}={}) {
  if (!worldPortfolio || !out) throw new Error('Use --world-portfolio <validated World dashboard.json> --out <new-directory>');
  const input=path.resolve(worldPortfolio),outDir=path.resolve(out);
  try { await lstat(outDir); throw new Error(`Output already exists: ${outDir}`); }
  catch(error) { if(error.code!=='ENOENT') throw error; }
  const inputBytes=await readFile(input),world=JSON.parse(inputBytes.toString('utf8'));
  const dataset=buildAsia(world),validation=validateDataset(dataset);
  if(validation.errors.length)throw new Error(`Asia validation failed: ${validation.errors.slice(0,12).join('; ')}`);
  const content=JSON.stringify(dataset)+'\n';
  await mkdir(path.join(outDir,'data'),{recursive:true});
  await mkdir(path.join(outDir,'evidence'),{recursive:true});
  await writeFile(path.join(outDir,'data/dashboard.json'),content);
  await writeFile(path.join(outDir,'evidence/validation.json'),JSON.stringify({...validation,dataset_sha256:hash(content),checked_at:new Date().toISOString()},null,2)+'\n');
  await writeFile(path.join(outDir,'evidence/ASIA_SCOPE.json'),JSON.stringify({scope_id:'M49:142',source_world_path:input,source_world_sha256:hash(inputBytes),source_world_generated_at:world.generated_at,
    country_area_ids:dataset.territories.filter(area=>area.type==='country').map(area=>area.id),
    subregion_ids:dataset.territories.filter(area=>area.parent_id==='M49:142').map(area=>area.id),
    country_area_count:dataset.analysis.coverage.country_area_count,
    wpp_country_area_count:dataset.analysis.coverage.un_wpp_country_area_count,
    domestic_branch_country_ids:dataset.analysis.coverage.census_integrated_country_ids,
    observation_count:dataset.observations.length,indicator_count:dataset.indicators.length,
    reference_boundary_count:dataset.boundaries.features.length,dataset_sha256:hash(content)},null,2)+'\n');
  await copyFile(new URL('../templates/REGIONAL_ACCEPTANCE.md',import.meta.url),path.join(outDir,'evidence/ACCEPTANCE.md'));
  await copyFile(new URL('../templates/REGIONAL_INDEPENDENT_AUDIT.md',import.meta.url),path.join(outDir,'evidence/INDEPENDENT_AUDIT.md'));
  await writeFile(path.join(outDir,'evidence/DELIVERY.json'),JSON.stringify({schema_version:'0.1',project:'AreaData Asia exploration gateway',build_status:'candidate',
    scope:{id:'M49:142',country_area_count:dataset.analysis.coverage.country_area_count,classification:'UN M49 Asia and five statistical subregions'},
    checks:Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'pending',evidence_file:'evidence/ACCEPTANCE.md'}])),
    independent_audit:{status:'pending',file:'evidence/INDEPENDENT_AUDIT.md'},
    release:{github_status:'pending',hosting_status:'blocked_by_audit',public_status:'not_published'}},null,2)+'\n');
  await generate({dataset,outDir,canonicalSha256:hash(content)});
  await writeFile(path.join(outDir,'TEMPLATE_REFERENCE.json'),JSON.stringify(await readTemplateReference(),null,2)+'\n');
  await writeFile(path.join(outDir,'HANDOFF.md'),`# AreaData Asia gateway\n\nScope: all ${dataset.analysis.coverage.country_area_count} UN M49 Asia countries/areas, in five statistical subregions. This does not mean ${dataset.analysis.coverage.country_area_count} completed domestic country editions. The input World portfolio SHA-256 is ${hash(inputBytes)}; the Asia dataset SHA-256 is ${hash(content)}.\n\nInternational data and years follow the input World portfolio. No country total is copied to a subnational area, and missing geography does not erase a country from the registry. Domestic census, official codes, legal planning units and planning evidence must be completed through verified country adapters.\n\nBefore publication, complete evidence/ACCEPTANCE.md and independent evidence review. PENDING is not ACCEPT.\n`);
  return {outDir,dataset,validation};
}

if(isMain(import.meta.url)){
  try { const args=parseArgs(process.argv.slice(2),['world-portfolio','out']);
    if(args.help)console.log('node scripts/create-asia.mjs --world-portfolio <validated World dashboard.json> --out <new-directory>');
    else { const result=await createAsia({worldPortfolio:args['world-portfolio'],out:args.out});
      console.log(`Created ${result.outDir}: ${result.dataset.analysis.coverage.country_area_count} countries/areas, ${result.dataset.observations.length} observations`); }
  } catch(error) { reportError(error); }
}

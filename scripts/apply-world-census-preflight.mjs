import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {attachWorldCensusListings,loadBundledWorldCensusListings} from '../lib/world-census-preflight.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

export async function applyWorldCensusPreflight(project){
  if(!project)throw new Error('Provide --project <generated project>');
  const root=path.resolve(project),dataPath=path.join(root,'data','dashboard.json');
  const dataset=JSON.parse(await readFile(dataPath,'utf8')),registry=await loadBundledWorldCensusListings();
  const updated=attachWorldCensusListings(dataset,registry),validation=validateDataset(updated);
  if(validation.errors.length)throw new Error(validation.errors.join('; '));
  // Large regional datasets can exceed V8's single-string limit when pretty
  // printing adds hundreds of megabytes of indentation. Keep the canonical
  // JSON lossless and compact, as the generated browser copies already are.
  const content=JSON.stringify(updated)+'\n';
  await writeFile(dataPath,content,'utf8');
  await writeFile(path.join(root,'evidence','CENSUS_SOURCE_PREFLIGHT_IMPORT.json'),JSON.stringify({schema_version:'1.0',applied_at:new Date().toISOString(),source:registry.source,record_count:updated.analysis.census_source_preflight.records.length,scope_country_ids:updated.analysis.census_source_preflight.scope_country_ids,missing_country_ids:updated.analysis.census_source_preflight.missing_country_ids,dataset_sha256:createHash('sha256').update(content).digest('hex'),validation},null,2)+'\n','utf8');
  console.log(`Applied ${updated.analysis.census_source_preflight.records.length} Census listing records to ${root}`);
  return {dataset:updated,validation};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(args.help)console.log('node scripts/apply-world-census-preflight.mjs --project <generated project>');else await applyWorldCensusPreflight(args.project);}catch(error){reportError(error);}
}

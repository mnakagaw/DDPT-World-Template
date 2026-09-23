import {readFile,writeFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {buildCountryCompletionMatrix,validateCountryCompletionMatrix} from '../lib/country-completion-matrix.mjs';
import {buildCountry} from './build-country.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const readOptional=async filename=>{try{return JSON.parse(await readFile(filename,'utf8'));}catch(error){if(error.code==='ENOENT')return {records:[]};throw error;}};
export async function writeCountryCompletionMatrix({project}={}){
  if(!project)throw new Error('A project directory is required.');
  const root=path.resolve(project),evidence=path.join(root,'evidence');
  const preflight=JSON.parse(await readFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),'utf8'));
  const semantic=await readOptional(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'));
  const datasetPath=path.join(root,'data/dashboard.json'),dataset=JSON.parse(await readFile(datasetPath,'utf8'));
  const matrix=buildCountryCompletionMatrix(preflight,{semanticInventory:semantic,dataset}),validation=validateCountryCompletionMatrix(matrix,{expectedCountryIds:preflight.countries.map(row=>row.country_area_id)});
  if(!validation.ok)throw new Error(validation.errors.join('; '));
  preflight.summary={...(preflight.summary||{}),integrated_country_adapters:matrix.broad_local_edition_country_area_count,source_review_complete_country_areas:matrix.source_review_complete_country_area_count,country_edition_complete_country_areas:matrix.country_edition_complete_country_area_count,planning_ready_country_areas:matrix.planning_ready_country_area_count,structural_nonresident_exceptions:matrix.structural_nonresident_exception_country_area_count,classification_counts:matrix.classification_counts};
  dataset.analysis={...(dataset.analysis||{}),coverage:{...(dataset.analysis?.coverage||{}),source_review_complete_country_area_count:matrix.source_review_complete_country_area_count,country_edition_complete_country_area_count:matrix.country_edition_complete_country_area_count,broad_local_edition_country_area_count:matrix.broad_local_edition_country_area_count,planning_ready_country_area_count:matrix.planning_ready_country_area_count,structural_nonresident_exception_country_area_count:matrix.structural_nonresident_exception_country_area_count,country_edition_classification_counts:matrix.classification_counts,minimum_broad_local_observed_indicators:matrix.minimum_broad_local_observed_indicators,minimum_broad_local_diagnostic_groups:matrix.minimum_broad_local_diagnostic_groups}};
  // The Americas canonical dataset is large enough that pretty-printing can exceed V8's
  // maximum string length. Compact JSON preserves the same data and remains reproducible.
  const datasetContent=JSON.stringify(dataset)+'\n',datasetSha256=createHash('sha256').update(datasetContent).digest('hex');
  const auditFiles=(await readdir(evidence)).filter(name=>name.endsWith('_INTEGRATION_AUDIT.json'));
  await Promise.all(auditFiles.map(async name=>{const filename=path.join(evidence,name),audit=JSON.parse(await readFile(filename,'utf8'));audit.final_dataset_sha256=datasetSha256;await writeFile(filename,JSON.stringify(audit,null,2)+'\n');}));
  await Promise.all([
    writeFile(datasetPath,datasetContent),
    writeFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
    writeFile(path.join(evidence,'COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix,null,2)+'\n')
  ]);
  const datasetValidation=await buildCountry(root);
  return {matrix,validation,datasetValidation,dataset_sha256:datasetSha256,integration_audit_count:auditFiles.length};
}
if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(args.help||!args.project)console.log('node scripts/build-country-completion-matrix.mjs --project <directory>');else {const {validation,dataset_sha256,integration_audit_count}=await writeCountryCompletionMatrix({project:args.project});console.log(JSON.stringify({...validation,dataset_sha256,integration_audit_count},null,2));}}
  catch(error){reportError(error);}
}

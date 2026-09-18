import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {buildCountryCompletionMatrix,validateCountryCompletionMatrix} from '../lib/country-completion-matrix.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const readOptional=async filename=>{try{return JSON.parse(await readFile(filename,'utf8'));}catch(error){if(error.code==='ENOENT')return {records:[]};throw error;}};
export async function writeCountryCompletionMatrix({project}={}){
  if(!project)throw new Error('A project directory is required.');
  const root=path.resolve(project),evidence=path.join(root,'evidence');
  const preflight=JSON.parse(await readFile(path.join(evidence,'SOURCE_PREFLIGHT.json'),'utf8'));
  const semantic=await readOptional(path.join(evidence,'COUNTRY_SEMANTIC_INVENTORY.json'));
  const matrix=buildCountryCompletionMatrix(preflight,{semanticInventory:semantic}),validation=validateCountryCompletionMatrix(matrix,{expectedCountryIds:preflight.countries.map(row=>row.country_area_id)});
  if(!validation.ok)throw new Error(validation.errors.join('; '));
  await writeFile(path.join(evidence,'COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix,null,2)+'\n');
  return {matrix,validation};
}
if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(args.help||!args.project)console.log('node scripts/build-country-completion-matrix.mjs --project <directory>');else {const {validation}=await writeCountryCompletionMatrix({project:args.project});console.log(JSON.stringify(validation,null,2));}}
  catch(error){reportError(error);}
}

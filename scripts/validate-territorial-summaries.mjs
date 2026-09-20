import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {auditTerritorialSummaries} from '../lib/territorial-summary-audit.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

export async function validateTerritorialSummaries({project,output}={}) {
  if(!project)throw new Error('A project directory is required.');
  const root=path.resolve(project),dataset=JSON.parse(await readFile(path.join(root,'data','dashboard.json'),'utf8'));
  const result=auditTerritorialSummaries(dataset);
  const target=output?path.resolve(output):path.join(root,'evidence','TERRITORIAL_SUMMARY_AUDIT.json');
  await writeFile(target,JSON.stringify({...result,checked_at:new Date().toISOString(),project:root},null,2)+'\n');
  return result;
}

if(isMain(import.meta.url)){
  try{
    const args=parseArgs(process.argv.slice(2),['project','output']);
    if(args.help||!args.project)console.log('node scripts/validate-territorial-summaries.mjs --project <directory> [--output <file>; defaults to evidence/TERRITORIAL_SUMMARY_AUDIT.json]');
    else {const result=await validateTerritorialSummaries({project:args.project,output:args.output});console.log(JSON.stringify(result,null,2));if(!result.ok)process.exitCode=1;}
  }catch(error){reportError(error);}
}

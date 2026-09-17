import {readFile,access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateDataset} from '../lib/validate.mjs';

const requiredChecks=['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'];
const exists=async filename=>{try{await access(filename);return true;}catch{return false;}};
const inside=(root,relative)=>{if(typeof relative!=='string'||!relative)return null;const target=path.resolve(root,relative),prefix=path.resolve(root)+path.sep;return target.startsWith(prefix)?target:null;};

export async function verifyRegionalDelivery(project,{requirePublishable=false}={}){
  const root=path.resolve(project),errors=[],warnings=[];
  const readJson=async relative=>{const filename=inside(root,relative);if(!filename||!await exists(filename)){errors.push(`Missing ${relative}`);return null;}try{return JSON.parse(await readFile(filename,'utf8'));}catch(error){errors.push(`Invalid JSON ${relative}: ${error.message}`);return null;}};
  const data=await readJson('data/dashboard.json'),validation=await readJson('evidence/validation.json'),delivery=await readJson('evidence/DELIVERY.json');
  for(const relative of ['evidence/ACCEPTANCE.md','evidence/INDEPENDENT_AUDIT.md','site/index.html','site/territorial/index.html','site/thematic/index.html','site/planning/index.html','site/database/index.html'])if(!await exists(inside(root,relative)||''))errors.push(`Missing ${relative}`);
  if(data){
    const result=validateDataset(data);errors.push(...result.errors.map(item=>`dataset: ${item}`));warnings.push(...result.warnings.map(item=>`dataset: ${item}`));
    if(data.analysis?.kind!=='regional'&&data.analysis?.kind!=='world')errors.push('dataset.analysis.kind must be regional or world');
    const countryCount=data.territories?.filter(area=>area.type==='country').length||0;
    if(delivery?.scope?.country_area_count!==countryCount)errors.push('delivery scope count does not match the dataset');
    const content=await readFile(path.join(root,'data/dashboard.json'));
    const hash=createHash('sha256').update(content).digest('hex');
    if(validation?.dataset_sha256!==hash)errors.push('validation dataset_sha256 does not match data/dashboard.json');
  }
  if(validation?.errors?.length)errors.push('evidence/validation.json contains validation errors');
  if(delivery?.schema_version!=='0.1')errors.push('DELIVERY schema_version must be 0.1');
  for(const key of requiredChecks){
    const check=delivery?.checks?.[key];
    if(check?.status!=='passed')errors.push(`checks.${key}.status must be passed`);
    const evidence=inside(root,check?.evidence_file);
    if(!evidence||!await exists(evidence))errors.push(`checks.${key}.evidence_file is missing or outside the project`);
  }
  const audit=delivery?.independent_audit;
  if(!['pending','accept','reject','incomplete_audit'].includes(audit?.status))errors.push('independent_audit.status is invalid');
  if(requirePublishable&&audit?.status!=='accept')errors.push('Independent audit must be ACCEPT before publication');
  if(!requirePublishable&&audit?.status!=='accept')warnings.push('Independent audit is pending or not accepted; the candidate is not publishable.');
  if(delivery?.release?.public_status==='published'&&audit?.status!=='accept')errors.push('Public status cannot be published before independent audit ACCEPT');
  return {ok:errors.length===0,publishable:errors.length===0&&audit?.status==='accept',errors,warnings};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2),project=args[args.indexOf('--project')+1],requirePublishable=args.includes('--require-publishable');
  if(!project){console.error('Usage: node scripts/verify-regional-delivery.mjs --project <directory> [--require-publishable]');process.exit(2);}
  const result=await verifyRegionalDelivery(project,{requirePublishable});console.log(JSON.stringify(result,null,2));if(!result.ok)process.exitCode=1;
}


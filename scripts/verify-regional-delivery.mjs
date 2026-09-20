import {readFile,access} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateDataset} from '../lib/validate.mjs';
import {validateCountryCompletionMatrix} from '../lib/country-completion-matrix.mjs';

const requiredChecks=['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'];
const exists=async filename=>{try{await access(filename);return true;}catch{return false;}};
const inside=(root,relative)=>{if(typeof relative!=='string'||!relative)return null;const target=path.resolve(root,relative),prefix=path.resolve(root)+path.sep;return target.startsWith(prefix)?target:null;};
const sha256File=filename=>new Promise((resolve,reject)=>{const hash=createHash('sha256'),stream=createReadStream(filename);stream.on('data',chunk=>hash.update(chunk));stream.on('error',reject);stream.on('end',()=>resolve(hash.digest('hex')));});

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

    const descendantCountries=[...new Set(data.territories.filter(area=>area.type!=='country'&&area.country_id).map(area=>area.country_id))].filter(id=>data.territories.some(area=>area.type==='country'&&area.id===id)).sort();
    if(descendantCountries.length){
      const bootstrap=await readJson('site/data/dashboard.json');
      const manifest=bootstrap?.data_shards,integrity=manifest?.integrity,countries=manifest?.countries||{},countryIntegrity=integrity?.countries||{};
      if(manifest?.schema_version!=='1.1')errors.push('site country-shard manifest schema_version must be 1.1');
      if(integrity?.canonical_sha256!==hash)errors.push('site country-shard manifest is not bound to the canonical dataset hash');
      const expectedCounts={territory_count:data.territories.length,observation_count:data.observations.length,boundary_count:data.boundaries?.features?.length||0,document_count:data.documents?.length||0,comparison_count:data.analysis?.comparisons?.length||0};
      for(const [key,value] of Object.entries(expectedCounts))if(integrity?.[key]!==value)errors.push(`site country-shard manifest ${key} does not match the canonical dataset`);
      const manifestCountries=Object.keys(countries).sort();
      if(JSON.stringify(manifestCountries)!==JSON.stringify(descendantCountries))errors.push('site country-shard manifest country keys do not match canonical country-depth branches');
      const fullRelative=manifest?.full&&`site/data/${manifest.full}`,fullFile=inside(root,fullRelative);
      if(!fullFile||!await exists(fullFile))errors.push('Missing site/data/dashboard-full.json declared by the shard manifest');
      else if(await sha256File(fullFile)!==integrity?.full_sha256)errors.push('site full dataset hash does not match the shard manifest');
      for(const countryId of manifestCountries){
        const relative=`site/data/${countries[countryId]}`,filename=inside(root,relative),expected=countryIntegrity[countryId];
        if(!filename||!await exists(filename)){errors.push(`Missing ${relative}`);continue;}
        const content=await readFile(filename),actualHash=createHash('sha256').update(content).digest('hex');
        if(actualHash!==expected?.sha256)errors.push(`${relative} hash does not match the shard manifest`);
        let shard;try{shard=JSON.parse(content.toString('utf8'));}catch(error){errors.push(`Invalid JSON ${relative}: ${error.message}`);continue;}
        if(shard.schema_version!=='0.2-country-shard'||shard.country_area_id!==countryId)errors.push(`${relative} has incompatible shard identity`);
        const expectedIds=new Set(data.territories.filter(area=>area.country_id===countryId&&area.id!==countryId).map(area=>area.id));
        const actualIds=new Set((shard.territories||[]).map(area=>area.id));
        if(expectedIds.size!==actualIds.size||[...expectedIds].some(id=>!actualIds.has(id)))errors.push(`${relative} territory membership does not match the canonical dataset`);
        const counts={territory_count:shard.territories?.length||0,observation_count:shard.observations?.length||0,boundary_count:shard.boundaries?.features?.length||0,document_count:shard.documents?.length||0,comparison_count:shard.comparisons?.length||0};
        for(const [key,value] of Object.entries(counts))if(expected?.[key]!==value)errors.push(`${relative} ${key} does not match the shard manifest`);
        if((shard.observations||[]).some(row=>!expectedIds.has(row.territory_id)))errors.push(`${relative} contains an observation outside its country branch`);
        if((shard.boundaries?.features||[]).some(feature=>!expectedIds.has(feature.properties?.territory_id)))errors.push(`${relative} contains a boundary outside its country branch`);
      }
    }
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
  if(requirePublishable&&delivery?.scope?.id==='M49:019'){
    const matrix=await readJson('evidence/COUNTRY_COMPLETION_MATRIX.json');
    if(matrix&&data){
      const expected=data.territories.filter(area=>area.type==='country').map(area=>area.id),result=validateCountryCompletionMatrix(matrix,{expectedCountryIds:expected});
      errors.push(...result.errors.map(item=>`completion matrix: ${item}`));
      if(result.country_edition_complete_country_area_count!==expected.length)errors.push(`All ${expected.length} Americas country editions must be complete before publication; matrix has ${result.country_edition_complete_country_area_count}. Source-review completion is not country-edition completion.`);
    }
    const semantic=await readJson('evidence/COUNTRY_SEMANTIC_INVENTORY.json'),terminal=new Set(['integrated','not_adopted','unavailable','restricted','failed_with_evidence']);
    if(semantic){
      const unresolved=(semantic.records||[]).filter(row=>Number(row.numeric_cell_count)>0&&(!terminal.has(row.disposition)||!row.reason));
      if(unresolved.length)errors.push(`All acquired numeric fields, including shared MULTI sources, need terminal dispositions before publication; ${unresolved.length} remain unresolved`);
    }
  }
  return {ok:errors.length===0,publishable:errors.length===0&&audit?.status==='accept',errors,warnings};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2),project=args[args.indexOf('--project')+1],requirePublishable=args.includes('--require-publishable');
  if(!project){console.error('Usage: node scripts/verify-regional-delivery.mjs --project <directory> [--require-publishable]');process.exit(2);}
  const result=await verifyRegionalDelivery(project,{requirePublishable});console.log(JSON.stringify(result,null,2));if(!result.ok)process.exitCode=1;
}

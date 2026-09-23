import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {verifyRegionalDelivery} from '../scripts/verify-regional-delivery.mjs';
import {buildCountryCompletionMatrix,COMPLETION_DOMAINS,CENSUS_THEMES} from '../lib/country-completion-matrix.mjs';
import {generateSite} from '../lib/generate.mjs';

const data={schema_version:'0.2',generated_at:'2026-09-17T00:00:00Z',country:{id:'AMR',name:'Americas',national_territory_id:'AMR'},territories:[{id:'AMR',name:'Americas',level:'national',type:'exploration_scope',parent_id:null},{id:'AAA',name:'A',level:'country',type:'country',parent_id:'AMR'}],analysis:{kind:'regional',terminal_territory_ids:['AAA'],comparisons:[{parent_id:'AMR',member_ids:['AAA'],label:'Members',membership_note:'Test.',source_ids:['membership']}],coverage:{country_area_count:1}},indicators:[{id:'POP',name:'Population',theme:'Population',unit:'people',definition:'Population.',definition_id:'pop',population:'All',measurement_method:'reported',aggregation:'official_only',source_id:'values'}],observations:[{territory_id:'AAA',indicator_id:'POP',period:'2025',value:1,status:'observed',source_id:'values'}],sources:[{id:'membership',name:'Membership',publisher:'Test',url:'https://example.org/m',status:'ready',retrieved_at:'2026-09-17',reference_period:'2025',license:'Test'},{id:'values',name:'Values',publisher:'Test',url:'https://example.org/v',status:'ready',retrieved_at:'2026-09-17',reference_period:'2025',license:'Test'}],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['test'],notes:['Test.']}};

async function fixture(audit='pending',scopeId='M49:019'){
  const root=await mkdtemp(path.join(os.tmpdir(),'regional-delivery-'));for(const dir of ['data','evidence','site','site/territorial','site/thematic','site/planning','site/database'])await mkdir(path.join(root,dir),{recursive:true});
  const content=JSON.stringify(data,null,2)+'\n',hash=createHash('sha256').update(content).digest('hex');await writeFile(path.join(root,'data/dashboard.json'),content);await writeFile(path.join(root,'evidence/validation.json'),JSON.stringify({errors:[],warnings:[],dataset_sha256:hash}));await writeFile(path.join(root,'evidence/ACCEPTANCE.md'),'acceptance');await writeFile(path.join(root,'evidence/INDEPENDENT_AUDIT.md'),'audit');await writeFile(path.join(root,'evidence/FTP_DEPLOYMENT_FINAL.json'),'{}');await writeFile(path.join(root,'evidence/PUBLIC_VERIFICATION_FINAL.json'),'{}');await writeFile(path.join(root,'evidence/SOURCE_PREFLIGHT.json'),JSON.stringify({summary:{integrated_country_adapters:0}}));
  for(const page of ['site/index.html','site/territorial/index.html','site/thematic/index.html','site/planning/index.html','site/database/index.html'])await writeFile(path.join(root,page),'ok');
  const checks=Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'passed',evidence_file:'evidence/ACCEPTANCE.md'}]));
  await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify({schema_version:'0.1',scope:{id:scopeId,country_area_count:1},checks,independent_audit:{status:audit,file:'evidence/INDEPENDENT_AUDIT.md',auditor:'independent-reviewer',task_thread_id:'thread-1',audited_commit:'commit-1',audited_dataset_sha256:hash},release:{public_status:'not_published',github_commit:'commit-1',ftps_receipt:'evidence/FTP_DEPLOYMENT_FINAL.json',public_verification:'evidence/PUBLIC_VERIFICATION_FINAL.json'}}));return root;
}

async function bindMatrixFixture(root,matrix){
  const dataset=structuredClone(data);dataset.analysis.coverage={...dataset.analysis.coverage,source_review_complete_country_area_count:matrix.source_review_complete_country_area_count,country_edition_complete_country_area_count:matrix.country_edition_complete_country_area_count};
  const content=JSON.stringify(dataset,null,2)+'\n',hash=createHash('sha256').update(content).digest('hex');
  await writeFile(path.join(root,'data/dashboard.json'),content);await writeFile(path.join(root,'evidence/validation.json'),JSON.stringify({errors:[],warnings:[],dataset_sha256:hash}));
  const delivery=JSON.parse(await readFile(path.join(root,'evidence/DELIVERY.json'),'utf8'));delivery.independent_audit.audited_dataset_sha256=hash;await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify(delivery));
  await writeFile(path.join(root,'evidence/SOURCE_PREFLIGHT.json'),JSON.stringify({summary:{integrated_country_adapters:matrix.broad_local_edition_country_area_count}}));
}

test('regional delivery candidate passes checks but remains not publishable before audit',async()=>{const root=await fixture();const result=await verifyRegionalDelivery(root);assert.equal(result.ok,true);assert.equal(result.publishable,false);assert.match(result.warnings.join(' '),/not publishable/);});
test('regional publication gate requires independent ACCEPT',async()=>{const root=await fixture();const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/ACCEPT/);});
test('regional publication gate rejects Americas even after ACCEPT when all country adapters are not complete',async()=>{const root=await fixture('accept');const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/COUNTRY_COMPLETION_MATRIX/);});
test('regional publication gate retains the ordinary ACCEPT contract outside the full Americas completion scope',async()=>{const root=await fixture('accept','CUSTOM:TEST');const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,true);assert.equal(result.publishable,true);});
const completeMatrix=(disposition='integrated')=>{
  const country={country_area_id:'AAA',name:'A'};
  for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={identified:true,accessed:true,acquired:true,inspected:true,geography_matched:true,adopted:true,completion_verified:true,urls:['https://example.org'],note:'Verified.',evidence:[{object_path:'raw/source.json',object_sha256:'a'.repeat(64),locator:'Exact table/API locator.',geography_match:'Exact source-code join.'}]};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition,reason:'Reviewed.',coverage_complete:true,country_edition_eligible:disposition==='integrated'}));
  const localIds=records.slice(0,12).map(row=>row.field_id),dataset={territories:[{id:'AAA',type:'country'},{id:'AAA:1',type:'adm1',country_id:'AAA'}],indicators:localIds.map((id,index)=>({id,theme:index===0?'Population':'Other'})),observations:localIds.map(id=>({territory_id:'AAA:1',indicator_id:id,status:'observed',value:1}))};
  return {matrix:buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset,generatedAt:'2026-09-18T00:00:00Z'}),records};
};
test('regional publication gate accepts Americas only after every country edition meets broad local statistical criteria',async()=>{
  const root=await fixture('accept'),{matrix,records}=completeMatrix();
  await bindMatrixFixture(root,matrix);
  const delivery=JSON.parse(await readFile(path.join(root,'evidence/DELIVERY.json'),'utf8'));delete delivery.release.ftps_receipt;delete delivery.release.public_verification;await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify(delivery));
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records:[...records,{country_area_id:'MULTI',source_id:'shared',table_id:'table',field_id:'field',numeric_cell_count:1,disposition:'not_adopted',reason:'Explicitly excluded.'}]}));
  const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,true);assert.equal(result.publishable,true);
});
test('Americas post-publication verification requires packaged deployment and HTTPS receipts',async()=>{
  const root=await fixture('accept'),{matrix,records}=completeMatrix();await bindMatrixFixture(root,matrix);
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records}));
  let delivery=JSON.parse(await readFile(path.join(root,'evidence/DELIVERY.json'),'utf8'));delivery.release.public_status='verified';delete delivery.release.ftps_receipt;delete delivery.release.public_verification;await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify(delivery));
  let result=await verifyRegionalDelivery(root,{requirePublished:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/receipt must be inside/);
  delivery.release.ftps_receipt='evidence/FTP_DEPLOYMENT_FINAL.json';delivery.release.public_verification='evidence/PUBLIC_VERIFICATION_FINAL.json';await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify(delivery));
  result=await verifyRegionalDelivery(root,{requirePublished:true});assert.equal(result.ok,true);assert.equal(result.publishable,true);
});
test('Americas source review completion cannot substitute for country edition completion',async()=>{
  const root=await fixture('accept'),{matrix,records}=completeMatrix('not_adopted');
  await bindMatrixFixture(root,matrix);
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records:[...records,{country_area_id:'MULTI',source_id:'shared',table_id:'table',field_id:'field',numeric_cell_count:1,disposition:'not_adopted',reason:'Explicitly excluded.'}]}));
  const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/country editions must be complete/);
});
test('Americas publication gate rejects unresolved numeric fields in shared sources',async()=>{
  const root=await fixture('accept'),{matrix,records}=completeMatrix();
  await bindMatrixFixture(root,matrix);
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify(matrix));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records:[...records,{country_area_id:'MULTI',source_id:'shared',table_id:'table',field_id:'field',numeric_cell_count:1,disposition:'unreviewed',reason:'Pending.'}]}));
  const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/shared MULTI sources/);
});

test('regional delivery verifies generated full data and country shard integrity',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'regional-shards-'));
  for(const dir of ['data','evidence'])await mkdir(path.join(root,dir),{recursive:true});
  const sharded=structuredClone(data),child={id:'AAA:1',name:'A1',level:'adm1',type:'adm1',parent_id:'AAA',country_id:'AAA'};
  sharded.territories[1].country_id='AAA';sharded.territories.push(child);
  sharded.observations.push({territory_id:'AAA:1',indicator_id:'POP',period:'2025',value:1,status:'observed',source_id:'values'});
  sharded.analysis.comparisons.push({parent_id:'AAA',member_ids:['AAA:1'],label:'A members',membership_note:'Test.',source_ids:['membership']});
  sharded.analysis.terminal_territory_ids=['AAA:1'];
  const canonical=JSON.stringify(sharded,null,2)+'\n',canonicalHash=createHash('sha256').update(canonical).digest('hex');
  await writeFile(path.join(root,'data','dashboard.json'),canonical);await generateSite({dataset:sharded,outDir:root,canonicalSha256:canonicalHash});
  await writeFile(path.join(root,'evidence','validation.json'),JSON.stringify({errors:[],warnings:[],dataset_sha256:canonicalHash}));
  await writeFile(path.join(root,'evidence','ACCEPTANCE.md'),'acceptance');await writeFile(path.join(root,'evidence','INDEPENDENT_AUDIT.md'),'audit');
  const checks=Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'passed',evidence_file:'evidence/ACCEPTANCE.md'}]));
  await writeFile(path.join(root,'evidence','DELIVERY.json'),JSON.stringify({schema_version:'0.1',scope:{id:'CUSTOM:TEST',country_area_count:1},checks,independent_audit:{status:'accept',file:'evidence/INDEPENDENT_AUDIT.md'},release:{public_status:'not_published'}}));
  let result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,true,JSON.stringify(result));
  await writeFile(path.join(root,'site','data','countries','AAA.json'),'{}\n');
  result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/hash does not match/);
});

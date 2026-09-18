import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {verifyRegionalDelivery} from '../scripts/verify-regional-delivery.mjs';
import {COMPLETION_DOMAINS,CENSUS_THEMES} from '../lib/country-completion-matrix.mjs';

const data={schema_version:'0.2',generated_at:'2026-09-17T00:00:00Z',country:{id:'AMR',name:'Americas',national_territory_id:'AMR'},territories:[{id:'AMR',name:'Americas',level:'national',type:'exploration_scope',parent_id:null},{id:'AAA',name:'A',level:'country',type:'country',parent_id:'AMR'}],analysis:{kind:'regional',terminal_territory_ids:['AAA'],comparisons:[{parent_id:'AMR',member_ids:['AAA'],label:'Members',membership_note:'Test.',source_ids:['membership']}],coverage:{country_area_count:1}},indicators:[{id:'POP',name:'Population',theme:'Population',unit:'people',definition:'Population.',definition_id:'pop',population:'All',measurement_method:'reported',aggregation:'official_only',source_id:'values'}],observations:[{territory_id:'AAA',indicator_id:'POP',period:'2025',value:1,status:'observed',source_id:'values'}],sources:[{id:'membership',name:'Membership',publisher:'Test',url:'https://example.org/m',status:'ready',retrieved_at:'2026-09-17',reference_period:'2025',license:'Test'},{id:'values',name:'Values',publisher:'Test',url:'https://example.org/v',status:'ready',retrieved_at:'2026-09-17',reference_period:'2025',license:'Test'}],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['test'],notes:['Test.']}};

async function fixture(audit='pending',scopeId='M49:019'){
  const root=await mkdtemp(path.join(os.tmpdir(),'regional-delivery-'));for(const dir of ['data','evidence','site','site/territorial','site/thematic','site/planning','site/database'])await mkdir(path.join(root,dir),{recursive:true});
  const content=JSON.stringify(data,null,2)+'\n';await writeFile(path.join(root,'data/dashboard.json'),content);await writeFile(path.join(root,'evidence/validation.json'),JSON.stringify({errors:[],warnings:[],dataset_sha256:createHash('sha256').update(content).digest('hex')}));await writeFile(path.join(root,'evidence/ACCEPTANCE.md'),'acceptance');await writeFile(path.join(root,'evidence/INDEPENDENT_AUDIT.md'),'audit');
  for(const page of ['site/index.html','site/territorial/index.html','site/thematic/index.html','site/planning/index.html','site/database/index.html'])await writeFile(path.join(root,page),'ok');
  const checks=Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'passed',evidence_file:'evidence/ACCEPTANCE.md'}]));
  await writeFile(path.join(root,'evidence/DELIVERY.json'),JSON.stringify({schema_version:'0.1',scope:{id:scopeId,country_area_count:1},checks,independent_audit:{status:audit,file:'evidence/INDEPENDENT_AUDIT.md'},release:{public_status:'not_published'}}));return root;
}

test('regional delivery candidate passes checks but remains not publishable before audit',async()=>{const root=await fixture();const result=await verifyRegionalDelivery(root);assert.equal(result.ok,true);assert.equal(result.publishable,false);assert.match(result.warnings.join(' '),/not publishable/);});
test('regional publication gate requires independent ACCEPT',async()=>{const root=await fixture();const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/ACCEPT/);});
test('regional publication gate rejects Americas even after ACCEPT when all country adapters are not complete',async()=>{const root=await fixture('accept');const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/COUNTRY_COMPLETION_MATRIX/);});
test('regional publication gate retains the ordinary ACCEPT contract outside the full Americas completion scope',async()=>{const root=await fixture('accept','CUSTOM:TEST');const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,true);assert.equal(result.publishable,true);});
test('regional publication gate accepts Americas only after every matrix domain and theme is complete',async()=>{
  const root=await fixture('accept'),domains=Object.fromEntries(COMPLETION_DOMAINS.map(id=>[id,{complete:true,stage:'adopted'}])),themes=Object.fromEntries(CENSUS_THEMES.map(id=>[id,{complete:true,stage:'disposed'}]));
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify({schema_version:'1.0',scope_id:'M49:019',country_area_count:1,complete_country_area_count:1,countries:[{country_area_id:'AAA',domains,themes,overall_status:'complete'}]}));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records:[{country_area_id:'MULTI',source_id:'shared',table_id:'table',field_id:'field',numeric_cell_count:1,disposition:'not_adopted',reason:'Explicitly excluded.'}]}));
  const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,true);assert.equal(result.publishable,true);
});
test('Americas publication gate rejects unresolved numeric fields in shared sources',async()=>{
  const root=await fixture('accept'),domains=Object.fromEntries(COMPLETION_DOMAINS.map(id=>[id,{complete:true,stage:'adopted'}])),themes=Object.fromEntries(CENSUS_THEMES.map(id=>[id,{complete:true,stage:'disposed'}]));
  await writeFile(path.join(root,'evidence/COUNTRY_COMPLETION_MATRIX.json'),JSON.stringify({schema_version:'1.0',scope_id:'M49:019',country_area_count:1,complete_country_area_count:1,countries:[{country_area_id:'AAA',domains,themes,overall_status:'complete'}]}));
  await writeFile(path.join(root,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify({records:[{country_area_id:'MULTI',source_id:'shared',table_id:'table',field_id:'field',numeric_cell_count:1,disposition:'unreviewed',reason:'Pending.'}]}));
  const result=await verifyRegionalDelivery(root,{requirePublishable:true});assert.equal(result.ok,false);assert.match(result.errors.join(' '),/shared MULTI sources/);
});

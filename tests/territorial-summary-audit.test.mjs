import test from 'node:test';
import assert from 'node:assert/strict';
import {auditTerritorialSummaries} from '../lib/territorial-summary-audit.mjs';

const source=id=>({id,name:id,publisher:'Test',url:`https://example.org/${id}`,status:'ready',retrieved_at:'2026-09-18',reference_period:'2020:2025',license:'Test'});
function fixture(){
  return {country:{id:'AMR',national_territory_id:'AMR'},analysis:{kind:'regional',default_period_by_indicator:{POP:'2025',RATE:'2025'}},territories:[{id:'AMR',type:'exploration_scope'},{id:'AAA',type:'country',parent_id:'AMR'},{id:'BBB',type:'country',parent_id:'AMR'}],indicators:[{id:'POP',unit:'people',source_id:'pop'},{id:'RATE',unit:'%',source_id:'rate'}],observations:[{territory_id:'AAA',indicator_id:'POP',period:'2025',value:10,status:'observed',source_id:'pop'},{territory_id:'AAA',indicator_id:'RATE',period:'2024',value:0,status:'observed',source_id:'rate'},{territory_id:'BBB',indicator_id:'POP',period:'2023',value:20,status:'observed',source_id:'pop'},{territory_id:'BBB',indicator_id:'POP',period:'2025',value:null,status:'missing',source_id:'pop'}],sources:[source('pop'),source('rate')],documents:[],gaps:[],boundaries:{type:'FeatureCollection',features:[]}};
}

test('audit checks per-territory latest values, explicit years, sources, statuses and zero',()=>{
  const result=auditTerritorialSummaries(fixture());
  assert.equal(result.ok,true);assert.equal(result.territory_count,2);assert.equal(result.latest_indicator_checks,3);assert.equal(result.explicit_observation_checks,3);assert.equal(result.zero_value_checks,1);assert.deepEqual(result.errors,[]);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {verifyCrossCountryIsolation} from '../scripts/verify-cross-country-isolation.mjs';

test('cross-country verifier rejects no foreign route, CSV or planning evidence in a regional dataset',()=>{
  const source=id=>({id,name:`Source ${id}`,publisher:'Test',url:`https://example.org/${id}`,status:'ready',retrieved_at:'2026-09-18',reference_period:'2024',license:'Test'});
  const indicator=(id,source_id)=>({id,name:id,theme:'Test',unit:'people',definition:id,source_id,aggregation:'none',measurement_method:'reported'});
  const dataset={schema_version:'0.2',generated_at:'2026-09-18T00:00:00Z',country:{id:'AMR',name:'Americas',national_territory_id:'AMR'},territories:[{id:'AMR',name:'Americas',level:'national',type:'exploration_scope',parent_id:null},{id:'AAA',name:'A',level:'country',type:'country',parent_id:'AMR'},{id:'BBB',name:'B',level:'country',type:'country',parent_id:'AMR'}],analysis:{kind:'regional',comparisons:[{parent_id:'AMR',member_ids:['AAA','BBB']}],coverage:{country_area_count:2,census_integrated_country_ids:[]}},indicators:[indicator('A_ONLY','a'),indicator('B_ONLY','b')],observations:[{territory_id:'AAA',indicator_id:'A_ONLY',period:'2024',value:1,status:'observed',source_id:'a'},{territory_id:'BBB',indicator_id:'B_ONLY',period:'2024',value:2,status:'observed',source_id:'b'}],sources:[source('a'),source('b')],documents:[],gaps:[],boundaries:{type:'FeatureCollection',features:[]},collection:{status:'partial'}};
  const result=verifyCrossCountryIsolation(dataset);
  assert.equal(result.ok,true);assert.equal(result.country_count,2);assert.equal(result.route_checks,2);assert.equal(result.output_checks,12);assert.deepEqual(result.errors,[]);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {buildRegionalPilot,CENTRAL_AMERICA_CONFIG} from '../lib/regional-pilot.mjs';
import {mergeUnPopulation,validateNormalizedUnPopulation} from '../lib/un-population-adapter.mjs';
import {resolvedObservation} from '../scaffold/site/aggregation.mjs';
import {validateDataset} from '../lib/validate.mjs';

const source=id=>({id,name:id,publisher:'Test',url:`https://example.test/${id}`,status:'ready',retrieved_at:'2026-09-15T00:00:00Z',license:'test'});
function world(){
  const ids=CENTRAL_AMERICA_CONFIG.member_ids;
  return {schema_version:'0.2',generated_at:'2026-09-15T00:00:00Z',country:{id:'WLD',name:'World',national_territory_id:'WLD'},territories:ids.map(id=>({id,country_id:id,name:id,level:'country',type:'country',parent_id:'M49:013',official_code:id,code_system:'test',boundary_version:null})),indicators:[{id:'SP.POP.TOTL',name:'WDI population',theme:'Population',unit:'people',definition:'test',aggregation:'official_only',source_id:'wdi'}],observations:ids.map((id,index)=>({territory_id:id,indicator_id:'SP.POP.TOTL',period:'2025',value:index+1,status:'observed',source_id:'wdi'})),sources:[source('un-m49'),source('natural-earth'),{...source('wdi'),geographic_level:'world_country_series'}],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[{category:'indicator_coverage',status:'ready',detail:'Population',source_id:'wdi'}],collection:{status:'partial',adapters:['test'],notes:[]}};
}
function normalized(){
  const periods=['2023','2024','2025','2026'],observations=periods.flatMap((period,p)=>CENTRAL_AMERICA_CONFIG.member_ids.map((id,i)=>({territory_id:id,indicator_id:'UN_WPP_POP_TOTAL',period,value:1000+p*100+i,status:'observed',source_id:'un-wpp',series_stage:period==='2023'?'estimate':'medium_projection'})));
  return {schema_version:'1.0',scope_id:CENTRAL_AMERICA_CONFIG.id,replaces_indicator_id:'SP.POP.TOTL',indicator:{id:'UN_WPP_POP_TOTAL',name:'UN population estimate / medium projection',theme:'Population',unit:'people',definition:'UN population',aggregation:'sum',series_family:'international_reference',display_role:'context',period_policy:'same_period',series_stage_by_period:{2023:'estimate',2024:'medium_projection',2025:'medium_projection',2026:'medium_projection'},source_id:'un-wpp'},source:{...source('un-wpp'),sha256:'a'.repeat(64)},observations,summary:{periods,default_display_period:'2026',regional_totals:Object.fromEntries(periods.map(period=>[period,observations.filter(row=>row.period===period).reduce((sum,row)=>sum+row.value,0)]))}};
}

test('UN population adapter replaces duplicate WDI population and calculates complete same-year context',()=>{
  const input=normalized();assert.equal(validateNormalizedUnPopulation(input),input);
  const result=mergeUnPopulation(buildRegionalPilot(world()),input);
  assert.deepEqual(validateDataset(result).errors,[]);
  assert.equal(result.indicators.some(row=>row.id==='SP.POP.TOTL'),false);
  assert.equal(result.sources.some(row=>row.id==='wdi'),false);
  assert.equal(result.analysis.population_context.reference_period,'2026');
  const total=resolvedObservation(result,result.country.national_territory_id,'UN_WPP_POP_TOTAL','2026');
  assert.equal(total.status,'calculated');assert.equal(total.value,input.summary.regional_totals['2026']);assert.equal(total.components.length,7);
});

test('UN population adapter rejects an incomplete country-period cover',()=>{
  const input=normalized();input.observations.pop();
  assert.throws(()=>validateNormalizedUnPopulation(input),/coverage is incomplete/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {indicatorsForTerritorialScope,initialState,evidenceCsv,seriesGeometry,areaObservationState} from '../scaffold/site/model.mjs';
import {renderWppDemographics} from '../scaffold/site/un-demographics.mjs';

function sample(){
  const ages=[...Array(20)].map((_,i)=>`${i*5}-${i*5+4}`).concat('100+');
  const profile=(id,period)=>({territory_id:id,period,ages,male:ages.map(()=>10),female:ages.map(()=>11)});
  return {schema_version:'0.2',generated_at:'2026-09-23T00:00:00Z',country:{id:'WLD',name:'World',national_territory_id:'WLD'},
    analysis:{kind:'world',supranational_indicator_ids:['UN_WPP_POP_TOTAL','UN_WPP_POP_MALE','UN_WPP_POP_FEMALE','UN_WPP_FERTILITY'],default_period_by_indicator:{UN_WPP_POP_TOTAL:'2026',UN_WPP_POP_MALE:'2026',UN_WPP_POP_FEMALE:'2026'},population_pyramids:{'WLD@2000':profile('WLD','2000'),'WLD@2026':profile('WLD','2026')}},
    territories:[{id:'WLD',name:'World',level:'national',type:'exploration_scope',parent_id:null},{id:'M49:019',name:'Americas',level:'continent',type:'exploration_scope',parent_id:'WLD'},{id:'AAA',country_id:'AAA',name:'Alpha',level:'country',type:'country',parent_id:'M49:019'},{id:'AAA:city',country_id:'AAA',name:'Alpha city',level:'municipality',type:'municipality',parent_id:'AAA'}],
    indicators:[{id:'CENSUS',name:'Official census population',theme:'Census',unit:'people',definition:'Census',source_id:'national',series_family:'census'},...['UN_WPP_POP_TOTAL','UN_WPP_POP_MALE','UN_WPP_POP_FEMALE','UN_WPP_FERTILITY'].map(id=>({id,name:id,theme:'Population',unit:'people',definition:id,source_id:'un',series_family:'international_reference'}))],
    observations:[{territory_id:'AAA',indicator_id:'CENSUS',period:'2018',value:800,status:'observed',source_id:'national'},...['WLD','M49:019','AAA'].flatMap(id=>['UN_WPP_POP_TOTAL','UN_WPP_POP_MALE','UN_WPP_POP_FEMALE'].map((indicator_id,index)=>({territory_id:id,indicator_id,period:'2026',value:[1000,490,510][index],status:'observed',source_id:'un'}))),{territory_id:'WLD',indicator_id:'UN_WPP_FERTILITY',period:'2026',value:2.1,status:'observed',source_id:'un'}],
    sources:[{id:'un',name:'UN WPP',url:'https://population.un.org/wpp/',retrieved_at:'2026-09-23T00:00:00Z',status:'ready',geographic_level:'world_multi_scope_series'},{id:'national',name:'Census',url:'https://example.org/census',retrieved_at:'2026-09-23T00:00:00Z',status:'ready',geographic_level:'national',country_id:'AAA'}]};
}

test('supra-country diagnostic and evidence exclude national Census and unavailable regional rates',()=>{
  const data=sample(),ids=indicatorsForTerritorialScope(data,'M49:019').map(row=>row.id);
  assert.deepEqual(ids,['UN_WPP_POP_TOTAL','UN_WPP_POP_MALE','UN_WPP_POP_FEMALE']);
  assert.equal(initialState(data,'?territory=M49:019&metric=CENSUS').metric,'UN_WPP_POP_TOTAL');
  assert.doesNotMatch(evidenceCsv(data,'M49:019','2026'),/CENSUS/);
  assert.ok(indicatorsForTerritorialScope(data,'AAA').some(row=>row.id==='CENSUS'));
});

test('country-only international inflation can be compared without inventing a regional value',()=>{
  const data=sample();
  data.analysis.supranational_indicator_ids.push('IMF_INFLATION');
  data.indicators.push({id:'IMF_INFLATION',name:'Annual CPI change',theme:'Economy',unit:'%',source_id:'imf',series_family:'international_reference',period_policy:'same_period'});
  data.observations.push({territory_id:'AAA',indicator_id:'IMF_INFLATION',period:'2024',value:4.2,status:'observed',source_id:'imf'});
  assert.ok(indicatorsForTerritorialScope(data,'M49:019').some(row=>row.id==='IMF_INFLATION'));
  assert.equal(initialState(data,'?territory=M49:019&metric=IMF_INFLATION&period=2024').metric,'IMF_INFLATION');
  assert.equal(areaObservationState(data,'M49:019','IMF_INFLATION','2024').value,null);
});

test('age pyramid compares 2000 in gray with selected year and sex split as a pie',()=>{
  const markup=renderWppDemographics(sample(),'WLD','2026','ja');
  assert.match(markup,/2000/);assert.match(markup,/2026/);
  assert.match(markup,/pyramid-past/);assert.match(markup,/pyramid-male/);assert.match(markup,/sex-pie-male/);
  assert.match(markup,/男性/);assert.match(markup,/女性/);
});

test('annual chart leaves the unobserved 2001–2022 interval unconnected',()=>{
  const rows=['2000','2023','2024'].map((period,index)=>({period,value:100+index,status:'observed'}));
  const chart=seriesGeometry(rows);
  assert.equal(chart.segments.length,2);
  assert.notEqual(chart.points[1].x-chart.points[0].x,chart.points[2].x-chart.points[1].x);
});

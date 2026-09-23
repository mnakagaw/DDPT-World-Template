import test from 'node:test';
import assert from 'node:assert/strict';
import {buildAmericas} from '../lib/americas-adapter.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {initialState,comparisonLevelForArea,comparisonRows,areaObservationState} from '../scaffold/site/model.mjs';

const caIds=['BLZ','GTM','SLV','HND','NIC','CRI','PAN'];
const otherIds=['MEX','USA','CAN',...Array.from({length:47},(_,index)=>`X${String(index).padStart(2,'0')}`)];
const countryIds=[...caIds,...otherIds];
const source=(id,extra={})=>({id,name:id,publisher:'Synthetic test',url:`https://example.org/${id}`,status:'ready',retrieved_at:'2026-09-17T00:00:00Z',reference_period:'Synthetic',license:'Test fixture',...extra});
const indicator={id:'SP.POP.TOTL',name:'Population',theme:'Population',unit:'people',definition:'Synthetic total population.',definition_id:'population-total',population:'All residents',measurement_method:'source reported',aggregation:'official_only',series_family:'international_reference',display_role:'context',period_policy:'same_period',source_id:'population-source'};
const feature=id=>({type:'Feature',properties:{territory_id:id,source_id:'natural-earth',geometry_edition:'test'},geometry:{type:'Polygon',coordinates:[[[0,0],[1,0],[1,1],[0,0]]]}});

function worldFixture(){
  const regions=[{id:'M49:021',name:'Northern America'},{id:'M49:005',name:'South America'},{id:'CUSTOM:CAM-CAR',name:'Central America + Caribbean'}];
  const memberships=new Map(countryIds.map((id,index)=>[id,regions[index%3].id]));
  const territories=[
    {id:'WLD',name:'World',level:'national',type:'exploration_scope',parent_id:null,official_code:'001',code_system:'UN M49',boundary_version:null,source_id:'un-m49'},
    {id:'M49:019',name:'Americas',level:'continent',type:'exploration_scope',parent_id:'WLD',official_code:'019',code_system:'UN M49',boundary_version:null,source_id:'un-m49'},
    ...regions.map(region=>({...region,level:'region',type:'exploration_scope',parent_id:'M49:019',official_code:region.id.slice(-3),code_system:'UN M49',boundary_version:null,source_id:'un-m49'})),
    ...countryIds.map(id=>({id,country_id:id,name:id,level:'country',type:'country',parent_id:memberships.get(id),official_code:id,code_system:'UN M49',boundary_version:null,source_id:'un-m49'}))
  ];
  const comparison=parent_id=>({parent_id,member_ids:countryIds.filter(id=>memberships.get(id)===parent_id),label:`Countries in ${parent_id}`,membership_note:'Synthetic non-overlapping membership.',source_ids:['un-m49']});
  return {schema_version:'0.2',generated_at:'2026-09-17T00:00:00Z',country:{id:'WLD',name:'World',requested_name:'World',locale:'en',national_territory_id:'WLD'},territories,analysis:{kind:'world',terminal_territory_ids:countryIds,comparisons:[{parent_id:'M49:019',member_ids:countryIds,label:'Countries and areas in Americas',membership_note:'Synthetic non-overlapping membership.',source_ids:['un-m49']},...regions.map(region=>comparison(region.id))],country_sites:[]},indicators:[indicator],observations:countryIds.map((id,index)=>({territory_id:id,indicator_id:indicator.id,period:'2026',value:index+1,status:'observed',source_id:'population-source'})),sources:[source('un-m49'),source('population-source',{geographic_level:'world_country_series'}),source('natural-earth')],boundaries:{type:'FeatureCollection',features:countryIds.slice(0,10).map(feature)},documents:[],gaps:[],collection:{status:'partial',adapters:['synthetic-world'],notes:['Synthetic fixture.'],boundary_coverage:[]}};
}

function centralFixture(){
  const census={id:'CENSUS_POP_TOTAL',name:'Official census population',theme:'Population',unit:'people',definition:'Synthetic official census population.',definition_id:'census-population',population:'Census population',measurement_method:'official census',aggregation:'sum',series_family:'census',display_role:'primary',period_policy:'latest_available_by_component',source_id:'census-source'};
  const local={id:'GTM:ADM1',country_id:'GTM',name:'Guatemala test area',level:'adm1',type:'department',parent_id:'GTM',official_code:'01',code_system:'Synthetic',boundary_version:null,source_id:'census-source'};
  return {schema_version:'0.2',generated_at:'2026-09-17T00:00:00Z',country:{id:'CAM',name:'Central America',national_territory_id:'CUSTOM:CA7'},territories:[{id:'CUSTOM:CA7',name:'Central America',level:'national',type:'exploration_scope',parent_id:null},...caIds.map(id=>({id,country_id:id,name:id,level:'country',type:'country',parent_id:'CUSTOM:CA7'})),local],analysis:{kind:'regional',terminal_territory_ids:['GTM:ADM1',...caIds.filter(id=>id!=='GTM')],comparisons:[{parent_id:'CUSTOM:CA7',member_ids:caIds,label:'Seven countries',membership_note:'Synthetic.',source_ids:['un-m49']},{parent_id:'GTM',member_ids:['GTM:ADM1'],label:'Guatemala areas',membership_note:'Synthetic.',source_ids:['un-m49']}],default_period_by_indicator:{CENSUS_POP_TOTAL:'latest-available'},aggregation:{policy:'exact_then_complete_cover',rules:[{indicator_id:'CENSUS_POP_TOTAL',method:'sum',completeness:'full_cover',period_policy:'latest_available_by_component',label:'Census sum',note:'Only a complete cover is calculated.'}]},pilot:{country_ids:caIds},census_history:{schema_version:'1.0',as_of_year:2026,checked_at:'2026-09-17',countries:caIds.map(id=>({country_id:id})),reference_boundaries:{type:'FeatureCollection',features:[]}}},indicators:[census],observations:[{territory_id:'GTM',indicator_id:'CENSUS_POP_TOTAL',period:'2018',value:10,status:'observed',source_id:'census-source'},{territory_id:'GTM:ADM1',indicator_id:'CENSUS_POP_TOTAL',period:'2018',value:10,status:'observed',source_id:'census-source'}],sources:[source('un-m49'),source('census-source')],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['synthetic-census'],notes:['Synthetic fixture.']}};
}

function unPopulationFixture(){
  const found=countryIds.slice(0,-2),periods=['2023','2024','2025','2026'];
  return {schema_version:'1.0',scope_id:'M49:019',replaces_indicator_id:'SP.POP.TOTL',indicator:{id:'UN_WPP_POP_TOTAL',name:'UN population',theme:'Population',unit:'people',definition:'Synthetic UN population.',definition_id:'un-population',population:'All',measurement_method:'estimate and projection',aggregation:'sum',series_family:'international_reference',display_role:'context',period_policy:'same_period',source_id:'un-wpp'},source:source('un-wpp'),observations:periods.flatMap((period,p)=>found.map((id,index)=>({territory_id:id,indicator_id:'UN_WPP_POP_TOTAL',period,value:1000+p+index,status:'observed',source_id:'un-wpp'}))),summary:{registry_country_ids:countryIds,country_ids:found,missing_country_ids:countryIds.slice(-2),default_display_period:'2026'}};
}

test('Americas adapter keeps all M49 countries and three navigation regions',()=>{
  const result=buildAmericas(worldFixture()),root=result.territories.find(area=>area.id==='M49:019');
  assert.equal(result.country.id,'AMR');assert.equal(root.level,'national');assert.equal(root.parent_id,null);
  assert.equal(result.territories.filter(area=>area.type==='country').length,57);
  assert.deepEqual(result.territories.filter(area=>area.parent_id==='M49:019').map(area=>area.id).sort(),['CUSTOM:CAM-CAR','M49:005','M49:021']);
  assert.equal(result.analysis.comparisons.find(item=>item.parent_id==='M49:019').member_ids.length,57);
  assert.deepEqual(validateDataset(result).errors,[]);
});

test('regional thematic comparison stays inside the selected Americas subregion',()=>{
  const result=buildAmericas(worldFixture()),selected='M49:005';
  const level=comparisonLevelForArea(result,selected);
  assert.equal(level,'country');
  assert.equal(comparisonLevelForArea(result,'M49:019'),'country');
  const state=initialState(result,`?country=AMR&territory=${encodeURIComponent(selected)}&metric=SP.POP.TOTL&period=latest-available&level=${level}&type=exploration_scope&code=005`);
  const expected=result.analysis.comparisons.find(item=>item.parent_id===selected).member_ids;
  assert.deepEqual(comparisonRows(result,state).map(row=>row.area.id).sort(),[...expected].sort());
  assert.ok(comparisonRows(result,state).every(row=>row.area.parent_id===selected));
});

test('Americas overlay reuses known census evidence without extending it to other countries',()=>{
  const result=buildAmericas(worldFixture(),{centralAmerica:centralFixture()});
  assert.equal(result.analysis.coverage.country_area_count,57);
  assert.equal(result.analysis.coverage.census_integrated_country_ids.length,7);
  assert.equal(result.analysis.coverage.census_integrated_territory_count,1);
  assert.ok(result.territories.some(area=>area.parent_id==='GTM'));
  assert.ok(result.observations.some(row=>row.territory_id==='GTM'&&row.indicator_id==='CENSUS_POP_TOTAL'));
  assert.equal(result.observations.some(row=>row.territory_id==='MEX'&&row.indicator_id==='CENSUS_POP_TOTAL'),false);
  assert.equal(result.observations.some(row=>row.territory_id==='M49:019'&&row.indicator_id==='CENSUS_POP_TOTAL'),false);
  assert.ok(result.analysis.terminal_territory_ids.includes('MEX'));
  assert.equal(result.analysis.terminal_territory_ids.includes('GTM'),false);
  assert.equal(result.analysis.census_history.catalog_status,'partial');
  assert.deepEqual(validateDataset(result).errors,[]);
});

test('Americas UN overlay covers available source rows and preserves missing registry entries',()=>{
  const unPopulation=unPopulationFixture(),result=buildAmericas(worldFixture(),{centralAmerica:centralFixture(),unPopulation});
  assert.equal(result.analysis.coverage.un_wpp_country_area_count,55);
  assert.deepEqual(result.analysis.coverage.un_wpp_missing_country_area_ids,countryIds.slice(-2));
  assert.equal(result.observations.filter(row=>row.indicator_id==='UN_WPP_POP_TOTAL').length,220);
  assert.equal(result.observations.some(row=>row.territory_id===countryIds.at(-1)&&row.indicator_id==='UN_WPP_POP_TOTAL'),false);
  assert.match(result.gaps.find(gap=>gap.category==='un_wpp_country_area_coverage').detail,/55 of 57/);
  assert.match(result.analysis.aggregation.rules.find(rule=>rule.indicator_id==='UN_WPP_POP_TOTAL').note,/Missing members remain missing/);
  assert.deepEqual(validateDataset(result).errors,[]);
});

test('published South America WPP value completes the continental cover without filling missing countries',()=>{
  const unPopulation=unPopulationFixture();
  const missingInCentral=countryIds.at(-1),missingInSouth=countryIds.at(-2);
  unPopulation.source.sha256='a'.repeat(64);
  unPopulation.observations.push(...['2023','2024','2025','2026'].map(period=>({territory_id:missingInCentral,indicator_id:'UN_WPP_POP_TOTAL',period,value:500,status:'observed',source_id:'un-wpp'})));
  unPopulation.summary.country_ids.push(missingInCentral);
  unPopulation.summary.missing_country_ids=[missingInSouth];
  unPopulation.regional_source={...source('un-wpp-south',{geographic_level:'world_region_series',territory_id:'M49:005',sha256:unPopulation.source.sha256})};
  unPopulation.regional_observations=['2023','2024','2025','2026'].map(period=>({territory_id:'M49:005',indicator_id:'UN_WPP_POP_TOTAL',period,value:100000,status:'observed',source_id:'un-wpp-south'}));
  const result=buildAmericas(worldFixture(),{unPopulation});
  const continent=areaObservationState(result,'M49:019','UN_WPP_POP_TOTAL','2026');
  assert.equal(continent.status,'calculated');assert.ok(continent.value>100000);
  assert.ok(continent.components.some(item=>item.territory_id==='M49:005'));
  assert.equal(areaObservationState(result,missingInSouth,'UN_WPP_POP_TOTAL','2026').value,null);
  assert.equal(result.analysis.comparisons.find(item=>item.parent_id==='M49:019').member_ids.length,57);
  assert.deepEqual(validateDataset(result).errors,[]);
  const wrong=structuredClone(result);
  wrong.observations.find(row=>row.territory_id==='M49:005'&&row.indicator_id==='UN_WPP_POP_TOTAL').territory_id='M49:021';
  assert.match(validateDataset(wrong).errors.join(' '),/World region series .*cannot supply this regional observation/);
});

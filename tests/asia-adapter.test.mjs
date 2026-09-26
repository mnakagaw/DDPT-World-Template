import test from 'node:test';
import assert from 'node:assert/strict';
import {buildAsia} from '../lib/asia-adapter.mjs';
import {comparisonRows,initialState,routeQuery,selectHierarchyOption,selectTerritory,territorialIndicatorState,thematicReferenceState} from '../scaffold/site/model.mjs';
import {translateText} from '../scaffold/site/i18n.mjs';
import {sourceScopeNote,diagnosticCsv} from '../scaffold/site/diagnostic.mjs';

const source=id=>({id,name:id,publisher:'Synthetic',url:`https://example.org/${id}`,status:'ready',retrieved_at:'2026-09-26',reference_period:'2024',license:'Test'});
const area=(id,name,parent_id,type='exploration_scope',country_id)=>({id,name,parent_id,type,country_id,level:type==='country'?'country':'macroregion',official_code:id,code_system:'UN M49',boundary_version:null,source_id:'un-m49'});
const indicator=(id,source_id,unit='people')=>({id,name:id,theme:'Population',unit,definition:id,definition_id:id,population:'All residents',measurement_method:'source reported',aggregation:'official_only',series_family:'international_reference',display_role:'context',period_policy:'same_period',source_id});

function fixture(){
  const territories=[area('WLD','World',null),area('M49:019','Americas','WLD'),area('M49:142','Asia','WLD'),
    area('M49:030','Eastern Asia','M49:142'),area('M49:035','South-eastern Asia','M49:142'),
    area('JPN','Japan','M49:030','country','JPN'),area('LAO','Lao PDR','M49:035','country','LAO'),
    area('LAO:ADM1','Lao region','LAO','province','LAO'),area('USA','United States','M49:019','country','USA'),
    area('USA:ADM1','US state','USA','province','USA')];
  const comparisons=[{parent_id:'M49:142',member_ids:['M49:030','M49:035'],label:'Asian subregions',membership_note:'UN M49',source_ids:['un-m49']},
    {parent_id:'M49:030',member_ids:['JPN'],label:'Eastern Asia',membership_note:'UN M49',source_ids:['un-m49']},
    {parent_id:'M49:035',member_ids:['LAO'],label:'South-eastern Asia',membership_note:'UN M49',source_ids:['un-m49']}];
  const observations=[{territory_id:'M49:142',indicator_id:'UN_WPP_POP_TOTAL',period:'2024',value:300,status:'observed',source_id:'wpp'},
    {territory_id:'JPN',indicator_id:'UN_WPP_POP_TOTAL',period:'2024',value:100,status:'observed',source_id:'wpp'},
    {territory_id:'LAO',indicator_id:'UN_WPP_POP_TOTAL',period:'2024',value:20,status:'observed',source_id:'wpp'},
    {territory_id:'USA',indicator_id:'UN_WPP_POP_TOTAL',period:'2024',value:400,status:'observed',source_id:'wpp'},
    {territory_id:'LAO:ADM1',indicator_id:'LAO_CENSUS_POP',period:'2020',value:7,status:'observed',source_id:'lao-census'},
    {territory_id:'USA:ADM1',indicator_id:'USA_CENSUS_POP',period:'2020',value:8,status:'observed',source_id:'usa-census'}];
  return {schema_version:'0.2',generated_at:'2026-09-26T00:00:00Z',country:{id:'WLD',name:'World',national_territory_id:'WLD'},
    territories,indicators:[indicator('UN_WPP_POP_TOTAL','wpp'),indicator('LAO_CENSUS_POP','lao-census'),indicator('USA_CENSUS_POP','usa-census')],
    observations,sources:[source('un-m49'),source('natural-earth'),source('wpp'),source('lao-census'),source('usa-census')],
    boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['world'],boundary_coverage:[]},
    analysis:{kind:'world',comparisons,terminal_territory_ids:['JPN','LAO:ADM1','USA:ADM1'],
      supranational_indicator_ids:['UN_WPP_POP_TOTAL'],default_period_by_indicator:{UN_WPP_POP_TOTAL:'2024'},
      population_pyramids:{'M49:142@2000':{},'JPN@2024':{},'USA@2024':{}},
      census_source_preflight:{records:[{country_id:'JPN'},{country_id:'LAO'},{country_id:'USA'}]}}};
}

test('Asia scope retains its source-reported values and verified domestic branch without Americas leakage',()=>{
  const asia=buildAsia(fixture());
  assert.equal(asia.country.national_territory_id,'M49:142');
  assert.equal(asia.territories.find(row=>row.id==='M49:142').parent_id,null);
  assert.deepEqual(asia.territories.filter(row=>row.type==='country').map(row=>row.id),['JPN','LAO']);
  assert.ok(asia.territories.some(row=>row.id==='LAO:ADM1'));
  assert.ok(!asia.territories.some(row=>row.id==='USA'));
  assert.ok(!asia.indicators.some(row=>row.id==='USA_CENSUS_POP'));
  assert.ok(!asia.sources.some(row=>row.id==='usa-census'));
  assert.deepEqual(asia.analysis.census_source_preflight.records.map(row=>row.country_id),['JPN','LAO']);
  assert.deepEqual(Object.keys(asia.analysis.population_pyramids).sort(),['JPN@2024','M49:142@2000']);
  assert.deepEqual(asia.analysis.coverage.census_integrated_country_ids,['LAO']);
  assert.equal(territorialIndicatorState(asia,'M49:142','UN_WPP_POP_TOTAL','latest-available').result.value,300);
});

test('Asia comparison uses only the selected M49 subregion',()=>{
  const asia=buildAsia(fixture());
  const state=initialState(asia,'?country=ASI&territory=M49%3A035&metric=UN_WPP_POP_TOTAL&period=latest-available');
  assert.deepEqual(comparisonRows(asia,state).map(row=>row.area.id),['LAO']);
  assert.equal(asia.analysis.coverage.country_area_count,2);
  assert.equal(asia.analysis.coverage.un_wpp_country_area_count,2);
  assert.equal(translateText('Asia','ja'),'アジア');
  assert.equal(translateText('South-eastern Asia','es'),'Asia Sudoriental');
});

test('Asia hierarchy keeps a shared GDP indicator and chosen year when a country or parent is selected',()=>{
  const asia=buildAsia(fixture());
  asia.indicators.push(indicator('UN_AMA_GDP_CURRENT_USD','ama','US$'));
  asia.observations.push(
    {territory_id:'M49:142',indicator_id:'UN_AMA_GDP_CURRENT_USD',period:'2024',value:500,status:'observed',source_id:'ama'},
    {territory_id:'M49:035',indicator_id:'UN_AMA_GDP_CURRENT_USD',period:'2024',value:90,status:'observed',source_id:'ama'},
    {territory_id:'LAO',indicator_id:'UN_AMA_GDP_CURRENT_USD',period:'2024',value:20,status:'observed',source_id:'ama'},
    {territory_id:'JPN',indicator_id:'UN_AMA_GDP_CURRENT_USD',period:'2024',value:200,status:'observed',source_id:'ama'}
  );
  asia.analysis.supranational_indicator_ids.push('UN_AMA_GDP_CURRENT_USD');
  const start=initialState(asia,'?country=ASI&territory=M49%3A142&metric=UN_AMA_GDP_CURRENT_USD&period=2024');
  const region=selectHierarchyOption(asia,start,'M49:142','area:M49:035');
  const country=selectHierarchyOption(asia,region,'M49:035','area:LAO');
  assert.equal(region.level,'country');
  for(const state of [region,country]){
    assert.equal(state.metric,'UN_AMA_GDP_CURRENT_USD');
    assert.equal(state.period,'2024');
  }
  assert.equal(territorialIndicatorState(asia,country.selected,country.metric,country.period).result.value,20);
  assert.equal(thematicReferenceState(asia,start,'2024').observation.value,500);
  assert.equal(thematicReferenceState(asia,region,'2024').observation.value,90);
  assert.equal(thematicReferenceState(asia,region,'2024').area.name,'South-eastern Asia');
  assert.equal(thematicReferenceState(asia,country,'2024').observation.value,20);
  const backToRegion=selectHierarchyOption(asia,country,'M49:142','area:M49:035');
  assert.equal(backToRegion.selected,'M49:035');
  assert.equal(backToRegion.metric,'UN_AMA_GDP_CURRENT_USD');
  assert.equal(backToRegion.period,'2024');
  assert.equal(backToRegion.level,region.level);
  assert.equal(routeQuery(asia,backToRegion),routeQuery(asia,region));
  assert.equal(territorialIndicatorState(asia,backToRegion.selected,backToRegion.metric,backToRegion.period).result.value,90);
  assert.equal(thematicReferenceState(asia,backToRegion,'2024').observation.value,90);
  const otherCountry=selectTerritory(asia,country,'JPN');
  assert.equal(otherCountry.metric,'UN_AMA_GDP_CURRENT_USD');
  assert.equal(otherCountry.period,'2024');
  const branchOnly=initialState(asia,'?country=ASI&territory=LAO&metric=LAO_CENSUS_POP&period=2020');
  assert.equal(selectTerritory(asia,branchOnly,'JPN').metric,'UN_WPP_POP_TOTAL');
});

test('a provider regional scope difference is disclosed in the screen copy and diagnostic export',()=>{
  const asia=buildAsia(fixture());
  asia.analysis.source_scope_differences=[{territory_id:'M49:142',source_id:'wpp',listed_member_count:2,difference:23011294}];
  assert.match(sourceScopeNote(asia,'M49:142','UN_WPP_POP_TOTAL','en'),/Taiwan/);
  assert.match(sourceScopeNote(asia,'M49:142','UN_WPP_POP_TOTAL','ja'),/23,011,294/);
  assert.match(diagnosticCsv(asia,'M49:142','2024'),/Regional source scope note/);
  assert.match(diagnosticCsv(asia,'M49:142','2024'),/Taiwan/);
  assert.equal(sourceScopeNote(asia,'JPN','UN_WPP_POP_TOTAL','en'),'');
  asia.indicators.push(indicator('UN_AMA_GDP_CURRENT_USD','ama','US$'));
  asia.analysis.source_scope_differences.push({kind:'published_vs_listed_sum_unreconciled',territory_id:'M49:142',indicator_id:'UN_AMA_GDP_CURRENT_USD',source_id:'ama',reference_period:'2024',listed_member_count:2,difference:797003778521});
  assert.match(sourceScopeNote(asia,'M49:142','UN_AMA_GDP_CURRENT_USD','en'),/aggregate composition and adjustments/);
  assert.match(sourceScopeNote(asia,'M49:142','UN_AMA_GDP_CURRENT_USD','ja'),/照合できていません/);
});

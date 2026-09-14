import test from 'node:test';
import assert from 'node:assert/strict';
import {validateDataset} from '../lib/validate.mjs';
import {validateAnalysis} from '../lib/analysis-validation.mjs';
import {comparisonSet,internalComparison,observationMeaning,observationContext,colorForComparison,NO_COMPARISON_COLOR,isTerminalTerritory} from '../scaffold/site/analysis.mjs';
import {initialState,selectTerritory,selectHierarchyOption,observationState,routeQuery} from '../scaffold/site/model.mjs';
import {analysisFixture} from './analysis-fixture.mjs';
import {fixture} from './fixture.mjs';

const errors=data=>validateDataset(data).errors.join('\n');
const freeze=value=>{if(value && typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
test('world exploration scope and legacy country datasets both validate',()=>{
  assert.deepEqual(validateDataset(analysisFixture()).errors,[]);
  assert.deepEqual(validateDataset(fixture()).errors,[]);
  assert.deepEqual(comparisonSet(fixture(),'TST').members.map(area=>area.id),['TST-A','TST-B']);
});
test('configured world comparison skips geographic tiers while default comparison uses direct children',()=>{
  const data=analysisFixture();
  assert.deepEqual(comparisonSet(data,'WLD').members.map(area=>area.id),['TST','OTH']);
  assert.equal(comparisonSet(data,'WLD').explicit,true);
  assert.deepEqual(comparisonSet(data,'TST').members.map(area=>area.id),['north','south']);
  assert.equal(comparisonSet(data,'TST').explicit,false);
  assert.deepEqual(comparisonSet(data,'north').members.map(area=>area.id),['river','lake']);
  assert.equal(comparisonSet(data,'not-a-parent').members.length,0);
});
test('full comparison retains thirty areas, exact zero, missing, duplicate names and absent boundaries',()=>{
  const result=internalComparison(analysisFixture(),'river','people','2024');
  assert.equal(result.rows.length,30);
  const zero=result.rows.find(row=>row.area.id==='city'),missing=result.rows.find(row=>row.area.id==='missing-city');
  assert.equal(zero.value,0);assert.equal(zero.comparable,true);
  assert.equal(result.rows.filter(row=>row.area.name==='Same name').length,2);
  assert.equal(missing.status,'not_collected');assert.equal(missing.value,null);assert.equal(missing.comparable,false);assert.equal(missing.boundary,null);
  assert.equal(result.features.length,29);
  assert.equal(colorForComparison(result,missing),NO_COMPARISON_COLOR);
  assert.notEqual(colorForComparison(result,zero),NO_COMPARISON_COLOR);
});
test('comparison does not infer parent totals or substitute a different period',()=>{
  const data=analysisFixture(),comparison=internalComparison(data,'north','people','2024');
  assert.equal(observationState(data,'north','people','2024').value,null);
  assert.equal(comparison.rows.find(row=>row.area.id==='river').value,400);
  assert.equal(comparison.rows.find(row=>row.area.id==='lake').status,'missing');
  const absentYear=internalComparison(data,'river','people','2025');
  assert.ok(absentYear.rows.every(row=>row.value===null && !row.comparable));
  assert.equal(absentYear.period,'2025');assert.deepEqual(absentYear.scale.breaks,[]);
  const exactOld=internalComparison(data,'river','people','2023');
  assert.equal(exactOld.rows.find(row=>row.area.id==='city').value,90);
  assert.equal(exactOld.rows.find(row=>row.area.id==='municipality').value,null);
});
test('comparison is read-only and selecting the same ancestor clears a city with metric and period intact',()=>{
  const data=freeze(analysisFixture()),state=freeze(initialState(data,'?territory=city&metric=water&period=2024'));
  internalComparison(data,'river','water','2024');
  assert.equal(state.selected,'city');
  const province=selectHierarchyOption(data,state,'north','area:river');
  assert.equal(province.selected,'river');assert.equal(province.metric,'water');assert.equal(province.period,'2024');
  assert.equal(observationState(data,province.selected,province.metric,province.period).value,null);
  const region=selectHierarchyOption(data,state,'TST','area:north');
  assert.equal(region.selected,'north');assert.equal(observationState(data,'north',region.metric,region.period).value,null);
  assert.equal(new URLSearchParams(routeQuery(data,region)).get('territory'),'north');
  assert.deepEqual(internalComparison(data,region.selected,region.metric,region.period).rows.map(row=>row.area.id),['river','lake']);
  assert.equal(selectTerritory(data,state,'TST').selected,'TST');
});
test('cities and base municipalities stop comparison even when lower wards exist',()=>{
  const data=analysisFixture();
  for(const id of ['city','municipality']) {
    const result=internalComparison(data,id,'people','2024');assert.equal(result.set.terminal,true);assert.equal(result.rows.length,0);assert.match(result.reason,/stops/);
  }
  for(const type of ['Municipio','commune','COMUNA','municipal-district'])assert.equal(isTerminalTerritory(data,{id:'sample',type,level:'custom'}),true);
  data.analysis.terminal_territory_ids.push('north');assert.equal(comparisonSet(data,'north').members.length,0);
});
test('an explicit country-adapter comparison can document a valid level below a municipality',()=>{
  const data=analysisFixture();
  data.analysis.comparisons.push({parent_id:'city',member_ids:['city-ward'],label:'Documented wards',membership_note:'Synthetic explicit lower membership.',source_ids:['membership']});
  assert.equal(isTerminalTerritory(data,'city'),false);
  assert.deepEqual(comparisonSet(data,'city').members.map(area=>area.id),['city-ward']);
  data.analysis.terminal_territory_ids.push('city');
  assert.equal(isTerminalTerritory(data,'city'),true);
  assert.equal(comparisonSet(data,'city').members.length,0);
});
test('meaning metadata preserves values but excludes declared differences from comparison',()=>{
  for(const [field,value] of [['definition_id','another-concept'],['definition','Different definition'],['unit','thousands'],['population','Adults only'],['measurement_method','modeled']]) {
    const data=analysisFixture(),observation=data.observations.find(row=>row.territory_id==='municipality' && row.indicator_id==='people');
    observation[field]=value;
    assert.deepEqual(validateDataset(data).errors,[],`Declared ${field} difference remains evidence`);
    const result=internalComparison(data,'river','people','2024'),row=result.rows.find(item=>item.area.id==='municipality');
    assert.equal(row.value,100);assert.equal(row.status,'observed');assert.equal(row.comparable,false);assert.match(row.reason,/differs/);
    assert.equal(row[field==='measurement_method'?'method':field],value);
    assert.equal(colorForComparison(result,row),NO_COMPARISON_COLOR);
    assert.equal(result.scale.breaks.at(-1),21.6); // 100 is absent from the 0..27 scale.
  }
});
test('shared indicator meaning accepts different sources and rejects ungrounded method metadata',()=>{
  const data=analysisFixture(),indicator=data.indicators[0];
  const countries=internalComparison(data,'WLD','people','2024');
  assert.deepEqual(countries.rows.map(row=>row.source.id),['national-tst','national-oth']);
  assert.ok(countries.rows.every(row=>row.comparable));
  assert.equal(observationMeaning(indicator,{method:'source_reported'}).comparable,true);
  assert.equal(observationMeaning({...indicator,population:undefined},{population:'Adult residents'}).comparable,false);
  assert.equal(observationMeaning(indicator,{method:'modeled'}).method,'modeled');
  const city=data.observations.find(row=>row.territory_id==='city' && row.period==='2024' && row.indicator_id==='people');
  city.source_id='membership';assert.equal(internalComparison(data,'river','people','2024').rows.find(row=>row.area.id==='city').comparable,true);
});
test('mixed undeclared cohorts retain readable values and refuse numeric color classes',()=>{
  const data=analysisFixture();data.analysis.comparisons=data.analysis.comparisons.filter(item=>item.parent_id!=='river');
  const mixed=internalComparison(data,'river','people','2024');
  assert.ok(mixed.rows.every(row=>!row.comparable));assert.equal(mixed.rows.find(row=>row.area.id==='municipality').value,100);assert.match(mixed.reason,/different type/);
  data.territories.find(area=>area.id==='south').boundary_version='other-local-edition';
  assert.match(internalComparison(data,'TST','people','2024').reason,/boundary_version/);
});
test('fixed scales are comparable between selections and dynamic scale handles ties, negatives and extreme values',()=>{
  const data=analysisFixture(),config=data.analysis.comparisons.find(item=>item.parent_id==='river');
  config.color_scale={mode:'fixed',breaks:[0,10,50,100],label:'Fictional fixed thresholds'};
  assert.deepEqual(validateDataset(data).errors,[]);
  const fixed=internalComparison(data,'river','people','2024');
  assert.deepEqual(fixed.scale.breaks,[0,10,50,100]);assert.equal(fixed.scale.legend.length,5);assert.equal(fixed.scale.label,'Fictional fixed thresholds');
  assert.equal(colorForComparison(fixed,fixed.rows.find(row=>row.area.id==='city')),fixed.scale.colors[0]);
  assert.equal(colorForComparison(fixed,fixed.rows.find(row=>row.area.id==='municipality')),fixed.scale.colors[3]);
  const countries=data.observations.filter(row=>row.indicator_id==='people' && ['TST','OTH'].includes(row.territory_id));
  countries.forEach(row=>row.value=-5);
  const tied=internalComparison(data,'WLD','people','2024');assert.equal(tied.scale.constant_value,-5);assert.equal(tied.scale.legend.length,1);
  countries[0].value=-Number.MAX_VALUE;countries[1].value=Number.MAX_VALUE;
  assert.ok(internalComparison(data,'WLD','people','2024').scale.breaks.every(Number.isFinite));
});
test('boundary IDs, codes and editions join exactly; unresolved geometry never joins by name',()=>{
  for(const [key,value] of [['code','wrong-code'],['official_code','wrong-code'],['boundary_version','other-edition'],['code_system','other-system']]) {
    const data=analysisFixture(),feature=data.boundaries.features.find(item=>item.properties.territory_id==='city');feature.properties[key]=value;
    assert.match(errors(data),/Boundary city.*does not match/);
    const result=internalComparison(data,'river','people','2024'),row=result.rows.find(item=>item.area.id==='city');
    assert.equal(row.boundary,null);assert.equal(row.value,0);assert.match(row.boundary_reason,/does not match/);
    assert.ok(result.rows.find(item=>item.area.id==='municipality').boundary);
  }
  const duplicate=analysisFixture();duplicate.boundaries.features.push(structuredClone(duplicate.boundaries.features.find(item=>item.properties.territory_id==='city')));
  assert.match(errors(duplicate),/Duplicate boundary/);assert.equal(internalComparison(duplicate,'river','people','2024').rows.find(row=>row.area.id==='city').boundary,null);
});
test('an observation using a historical boundary stays readable and excluded',()=>{
  const data=analysisFixture();data.observations.find(row=>row.territory_id==='municipality' && row.indicator_id==='people').boundary_version='historical-geometry';
  assert.deepEqual(validateDataset(data).errors,[]);
  const row=internalComparison(data,'river','people','2024').rows.find(row=>row.area.id==='municipality');
  assert.equal(row.value,100);assert.equal(row.comparable,false);assert.match(row.reason,/Observation boundary edition/);
});
test('shared observation context preserves actual values and does not invent an unrecorded boundary mismatch',()=>{
  const data=analysisFixture(),area=data.territories.find(row=>row.id==='city'),indicator=data.indicators[0];
  const observation=data.observations.find(row=>row.territory_id==='city' && row.period==='2024' && row.indicator_id==='people');
  const original=freeze(structuredClone(observation));
  assert.equal(observationContext(data,area,indicator,original).comparable,true);
  assert.equal(observationContext(data,{...area,boundary_version:null},indicator,original).comparable,true);
  assert.equal(observationContext(data,area,indicator,{...original,boundary_version:area.boundary_version}).comparable,true);
  const context=observationContext(data,area,indicator,{...original,boundary_version:'historical-1900'});
  assert.equal(context.comparable,false);assert.equal(context.meaning_comparable,true);assert.match(context.reason,/Observation boundary edition/);
  assert.equal(Object.hasOwn(context,'value'),false);assert.equal(Object.hasOwn(context,'status'),false);
  assert.equal(original.value,0);assert.equal(original.status,'observed');
  assert.equal(observationContext(data,area,indicator,{...original,boundary_version:null}).comparable,false);
  assert.equal(observationContext(data,{...area,boundary_version:null},indicator,{...original,boundary_version:null}).comparable,true);
});
test('observation context and internal comparison share source and scope exclusions',()=>{
  const data=analysisFixture(),area=data.territories.find(row=>row.id==='city'),indicator=data.indicators[0];
  const observation=data.observations.find(row=>row.territory_id==='city' && row.period==='2024' && row.indicator_id==='people'),source=data.sources.find(row=>row.id==='local');
  for(const status of ['failed','error','unavailable','not_collected']) {
    source.status=status;
    const context=observationContext(data,area,indicator,observation),internal=internalComparison(data,'river','people','2024').rows.find(row=>row.area.id==='city');
    assert.equal(context.comparable,false);assert.equal(context.meaning_comparable,true);assert.match(context.reason,/no acquired usable data/);assert.equal(internal.reason,context.reason);assert.equal(internal.value,0);assert.equal(internal.status,'observed');
  }
  source.status='partial';assert.equal(observationContext(data,area,indicator,observation).comparable,true);
  source.geographic_level='national';source.country_id='TST';assert.equal(observationContext(data,area,indicator,observation).comparable,false);
  delete source.geographic_level;delete source.country_id;observation.source_id='unknown-source';assert.match(observationContext(data,area,indicator,observation).reason,/source is unavailable/);
});
test('national source scope requires country identity and never supplies a local area',()=>{
  const data=analysisFixture(),national=data.observations.find(row=>row.territory_id==='TST' && row.indicator_id==='people');
  national.territory_id='north';assert.match(errors(data),/National source/);
  national.territory_id='OTH';national.period='2025';assert.match(errors(data),/different-country/);
  const noIdentity=analysisFixture();delete noIdentity.territories.find(area=>area.id==='TST').country_id;assert.match(errors(noIdentity),/explicit country_id/);
  const sourceNoCountry=analysisFixture();delete sourceNoCountry.sources.find(source=>source.id==='national-tst').country_id;assert.match(errors(sourceNoCountry),/National source/);
});
test('world country series permits the world total or country rows, never synthetic region sums',()=>{
  const data=analysisFixture(),source=data.sources.find(row=>row.id==='national-tst');source.geographic_level='world_country_series';delete source.country_id;
  data.observations.push({territory_id:'WLD',indicator_id:'people',period:'2024',value:12345,status:'observed',source_id:source.id});
  assert.deepEqual(validateDataset(data).errors,[]);
  data.observations.at(-1).territory_id='north';assert.match(errors(data),/World country series/);
  const row=internalComparison(data,'TST','people','2024').rows.find(row=>row.area.id==='north');assert.equal(row.value,12345);assert.equal(row.comparable,false);
});
test('membership validation rejects cross-branch, overlapping, duplicate and ungrounded sets',()=>{
  for(const mutate of [
    data=>data.analysis.comparisons[1].member_ids.push('OTH'),
    data=>data.analysis.comparisons[0].member_ids.push('north'),
    data=>data.analysis.comparisons.push(structuredClone(data.analysis.comparisons[0])),
    data=>data.analysis.comparisons[0].source_ids=['missing-source'],
    data=>data.analysis.comparisons[0].source_ids=[],
    data=>data.analysis.comparisons[0].member_ids=['TST','TST'],
    data=>data.analysis.comparisons[0].member_ids=['WLD'],
    data=>data.analysis.terminal_territory_ids=['unknown-area']
  ]){const data=analysisFixture();mutate(data);assert.ok(validateDataset(data).errors.length>0);}
});
test('country links require explicit matching identity and safe paths',()=>{
  for(const url of ['https://example.org/country/','./countries/TST/?metric=people']) {const data=analysisFixture();data.analysis.country_sites[0].url=url;assert.deepEqual(validateDataset(data).errors,[]);}
  for(const change of [{url:'../TST/'},{url:'/TST/'},{url:'//example.org/TST/'},{url:'./%2e%2e/TST/'},{url:'https://name:secret@example.org/'},{country_id:'OTH'},{territory_id:'north'},{indicator_map:{people:0}}]) {
    const data=analysisFixture();Object.assign(data.analysis.country_sites[0],change);assert.match(errors(data),/country_sites/);
  }
});
test('invalid nested shapes report validation errors without throwing',()=>{
  const broken=[null,[],0,'bad',true];
  for(const value of broken)for(const mutate of [
    data=>data.analysis=value,
    data=>data.analysis.comparisons=[value],
    data=>data.analysis.comparisons[0].color_scale=value,
    data=>data.analysis.comparisons[0].member_ids=value,
    data=>data.analysis.country_sites=[value]
  ]) {const data=analysisFixture();mutate(data);assert.doesNotThrow(()=>validateDataset(data));assert.ok(validateDataset(data).errors.length>0);}
  for(const value of [null,0,'bad',true]) {const data=analysisFixture();data.analysis.comparisons=value;assert.match(errors(data),/comparisons must be an array/);}
  for(const value of [null,[],0,true]) {const data=analysisFixture();data.observations[0].population=value;assert.match(errors(data),/population must be a nonempty string/);}
  for(const breaks of [[0,1,1,4],[0,1,2],[0,1,2,Infinity],['0',1,2,3]]) {const data=analysisFixture();data.analysis.comparisons[0].color_scale={mode:'fixed',breaks};assert.match(errors(data),/thresholds/);}
  assert.ok(validateAnalysis(null).errors.length);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {analysisFixture} from './analysis-fixture.mjs';
import {resolvedObservation,aggregationAuditRows} from '../scaffold/site/aggregation.mjs';
import {validateDataset} from '../lib/validate.mjs';

function enabled() {
  const data=analysisFixture();
  data.indicators.find(item=>item.id==='people').aggregation='sum';
  data.analysis.aggregation={policy:'exact_then_complete_cover',rules:[{indicator_id:'people',method:'sum',completeness:'full_cover',label:'Calculated population',note:'Synthetic complete-cover rule.'}]};
  data.analysis.comparisons.push({parent_id:'north',member_ids:['river','lake'],label:'Synthetic provinces',membership_note:'Complete fictional membership.',source_ids:['membership']});
  return data;
}

test('exact country or province values take priority over lower-area gaps',()=>{
  const data=enabled();
  const country=resolvedObservation(data,'TST','people','2024');
  assert.equal(country.value,1000);assert.equal(country.provenance,'source_reported');assert.deepEqual(country.components.map(item=>item.territory_id),['TST']);
  const province=resolvedObservation(data,'river','people','2024');
  assert.equal(province.value,400);assert.deepEqual(province.components.map(item=>item.territory_id),['river']);
  assert.ok(data.observations.some(row=>row.territory_id==='missing-city'&&row.status==='missing')===false,'Missing or uncollected municipalities need no fabricated row');
});

test('an exact value calculated from source counts retains calculated provenance',()=>{
  const data=enabled();
  const row=data.observations.find(item=>item.territory_id==='river'&&item.indicator_id==='people'&&item.period==='2024');
  row.provenance='calculated';
  row.calculation={formula:'numerator / denominator * 100',numerator:2,denominator:5};
  const result=resolvedObservation(data,'river','people','2024');
  assert.equal(result.value,400);
  assert.equal(result.status,'calculated');
  assert.equal(result.provenance,'calculated');
});

test('complete non-overlapping cover calculates a sum and exports its audit components',()=>{
  const data=enabled();
  const world=resolvedObservation(data,'WLD','people','2024');
  assert.equal(world.value,3000);assert.equal(world.status,'calculated');assert.deepEqual(world.components.map(item=>item.territory_id),['TST','OTH']);
  assert.deepEqual(aggregationAuditRows(data,'WLD','people','2024').map(row=>row.area.id),['TST','OTH']);
});

test('incomplete cover never becomes a total and keeps only a labelled covered subtotal',()=>{
  const data=enabled();
  const incomplete=resolvedObservation(data,'north','people','2024');
  assert.equal(incomplete.value,null);assert.equal(incomplete.status,'incomplete');assert.equal(incomplete.covered_value,400);assert.deepEqual(incomplete.missing_ids,['lake']);
  Object.assign(data.observations.find(row=>row.territory_id==='lake'&&row.indicator_id==='people'&&row.period==='2024'),{value:600,status:'observed'});
  const complete=resolvedObservation(data,'north','people','2024');
  assert.equal(complete.value,1000);assert.deepEqual(complete.components.map(item=>item.territory_id),['river','lake']);
});

test('complete same-year international population is independent of an incomplete census series',()=>{
  const data=enabled();
  data.indicators.find(item=>item.id==='people').series_family='census';
  data.indicators.push({id:'international-people',name:'Fictional international population',theme:'Population',unit:'people',definition:'Synthetic same-year population.',definition_id:'synthetic-international-population',population:'Synthetic residents',measurement_method:'fictional international estimate',aggregation:'sum',series_family:'international_reference',source_id:'international'});
  data.sources.push({id:'international',name:'Fictional international source',url:'https://example.org/international',publisher:'Synthetic fixture',retrieved_at:'2026-09-13T00:00:00Z',status:'ready',license:'Fictional data'});
  data.observations=data.observations.filter(row=>!(row.territory_id==='OTH'&&row.indicator_id==='people'));
  data.observations.push({territory_id:'TST',indicator_id:'international-people',period:'2024',value:1100,status:'observed',source_id:'international'},{territory_id:'OTH',indicator_id:'international-people',period:'2024',value:2100,status:'observed',source_id:'international'});
  data.analysis.aggregation.rules.push({indicator_id:'international-people',method:'sum',completeness:'full_cover',period_policy:'same_period',label:'Synthetic international total',note:'Only same-year fictional country values.'});
  const census=resolvedObservation(data,'WLD','people','2024');
  const international=resolvedObservation(data,'WLD','international-people','2024');
  assert.equal(census.value,null);assert.equal(census.covered_value,1000);assert.deepEqual(census.missing_ids,['OTH']);
  assert.equal(international.value,3200);assert.equal(international.status,'calculated');
  assert.deepEqual(international.components.map(item=>item.territory_id),['TST','OTH']);
  assert.deepEqual(validateDataset(data).errors,[]);
});

test('a source-backed aggregation cover can use direct regions while comparison retains country rows',()=>{
  const data=enabled();
  data.analysis.comparisons.push({parent_id:'other-continent',member_ids:['OTH'],label:'Other fictional region',membership_note:'Source-backed synthetic membership.',source_ids:['membership']});
  data.analysis.aggregation.coverage_sets=[{parent_id:'WLD',indicator_id:'people',member_ids:['americas','other-continent'],source_ids:['membership'],membership_note:'The two direct fictional regions exhaust the fictional world.'}];
  const comparison=data.analysis.comparisons.find(item=>item.parent_id==='WLD');
  assert.deepEqual(comparison.member_ids,['TST','OTH']);
  const result=resolvedObservation(data,'WLD','people','2024');
  assert.equal(result.value,3000);
  assert.deepEqual(result.components.map(item=>item.territory_id),['TST','OTH']);
  assert.deepEqual(validateDataset(data).errors,[]);
  data.analysis.aggregation.coverage_sets[0].member_ids=['americas'];
  assert.equal(resolvedObservation(data,'WLD','people','2024').value,null);
  assert.match(validateDataset(data).errors.join(' '),/every direct child/);
});

test('overlapping selections and non-additive indicators are not calculated',()=>{
  const data=enabled();
  assert.equal(resolvedObservation(data,['TST','river'],'people','2024').status,'incomparable');
  const rate=resolvedObservation(data,'WLD','water','2024');
  assert.equal(rate.value,null);assert.match(rate.note,/averages are not calculated/);
  assert.deepEqual(validateDataset(data).errors,[]);
});

test('latest census observations can use different declared years only under an explicit mixed-period rule',()=>{
  const data=enabled();
  const rule=data.analysis.aggregation.rules[0];
  rule.period_policy='latest_available_by_component';
  data.indicators.find(item=>item.id==='people').series_family='census';
  data.observations.find(row=>row.territory_id==='TST'&&row.indicator_id==='people'&&row.period==='2024').period='2018';
  data.observations.find(row=>row.territory_id==='OTH'&&row.indicator_id==='people'&&row.period==='2024').period='2022';
  const mixed=resolvedObservation(data,'WLD','people','latest-available');
  assert.equal(mixed.value,3000);
  assert.equal(mixed.period_policy,'latest_available_by_component');
  assert.deepEqual(mixed.components.map(item=>`${item.territory_id}@${item.period}`),['TST@2018','OTH@2022']);
  assert.match(mixed.note,/not a same-year total/);
  assert.deepEqual(aggregationAuditRows(data,'WLD','people','latest-available').map(row=>row.period),['2018','2022']);
  delete rule.period_policy;
  const refused=resolvedObservation(data,'WLD','people','latest-available');
  assert.equal(refused.value,null);
  assert.match(refused.note,/not approved/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCensusHistory,mergeCensusHistory} from '../lib/census-history-adapter.mjs';
import {censusAge,censusIntervals,censusRecencyClass,censusRecencyColor} from '../scaffold/site/census-history.mjs';

const catalog=JSON.parse(await readFile(new URL('../data/census/central-america-census-history-v0.9.json',import.meta.url),'utf8'));

function dataset(){
  const ids=catalog.countries.map(country=>country.country_id);
  return {country:{national_territory_id:catalog.scope_id},analysis:{pilot:{country_ids:ids}},observations:catalog.countries.map(country=>({territory_id:country.country_id,indicator_id:'CENSUS_POP_TOTAL',period:String(country.adopted_data_year),value:1,status:'observed'})),collection:{adapters:[],notes:[]}};
}

test('official census history validates and is attached with world reference shapes',()=>{
  assert.equal(validateCensusHistory(catalog),catalog);
  const boundaries={type:'FeatureCollection',features:[{type:'Feature',properties:{territory_id:'BLZ'},geometry:{type:'Polygon',coordinates:[[[0,0],[1,0],[1,1],[0,0]]]}}]};
  const result=mergeCensusHistory(dataset(),catalog,boundaries);
  assert.equal(result.analysis.census_history.countries.length,7);
  assert.equal(result.analysis.census_history.reference_boundaries.features.length,1);
  assert.ok(result.collection.adapters.includes('official-census-round-history-v1'));
});

test('adopted census year must match an active country observation',()=>{
  const broken=dataset();broken.observations=broken.observations.filter(row=>row.territory_id!=='NIC');
  assert.throws(()=>mergeCensusHistory(broken,catalog),/NIC 2005/);
});

test('recency scale makes ten-year-old data pale red and preserves round intervals',()=>{
  assert.equal(censusAge(2016,2026),10);
  assert.equal(censusRecencyClass(2016,2026),'overdue');
  assert.equal(censusRecencyColor(2016,2026),'#e8aaa5');
  assert.equal(censusRecencyClass(2024,2026),'current');
  assert.deepEqual(censusIntervals([{year:2024},{year:2007},{year:1992}]),[17,15]);
});

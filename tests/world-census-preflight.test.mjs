import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {attachWorldCensusListings,importKitWorldSourcePreflight,validateWorldCensusListings,validateWorldCensusListingsAgainstDataset,KIT_WORLD_PREFLIGHT_COMMIT,KIT_WORLD_PREFLIGHT_SHA256} from '../lib/world-census-preflight.mjs';
import {censusSourcePreflightCsv} from '../scaffold/site/model.mjs';

const registry=JSON.parse(await readFile(new URL('../data/census/world-census-listings-v1.8.1.json',import.meta.url),'utf8'));

function dataset({censusPeriod='2008'}={}){
  const ids=['DZA','KNA','LCA','SPM','VCT','SXM','NLD'];
  return {
    schema_version:'0.2',generated_at:'2026-09-23T00:00:00Z',country:{id:'WLD',name:'World',national_territory_id:'WLD'},
    territories:[{id:'WLD',name:'World',level:'national',type:'exploration_scope',parent_id:null},...ids.map(id=>({id,name:id,level:'country',type:'country',parent_id:'WLD',country_id:id}))],
    analysis:{kind:'world',terminal_territory_ids:ids,comparisons:[],country_sites:[]},
    indicators:[{id:'DZA_CENSUS_POP',name:'Population',theme:'Population',unit:'people',definition:'Census population',aggregation:'official_only',series_family:'census',source_id:'dza-census'},{id:'WDI_POP',name:'WDI population',theme:'Population',unit:'people',definition:'International comparison series',aggregation:'official_only',series_family:'international_reference',source_id:'wdi'}],
    observations:[{territory_id:'DZA',indicator_id:'DZA_CENSUS_POP',period:censusPeriod,value:1,status:'observed',source_id:'dza-census'},{territory_id:'DZA',indicator_id:'WDI_POP',period:'2022',value:2,status:'observed',source_id:'wdi'}],
    sources:[],documents:[],gaps:[],boundaries:{type:'FeatureCollection',features:[]},collection:{status:'partial',adapters:[],notes:[]}
  };
}

test('bundled Kit v1.8.1 registry preserves separate Algeria listing and linked listing',()=>{
  assert.deepEqual(validateWorldCensusListings(registry),[]);
  assert.equal(registry.source.commit,KIT_WORLD_PREFLIGHT_COMMIT);
  assert.equal(registry.source.sha256,KIT_WORLD_PREFLIGHT_SHA256);
  const dza=registry.records.find(row=>row.country_id==='DZA');
  assert.deepEqual({round:dza.latest_un_census_listing.round,date:dza.latest_un_census_listing.date_text,url:dza.latest_un_census_listing.primary_url},{round:2020,date:'25 September 2022',url:null});
  assert.deepEqual({round:dza.latest_un_census_linked_listing.round,date:dza.latest_un_census_linked_listing.date_text,url:dza.latest_un_census_linked_listing.primary_url},{round:2010,date:'16-30 April 2008',url:'http://rgph2008.ons.dz/'});
});

test('current UNSD identities are imported by ISO3 without local name matching',()=>{
  const attached=attachWorldCensusListings(dataset(),registry),records=new Map(attached.analysis.census_source_preflight.records.map(row=>[row.country_id,row]));
  assert.deepEqual([...records.keys()].sort(),['DZA','KNA','LCA','NLD','SPM','SXM','VCT']);
  assert.equal(records.get('KNA').latest_un_census_listing.country_label,'St. Kitts and Nevis');
  assert.equal(records.get('LCA').latest_un_census_listing.country_label,'St. Lucia');
  assert.equal(records.get('SPM').latest_un_census_listing.country_label,'St. Pierre and Miquelon');
  assert.equal(records.get('VCT').latest_un_census_listing.country_label,'St. Vincent and the Grenadines');
  assert.equal(records.get('SXM').latest_un_census_listing.country_label,'Sint Maarten');
  assert.match(records.get('NLD').latest_un_census_listing.country_label,/Netherlands/);
  assert.deepEqual(validateWorldCensusListingsAgainstDataset(attached),[]);
});

test('Algeria rejects 2022 census observations but allows a separate 2022 international series',()=>{
  const invalid=attachWorldCensusListings(dataset({censusPeriod:'2022'}),registry);
  assert.match(validateWorldCensusListingsAgainstDataset(invalid).join('\n'),/DZA census observation.+exceeds the adopted 2008 source year/);
  const valid=attachWorldCensusListings(dataset(),registry);
  assert.deepEqual(validateWorldCensusListingsAgainstDataset(valid),[]);
});

test('Census listing CSV exports round, date, link and evidence states separately',()=>{
  const csv=censusSourcePreflightCsv(attachWorldCensusListings(dataset(),registry));
  const dza=csv.split('\r\n').find(line=>line.includes('"DZA"'));
  assert.match(dza,/"2020","2015-2024","25 September 2022","no_unsd_link_listed","","2010","2005-2014","16-30 April 2008","http:\/\/rgph2008\.ons\.dz\/"/);
  assert.match(dza,/"not_acquired_by_preflight","not_verified_by_preflight","not_adopted_by_preflight"/);
});

test('importer rejects bytes that do not match the pinned Kit registry',async()=>{
  await assert.rejects(()=>importKitWorldSourcePreflight(Buffer.from('{}')),/hash mismatch/);
});

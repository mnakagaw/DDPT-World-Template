import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildRegionalPilot,buildCensusPilotPreflight,CENTRAL_AMERICA_CONFIG} from '../lib/regional-pilot.mjs';
import {loadSourceCatalog} from '../lib/source-catalog.mjs';
import {resolvedObservation} from '../scaffold/site/aggregation.mjs';

function worldFixture() {
  const ids=CENTRAL_AMERICA_CONFIG.member_ids;
  const source=id=>({id,name:id,publisher:'Synthetic test',url:`https://example.org/${id}`,status:'ready',retrieved_at:'2026-09-15T00:00:00Z'});
  const indicators=[{id:'SP.POP.TOTL',name:'Population',theme:'Population',unit:'people',definition:'Synthetic population.',definition_id:'population',population:'All residents',measurement_method:'source_reported',aggregation:'official_only',source_id:'population-source'},{id:'RATE',name:'Rate',theme:'Test',unit:'%',definition:'Synthetic rate.',definition_id:'rate',population:'Synthetic denominator',measurement_method:'source_reported',aggregation:'official_only',source_id:'rate-source'}];
  const observations=ids.flatMap((id,index)=>[
    {territory_id:id,indicator_id:'SP.POP.TOTL',period:'2024',value:index+1,status:'observed',source_id:'population-source'},
    {territory_id:id,indicator_id:'SP.POP.TOTL',period:'2025',value:id==='BLZ'?null:index+2,status:id==='BLZ'?'missing':'observed',source_id:'population-source'},
    {territory_id:id,indicator_id:'RATE',period:'2024',value:50+index,status:'observed',source_id:'rate-source'}
  ]);
  return {schema_version:'0.2',generated_at:'2026-09-15T00:00:00Z',country:{id:'WLD',name:'Synthetic world',national_territory_id:'WLD'},territories:ids.map(id=>({id,country_id:id,name:id,level:'country',type:'country',parent_id:'M49:013',official_code:id,code_system:'Synthetic',boundary_version:null})),indicators,observations,sources:[source('un-m49'),{...source('population-source'),geographic_level:'world_country_series'},{...source('rate-source'),geographic_level:'world_country_series'},source('natural-earth')],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['synthetic'],notes:[]}};
}

test('Central America pilot has the conventional seven states and excludes Mexico',()=>{
  const data=buildRegionalPilot(worldFixture());
  assert.deepEqual(data.analysis.pilot.country_ids,['BLZ','GTM','SLV','HND','NIC','CRI','PAN']);
  assert.equal(data.territories.some(area=>area.id==='MEX'),false);
  assert.equal(data.analysis.default_period_by_indicator['SP.POP.TOTL'],'2024');
  const total=resolvedObservation(data,data.country.national_territory_id,'SP.POP.TOTL','2024');
  assert.equal(total.value,28);assert.equal(total.status,'calculated');assert.equal(total.components.length,7);
  const incomplete=resolvedObservation(data,data.country.national_territory_id,'SP.POP.TOTL','2025');
  assert.equal(incomplete.value,null);assert.equal(incomplete.status,'incomplete');assert.deepEqual(incomplete.missing_ids,['BLZ']);
  assert.equal(resolvedObservation(data,data.country.national_territory_id,'RATE','2024').value,null,'Rates are not simply averaged');
  assert.equal(data.analysis.pilot.primary_series_family,'census');
  assert.deepEqual(data.analysis.pilot.available_series_families,['international_reference']);
  assert.ok(data.indicators.every(indicator=>indicator.series_family==='international_reference'&&indicator.display_role==='context'));
});

test('census preflight covers all seven countries but does not promote source locations to acquired data',async()=>{
  const plan=buildCensusPilotPreflight(await loadSourceCatalog());
  assert.deepEqual(plan.countries.map(country=>country.iso3),CENTRAL_AMERICA_CONFIG.member_ids);
  assert.equal(plan.summary.countries_with_census_source_locations,7);
  assert.equal(plan.summary.data_acquired,0);
  assert.equal(plan.countries.find(country=>country.iso3==='BLZ').usable_detailed_year,2022);
  assert.equal(plan.countries.find(country=>country.iso3==='NIC').usable_detailed_year,2005);
  assert.ok(plan.countries.every(country=>country.acquisition_status==='not_acquired_by_this_build'));
});

test('MariaDB schema preserves identity, missingness, aggregation lineage and indexed queries',async()=>{
  const sql=await readFile(new URL('../database/mariadb/001_schema.sql',import.meta.url),'utf8');
  for(const table of ['dataset_version','source_record','geography','geography_membership','indicator','observation','aggregation_rule','aggregate_result','aggregate_component','boundary_asset'])assert.match(sql,new RegExp(`CREATE TABLE IF NOT EXISTS ${table}`));
  assert.match(sql,/uq_observation_identity/);assert.match(sql,/chk_observation_value/);assert.match(sql,/inputs_sha256/);assert.match(sql,/full_cover/);assert.doesNotMatch(sql,/INSERT\s+INTO/i,'The schema does not mix synthetic or public facts into production tables');
});

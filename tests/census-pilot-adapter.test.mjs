import test from 'node:test';
import assert from 'node:assert/strict';
import {buildRegionalPilot,CENTRAL_AMERICA_CONFIG} from '../lib/regional-pilot.mjs';
import {mergeCensusPilot,validateNormalizedCensus} from '../lib/census-pilot-adapter.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {resolvedObservation} from '../scaffold/site/aggregation.mjs';
import {displayValue,comparisonRows} from '../scaffold/site/model.mjs';
import {internalComparison} from '../scaffold/site/analysis.mjs';

const source=id=>({id,name:id,publisher:'Test',url:`https://example.test/${id}`,status:'ready',retrieved_at:'2026-09-15T00:00:00Z',license:'test'});
function world(){
  const ids=CENTRAL_AMERICA_CONFIG.member_ids;
  return {schema_version:'0.2',generated_at:'2026-09-15T00:00:00Z',country:{id:'WLD',name:'World',national_territory_id:'WLD'},territories:ids.map(id=>({id,country_id:id,name:id,level:'country',type:'country',parent_id:'M49:013',official_code:id,code_system:'test',boundary_version:null})),indicators:[{id:'SP.POP.TOTL',name:'WDI population',theme:'Population',unit:'people',definition:'test',definition_id:'wdi',population:'test',measurement_method:'test',aggregation:'official_only',source_id:'wdi'}],observations:ids.map((id,index)=>({territory_id:id,indicator_id:'SP.POP.TOTL',period:'2025',value:index+1,status:'observed',source_id:'wdi'})),sources:[source('un-m49'),source('natural-earth'),{...source('wdi'),geographic_level:'world_country_series'}],boundaries:{type:'FeatureCollection',features:[]},documents:[],gaps:[],collection:{status:'partial',adapters:['test'],notes:[]}};
}
function normalized(){
  const official=id=>({...source(id),sha256:'a'.repeat(64),geographic_level:'subnational'});
  const indicator={id:'CENSUS_POP_TOTAL',name:'Official census population',theme:'Population',unit:'people',definition:'Country census population',definition_id:'census-pop',population:'Country census population',measurement_method:'country-specific official census product',aggregation:'sum',series_family:'census',display_role:'primary',period_policy:'latest_available_by_component',display_decimals:0,source_id:'census-contract'};
  const country=(country_id,period,value,source_id)=>({country_id,period,territories:[],observations:[{territory_id:country_id,indicator_id:indicator.id,period,value,status:'observed',source_id}],comparisons:[],terminal_territory_ids:[],sources:[official(source_id)],audit:{}});
  return {schema_version:'1.0',scope_id:CENTRAL_AMERICA_CONFIG.id,generated_at:'2026-09-15T00:00:00Z',status:'partial_country_coverage',indicator,series_source:{...source('census-contract'),status:'partial'},countries:[country('BLZ','2022',397483.456,'blz-source'),country('GTM','2018',14901286,'gtm-source')],summary:{pilot_country_count:7,countries_acquired:['BLZ','GTM'],countries_pending:['SLV','HND','NIC','CRI','PAN'],territories_added:0,observations_added:2,regional_total_status:'not_available_incomplete_country_coverage'}};
}
function completeNormalized(){
  const data=normalized();
  const add=(country_id,period,value,source_id)=>({country_id,period,territories:[],observations:[{territory_id:country_id,indicator_id:data.indicator.id,period,value,status:'observed',source_id}],comparisons:[],terminal_territory_ids:[],sources:[{...source(source_id),sha256:'b'.repeat(64),geographic_level:'subnational'}],audit:{national_population:value}});
  data.countries.push(add('SLV','2024',6029976,'slv-source'),add('HND','2013',8303771,'hnd-source'),add('NIC','2005',5142098,'nic-source'),add('CRI','2022',5044197,'cri-source'),add('PAN','2023',4064780,'pan-source'));
  data.status='available_complete_country_coverage';data.series_source.status='ready';
  const periods=Object.fromEntries(data.countries.map(item=>[item.country_id,item.period])),values=Object.fromEntries(data.countries.map(item=>[item.country_id,item.observations[0].value]));
  Object.assign(data.summary,{countries_acquired:data.countries.map(item=>item.country_id),countries_pending:[],observations_added:7,regional_total_status:'available_complete_country_coverage_mixed_reference_years',regional_total:Object.values(values).reduce((sum,value)=>sum+value,0),regional_total_component_periods:periods,regional_total_country_values:values});
  return data;
}

test('partial official census layer becomes primary without claiming the regional total',()=>{
  const result=mergeCensusPilot(buildRegionalPilot(world()),normalized());
  assert.deepEqual(validateDataset(result).errors,[]);
  assert.equal(result.indicators[0].id,'CENSUS_POP_TOTAL');
  assert.equal(result.analysis.pilot.census_adapter_status,'partial');
  const regional=resolvedObservation(result,result.country.national_territory_id,'CENSUS_POP_TOTAL','latest-available');
  assert.equal(regional.value,null);assert.equal(regional.status,'incomplete');assert.equal(regional.components.length,2);assert.deepEqual(regional.component_periods.sort(),['2018','2022']);assert.deepEqual(regional.missing_ids,['SLV','HND','NIC','CRI','PAN']);
  assert.equal(resolvedObservation(result,'BLZ','CENSUS_POP_TOTAL','latest-available').value,397483.456);
  const rows=comparisonRows(result,{selected:result.country.national_territory_id,metric:'CENSUS_POP_TOTAL',period:'latest-available',level:'country'});
  assert.equal(rows.find(row=>row.area.id==='BLZ').period,'2022');assert.equal(rows.find(row=>row.area.id==='GTM').period,'2018');
  const internal=internalComparison(result,result.country.national_territory_id,'CENSUS_POP_TOTAL','latest-available');
  assert.equal(internal.rows.find(row=>row.area.id==='BLZ').period,'2022');assert.equal(internal.rows.find(row=>row.area.id==='GTM').value,14901286);
  assert.equal(displayValue(397483.456,'en',0),'397,483');
});

test('partial normalized layer cannot claim a regional total',()=>{
  const data=normalized();data.summary.regional_total_status='available';
  assert.throws(()=>validateNormalizedCensus(data),/cannot claim a regional total/);
});

test('complete mixed-year census cover yields a regional sum from exact country observations',()=>{
  const normalizedData=completeNormalized(),result=mergeCensusPilot(buildRegionalPilot(world()),normalizedData);
  assert.deepEqual(validateDataset(result).errors,[]);
  assert.equal(result.analysis.pilot.census_adapter_status,'complete');
  const regional=resolvedObservation(result,result.country.national_territory_id,'CENSUS_POP_TOTAL','latest-available');
  assert.equal(regional.value,43883591.456);assert.equal(regional.status,'calculated');assert.equal(regional.components.length,7);assert.equal(regional.missing_ids.length,0);
  assert.deepEqual(regional.component_periods.sort(),['2005','2013','2018','2022','2023','2024']);
  assert.equal(result.gaps.find(gap=>gap.category==='regional_aggregation').status,'ready');
});

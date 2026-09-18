import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCountryCompletionMatrix,validateCountryCompletionMatrix,COMPLETION_DOMAINS,CENSUS_THEMES} from '../lib/country-completion-matrix.mjs';

const verified={identified:true,accessed:true,acquired:true,inspected:true,geography_matched:true,adopted:true,completion_verified:true,urls:['https://example.org'],note:'Verified.'};
test('identified-only records remain incomplete and cannot satisfy the all-country gate',()=>{
  const preflight={scope_id:'M49:019',countries:[{country_area_id:'AAA',name:'A',official_statistics_office:{identified:true,status:'identified'}}]};
  const matrix=buildCountryCompletionMatrix(preflight,{generatedAt:'2026-09-18T00:00:00Z'}),check=validateCountryCompletionMatrix(matrix,{expectedCountryIds:['AAA']});
  assert.equal(check.ok,true);assert.equal(matrix.complete_country_area_count,0);assert.equal(matrix.countries[0].overall_status,'incomplete');assert.ok(matrix.countries[0].incomplete_domains.includes('official_statistics_office'));assert.ok(matrix.countries[0].incomplete_themes.includes('population_total'));
});

test('all domains and theme dispositions need explicit verified evidence before a country is complete',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,theme,disposition:index?'not_adopted':'integrated',reason:index?'Not published at compatible geography.':'Integrated.',coverage_complete:true}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-18T00:00:00Z'}),check=validateCountryCompletionMatrix(matrix,{expectedCountryIds:['AAA']});
  assert.equal(check.ok,true);assert.equal(matrix.complete_country_area_count,1);assert.equal(matrix.countries[0].overall_status,'complete');
});

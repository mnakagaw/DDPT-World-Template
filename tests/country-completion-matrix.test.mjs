import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCountryCompletionMatrix,validateCountryCompletionMatrix,COMPLETION_DOMAINS,CENSUS_THEMES} from '../lib/country-completion-matrix.mjs';

const verified={identified:true,accessed:true,acquired:true,inspected:true,geography_matched:true,adopted:true,completion_verified:true,urls:['https://example.org'],note:'Verified.',evidence:[{object_path:'raw/source.json',object_sha256:'a'.repeat(64),locator:'Exact table/API locator.',geography_match:'Exact source-code join.'}]};
const localDataset=(indicatorIds)=>({
  territories:[{id:'AAA',type:'country'},{id:'AAA:1',type:'adm1',country_id:'AAA',parent_id:'AAA'}],
  indicators:indicatorIds.map((id,index)=>({id,theme:index===0?'Population':'Other'})),
  observations:indicatorIds.map(id=>({territory_id:'AAA:1',indicator_id:id,status:'observed',value:1}))
});
test('identified-only records complete neither source review nor country edition',()=>{
  const preflight={scope_id:'M49:019',countries:[{country_area_id:'AAA',name:'A',official_statistics_office:{identified:true,status:'identified'}}]};
  const matrix=buildCountryCompletionMatrix(preflight,{generatedAt:'2026-09-18T00:00:00Z'}),check=validateCountryCompletionMatrix(matrix,{expectedCountryIds:['AAA']});
  assert.equal(check.ok,true);assert.equal(matrix.source_review_complete_country_area_count,0);assert.equal(matrix.country_edition_complete_country_area_count,0);assert.equal(matrix.countries[0].source_review_status,'incomplete');assert.equal(matrix.countries[0].country_edition_status,'incomplete');
});

test('legacy evidence pointers without a retained hash and exact locator do not close a source domain',()=>{
  for(const evidence of [
    [{audit:'evidence/AAA_INTEGRATION_AUDIT.json'}],
    [{raw:'raw/AAA/census.pdf'}],
    [{path:'raw/AAA/census.pdf',sha256:'a'.repeat(64)}],
    [{object_path:'raw/AAA/census.pdf',object_sha256:'a'.repeat(64)}]
  ]){
    const country={country_area_id:'AAA',name:'A',official_statistics_office:{...verified,evidence}};
    const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{generatedAt:'2026-09-21T00:00:00Z'});
    assert.equal(matrix.countries[0].domains.official_statistics_office.source_review_complete,false);
  }
});

test('terminal non-adoption can complete source review but never a country edition',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition:index?'not_adopted':'integrated',reason:index?'Not published at compatible geography.':'Integrated.',coverage_complete:true,country_edition_eligible:index===0}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-18T00:00:00Z'}),check=validateCountryCompletionMatrix(matrix,{expectedCountryIds:['AAA']});
  assert.equal(check.ok,true);assert.equal(matrix.source_review_complete_country_area_count,1);assert.equal(matrix.country_edition_complete_country_area_count,0);assert.equal(matrix.countries[0].source_review_complete,true);assert.equal(matrix.countries[0].country_edition_complete,false);
});

test('an explicit evidence-backed theme gap closes source review without completing an edition or inventing a value',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const evidence=[{url:'https://example.org/questionnaire',note:'Official questionnaire and table inventory reviewed.'}];
  const records=CENSUS_THEMES.map((theme,index)=>index===0
    ? {country_area_id:'AAA',source_id:'source',table_id:'population',field_id:'population',indicator_id:'population',theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}
    : {country_area_id:'AAA',source_id:'source',table_id:'inventory',field_id:`gap-${index}`,theme,disposition:'unavailable',reason:'The reviewed official Census products do not publish this theme.',coverage_complete:true,country_edition_eligible:false,edition_gap_closed:true,gap_kind:'not_published',evidence});
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-20T00:00:00Z'});
  assert.equal(matrix.countries[0].source_review_complete,true);
  assert.equal(matrix.countries[0].country_edition_complete,false);
  assert.equal(matrix.countries[0].themes.population_total.data_available,true);
  assert.equal(matrix.countries[0].themes.nutrition.data_available,false);
  assert.equal(matrix.countries[0].themes.nutrition.gap_closed,true);
});

test('a claimed theme gap without evidence cannot complete an edition',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>index===0
    ? {country_area_id:'AAA',source_id:'source',table_id:'population',field_id:'population',indicator_id:'population',theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}
    : {country_area_id:'AAA',source_id:'source',table_id:'inventory',field_id:`gap-${index}`,theme,disposition:'unavailable',reason:'Claimed unavailable.',coverage_complete:true,edition_gap_closed:true,gap_kind:'not_published',evidence:[]});
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-20T00:00:00Z'});
  assert.equal(matrix.countries[0].source_review_complete,true);
  assert.equal(matrix.countries[0].country_edition_complete,false);
});

test('a country edition requires reviewed themes plus broad local integrated evidence',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset:localDataset(records.slice(0,12).map(row=>row.field_id)),generatedAt:'2026-09-18T00:00:00Z'}),check=validateCountryCompletionMatrix(matrix,{expectedCountryIds:['AAA']});
  assert.equal(check.ok,true);assert.equal(matrix.source_review_complete_country_area_count,1);assert.equal(matrix.country_edition_complete_country_area_count,1);assert.equal(matrix.countries[0].country_edition_complete,true);
});

test('explicitly excluded extra fields do not poison an otherwise complete theme',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.flatMap((theme,index)=>[
    {country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`eligible-${index}`,indicator_id:`eligible-${index}`,theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true},
    {country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`excluded-${index}`,theme,disposition:'not_adopted',reason:'Definition differs.',coverage_complete:false,country_edition_eligible:false}
  ]);
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset:localDataset(records.filter(row=>row.disposition==='integrated').slice(0,12).map(row=>row.field_id)),generatedAt:'2026-09-18T00:00:00Z'});
  assert.equal(matrix.countries[0].country_edition_complete,true);
});

test('all 15 integrated national themes do not complete an edition below the local-depth threshold',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset:localDataset(records.slice(0,9).map(row=>row.field_id)),generatedAt:'2026-09-21T00:00:00Z'});
  assert.equal(matrix.countries[0].themes.poverty.country_edition_complete,true);
  assert.equal(matrix.countries[0].edition_depth.local_observed_indicator_count,9);
  assert.equal(matrix.countries[0].edition_classification,'population_local_hierarchy_only');
  assert.equal(matrix.countries[0].country_edition_complete,false);
});

test('ten local indicators still require six of the eight diagnostic groups',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset:localDataset(records.slice(0,10).map(row=>row.field_id)),generatedAt:'2026-09-21T00:00:00Z'});
  assert.equal(matrix.countries[0].edition_depth.local_observed_indicator_count,10);
  assert.equal(matrix.countries[0].edition_depth.local_diagnostic_group_count,5);
  assert.equal(matrix.countries[0].country_edition_complete,false);
});

test('planning readiness is reported separately from a complete statistical diagnostic edition',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  for(const domain of ['planning_law','planning_guidance','plans_budgets_implementation_evaluation'])country[domain]={identified:true,completion_verified:false,urls:['https://example.org'],note:'Not acquired.',evidence:[]};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,indicator_id:`field-${index}`,theme,disposition:'integrated',reason:'Integrated.',coverage_complete:true,country_edition_eligible:true}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},dataset:localDataset(records.slice(0,12).map(row=>row.field_id)),generatedAt:'2026-09-21T00:00:00Z'});
  assert.equal(matrix.countries[0].source_review_complete,true);
  assert.equal(matrix.countries[0].country_edition_complete,true);
  assert.equal(matrix.countries[0].planning_readiness.ready,false);
  assert.deepEqual(matrix.countries[0].planning_readiness.incomplete_domains,['planning_law','planning_guidance','plans_budgets_implementation_evaluation']);
});

test('an evidenced nonresident-area profile may close structurally inapplicable domains and themes',()=>{
  const basis='The administering authority states that the area has no permanent resident population.';
  const evidence=[{url:'https://authority.example/nonresident',object_path:'raw/nonresident.json',object_sha256:'b'.repeat(64),locator:'Permanent-resident status, exact table row.',geography_match:'Applies to the named area.'}];
  const country={country_area_id:'AAA',name:'A',edition_mode:'nonresident_area_profile',official_statistics_office:{...verified}};
  for(const domain of COMPLETION_DOMAINS.filter(id=>!['semantic_table_column_inventory','official_statistics_office'].includes(id)))country[domain]={status:'structurally_not_applicable',structurally_not_applicable:true,applicability_basis:basis,evidence,completion_verified:true,urls:evidence.map(row=>row.url),note:basis};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'authority',table_id:'nonresident-profile',field_id:`field-${index}`,theme,disposition:'structurally_not_applicable',reason:'No resident population exists for this resident-population theme.',coverage_complete:true,country_edition_eligible:false,applicability_basis:basis,evidence}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-20T00:00:00Z'});
  assert.equal(matrix.countries[0].source_review_complete,true);
  assert.equal(matrix.countries[0].country_edition_complete,true);
  assert.equal(matrix.countries[0].edition_classification,'structural_nonresident_exception');
  assert.equal(matrix.countries[0].domains.latest_census.stage,'structurally_not_applicable');
});

test('structural exceptions cannot complete an ordinary country or omit evidence',()=>{
  const country={country_area_id:'AAA',name:'A'};for(const domain of COMPLETION_DOMAINS.filter(id=>id!=='semantic_table_column_inventory'))country[domain]={...verified};
  const records=CENSUS_THEMES.map((theme,index)=>({country_area_id:'AAA',source_id:'source',table_id:'table',field_id:`field-${index}`,theme,disposition:'structurally_not_applicable',reason:'Claimed inapplicable.',coverage_complete:true,country_edition_eligible:false,applicability_basis:'Claimed.',evidence:[]}));
  const matrix=buildCountryCompletionMatrix({scope_id:'M49:019',countries:[country]},{semanticInventory:{records},generatedAt:'2026-09-20T00:00:00Z'});
  assert.equal(matrix.countries[0].source_review_complete,true);
  assert.equal(matrix.countries[0].country_edition_complete,false);
});

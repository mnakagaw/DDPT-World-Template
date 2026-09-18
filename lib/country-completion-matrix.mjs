export const COMPLETION_DOMAINS=[
  'official_statistics_office','latest_census','census_results','table_catalog','machine_readable_data',
  'administrative_codes','adm1_adm2_boundaries','semantic_table_column_inventory',
  'planning_law','planning_guidance','plans_budgets_implementation_evaluation'
];
export const CENSUS_THEMES=[
  'population_total','age_sex','households_housing','drinking_water','sanitation','electricity',
  'education_literacy','employment','disability','migration','urban_rural','ethnicity',
  'health','nutrition','poverty'
];

function stage(record){
  if(!record)return 'not_started';
  if(record.adopted)return 'adopted';
  if(record.unavailable)return 'unavailable';
  if(record.restricted)return 'restricted';
  if(record.failed_with_evidence)return 'failed_with_evidence';
  if(record.geography_matched)return 'geography_matched';
  if(record.inspected)return 'inspected';
  if(record.acquired)return 'acquired';
  if(record.accessed)return 'accessed';
  if(record.identified)return 'identified';
  return String(record.status||'not_started');
}
const terminal=new Set(['integrated','not_adopted','unavailable','restricted','failed_with_evidence']);

export function buildCountryCompletionMatrix(preflight,{semanticInventory={records:[]},generatedAt=new Date().toISOString()}={}){
  const semanticRows=Array.isArray(semanticInventory?.records)?semanticInventory.records:[];
  const countries=(preflight?.countries||[]).map(country=>{
    const countryRows=semanticRows.filter(row=>row.country_area_id===country.country_area_id);
    const completeInventory=countryRows.length>0&&countryRows.every(row=>row.source_id&&row.table_id&&row.field_id&&terminal.has(row.disposition)&&row.reason);
    const domains={};
    for(const id of COMPLETION_DOMAINS){
      if(id==='semantic_table_column_inventory')domains[id]={stage:completeInventory?'inspected':'not_started',complete:completeInventory,evidence_count:countryRows.length,note:completeInventory?'Every inventoried numeric field has an explicit terminal disposition.':'No complete table-and-numeric-field semantic disposition inventory has been verified.'};
      else {const source=country[id];domains[id]={stage:stage(source),complete:source?.completion_verified===true,urls:source?.urls||[],note:source?.note||''};}
    }
    const themes={};
    for(const theme of CENSUS_THEMES){
      const rows=countryRows.filter(row=>row.theme===theme),complete=rows.length>0&&rows.every(row=>terminal.has(row.disposition)&&row.reason)&&rows.some(row=>row.coverage_complete===true);
      themes[theme]={stage:complete?'disposed':rows.length?'partial':'not_started',complete,record_count:rows.length,dispositions:[...new Set(rows.map(row=>row.disposition).filter(Boolean))]};
    }
    const incomplete_domains=Object.entries(domains).filter(([,value])=>!value.complete).map(([id])=>id);
    const incomplete_themes=Object.entries(themes).filter(([,value])=>!value.complete).map(([id])=>id);
    return {country_area_id:country.country_area_id,m49:country.m49,name:country.name,country_adapter_status:country.country_adapter_status||'not_started',domains,themes,overall_status:incomplete_domains.length||incomplete_themes.length?'incomplete':'complete',incomplete_domains,incomplete_themes};
  });
  return {schema_version:'1.0',scope_id:preflight?.scope_id||null,generated_at:generatedAt,completion_rule:'Every required domain and theme needs explicit completion_verified evidence or a field-level terminal disposition with a reason. Identified or accessed locations alone never complete a country adapter.',country_area_count:countries.length,complete_country_area_count:countries.filter(row=>row.overall_status==='complete').length,countries};
}

export function validateCountryCompletionMatrix(matrix,{expectedCountryIds=[]}={}){
  const errors=[],countries=Array.isArray(matrix?.countries)?matrix.countries:[],ids=countries.map(row=>row.country_area_id),unique=new Set(ids);
  if(matrix?.schema_version!=='1.0')errors.push('completion matrix schema_version must be 1.0');
  if(unique.size!==ids.length)errors.push('completion matrix has duplicate country_area_id values');
  if(expectedCountryIds.length){for(const id of expectedCountryIds)if(!unique.has(id))errors.push(`completion matrix is missing ${id}`);for(const id of unique)if(!expectedCountryIds.includes(id))errors.push(`completion matrix has unexpected ${id}`);}
  for(const country of countries){
    for(const domain of COMPLETION_DOMAINS)if(!country.domains?.[domain])errors.push(`${country.country_area_id}: missing domain ${domain}`);
    for(const theme of CENSUS_THEMES)if(!country.themes?.[theme])errors.push(`${country.country_area_id}: missing theme ${theme}`);
    const computed=[...COMPLETION_DOMAINS.map(id=>country.domains?.[id]?.complete===true),...CENSUS_THEMES.map(id=>country.themes?.[id]?.complete===true)].every(Boolean)?'complete':'incomplete';
    if(country.overall_status!==computed)errors.push(`${country.country_area_id}: overall_status does not match domain/theme completion`);
  }
  if(matrix?.country_area_count!==countries.length)errors.push('completion matrix country_area_count is incorrect');
  if(matrix?.complete_country_area_count!==countries.filter(row=>row.overall_status==='complete').length)errors.push('completion matrix complete_country_area_count is incorrect');
  return {ok:errors.length===0,errors,country_area_count:countries.length,complete_country_area_count:countries.filter(row=>row.overall_status==='complete').length};
}

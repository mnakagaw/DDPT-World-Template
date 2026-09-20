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
const reviewTerminal=new Set(['integrated','not_adopted','unavailable','restricted','failed_with_evidence','structurally_not_applicable']);
const editionGapTerminal=new Set(['not_adopted','unavailable','restricted','failed_with_evidence']);
const editionDomainStages={
  official_statistics_office:new Set(['inspected','acquired','geography_matched','adopted','integrated']),
  latest_census:new Set(['adopted','integrated']),
  census_results:new Set(['adopted','integrated']),
  table_catalog:new Set(['inspected','acquired','adopted','integrated']),
  machine_readable_data:new Set(['adopted','integrated']),
  administrative_codes:new Set(['geography_matched','adopted','integrated']),
  adm1_adm2_boundaries:new Set(['adopted','integrated']),
  planning_law:new Set(['inspected','acquired','adopted','integrated']),
  planning_guidance:new Set(['inspected','acquired','adopted','integrated']),
  plans_budgets_implementation_evaluation:new Set(['inspected','acquired','adopted','integrated'])
};

export function buildCountryCompletionMatrix(preflight,{semanticInventory={records:[]},generatedAt=new Date().toISOString()}={}){
  const semanticRows=Array.isArray(semanticInventory?.records)?semanticInventory.records:[];
  const countries=(preflight?.countries||[]).map(country=>{
    const countryRows=semanticRows.filter(row=>row.country_area_id===country.country_area_id);
    const nonresidentProfile=country.edition_mode==='nonresident_area_profile';
    const structuralRow=row=>nonresidentProfile&&row.disposition==='structurally_not_applicable'&&row.coverage_complete===true&&typeof row.applicability_basis==='string'&&row.applicability_basis.trim()&&Array.isArray(row.evidence)&&row.evidence.length>0;
    const integratedRow=row=>row.disposition==='integrated'&&row.country_edition_eligible===true&&row.coverage_complete===true;
    const evidencedGapRow=row=>editionGapTerminal.has(row.disposition)&&row.edition_gap_closed===true&&row.coverage_complete===true&&typeof row.gap_kind==='string'&&row.gap_kind.trim()&&typeof row.reason==='string'&&row.reason.trim()&&Array.isArray(row.evidence)&&row.evidence.length>0;
    const sourceReviewInventory=countryRows.length>0&&countryRows.every(row=>row.source_id&&row.table_id&&row.field_id&&reviewTerminal.has(row.disposition)&&row.reason);
    const corePopulationIntegrated=countryRows.some(row=>row.theme==='population_total'&&integratedRow(row));
    const editionInventory=sourceReviewInventory&&(corePopulationIntegrated||nonresidentProfile)&&CENSUS_THEMES.every(theme=>countryRows.some(row=>row.theme===theme&&(integratedRow(row)||evidencedGapRow(row)||structuralRow(row))));
    const domains={};
    for(const id of COMPLETION_DOMAINS){
      if(id==='semantic_table_column_inventory')domains[id]={stage:sourceReviewInventory?'inspected':'not_started',source_review_complete:sourceReviewInventory,country_edition_complete:editionInventory,evidence_count:countryRows.length,note:sourceReviewInventory?'Every inventoried numeric field has an explicit terminal disposition.':'No complete table-and-numeric-field semantic disposition inventory has been verified.'};
      else {
        const source=country[id],currentStage=stage(source),sourceReviewComplete=source?.completion_verified===true;
        const structuralDomain=nonresidentProfile&&source?.structurally_not_applicable===true&&typeof source?.applicability_basis==='string'&&source.applicability_basis.trim()&&Array.isArray(source?.evidence)&&source.evidence.length>0;
        domains[id]={stage:structuralDomain?'structurally_not_applicable':currentStage,source_review_complete:sourceReviewComplete,country_edition_complete:sourceReviewComplete&&((editionDomainStages[id]?.has(currentStage)||false)||structuralDomain),urls:source?.urls||[],note:source?.note||''};
      }
    }
    const themes={};
    for(const theme of CENSUS_THEMES){
      const rows=countryRows.filter(row=>row.theme===theme);
      const sourceReviewComplete=rows.length>0&&rows.every(row=>reviewTerminal.has(row.disposition)&&row.reason)&&rows.some(row=>row.coverage_complete===true);
      const integrated=rows.some(integratedRow),gapClosed=rows.some(evidencedGapRow),structural=rows.some(structuralRow);
      const countryEditionComplete=sourceReviewComplete&&(integrated||gapClosed||structural)&&(theme!=='population_total'||integrated||structural);
      themes[theme]={stage:sourceReviewComplete?'disposed':rows.length?'partial':'not_started',source_review_complete:sourceReviewComplete,country_edition_complete:countryEditionComplete,data_available:integrated,gap_closed:gapClosed||structural,record_count:rows.length,dispositions:[...new Set(rows.map(row=>row.disposition).filter(Boolean))]};
    }
    const source_review_incomplete_domains=Object.entries(domains).filter(([,value])=>!value.source_review_complete).map(([id])=>id);
    const source_review_incomplete_themes=Object.entries(themes).filter(([,value])=>!value.source_review_complete).map(([id])=>id);
    const country_edition_incomplete_domains=Object.entries(domains).filter(([,value])=>!value.country_edition_complete).map(([id])=>id);
    const country_edition_incomplete_themes=Object.entries(themes).filter(([,value])=>!value.country_edition_complete).map(([id])=>id);
    const source_review_complete=!source_review_incomplete_domains.length&&!source_review_incomplete_themes.length;
    const country_edition_complete=!country_edition_incomplete_domains.length&&!country_edition_incomplete_themes.length;
    return {country_area_id:country.country_area_id,m49:country.m49,name:country.name,country_adapter_status:country.country_adapter_status||'not_started',source_review_complete,country_edition_complete,source_review_status:source_review_complete?'complete':'incomplete',country_edition_status:country_edition_complete?'complete':'incomplete',domains,themes,source_review_incomplete_domains,source_review_incomplete_themes,country_edition_incomplete_domains,country_edition_incomplete_themes};
  });
  return {schema_version:'2.0',scope_id:preflight?.scope_id||null,generated_at:generatedAt,source_review_rule:'Every required domain and theme needs an evidence-backed terminal review disposition. This status does not mean that a country edition exists.',country_edition_rule:'Every required source domain must reach the required stage. Resident editions require a complete eligible population-total field. Each other theme must either contain a complete eligible integrated field or an explicit evidence-backed terminal gap with edition_gap_closed=true, gap_kind, reason and evidence. A gap closes the edition workflow but remains data_available=false; it never creates a value. Formally evidenced nonresident areas may use the stricter structurally_not_applicable exception.',country_area_count:countries.length,source_review_complete_country_area_count:countries.filter(row=>row.source_review_complete).length,country_edition_complete_country_area_count:countries.filter(row=>row.country_edition_complete).length,countries};
}

export function validateCountryCompletionMatrix(matrix,{expectedCountryIds=[]}={}){
  const errors=[],countries=Array.isArray(matrix?.countries)?matrix.countries:[],ids=countries.map(row=>row.country_area_id),unique=new Set(ids);
  if(matrix?.schema_version!=='2.0')errors.push('completion matrix schema_version must be 2.0');
  if(unique.size!==ids.length)errors.push('completion matrix has duplicate country_area_id values');
  if(expectedCountryIds.length){for(const id of expectedCountryIds)if(!unique.has(id))errors.push(`completion matrix is missing ${id}`);for(const id of unique)if(!expectedCountryIds.includes(id))errors.push(`completion matrix has unexpected ${id}`);}
  for(const country of countries){
    for(const domain of COMPLETION_DOMAINS)if(!country.domains?.[domain])errors.push(`${country.country_area_id}: missing domain ${domain}`);
    for(const theme of CENSUS_THEMES)if(!country.themes?.[theme])errors.push(`${country.country_area_id}: missing theme ${theme}`);
    const sourceReview=[...COMPLETION_DOMAINS.map(id=>country.domains?.[id]?.source_review_complete===true),...CENSUS_THEMES.map(id=>country.themes?.[id]?.source_review_complete===true)].every(Boolean);
    const edition=[...COMPLETION_DOMAINS.map(id=>country.domains?.[id]?.country_edition_complete===true),...CENSUS_THEMES.map(id=>country.themes?.[id]?.country_edition_complete===true)].every(Boolean);
    if(country.source_review_complete!==sourceReview||country.source_review_status!==(sourceReview?'complete':'incomplete'))errors.push(`${country.country_area_id}: source review status does not match domain/theme evidence`);
    if(country.country_edition_complete!==edition||country.country_edition_status!==(edition?'complete':'incomplete'))errors.push(`${country.country_area_id}: country edition status does not match integrated domain/theme evidence`);
  }
  const reviewCount=countries.filter(row=>row.source_review_complete).length,editionCount=countries.filter(row=>row.country_edition_complete).length;
  if(matrix?.country_area_count!==countries.length)errors.push('completion matrix country_area_count is incorrect');
  if(matrix?.source_review_complete_country_area_count!==reviewCount)errors.push('completion matrix source_review_complete_country_area_count is incorrect');
  if(matrix?.country_edition_complete_country_area_count!==editionCount)errors.push('completion matrix country_edition_complete_country_area_count is incorrect');
  return {ok:errors.length===0,errors,country_area_count:countries.length,source_review_complete_country_area_count:reviewCount,country_edition_complete_country_area_count:editionCount};
}

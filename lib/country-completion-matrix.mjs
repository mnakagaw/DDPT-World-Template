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
export const MIN_BROAD_LOCAL_INDICATORS=10;
export const MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS=6;
export const LOCAL_DIAGNOSTIC_GROUPS={
  housing_services:['households_housing','drinking_water','sanitation','electricity'],
  education:['education_literacy'],employment:['employment'],disability_health:['disability','health'],
  migration_urban:['migration','urban_rural'],ethnicity:['ethnicity'],nutrition:['nutrition'],poverty:['poverty']
};
export const PLANNING_DOMAINS=['planning_law','planning_guidance','plans_budgets_implementation_evaluation'];
export const STATISTICAL_DOMAINS=COMPLETION_DOMAINS.filter(id=>!PLANNING_DOMAINS.includes(id));
export const EDITION_CLASSIFICATIONS=[
  'source_review_incomplete','source_review_complete','national_only','population_local_hierarchy_only','broad_local_edition','structural_nonresident_exception'
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
const evidenceReference=row=>{
  if(!row)return false;
  const objectPath=String(row.object_path||row.path||'').trim();
  const objectHash=String(row.object_sha256||row.sha256||'').trim();
  const locator=String(row.locator||'').trim();
  return Boolean(objectPath&&/^[a-f0-9]{64}$/i.test(objectHash)&&locator);
};
const domainEvidenceComplete=(source,id)=>{
  const evidence=Array.isArray(source?.evidence)?source.evidence:[];
  if(source?.completion_verified!==true||!evidence.length||!evidence.some(evidenceReference))return false;
  if(['administrative_codes','adm1_adm2_boundaries'].includes(id))return source.geography_matched===true||evidence.some(row=>typeof row?.geography_match==='string'&&row.geography_match.trim());
  return Array.isArray(source.urls)&&source.urls.length>0&&typeof source.note==='string'&&source.note.trim().length>0;
};

export function buildCountryCompletionMatrix(preflight,{semanticInventory={records:[]},dataset={territories:[],observations:[],indicators:[]},generatedAt=new Date().toISOString()}={}){
  const semanticRows=Array.isArray(semanticInventory?.records)?semanticInventory.records:[];
  const territories=Array.isArray(dataset?.territories)?dataset.territories:[],observations=Array.isArray(dataset?.observations)?dataset.observations:[];
  const indicatorById=new Map((dataset?.indicators||[]).map(row=>[row.id,row]));
  const countries=(preflight?.countries||[]).map(country=>{
    const countryRows=semanticRows.filter(row=>row.country_area_id===country.country_area_id);
    const nonresidentProfile=country.edition_mode==='nonresident_area_profile';
    const domesticIds=new Set(territories.filter(row=>row.country_id===country.country_area_id&&row.id!==country.country_area_id).map(row=>row.id));
    const localObservedIndicatorIds=[...new Set(observations.filter(row=>domesticIds.has(row.territory_id)&&row.status==='observed'&&row.indicator_id).map(row=>row.indicator_id))].sort();
    const localPopulationAvailable=localObservedIndicatorIds.some(id=>{
      const indicator=indicatorById.get(id),label=String(indicator?.theme||'').toLowerCase();
      return label==='population'||/(^|_)POP(?:ULATION)?(?:_|$)/i.test(id);
    });
    const structuralRow=row=>nonresidentProfile&&row.disposition==='structurally_not_applicable'&&row.coverage_complete===true&&typeof row.applicability_basis==='string'&&row.applicability_basis.trim()&&Array.isArray(row.evidence)&&row.evidence.length>0;
    const integratedRow=row=>row.disposition==='integrated'&&row.country_edition_eligible===true&&row.coverage_complete===true;
    const evidencedGapRow=row=>editionGapTerminal.has(row.disposition)&&row.edition_gap_closed===true&&row.coverage_complete===true&&typeof row.gap_kind==='string'&&row.gap_kind.trim()&&typeof row.reason==='string'&&row.reason.trim()&&Array.isArray(row.evidence)&&row.evidence.length>0;
    const sourceReviewInventory=countryRows.length>0&&countryRows.every(row=>row.source_id&&row.table_id&&row.field_id&&reviewTerminal.has(row.disposition)&&row.reason);
    const localIndicatorSet=new Set(localObservedIndicatorIds);
    const localIntegratedThemes=new Set(countryRows.filter(row=>row.disposition==='integrated'&&row.country_edition_eligible===true&&String(row.indicator_id||'').split(';').some(id=>localIndicatorSet.has(id))).map(row=>row.theme));
    const localAgeSexAvailable=localIntegratedThemes.has('age_sex');
    const localDiagnosticGroups=Object.entries(LOCAL_DIAGNOSTIC_GROUPS).filter(([,themes])=>themes.some(theme=>localIntegratedThemes.has(theme))).map(([id])=>id);
    const domains={};
    for(const id of COMPLETION_DOMAINS){
      if(id==='semantic_table_column_inventory')domains[id]={stage:sourceReviewInventory?'inspected':'not_started',source_review_complete:sourceReviewInventory,country_edition_complete:sourceReviewInventory,evidence_count:countryRows.length,note:sourceReviewInventory?'Every inventoried numeric field has an explicit terminal disposition.':'No complete table-and-numeric-field semantic disposition inventory has been verified.'};
      else {
        const source=country[id],currentStage=stage(source);
        const structuralDomain=nonresidentProfile&&source?.structurally_not_applicable===true&&typeof source?.applicability_basis==='string'&&source.applicability_basis.trim()&&Array.isArray(source?.evidence)&&source.evidence.length>0;
        const sourceReviewComplete=domainEvidenceComplete(source,id)||Boolean(structuralDomain);
        domains[id]={stage:structuralDomain?'structurally_not_applicable':currentStage,source_review_complete:sourceReviewComplete,country_edition_complete:sourceReviewComplete&&((editionDomainStages[id]?.has(currentStage)||false)||structuralDomain),urls:source?.urls||[],note:source?.note||''};
      }
    }
    const themes={};
    for(const theme of CENSUS_THEMES){
      const rows=countryRows.filter(row=>row.theme===theme);
      const sourceReviewComplete=rows.length>0&&rows.every(row=>reviewTerminal.has(row.disposition)&&row.reason)&&rows.some(row=>row.coverage_complete===true);
      const integrated=rows.some(integratedRow),gapClosed=rows.some(evidencedGapRow),structural=rows.some(structuralRow);
      const countryEditionComplete=sourceReviewComplete&&(integrated||structural);
      themes[theme]={stage:sourceReviewComplete?'disposed':rows.length?'partial':'not_started',source_review_complete:sourceReviewComplete,country_edition_complete:countryEditionComplete,data_available:integrated,gap_closed:gapClosed||structural,source_review_gap_closed:gapClosed,record_count:rows.length,dispositions:[...new Set(rows.map(row=>row.disposition).filter(Boolean))]};
    }
    const source_review_incomplete_domains=STATISTICAL_DOMAINS.filter(id=>!domains[id]?.source_review_complete);
    const source_review_incomplete_themes=Object.entries(themes).filter(([,value])=>!value.source_review_complete).map(([id])=>id);
    const country_edition_incomplete_domains=STATISTICAL_DOMAINS.filter(id=>!domains[id]?.country_edition_complete);
    const country_edition_incomplete_themes=Object.entries(themes).filter(([,value])=>!value.country_edition_complete).map(([id])=>id);
    const source_review_complete=!source_review_incomplete_domains.length&&!source_review_incomplete_themes.length;
    const statisticalDomainsReady=!country_edition_incomplete_domains.length;
    const broadLocalEdition=source_review_complete&&statisticalDomainsReady&&domesticIds.size>0&&localPopulationAvailable&&localAgeSexAvailable&&localObservedIndicatorIds.length>=MIN_BROAD_LOCAL_INDICATORS&&localDiagnosticGroups.length>=MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS;
    const structuralNonresidentException=source_review_complete&&nonresidentProfile&&CENSUS_THEMES.every(theme=>themes[theme].country_edition_complete);
    const country_edition_complete=broadLocalEdition||structuralNonresidentException;
    const planningIncompleteDomains=PLANNING_DOMAINS.filter(id=>!domains[id]?.source_review_complete||!domains[id]?.country_edition_complete),planningReady=planningIncompleteDomains.length===0;
    const planning_readiness={ready:planningReady,status:planningReady?'ready':'incomplete',incomplete_domains:planningIncompleteDomains};
    const edition_classification=!source_review_complete?'source_review_incomplete':structuralNonresidentException?'structural_nonresident_exception':broadLocalEdition?'broad_local_edition':domesticIds.size>0&&localPopulationAvailable?'population_local_hierarchy_only':localObservedIndicatorIds.length===0?'national_only':'source_review_complete';
    const country_edition_incomplete_reasons=[];
    if(!country_edition_complete){
      if(country_edition_incomplete_domains.length)country_edition_incomplete_reasons.push('required_source_domains_incomplete');
      if(domesticIds.size===0)country_edition_incomplete_reasons.push('no_domestic_hierarchy');
      if(!localPopulationAvailable)country_edition_incomplete_reasons.push('local_population_not_integrated');
      if(!localAgeSexAvailable)country_edition_incomplete_reasons.push('local_age_sex_not_integrated');
      if(localObservedIndicatorIds.length<MIN_BROAD_LOCAL_INDICATORS)country_edition_incomplete_reasons.push('insufficient_local_observed_indicator_depth');
      if(localDiagnosticGroups.length<MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS)country_edition_incomplete_reasons.push('insufficient_local_diagnostic_group_depth');
    }
    return {country_area_id:country.country_area_id,m49:country.m49,name:country.name,country_adapter_status:country.country_adapter_status||'not_started',edition_mode:country.edition_mode||'resident_country_edition',edition_classification,source_review_complete,country_edition_complete,source_review_status:source_review_complete?'complete':'incomplete',country_edition_status:country_edition_complete?'complete':'incomplete',planning_readiness,edition_depth:{domestic_territory_count:domesticIds.size,local_observed_indicator_count:localObservedIndicatorIds.length,minimum_local_observed_indicators:MIN_BROAD_LOCAL_INDICATORS,local_population_available:localPopulationAvailable,local_age_sex_available:localAgeSexAvailable,local_integrated_themes:[...localIntegratedThemes].sort(),local_diagnostic_group_count:localDiagnosticGroups.length,minimum_local_diagnostic_groups:MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS,local_diagnostic_groups:localDiagnosticGroups,local_observed_indicator_ids:localObservedIndicatorIds},domains,themes,source_review_incomplete_domains,source_review_incomplete_themes,country_edition_incomplete_domains,country_edition_incomplete_themes,country_edition_incomplete_reasons};
  });
  const classification_counts=Object.fromEntries(EDITION_CLASSIFICATIONS.map(id=>[id,countries.filter(row=>row.edition_classification===id).length]));
  return {schema_version:'2.0',scope_id:preflight?.scope_id||null,generated_at:generatedAt,source_review_rule:'Every required statistical source domain and all 15 themes need an evidence-backed terminal review disposition. not_adopted, unavailable, restricted and failed_with_evidence close review only. Planning readiness is reported separately.',country_edition_rule:`country_edition_complete means a statistical diagnostic edition is ready. An ordinary edition requires reviewed statistical domains and all 15 theme reviews, locally integrated population and age/sex, at least ${MIN_BROAD_LOCAL_INDICATORS} distinct observed indicators on domestic territories, and at least ${MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS} of 8 local diagnostic groups. National observations, common international series and terminal gaps do not count toward local depth. Formally evidenced nonresident areas may use the stricter structurally_not_applicable exception. Planning readiness is separate and does not change this flag.`,minimum_broad_local_observed_indicators:MIN_BROAD_LOCAL_INDICATORS,minimum_broad_local_diagnostic_groups:MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS,local_diagnostic_groups:LOCAL_DIAGNOSTIC_GROUPS,country_area_count:countries.length,source_review_complete_country_area_count:countries.filter(row=>row.source_review_complete).length,broad_local_edition_country_area_count:classification_counts.broad_local_edition,structural_nonresident_exception_country_area_count:classification_counts.structural_nonresident_exception,country_edition_complete_country_area_count:countries.filter(row=>row.country_edition_complete).length,planning_ready_country_area_count:countries.filter(row=>row.planning_readiness.ready).length,classification_counts,countries};
}

export function validateCountryCompletionMatrix(matrix,{expectedCountryIds=[]}={}){
  const errors=[],countries=Array.isArray(matrix?.countries)?matrix.countries:[],ids=countries.map(row=>row.country_area_id),unique=new Set(ids);
  if(matrix?.schema_version!=='2.0')errors.push('completion matrix schema_version must be 2.0');
  if(unique.size!==ids.length)errors.push('completion matrix has duplicate country_area_id values');
  if(expectedCountryIds.length){for(const id of expectedCountryIds)if(!unique.has(id))errors.push(`completion matrix is missing ${id}`);for(const id of unique)if(!expectedCountryIds.includes(id))errors.push(`completion matrix has unexpected ${id}`);}
  for(const country of countries){
    for(const domain of COMPLETION_DOMAINS)if(!country.domains?.[domain])errors.push(`${country.country_area_id}: missing domain ${domain}`);
    for(const theme of CENSUS_THEMES)if(!country.themes?.[theme])errors.push(`${country.country_area_id}: missing theme ${theme}`);
    const sourceReview=[...STATISTICAL_DOMAINS.map(id=>country.domains?.[id]?.source_review_complete===true),...CENSUS_THEMES.map(id=>country.themes?.[id]?.source_review_complete===true)].every(Boolean);
    const editionEvidence=STATISTICAL_DOMAINS.map(id=>country.domains?.[id]?.country_edition_complete===true).every(Boolean);
    const structuralMode=country.edition_mode==='nonresident_area_profile',structural=country.edition_classification==='structural_nonresident_exception'&&structuralMode;
    const broad=country.edition_classification==='broad_local_edition'&&country.edition_depth?.domestic_territory_count>0&&country.edition_depth?.local_population_available===true&&country.edition_depth?.local_age_sex_available===true&&country.edition_depth?.local_observed_indicator_count>=MIN_BROAD_LOCAL_INDICATORS&&country.edition_depth?.local_diagnostic_group_count>=MIN_BROAD_LOCAL_DIAGNOSTIC_GROUPS;
    const edition=sourceReview&&editionEvidence&&(broad||structural);
    if(!EDITION_CLASSIFICATIONS.includes(country.edition_classification))errors.push(`${country.country_area_id}: invalid edition classification`);
    for(const theme of CENSUS_THEMES){const value=country.themes?.[theme];if(value?.country_edition_complete===true&&value?.data_available!==true&&!(structuralMode&&value?.dispositions?.includes('structurally_not_applicable')))errors.push(`${country.country_area_id}: ${theme} cannot complete a country edition without integrated data`);}
    if(country.source_review_complete!==sourceReview||country.source_review_status!==(sourceReview?'complete':'incomplete'))errors.push(`${country.country_area_id}: source review status does not match domain/theme evidence`);
    if(country.country_edition_complete!==edition||country.country_edition_status!==(edition?'complete':'incomplete'))errors.push(`${country.country_area_id}: country edition status does not match integrated domain/theme evidence`);
    const planningReady=PLANNING_DOMAINS.every(id=>country.domains?.[id]?.source_review_complete===true&&country.domains?.[id]?.country_edition_complete===true);
    if(country.planning_readiness?.ready!==planningReady||country.planning_readiness?.status!==(planningReady?'ready':'incomplete'))errors.push(`${country.country_area_id}: planning readiness does not match planning-domain evidence`);
  }
  const reviewCount=countries.filter(row=>row.source_review_complete).length,editionCount=countries.filter(row=>row.country_edition_complete).length;
  if(matrix?.country_area_count!==countries.length)errors.push('completion matrix country_area_count is incorrect');
  if(matrix?.source_review_complete_country_area_count!==reviewCount)errors.push('completion matrix source_review_complete_country_area_count is incorrect');
  if(matrix?.country_edition_complete_country_area_count!==editionCount)errors.push('completion matrix country_edition_complete_country_area_count is incorrect');
  const counts=Object.fromEntries(EDITION_CLASSIFICATIONS.map(id=>[id,countries.filter(row=>row.edition_classification===id).length]));
  if(JSON.stringify(matrix?.classification_counts)!==JSON.stringify(counts))errors.push('completion matrix classification_counts are incorrect');
  if(matrix?.broad_local_edition_country_area_count!==counts.broad_local_edition)errors.push('completion matrix broad_local_edition_country_area_count is incorrect');
  if(matrix?.structural_nonresident_exception_country_area_count!==counts.structural_nonresident_exception)errors.push('completion matrix structural_nonresident_exception_country_area_count is incorrect');
  if(matrix?.planning_ready_country_area_count!==countries.filter(row=>row.planning_readiness?.ready).length)errors.push('completion matrix planning_ready_country_area_count is incorrect');
  return {ok:errors.length===0,errors,country_area_count:countries.length,source_review_complete_country_area_count:reviewCount,country_edition_complete_country_area_count:editionCount};
}

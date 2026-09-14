import {readFile} from 'node:fs/promises';
import {CENTRAL_AMERICA_CONFIG} from './regional-pilot.mjs';

const list=value=>Array.isArray(value)?value:[];
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const populationLabel=value=>new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(value);

export async function loadNormalizedCensus(file){
  const data=JSON.parse(await readFile(file,'utf8'));validateNormalizedCensus(data);return data;
}

export function validateNormalizedCensus(data,config=CENTRAL_AMERICA_CONFIG){
  if(data?.schema_version!=='1.0')throw new Error('Normalized census schema_version must be 1.0');
  if(data.scope_id!==config.id)throw new Error(`Normalized census scope mismatch: ${data.scope_id}`);
  if(!data.indicator?.id||data.indicator.series_family!=='census'||data.indicator.display_role!=='primary')throw new Error('Normalized census needs one primary census indicator');
  if(data.indicator.period_policy!=='latest_available_by_component'||data.indicator.aggregation!=='sum')throw new Error('Census population requires explicit mixed-period full-cover summation');
  const countries=list(data.countries),countryIds=countries.map(country=>country.country_id);
  if(!countries.length||new Set(countryIds).size!==countryIds.length)throw new Error('Normalized census countries must be unique');
  for(const id of countryIds)if(!config.member_ids.includes(id))throw new Error(`Normalized census country is outside the pilot: ${id}`);
  const sourceIds=new Set([data.series_source?.id]),territoryIds=new Set(config.member_ids),observationKeys=new Set();
  if(!data.series_source?.id)throw new Error('Normalized census series source is required');
  for(const country of countries){
    for(const source of list(country.sources)){
      if(!source?.id||sourceIds.has(source.id))throw new Error(`Duplicate or missing normalized census source: ${source?.id}`);sourceIds.add(source.id);
      if(!/^https:\/\//.test(source.url||'')||!source.sha256)throw new Error(`Normalized census source needs HTTPS and hash: ${source.id}`);
    }
    for(const territory of list(country.territories)){
      if(!territory?.id||territoryIds.has(territory.id))throw new Error(`Duplicate normalized census territory: ${territory?.id}`);territoryIds.add(territory.id);
      if(territory.country_id!==country.country_id)throw new Error(`Territory country mismatch: ${territory.id}`);
    }
  }
  for(const country of countries){
    for(const territory of list(country.territories))if(!territoryIds.has(territory.parent_id))throw new Error(`Unknown normalized parent: ${territory.id}`);
    for(const row of list(country.observations)){
      if(!territoryIds.has(row.territory_id)||row.indicator_id!==data.indicator.id||row.status!=='observed'||!finite(row.value)||!sourceIds.has(row.source_id))throw new Error(`Invalid normalized census observation: ${row.territory_id}`);
      const key=`${row.territory_id}|${row.indicator_id}|${row.period}`;if(observationKeys.has(key))throw new Error(`Duplicate normalized observation: ${key}`);observationKeys.add(key);
    }
    for(const comparison of list(country.comparisons)){
      if(!territoryIds.has(comparison.parent_id)||!comparison.member_ids?.length||comparison.member_ids.some(id=>!territoryIds.has(id))||comparison.source_ids?.some(id=>!sourceIds.has(id)))throw new Error(`Invalid normalized comparison: ${comparison.parent_id}`);
    }
  }
  const expectedTerritories=countries.reduce((sum,country)=>sum+country.territories.length,0),expectedObservations=countries.reduce((sum,country)=>sum+country.observations.length,0);
  if(data.summary?.territories_added!==expectedTerritories||data.summary?.observations_added!==expectedObservations)throw new Error('Normalized census summary counts do not match its records');
  const pending=config.member_ids.filter(id=>!countryIds.includes(id));
  if(JSON.stringify(data.summary?.countries_acquired)!==JSON.stringify(countryIds)||JSON.stringify(data.summary?.countries_pending)!==JSON.stringify(pending))throw new Error('Normalized census country coverage summary does not match its records');
  if(data.summary?.regional_total_status!=='not_available_incomplete_country_coverage'&&pending.length)throw new Error('Partial census coverage cannot claim a regional total');
  if(!pending.length){
    if(data.summary?.regional_total_status!=='available_complete_country_coverage_mixed_reference_years')throw new Error('Complete census coverage needs the explicit mixed-reference-year regional status');
    const countryValues=countries.map(country=>country.observations.find(row=>row.territory_id===country.country_id));
    if(countryValues.some(row=>!row||!finite(row.value)))throw new Error('Every complete-cover country needs an exact national census observation');
    const expected=countryValues.reduce((sum,row)=>sum+row.value,0);
    if(!finite(data.summary?.regional_total)||Math.abs(data.summary.regional_total-expected)>1e-9)throw new Error('Normalized census regional total must equal the seven exact country observations');
    for(const country of countries)if(String(data.summary?.regional_total_component_periods?.[country.country_id])!==String(country.period))throw new Error(`Regional component period mismatch: ${country.country_id}`);
  }
  return data;
}

export function mergeCensusPilot(dataset,normalized,config=CENTRAL_AMERICA_CONFIG){
  validateNormalizedCensus(normalized,config);
  const result=structuredClone(dataset),countries=normalized.countries,acquiredIds=countries.map(country=>country.country_id),pendingIds=config.member_ids.filter(id=>!acquiredIds.includes(id));
  const regionalPopulation=pendingIds.length?null:populationLabel(normalized.summary.regional_total);
  const existingTerritories=new Set(result.territories.map(area=>area.id)),existingSources=new Set(result.sources.map(source=>source.id));
  if(existingSources.has(normalized.series_source.id)||result.indicators.some(indicator=>indicator.id===normalized.indicator.id))throw new Error('Census series collides with an existing dataset record');
  result.sources.push(structuredClone(normalized.series_source));existingSources.add(normalized.series_source.id);
  result.indicators.unshift(structuredClone(normalized.indicator));
  for(const country of countries){
    for(const source of country.sources){if(existingSources.has(source.id))throw new Error(`Census source collides with dataset: ${source.id}`);result.sources.push(structuredClone(source));existingSources.add(source.id);}
    for(const territory of country.territories){if(existingTerritories.has(territory.id))throw new Error(`Census territory collides with dataset: ${territory.id}`);result.territories.push(structuredClone(territory));existingTerritories.add(territory.id);}
    result.observations.push(...country.observations.map(row=>structuredClone(row)));
    result.analysis.comparisons.push(...country.comparisons.map(row=>structuredClone(row)));
    result.analysis.terminal_territory_ids.push(...country.terminal_territory_ids);
  }
  result.analysis.aggregation.rules.unshift({indicator_id:normalized.indicator.id,method:'sum',completeness:'full_cover',period_policy:'latest_available_by_component',label:'AreaData mixed-reference-year official census population',note:'Use each country exact census population before any lower-area cover. A seven-country value exists only after all members pass source, meaning and non-overlap checks; every component country year remains visible.'});
  result.analysis.default_period_by_indicator[normalized.indicator.id]='latest-available';
  result.analysis.pilot.available_series_families=['census',...result.analysis.pilot.available_series_families.filter(value=>value!=='census')];
  Object.assign(result.analysis.pilot,{census_adapter_status:pendingIds.length?'partial':'complete',census_country_ids:acquiredIds,census_pending_country_ids:pendingIds,census_observations:normalized.summary.observations_added,census_territories:normalized.summary.territories_added,regional_census_total_status:normalized.summary.regional_total_status});
  result.gaps=result.gaps.map(gap=>gap.category==='census_primary_series'?{...gap,status:pendingIds.length?'partial':'ready',detail:pendingIds.length?`Official census population is integrated for ${acquiredIds.length} of ${config.member_ids.length} pilot countries (${acquiredIds.join(', ')}). The remaining ${pendingIds.length} (${pendingIds.join(', ')}) prevent a seven-country census total.`:`Official census population is integrated for all ${config.member_ids.length} pilot countries. The displayed regional value is ${regionalPopulation} people and retains mixed component years; source precision remains in data exports.`,next_action:pendingIds.length?'Acquire and audit each pending national source, population concept, country total and geography before enabling the regional value.':'Retain every country year, country method and reconciliation exception in screens and exports.'}:gap.category==='regional_aggregation'?{...gap,status:pendingIds.length?'partial':'ready',detail:pendingIds.length?'No complete seven-country census cover is available. Missing country coverage remains explicit.':`A full seven-country cover is available from exact national census observations. The displayed mixed-reference-year sum is ${regionalPopulation} people; it is not reconstructed from lower-area rows, and source precision remains in data exports.`,next_action:'Keep component countries, years, methods and source links visible; recompute only when all seven exact national observations remain available.'}:gap.category==='country_adapters'?{...gap,status:'partial',detail:`Official census hierarchy records are active for ${acquiredIds.join(', ')}. The country-specific terminal levels, codes and known source reconciliation exceptions remain distinct; polygon joins and planning materials are separate work.`,next_action:'Join compatible official polygons by verified codes where available, document uncoded source-order IDs, and continue country planning adapters.'}:gap);
  result.gaps.push({category:'census_geography_depth',status:'partial',detail:'All seven countries have an adopted subnational census layer, but terminal depth differs by official product: Belize district; Guatemala, Honduras and Nicaragua municipality; El Salvador district; Costa Rica canton; Panama corregimiento. Known withheld or audit-only rows remain explicit.',next_action:'Adopt finer layers only after official identity, role, complete membership and compatible boundary or coordinate use are documented.',source_id:normalized.series_source.id});
  result.collection.adapters.push('central-america-official-census-population-v1');
  result.collection.notes.push(pendingIds.length?`Primary census population currently covers ${acquiredIds.join(', ')}; ${pendingIds.join(', ')} remain unavailable. No seven-country census total is claimed.`:`Primary census population covers all seven countries. The regional value sums exact national observations for ${Object.entries(normalized.summary.regional_total_component_periods).map(([id,period])=>`${id} ${period}`).join(', ')}; lower-area gaps and discrepancies do not replace those country values.`);
  return result;
}

export function updateCensusPreflight(plan,normalized){
  validateNormalizedCensus(normalized);
  const result=structuredClone(plan),byId=new Map(normalized.countries.map(country=>[country.country_id,country]));
  for(const country of result.countries){
    const acquired=byId.get(country.iso3);if(!acquired)continue;
    country.acquisition_status=`acquired_and_hashed_${acquired.sources.length}_sources`;
    const coded=acquired.territories.filter(area=>area.official_code!=null).length,uncoded=acquired.territories.length-coded;
    country.geography_match_status=`hierarchy_adopted_${coded}_coded_${uncoded}_uncoded_boundaries_not_joined`;
    country.indicator_acceptance_status=`population_accepted_${acquired.observations.length}_observations`;
    country.adapter_audit=acquired.audit;
  }
  result.summary.data_acquired=byId.size;
  result.summary.geographies_matched=0;
  result.summary.indicator_sets_accepted=byId.size;
  result.summary.active_population_observations=normalized.summary.observations_added;
  result.summary.active_territories_added=normalized.summary.territories_added;
  result.summary.regional_total_status=normalized.summary.regional_total_status;
  return result;
}

export function renderCensusAdapterAudit(normalized){
  validateNormalizedCensus(normalized);
  const regional=normalized.summary.countries_pending.length?`Seven-country total: **not available** while ${normalized.summary.countries_pending.join(', ')} remain pending.`:`Seven-country displayed total: **${populationLabel(normalized.summary.regional_total)} people**, calculated from exact national observations with component years ${Object.entries(normalized.summary.regional_total_component_periods).map(([id,period])=>`${id} ${period}`).join(', ')}. Source precision remains in the JSON and exports.`;
  const lines=['# Central America census adapter audit','',`Generated from acquired originals at ${normalized.generated_at}.`,'',`Active population records: ${normalized.summary.observations_added}. Added territories: ${normalized.summary.territories_added}. ${regional}`,''];
  for(const country of normalized.countries){
    lines.push(`## ${country.country_id}`,'',`Period: ${country.period}. Active observations: ${country.observations.length}. Added territories: ${country.territories.length}.`,'');
    const scalarEntries=Object.entries(country.audit).filter(([key,value])=>['number','string'].includes(typeof value)&&!key.endsWith('_note')&&!key.endsWith('_status'));
    lines.push(...scalarEntries.map(([key,value])=>`- ${key.replaceAll('_',' ')}: ${value}`));
    for(const [key,value] of Object.entries(country.audit).filter(([key,value])=>(key.endsWith('_note')||key.endsWith('_status'))&&typeof value==='string'))lines.push(`- ${key.replaceAll('_',' ')}: ${value}`);
    const reconciliations=list(country.audit.department_reconciliation).filter(row=>row.difference!==0);
    if(reconciliations.length)lines.push('',`Published parent/child differences (${reconciliations.length}):`,...reconciliations.map(row=>`- ${row.department||row.district}: parent ${row.department_total??row.general_characteristics_total}; child table ${row.municipality_sum??row.locality_table_total}; difference ${row.difference}.`));
    for(const withheld of list(country.audit.municipal_values_withheld))lines.push(`- Withheld ${withheld.code} ${withheld.name}: published candidate ${withheld.published_population}; ${withheld.reason}.`);
    lines.push('');
  }
  lines.push('Acquisition, indicator acceptance, geography identity and polygon matching are separate checks. Raw source precision remains in observations; display rounding does not change exports.','');return lines.join('\n');
}

import {readFile} from 'node:fs/promises';

export const CENTRAL_AMERICA_CONFIG=JSON.parse(await readFile(new URL('../config/central-america-pilot.json',import.meta.url),'utf8'));

const asMulti=geometry=>geometry?.type==='Polygon'?[geometry.coordinates]:geometry?.type==='MultiPolygon'?geometry.coordinates:[];

export function buildCensusPilotPreflight(catalog,config=CENTRAL_AMERICA_CONFIG) {
  const byId=new Map(catalog.countries.map(country=>[country.iso3,country]));
  const countries=config.member_ids.map(iso3=>{
    const record=byId.get(iso3);
    if(!record)throw new Error(`Census source registry has no pilot country record: ${iso3}`);
    const sourceLocations=record.sources.filter(source=>String(source.role).includes('census'));
    return {iso3,name:record.names[0],registry_status:record.research_status,checked_at:record.checked_at,latest_census_year:record.census.latest_census_year,usable_detailed_year:record.census.usable_detailed_year,published_geography:record.census.published_geography,formats:record.census.formats,caveat:record.census.caveat || null,source_locations:sourceLocations,acquisition_status:'not_acquired_by_this_build',geography_match_status:'not_checked_by_this_build',indicator_acceptance_status:'not_checked_by_this_build'};
  });
  return {schema_version:'1.0',generated_at:new Date().toISOString(),scope_id:config.id,primary_series_family:'census',aggregation_period_policy:'latest_available_by_component',same_year_reference_series:'international_reference',countries,summary:{pilot_countries:countries.length,countries_with_census_source_locations:countries.filter(country=>country.source_locations.length).length,data_acquired:0,geographies_matched:0,indicator_sets_accepted:0},required_actions:['Refresh each official source location and acquire permitted originals with hashes.','Inventory every published table and numeric column before selecting indicators.','Match census geography codes, hierarchy and boundary edition; do not join by names alone.','Record population concept, census date or period, unit, denominator and source year for every accepted observation.','Enable the mixed-period regional census total only after all seven country totals pass compatibility and coverage checks.']};
}

export function renderCensusPilotPreflight(plan) {
  const lines=['# Central America seven-country census source preflight','',`Generated ${plan.generated_at}. Source locations are leads for acquisition; they are not acquired observations.`,'',`Primary series: **${plan.primary_series_family}**. Cross-country census policy: **${plan.aggregation_period_policy}**. Same-year international values remain a separate **${plan.same_year_reference_series}** series.`,'','| Country | Latest census | Detailed year proposed | Registry state | Source locations | Acquisition |','|---|---:|---:|---|---:|---|'];
  for(const country of plan.countries)lines.push(`| ${country.name} (${country.iso3}) | ${country.latest_census_year ?? 'unverified'} | ${country.usable_detailed_year ?? 'unverified'} | ${country.registry_status} | ${country.source_locations.length} | ${country.acquisition_status} |`);
  lines.push('','## Required actions','',...plan.required_actions.map(item=>`- ${item}`),'','A different census year is acceptable when every component year is displayed. It is not a same-year total. Nicaragua, Costa Rica and any other qualified or incomplete census product retain their country-specific caveats; a census label alone does not make the values equivalent.','');
  return lines.join('\n');
}

export function buildRegionalPilot(world,config=CENTRAL_AMERICA_CONFIG) {
  const memberIds=[...config.member_ids];
  if(!memberIds.length||new Set(memberIds).size!==memberIds.length)throw new Error('Regional pilot needs unique country members.');
  const worldTerritories=new Map(world.territories.map(area=>[area.id,area]));
  for(const id of memberIds)if(!worldTerritories.has(id))throw new Error(`Regional pilot country is absent from the world registry: ${id}`);
  const root={id:config.id,name:config.name,level:'national',type:'exploration_scope',parent_id:null,official_code:null,code_system:'AreaData project analysis scope; member identities use UN M49',boundary_version:null,source_id:config.scope_source.id,geography_note:config.scope_note};
  const countries=memberIds.map(id=>({...worldTerritories.get(id),parent_id:config.id}));
  const territories=[root,...countries];
  const comparisons=[{parent_id:config.id,member_ids:memberIds,label:'Seven Central American countries',membership_note:config.scope_note,source_ids:[config.scope_source.id,'un-m49']}];
  const periods=[...new Set(world.observations.map(row=>String(row.period)))];
  const memberSet=new Set(memberIds);
  const observations=world.observations.filter(row=>memberSet.has(row.territory_id)).map(row=>({...row}));
  for(const indicator of world.indicators)for(const period of periods)observations.push({territory_id:root.id,indicator_id:indicator.id,period,value:null,status:'missing',source_id:indicator.source_id,footnote:indicator.id==='SP.POP.TOTL'?'No exact seven-country observation. AreaData may calculate a total only from a complete non-overlapping country cover.':'No exact seven-country observation. Percentages and non-additive measures are not averaged.'});
  const completePeriods={};
  for(const indicator of world.indicators)completePeriods[indicator.id]=[...periods].sort((a,b)=>b.localeCompare(a,'en',{numeric:true})).find(period=>memberIds.every(id=>observations.some(row=>row.territory_id===id&&row.indicator_id===indicator.id&&String(row.period)===period&&row.status==='observed'&&Number.isFinite(row.value)))) || null;
  const sourceFeatures=new Map((world.boundaries?.features||[]).filter(feature=>memberSet.has(feature.properties?.territory_id)).map(feature=>[feature.properties.territory_id,structuredClone(feature)]));
  const features=[...sourceFeatures.values()],mapped=memberIds.filter(id=>sourceFeatures.has(id)),omitted=memberIds.filter(id=>!sourceFeatures.has(id));
  if(mapped.length)features.push({type:'Feature',properties:{territory_id:root.id,name:root.name,source_id:'natural-earth',geometry_edition:world.sources.find(source=>source.id==='natural-earth')?.boundary_version||null,reference_only:true,display_only:true,construction:'Concatenated exact-joined country map units for pilot navigation only; not a legal boundary or numerical aggregation.',mapped_member_ids:mapped,omitted_member_ids:omitted},geometry:{type:'MultiPolygon',coordinates:mapped.flatMap(id=>asMulti(sourceFeatures.get(id).geometry))}});
  const indicators=world.indicators.map(indicator=>indicator.id==='SP.POP.TOTL'?{...indicator,aggregation:'sum',series_family:'international_reference',display_role:'context',period_policy:'same_period'}:{...indicator,aggregation:'official_only',series_family:'international_reference',display_role:'context',period_policy:'same_period'});
  const coverageGaps=indicators.map(indicator=>{
    const rows=observations.filter(row=>memberSet.has(row.territory_id)&&row.indicator_id===indicator.id),observed=rows.filter(row=>row.status==='observed'&&Number.isFinite(row.value)).length,total=memberIds.length*periods.length;
    return {category:'indicator_coverage',status:observed===total?'ready':'partial',detail:`${indicator.name}: ${observed} source-reported country-period values of ${total} possible records for the seven-country, ${periods.length}-period pilot. Missing records remain null.`,next_action:'Acquire or verify a compatible source for each missing country-period; never carry a different year forward.',source_id:indicator.source_id};
  });
  return {
    schema_version:world.schema_version,generated_at:world.generated_at,
    country:{id:config.dataset_id,name:config.name,requested_name:config.name,locale:config.locale,national_territory_id:config.id,geography_note:config.scope_note},territories,
    analysis:{kind:'regional',terminal_territory_ids:[],comparisons,country_sites:[],aggregation:structuredClone(config.aggregation),default_period_by_indicator:completePeriods,pilot:{stage:'central_america_7',country_count:memberIds.length,country_ids:memberIds,scope_source_id:config.scope_source.id,primary_series_family:'census',available_series_families:['international_reference'],census_adapter_status:'not_collected'}},
    indicators,observations,sources:[...world.sources.map(source=>({...source})),structuredClone(config.scope_source)],boundaries:{type:'FeatureCollection',features},documents:[],
    gaps:[...coverageGaps,
      {category:'boundary_reconciliation',status:omitted.length?'partial':'ready',detail:`${mapped.length} of ${memberIds.length} pilot countries have an exact-joined Natural Earth reference map unit; ${omitted.length} remain without a pilot map shape.`,next_action:omitted.length?`Keep ${omitted.join(', ')} in the tables and reconcile an appropriate reference geometry.`:'Retain the map edition and exact join evidence.',source_id:'natural-earth'},
      {category:'regional_aggregation',status:'partial',detail:'Population can be calculated only when all seven countries are covered by compatible, non-overlapping source observations. Other rates and averages remain unavailable without exact regional observations or compatible numerator, denominator or weight series.',next_action:'Expose calculation components and missing countries in every screen and export.',source_id:config.scope_source.id},
      {category:'census_primary_series',status:'not_collected',detail:'AreaData designates official national censuses as the primary diagnostic series. This build contains only international reference series; it is not a completed census dashboard.',next_action:'Acquire each country census table, source year, geography codes and compatible boundaries. Enable mixed-period census aggregation only after all seven country components are verified.',source_id:config.scope_source.id},
      {category:'country_adapters',status:'not_collected',detail:'Country-level international reference series are present. Official census tables, administrative codes, boundaries and planning materials below the country level are not yet integrated for the seven countries.',next_action:'Implement representative country adapters and retain unavailable country or municipal evidence as explicit gaps.',source_id:config.scope_source.id}],
    collection:{status:'partial',adapters:[...world.collection.adapters,'central-america-pilot-transform'],notes:[`Pilot scope: ${memberIds.length} sovereign Central American countries.`,config.scope_note,'Population uses exact country observations as the preferred cover. Missing municipalities below an available country total do not affect a regional calculation. Incomplete country coverage never becomes a claimed total.']}
  };
}

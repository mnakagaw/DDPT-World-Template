const clone=value=>structuredClone(value);

function descendants(dataset,rootId){
  const byId=new Map(dataset.territories.map(area=>[area.id,area]));
  return dataset.territories.filter(area=>{
    if(area.id===rootId)return true;
    const seen=new Set([area.id]);let current=area;
    while(current?.parent_id&&!seen.has(current.parent_id)){
      if(current.parent_id===rootId)return true;
      seen.add(current.parent_id);current=byId.get(current.parent_id);
    }
    return false;
  });
}

const latestPeriod=(dataset,indicatorId,allowed)=>dataset.observations
  .filter(row=>allowed.has(row.territory_id)&&row.indicator_id===indicatorId&&row.status==='observed'&&Number.isFinite(row.value))
  .map(row=>String(row.period)).sort((a,b)=>b.localeCompare(a,'en',{numeric:true}))[0]||null;

/**
 * Create an Americas runtime from the complete World registry. An optional,
 * already validated Central America project can be overlaid without promoting
 * its seven-country evidence to the other countries or to the whole Americas.
 */
export function buildAmericas(world,{centralAmerica=null,unPopulation=null}={}){
  const rootId='M49:019',scope=descendants(world,rootId),scopeIds=new Set(scope.map(area=>area.id));
  if(!scopeIds.has(rootId))throw new Error('World dataset has no UN M49 Americas root (019).');
  const root=scope.find(area=>area.id===rootId);
  const territories=scope.map(area=>area.id===rootId?{...clone(area),level:'national',parent_id:null}:clone(area));
  const indicators=world.indicators.map(clone),observations=world.observations.filter(row=>scopeIds.has(row.territory_id)).map(clone);
  const sources=world.sources.map(clone),sourceIds=new Set(sources.map(source=>source.id));
  const boundaries={type:'FeatureCollection',features:(world.boundaries?.features||[]).filter(feature=>scopeIds.has(feature.properties?.territory_id)).map(clone)};
  const comparisons=world.analysis.comparisons.filter(item=>scopeIds.has(item.parent_id)&&item.member_ids.every(id=>scopeIds.has(id))).map(clone);
  const countryIds=territories.filter(area=>area.type==='country').map(area=>area.id);
  let terminal=world.analysis.terminal_territory_ids.filter(id=>scopeIds.has(id));
  const defaults=Object.fromEntries(indicators.map(indicator=>[indicator.id,latestPeriod(world,indicator.id,scopeIds)]));
  const imported={country_ids:[],territory_count:0,observation_count:0,source:'none'};
  let aggregation;
  let censusHistory;

  if(unPopulation){
    if(unPopulation.scope_id!==rootId||unPopulation.indicator?.id!=='UN_WPP_POP_TOTAL')throw new Error('Americas UN population overlay has an invalid scope or indicator.');
    const registryIds=new Set(unPopulation.summary?.registry_country_ids||[]),availableIds=new Set(unPopulation.summary?.country_ids||[]);
    if(registryIds.size!==countryIds.length||countryIds.some(id=>!registryIds.has(id))||[...availableIds].some(id=>!scopeIds.has(id)))throw new Error('Americas UN population overlay does not match the M49 registry.');
    if(indicators.some(item=>item.id===unPopulation.indicator.id))throw new Error('World dataset unexpectedly already contains the Americas UN population indicator.');
    indicators.push(clone(unPopulation.indicator));sources.push(clone(unPopulation.source));sourceIds.add(unPopulation.source.id);
    observations.push(...unPopulation.observations.map(clone));defaults[unPopulation.indicator.id]=unPopulation.summary.default_display_period;
    aggregation={policy:'exact_then_complete_cover',rules:[{indicator_id:'UN_WPP_POP_TOTAL',method:'sum',completeness:'full_cover',period_policy:'same_period',label:'AreaData calculated UN population context',note:'Sum exact country/area observations only for one UN WPP period and variant, with every non-overlapping member covered. Missing members remain missing; no partial subtotal is presented as the whole region.'}]};
  }

  if(centralAmerica){
    const integrated=centralAmerica.analysis?.pilot?.country_ids||[];
    if(!integrated.length||integrated.some(id=>!scopeIds.has(id)))throw new Error('Central America overlay has countries outside the Americas registry.');
    const countrySet=new Set(integrated),localAreas=centralAmerica.territories.filter(area=>area.id!==centralAmerica.country.national_territory_id&&!countrySet.has(area.id));
    for(const area of localAreas){if(scopeIds.has(area.id))throw new Error(`Central America overlay duplicates territory ${area.id}`);scopeIds.add(area.id);territories.push(clone(area));}
    const importedIndicatorIds=new Set();
    for(const indicator of centralAmerica.indicators)if(!indicators.some(item=>item.id===indicator.id)){indicators.push(clone(indicator));importedIndicatorIds.add(indicator.id);defaults[indicator.id]=centralAmerica.analysis?.default_period_by_indicator?.[indicator.id]||latestPeriod(centralAmerica,indicator.id,new Set(centralAmerica.territories.map(area=>area.id)));}
    const importedRows=centralAmerica.observations.filter(row=>row.territory_id!==centralAmerica.country.national_territory_id&&importedIndicatorIds.has(row.indicator_id));
    const importedCensusRows=importedRows.filter(row=>centralAmerica.indicators.find(indicator=>indicator.id===row.indicator_id)?.series_family==='census');
    observations.push(...importedRows.map(clone));
    for(const source of centralAmerica.sources)if(!sourceIds.has(source.id)){
      const copy=clone(source);
      if(!copy.license){copy.license='Reuse terms not stated in the source publication; raw files are excluded from public redistribution pending terms review.';copy.license_detail='AreaData publishes source-linked factual observations and provenance only. This statement does not assert an open-data license.';}
      sources.push(copy);sourceIds.add(copy.id);
    }
    for(const item of centralAmerica.analysis.comparisons)if(item.parent_id!==centralAmerica.country.national_territory_id)comparisons.push(clone(item));
    const existingBoundaryIds=new Set(boundaries.features.map(feature=>feature.properties?.territory_id));
    for(const feature of centralAmerica.boundaries?.features||[])if(scopeIds.has(feature.properties?.territory_id)&&!existingBoundaryIds.has(feature.properties?.territory_id)){boundaries.features.push(clone(feature));existingBoundaryIds.add(feature.properties?.territory_id);}
    terminal=terminal.filter(id=>!countrySet.has(id));
    terminal.push(...centralAmerica.analysis.terminal_territory_ids.filter(id=>scopeIds.has(id)));
    const centralAggregation=clone(centralAmerica.analysis.aggregation);
    if(!aggregation)aggregation=centralAggregation;
    else for(const rule of centralAggregation?.rules||[])if(!aggregation.rules.some(item=>item.indicator_id===rule.indicator_id))aggregation.rules.push(rule);
    censusHistory=centralAmerica.analysis.census_history?clone(centralAmerica.analysis.census_history):undefined;
    Object.assign(imported,{country_ids:[...integrated],territory_count:localAreas.length,observation_count:importedCensusRows.length,source:'validated_central_america_project'});
  }

  const mappedCountryIds=new Set(boundaries.features.filter(feature=>territories.find(area=>area.id===feature.properties?.territory_id)?.type==='country').map(feature=>feature.properties.territory_id));
  const censusSourceId=indicators.find(indicator=>indicator.id==='CENSUS_POP_TOTAL')?.source_id||'un-m49';
  const gaps=[
    {category:'americas_regional_observation',status:'not_collected',detail:'No exact source-reported observation for the full UN M49 Americas scope has been adopted. Country values remain visible, but they are not silently summed into an Americas value.',next_action:'Acquire an exact-scope official regional series, or approve a complete non-overlapping aggregation rule with every component and period exposed.',source_id:'un-m49'},
    {category:'census_country_coverage',status:imported.country_ids.length===countryIds.length?'ready':'partial',detail:`Official census population and domestic hierarchy are integrated for ${imported.country_ids.length} of ${countryIds.length} UN M49 countries/areas in this Americas scope. Unintegrated does not mean that a census does not exist.`,next_action:'Use the country adapter workflow to inventory official census tables, codes, compatible boundaries and recent census rounds for each remaining country or area.',source_id:censusSourceId},
    {category:'boundary_reconciliation',status:mappedCountryIds.size===countryIds.length?'ready':'partial',detail:`${mappedCountryIds.size} of ${countryIds.length} countries/areas have exact-joined Natural Earth reference map units. Missing shapes stay in the registry and tables.`,next_action:'Reconcile suitable display geometry without name-only joins; do not use the reference map as a legal or statistical boundary.',source_id:'natural-earth'},
    {category:'planning_materials',status:'not_collected',detail:'The Americas exploration scope is not a legal planning authority. Country and local planning laws, plans, budgets and evaluation materials have not been generalized across the region.',next_action:'Collect planning evidence in each country adapter and keep the legal planning unit separate from lower diagnostic geography.',source_id:'un-m49'}
  ];
  if(unPopulation&&unPopulation.summary.missing_country_ids.length)gaps.push({category:'un_wpp_country_area_coverage',status:'partial',detail:`UN WPP 2024 country/area rows are available for ${unPopulation.summary.country_ids.length} of ${countryIds.length} Americas registry entries. Missing: ${unPopulation.summary.missing_country_ids.join(', ')}. These entries remain missing, not zero.`,next_action:'Retain missing status unless a definition-compatible UN source row becomes available; do not use a partial sum as the regional total.',source_id:unPopulation.source.id});
  const adapters=[...new Set([...world.collection.adapters,...(centralAmerica?.collection?.adapters||[]),...(unPopulation?['un-wpp2024-americas-population-v1']:[]),'americas-scope-v1'])];
  const analysis={kind:'regional',terminal_territory_ids:[...new Set(terminal)],comparisons,country_sites:[],default_period_by_indicator:defaults,coverage:{scope:'UN M49 Americas 019',country_area_count:countryIds.length,international_series_country_area_count:countryIds.length,un_wpp_country_area_count:unPopulation?.summary?.country_ids?.length||0,un_wpp_missing_country_area_ids:unPopulation?.summary?.missing_country_ids||countryIds,census_integrated_country_ids:imported.country_ids,census_integrated_territory_count:imported.territory_count,census_integrated_observation_count:imported.observation_count}};
  if(aggregation)analysis.aggregation=aggregation;
  if(censusHistory)analysis.census_history={...censusHistory,catalog_scope_country_ids:countryIds,catalog_status:imported.country_ids.length===countryIds.length?'complete':'partial'};
  return {
    schema_version:world.schema_version,generated_at:world.generated_at,
    country:{id:'AMR',name:'Americas',requested_name:'Americas',locale:'en',national_territory_id:rootId,geography_note:'UN M49 Americas (019), presented through Northern America, South America, and an AreaData navigation group combining UN M49 Central America and Caribbean. The registry contains countries and areas and is not a sovereign-state or legal-planning-authority list.'},
    territories,analysis,indicators,observations,sources,boundaries,documents:[],gaps,
    collection:{status:'partial',adapters,notes:[...world.collection.notes,'The Americas scope contains all 57 UN M49 countries/areas. Missing country or local evidence remains explicit and does not become zero.',...(unPopulation?[`UN WPP 2024 population is integrated for ${unPopulation.summary.country_ids.length} of 57 registry entries; ${unPopulation.summary.missing_country_ids.join(', ')} have no source row and remain missing.`]:[]),'The seven-country Central America evidence is reused at its verified country and domestic geography only; it is not attributed to Mexico, the Caribbean, Northern America, South America or the whole Americas.'],boundary_coverage:(world.collection.boundary_coverage||[]).filter(item=>scopeIds.has(item.territory_id))}
  };
}

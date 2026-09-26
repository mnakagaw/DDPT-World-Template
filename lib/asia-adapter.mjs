const ASIA_ID = 'M49:142';

function descendants(dataset, rootId) {
  const byId = new Map(dataset.territories.map(area => [area.id, area]));
  return dataset.territories.filter(area => {
    let current = area;
    const seen = new Set();
    while (current && !seen.has(current.id)) {
      if (current.id === rootId) return true;
      seen.add(current.id);
      current = byId.get(current.parent_id);
    }
    return false;
  });
}

/** Derive an Asia-only gateway from one already validated, versioned World portfolio. */
export function buildAsia(world) {
  if (world?.analysis?.kind !== 'world' || world.country?.id !== 'WLD') {
    throw new Error('Asia requires a validated AreaData World portfolio');
  }
  const territories = descendants(world, ASIA_ID).map(area => structuredClone(area));
  if (!territories.some(area => area.id === ASIA_ID)) throw new Error('World portfolio has no UN M49 Asia root');
  const ids = new Set(territories.map(area => area.id));
  const countries = territories.filter(area => area.type === 'country');
  const countryIds = new Set(countries.map(area => area.id));
  const observations = world.observations.filter(row => ids.has(row.territory_id)).map(row => structuredClone(row));
  const indicatorIds = new Set(observations.map(row => row.indicator_id));
  for (const id of world.analysis.supranational_indicator_ids || []) indicatorIds.add(id);
  const indicators = world.indicators.filter(row => indicatorIds.has(row.id)).map(row => structuredClone(row));
  const sourcesNeeded = new Set(['un-m49', 'natural-earth']);
  for (const item of [...indicators, ...observations]) if (item.source_id) sourcesNeeded.add(item.source_id);
  const sources = world.sources.filter(row => sourcesNeeded.has(row.id)).map(row => structuredClone(row));
  const boundaries = {type: 'FeatureCollection', features: (world.boundaries?.features || [])
    .filter(feature => ids.has(feature.properties?.territory_id)).map(feature => structuredClone(feature))};
  const comparisons = world.analysis.comparisons
    .filter(item => ids.has(item.parent_id) && item.member_ids.every(id => ids.has(id)))
    .map(item => structuredClone(item));
  const root = territories.find(area => area.id === ASIA_ID);
  root.level = 'national';
  root.parent_id = null;
  const preflight = world.analysis.census_source_preflight;
  const records = (preflight?.records || []).filter(item => countryIds.has(item.country_id));
  const integratedCountryIds = [...new Set(territories
    .filter(area => area.country_id && countryIds.has(area.country_id) && area.id !== area.country_id)
    .map(area => area.country_id))];
  const wppCountryIds = new Set(observations.filter(row => countryIds.has(row.territory_id)
    && row.indicator_id === 'UN_WPP_POP_TOTAL' && row.status === 'observed').map(row => row.territory_id));
  const mappedCountryIds = new Set(boundaries.features
    .filter(feature => countryIds.has(feature.properties?.territory_id))
    .map(feature => feature.properties.territory_id));
  const gaps = [
    {category:'domestic_census_coverage',status:'partial',source_id:'un-m49',
      detail:`Domestic Census data are integrated for ${integratedCountryIds.length} of ${countries.length} UN M49 Asia countries/areas. A missing branch does not mean that no census exists.`,
      next_action:'Acquire, audit and connect country-specific census and local geography without copying national values to local areas.'},
    {category:'boundary_reconciliation',status:mappedCountryIds.size === countries.length ? 'ready' : 'partial',source_id:'natural-earth',
      detail:`${mappedCountryIds.size} of ${countries.length} country/area reference map units have an exact code join. Unmapped entries remain in the registry and tables.`,
      next_action:'Audit display-only geometry and official local boundary correspondence separately.'},
    {category:'planning_materials',status:'not_collected',source_id:'un-m49',
      detail:'UN M49 Asia and its five subregions are statistical exploration areas, not planning authorities. No common planning law or form is inferred.',
      next_action:'Collect planning law, plans, budgets and evaluations in each country adapter.'}
  ];
  const missingWpp = countries.filter(area => !wppCountryIds.has(area.id)).map(area => area.id);
  const populationFor = id => observations.find(row => row.territory_id === id
    && row.indicator_id === 'UN_WPP_POP_TOTAL' && row.period === '2026' && row.status === 'observed')?.value;
  const scopeDifferences = observations.some(row => row.source_id === 'un-wpp2024-global-rev1' && row.period === '2026') ? ['M49:142','M49:030'].map(id => {
    const memberIds = countries.filter(area => id === 'M49:142' || area.parent_id === id).map(area => area.id);
    const sourceValue = populationFor(id);
    const memberValues = memberIds.map(populationFor);
    if (!Number.isFinite(sourceValue) || memberValues.some(value => !Number.isFinite(value)))
      throw new Error(`Cannot verify 2026 WPP source/member scope for ${id}`);
    return {territory_id:id,source_id:'un-wpp2024-global-rev1',
      source_scope:'UN WPP 2024 Rev.1 Asia/Eastern Asia geographic series',
      comparison_scope:'UN M49 Asia country/area registry',
      source_country_area_code_outside_comparison:'158',
      source_country_area_name:'China, Taiwan Province of China',
      source_locator:'WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx, Medium variant, 2026: Asia row 7493; Eastern Asia row 8032; Taiwan row 8340; population column M (thousands)',
      reference_period:'2026',source_value:sourceValue,listed_member_count:memberIds.length,
      listed_member_sum:memberValues.reduce((sum,value)=>sum+value,0),
      difference:sourceValue-memberValues.reduce((sum,value)=>sum+value,0)};
  }) : [];
  if (scopeDifferences.length && (scopeDifferences[1].difference !== 23011292 || Math.abs(scopeDifferences[0].difference-23011292)>2))
    throw new Error('WPP geographic scope changed; verify the Taiwan row before using the Asia adapter');
  if (missingWpp.length) gaps.push({category:'un_wpp_country_area_coverage',status:'partial',source_id:'un-wpp2024-global-rev1',
    detail:`UN WPP population observations are missing for ${missingWpp.join(', ')}. Missing is not zero.`,
    next_action:'Verify an exact official source row before adoption; do not calculate a partial Asia total.'});
  return {
    schema_version:world.schema_version, generated_at:world.generated_at,
    country:{id:'ASI',name:'Asia',requested_name:'Asia',locale:'en',national_territory_id:ASIA_ID,
      geography_note:'UN M49 Asia (142) and its five statistical subregions. Country/area classification does not determine sovereignty, legal borders or planning authority.'},
    territories, indicators, observations, sources, boundaries,
    documents:(world.documents || []).filter(row => ids.has(row.territory_id)).map(row => structuredClone(row)),
    gaps,
    analysis:{kind:'regional',terminal_territory_ids:world.analysis.terminal_territory_ids.filter(id => ids.has(id)),
      source_scope_differences:scopeDifferences,
      comparisons,default_period_by_indicator:Object.fromEntries(Object.entries(world.analysis.default_period_by_indicator || {})
        .filter(([id]) => indicatorIds.has(id))),supranational_indicator_ids:(world.analysis.supranational_indicator_ids || [])
        .filter(id => indicatorIds.has(id)),
      population_pyramids:Object.fromEntries(Object.entries(world.analysis.population_pyramids || {})
        .filter(([key]) => ids.has(key.split('@')[0]))),
      ...(preflight ? {census_source_preflight:{...structuredClone(preflight),records,
        requested_country_ids:countries.map(area => area.id),scope_country_ids:countries.map(area => area.id),
        missing_country_ids:countries.filter(area => !records.some(row => row.country_id === area.id)).map(area => area.id)}} : {}),
      coverage:{scope:'UN M49 Asia 142',country_area_count:countries.length,
        un_wpp_country_area_count:wppCountryIds.size,un_wpp_missing_country_area_ids:missingWpp,
        census_integrated_country_ids:integratedCountryIds}},
    collection:{status:'partial',adapters:[...new Set([...(world.collection?.adapters || []),'asia-scope-v1'])],
      notes:[`All ${countries.length} UN M49 Asia countries/areas are registered; a national international observation is not a completed domestic Census edition.`,
        'Broad-area values use exact international observations or explicitly approved complete-cover calculations only.'],
      boundary_coverage:(world.collection?.boundary_coverage || []).filter(item => ids.has(item.territory_id))}
  };
}

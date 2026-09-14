import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSourceCatalog, findCountrySourceRecord, buildSourcePreflight, renderSourcePreflightMarkdown } from '../lib/source-catalog.mjs';
import { sourcePlan } from '../scripts/source-plan.mjs';

test('source catalog combines reusable international candidates and pre-researched countries', async () => {
  const catalog = await loadSourceCatalog();
  assert.equal(catalog.coverage.common_sources, 10);
  assert.equal(catalog.coverage.country_records, 22);
  assert.deepEqual(catalog.coverage.status_model, [
    'catalogued',
    'country_availability_checked',
    'data_acquired',
    'geography_matched',
    'indicator_accepted',
  ]);
  assert.equal(new Set(catalog.common_sources.map(source => source.id)).size, 10);
  assert.ok(catalog.common_sources.every(source => source.catalog_url.startsWith('https://')));
});

test('Uganda preflight separates planning level, internal analysis geography and acquisition status', async () => {
  const catalog = await loadSourceCatalog();
  const uganda = findCountrySourceRecord(catalog, 'ウガンダ');
  assert.equal(uganda.iso3, 'UGA');
  assert.match(uganda.planning.planning_level, /District/);
  assert.match(uganda.planning.internal_analysis_geography, /Subcounty/);
  const preflight = buildSourcePreflight(catalog, { id: 'UGA', name: 'Uganda' });
  assert.ok(preflight.country_research.sources.some(source => source.role === 'census_catalog'));
  assert.ok(preflight.country_research.sources.some(source => source.role === 'planning_law'));
  assert.ok(preflight.country_research.sources.some(source => source.stage === 'negative_availability_verified'));
  assert.equal(preflight.summary.acquired_sources, 0);
  assert.ok(preflight.common_candidates.every(source => source.country_status === 'availability_not_checked_for_country'));
});

test('Latin America desk research is reused without being promoted to acquired evidence', async () => {
  const catalog = await loadSourceCatalog();
  const dominican = findCountrySourceRecord(catalog, 'DOM');
  assert.equal(dominican.origin_registry, 'latin-america-20-2026');
  assert.equal(dominican.census.latest_census_year, 2022);
  assert.ok(dominican.sources.length >= 4);
  assert.ok(dominican.sources.every(source => source.stage === 'desk_research_location'));
});

test('Belize has a verified 2022 census location without claiming planning research is complete', async () => {
  const catalog = await loadSourceCatalog();
  const belize = findCountrySourceRecord(catalog, 'ベリーズ');
  assert.equal(belize.iso3, 'BLZ');
  assert.equal(belize.census.usable_detailed_year, 2022);
  assert.match(belize.census.published_geography, /city, town, village or community/i);
  assert.match(belize.planning.planning_level, /Not yet researched/);
  assert.ok(belize.sources.every(source => source.publisher === 'Statistical Institute of Belize'));
});

test('unresearched country still receives common candidates and an explicit research task', async () => {
  const catalog = await loadSourceCatalog();
  const preflight = buildSourcePreflight(catalog, { id: 'JPN', name: 'Japan' });
  assert.equal(preflight.country_research.status, 'source_locations_not_pre_researched');
  assert.equal(preflight.country_research.sources.length, 0);
  assert.equal(preflight.common_candidates.length, 10);
  assert.match(preflight.required_actions[0], /Locate and verify/);
  assert.match(renderSourcePreflightMarkdown(preflight), /does not mean the listed data were acquired/);
});

test('source plan can narrow common candidates by theme without implying country availability', async () => {
  const json = JSON.parse(await sourcePlan({ country: 'UGA', theme: 'refugees', format: 'json' }));
  assert.deepEqual(json.common_candidates.map(source => source.id), ['unhcr-refugee-data-finder']);
  assert.equal(json.common_candidates[0].country_status, 'availability_not_checked_for_country');
  await assert.rejects(sourcePlan({ country: 'Japan', format: 'json' }), /unresearched country must be specified by ISO3/);
});

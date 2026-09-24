import path from 'node:path';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, copyFile, lstat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { validateDataset } from '../../lib/validate.mjs';
import { parseArgs, isMain, reportError } from '../../lib/cli.mjs';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const here = path.dirname(fileURLToPath(import.meta.url));
const templateRoot = path.resolve(here, '../..');
const gitOutput = args => { try { return execFileSync('git', args, { cwd: templateRoot, encoding: 'utf8' }).trim(); } catch { return null; } };
const inputFiles = ['geography-statistics.json', 'resources.json', 'boundaries-region.geojson', 'boundaries-subregion.geojson', 'boundaries.geojson', 'boundaries-subcounty.geojson'];
const areaId = id => id === 'all-uganda' ? 'UGA' : `UGA:${id}`;
const safeHttps = url => { try { return new URL(url).protocol === 'https:'; } catch { return false; } };

/** Adapt the vetted Uganda-LGDP normalized census to the AreaData schema. */
export async function importUganda({ source, out }) {
  if (!source || !out) throw new Error('Provide --source <Uganda-LGDP/public/data> --out <new project>');
  const from = path.resolve(source), target = path.resolve(out);
  if (await lstat(target).catch(error => error.code === 'ENOENT' ? null : Promise.reject(error))) throw new Error(`Output already exists: ${target}`);
  const bytes = new Map();
  for (const name of inputFiles) bytes.set(name, await readFile(path.join(from, name)));
  const geo = JSON.parse(bytes.get('geography-statistics.json'));
  const resources = JSON.parse(bytes.get('resources.json'));
  const checkedAt = new Date().toISOString();
  const sources = [
    { id: 'uga-lgdp-census-normalized', name: 'UBOS NPHC 2024 subcounty profiles — Uganda-LGDP normalized extraction', url: geo.source.landingUrl, publisher: geo.source.publisher, status: 'ready', retrieved_at: checkedAt, reference_period: '2024', raw_path: 'raw/geography-statistics.json', sha256: sha256(bytes.get('geography-statistics.json')), license: null, note: `This hash identifies the copied normalized artifact. Its upstream UBOS workbook SHA-256 is ${geo.source.sha256}; original workbook was not contained in the Uganda-LGDP source checkout. Cell locators and derived numerators/denominators are retained per observation.` },
    { id: 'uga-lgdp-boundaries', name: 'UBOS NPHC 2024 portal reference geography, normalized by Uganda-LGDP', url: 'https://statistics.ubos.org/nphc/drilldown', publisher: 'Uganda Bureau of Statistics', status: 'ready', retrieved_at: checkedAt, reference_period: '2024', raw_path: 'raw/boundaries.geojson', sha256: sha256(bytes.get('boundaries.geojson')), license: null, note: 'Upper areas are visual unions of verified district/city shapes; lower features use separately matched source units. These are reference shapes, not legal boundaries.' },
    { id: 'uga-ubos-volume1-a7', name: 'UBOS NPHC 2024 Final Report Volume 1, Appendix A7', url: 'https://statistics.ubos.org/nphc/reports/National-Population-and-Housing-Census-2024-Final-Report-Volume-1-Main.pdf', publisher: 'Uganda Bureau of Statistics', status: 'partial', retrieved_at: checkedAt, reference_period: '2024', license: null, note: 'Refugee/asylum-seeker census counts were previously source-checked in Uganda-LGDP. PDF body is retained in that origin project, not copied here.' },
  ];
  for (const row of resources.sources || []) if (safeHttps(row.url) && !sources.some(source => source.id === `uga-plan-${row.id}`)) {
    sources.push({ id: `uga-plan-${row.id}`, name: row.title || row.id, url: row.url, publisher: row.publisher || 'Uganda National Planning Authority', status: row.sha256 ? 'ready' : 'partial', retrieved_at: row.fetchedAt || checkedAt, reference_period: row.period || null, license: null, note: row.usage || row.verificationStatus || '' });
  }
  const sourceById = new Map(sources.map(source => [source.id, source]));
  const territories = [{ id: 'UGA', name: 'Uganda', level: 'national', type: 'country', parent_id: null, official_code: 'UG', code_system: 'ISO 3166-1 alpha-2', source_id: 'uga-lgdp-census-normalized' }];
  const levels = [ ['region', 'region'], ['subregion', 'subregion'], ['district', 'district'], ['subcounty', 'subcounty'] ];
  const areas = [];
  for (const [key, level] of levels) for (const area of geo.levels[key].areas) {
    territories.push({ id: areaId(area.id), name: area.name, level, type: area.type || level, parent_id: areaId(area.parentId), official_code: area.code || null, code_system: area.code ? 'UBOS NPHC 2024 district/city code' : null, boundary_version: 'UBOS NPHC 2024 portal geography, exact issue date unstated', source_id: 'uga-lgdp-census-normalized', provider_id: area.id, region_name: area.region || null, subregion_name: area.subregion || null });
    areas.push(area);
  }
  const indicatorSource = indicator => indicator.sourceId === 'ubos-nphc2024-volume1-a7' ? 'uga-ubos-volume1-a7' : 'uga-lgdp-census-normalized';
  const indicators = geo.indicators.map(indicator => ({
    id: indicator.id, name: indicator.label, theme: indicator.theme || 'Other', unit: indicator.unit || 'unit not recorded', definition: indicator.definition || indicator.label,
    ...(indicator.universe ? { population: indicator.universe } : {}), source_id: indicatorSource(indicator), aggregation: 'none', measurement_method: indicator.calculation || 'UBOS census source value', series_family: 'census', display_role: 'primary', period_policy: 'source_year',
    upstream_source_id: indicator.sourceId, upstream_table: indicator.sheet || null, upstream_column: indicator.column || null,
  }));
  const observations = [];
  const addObservations = (id, values) => {
    for (const indicator of geo.indicators) {
      const cell = values?.[indicator.id];
      if (!cell) continue;
      const observed = Number.isFinite(cell.value);
      observations.push({ territory_id: id, indicator_id: indicator.id, period: '2024', value: observed ? cell.value : null, status: observed ? 'observed' : 'missing', source_id: indicatorSource(indicator), upstream_status: cell.status || null, source_locator: cell.reference || null, numerator: Number.isFinite(cell.numerator) ? cell.numerator : null, denominator: Number.isFinite(cell.denominator) ? cell.denominator : null, ...(cell.method ? { method: cell.method } : {}), coverage: cell.coverage || null, missing_reason: observed ? null : cell.reason || null });
    }
  };
  addObservations('UGA', geo.officialNational.observations);
  for (const area of areas) addObservations(areaId(area.id), area.values);
  const boundaries = { type: 'FeatureCollection', features: [] };
  const knownTerritoryIds = new Set(territories.map(area => area.id));
  let unjoinedBoundaryFeatures = 0;
  for (const name of inputFiles.filter(name => name.endsWith('.geojson'))) {
    const featureCollection = JSON.parse(bytes.get(name));
    for (const feature of featureCollection.features) {
      if (!['Polygon', 'MultiPolygon'].includes(feature.geometry?.type)) continue;
      if (!knownTerritoryIds.has(areaId(feature.properties.territoryId))) { unjoinedBoundaryFeatures++; continue; }
      boundaries.features.push({ type: 'Feature', properties: { ...feature.properties, territory_id: areaId(feature.properties.territoryId), source_id: 'uga-lgdp-boundaries', original_id: feature.properties.territoryId }, geometry: feature.geometry });
    }
  }
  const districtByName = new Map(areas.filter(area => area.type === 'district' || area.type === 'city').map(area => [area.name.toLowerCase(), areaId(area.id)]));
  const documents = [];
  for (const plan of resources.plans || []) {
    if (!safeHttps(plan.url) || !sourceById.has(`uga-plan-${plan.sourceId}`)) continue;
    const territoryId = districtByName.get(String(plan.districtName || '').toLowerCase());
    if (!territoryId) continue;
    documents.push({ id: `uga-${plan.id}`, territory_id: territoryId, title: plan.title, url: plan.url, source_id: `uga-plan-${plan.sourceId}`, category: 'plan', period: plan.period || 'period not verified', availability: 'link_verified', official_status: 'unverified', note: `Origin acquisition: ${plan.verificationStatus || plan.version || 'unknown'}; original PDF not copied into this AreaData adapter.` });
  }
  const dataset = {
    schema_version: '0.2', generated_at: checkedAt,
    country: { id: 'UGA', iso2: 'UG', name: 'Uganda', requested_name: 'ウガンダ', locale: 'en', national_territory_id: 'UGA', geography_note: '2024 UBOS national count, four regions, 17 subregions, 146 district/city profiles and 2,207 subcounty-equivalent units. The national record includes APAA, while district/city profile totals exclude it. No parent is inferred by summing incomplete children.' },
    territories, indicators, observations, population_pyramids: [], sources, boundaries, documents,
    planning: { title: 'Planning materials', purpose: 'Use the selected area’s census evidence and verified planning references to prepare local-government development planning material.', sections: [ { id: 'plan', label: 'Plans', empty_message: 'No area-specific plan was acquired.' }, { id: 'budget', label: 'Budgets', empty_message: 'No area-specific budget was acquired.' }, { id: 'implementation', label: 'Implementation reports', empty_message: 'No area-specific implementation report was acquired.' }, { id: 'evaluation', label: 'Evaluations', empty_message: 'No area-specific official evaluation was acquired.' }, { id: 'reference', label: 'Census and planning references', empty_message: 'No additional reference was acquired.' } ], system: { label: 'Uganda Local Government Development Planning', scope: 'District/city local governments integrate lower local-government plans. Subcounty-level census data support internal diagnosis and do not automatically make subcounties the statutory plan authority.', cycle: 'Use the planning period stated in each plan; the current NDP IV period is 2025/26–2029/30.', source_ids: sources.filter(source => source.id.startsWith('uga-plan-')).slice(0, 2).map(source => source.id) }, outputs: ['markdown', 'html', 'evidence_csv', 'documents_csv'] },
    gaps: [
      { category: 'geography', status: 'partial', detail: `${geo.levels.subcounty.areas.length - boundaries.features.filter(feature => feature.properties.adminType === 'subcounty-equivalent').length} subcounty-equivalent units lack verified reference polygons. Numeric rows remain in the register.`, next_action: 'Resolve only against an official code/boundary edition; do not infer a match from names.' },
      { category: 'geography', status: 'partial', detail: `${unjoinedBoundaryFeatures} supplied boundary features lack a matching source-area ID in this adopted census register and are not displayed.`, next_action: 'Review the source crosswalk and do not assign a polygon by name alone.' },
      { category: 'planning', status: 'partial', detail: 'Area-specific plans, budgets, implementation reports and official evaluations are only partially acquired in the origin project.', next_action: 'Inventory and inspect each current district/city planning source before claiming a completed local plan materials edition.' },
      { category: 'source', status: 'partial', detail: 'The original UBOS workbook and report PDFs were not present in the source checkout used for this adapter. The copied normalized extraction retains source locators and upstream SHA-256.', next_action: 'Acquire the exact official originals and verify their hashes and extraction cells before independent acceptance.' },
    ],
    analysis: { kind: 'country', default_indicator_id: 'population', latest_values_only: true, terminal_territory_ids: [], comparisons: [] },
    collection: { status: 'partial', acquired_at: checkedAt, note: 'Imported the source-checked Uganda-LGDP normalized 2024 UBOS regional, district and subcounty census profile data. Planning source coverage and original raw-file republication remain partial.' },
  };
  const result = validateDataset(dataset);
  if (result.errors.length) throw new Error(`Uganda adapter rejected: ${result.errors.slice(0, 12).join('; ')}`);
  await mkdir(path.join(target, 'data'), { recursive: true });
  await mkdir(path.join(target, 'raw'), { recursive: true });
  await mkdir(path.join(target, 'evidence'), { recursive: true });
  for (const name of inputFiles) await copyFile(path.join(from, name), path.join(target, 'raw', name));
  await writeFile(path.join(target, 'data', 'dashboard.json'), JSON.stringify(dataset));
  await writeFile(path.join(target, 'evidence', 'IMPORT_ORIGIN.json'), JSON.stringify({ imported_at: checkedAt, origin: from, source_files: inputFiles.map(name => ({ name, sha256: sha256(bytes.get(name)), bytes: bytes.get(name).length })), template_commit: gitOutput(['rev-parse', 'HEAD']), template_dirty: Boolean(gitOutput(['status', '--porcelain'])), warnings: result.warnings, limitations: geo.limitations, independent_areadata_audit: 'pending' }, null, 2) + '\n');
  await writeFile(path.join(target, 'HANDOFF.md'), `# Uganda AreaData handoff\n\nImported Uganda-LGDP's normalized UBOS NPHC 2024 records into a separate AreaData schema-0.2 project. The original project was not modified. Source-file hashes and limitations are in evidence/IMPORT_ORIGIN.json; copied normalized source files are in raw/. National UBOS figures include APAA and differ from the 146 district/city profile scope. No child total is silently substituted.\n\nRun \`node scripts/validate-country.mjs --project ${target}\` then \`node scripts/build-country.mjs --project ${target}\`. Review national, region, subregion, district and subcounty views, thematic comparisons, planning links and exports. This adaptation requires an independent AreaData audit before publication.\n`);
  return { target, territories: territories.length, indicators: indicators.length, observations: observations.length, boundaries: boundaries.features.length, documents: documents.length, warnings: result.warnings.length };
}

if (isMain(import.meta.url)) {
  try { console.log(JSON.stringify(await importUganda(parseArgs(process.argv.slice(2), ['source', 'out'])), null, 2)); }
  catch (error) { reportError(error); }
}

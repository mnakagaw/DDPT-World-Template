#!/usr/bin/env node
import {readFile, mkdir, writeFile, stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {validateDataset} from '../../lib/validate.mjs';
import {generateSite} from '../../lib/generate.mjs';

const value = flag => {
  const index = process.argv.indexOf(flag);
  return index < 0 ? undefined : process.argv[index + 1];
};
const worldPath = value('--world');
const countryPath = value('--country');
const outArg = value('--out');
if (!worldPath || !countryPath || !outArg) throw new Error('Use --world canonical-world.json --country BFA-dashboard.json --out new-directory');
const out = path.resolve(outArg);
try { await stat(out); throw new Error(`Output already exists: ${out}`); } catch (error) { if (error.code !== 'ENOENT') throw error; }
const [world, country] = await Promise.all([worldPath, countryPath].map(async file => JSON.parse(await readFile(path.resolve(file), 'utf8'))));
if (world.country?.id !== 'WLD' || world.analysis?.kind !== 'world') throw new Error('Expected the canonical AreaData world dataset');
if (country.country?.id !== 'BFA' || country.analysis?.kind !== 'country') throw new Error('Expected the reviewed Burkina Faso country dataset');
const bfaRoot = world.territories.find(area => area.id === 'BFA' && area.type === 'country');
if (!bfaRoot || world.territories.some(area => area.country_id === 'BFA' && area.id !== 'BFA')) throw new Error('World BFA identity missing or country branch already integrated');
const existingTerritories = new Set(world.territories.map(area => area.id));
const local = country.territories.filter(area => area.id !== 'BFA').map(area => ({...area, country_id: 'BFA'}));
if (local.length !== 409 || local.some(area => existingTerritories.has(area.id))) throw new Error('Expected 409 distinct historical BFA descendants');
const localIds = new Set(local.map(area => area.id));
const worldIndicators = new Set(world.indicators.map(indicator => indicator.id));
const indicators = country.indicators.filter(indicator => !worldIndicators.has(indicator.id));
const indicatorIds = new Set(indicators.map(indicator => indicator.id));
const worldSources = new Set(world.sources.map(source => source.id));
const sources = country.sources.filter(source => !worldSources.has(source.id)).map(source =>
  source.geographic_level === 'national' && !source.country_id ? {...source, country_id: 'BFA'} : source);
const observations = country.observations.filter(row => indicatorIds.has(row.indicator_id));
if (observations.some(row => row.territory_id !== 'BFA' && !localIds.has(row.territory_id))) throw new Error('Unmatched BFA observation territory');
const boundaries = country.boundaries.features.filter(feature => localIds.has(feature.properties?.territory_id));
const documents = country.documents || [];
const sourceIds = new Set([...world.sources, ...sources].map(source => source.id));
if (indicators.some(indicator => !sourceIds.has(indicator.source_id)) || observations.some(row => !sourceIds.has(row.source_id)) || documents.some(row => !sourceIds.has(row.source_id))) throw new Error('Unmatched source ID');
const directChildren = new Map();
for (const area of local) {
  if (!directChildren.has(area.parent_id)) directChildren.set(area.parent_id, []);
  directChildren.get(area.parent_id).push(area.id);
}
const comparisons = [...directChildren].map(([parent_id, member_ids]) => ({
  parent_id, member_ids, label: `${member_ids.length} historical 2019 Census areas`,
  membership_note: 'INSD RGPH 2019 locality register; 2017 provider boundaries are reference shapes and do not certify present legal boundaries or 2025 administrative units.',
  source_ids: ['bfa-insd-rgph2019-localities'],
}));
const terminals = local.filter(area => !directChildren.has(area.id)).map(area => area.id);
const dataset = structuredClone(world);
dataset.generated_at = new Date().toISOString();
dataset.territories.push(...local);
dataset.indicators.push(...indicators);
dataset.sources.push(...sources);
dataset.observations.push(...observations);
dataset.boundaries.features.push(...boundaries);
dataset.documents.push(...documents);
dataset.analysis.comparisons.push(...comparisons);
dataset.analysis.terminal_territory_ids = [...new Set([...dataset.analysis.terminal_territory_ids.filter(id => id !== 'BFA'), ...terminals])];
dataset.analysis.census_population_pyramids = {...(dataset.analysis.census_population_pyramids || {}), ...(country.analysis.census_population_pyramids || {})};
dataset.analysis.default_period_by_indicator = {...dataset.analysis.default_period_by_indicator};
for (const indicator of indicators) {
  const periods = observations.filter(row => row.indicator_id === indicator.id).map(row => row.period).sort();
  if (periods.length) dataset.analysis.default_period_by_indicator[indicator.id] = periods.at(-1);
}
dataset.analysis.coverage.census_integrated_country_ids = [...new Set([...(dataset.analysis.coverage.census_integrated_country_ids || []), 'BFA'])].sort();
dataset.collection.adapters = [...new Set([...dataset.collection.adapters, 'bfa-rgph2019-country-depth'])];
dataset.collection.notes.push('Burkina Faso country depth uses the INSD 2019 13-region/45-province/351-commune Census register. Its 2017 reference shapes and 2025 administrative reform are distinct; unverified present-day plan/budget records are not asserted.');
const validation = validateDataset(dataset);
if (validation.errors.length) throw new Error(`World integration validation: ${validation.errors.slice(0, 20).join('; ')}`);
await mkdir(path.join(out, 'data'), {recursive: true});
await mkdir(path.join(out, 'evidence'), {recursive: true});
const content = JSON.stringify(dataset) + '\n';
const datasetSha256 = createHash('sha256').update(content).digest('hex');
await writeFile(path.join(out, 'data/dashboard.json'), content);
await writeFile(path.join(out, 'evidence/validation.json'), JSON.stringify({...validation, dataset_sha256: datasetSha256, checked_at: new Date().toISOString()}, null, 2) + '\n');
await generateSite({dataset, outDir: out, canonicalSha256: datasetSha256});
await writeFile(path.join(out, 'evidence/BFA_WORLD_INTEGRATION.json'), JSON.stringify({
  world_source: path.resolve(worldPath), country_source: path.resolve(countryPath), dataset_sha256: datasetSha256,
  country_area_id: 'BFA', local_territories: local.length, indicators: indicators.length,
  observations: observations.length, reference_boundaries: boundaries.length,
  documents: documents.length, comparisons: comparisons.length, terminal_areas: terminals.length,
  validation_errors: validation.errors.length, validation_warnings: validation.warnings.length,
  source_conflict: 'INSD Table II.10 fertility values are withheld pending reconciliation with the final report.',
}, null, 2) + '\n');
console.log(JSON.stringify({out, dataset_sha256: datasetSha256, local_territories: local.length, indicators: indicators.length, observations: observations.length, validation_errors: 0}));

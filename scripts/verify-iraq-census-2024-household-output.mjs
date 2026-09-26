#!/usr/bin/env node
// Inspect actual country exports, including every governorate row of six new fields.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

function csvRows(value) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let i = value.charCodeAt(0) === 0xfeff ? 1 : 0; i < value.length; i++) {
    const c = value[i];
    if (quoted) {
      if (c === '"' && value[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { row.push(cell.replace(/\r$/, '')); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (quoted) throw new Error('Unterminated CSV quote');
  if (row.length || cell) rows.push([...row, cell]);
  return rows.filter(row => row.some(cell => cell !== ''));
}

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const arg = process.argv.indexOf('--project');
if (arg < 0 || !process.argv[arg + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-iraq-census-2024-household-output.mjs --project <new-project>');
}
const project = path.resolve(process.argv[arg + 1]);
const datasetBytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(datasetBytes.toString('utf8'));
if (dataset.country.id !== 'IRQ') throw new Error('Expected Iraq dataset');
const sourceById = new Map(dataset.sources.map(source => [source.id, source]));
const specs = [
  ['ELEC_RESPONDING_HH', 7757742, 1672741, 368007],
  ['ELEC_PUBLIC_GRID_HH', 7634417, 1629691, 362269],
  ['ELEC_PUBLIC_GRID_PCT', 98.41, 97.43, 98.44],
  ['WATER_HH_TOTAL', 8054385, 1783021, 378179],
  ['WATER_PIPED_IN_HOME_HH', 6734842, 1545712, 269437],
  ['WATER_PIPED_IN_HOME_PCT', 83.6, 86.7, 71.2],
];
const allGovernors = dataset.territories.filter(territory => territory.parent_id === 'IRQ');
if (allGovernors.length !== 18) throw new Error('Governorate roster changed');
const areas = ['Iraq', 'Baghdad', 'Dhi Qar'].map(name => {
  const matches = dataset.territories.filter(territory => territory.name === name);
  if (matches.length !== 1) throw new Error(`Missing or ambiguous area ${name}`);
  return matches[0];
});
const checks = [];
const out = path.join(project, 'evidence/output-verification-households');
await mkdir(out, {recursive: true});
for (let areaIndex = 0; areaIndex < areas.length; areaIndex++) {
  const area = areas[areaIndex];
  const exports = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, contents] of Object.entries(exports)) {
    await writeFile(path.join(out, `${area.name.replaceAll(' ', '_')}-${suffix}`), contents);
  }
  const [heading, ...rows] = csvRows(exports['diagnostic.csv']);
  const col = name => {
    const index = heading.indexOf(name);
    if (index < 0) throw new Error(`Missing CSV column ${name}`);
    return index;
  };
  for (const [suffix, ...expected] of specs) {
    const indicatorId = `IRQ_CENSUS_2024_HH_${suffix}`;
    const indicator = dataset.indicators.find(item => item.id === indicatorId);
    const actual = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === indicatorId);
    if (actual.length !== 1 || Number(actual[0][col('Value')]) !== expected[areaIndex] ||
        actual[0][col('Period')] !== '2024' || actual[0][col('Status')] !== 'observed') {
      throw new Error(`${area.name}/${suffix}: overall export differs from source`);
    }
    const source = sourceById.get(indicator.source_id);
    if (!source || actual[0][col('Source URL')] !== source.url || !source.url.startsWith('https://cosit.gov.iq/')) {
      throw new Error(`${area.name}/${suffix}: source attribution mismatch`);
    }
    const children = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === indicatorId);
    if (children.length !== (areaIndex === 0 ? 18 : 0)) throw new Error(`${area.name}/${suffix}: internal row count mismatch`);
    if (areaIndex === 0) {
      for (const governor of allGovernors) {
        const published = dataset.observations.find(item => item.territory_id === governor.id && item.indicator_id === indicatorId);
        const exported = children.find(row => row[col('Territory ID')] === governor.id);
        if (!published || !exported || Number(exported[col('Value')]) !== published.value ||
            exported[col('Period')] !== '2024' || exported[col('Source URL')] !== source.url) {
          throw new Error(`${governor.name}/${suffix}: internal export mismatch`);
        }
      }
    }
  }
  if (!exports['diagnostic.html'].includes(area.name) || !exports['planning.html'].includes(area.name) ||
      !exports['evidence.csv'].includes(area.name)) throw new Error(`${area.name}: output area mismatch`);
  checks.push({area: area.name, territory_id: area.id, household_indicators: specs.length,
    complete_governorate_rows_per_indicator: areaIndex === 0 ? 18 : 0, csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    export_sha256: Object.fromEntries(Object.entries(exports).map(([kind, contents]) => [kind, digest(contents)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: digest(datasetBytes), source_pdf_sha256: Object.fromEntries(
    ['irq-cosit-census-2024-electricity-pdf', 'irq-cosit-census-2024-home-water-pdf']
      .map(id => [id, sourceById.get(id)?.sha256])), checks,
  limitations: ['No verified Iraqi planning document adopted',
    'Official 2024 boundary and administrative-code equivalence not established',
    'This is not an independent acceptance audit']};
await writeFile(path.join(project, 'evidence/OUTPUT_VERIFICATION_HOUSEHOLDS.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, csv_rows: item.csv_rows,
  household_indicators: item.household_indicators,
  complete_governorate_rows_per_indicator: item.complete_governorate_rows_per_indicator})), null, 2));

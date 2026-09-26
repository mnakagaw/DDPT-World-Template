#!/usr/bin/env node
// Check source values, selected-area exports and complete national comparison rows.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const option = process.argv.indexOf('--project');
if (option < 0 || !process.argv[option + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-jordan-population-output.mjs --project <project>');
}
const project = path.resolve(process.argv[option + 1]);
const datasetBytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(datasetBytes.toString('utf8'));
if (dataset.country.id !== 'JOR') throw new Error('Expected Jordan project');
const source = dataset.sources.find(item => item.id === 'jor-dos-population-estimates-end-2025');
const hash = input => createHash('sha256').update(input).digest('hex');
if (!source || source.sha256 !== '659587a2f4a243c912835720073c76974dd64bdb44dbab0411238cf425deacce') {
  throw new Error('DoS PDF source changed');
}
if (hash(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('DoS PDF bytes changed');
}
const ids = ['JOR_DOS_EST_2025_POP', 'JOR_DOS_EST_2025_FEMALE', 'JOR_DOS_EST_2025_MALE',
  'JOR_DOS_EST_2025_RURAL', 'JOR_DOS_EST_2025_URBAN'];
const expected = {
  Jordan: [11937000, 5617100, 6319900, 1152300, 10784700],
  Amman: [5004600, 2315600, 2689000, 139300, 4865300],
  Ajloun: [219900, 106600, 113300, 35400, 184500],
  Tafilah: [120300, 57300, 63000, 26500, 93800],
};
const children = dataset.territories.filter(item => item.parent_id === 'JOR');
if (children.length !== 12 || new Set(children.map(item => item.source_name_en)).size !== 12) {
  throw new Error('The 12-governorate source crosswalk is incomplete');
}
for (const id of ids) {
  const observations = dataset.observations.filter(item => item.indicator_id === id);
  if (observations.length !== 13 || observations.some(item => item.period !== '2025' ||
    item.source_id !== source.id || item.status !== 'observed')) {
    throw new Error(`Wrong adopted observation coverage: ${id}`);
  }
  if (observations.filter(item => item.territory_id !== 'JOR').reduce((sum, item) => sum + item.value, 0) !==
    observations.find(item => item.territory_id === 'JOR').value) {
    throw new Error(`The 12 governorate totals do not equal printed national value: ${id}`);
  }
}
function rowsOf(csv) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let i = csv.charCodeAt(0) === 0xfeff ? 1 : 0; i < csv.length; i++) {
    const c = csv[i];
    if (quoted) {
      if (c === '"' && csv[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { rows.push([...row, cell.replace(/\r$/, '')]); row = []; cell = ''; }
    else cell += c;
  }
  if (row.length || cell) rows.push([...row, cell]);
  return rows.filter(row => row.some(value => value !== ''));
}
const out = path.join(project, 'evidence/output-verification');
await mkdir(out, {recursive: true});
const checks = [];
for (const [name, values] of Object.entries(expected)) {
  const area = dataset.territories.find(item => item.name === name);
  if (!area) throw new Error(`Missing area ${name}`);
  const exports = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, contents] of Object.entries(exports)) {
    await writeFile(path.join(out, `${name}-${suffix}`), contents);
  }
  const [head, ...rows] = rowsOf(exports['diagnostic.csv']);
  const col = key => {
    const index = head.indexOf(key);
    if (index < 0) throw new Error(`Missing export column ${key}`);
    return index;
  };
  for (let index = 0; index < ids.length; index++) {
    const overall = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === ids[index]);
    if (overall.length !== 1 || Number(overall[0][col('Value')]) !== values[index] ||
      overall[0][col('Period')] !== '2025' || overall[0][col('Status')] !== 'observed' ||
      overall[0][col('Source URL')] !== source.url) {
      throw new Error(`Area export differs from DoS PDF: ${name}/${ids[index]}`);
    }
    const within = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === ids[index]);
    if (within.length !== (name === 'Jordan' ? 12 : 0)) {
      throw new Error(`Wrong comparison row count: ${name}/${ids[index]}`);
    }
    if (name === 'Jordan') for (const child of children) {
      const datum = dataset.observations.find(item => item.territory_id === child.id && item.indicator_id === ids[index]);
      const exported = within.find(row => row[col('Territory ID')] === child.id);
      if (!datum || !exported || Number(exported[col('Value')]) !== datum.value ||
        exported[col('Source URL')] !== source.url) {
        throw new Error(`Country comparison changed: ${child.name}/${ids[index]}`);
      }
    }
  }
  if (!exports['diagnostic.html'].includes(name) || !exports['planning.html'].includes(name) ||
      !exports['evidence.csv'].includes(name)) throw new Error(`Area missing from generated output: ${name}`);
  checks.push({area: name, territory_id: area.id, values,
    diagnostic_csv_rows: rows.length, comparison_rows_per_indicator: name === 'Jordan' ? 12 : 0,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    export_sha256: Object.fromEntries(Object.entries(exports).map(([kind, contents]) => [kind, hash(contents)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: hash(datasetBytes), source_pdf_sha256: source.sha256, checks,
  limitations: ['Official 2025 governorate boundary and code crosswalk remains unverified',
    '2015 census and 2025 district/age/area tables remain unadopted',
    'Actual local plans, budgets, execution and independent acceptance remain unverified']};
await writeFile(path.join(project, 'evidence/JOR_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, values: item.values,
  diagnostic_csv_rows: item.diagnostic_csv_rows,
  comparison_rows_per_indicator: item.comparison_rows_per_indicator})), null, 2));

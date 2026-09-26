#!/usr/bin/env node
// Inspect rendered/downloadable output for the limited CBS district adoption.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-israel-cbs-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
if (dataset.country.id !== 'ISR') throw new Error('Expected Israel candidate');
const sha = input => createHash('sha256').update(input).digest('hex');
const source = dataset.sources.find(item => item.id === 'isr-cbs-census-2022-broad-geographical');
if (!source || sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('CBS acquired original/hash changed');
}
const ids = dataset.indicators.filter(item => item.id.startsWith('ISR_CBS_2022_')).map(item => item.id);
if (ids.length !== 12) throw new Error('Expected twelve adopted CBS fields');
const inventory = csvRows(await readFile(path.join(project, 'evidence/ISR_CBS_COLUMN_INVENTORY.csv'), 'utf8'));
const [inventoryHeader, ...inventoryRows] = inventory;
const inventoryIndex = key => inventoryHeader.indexOf(key);
const adoptedInventory = inventoryRows.filter(row => row[inventoryIndex('decision')] === 'adopted_country_six_districts');
if (adoptedInventory.length !== 12 ||
    adoptedInventory.some(row => row[inventoryIndex('sheet')] !== 'District Sub-District Natural  ')) {
  throw new Error('CBS column inventory/adoption disposition changed');
}
const children = dataset.territories.filter(item => item.parent_id === 'ISR');
if (children.length !== 6 || children.some(item => !item.reconciliation_status?.includes('boundary_unverified'))) {
  throw new Error('Six provider district matches changed');
}
for (const id of ids) {
  const found = dataset.observations.filter(item => item.indicator_id === id);
  if (found.length !== 7 || found.some(item => item.period !== '2022' || item.source_id !== source.id)) {
    throw new Error(`CBS field coverage changed: ${id}`);
  }
}
const population = dataset.observations.filter(item => item.indicator_id === 'ISR_CBS_2022_POP');
if (population.find(item => item.territory_id === 'ISR')?.value !== 9601720 ||
    population.filter(item => item.territory_id !== 'ISR').reduce((sum, item) => sum + item.value, 0) !== 9119780 ||
    9601720 - 9119780 !== 481940) throw new Error('CBS separate-area control changed');

function csvRows(csv) {
  const rows = []; let row = [], cell = '', quoted = false;
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
for (const area of [dataset.territories.find(item => item.id === 'ISR'),
  ...['Jerusalem District', 'Tel Aviv', 'Haifa', 'Southern District'].map(name =>
    children.find(item => item.name === name))]) {
  if (!area) throw new Error('Selected verification area absent');
  const outputs = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, content] of Object.entries(outputs)) {
    await writeFile(path.join(out, `${area.name}-${suffix}`), content);
  }
  const [head, ...rows] = csvRows(outputs['diagnostic.csv']);
  const column = key => {
    const index = head.indexOf(key);
    if (index < 0) throw new Error(`Missing output column ${key}`);
    return index;
  };
  for (const id of ids) {
    const observed = dataset.observations.find(item => item.territory_id === area.id && item.indicator_id === id);
    const output = rows.filter(row => row[column('Record scope')] === 'overall' && row[column('Indicator ID')] === id);
    if (output.length !== 1 || Number(output[0][column('Value')]) !== observed.value ||
        output[0][column('Period')] !== '2022' || output[0][column('Source URL')] !== source.url) {
      throw new Error(`CBS rendered value/source differs: ${area.name}/${id}`);
    }
    const within = rows.filter(row => row[column('Record scope')] === 'within_area' && row[column('Indicator ID')] === id);
    if (within.length !== (area.id === 'ISR' ? 6 : 0)) {
      throw new Error(`District comparison coverage differs: ${area.name}/${id}`);
    }
    if (area.id === 'ISR') for (const child of children) {
      const expected = dataset.observations.find(item => item.territory_id === child.id && item.indicator_id === id);
      const exported = within.find(row => row[column('Territory ID')] === child.id);
      if (!expected || !exported || Number(exported[column('Value')]) !== expected.value) {
        throw new Error(`District comparison value differs: ${child.name}/${id}`);
      }
    }
  }
  if (!outputs['diagnostic.html'].includes('Judea and Samaria Area')) {
    throw new Error('CBS national coverage caveat absent from diagnostic HTML');
  }
  checks.push({area: area.name, id: area.id, diagnostic_csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_id: source.id, checks,
  limitations: ['Only six provider districts are name-matched; legal boundary versions remain unverified',
    'CBS nationwide includes a seventh separately reported area not shown as a mapped district',
    'Other source sheets/fields, locality data, planning, finance, all 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project, 'evidence/ISR_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, rows: item.diagnostic_csv_rows})), null, 2));

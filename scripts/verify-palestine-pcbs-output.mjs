#!/usr/bin/env node
// Compare selected generated diagnosis/planning exports with pinned PCBS source counts.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-palestine-pcbs-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const sha = input => createHash('sha256').update(input).digest('hex');
if (dataset.country.id !== 'PSE') throw new Error('Expected Palestine candidate');
const sourceId = 'pse-pcbs-phc-2017-summary-table2';
const source = dataset.sources.find(item => item.id === sourceId);
if (!source || source.sha256 !== '25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f' ||
    sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('PCBS 2017 summary original/hash changed');
}
const regions = dataset.territories.filter(item => item.parent_id === 'PSE');
const governorates = dataset.territories.filter(item => regions.some(region => region.id === item.parent_id));
const ids = ['TOTAL', 'FEMALE', 'MALE', 'HOUSEHOLDS'].map(suffix => 'PSE_PCBS_2017_' + suffix);
if (dataset.territories.length !== 19 || regions.length !== 2 || governorates.length !== 16 ||
    dataset.boundaries.features.length !== 0 || dataset.documents.length !== 2 ||
    dataset.territories.some(item => item.boundary_version !== null) ||
    dataset.documents.some(item => item.territory_id !== 'PSE')) {
  throw new Error('PCBS hierarchy, boundary or planning scope changed');
}
for (const id of ids) {
  const indicator = dataset.indicators.find(item => item.id === id);
  const rows = dataset.observations.filter(item => item.indicator_id === id);
  if (!indicator || rows.length !== 19 || rows.some(item => item.period !== '2017' ||
      item.source_id !== sourceId || item.measurement_method !== indicator.measurement_method ||
      item.provenance === 'calculated')) {
    throw new Error(`PCBS indicator coverage/meaning changed: ${id}`);
  }
}
const areaById = new Map(dataset.territories.map(item => [item.id, item]));
const observations = new Map(dataset.observations.filter(item => ids.includes(item.indicator_id))
  .map(item => [`${item.territory_id}/${item.indicator_id}`, item]));
for (const area of dataset.territories) {
  const get = id => observations.get(`${area.id}/${id}`);
  if (get(ids[1]).value + get(ids[2]).value !== get(ids[0]).value) {
    throw new Error(`PCBS sex count mismatch: ${area.id}`);
  }
}
for (const parent of ['PSE', ...regions.map(item => item.id)]) {
  const children = dataset.territories.filter(item => item.parent_id === parent);
  for (const id of ids) {
    if (children.reduce((sum, child) => sum + observations.get(`${child.id}/${id}`).value, 0) !==
        observations.get(`${parent}/${id}`).value) {
      throw new Error(`PCBS reporting hierarchy count mismatch: ${parent}/${id}`);
    }
  }
}
const sample = [
  ['PSE', 4781248],
  ['PSE:PCBS2017:REG:WEST-BANK', 2881957],
  ['PSE:PCBS2017:GOV:JENIN', 314866],
  ['PSE:PCBS2017:GOV:JERUSALEM', 435753],
  ['PSE:PCBS2017:REG:GAZA-STRIP', 1899291],
  ['PSE:PCBS2017:GOV:GAZA', 652597],
  ['PSE:PCBS2017:GOV:RAFAH', 233878],
];
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
  return rows.filter(item => item.some(value => value !== ''));
}
const out = path.join(project, 'evidence/output-verification');
await mkdir(out, {recursive: true});
const checks = [];
for (const [areaId, total] of sample) {
  const area = areaById.get(areaId);
  if (!area || observations.get(`${areaId}/${ids[0]}`).value !== total) {
    throw new Error(`Independent PCBS sample control changed: ${areaId}`);
  }
  const outputs = {
    'diagnostic.csv': diagnosticCsv(dataset, areaId, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, areaId, 'latest-available'),
    'planning.html': planningHtml(dataset, areaId, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, areaId, 'latest-available'),
  };
  const prefix = areaId.replaceAll(':', '_');
  for (const [suffix, content] of Object.entries(outputs)) {
    await writeFile(path.join(out, `${prefix}-${suffix}`), content);
  }
  const [header, ...rows] = csvRows(outputs['diagnostic.csv']);
  const col = key => {
    const index = header.indexOf(key);
    if (index < 0) throw new Error(`Missing export column: ${key}`);
    return index;
  };
  for (const id of ids) {
    const expected = observations.get(`${areaId}/${id}`);
    const overall = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === id);
    if (overall.length !== 1 || Number(overall[0][col('Value')]) !== expected.value ||
        overall[0][col('Period')] !== '2017' || overall[0][col('Source URL')] !== source.url ||
        overall[0][col('Territory ID')] !== areaId) {
      throw new Error(`PCBS diagnostic export differs: ${areaId}/${id}`);
    }
    const children = dataset.territories.filter(item => item.parent_id === areaId);
    const within = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === id);
    if (within.length !== children.length) throw new Error(`Child coverage differs: ${areaId}/${id}`);
    for (const child of children) {
      const expectedChild = observations.get(`${child.id}/${id}`);
      const exported = within.find(row => row[col('Territory ID')] === child.id);
      if (!expectedChild || !exported || Number(exported[col('Value')]) !== expectedChild.value ||
          exported[col('Comparable')] !== 'true') {
        throw new Error(`Child comparison differs: ${child.id}/${id}`);
      }
    }
  }
  if (!outputs['diagnostic.html'].includes('2017') ||
      !outputs['planning.html'].includes(area.name)) {
    throw new Error(`2017 caveat or selected-area label absent: ${areaId}`);
  }
  checks.push({area_id: areaId, area_name: area.name, total,
    diagnostic_csv_rows: rows.length, first_data_row: rows[0]?.slice(0, 17),
    last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_id: sourceId, checks,
  limitations: ['Historical 2017 final census counts are not 2026 population or WDI midyear estimates',
    'Table 29 locality values and dated official polygons/codes remain unadopted',
    'Two national Ministry documents are not local plans, budgets or implementation results',
    '42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project, 'evidence/PSE_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area_id: item.area_id, rows: item.diagnostic_csv_rows})), null, 2));

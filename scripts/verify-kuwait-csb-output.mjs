#!/usr/bin/env node
// Check generated diagnosis/planning exports against pinned Kuwait Table 1 counts.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-kuwait-csb-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const sha = input => createHash('sha256').update(input).digest('hex');
const sourceId = 'kwt-csb-registration-census-2021-table1';
const source = dataset.sources.find(item => item.id === sourceId);
if (dataset.country.id !== 'KWT' || !source ||
    source.sha256 !== '1ef400667d1cd91b68aba1c446fb63861a65cd45d269b4090707b27893f89bd7' ||
    sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('Kuwait Table 1 original/hash changed');
}
const ids = ['ALL_TOTAL', 'ALL_FEMALE', 'ALL_MALE', 'KUWAITI_TOTAL', 'KUWAITI_FEMALE',
  'KUWAITI_MALE', 'NONKUWAITI_TOTAL', 'NONKUWAITI_FEMALE', 'NONKUWAITI_MALE']
  .map(suffix => 'KWT_CSB_2021_' + suffix);
const areas = dataset.territories;
const observations = new Map(dataset.observations.filter(item => ids.includes(item.indicator_id))
  .map(item => [`${item.territory_id}/${item.indicator_id}`, item]));
if (areas.length !== 7 || areas.filter(item => item.parent_id === 'KWT').length !== 6 ||
    dataset.boundaries.features.length !== 0 || dataset.documents.length !== 0 || observations.size !== 63) {
  throw new Error('Kuwait hierarchy, boundary, document or observation scope changed');
}
for (const id of ids) {
  const indicator = dataset.indicators.find(item => item.id === id);
  if (!indicator || [...observations.values()].filter(item => item.indicator_id === id).length !== 7 ||
      [...observations.values()].filter(item => item.indicator_id === id).some(item =>
        item.period !== '2021' || item.source_id !== sourceId || item.measurement_method !== indicator.measurement_method)) {
    throw new Error(`Kuwait count field changed: ${id}`);
  }
}
const get = (area, id) => observations.get(`${area}/${id}`)?.value;
if (get('KWT', ids[0]) !== 4385717 ||
    areas.filter(item => item.parent_id === 'KWT').reduce((sum, area) => sum + get(area.id, ids[0]), 0) !== 4381139 ||
    get('KWT', ids[0]) - 4381139 !== 4578) {
  throw new Error('Kuwait unassigned-population control differs');
}
for (const area of areas) {
  if (get(area.id, ids[1]) + get(area.id, ids[2]) !== get(area.id, ids[0]) ||
      get(area.id, ids[3]) + get(area.id, ids[6]) !== get(area.id, ids[0])) {
    throw new Error(`Sex/nationality identities differ: ${area.id}`);
  }
}
const samples = [
  ['KWT', 4385717],
  ['KWT:CSB2021:GOV:THE-CAPITAL', 574839],
  ['KWT:CSB2021:GOV:HAWALLI', 926170],
  ['KWT:CSB2021:GOV:AL-FARWANIYA', 1109819],
  ['KWT:CSB2021:GOV:MUBARAK-AL-KABEER', 279666],
];
function parseCsv(csv) {
  const result = []; let row = [], cell = '', quoted = false;
  for (let i = csv.charCodeAt(0) === 0xfeff ? 1 : 0; i < csv.length; i++) {
    const c = csv[i];
    if (quoted) {
      if (c === '"' && csv[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { result.push([...row, cell.replace(/\r$/, '')]); row = []; cell = ''; }
    else cell += c;
  }
  if (row.length || cell) result.push([...row, cell]);
  return result.filter(item => item.some(value => value !== ''));
}
const out = path.join(project, 'evidence/output-verification');
await mkdir(out, {recursive: true});
const checks = [];
for (const [areaId, total] of samples) {
  const area = areas.find(item => item.id === areaId);
  if (!area || get(areaId, ids[0]) !== total) throw new Error(`Sample control changed: ${areaId}`);
  const outputs = {
    'diagnostic.csv': diagnosticCsv(dataset, areaId, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, areaId, 'latest-available'),
    'planning.html': planningHtml(dataset, areaId, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, areaId, 'latest-available'),
  };
  const prefix = areaId.replaceAll(':', '_');
  for (const [kind, content] of Object.entries(outputs)) {
    await writeFile(path.join(out, `${prefix}-${kind}`), content);
  }
  const [header, ...rows] = parseCsv(outputs['diagnostic.csv']);
  const col = name => {
    const at = header.indexOf(name);
    if (at < 0) throw new Error(`Missing diagnostic CSV column: ${name}`);
    return at;
  };
  for (const id of ids) {
    const actual = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === id);
    if (actual.length !== 1 || actual[0][col('Territory ID')] !== areaId ||
        actual[0][col('Period')] !== '2021' || actual[0][col('Source URL')] !== source.url ||
        Number(actual[0][col('Value')]) !== get(areaId, id)) {
      throw new Error(`Kuwait export mismatch: ${areaId}/${id}`);
    }
    const children = areas.filter(item => item.parent_id === areaId);
    const within = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === id);
    if (within.length !== children.length || within.some(row =>
      !children.some(child => child.id === row[col('Territory ID')] &&
        get(child.id, id) === Number(row[col('Value')])))) {
      throw new Error(`Kuwait child comparison mismatch: ${areaId}/${id}`);
    }
  }
  if (!outputs['diagnostic.html'].includes('2021') || !outputs['planning.html'].includes(area.name)) {
    throw new Error(`Kuwait diagnosis/planning label absent: ${areaId}`);
  }
  checks.push({area_id: areaId, area_name: area.name, total,
    diagnostic_csv_rows: rows.length, first_data_row: rows[0]?.slice(0, 17),
    last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_id: sourceId, checks,
  limitations: ['2021 registration census counts are not current WDI annual population values',
    'Six governorates exclude the separate 4,578-person Not Stated row',
    '157 Table 51 areas and legal polygons/codes remain unadopted',
    'No local planning/budget original, 42-scenario pass or independent ACCEPT']};
await writeFile(path.join(project, 'evidence/KWT_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area_id: item.area_id, rows: item.diagnostic_csv_rows})), null, 2));

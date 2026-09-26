#!/usr/bin/env node
// Check the limited LFHLCS adoption against actual diagnostic/planning exports.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-lebanon-lfhlcs-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
if (dataset.country.id !== 'LBN') throw new Error('Expected Lebanon candidate');
const sha = input => createHash('sha256').update(input).digest('hex');
const sourceId = 'lbn-cas-lfhlcs-2018-19-hl5';
const source = dataset.sources.find(item => item.id === sourceId);
if (!source || sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('CAS original/hash changed');
}
const ids = dataset.indicators.filter(item => item.id.startsWith('LBN_CAS_LFHLCS_2018_')).map(item => item.id);
if (ids.length !== 3) throw new Error('Expected three adopted HL5 fields');
const governors = dataset.territories.filter(item => item.parent_id === 'LBN');
const caza = dataset.territories.filter(item => governors.some(gov => gov.id === item.parent_id));
if (governors.length !== 8 || caza.length !== 26 || dataset.territories.length !== 35 ||
    dataset.boundaries.features.length !== 26 || governors.some(item => item.boundary_version !== null) ||
    caza.some(item => !item.reconciliation_status?.includes('equivalence_unverified'))) {
  throw new Error('CAS eight-governorate/26-caza or reference-boundary scope changed');
}
for (const id of ids) {
  const indicator = dataset.indicators.find(item => item.id === id);
  const values = dataset.observations.filter(item => item.indicator_id === id);
  if (values.length !== 35 || values.some(item => item.period !== '2018' || item.source_id !== sourceId ||
      item.measurement_method !== indicator.measurement_method) ||
      values.filter(item => caza.some(area => area.id === item.territory_id)).some(item =>
        item.boundary_version === caza.find(area => area.id === item.territory_id).boundary_version)) {
    throw new Error(`Survey field coverage or boundary guard changed: ${id}`);
  }
}
if (dataset.observations.filter(item => ids.includes(item.indicator_id)).length !== 105 ||
    dataset.observations.length !== 417 || dataset.documents.length !== 0) {
  throw new Error('Candidate observation/document counts changed');
}
const totalId = 'LBN_CAS_LFHLCS_2018_TOTAL';
const sample = [
  ['Lebanon', 4842500], ['Beirut', 341700], ['Mount Lebanon', 2032600],
  ['Akkar', 324000], ['Keserwan', 260500], ['Jbeil', 129500],
];
for (const [name, value] of sample) {
  const area = dataset.territories.find(item => item.name === name);
  const found = dataset.observations.find(item => item.territory_id === area?.id && item.indicator_id === totalId);
  if (found?.value !== value) throw new Error(`CAS HL5 control differs: ${name}`);
}

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
for (const [name] of sample) {
  const area = dataset.territories.find(item => item.name === name);
  const outputs = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, content] of Object.entries(outputs)) {
    await writeFile(path.join(out, `${name}-${suffix}`), content);
  }
  const [header, ...rows] = csvRows(outputs['diagnostic.csv']);
  const column = key => {
    const index = header.indexOf(key);
    if (index < 0) throw new Error(`Missing output column ${key}`);
    return index;
  };
  for (const id of ids) {
    const observed = dataset.observations.find(item => item.territory_id === area.id && item.indicator_id === id);
    const overall = rows.filter(row => row[column('Record scope')] === 'overall' && row[column('Indicator ID')] === id);
    if (overall.length !== 1 || Number(overall[0][column('Value')]) !== observed.value ||
        overall[0][column('Period')] !== '2018' || overall[0][column('Source URL')] !== source.url) {
      throw new Error(`Survey export differs: ${name}/${id}`);
    }
    const within = rows.filter(row => row[column('Record scope')] === 'within_area' && row[column('Indicator ID')] === id);
    const children = dataset.territories.filter(item => item.parent_id === area.id);
    if (within.length !== children.length) {
      throw new Error(`Raw child coverage differs: ${name}/${id}`);
    }
    for (const child of children) {
      const expected = dataset.observations.find(item => item.territory_id === child.id && item.indicator_id === id);
      const exported = within.find(row => row[column('Territory ID')] === child.id);
      const comparable = area.id === 'LBN';
      if (!exported || Number(exported[column('Value')]) !== expected.value ||
          exported[column('Comparable')] !== String(comparable) ||
          (!comparable && !exported[column('Comparison reason')].includes('boundary edition'))) {
        throw new Error(`Child comparison disposition differs: ${child.name}/${id}`);
      }
    }
  }
  if (!outputs['diagnostic.html'].includes('MOPH map shows nine governorates') ||
      !outputs['planning.html'].includes(name)) {
    throw new Error(`Survey geographic caveat or planning-area label absent: ${name}`);
  }
  checks.push({area: name, id: area.id, diagnostic_csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_id: sourceId, checks,
  limitations: ['LFHLCS is a 2018 sample-survey estimate for residential-dwelling residents, not a census',
    'CAS eight-governorate reporting geography does not match the undated MOPH nine-governorate map',
    'MOPH caza shapes are name-matched reference only; their dates/legal boundary equivalence are unverified',
    'Other workbook fields, 26 profile contents, local planning/finance, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project, 'evidence/LBN_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, rows: item.diagnostic_csv_rows})), null, 2));

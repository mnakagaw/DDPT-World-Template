#!/usr/bin/env node
// Compare selected Oman diagnosis/planning exports with verified source cells.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-oman-ecensus-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const sha = input => createHash('sha256').update(input).digest('hex');
if (dataset.country.id !== 'OMN') throw new Error('Expected Oman candidate');
const sourceId = 'omn-ecensus-2020-population';
const source = dataset.sources.find(item => item.id === sourceId);
if (!source || sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('eCensus source pivot original/hash changed');
}
const ministry = dataset.sources.find(item => item.id === 'omn-moi-governorate-wilayat-2025');
if (!ministry || sha(await readFile(path.join(project, ministry.raw_path))) !== ministry.sha256 ||
    ministry.sha256 !== '63225e0a09ad41a41d5bd3b98b506e9117defdd67b8a7bbc0770ed686c63419b') {
  throw new Error('MOI directory original/hash changed');
}
const governors = dataset.territories.filter(item => item.parent_id === 'OMN');
const wilayats = dataset.territories.filter(item => governors.some(gov => gov.id === item.parent_id));
const ids = ['OMN_ECENSUS_2020_TOTAL', 'OMN_ECENSUS_2020_OMANI', 'OMN_ECENSUS_2020_EXPAT'];
if (dataset.territories.length !== 73 || governors.length !== 11 || wilayats.length !== 61 ||
    dataset.boundaries.features.length !== 0 ||
    dataset.territories.some(item => item.boundary_version !== null) ||
    dataset.documents.length > 1) {
  throw new Error('eCensus source hierarchy/boundary/document scope changed');
}
for (const id of ids) {
  const indicator = dataset.indicators.find(item => item.id === id);
  const rows = dataset.observations.filter(item => item.indicator_id === id);
  if (!indicator || rows.length !== 73 || rows.some(item => item.period !== '2020' ||
      item.source_id !== sourceId || item.measurement_method !== indicator.measurement_method)) {
    throw new Error(`eCensus indicator coverage/meaning changed: ${id}`);
  }
}
const areaById = new Map(dataset.territories.map(item => [item.id, item]));
const observations = new Map(dataset.observations.filter(item => ids.includes(item.indicator_id))
  .map(item => [`${item.territory_id}/${item.indicator_id}`, item]));
for (const area of dataset.territories) {
  const get = id => observations.get(`${area.id}/${id}`);
  if (get(ids[0]).value !== get(ids[1]).value + get(ids[2]).value ||
      (area.id === 'OMN') === (get(ids[0]).provenance === 'calculated')) {
    throw new Error(`Nationality sum/provenance mismatch: ${area.id}`);
  }
}
for (const gov of governors) {
  const children = wilayats.filter(item => item.parent_id === gov.id);
  for (const id of ids) {
    if (children.reduce((sum, child) => sum + observations.get(`${child.id}/${id}`).value, 0) !==
        observations.get(`${gov.id}/${id}`).value) {
      throw new Error(`Governorate source total mismatch: ${gov.id}/${id}`);
    }
  }
}
for (const id of ids) {
  if (governors.reduce((sum, gov) => sum + observations.get(`${gov.id}/${id}`).value, 0) !==
      observations.get(`OMN/${id}`).value) throw new Error(`National source total mismatch: ${id}`);
}
const sample = [
  ['OMN', 4471148],
  ['OMN:ECENSUS2020:GOV:MUSCAT', 1302440],
  ['OMN:ECENSUS2020:WIL:MUSCAT:MUSCAT', 31317],
  ['OMN:ECENSUS2020:GOV:AD-DAKHLIYAH', 478501],
  ['OMN:ECENSUS2020:WIL:AD-DAKHLIYAH:NIZWA', 131763],
  ['OMN:ECENSUS2020:WIL:AL-BATINAH-NORTH:SOHAR', 232849],
  ['OMN:ECENSUS2020:GOV:AL-WUSTA', 52344],
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
    throw new Error(`Independent sample control changed: ${areaId}`);
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
    if (index < 0) throw new Error(`Missing output column: ${key}`);
    return index;
  };
  for (const id of ids) {
    const expected = observations.get(`${areaId}/${id}`);
    const overall = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === id);
    if (overall.length !== 1 || Number(overall[0][col('Value')]) !== expected.value ||
        overall[0][col('Period')] !== '2020' || overall[0][col('Source URL')] !== source.url ||
        overall[0][col('Territory ID')] !== areaId) {
      throw new Error(`eCensus export differs: ${areaId}/${id}`);
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
  if (!outputs['diagnostic.html'].includes('2025 Ministry of Interior') ||
      !outputs['planning.html'].includes(area.name)) {
    throw new Error(`Geographic caveat or selected-area planning label absent: ${areaId}`);
  }
  checks.push({area_id: areaId, area_name: area.name, total,
    diagnostic_csv_rows: rows.length, first_data_row: rows[0]?.slice(0, 17),
    last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_id: sourceId, checks,
  limitations: ['National eCensus 2020 date is not WDI 2025 estimate or later portal snapshots',
    'MOI October-2025 directory was matched by names but does not certify 2020 legal codes or polygons',
    'Two 2025-listed wilayats have null 2020 cells; source exceptions and unassessed fields remain',
    'Local plans, financing, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project, 'evidence/OMN_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area_id: item.area_id, rows: item.diagnostic_csv_rows})), null, 2));

#!/usr/bin/env node
// Check generated Georgia diagnosis/planning exports against pinned Geostat originals.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-georgia-geostat-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const sha = input => createHash('sha256').update(input).digest('hex');
const popSource = dataset.sources.find(item => item.id === 'geo-geostat-census-2024-population-by-local-unit');
const idpSource = dataset.sources.find(item => item.id === 'geo-geostat-census-2024-idp-by-residence-origin');
if (dataset.country.id !== 'GEO' || !popSource || !idpSource ||
    popSource.sha256 !== 'b3629935b5d8107c924ae8f5472a1537f6689227373a9e2936dcc46b20753474' ||
    idpSource.sha256 !== 'a4d2483aa428f43b6e87f152e130216cd8b27bf2e41859b0a7961c8bf876b711' ||
    sha(await readFile(path.join(project, popSource.raw_path))) !== popSource.sha256 ||
    sha(await readFile(path.join(project, idpSource.raw_path))) !== idpSource.sha256) {
  throw new Error('Georgia Geostat originals/hashes changed');
}
const areas = dataset.territories;
const domestic = dataset.observations.filter(item => item.indicator_id.startsWith('GEO_GEOSTAT_2024_'));
const observed = domestic.filter(item => item.status === 'observed');
const missing = domestic.filter(item => item.status === 'missing');
if (areas.length !== 85 || dataset.boundaries.features.length !== 0 ||
    dataset.documents.length !== 2 || domestic.length !== 1440 || observed.length !== 1413 || missing.length !== 27 ||
    areas.filter(item => item.parent_id === 'GEO').length !== 11 ||
    areas.filter(item => item.type === 'municipality').length !== 63 ||
    areas.filter(item => item.type === 'municipal_district').length !== 10) {
  throw new Error('Georgia hierarchy, boundary, document or observation scope changed');
}
const map = new Map(domestic.map(item => [`${item.territory_id}/${item.indicator_id}`, item]));
const byName = name => {
  const matches = areas.filter(item => item.name === name);
  if (matches.length !== 1) throw new Error(`Expected one source geography: ${name}`);
  return matches[0];
};
const get = (name, suffix, source = 'POP') => map.get(`${byName(name).id}/GEO_GEOSTAT_2024_${source}_${suffix}`);
for (const [name, pop, idp] of [
  ['Georgia', 3929581, 210628], ['C. Tbilisi', 1331485, 95563],
  ['Imereti', 510741, 20305], ['C. Kutaisi', 160971, 10059],
  ['Sighnagi Municipality', 28762, 226], ['Kazbegi Municipality', 4887, 61],
]) {
  if (get(name, 'TOTAL')?.value !== pop || get(name, 'TOTAL', 'IDP')?.value !== idp) {
    throw new Error(`Georgia source control differs: ${name}`);
  }
}
if (get('Georgia', 'URBAN_TOTAL').value !== 2455444 ||
    get('Georgia', 'RURAL_TOTAL').value !== 1474137 ||
    get('Didube District', 'RURAL_TOTAL').status !== 'missing' ||
    get('Didube District', 'RURAL_TOTAL').value !== null ||
    get('Didube District', 'TOTAL', 'IDP') !== undefined) {
  throw new Error('Georgia urban/rural nil or IDP district controls changed');
}
for (const area of areas) {
  const pop = map.get(`${area.id}/GEO_GEOSTAT_2024_POP_TOTAL`);
  if (!pop || pop.period !== '2024-11-14' || pop.source_id !== popSource.id) throw new Error(`Population source mismatch: ${area.id}`);
  if (area.type !== 'municipal_district') {
    const idp = map.get(`${area.id}/GEO_GEOSTAT_2024_IDP_TOTAL`);
    if (!idp || idp.period !== '2024-11-14' || idp.source_id !== idpSource.id || idp.value > pop.value) {
      throw new Error(`IDP subset mismatch: ${area.id}`);
    }
  }
}

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
const output = path.join(project, 'evidence/output-verification');
await mkdir(output, {recursive: true});
const checks = [];
for (const areaName of ['Georgia', 'C. Tbilisi', 'Didube District', 'Imereti', 'C. Kutaisi', 'Sighnagi Municipality', 'Kazbegi Municipality']) {
  const area = byName(areaName);
  const files = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [kind, content] of Object.entries(files)) {
    await writeFile(path.join(output, `${area.id.replaceAll(':', '_')}-${kind}`), content);
  }
  const [header, ...rows] = parseCsv(files['diagnostic.csv']);
  const col = name => {
    const index = header.indexOf(name);
    if (index < 0) throw new Error(`Diagnostic CSV column absent: ${name}`);
    return index;
  };
  for (const source of [popSource, idpSource]) {
    const prefix = source === popSource ? 'GEO_GEOSTAT_2024_POP_' : 'GEO_GEOSTAT_2024_IDP_';
    for (const indicator of dataset.indicators.filter(item => item.id.startsWith(prefix))) {
      const expected = map.get(`${area.id}/${indicator.id}`);
      const actual = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === indicator.id);
      if (expected && (actual.length !== 1 || actual[0][col('Territory ID')] !== area.id ||
          actual[0][col('Period')] !== '2024-11-14' || actual[0][col('Source URL')] !== source.url ||
          (expected.status === 'observed' && Number(actual[0][col('Value')]) !== expected.value) ||
          (expected.status === 'missing' && actual[0][col('Value')] !== ''))) {
        throw new Error(`Georgia export mismatch: ${areaName}/${indicator.id}`);
      }
      const children = areas.filter(item => item.parent_id === area.id);
      const childRows = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === indicator.id);
      const expectedChildren = children;
      if (childRows.length !== expectedChildren.length || childRows.some(row => {
        const child = expectedChildren.find(item => item.id === row[col('Territory ID')]);
        const observation = child && map.get(`${child.id}/${indicator.id}`);
        return !child || (!observation && (row[col('Status')] !== 'not_collected' || row[col('Value')] !== '')) ||
          (observation?.status === 'observed' && Number(row[col('Value')]) !== observation.value) ||
          (observation?.status === 'missing' && row[col('Value')] !== '');
      })) {
        throw new Error(`Georgia child export mismatch: ${areaName}/${indicator.id}`);
      }
    }
  }
  const planning = files['planning.html'];
  const hasKutaisiDocs = planning.includes('Kutaisi Municipality 2026') && planning.includes('Kutaisi 2026 municipal budget');
  const originalBudgetStatus = planning.includes('original_ordinance_approved_2025_current_amendments_unverified') &&
    planning.includes('No current or executed amount is derived from this original.');
  if ((areaName === 'C. Kutaisi') !== hasKutaisiDocs ||
      (areaName === 'C. Kutaisi') !== originalBudgetStatus ||
      !files['diagnostic.html'].includes(areaName)) {
    throw new Error(`Georgia diagnosis/planning target differs: ${areaName}`);
  }
  checks.push({area_id: area.id, area_name: area.name, diagnostic_csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(files).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), pop_source_sha256: popSource.sha256, idp_source_sha256: idpSource.sha256, checks,
  limitations: ['Occupied territories outside Geostat 2024 census source coverage',
    'Twenty-seven dash cells are missing, never numeric zero',
    'IDPs are a subset and are not added to the resident total',
    'Official code and dated polygon crosswalk unverified',
    'Kutaisi is the only municipality with acquired planning/budget originals; later amendments unverified',
    '42-scenario pass and independent ACCEPT not completed']};
await writeFile(path.join(project, 'evidence/GEO_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area_id: item.area_id, rows: item.diagnostic_csv_rows})), null, 2));

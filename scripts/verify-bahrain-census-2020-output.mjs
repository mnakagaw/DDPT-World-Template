#!/usr/bin/env node
// Check the five selected-area outputs against the acquired Census 2020 cells.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv, comparisonCsv, seriesCsv, observationsCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-bahrain-census-2020-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const data = JSON.parse(bytes.toString('utf8'));
const sha = input => createHash('sha256').update(input).digest('hex');
if (data.country.id !== 'BHR') throw new Error('Expected Bahrain candidate');
const inventory = JSON.parse(await readFile(path.join(project, 'evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json')));
if (inventory.tables.length !== 45 || inventory.tables.reduce((n, row) => n + row.record_count, 0) !== 2602) {
  throw new Error('Census catalogue or source row count changed');
}
for (const table of inventory.tables) {
  for (const page of table.pages) {
    const body = await readFile(path.join(project, page.raw_path));
    const receipt = JSON.parse(await readFile(path.join(project, `${page.raw_path}.receipt.json`)));
    if (sha(body) !== page.sha256 || receipt.sha256 !== page.sha256 || receipt.status !== 'acquired') {
      throw new Error(`Census source page/receipt changed: ${page.raw_path}`);
    }
  }
}
const controls = {
  POP_TOTAL: 1501635, POP_MALE: 942895, POP_FEMALE: 558740,
  POP_BAHRAINI: 712362, POP_NON_BAHRAINI: 789273,
  HOUSING_UNITS: 387126, HOUSEHOLDS_TOTAL: 245983, HOUSEHOLDS_PRIVATE: 228972,
  SCHOOL_ENROLLED_3PLUS: 309557, ECONOMICALLY_ACTIVE_15PLUS: 875558,
};
const governorates = data.territories.filter(row => row.parent_id === 'BHR');
if (data.territories.length !== 5 || governorates.length !== 4 || data.boundaries.features.length !== 0 ||
    data.observations.filter(row => row.indicator_id.startsWith('BHR_CENSUS2020_')).length !== 40 ||
    data.documents.length !== 0) throw new Error('Bahrain edition geography or adoption scope changed');
const obs = new Map(data.observations.map(row => [`${row.territory_id}/${row.indicator_id}`, row]));
for (const [suffix, total] of Object.entries(controls)) {
  const id = `BHR_CENSUS2020_${suffix}`;
  const rows = governorates.map(area => obs.get(`${area.id}/${id}`));
    if (rows.some(row => !row || row.period !== '2020' || row.status !== 'observed' || row.provenance !== 'calculated' || !Number.isInteger(row.value)) ||
      rows.reduce((sum, row) => sum + row.value, 0) !== total || obs.has(`BHR/${id}`)) {
    throw new Error(`Domestic source observation coverage changed: ${id}`);
  }
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
  return rows.filter(item => item.some(value => value !== ''));
}
const exportedObservations = csvRows(observationsCsv(data, governorates.map(area => area.id)));
const observationHeader = exportedObservations.shift();
const observationCol = name => observationHeader.indexOf(name);
const domesticExports = exportedObservations.filter(row => row[observationCol('Indicator ID')].startsWith('BHR_CENSUS2020_'));
if (domesticExports.length !== 40 || domesticExports.some(row =>
  row[observationCol('Status')] !== 'calculated' || row[observationCol('Value provenance')] !== 'calculated')) {
  throw new Error('All-observations CSV lost domestic calculated provenance');
}
const out = path.join(project, 'evidence/output-verification');
await mkdir(out, {recursive: true});
const checks = [];
for (const area of [data.territories.find(row => row.id === 'BHR'), ...governorates]) {
  const outputs = {
    'diagnostic.csv': diagnosticCsv(data, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(data, area.id, 'latest-available'),
    'diagnostic.md': diagnosticMarkdown(data, area.id, 'latest-available'),
    'planning.html': planningHtml(data, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(data, area.id, 'latest-available'),
  };
  const prefix = area.id.replaceAll(':', '_');
  for (const [kind, content] of Object.entries(outputs)) await writeFile(path.join(out, `${prefix}-${kind}`), content);
  const [header, ...rows] = csvRows(outputs['diagnostic.csv']);
  const col = name => { const index = header.indexOf(name); if (index < 0) throw new Error(`CSV column missing: ${name}`); return index; };
  for (const [suffix, total] of Object.entries(controls)) {
    const id = `BHR_CENSUS2020_${suffix}`;
    const source = data.sources.find(item => item.id === data.indicators.find(item => item.id === id)?.source_id);
    const overall = rows.filter(row => row[col('Record scope')] === 'overall' && row[col('Indicator ID')] === id);
    const expected = area.id === 'BHR' ? total : obs.get(`${area.id}/${id}`)?.value;
    if (!source || overall.length !== 1 || Number(overall[0][col('Value')]) !== expected ||
        overall[0][col('Period')] !== '2020' || overall[0][col('Status')] !== 'calculated' ||
        overall[0][col('Value provenance')] !== (area.id === 'BHR' ? 'areadata_calculated' : 'calculated') ||
        overall[0][col('Territory ID')] !== area.id || overall[0][col('Source URL')] !== source.url) {
      throw new Error(`Diagnosis does not match census source: ${area.id}/${id}`);
    }
    const within = rows.filter(row => row[col('Record scope')] === 'within_area' && row[col('Indicator ID')] === id);
    if (within.length !== (area.id === 'BHR' ? 4 : 0)) throw new Error(`Comparison coverage changed: ${area.id}/${id}`);
    for (const child of governorates.filter(row => row.parent_id === area.id)) {
      const exported = within.find(row => row[col('Territory ID')] === child.id);
      if (!exported || Number(exported[col('Value')]) !== obs.get(`${child.id}/${id}`)?.value ||
          exported[col('Comparable')] !== 'true' || exported[col('Status')] !== 'calculated' ||
          exported[col('Value provenance')] !== 'calculated' || exported[col('Period')] !== '2020' ||
          exported[col('Source URL')] !== source.url ||
          !exported[col('Aggregation note')].includes('sum')) throw new Error(`Comparison value or provenance changed: ${child.id}/${id}`);
      const htmlRow = outputs['diagnostic.html'].split(`data-internal-comparison="${id}"`)[1]?.split(`data-internal-row="${child.id}"`)[1]?.split('</tr>')[0] || '';
      const markdownRow = outputs['diagnostic.md'].split('\n').find(line => line.includes(`${child.name} / ${child.id}`) && line.includes(`| ${obs.get(`${child.id}/${id}`).value.toLocaleString('en')} |`)) || '';
      if (!htmlRow.includes('Calculated from source values') ||
          !markdownRow.includes('Calculated from source values')) {
        throw new Error(`Comparison display provenance changed: ${child.id}/${id}`);
      }
      const [comparisonHeader, ...comparisonRows] = csvRows(comparisonCsv(data,{selected:'BHR',level:'adm1',metric:id,period:'2020'}));
      const comparisonCol = name => comparisonHeader.indexOf(name);
      const comparisonExport = comparisonRows.find(row => row[comparisonCol('Territory ID')] === child.id);
      if (!comparisonExport || comparisonExport[comparisonCol('Status')] !== 'calculated' ||
          comparisonExport[comparisonCol('Value provenance')] !== 'calculated' ||
          Number(comparisonExport[comparisonCol('Value')]) !== obs.get(`${child.id}/${id}`).value ||
          comparisonExport[comparisonCol('Source URL')] !== source.url) {
        throw new Error(`Thematic comparison CSV provenance changed: ${child.id}/${id}`);
      }
      const [seriesHeader, ...seriesRows] = csvRows(seriesCsv(data,child.id,id));
      const seriesCol = name => seriesHeader.indexOf(name);
      if (seriesRows.length !== 1 || seriesRows[0][seriesCol('Status')] !== 'calculated' ||
          seriesRows[0][seriesCol('Value provenance')] !== 'calculated' ||
          Number(seriesRows[0][seriesCol('Value')]) !== obs.get(`${child.id}/${id}`).value) {
        throw new Error(`Thematic history CSV provenance changed: ${child.id}/${id}`);
      }
    }
  }
  const [evidenceHeader, ...evidenceRows] = csvRows(outputs['evidence.csv']);
  const evidenceCol = name => { const index = evidenceHeader.indexOf(name); if (index < 0) throw new Error(`Evidence CSV column missing: ${name}`); return index; };
  for (const suffix of Object.keys(controls)) {
    const row = evidenceRows.find(item => item[evidenceCol('Indicator ID')] === `BHR_CENSUS2020_${suffix}`);
    if (!row || row[evidenceCol('Status')] !== 'calculated' ||
        row[evidenceCol('Value provenance')] !== (area.id === 'BHR' ? 'areadata_calculated' : 'calculated')) {
      throw new Error(`Evidence CSV provenance changed: ${area.id}/${suffix}`);
    }
  }
  if (!outputs['planning.html'].includes(area.name) || !outputs['diagnostic.html'].includes(area.name)) {
    throw new Error(`Selected-area label missing: ${area.id}`);
  }
  checks.push({area_id: area.id, diagnostic_csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 18), last_data_row: rows.at(-1)?.slice(0, 18),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, content]) => [kind, sha(content)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), inventory_sha256: sha(await readFile(path.join(project, 'evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json'))), checks,
  limitations: ['Only 10 indicators from five of 45 Census 2020 tables are adopted',
    'The four census reporting names lack verified official codes and dated legal polygons',
    'No individual municipality plan, budget or official evaluation original is adopted',
    'Portal terms, complete acceptance scenarios and independent country audit remain open']};
await writeFile(path.join(project, 'evidence/BHR_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area_id: item.area_id, rows: item.diagnostic_csv_rows})), null, 2));

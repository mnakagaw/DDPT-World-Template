#!/usr/bin/env node
// Check the printed COSIT governorate totals against actual country exports.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const arg = process.argv.indexOf('--project');
if (arg < 0 || !process.argv[arg + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-iraq-census-2024-age-sex-output.mjs --project <project>');
}
const project = path.resolve(process.argv[arg + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
if (dataset.country.id !== 'IRQ') throw new Error('Expected Iraq country dataset');
const digest = input => createHash('sha256').update(input).digest('hex');
const source = dataset.sources.find(item => item.id === 'irq-cosit-census-2024-age-sex-urban-rural-pdf');
if (!source || source.sha256 !== 'e0800bbfd58a41d879ed4b9edc269eefe37a632eb2d32ecbade2b3f171ea0b3f') {
  throw new Error('Printed COSIT age/sex PDF source is missing or changed');
}
const raw = await readFile(path.join(project, source.raw_path));
if (digest(raw) !== source.sha256) throw new Error('Source PDF bytes differ from receipt');
const expected = {
  Iraq: [23161604, 22957189, 32363649, 13755144],
  Baghdad: [4904977, 4875452, 8334666, 1445763],
  'Dhi Qar': [1264589, 1234879, 1702948, 796520],
  'Al-Basrah': [1856748, 1807420, 3079170, 584998],
};
const indicators = ['IRQ_CENSUS_2024_MALE', 'IRQ_CENSUS_2024_FEMALE',
  'IRQ_CENSUS_2024_URBAN', 'IRQ_CENSUS_2024_RURAL'];
const children = dataset.territories.filter(item => item.parent_id === 'IRQ');
if (children.length !== 18 || new Set(children.map(item => item.census_source_code)).size !== 18) {
  throw new Error('The 18 census-code crosswalk is incomplete');
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
const out = path.join(project, 'evidence/output-verification-age-sex');
await mkdir(out, {recursive: true});
const checks = [];
for (const [name, values] of Object.entries(expected)) {
  const matches = dataset.territories.filter(item => item.name === name);
  if (matches.length !== 1) throw new Error(`Area is missing or ambiguous: ${name}`);
  const area = matches[0];
  const exports = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, contents] of Object.entries(exports)) {
    await writeFile(path.join(out, `${name.replaceAll(' ', '_')}-${suffix}`), contents);
  }
  const [heading, ...rows] = rowsOf(exports['diagnostic.csv']);
  const col = key => {
    const index = heading.indexOf(key);
    if (index < 0) throw new Error(`Output lacks ${key}`);
    return index;
  };
  for (let index = 0; index < indicators.length; index++) {
    const indicatorId = indicators[index];
    const overall = rows.filter(row => row[col('Record scope')] === 'overall' &&
      row[col('Indicator ID')] === indicatorId);
    if (overall.length !== 1 || Number(overall[0][col('Value')]) !== values[index] ||
        overall[0][col('Period')] !== '2024' || overall[0][col('Status')] !== 'observed' ||
        overall[0][col('Source URL')] !== source.url) {
      throw new Error(`${name}/${indicatorId}: overall export differs from COSIT printed total`);
    }
    const within = rows.filter(row => row[col('Record scope')] === 'within_area' &&
      row[col('Indicator ID')] === indicatorId);
    if (within.length !== (name === 'Iraq' ? 18 : 0)) {
      throw new Error(`${name}/${indicatorId}: wrong internal comparison row count`);
    }
    if (name === 'Iraq') {
      for (const child of children) {
        const datum = dataset.observations.find(item => item.territory_id === child.id &&
          item.indicator_id === indicatorId && item.period === '2024');
        const exported = within.find(row => row[col('Territory ID')] === child.id);
        if (!datum || !exported || Number(exported[col('Value')]) !== datum.value ||
            exported[col('Source URL')] !== source.url || exported[col('Status')] !== 'observed') {
          throw new Error(`${child.name}/${indicatorId}: internal export differs from accepted source value`);
        }
      }
    }
  }
  if (!exports['diagnostic.html'].includes(name) || !exports['planning.html'].includes(name) ||
      !exports['evidence.csv'].includes(name)) throw new Error(`${name}: area absent from generated output`);
  checks.push({area: name, territory_id: area.id, csv_rows: rows.length,
    four_indicator_values: values, comparison_rows_per_indicator: name === 'Iraq' ? 18 : 0,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    export_sha256: Object.fromEntries(Object.entries(exports).map(([kind, contents]) => [kind, digest(contents)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: digest(bytes), source_pdf_sha256: source.sha256, checks,
  limitations: ['Sub-governorate age bands remain unreviewed',
    'Census source codes are not reconciled to official 2024 boundary geometry',
    'No verified governorate planning documents or independent acceptance audit']};
await writeFile(path.join(project, 'evidence/OUTPUT_VERIFICATION_AGE_SEX.json'),
  JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, csv_rows: item.csv_rows,
  comparison_rows_per_indicator: item.comparison_rows_per_indicator, four_indicator_values: item.four_indicator_values})), null, 2));

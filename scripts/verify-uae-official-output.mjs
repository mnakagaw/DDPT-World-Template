#!/usr/bin/env node
// Compare selected exports with source controls and keep national/local series separate.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const flag = process.argv.indexOf('--project');
if (flag < 0 || !process.argv[flag + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-uae-official-output.mjs --project <project>');
}
const project = path.resolve(process.argv[flag + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
if (dataset.country.id !== 'ARE') throw new Error('Expected UAE candidate');
const sha = input => createHash('sha256').update(input).digest('hex');
const sourceIds = ['are-fcsc-census-figures-2005', 'are-scad-abu-dhabi-census-2024',
  'are-dubai-2040-structure-plan', 'are-dubai-urban-planning-law-16-2023'];
for (const id of sourceIds) {
  const source = dataset.sources.find(item => item.id === id);
  if (!source || sha(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
    throw new Error(`Acquired source or hash changed: ${id}`);
  }
}
const historical = ['ARE_FCSC_CENSUS_POP', 'ARE_FCSC_CENSUS_URBAN',
  'ARE_FCSC_CENSUS_RURAL', 'ARE_FCSC_CENSUS_BUILDINGS'];
const scad = ['ARE_SCAD_AD_CENSUS_2024_POPULATION', 'ARE_SCAD_AD_CENSUS_2024_MALE',
  'ARE_SCAD_AD_CENSUS_2024_FEMALE'];
const expected = {
  'United Arab Emirates': [4106427, 3384844, 721583, 336815],
  'Abu Dhabi': [1399484, 959692, 439792, 117469],
  'Dubai': [1321453, 1305060, 16393, 79214],
  'Ras al-Khaimah': [210063, 111261, 98802, 40143],
  'Umm al-Quwain': [49159, 32800, 16359, 8741],
  'Fujairah': [125698, 71874, 53824, 16197],
};
const children = dataset.territories.filter(item => item.parent_id === 'ARE');
if (children.length !== 7 || new Set(children.map(item => item.source_name_en)).size !== 7) {
  throw new Error('Seven-emirate source crosswalk incomplete');
}
for (const id of historical) {
  const observations = dataset.observations.filter(item => item.indicator_id === id);
  if (observations.length !== 40) throw new Error(`Wrong historical coverage: ${id}`);
  for (const year of ['1975', '1980', '1985', '1995', '2005']) {
    const annual = observations.filter(item => item.period === year);
    if (annual.length !== 8 || annual.filter(item => item.territory_id !== 'ARE')
      .reduce((sum, item) => sum + item.value, 0) !== annual.find(item => item.territory_id === 'ARE')?.value) {
      throw new Error(`Census total mismatch: ${id}/${year}`);
    }
  }
}
for (const id of scad) {
  const observations = dataset.observations.filter(item => item.indicator_id === id);
  if (observations.length !== 1 || observations[0].territory_id !== children.find(item => item.name === 'Abu Dhabi').id ||
      observations[0].period !== '2024') throw new Error(`SCAD scope changed: ${id}`);
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
for (const [name, values] of Object.entries(expected)) {
  const area = dataset.territories.find(item => item.name === name);
  if (!area) throw new Error(`Missing area ${name}`);
  const outputs = {
    'diagnostic.csv': diagnosticCsv(dataset, area.id, 'latest-available'),
    'diagnostic.html': diagnosticHtml(dataset, area.id, 'latest-available'),
    'planning.html': planningHtml(dataset, area.id, 'latest-available', 'en'),
    'evidence.csv': evidenceCsv(dataset, area.id, 'latest-available'),
  };
  for (const [suffix, contents] of Object.entries(outputs)) {
    await writeFile(path.join(out, `${name}-${suffix}`), contents);
  }
  const [head, ...rows] = csvRows(outputs['diagnostic.csv']);
  const column = key => {
    const index = head.indexOf(key);
    if (index < 0) throw new Error(`Missing output column ${key}`);
    return index;
  };
  for (let index = 0; index < historical.length; index++) {
    const overall = rows.filter(row => row[column('Record scope')] === 'overall' && row[column('Indicator ID')] === historical[index]);
    if (overall.length !== 1 || Number(overall[0][column('Value')]) !== values[index] ||
        overall[0][column('Period')] !== '2005' || overall[0][column('Source URL')] !==
          dataset.sources.find(item => item.id === sourceIds[0]).url) {
      throw new Error(`Historical output differs: ${name}/${historical[index]}`);
    }
    const within = rows.filter(row => row[column('Record scope')] === 'within_area' && row[column('Indicator ID')] === historical[index]);
    if (within.length !== (name === 'United Arab Emirates' ? 7 : 0)) {
      throw new Error(`Historical comparison coverage differs: ${name}/${historical[index]}`);
    }
    if (name === 'United Arab Emirates') for (const child of children) {
      const datum = dataset.observations.find(item => item.territory_id === child.id &&
        item.indicator_id === historical[index] && item.period === '2005');
      const exported = within.find(row => row[column('Territory ID')] === child.id);
      if (!datum || !exported || Number(exported[column('Value')]) !== datum.value) {
        throw new Error(`Historical country comparison differs: ${child.name}/${historical[index]}`);
      }
    }
  }
  for (let index = 0; index < scad.length; index++) {
    const overall = rows.filter(row => row[column('Record scope')] === 'overall' && row[column('Indicator ID')] === scad[index]);
    if (name === 'Abu Dhabi') {
      if (overall.length !== 1 || Number(overall[0][column('Value')]) !== [4135985, 2767060, 1368925][index] ||
          overall[0][column('Period')] !== '2024') throw new Error(`Abu Dhabi current output differs: ${scad[index]}`);
    } else if (overall.some(row => row[column('Status')] === 'observed')) {
      throw new Error(`SCAD Abu Dhabi observation leaked to ${name}: ${scad[index]}`);
    }
  }
  const hasDubaiPlan = outputs['planning.html'].includes('Dubai 2040 Structure Plan');
  if (hasDubaiPlan !== (name === 'Dubai')) throw new Error(`Dubai plan visibility differs: ${name}`);
  checks.push({area: name, territory_id: area.id, diagnostic_csv_rows: rows.length,
    first_data_row: rows[0]?.slice(0, 17), last_data_row: rows.at(-1)?.slice(0, 17),
    output_sha256: Object.fromEntries(Object.entries(outputs).map(([kind, contents]) => [kind, sha(contents)]))});
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: sha(bytes), source_ids: sourceIds, checks,
  limitations: ['2017 provider shapes lack official/historical code and boundary confirmation',
    'Current comparable data for six other emirates, lower geography and other sector data are unadopted',
    'Plan/law full review, budget, implementation, evaluation, print QA and independent acceptance remain open']};
await writeFile(path.join(project, 'evidence/ARE_OUTPUT_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(checks.map(item => ({area: item.area, diagnostic_csv_rows: item.diagnostic_csv_rows})), null, 2));

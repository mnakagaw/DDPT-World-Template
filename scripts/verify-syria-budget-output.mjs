#!/usr/bin/env node
// Check national-only budget attribution and exclusion of restricted IOM values.
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {planningHtml, documentsCsv} from '../scaffold/site/model.mjs';

const arg = process.argv.indexOf('--project');
if (arg < 0 || !process.argv[arg + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-syria-budget-output.mjs --project <project>');
}
const project = path.resolve(process.argv[arg + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const digest = input => createHash('sha256').update(input).digest('hex');
const budget = dataset.sources.find(item => item.id === 'syr-mof-citizen-budget-2026');
const iom = dataset.sources.find(item => item.id === 'syr-iom-dtm-baseline-round17-june-2026');
const document = dataset.documents.find(item => item.id === 'syr-national-citizen-budget-2026');
const aleppo = dataset.territories.find(item => item.name === 'Aleppo');
if (dataset.country.id !== 'SYR' || !budget || !iom || !document || !aleppo ||
    document.territory_id !== 'SYR' || document.category !== 'budget' ||
    document.availability !== 'content_verified' || document.official_status !== 'unverified') {
  throw new Error('Expected Syria national budget and Aleppo reference territory');
}
if (digest(await readFile(path.join(project, budget.raw_path))) !== budget.sha256 ||
    digest(await readFile(path.join(project, iom.raw_path))) !== iom.sha256) {
  throw new Error('Source original bytes differ from registered hashes');
}
if (dataset.observations.some(item => item.source_id === iom.id) ||
    dataset.indicators.some(item => item.source_id === iom.id)) {
  throw new Error('Restricted IOM values were unexpectedly adopted');
}
const nationalDocuments = dataset.documents.filter(item => item.territory_id === 'SYR');
const aleppoDocuments = dataset.documents.filter(item => item.territory_id === aleppo.id);
if (nationalDocuments.length !== 1 || aleppoDocuments.length !== 0) {
  throw new Error('National budget must not become an Aleppo document');
}
const outputs = {
  nationalHtml: planningHtml(dataset, 'SYR', '2025', 'en'),
  aleppoHtml: planningHtml(dataset, aleppo.id, '2025', 'en'),
  nationalCsv: documentsCsv(dataset, 'SYR'),
  aleppoCsv: documentsCsv(dataset, aleppo.id),
};
for (const expected of [document.title, budget.url, '2026', 'unverified']) {
  if (!outputs.nationalHtml.includes(expected) || !outputs.nationalCsv.includes(expected)) {
    throw new Error(`National planning outputs lack ${expected}`);
  }
}
if (outputs.aleppoHtml.includes(document.title) || outputs.aleppoCsv.includes(document.title) ||
    !outputs.aleppoHtml.includes('Aleppo')) {
  throw new Error('National budget leaked into Aleppo output');
}
const outputDir = path.join(project, 'evidence');
for (const [name, contents] of Object.entries(outputs)) {
  await writeFile(path.join(outputDir, `SYR_BUDGET_${name}.txt`), contents);
}
const report = {
  status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: digest(bytes), budget_pdf_sha256: budget.sha256,
  national_document_count: nationalDocuments.length, aleppo_document_count: aleppoDocuments.length,
  iom_adopted_observations: 0,
  output_sha256: Object.fromEntries(Object.entries(outputs).map(([name, contents]) => [name, digest(contents)])),
  limitations: ['Only selected budget pages were content-checked',
    'No governorate plan, budget, implementation or evaluation is adopted',
    'No IOM value is adopted because extraction and redistribution require prior written permission',
    'No independent acceptance audit or public verification'],
};
await writeFile(path.join(outputDir, 'OUTPUT_VERIFICATION_NATIONAL_BUDGET.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({national_document_count: 1, aleppo_document_count: 0,
  iom_adopted_observations: 0, dataset_sha256: report.dataset_sha256}, null, 2));

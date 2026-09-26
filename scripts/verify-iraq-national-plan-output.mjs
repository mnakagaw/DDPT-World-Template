#!/usr/bin/env node
// Verify the plan is attributed only to the national territory in outputs.
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {planningHtml, documentsCsv} from '../scaffold/site/model.mjs';

const arg = process.argv.indexOf('--project');
if (arg < 0 || !process.argv[arg + 1] || process.argv.length !== 4) {
  throw new Error('Usage: node scripts/verify-iraq-national-plan-output.mjs --project <project>');
}
const project = path.resolve(process.argv[arg + 1]);
const bytes = await readFile(path.join(project, 'data/dashboard.json'));
const dataset = JSON.parse(bytes.toString('utf8'));
const source = dataset.sources.find(item => item.id === 'irq-mop-national-development-plan-2024-2028');
const document = dataset.documents.find(item => item.id === 'irq-national-development-plan-2024-2028');
if (dataset.country.id !== 'IRQ' || !source || !document || document.territory_id !== 'IRQ' ||
    document.availability !== 'content_verified' || document.official_status !== 'unverified') {
  throw new Error('Expected verified national-only Iraq plan document');
}
const digest = input => createHash('sha256').update(input).digest('hex');
if (digest(await readFile(path.join(project, source.raw_path))) !== source.sha256) {
  throw new Error('Official Ministry of Planning PDF bytes differ from receipt');
}
const baghdad = dataset.territories.find(item => item.name === 'Baghdad');
if (!baghdad) throw new Error('Baghdad territory missing');
const nationalDocuments = dataset.documents.filter(item => item.territory_id === 'IRQ');
const baghdadDocuments = dataset.documents.filter(item => item.territory_id === baghdad.id);
if (nationalDocuments.length !== 1 || baghdadDocuments.length !== 0) {
  throw new Error('The plan must be the only national document and no Baghdad document may be inferred');
}
const nationalHtml = planningHtml(dataset, 'IRQ', 'latest-available', 'en');
const baghdadHtml = planningHtml(dataset, baghdad.id, 'latest-available', 'en');
const nationalCsv = documentsCsv(dataset, 'IRQ');
const baghdadCsv = documentsCsv(dataset, baghdad.id);
for (const text of [document.title, source.url, '2024-2028', 'unverified']) {
  if (!nationalHtml.includes(text) || !nationalCsv.includes(text)) {
    throw new Error(`National planning output lacks ${text}`);
  }
}
if (baghdadHtml.includes(document.title) || baghdadCsv.includes(document.title) ||
    !baghdadHtml.includes('Baghdad')) {
  throw new Error('National plan leaked into Baghdad governorate output');
}
const output = path.join(project, 'evidence');
const files = {nationalHtml, baghdadHtml, nationalCsv, baghdadCsv};
for (const [name, contents] of Object.entries(files)) {
  await writeFile(path.join(output, `IRQ_NDP_${name}.txt`), contents);
}
const report = {status: 'partial_candidate_output_check', checked_at: new Date().toISOString(),
  dataset_sha256: digest(bytes), source_pdf_sha256: source.sha256,
  national_plan_document_id: document.id, national_document_count: nationalDocuments.length,
  baghdad_document_count: baghdadDocuments.length,
  output_sha256: Object.fromEntries(Object.entries(files).map(([name, contents]) => [name, digest(contents)])),
  limitations: ['Only PDF pages 1, 2 and 157 were content-checked',
    'No governorate plan, budget, implementation or evaluation adopted',
    'This is not an independent acceptance audit']};
await writeFile(path.join(output, 'OUTPUT_VERIFICATION_NATIONAL_PLAN.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({national_document_count: nationalDocuments.length,
  baghdad_document_count: baghdadDocuments.length,
  source_pdf_sha256: source.sha256}, null, 2));

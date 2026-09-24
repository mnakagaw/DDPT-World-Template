import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { diagnosticCsv, diagnosticHtml, diagnosticMarkdown } from '../../scaffold/site/diagnostic.mjs';

const project = path.resolve(process.argv[2] || 'generated/burkina-faso-20260924');
const dataset = JSON.parse(await readFile(path.join(project, 'data/dashboard.json'), 'utf8'));
assert.equal(dataset.country.id, 'BFA');
const national = dataset.territories.find(area => area.id === 'BFA');
const centre = dataset.territories.find(area => area.name === 'Centre' && area.level === 'adm1');
const kadiogo = dataset.territories.find(area => area.name === 'Kadiogo' && area.parent_id === centre?.id);
const commune = dataset.territories.find(area => area.name === 'Komki-Ipala' && area.parent_id === kadiogo?.id);
assert(national && centre && kadiogo && commune);

const observation = (area, indicator) => dataset.observations.find(row =>
  row.territory_id === area.id && row.indicator_id === indicator && row.status === 'observed');
assert.equal(observation(national, 'BFA_RGPH2019_POP_TOTAL')?.value, 20505155);
assert.equal(observation(national, 'BFA_INSD_POVERTY_INCIDENCE_MODEL')?.value, 39.3);

const cases = [
  { area: national, expectedChild: centre.name },
  { area: centre, expectedChild: kadiogo.name },
  { area: kadiogo, expectedChild: commune.name },
  { area: commune, expectedChild: null },
];
const results = [];
for (const { area, expectedChild } of cases) {
  const markdown = diagnosticMarkdown(dataset, area.id, 'latest-available');
  const html = diagnosticHtml(dataset, area.id, 'latest-available');
  const csv = diagnosticCsv(dataset, area.id, 'latest-available');
  const population = observation(area, 'BFA_RGPH2019_POP_TOTAL');
  assert(population, `missing population for ${area.name}`);
  assert(markdown.includes(`# Territorial diagnostic — ${area.name}`));
  assert(html.includes(`<h1>Territorial diagnostic — ${area.name}</h1>`));
  assert(csv.includes(area.id) && csv.includes('BFA_RGPH2019_POP_TOTAL'));
  assert(markdown.includes(population.value.toLocaleString('en-US')));
  assert(html.includes(population.value.toLocaleString('en-US')));
  assert(csv.includes(String(population.value)));
  assert(markdown.includes('microdata.insd.bf/index.php/catalog/69/download/270'));
  assert(!markdown.includes('undefined') && !html.includes('undefined') && !csv.includes('undefined'));
  if (expectedChild) {
    assert(markdown.includes(expectedChild) && csv.includes(expectedChild));
  } else {
    assert(markdown.includes('Internal comparison stops at this area'));
  }
  const poverty = observation(area, 'BFA_INSD_POVERTY_INCIDENCE_MODEL');
  if (poverty) {
    assert(markdown.includes('Estimated population below the monetary poverty line'));
    assert(markdown.includes('2018'));
  }
  results.push({
    territory_id: area.id, area: area.name, level: area.level,
    population_2019: population.value, poverty_model_2018: poverty?.value ?? null,
    markdown_bytes: Buffer.byteLength(markdown), html_bytes: Buffer.byteLength(html), csv_bytes: Buffer.byteLength(csv),
    expected_child_confirmed: expectedChild || null,
  });
}
const report = {
  checked_at: new Date().toISOString(),
  dataset_edition: dataset.generated_at,
  cases: results,
  checked: 'Generated Markdown, HTML and CSV against country, region, province and commune observations, source URL, source year and child scope. Not a visual print or DOCX audit.',
};
await writeFile(path.join(project, 'evidence/OUTPUT_QA.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

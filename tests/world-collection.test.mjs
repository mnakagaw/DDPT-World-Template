import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, writeFile, readdir, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { collectWorld, parseM49, buildWorldMembership, joinWorldBoundaries, WORLD_CONFIG } from '../lib/collect-world.mjs';
import { createWorld } from '../scripts/create-world.mjs';
import { validateDataset } from '../lib/validate.mjs';

const YEAR = new Date().getUTCFullYear();
const headers = ['Global Code', 'Global Name', 'Region Code', 'Region Name', 'Sub-region Code', 'Sub-region Name', 'Intermediate Region Code', 'Intermediate Region Name', 'Country or Area', 'M49 Code', 'ISO-alpha2 Code', 'ISO-alpha3 Code'];
const row = (id, iso2, m49, name, region, subregion = ['', ''], intermediate = ['', '']) => ['001', 'World', ...region, ...subregion, ...intermediate, name, m49, iso2, id];
const ROWS = [
  row('UGA', 'UG', '800', 'Uganda', ['002', 'Africa'], ['202', 'Sub-Saharan Africa'], ['014', 'Eastern Africa']),
  row('DOM', 'DO', '214', 'Dominican Republic', ['019', 'Americas'], ['419', 'Latin America and the Caribbean'], ['029', 'Caribbean']),
  row('MEX', 'MX', '484', 'Mexico', ['019', 'Americas'], ['419', 'Latin America and the Caribbean'], ['013', 'Central America']),
  row('USA', 'US', '840', 'United States of America', ['019', 'Americas'], ['021', 'Northern America']),
  row('CHL', 'CL', '152', 'Chile', ['019', 'Americas'], ['419', 'Latin America and the Caribbean'], ['005', 'South America']),
  row('JPN', 'JP', '392', 'Japan', ['142', 'Asia'], ['030', 'Eastern Asia']),
  row('FRA', 'FR', '250', 'France', ['150', 'Europe'], ['155', 'Western Europe']),
  row('FJI', 'FJ', '242', 'Fiji', ['009', 'Oceania'], ['054', 'Melanesia']),
  row('ATA', 'AQ', '010', 'Antarctica', ['', '']),
];
const html = (rows = ROWS) => `<table id = "downloadTableEN"><thead><tr>${headers.map(h => `<td>${h}</td>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const economy = r => ({ id: r[11], iso2Code: r[10], name: r[8], region: { id: 'XXX' } });
const WORLD = { id: 'WLD', iso2Code: '1W', name: 'World', region: { id: 'NA' } };
const EAP = { id: 'EAP', iso2Code: '4E', name: 'East Asia & Pacific', region: { id: 'NA' } };
const envelope = (rows, page = 1, pages = 1, total = rows.length) => [{ page, pages, total, lastupdated: '2026-07-01' }, rows];
const response = (value, init) => new Response(typeof value === 'string' ? value : JSON.stringify(value), init);
const obs = (indicator, id, value, period = String(YEAR - 1), iso2 = id === 'WLD' ? '1W' : ROWS.find(r => r[11] === id)?.[10] || '4E') => ({ indicator: { id: indicator }, countryiso3code: id, country: { id: iso2 }, date: period, value });
const shape = (id, m49, geometry = { type: 'Polygon', coordinates: [[[30, 0], [31, 0], [31, 1], [30, 0]]] }) => ({ type: 'Feature', properties: { ISO_A3: id, ISO_N3: m49, NAME: id, NE_ID: id }, geometry });
const boundary = () => ({ type: 'FeatureCollection', features: [shape('DOM', '214'), shape('UGA', '800'), shape('MEX', '484'), shape('FRA', '249')] });

function fixtureFetch(overrides = {}) {
  const requests = [];
  const fetchImpl = async (address, options) => {
    const url = new URL(address); requests.push(url.href);
    assert.equal(options.redirect, 'manual'); assert.ok(options.signal instanceof AbortSignal);
    if (url.hostname === 'unstats.un.org') return response(overrides.html ?? html());
    if (url.hostname === 'raw.githubusercontent.com') return overrides.boundaries?.(url) ?? response(boundary());
    if (url.pathname === '/v2/country') return overrides.directory?.(url) ?? response(envelope([WORLD, EAP, ...ROWS.filter(r => r[11] !== 'ATA').map(economy)]));
    const id = url.pathname.split('/').at(-1), page = Number(url.searchParams.get('page'));
    if (url.pathname.startsWith('/v2/indicator/')) return response(envelope([{ id, name: `Fixture ${id}`, source: { id: '2' }, sourceNote: `Definition ${id}`, sourceOrganization: 'Fixture original organization', unit: '' }]));
    assert.equal(url.pathname, `/v2/country/all/indicator/${id}`);
    if (overrides.values) return overrides.values(id, url);
    const rows = [obs(id, 'WLD', 100), obs(id, 'UGA', 0), obs(id, 'DOM', null), obs(id, 'EAP', 999), obs(id, 'MEX', 12, String(YEAR - 2))];
    return response(page === 1 ? envelope(rows.slice(0, 3), 1, 2, 5) : envelope(rows.slice(3), 2, 2, 5));
  };
  return { fetchImpl, requests };
}
async function temp(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ddpt-world-'));
  t.after(() => rm(root, { recursive: true, force: true })); return root;
}

test('M49 derives five continents, one parent per country, custom Mexico-inclusive region and original hierarchy', () => {
  const countries = parseM49(html()), { territories, analysis } = buildWorldMembership(countries);
  const find = id => territories.find(t => t.id === id);
  assert.equal(territories.filter(t => t.level === 'continent').length, 5);
  assert.equal(find('DOM').parent_id, 'CUSTOM:CAM-CAR'); assert.equal(find('MEX').parent_id, 'CUSTOM:CAM-CAR');
  assert.equal(find('CUSTOM:CAM-CAR').parent_id, 'M49:019');
  assert.equal(find('DOM').m49_membership.intermediate.code, '029'); assert.equal(find('DOM').m49_membership.subregion.code, '419');
  assert.equal(find('ATA').parent_id, 'WLD'); assert.equal(find('UGA').parent_id, 'M49:014');
  assert.equal(find('M49:005').parent_id, 'M49:019'); assert.equal(find('M49:419'), undefined);
  assert.deepEqual(analysis.comparisons.find(c => c.parent_id === 'CUSTOM:CAM-CAR').member_ids, ['DOM', 'MEX']);
  assert.equal(new Set(territories.map(t => t.id)).size, territories.length);
  assert.match(find('CUSTOM:CAM-CAR').membership_note, /not a published UN M49/);
});

test('changed headers, duplicate country IDs/codes and ambiguous group membership fail instead of inferred joins', () => {
  assert.throws(() => parseM49(html().replace('ISO-alpha3 Code', 'Unknown header')), /headers changed/);
  assert.throws(() => parseM49(html([...ROWS, ROWS[0]])), /duplicate/);
  const countries = parseM49(html()); countries[1].region.name = 'Other Americas';
  assert.throws(() => buildWorldMembership(countries), /Ambiguous/);
});

test('paged official values preserve null and zero, do not propagate or average, and archive exact bytes', async t => {
  const root = await temp(t), rawDir = path.join(root, 'raw'), mock = fixtureFetch();
  const data = await collectWorld({ rawDir, fetchImpl: mock.fetchImpl, startYear: YEAR - 2, endYear: YEAR });
  assert.deepEqual(validateDataset(data).errors, []);
  const observations = data.observations.filter(o => o.indicator_id === 'SP.POP.TOTL');
  assert.equal(observations.find(o => o.territory_id === 'UGA').value, 0);
  assert.equal(observations.find(o => o.territory_id === 'UGA').status, 'observed');
  assert.equal(observations.find(o => o.territory_id === 'DOM').value, null);
  assert.equal(observations.find(o => o.territory_id === 'DOM').status, 'missing');
  assert.ok(observations.filter(o => o.territory_id === 'M49:002' || o.territory_id === 'CUSTOM:CAM-CAR').every(o => o.value === null));
  assert.ok(!observations.some(o => o.territory_id === 'EAP'));
  assert.ok(!observations.some(o => o.territory_id === 'JPN')); // no inherited World value
  assert.equal(observations.find(o => o.territory_id === 'WLD').value, 100);
  assert.ok(mock.requests.some(url => url.includes('page=2')));
  const receipt = JSON.parse(await readFile(path.join(rawDir, 'wb-data-SP.POP.TOTL-page-2.receipt.json')));
  const original = await readFile(path.join(rawDir, 'wb-data-SP.POP.TOTL-page-2.json'));
  assert.equal(receipt.sha256, createHash('sha256').update(original).digest('hex'));
  assert.ok(data.indicators.every(i => i.aggregation === 'official_only' && i.definition.startsWith('Definition ')));
  assert.ok(data.sources.find(s => s.id === 'wb-SP.POP.TOTL').raw_files.length === 3);
  assert.equal(data.boundaries.features.find(f => f.properties.territory_id === 'M49:019').geometry.type, 'MultiPolygon');
});

test('boundary ISO plus numeric match rejects aliases, wrong extent code and duplicates; groups use available same-edition shapes only', () => {
  const { territories, analysis } = buildWorldMembership(parseM49(html()));
  const shapes = boundary(); shapes.features.push(shape('-99', '826')); shapes.features.push(shape('DOM', '214'));
  const joined = joinWorldBoundaries(shapes, territories, analysis.comparisons);
  assert.ok(joined.unmapped_country_ids.includes('DOM')); assert.ok(joined.unmapped_country_ids.includes('FRA'));
  assert.ok(!joined.features.some(f => f.properties.territory_id === 'DOM' || f.properties.territory_id === 'FRA'));
  const group = joined.features.find(f => f.properties.territory_id === 'CUSTOM:CAM-CAR');
  assert.deepEqual(group.properties.mapped_member_ids, ['MEX']); assert.deepEqual(group.properties.omitted_member_ids, ['DOM']);
  assert.equal(group.properties.display_only, true); assert.equal(group.properties.geometry_edition, WORLD_CONFIG.boundary.commit);
  assert.equal(group.properties.boundary_version, undefined); assert.equal(territories.find(t => t.id === 'MEX').boundary_version, null);
});

test('invalid values and later-page/source failures remain scoped gaps while other indicators survive', async t => {
  const root = await temp(t), mock = fixtureFetch({
    values: (id, url) => {
      if (id === 'SP.POP.TOTL') return Number(url.searchParams.get('page')) === 1 ? response(envelope([obs(id, 'UGA', 7)], 1, 2, 2)) : response('not json', { status: 500 });
      if (id === 'SP.DYN.LE00.IN') return response(envelope([obs(id, 'DOM', '99'), obs(id, 'UGA', 2, 'bogus'), obs(id, 'UGA', 3), obs(id, 'UGA', 900)]));
      return response(envelope([obs(id, 'WLD', 4)]));
    }, boundaries: () => response({ error: 'missing' }, { status: 503 }),
  });
  const data = await collectWorld({ rawDir: path.join(root, 'raw'), fetchImpl: mock.fetchImpl });
  assert.deepEqual(validateDataset(data).errors, []);
  assert.equal(data.sources.find(s => s.id === 'wb-SP.POP.TOTL').status, 'partial');
  assert.equal(data.sources.find(s => s.id === 'natural-earth').status, 'failed');
  assert.equal(data.boundaries.features.length, 0);
  assert.ok(data.gaps.some(g => g.category === 'source_collection' && g.detail.includes('500')));
  assert.equal(data.observations.find(o => o.indicator_id === 'SP.POP.TOTL' && o.territory_id === 'UGA').value, 7);
  assert.ok(!data.observations.some(o => o.value === '99' || o.period === 'bogus' || o.value === 900));
  const failed = JSON.parse(await readFile(path.join(root, 'raw/wb-data-SP.POP.TOTL-page-2.receipt.json')));
  assert.equal(failed.status, 'failed'); assert.ok(failed.sha256);
});

test('incomplete country directory and incomplete M49 continental registry fail the collection', async t => {
  const root = await temp(t);
  await assert.rejects(collectWorld({ rawDir: path.join(root, 'one'), fetchImpl: fixtureFetch({ directory: () => response(envelope([WORLD], 1, 1, 2)) }).fetchImpl }), /directory incomplete/);
  await assert.rejects(collectWorld({ rawDir: path.join(root, 'two'), fetchImpl: fixtureFetch({ html: html(ROWS.filter(r => r[2] !== '009')) }).fetchImpl }), /missing one of the five/);
});

test('offline replay reproduces the dataset without fetch, detects altered originals and different year requests', async t => {
  const root = await temp(t), sourceDir = path.join(root, 'original');
  const data = await collectWorld({ rawDir: sourceDir, fetchImpl: fixtureFetch().fetchImpl });
  const offline = () => { throw new Error('Network must never run during replay.'); };
  const replay = await collectWorld({ rawDir: path.join(root, 'replay'), sourceDir, fetchImpl: offline });
  assert.deepEqual(replay, data);
  await assert.rejects(collectWorld({ rawDir: path.join(root, 'wrong-period'), sourceDir, fetchImpl: offline, startYear: YEAR - 2 }), /Invalid replay receipt/);
  await writeFile(path.join(sourceDir, 'natural-earth-map-units.json'), '{}');
  await assert.rejects(collectWorld({ rawDir: path.join(root, 'tamper'), sourceDir, fetchImpl: offline }), /Replay SHA\/size mismatch/);
});

test('world CLI refuses existing output before collecting and retains raw evidence on failure', async t => {
  const root = await temp(t); let called = false;
  await assert.rejects(createWorld({ out: root, collect: async () => { called = true; } }), /already exists/);
  assert.equal(called, false);
  const out = path.join(root, 'failed');
  await assert.rejects(createWorld({ out, collect: async ({ rawDir }) => { await writeFile(path.join(rawDir, 'evidence.json'), '{}'); throw new Error('Fixture source failed'); } }), /Fixture source failed/);
  assert.ok((await readdir(out)).includes('COLLECTION_FAILED.txt'));
  assert.equal(await readFile(path.join(out, 'raw/evidence.json'), 'utf8'), '{}');
});

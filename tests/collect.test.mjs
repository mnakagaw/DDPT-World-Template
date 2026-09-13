import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { collectCountry, resolveCountryName, WDI_INDICATORS } from '../lib/collect.mjs';

const YEAR = new Date().getUTCFullYear();
const UGANDA = { id: 'UGA', iso2Code: 'UG', name: 'Uganda', region: { id: 'SSF', value: 'Sub-Saharan Africa' } };
const KENYA = { id: 'KEN', iso2Code: 'KE', name: 'Kenya', region: { id: 'SSF', value: 'Sub-Saharan Africa' } };
const WORLD = { id: 'WLD', iso2Code: '1W', name: 'World', region: { id: 'NA', value: 'Aggregates' } };
const geometryUrl = 'https://raw.githubusercontent.com/wmgeolab/geoBoundaries/test/releaseData/gbOpen/UGA/ADM1/geoBoundaries-UGA-ADM1_simplified.geojson';
const metadata = { boundaryID: 'UGA-ADM1-fixture', boundaryName: 'Uganda', boundaryISO: 'UGA', boundaryType: 'ADM1',
  boundaryYearRepresented: '2017', boundaryCanonical: 'Unknown', boundarySource: 'Fixture source',
  boundaryLicense: 'Open Data Commons Open Database License 1.0', licenseSource: 'https://example.org/fixture-license',
  simplifiedGeometryGeoJSON: geometryUrl, admUnitCount: '2' };
const shape = (code) => ({ type: 'Feature', properties: { shapeID: code, shapeName: 'Same name', shapeGroup: 'UGA', shapeType: 'ADM1' },
  geometry: { type: 'Polygon', coordinates: [[[30, 0], [31, 0], [31, 1], [30, 0]]] } });

const envelope = (rows, { page = 1, pages = 1, total = rows?.length || 0 } = {}) => [{ page, pages, total, per_page: 400, lastupdated: '2026-01-01' }, rows];
const json = (value, options) => new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' }, ...options });
const observation = (id, value = 25, year = YEAR - 1) => ({ indicator: { id, value: `Fixture ${id}` }, country: { id: 'UG', value: 'Uganda' },
  countryiso3code: 'UGA', date: String(year), value, unit: '', obs_status: '', decimal: 0 });

function fixtureFetch(overrides = {}) {
  const requests = [];
  const fn = async (address, options) => {
    const url = new URL(address);
    requests.push(url);
    assert.equal(options.redirect, 'manual');
    assert.ok(options.signal instanceof AbortSignal);
    if (url.hostname === 'api.worldbank.org') {
      if (url.pathname === '/v2/country') {
        if (overrides.countries) return overrides.countries(url);
        return json(envelope([WORLD, UGANDA, KENYA]));
      }
      if (url.pathname.startsWith('/v2/indicator/')) {
        const id = url.pathname.split('/').at(-1);
        assert.equal(url.searchParams.get('source'), '2');
        if (overrides.indicatorMetadata) {
          const response = await overrides.indicatorMetadata(id, url);
          if (response) return response;
        }
        return json(envelope([{ id, name: `Fixture ${id}`, source: { id: '2', value: 'World Development Indicators' },
          unit: '', sourceNote: `Verified fixture definition for ${id}.`, sourceOrganization: 'Fixture national organization — café' }]));
      }
      const id = url.pathname.split('/').at(-1);
      assert.equal(url.searchParams.get('source'), '2');
      assert.equal(url.searchParams.get('date'), `2000:${YEAR}`);
      assert.equal(url.searchParams.has('gapfill'), false);
      if (overrides.series) {
        const response = await overrides.series(id, url);
        if (response) return response;
      }
      return json(envelope([observation(id)]));
    }
    if (url.hostname === 'www.geoboundaries.org') return overrides.boundaryMetadata ? overrides.boundaryMetadata(url) : json(metadata);
    if (url.href === geometryUrl) return overrides.geometry ? overrides.geometry(url) : json({ type: 'FeatureCollection', features: [shape('provider-1'), shape('provider-2')] });
    throw new Error(`Unexpected request: ${url.href}`);
  };
  fn.requests = requests;
  return fn;
}

async function rawDirectory(t) {
  const parent = await mkdtemp(path.join(os.tmpdir(), 'ddpt-collector-test-'));
  t.after(() => rm(parent, { recursive: true, force: true }));
  return path.join(parent, 'raw');
}

test('country resolution accepts live-directory English, ISO and Japanese names; rejects aggregates and ambiguity', () => {
  const congo = { id: 'COG', iso2Code: 'CG', name: 'Congo, Rep.', region: { id: 'SSF' } };
  const drc = { id: 'COD', iso2Code: 'CD', name: 'Congo, Dem. Rep.', region: { id: 'SSF' } };
  const economies = [WORLD, UGANDA, KENYA, congo, drc];
  for (const name of ['UGA', 'ug', ' Uganda ', 'ウガンダ']) assert.equal(resolveCountryName(name, economies).id, 'UGA');
  assert.equal(resolveCountryName('ケニア', economies).id, 'KEN');
  assert.throws(() => resolveCountryName('Congo', economies), /Ambiguous.*COG.*COD/);
  assert.throws(() => resolveCountryName('World', economies), /aggregate/);
  assert.throws(() => resolveCountryName('WLD', economies), /aggregate/);
  assert.throws(() => resolveCountryName('Ugan', economies), /not resolved/);
  assert.throws(() => resolveCountryName('not a country', economies), /not resolved/);
  assert.throws(() => resolveCountryName('', economies), /non-empty/);
});

test('follows both country and series pagination, preserves zero/null and archives original UTF-8 hashes', async (t) => {
  const rawDir = await rawDirectory(t);
  const populationPayload = `  ${JSON.stringify(envelope([observation('SP.POP.TOTL', 0)], { page: 1, pages: 2, total: 2 }))}\n`;
  const fetchImpl = fixtureFetch({
    countries: (url) => Number(url.searchParams.get('page')) === 1
      ? json(envelope([WORLD, KENYA], { pages: 2, total: 3 })) : json(envelope([UGANDA], { page: 2, pages: 2, total: 3 })),
    series: (id, url) => {
      if (id !== 'SP.POP.TOTL') return null;
      return Number(url.searchParams.get('page')) === 1 ? new Response(populationPayload)
        : json(envelope([observation(id, null, YEAR)], { page: 2, pages: 2, total: 2 }));
    },
  });
  const progress = [];
  const data = await collectCountry({ country: 'ウガンダ', rawDir, fetchImpl, onProgress: (message) => progress.push(message) });
  assert.equal(data.schema_version, '0.2');
  assert.equal(data.country.id, 'UGA');
  assert.equal(data.country.requested_name, 'ウガンダ');
  assert.equal(data.indicators.length, WDI_INDICATORS.length);
  const values = data.observations.filter((item) => item.indicator_id === 'SP.POP.TOTL');
  assert.deepEqual(values.map(({ value, status }) => ({ value, status })), [{ value: 0, status: 'observed' }, { value: null, status: 'missing' }]);
  assert.equal(values.length, 2, 'Omitted years must not be filled with zeros or national averages');
  const source = data.sources.find((item) => item.id === 'wb-SP.POP.TOTL');
  assert.equal(source.status, 'ready');
  assert.equal(source.geographic_level, 'national');
  assert.equal(source.raw_files.length, 3, 'Two data pages and one metadata page are retained');
  const primaryBytes = await readFile(path.join(path.dirname(rawDir), source.raw_path));
  assert.equal(primaryBytes.toString('utf8'), populationPayload);
  assert.equal(source.sha256, createHash('sha256').update(primaryBytes).digest('hex'));
  assert.match(source.source_organization, /café/);
  const receipt = JSON.parse(await readFile(path.join(rawDir, 'collection-receipt.json'), 'utf8'));
  assert.ok(receipt.requests.every((item) => item.retrieved_at && item.receipt_path));
  assert.ok(progress.length > 2);
  assert.equal(fetchImpl.requests.filter((url) => url.pathname === '/v2/country').length, 2);
});

test('reference shapes carry provider codes, actual license/year and national membership without copying statistics', async (t) => {
  const data = await collectCountry({ country: 'UGA', rawDir: await rawDirectory(t), fetchImpl: fixtureFetch() });
  const local = data.territories.filter((item) => item.level !== 'national');
  assert.equal(local.length, 2, 'Same names do not merge distinct provider units');
  assert.notEqual(local[0].id, local[1].id);
  assert.ok(local.every((item) => item.official_code === null && item.parent_id === 'UGA' && item.boundary_year === '2017'));
  assert.ok(local.every((item) => /provider/.test(item.code_system) && /pending/.test(item.reconciliation_status)));
  assert.ok(data.observations.every((item) => item.territory_id === 'UGA'));
  assert.ok(data.boundaries.features.every((item) => local.some((territory) => territory.id === item.properties.territory_id)));
  const source = data.sources.find((item) => item.id === 'geoboundaries-adm1');
  assert.equal(source.license, metadata.boundaryLicense, 'gbOpen is not relabeled as universally CC-BY');
  assert.equal(source.reference_period, '2017');
  assert.match(data.country.geography_note, /unresolved official-code/);
  assert.ok(data.gaps.some((item) => item.category === 'boundary_reconciliation'));
  assert.ok(data.gaps.some((item) => item.category === 'subnational_statistics'));
  assert.deepEqual(data.documents, []);
  assert.equal(data.collection.status, 'partial');
});

test('a later data page failure preserves earlier valid values and records failure evidence', async (t) => {
  const rawDir = await rawDirectory(t);
  const fetchImpl = fixtureFetch({ series: (id, url) => id !== 'SP.POP.TOTL' ? null : Number(url.searchParams.get('page')) === 1
    ? json(envelope([observation(id, 100)], { pages: 2, total: 2 })) : new Response('temporarily unavailable', { status: 503 }) });
  const data = await collectCountry({ country: 'Uganda', rawDir, fetchImpl });
  assert.equal(data.sources.find((item) => item.id === 'wb-SP.POP.TOTL').status, 'partial');
  assert.equal(data.observations.find((item) => item.indicator_id === 'SP.POP.TOTL').value, 100);
  assert.ok(data.observations.some((item) => item.indicator_id === 'SP.POP.GROW'));
  assert.ok(data.gaps.some((item) => item.source_id === 'wb-SP.POP.TOTL' && /503/.test(item.detail)));
  const receipt = JSON.parse(await readFile(path.join(rawDir, 'wb-data-SP.POP.TOTL-page-2.receipt.json'), 'utf8'));
  assert.equal(receipt.status, 'failed');
  assert.equal(receipt.http_status, 503);
  assert.match(receipt.sha256, /^[a-f0-9]{64}$/);
  assert.equal(await readFile(path.join(path.dirname(rawDir), receipt.raw_path), 'utf8'), 'temporarily unavailable');
});

test('wrong country, wrong indicator, numeric strings and duplicate observations are rejected, without numeric coercion', async (t) => {
  const fetchImpl = fixtureFetch({ series: (id) => id === 'SP.POP.TOTL' ? json(envelope([
    observation(id, 0), observation(id, 99),
    { ...observation(id, 20, YEAR - 2), countryiso3code: 'KEN' },
    observation('SP.POP.GROW', 30, YEAR - 3),
    observation(id, '0', YEAR - 4), observation(id, null, YEAR - 5),
  ])) : null });
  const data = await collectCountry({ country: 'UG', rawDir: await rawDirectory(t), fetchImpl });
  const values = data.observations.filter((item) => item.indicator_id === 'SP.POP.TOTL');
  assert.equal(values.length, 2);
  assert.ok(values.some((item) => item.value === 0 && item.status === 'observed'));
  assert.ok(values.some((item) => item.value === null && item.status === 'missing'));
  assert.equal(data.sources.find((item) => item.id === 'wb-SP.POP.TOTL').status, 'partial');
  assert.ok(data.gaps.some((item) => /Rejected an invalid/.test(item.detail)));
});

test('invalid metadata JSON and unavailable boundaries leave a useful national-only partial dataset', async (t) => {
  const rawDir = await rawDirectory(t);
  const fetchImpl = fixtureFetch({ indicatorMetadata: (id) => id === 'SP.POP.TOTL' ? new Response('{broken JSON') : null,
    boundaryMetadata: () => new Response('not found', { status: 404 }) });
  const data = await collectCountry({ country: 'Uganda', rawDir, fetchImpl });
  assert.equal(data.territories.length, 1);
  assert.equal(data.boundaries.features.length, 0);
  assert.ok(data.observations.length > 0);
  assert.equal(data.indicators.find((item) => item.id === 'SP.POP.TOTL').metadata_status, 'failed');
  assert.equal(data.sources.find((item) => item.id === 'wb-SP.POP.TOTL').status, 'partial');
  assert.equal(data.sources.find((item) => item.id === 'geoboundaries-adm1').status, 'failed');
  assert.ok(data.gaps.some((item) => item.category === 'boundaries' && /404/.test(item.detail)));
  assert.ok((await readdir(rawDir)).includes('wb-metadata-SP.POP.TOTL-page-1.receipt.json'));
});

test('unresolved countries and incomplete country directories fail before statistics collection', async (t) => {
  const unresolved = fixtureFetch();
  await assert.rejects(collectCountry({ country: 'Atlantis', rawDir: await rawDirectory(t), fetchImpl: unresolved }), /not resolved/);
  assert.ok(unresolved.requests.every((url) => url.pathname === '/v2/country'));
  const incomplete = fixtureFetch({ countries: (url) => Number(url.searchParams.get('page')) === 1
    ? json(envelope([UGANDA], { pages: 2, total: 2 })) : json([{ page: 1, pages: 2, total: 2 }, [KENYA]]) });
  await assert.rejects(collectCountry({ country: 'Uganda', rawDir: await rawDirectory(t), fetchImpl: incomplete }), /directory.*completely.*pagination/);
  assert.ok(incomplete.requests.every((url) => url.pathname === '/v2/country'));
});

test('rejects boundary metadata URL escape, oversized downloads and mismatched features', async (t) => {
  const blocked = fixtureFetch({ boundaryMetadata: () => json({ ...metadata, simplifiedGeometryGeoJSON: 'http://127.0.0.1/private' }) });
  const first = await collectCountry({ country: 'UGA', rawDir: await rawDirectory(t), fetchImpl: blocked });
  assert.equal(first.boundaries.features.length, 0);
  assert.ok(blocked.requests.every((url) => url.hostname !== '127.0.0.1'));
  const oversized = fixtureFetch({ geometry: () => new Response('{}', { headers: { 'content-length': String(21 * 1024 * 1024) } }) });
  const second = await collectCountry({ country: 'UGA', rawDir: await rawDirectory(t), fetchImpl: oversized });
  assert.equal(second.boundaries.features.length, 0);
  assert.ok(second.gaps.some((item) => /byte collection limit/.test(item.detail)));
  const mismatched = fixtureFetch({ geometry: () => json({ type: 'FeatureCollection', features: [shape('okay'), { ...shape('bad'), properties: { ...shape('bad').properties, shapeGroup: 'KEN' } }] }) });
  const third = await collectCountry({ country: 'UGA', rawDir: await rawDirectory(t), fetchImpl: mismatched });
  assert.equal(third.territories.length, 1, 'A partially validated layer must not escape on failure');
  assert.equal(third.boundaries.features.length, 0);
});

test('an empty WDI response records unavailable rather than fabricating a zero value', async (t) => {
  const fetchImpl = fixtureFetch({ series: (id) => id === 'SE.SEC.ENRR' ? json(envelope(null, { pages: 0, total: 0 })) : null });
  const data = await collectCountry({ country: 'UG', rawDir: await rawDirectory(t), fetchImpl });
  assert.equal(data.sources.find((item) => item.id === 'wb-SE.SEC.ENRR').status, 'unavailable');
  assert.equal(data.observations.filter((item) => item.indicator_id === 'SE.SEC.ENRR').length, 0);
});

test('retries a transient source failure once and preserves the failed-attempt receipt', async (t) => {
  const rawDir = await rawDirectory(t);
  let populationAttempts = 0;
  const fetchImpl = fixtureFetch({ series: (id) => {
    if (id !== 'SP.POP.TOTL') return null;
    populationAttempts += 1;
    return populationAttempts === 1 ? new Response('try again', { status: 503 }) : json(envelope([observation(id, 123)]));
  } });
  const data = await collectCountry({ country: 'UGA', rawDir, fetchImpl });
  assert.equal(populationAttempts, 2);
  const source = data.sources.find((item) => item.id === 'wb-SP.POP.TOTL');
  assert.equal(source.status, 'ready');
  assert.equal(data.observations.find((item) => item.indicator_id === 'SP.POP.TOTL').value, 123);
  assert.ok(source.raw_files.some((item) => item.status === 'failed'));
  assert.ok(source.raw_files.some((item) => item.raw_path?.endsWith('attempt-2.json')));
  assert.match(source.raw_path, /attempt-2\.json$/);
  assert.equal(JSON.parse(await readFile(path.join(rawDir, 'wb-data-SP.POP.TOTL-page-1.receipt.json'), 'utf8')).http_status, 503);
});

test('raw evidence is never overwritten when an archive path is reused', async (t) => {
  const rawDir = await rawDirectory(t);
  await collectCountry({ country: 'Uganda', rawDir, fetchImpl: fixtureFetch() });
  const original = await readFile(path.join(rawDir, 'world-bank-countries-page-1.json'));
  await assert.rejects(collectCountry({ country: 'Uganda', rawDir, fetchImpl: fixtureFetch() }), /EEXIST/);
  assert.deepEqual(await readFile(path.join(rawDir, 'world-bank-countries-page-1.json')), original);
});

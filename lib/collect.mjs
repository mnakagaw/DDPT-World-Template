import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

// API contracts verified against these primary sources on 2026-09-13:
// https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
// https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries
// https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries
// https://www.geoboundaries.org/api.html
const WB = 'https://api.worldbank.org/v2';
const WB_LICENSE = 'https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets';
const START_YEAR = 2000;
const MAX_JSON_BYTES = 4 * 1024 * 1024;
const MAX_BOUNDARY_BYTES = 20 * 1024 * 1024;
const REQUEST_TIMEOUT_MS = 25_000;

async function writeArchive(filename, data) {
  try { await writeFile(filename, data, { flag: 'wx' }); }
  catch (error) { error.archive_failure = true; throw error; }
}

// WDI often leaves the API's unit field empty. These explicit display units are
// tied to indicator definitions, never inferred from the magnitude of a value.
export const WDI_INDICATORS = Object.freeze([
  { id: 'SP.POP.TOTL', theme: 'Population', unit: 'people' },
  { id: 'SP.POP.GROW', theme: 'Population', unit: 'annual %' },
  { id: 'SP.URB.TOTL.IN.ZS', theme: 'Population', unit: '% of total population' },
  { id: 'SH.H2O.BASW.ZS', theme: 'Living conditions', unit: '% of population' },
  { id: 'SH.STA.BASS.ZS', theme: 'Living conditions', unit: '% of population' },
  { id: 'EG.ELC.ACCS.ZS', theme: 'Living conditions', unit: '% of population' },
  { id: 'SE.PRM.ENRR', theme: 'Education', unit: '% gross enrollment' },
  { id: 'SE.SEC.ENRR', theme: 'Education', unit: '% gross enrollment' },
  { id: 'SP.DYN.LE00.IN', theme: 'Health', unit: 'years' },
  { id: 'SH.DYN.MORT', theme: 'Health', unit: 'deaths per 1,000 live births' },
  { id: 'IT.NET.USER.ZS', theme: 'Connectivity', unit: '% of population' },
  { id: 'SL.UEM.TOTL.ZS', theme: 'Employment', unit: '% of total labor force (modeled ILO estimate)' },
].map(Object.freeze));

function normalName(value) {
  return String(value).normalize('NFKD').replace(/\p{M}/gu, '')
    .toLocaleLowerCase('en').replace(/[\p{P}\p{Z}\s]/gu, '');
}

function aliases(economy) {
  const names = [economy.id, economy.iso2Code, economy.name];
  for (const locale of ['en', 'ja']) {
    try {
      const value = new Intl.DisplayNames([locale], { type: 'region', fallback: 'none' }).of(economy.iso2Code);
      if (value) names.push(value);
    } catch { /* Some World Bank economy codes are not ISO codes. */ }
  }
  return names.map(normalName);
}

/** Resolve exact English/ISO/Intl Japanese aliases; never silently fuzzy-match. */
export function resolveCountryName(requested, economies) {
  if (typeof requested !== 'string' || !requested.trim() || requested.length > 160) {
    throw new Error('Country must be a non-empty name or ISO code (at most 160 characters).');
  }
  const query = normalName(requested);
  if (!query) throw new Error('Country name contains no searchable characters.');
  const valid = economies.filter((entry) => entry && /^[A-Z0-9]{3}$/.test(entry.id)
    && /^[A-Z]{2}$/.test(entry.iso2Code) && typeof entry.name === 'string'
    && entry.region?.id && entry.region.id !== 'NA' && entry.region.value !== 'Aggregates');
  const exact = valid.filter((entry) => aliases(entry).includes(query));
  if (exact.length === 1) return exact[0];
  const candidates = exact.length ? exact : valid.filter((entry) => aliases(entry).some((name) => name.includes(query)));
  if (candidates.length > 1) {
    throw new Error(`Ambiguous country "${requested}". Use an exact name or code: ${candidates.slice(0, 12).map((item) => `${item.name} (${item.id})`).join(', ')}.`);
  }
  const aggregate = economies.find((entry) => entry?.region?.id === 'NA'
    && [entry.id, entry.iso2Code, entry.name].some((name) => name && normalName(name) === query));
  if (aggregate) throw new Error(`"${requested}" is a World Bank aggregate, not an individual economy.`);
  throw new Error(`Country "${requested}" was not resolved. Use its exact English/Japanese name or ISO code.${candidates.length ? ` Possible exact name: ${candidates[0].name} (${candidates[0].id}).` : ''}`);
}

function checkedUrl(value) {
  const url = new URL(value);
  const host = url.hostname.toLowerCase();
  const api = host === 'api.worldbank.org' && url.pathname.startsWith('/v2/');
  const gb = ['www.geoboundaries.org', 'geoboundaries.org'].includes(host);
  const github = ['github.com', 'raw.githubusercontent.com', 'media.githubusercontent.com'].includes(host)
    && /^\/(?:media\/)?wmgeolab\/geoBoundaries\//i.test(url.pathname);
  if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443') || !(api || gb || github)) {
    throw new Error('Source URL is outside the approved public World Bank / geoBoundaries hosts.');
  }
  return url.href;
}

async function download(url, fetchImpl, signal, maxBytes) {
  let target = checkedUrl(url);
  for (let redirect = 0; redirect <= 5; redirect += 1) {
    const response = await fetchImpl(target, { signal, redirect: 'manual', headers: { Accept: 'application/json, application/geo+json' } });
    if (!response || typeof response.status !== 'number' || !response.headers?.get) throw new Error('Invalid fetch response.');
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      await response.body?.cancel();
      const location = response.headers.get('location');
      if (!location) throw new Error('Redirect did not provide a location.');
      target = checkedUrl(new URL(location, target).href);
      continue;
    }
    if (response.url) checkedUrl(response.url);
    const declared = Number(response.headers.get('content-length'));
    if (Number.isFinite(declared) && declared > maxBytes) {
      await response.body?.cancel();
      throw new Error(`Response exceeds the ${maxBytes}-byte collection limit.`);
    }
    const chunks = [];
    let size = 0;
    if (response.body?.getReader) {
      const reader = response.body.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > maxBytes) throw new Error(`Response exceeds the ${maxBytes}-byte collection limit.`);
          chunks.push(Buffer.from(value));
        }
      } catch (error) {
        await reader.cancel().catch(() => {});
        throw error;
      } finally { reader.releaseLock(); }
    } else if (response.body === null) {
      // A genuinely empty response is later rejected as invalid JSON.
    } else {
      throw new Error('Response body must support bounded streaming.');
    }
    return { response, bytes: Buffer.concat(chunks), finalUrl: response.url || target };
  }
  throw new Error('Too many source redirects.');
}

class RawArchive {
  constructor(rawDir, fetchImpl) {
    this.dir = path.resolve(rawDir);
    this.fetchImpl = fetchImpl;
    this.receipts = [];
  }

  async json(url, key, maxBytes = MAX_JSON_BYTES) {
    const attempts = [];
    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try {
        const result = await this.request(url, attempt === 1 ? key : `${key}-attempt-${attempt}`, maxBytes);
        return { ...result, receipts: [...attempts, result.receipt] };
      } catch (error) {
        if (error.archive_failure) throw error;
        if (error.receipt) attempts.push(error.receipt);
        error.receipts = attempts;
        if (attempt === 2 || !error.retryable) throw error;
        await new Promise((resolve) => setTimeout(resolve, 350));
      }
    }
  }

  async request(url, key, maxBytes = MAX_JSON_BYTES) {
    const controller = new AbortController();
    let timer;
    const record = { url, requested_at: new Date().toISOString(), retrieved_at: null, status: 'failed', http_status: null, raw_path: null, sha256: null, bytes: 0 };
    const filename = `${key}.json`;
    const receiptName = `${key}.receipt.json`;
    let value;
    let failure;
    try {
      const result = await Promise.race([
        download(url, this.fetchImpl, controller.signal, maxBytes),
        new Promise((_, reject) => {
          timer = setTimeout(() => { controller.abort(); reject(new Error(`Source request timed out after ${REQUEST_TIMEOUT_MS} ms.`)); }, REQUEST_TIMEOUT_MS);
        }),
      ]);
      record.retrieved_at = new Date().toISOString();
      record.http_status = result.response.status;
      record.final_url = result.finalUrl;
      record.bytes = result.bytes.byteLength;
      record.sha256 = createHash('sha256').update(result.bytes).digest('hex');
      record.raw_path = `raw/${filename}`;
      await writeArchive(path.join(this.dir, filename), result.bytes);
      if (result.response.status < 200 || result.response.status >= 300) throw new Error(`HTTP ${result.response.status}`);
      const text = new TextDecoder('utf-8', { fatal: true }).decode(result.bytes);
      try { value = JSON.parse(text); } catch { throw new Error('Source response is not valid JSON.'); }
      record.status = 'downloaded';
    } catch (error) {
      failure = error;
      record.error = error.message;
      record.retrieved_at ||= new Date().toISOString();
    } finally { clearTimeout(timer); controller.abort(); }
    record.receipt_path = `raw/${receiptName}`;
    // IO failures are fatal: a run without a reproducible raw archive is invalid.
    await writeArchive(path.join(this.dir, receiptName), `${JSON.stringify(record, null, 2)}\n`);
    this.receipts.push(record);
    if (failure) {
      failure.receipt = record;
      failure.retryable = record.http_status === 429 || record.http_status >= 500
        || (record.http_status === null && /timed out|fetch failed|ECONNRESET|ETIMEDOUT|network/i.test(failure.message));
      throw failure;
    }
    return { value, receipt: record };
  }
}

function apiUrl(endpoint, params = {}) {
  const url = new URL(`${WB}/${endpoint}`);
  for (const [key, value] of Object.entries({ format: 'json', per_page: 400, ...params })) url.searchParams.set(key, value);
  return url;
}

/** Returns validated pages already collected even if a later page fails. */
async function worldBankPages(archive, url, key) {
  const records = [];
  const receipts = [];
  let pages = 1;
  let total;
  let lastUpdated = null;
  try {
    for (let page = 1; page <= pages; page += 1) {
      const target = new URL(url);
      target.searchParams.set('page', page);
      const result = await archive.json(target.href, `${key}-page-${page}`);
      receipts.push(...result.receipts);
      const [meta, rows] = Array.isArray(result.value) ? result.value : [];
      const nextPages = Number(meta?.pages);
      const nextTotal = Number(meta?.total);
      if (!meta || Number(meta.page) !== page || !Number.isInteger(nextPages) || nextPages < 0 || nextPages > 50
        || !Number.isInteger(nextTotal) || nextTotal < 0 || nextTotal > 100_000
        || !(Array.isArray(rows) || (rows === null && nextTotal === 0))
        || (nextPages === 0 && nextTotal !== 0)) {
        throw new Error('Invalid World Bank JSON envelope or pagination metadata.');
      }
      if (page > 1 && (pages !== Math.max(1, nextPages) || total !== nextTotal)) throw new Error('World Bank pagination changed during collection.');
      pages = Math.max(1, nextPages);
      total = nextTotal;
      lastUpdated = meta.lastupdated || lastUpdated;
      records.push(...(rows || []));
      if (records.length > total) throw new Error('World Bank result exceeds the reported row count.');
    }
    if (records.length !== total) throw new Error('World Bank pagination ended with an incomplete row count.');
    return { records, receipts, lastUpdated, error: null };
  } catch (error) {
    if (error.archive_failure) throw error;
    for (const receipt of error.receipts || (error.receipt ? [error.receipt] : [])) if (!receipts.includes(receipt)) receipts.push(receipt);
    return { records, receipts, lastUpdated, error: error.message };
  }
}

function receiptFields(receipts) {
  const primary = receipts.find((item) => item.raw_path && item.status === 'downloaded')
    || receipts.find((item) => item.raw_path) || receipts[0];
  return {
    retrieved_at: receipts.map((item) => item.retrieved_at).filter(Boolean).sort().at(-1) || new Date().toISOString(),
    sha256: primary?.sha256 || null,
    raw_path: primary?.raw_path || null,
    raw_files: receipts.map((item) => ({ url: item.url, raw_path: item.raw_path, sha256: item.sha256, bytes: item.bytes, retrieved_at: item.retrieved_at, status: item.status, receipt_path: item.receipt_path })),
  };
}

async function collectIndicator(archive, economy, config, endYear, onProgress) {
  const id = config.id;
  onProgress(`World Bank: ${id}`);
  const metadataUrl = apiUrl(`indicator/${id}`, { source: 2 });
  const dataUrl = apiUrl(`country/${economy.id}/indicator/${id}`, { source: 2, date: `${START_YEAR}:${endYear}`, footnote: 'y' });
  const [metadataResult, dataResult] = await Promise.all([
    worldBankPages(archive, metadataUrl, `wb-metadata-${id}`),
    worldBankPages(archive, dataUrl, `wb-data-${id}`),
  ]);
  const metadata = metadataResult.records.find((item) => item?.id === id && String(item.source?.id) === '2');
  const errors = [metadataResult.error, dataResult.error].filter(Boolean);
  if (!metadata || !metadata.name || !metadata.sourceNote) errors.push('WDI indicator definition metadata is unavailable or mismatched.');
  const sourceId = `wb-${id}`;
  const unit = typeof metadata?.unit === 'string' && metadata.unit.trim() ? metadata.unit : config.unit;
  const indicator = {
    id, name: metadata?.name || id, theme: config.theme, unit,
    definition: metadata?.sourceNote || 'Definition metadata was not collected; verify the official indicator page before using this series for planning.',
    source_id: sourceId, aggregation: 'none', measurement_method: 'source_reported',
    unit_provenance: metadata?.unit?.trim() ? 'World Bank API unit' : 'Explicit WDI indicator unit catalog; API unit field empty or unavailable',
    metadata_status: metadata?.sourceNote && !metadataResult.error ? 'ready' : 'failed',
  };
  const observations = [];
  const seen = new Set();
  for (const row of dataResult.records) {
    if (!row || row.indicator?.id !== id || row.countryiso3code !== economy.id
      || (row.country?.id && row.country.id !== economy.iso2Code)
      || !/^\d{4}$/.test(row.date) || Number(row.date) < START_YEAR || Number(row.date) > endYear
      || !(row.value === null || (typeof row.value === 'number' && Number.isFinite(row.value)))
      || seen.has(row.date)) {
      errors.push('Rejected an invalid, duplicate, wrong-country or wrong-indicator observation.');
      continue;
    }
    seen.add(row.date);
    observations.push({ territory_id: economy.id, indicator_id: id, period: row.date, value: row.value,
      status: row.value === null ? 'missing' : 'observed', source_id: sourceId,
      ...(row.footnote ? { footnote: String(row.footnote) } : {}),
      ...(row.obs_status ? { provider_status: String(row.obs_status) } : {}) });
  }
  observations.sort((a, b) => a.period.localeCompare(b.period));
  const observedCount = observations.filter((item) => item.status === 'observed').length;
  const source = {
    id: sourceId, name: 'World Bank — World Development Indicators', url: dataUrl.href,
    metadata_url: metadataUrl.href, indicator_url: `https://data.worldbank.org/indicator/${id}`,
    publisher: 'World Bank', reference_period: `${START_YEAR}:${endYear}`, geographic_level: 'national',
    status: errors.length ? (observedCount ? 'partial' : 'failed') : observedCount ? 'ready' : 'unavailable',
    ...receiptFields([...dataResult.receipts, ...metadataResult.receipts]), license: WB_LICENSE,
    source_organization: metadata?.sourceOrganization || null,
    api_unit: metadata?.unit ?? null, api_last_updated: dataResult.lastUpdated,
    note: [metadata?.sourceNote, metadata?.sourceOrganization, 'National economy series only. No values are assigned to subnational boundaries.', ...new Set(errors)].filter(Boolean).join('\n\n'),
  };
  const gaps = [];
  if (errors.length) gaps.push({ category: 'source_collection', source_id: sourceId, status: source.status, detail: [...new Set(errors)].join(' '), next_action: `Retry and inspect the archived responses for ${id}; verify its metadata before use.` });
  if (observedCount < endYear - START_YEAR + 1) gaps.push({ category: 'indicator_coverage', source_id: sourceId, status: observedCount ? 'partial' : 'unavailable', detail: `${observedCount} years have a reported value in ${START_YEAR}–${endYear}; ${observations.filter((item) => item.value === null).length} explicit null observations. Omitted years are not filled.`, next_action: 'Use only reported periods; consult national sources for additional coverage.' });
  return { indicator, observations, source, gaps };
}

function validGeometry(geometry) {
  if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type)) return false;
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  if (!Array.isArray(polygons) || !polygons.length) return false;
  return polygons.every((polygon) => Array.isArray(polygon) && polygon.length && polygon.every((ring) =>
    Array.isArray(ring) && ring.length >= 4 && ring.every((point) => Array.isArray(point) && point.length >= 2
      && point.every(Number.isFinite) && Math.abs(point[0]) <= 180 && Math.abs(point[1]) <= 90)
      && ring[0][0] === ring.at(-1)[0] && ring[0][1] === ring.at(-1)[1]));
}

async function collectBoundaries(archive, economy, onProgress) {
  onProgress('geoBoundaries: reference ADM1 boundaries');
  const url = `https://www.geoboundaries.org/api/current/gbOpen/${economy.id}/ADM1/`;
  const id = 'geoboundaries-adm1';
  const receipts = [];
  const result = { territories: [], features: [], gaps: [], source: null };
  let metadata;
  try {
    const metaResult = await archive.json(url, 'geoboundaries-adm1-metadata');
    receipts.push(...metaResult.receipts);
    metadata = metaResult.value;
    if (!metadata || Array.isArray(metadata) || metadata.boundaryISO !== economy.id || metadata.boundaryType !== 'ADM1'
      || !['boundaryID', 'boundaryYearRepresented', 'boundarySource', 'boundaryLicense'].every((field) => typeof metadata[field] === 'string' && metadata[field].trim())
      || typeof metadata.simplifiedGeometryGeoJSON !== 'string') throw new Error('Invalid or mismatched geoBoundaries ADM1 metadata.');
    const geoResult = await archive.json(checkedUrl(metadata.simplifiedGeometryGeoJSON), 'geoboundaries-adm1-simplified', MAX_BOUNDARY_BYTES);
    receipts.push(...geoResult.receipts);
    const collection = geoResult.value;
    if (collection?.type !== 'FeatureCollection' || !Array.isArray(collection.features) || !collection.features.length || collection.features.length > 5000) throw new Error('Invalid or oversized ADM1 FeatureCollection.');
    if (metadata.admUnitCount && Number(metadata.admUnitCount) !== collection.features.length) throw new Error('ADM1 feature count does not match its metadata.');
    const seen = new Set();
    for (const feature of collection.features) {
      const props = feature?.properties;
      if (feature?.type !== 'Feature' || typeof props?.shapeID !== 'string' || !props.shapeID || props.shapeID.length > 200
        || typeof props.shapeName !== 'string' || !props.shapeName.trim() || seen.has(props.shapeID)
        || (props.shapeGroup && props.shapeGroup !== economy.id) || (props.shapeType && props.shapeType !== 'ADM1') || !validGeometry(feature.geometry)) {
        throw new Error('Invalid, duplicated or country-mismatched ADM1 feature.');
      }
      seen.add(props.shapeID);
      const territoryId = `${economy.id}:gbOpen:ADM1:${encodeURIComponent(props.shapeID)}`;
      result.territories.push({ id: territoryId, name: props.shapeName, level: 'adm1',
        type: metadata.boundaryCanonical && metadata.boundaryCanonical !== 'Unknown' ? metadata.boundaryCanonical : 'ADM1 (provider classification)',
        parent_id: economy.id, official_code: null, code_system: 'geoBoundaries gbOpen shapeID (provider identifier)',
        provider_code: props.shapeID, boundary_version: metadata.boundaryID, boundary_year: metadata.boundaryYearRepresented,
        source_id: id, reconciliation_status: 'pending_official_code_and_hierarchy_verification' });
      result.features.push({ type: 'Feature', properties: { territory_id: territoryId, name: props.shapeName,
        provider_shape_id: props.shapeID, code_system: 'geoBoundaries gbOpen shapeID (provider identifier)', boundary_version: metadata.boundaryID }, geometry: feature.geometry });
    }
    result.source = { id, name: 'geoBoundaries gbOpen ADM1 reference boundaries', url, publisher: 'William & Mary geoLab / geoBoundaries',
      reference_period: metadata.boundaryYearRepresented, status: 'ready', ...receiptFields(receipts), license: metadata.boundaryLicense,
      boundary_version: metadata.boundaryID, represented_year: metadata.boundaryYearRepresented, boundary_source: metadata.boundarySource,
      license_url: metadata.licenseSource || null, license_detail: metadata.licenseDetail || null, source_url: metadata.boundarySourceURL || null,
      geometry_url: metadata.simplifiedGeometryGeoJSON, note: 'Provider reference boundaries, not a verified current official administrative register. shapeID is not an official code. Parent membership records the country only; statistics have not been joined.' };
    result.gaps.push({ category: 'boundary_reconciliation', status: 'pending', detail: `ADM1 is a provider classification representing ${metadata.boundaryYearRepresented}. Current administrative status, local names and official codes are not reconciled.`, next_action: 'Compare with the national official administrative register and boundary versions before joining local statistics.' });
  } catch (error) {
    if (error.archive_failure) throw error;
    for (const receipt of error.receipts || (error.receipt ? [error.receipt] : [])) if (!receipts.includes(receipt)) receipts.push(receipt);
    result.territories = [];
    result.features = [];
    result.source = { id, name: 'geoBoundaries gbOpen ADM1 reference boundaries', url, publisher: 'William & Mary geoLab / geoBoundaries',
      reference_period: typeof metadata?.boundaryYearRepresented === 'string' ? metadata.boundaryYearRepresented : null,
      status: 'failed', ...receiptFields(receipts), license: typeof metadata?.boundaryLicense === 'string' ? metadata.boundaryLicense : 'https://www.geoboundaries.org/api.html',
      note: `Boundary collection failed; no reference shapes were accepted. ${error.message}` };
    result.gaps.push({ category: 'boundaries', status: 'failed', detail: error.message, next_action: 'Retry the provider or obtain licensed official boundaries. Continue using the national view.' });
  }
  return result;
}

async function mapConcurrent(items, limit, fn) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) { const index = next++; results[index] = await fn(items[index]); }
  }));
  return results;
}

export async function collectCountry({ country, rawDir, fetchImpl = globalThis.fetch, onProgress = () => {} }) {
  if (typeof rawDir !== 'string' || !rawDir.trim()) throw new Error('rawDir is required.');
  if (typeof fetchImpl !== 'function' || typeof onProgress !== 'function') throw new Error('fetchImpl and onProgress must be functions.');
  if (typeof country !== 'string' || !country.trim() || country.length > 160) throw new Error('A country name or ISO code is required.');
  await mkdir(rawDir, { recursive: true });
  const archive = new RawArchive(rawDir, fetchImpl);
  onProgress('World Bank: resolving country name');
  const countriesUrl = apiUrl('country');
  const countries = await worldBankPages(archive, countriesUrl, 'world-bank-countries');
  if (countries.error) throw new Error(`Country directory could not be collected completely: ${countries.error}`);
  const economy = resolveCountryName(country, countries.records);
  const endYear = new Date().getUTCFullYear();
  const [series, geography] = await Promise.all([
    mapConcurrent(WDI_INDICATORS, 3, (config) => collectIndicator(archive, economy, config, endYear, onProgress)),
    collectBoundaries(archive, economy, onProgress),
  ]);
  const directorySource = { id: 'world-bank-countries', name: 'World Bank economy directory', url: countriesUrl.href,
    publisher: 'World Bank', reference_period: 'Current directory at collection time', status: 'ready', ...receiptFields(countries.receipts),
    license: WB_LICENSE, note: 'Individual World Bank economies only; regional and income aggregates excluded. Economy codes and names do not assert sovereign or administrative status.' };
  const dataset = {
    schema_version: '0.2', generated_at: new Date().toISOString(),
    country: { id: economy.id, iso2: economy.iso2Code, name: economy.name, requested_name: country.trim(), locale: 'en', national_territory_id: economy.id,
      geography_note: 'World Bank economy definition. ADM1 shapes, if available, are provider reference boundaries with their own date and unresolved official-code correspondence. National statistics apply only to the national economy.' },
    territories: [{ id: economy.id, name: economy.name, level: 'national', type: 'country', parent_id: null, official_code: null,
      code_system: 'World Bank economy code', boundary_version: null, source_id: directorySource.id }, ...geography.territories],
    indicators: series.map((item) => item.indicator), observations: series.flatMap((item) => item.observations),
    sources: [directorySource, ...series.map((item) => item.source), geography.source],
    boundaries: { type: 'FeatureCollection', features: geography.features }, documents: [],
    gaps: [...series.flatMap((item) => item.gaps), ...geography.gaps,
      { category: 'subnational_statistics', status: 'not_collected', detail: 'This adapter collected national WDI series only; local values are absent, not zero.', next_action: 'Collect official census and sector statistics; reconcile codes, definitions and boundary dates before joining.' },
      { category: 'planning_documents', status: 'not_collected', detail: 'Official plans, planning templates, budgets, investment and participation records have not been researched by this adapter.', next_action: 'Research the country planning institutions and record verified documents and institutional requirements.' }],
    collection: { status: 'partial', adapters: ['world-bank', 'geoboundaries'], notes: [
      'Initial national-data site inputs only; this is not a completed local planning dashboard.',
      `Annual observations requested from ${START_YEAR} through ${endYear}; nulls are retained and omitted periods are never filled.`,
      'Raw source responses and per-request receipts are saved with SHA-256, UTC retrieval timestamps and failure details.',
    ] },
  };
  await writeArchive(path.join(archive.dir, 'collection-receipt.json'), `${JSON.stringify({ country: economy.id, generated_at: dataset.generated_at,
    status: dataset.collection.status, requests: archive.receipts, gaps: dataset.gaps }, null, 2)}\n`);
  onProgress(`Collected ${dataset.observations.filter((item) => item.status === 'observed').length} national values; ${geography.territories.length} reference ADM1 units; local data and planning research remain open.`);
  return dataset;
}

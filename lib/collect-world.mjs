import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

export const WORLD_CONFIG = JSON.parse(await readFile(new URL('../config/world-membership.json', import.meta.url), 'utf8'));
const WB = 'https://api.worldbank.org/v2';
const WB_LICENSE = 'World Bank dataset terms (CC BY 4.0 with additional conditions and possible third-party restrictions): https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets';
const LIMIT = 12 * 1024 * 1024;
const TIMEOUT = 25_000;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const jsonText = value => JSON.stringify(value, null, 2) + '\n';
const safeUrl = value => {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.port || !['unstats.un.org', 'api.worldbank.org', 'raw.githubusercontent.com'].includes(url.hostname)) throw new Error('Unapproved source URL.');
  return url.href;
};
async function writeNew(filename, value) {
  try { await writeFile(filename, value, { flag: 'wx' }); }
  catch (error) { error.archive_failure = true; throw error; }
}

/** Every response, including invalid/error responses, retains its original bytes and receipt. */
class Archive {
  constructor(rawDir, fetchImpl, sourceDir) { Object.assign(this, { rawDir, fetchImpl, sourceDir, receipts: [] }); }
  async get(url, key, kind = 'json') {
    safeUrl(url);
    const filename = `${key}.${kind === 'json' ? 'json' : 'html'}`;
    const receiptFile = `${key}.receipt.json`;
    let receipt, bytes, error;
    if (this.sourceDir) {
      // Replays only the exact archived request. No fallback network request is allowed.
      try {
        receipt = JSON.parse(await readFile(path.join(this.sourceDir, receiptFile), 'utf8'));
        if (receipt.url !== url || receipt.raw_path !== `raw/${filename}` && receipt.raw_path !== null
          || !Number.isFinite(Date.parse(receipt.retrieved_at))) throw new Error(`Invalid replay receipt: ${key}`);
        if (receipt.raw_path) {
          bytes = await readFile(path.join(this.sourceDir, filename));
          if (bytes.length > LIMIT || sha(bytes) !== receipt.sha256 || bytes.length !== receipt.bytes) throw new Error(`Replay SHA/size mismatch: ${key}`);
        }
      } catch (failure) { failure.archive_failure = true; throw failure; }
      if (receipt.status !== 'downloaded') error = new Error(receipt.error || `Archived request failed: ${key}`);
    } else {
      const controller = new AbortController();
      let timer;
      receipt = { url, requested_at: new Date().toISOString(), retrieved_at: null, status: 'failed', http_status: null, raw_path: null, sha256: null, bytes: 0 };
      try {
        bytes = await Promise.race([
          (async () => {
            let target = url;
            for (let redirect = 0; redirect <= 4; redirect++) {
              const response = await this.fetchImpl(safeUrl(target), { redirect: 'manual', signal: controller.signal, headers: { Accept: kind === 'json' ? 'application/json' : 'text/html' } });
              receipt.http_status = response.status;
              if (response.status >= 300 && response.status < 400) {
                const location = response.headers.get('location');
                await response.body?.cancel();
                if (!location) throw new Error('Redirect has no Location.');
                target = safeUrl(new URL(location, target).href); continue;
              }
              receipt.final_url = target;
              if (Number(response.headers.get('content-length')) > LIMIT) { await response.body?.cancel(); throw new Error('Source exceeds byte limit.'); }
              if (!response.body?.getReader) throw new Error('Source has no readable response body.');
              const reader = response.body.getReader(), chunks = []; let length = 0;
              for (;;) {
                const { value, done } = await reader.read(); if (done) break;
                length += value.byteLength;
                if (length > LIMIT) { await reader.cancel(); throw new Error('Source exceeds byte limit.'); }
                chunks.push(Buffer.from(value));
              }
              return Buffer.concat(chunks);
            }
            throw new Error('Too many source redirects.');
          })(),
          new Promise((_, reject) => { timer = setTimeout(() => { controller.abort(); reject(new Error('Source timed out after 25000 ms.')); }, TIMEOUT); }),
        ]);
        receipt.bytes = bytes.length; receipt.sha256 = sha(bytes); receipt.raw_path = `raw/${filename}`;
        if (receipt.http_status < 200 || receipt.http_status >= 300) throw new Error(`HTTP ${receipt.http_status}`);
        receipt.status = 'downloaded';
      } catch (failure) { error = failure; receipt.error = failure.message; }
      finally { clearTimeout(timer); controller.abort(); receipt.retrieved_at = new Date().toISOString(); }
    }
    let value;
    if (!error) {
      try {
        const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
        value = kind === 'json' ? JSON.parse(text) : text;
      } catch { error = new Error('Source is not valid UTF-8 or JSON.'); receipt.status = 'failed'; receipt.error = error.message; }
    }
    if (bytes) await writeNew(path.join(this.rawDir, filename), bytes);
    receipt.receipt_path = `raw/${receiptFile}`;
    await writeNew(path.join(this.rawDir, receiptFile), jsonText(receipt));
    this.receipts.push(receipt);
    if (error) { error.receipt = receipt; throw error; }
    return { value, receipt };
  }
}

const cleanCell = text => text.replace(/<[^>]*>/g, '').replace(/&(?:amp|lt|gt|quot|apos|nbsp);|&#(?:x[0-9a-f]+|\d+);/gi, entity => {
  const names = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'", '&nbsp;': ' ' };
  return names[entity.toLowerCase()] ?? String.fromCodePoint(entity[2].toLowerCase() === 'x' ? parseInt(entity.slice(3), 16) : parseInt(entity.slice(2), 10));
}).replace(/\s+/g, ' ').trim();

/** Parse the English table by its observed header contract; reject changed or duplicate identifiers. */
export function parseM49(html) {
  const table = html.replace(/<!--[\s\S]*?-->/g, '').match(/<table\b[^>]*\bid\s*=\s*["']downloadTableEN["'][^>]*>([\s\S]*?)<\/table>/i)?.[1];
  if (!table) throw new Error('UN M49 English table is unavailable.');
  const rows = [...table.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].map(row => [...row[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(cell => cleanCell(cell[1])));
  const expected = ['Global Code', 'Global Name', 'Region Code', 'Region Name', 'Sub-region Code', 'Sub-region Name', 'Intermediate Region Code', 'Intermediate Region Name', 'Country or Area', 'M49 Code', 'ISO-alpha2 Code', 'ISO-alpha3 Code'];
  if (!expected.every((label, index) => rows[0]?.[index] === label)) throw new Error('UN M49 table headers changed.');
  const seen = new Set(), codes = new Set();
  const countries = rows.slice(1).map(row => {
    if (row.length < 12 || row[0] !== '001' || !row[8] || !/^\d{3}$/.test(row[9]) || !/^[A-Z]{2}$/.test(row[10]) || !/^[A-Z]{3}$/.test(row[11])
      || seen.has(row[11]) || codes.has(row[9])) throw new Error('Invalid or duplicate UN M49 country/area row.');
    for (const i of [2, 4, 6]) if (row[i] && (!/^\d{3}$/.test(row[i]) || !row[i + 1])) throw new Error('Invalid UN M49 regional membership.');
    seen.add(row[11]); codes.add(row[9]);
    return { id: row[11], iso2: row[10], name: row[8], m49: row[9], region: { code: row[2], name: row[3] }, subregion: { code: row[4], name: row[5] }, intermediate: { code: row[6], name: row[7] } };
  });
  if (!countries.length) throw new Error('UN M49 has no country/area records.');
  return countries;
}

export function buildWorldMembership(countries, config = WORLD_CONFIG) {
  const territories = [{ id: 'WLD', name: 'World', level: 'national', type: 'exploration_scope', parent_id: null, official_code: null, code_system: 'World exploration scope; official World Bank WLD series', boundary_version: null, source_id: 'un-m49' }];
  const index = new Map(territories.map(t => [t.id, t]));
  const addGroup = (id, name, parent, level, code = null, note = 'UN M49 statistical grouping; not an administrative government.') => {
    if (index.has(id)) {
      const existing = index.get(id);
      if (existing.name !== name || existing.parent_id !== parent) throw new Error(`Ambiguous UN M49 group ${id}.`);
      return id;
    }
    const group = { id, name, level, type: 'exploration_scope', parent_id: parent, official_code: code, code_system: code ? 'UN M49 statistical region code' : 'Template exploration grouping', boundary_version: null, source_id: 'un-m49', membership_note: note };
    territories.push(group); index.set(id, group); return id;
  };
  for (const country of countries) {
    let parent = 'WLD';
    if (country.region.code) {
      if (!config.continents.includes(country.region.code)) throw new Error(`Unexpected M49 region ${country.region.code}; review the five-continent configuration.`);
      parent = addGroup(`M49:${country.region.code}`, country.region.name, 'WLD', 'continent', country.region.code);
      if (country.region.code === config.custom_region.parent_m49) {
        if (config.custom_region.member_intermediate_m49.includes(country.intermediate.code)) {
          parent = addGroup(config.custom_region.id, config.custom_region.name, parent, 'macroregion', null, config.custom_region.note);
        } else {
          const member = country.intermediate.code ? country.intermediate : country.subregion;
          if (!config.americas_navigation.direct_member_m49.includes(member.code)) throw new Error(`Unconfigured Americas membership: ${country.id}`);
          parent = addGroup(`M49:${member.code}`, member.name, parent, 'macroregion', member.code, config.americas_navigation.note);
        }
      } else {
        for (const member of [country.subregion, country.intermediate]) if (member.code) parent = addGroup(`M49:${member.code}`, member.name, parent, 'macroregion', member.code);
      }
    }
    const territory = { id: country.id, country_id: country.id, iso2: country.iso2, name: country.name, level: 'country', type: 'country', parent_id: parent,
      official_code: country.m49, code_system: 'UN M49 country or area code; country_id is ISO-alpha3', boundary_version: null, source_id: 'un-m49', m49_membership: { region: country.region, subregion: country.subregion, intermediate: country.intermediate },
      geography_note: 'UN statistical country/area, not a claim of sovereign status. WDI economy coverage and reference cartographic boundaries require scope verification for country planning.' };
    if (index.has(territory.id)) throw new Error(`Duplicate world territory ${territory.id}`);
    territories.push(territory); index.set(territory.id, territory);
  }
  const terminalIds = countries.map(t => t.id);
  const descendant = (id, parent) => { let current = index.get(id); while (current?.parent_id) { if (current.parent_id === parent) return true; current = index.get(current.parent_id); } return false; };
  // Country comparisons are explicit descendants, never a mixed set of continents and countries.
  const comparisons = territories.filter(t => t.level !== 'country').map(parent => ({ parent_id: parent.id, member_ids: terminalIds.filter(id => descendant(id, parent.id)), label: `Countries and areas in ${parent.name}`, membership_note: parent.membership_note || 'UN M49 country/area registry. Antarctica has no UN regional assignment and remains directly under World. Comparisons use reported economy values, not sums or mean rates.', source_ids: ['un-m49'] })).filter(c => c.member_ids.length);
  return { territories, analysis: { kind: 'world', terminal_territory_ids: terminalIds, comparisons } };
}

function api(endpoint, params = {}) {
  const url = new URL(`${WB}/${endpoint}`);
  for (const [key, value] of Object.entries({ format: 'json', per_page: 2000, ...params })) url.searchParams.set(key, value);
  return url.href;
}
async function pages(archive, url, key) {
  const records = [], receipts = []; let count = 1, total, lastUpdated = null;
  try {
    for (let page = 1; page <= count; page++) {
      const target = new URL(url); target.searchParams.set('page', page);
      const result = await archive.get(target.href, `${key}-page-${page}`); receipts.push(result.receipt);
      const [meta, rows] = Array.isArray(result.value) ? result.value : [];
      if (!meta || Number(meta.page) !== page || !Number.isInteger(Number(meta.pages)) || Number(meta.pages) < 0 || Number(meta.pages) > 30
        || !Number.isInteger(Number(meta.total)) || Number(meta.total) < 0 || Number(meta.total) > 100_000
        || !(Array.isArray(rows) || rows === null && Number(meta.total) === 0) || Number(meta.pages) === 0 && Number(meta.total) !== 0) throw new Error('Invalid World Bank pagination envelope.');
      const nextCount = Math.max(1, Number(meta.pages));
      if (page > 1 && (count !== nextCount || total !== Number(meta.total))) throw new Error('World Bank pagination changed during retrieval.');
      count = nextCount; total = Number(meta.total); lastUpdated = meta.lastupdated || lastUpdated;
      records.push(...(rows || [])); if (records.length > total) throw new Error('World Bank exceeded declared total.');
    }
    if (records.length !== total) throw new Error('World Bank pagination is incomplete.');
    return { records, receipts, lastUpdated, error: null };
  } catch (error) {
    if (error.archive_failure) throw error;
    if (error.receipt) receipts.push(error.receipt);
    return { records, receipts, lastUpdated, error: error.message };
  }
}
function evidence(receipts) {
  const primary = receipts.find(r => r.status === 'downloaded') || receipts[0];
  return { retrieved_at: receipts.map(r => r.retrieved_at).sort().at(-1) || new Date().toISOString(), raw_path: primary?.raw_path || null, sha256: primary?.sha256 || null, raw_files: receipts };
}
const gap = (category, detail, source_id, status = 'partial') => ({ category, detail, source_id, status, next_action: 'Inspect the archived source and reconcile scope before adding values or boundaries. Do not infer missing values.' });

async function indicatorSeries(archive, economies, countryIds, config, startYear, endYear) {
  const dataUrl = api(`country/all/indicator/${config.id}`, { source: 2, date: `${startYear}:${endYear}`, footnote: 'y' });
  const metadataUrl = api(`indicator/${config.id}`, { source: 2 });
  const [data, metadata] = await Promise.all([pages(archive, dataUrl, `wb-data-${config.id}`), pages(archive, metadataUrl, `wb-meta-${config.id}`)]);
  const meta = metadata.records.find(row => row?.id === config.id && String(row.source?.id) === '2');
  const errors = [data.error, metadata.error].filter(Boolean);
  if (!meta?.name || !meta?.sourceNote) errors.push('Definition metadata is missing or mismatched.');
  const sourceId = `wb-${config.id}`, observations = [], seen = new Set();
  const omissions = new Set();
  for (const row of data.records) {
    if (row?.countryiso3code !== 'WLD' && !countryIds.has(row?.countryiso3code)) { if (row?.countryiso3code) omissions.add(row.countryiso3code); continue; }
    const economy = economies.get(row.countryiso3code), key = `${row.countryiso3code}:${row.date}`;
    if (!economy || row.country?.id !== economy.iso2Code || row.indicator?.id !== config.id || !/^\d{4}$/.test(row.date) || Number(row.date) < startYear || Number(row.date) > endYear
      || row.value !== null && (typeof row.value !== 'number' || !Number.isFinite(row.value)) || seen.has(key)) { errors.push('Rejected invalid, duplicate or mismatched economy/indicator observation.'); continue; }
    seen.add(key);
    observations.push({ territory_id: row.countryiso3code, indicator_id: config.id, period: row.date, value: row.value, status: row.value === null ? 'missing' : 'observed', source_id: sourceId,
      ...(row.footnote ? { footnote: String(row.footnote) } : {}), ...(row.obs_status ? { provider_status: String(row.obs_status) } : {}) });
  }
  const indicator = { id: config.id, name: meta?.name || config.id, theme: config.theme, unit: meta?.unit?.trim() || config.unit, definition: meta?.sourceNote || 'Definition metadata was not obtained; consult the official WDI indicator before using the series.',
    aggregation: 'official_only', source_id: sourceId, measurement_method: 'source_reported', metadata_status: meta?.sourceNote && !metadata.error ? 'ready' : 'failed', unit_provenance: meta?.unit?.trim() ? 'World Bank API unit' : 'Explicit WDI unit catalog; API unit field is empty or unavailable' };
  const observed = observations.filter(o => o.status === 'observed').length;
  const source = { id: sourceId, name: `World Bank WDI — ${indicator.name}`, publisher: 'World Bank', url: dataUrl, metadata_url: metadataUrl, indicator_url: `https://data.worldbank.org/indicator/${config.id}`,
    geographic_level: 'world_country_series', reference_period: `${startYear}:${endYear}`, status: errors.length ? observed ? 'partial' : 'failed' : observed ? 'ready' : 'unavailable', ...evidence([...data.receipts, ...metadata.receipts]),
    license: WB_LICENSE, api_unit: meta?.unit ?? null, api_last_updated: data.lastUpdated, source_organization: meta?.sourceOrganization || null,
    note: [meta?.sourceNote, meta?.sourceOrganization, 'WLD is the provider-reported World aggregate; country observations are exact M49 ISO3 and non-aggregate World Bank economy matches. WLD is not a sum of the displayed registry. No continental/custom-region totals or average rates are calculated.', ...new Set(errors)].filter(Boolean).join('\n\n') };
  return { indicator, source, observations, gaps: [...(errors.length ? [gap('source_collection', [...new Set(errors)].join(' '), sourceId, source.status)] : []), gap('indicator_coverage', `${observed} reported values for ${startYear}–${endYear}; explicit nulls retained, absent years/economies unfilled. ${omissions.size} provider aggregate or unmatched economy codes excluded.`, sourceId)], excluded_codes: [...omissions].sort() };
}

function validGeometry(geometry) {
  if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type)) return false;
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return Array.isArray(polygons) && polygons.length > 0 && polygons.every(p => Array.isArray(p) && p.length > 0 && p.every(r => Array.isArray(r) && r.length >= 4
    && r.every(c => Array.isArray(c) && c.length >= 2 && c.every(Number.isFinite) && Math.abs(c[0]) <= 180 && Math.abs(c[1]) <= 90)
    && r[0][0] === r.at(-1)[0] && r[0][1] === r.at(-1)[1]));
}
export function joinWorldBoundaries(collection, territories, comparisons, config = WORLD_CONFIG) {
  if (collection?.type !== 'FeatureCollection' || !Array.isArray(collection.features) || !collection.features.length || collection.features.length > 1000) throw new Error('Invalid Natural Earth FeatureCollection.');
  const countries = new Map(territories.filter(t => t.level === 'country').map(t => [t.id, t]));
  const accepted = new Map(), unmatched = [], duplicateCodes = new Set();
  for (const feature of collection.features) {
    const p = feature?.properties || {}, territory = countries.get(p.ISO_A3);
    const code = typeof p.ISO_N3 === 'string' || typeof p.ISO_N3 === 'number' ? String(p.ISO_N3).padStart(3, '0') : null;
    if (!territory || code !== territory.official_code || !validGeometry(feature.geometry)) {
      unmatched.push({ provider_id: p.NE_ID ?? null, name: p.NAME || null, iso_a3: p.ISO_A3 || null, iso_n3: p.ISO_N3 ?? null, reason: 'No exact ISO_A3 + M49 numeric match, or invalid geometry. No fallback/extension code or name join.' }); continue;
    }
    if (accepted.has(territory.id)) { duplicateCodes.add(territory.id); continue; }
    accepted.set(territory.id, { type: 'Feature', properties: { territory_id: territory.id, name: territory.name, source_id: 'natural-earth', geometry_edition: config.boundary.commit,
      reference_only: true, join_method: 'Natural Earth ISO_A3 and ISO_N3 exactly match UN M49 ISO-alpha3 and M49 country/area code', provider_id: p.NE_ID ?? null }, geometry: feature.geometry });
  }
  // Ambiguous multiple features are not silently merged into a country's statistical area.
  for (const id of duplicateCodes) { accepted.delete(id); unmatched.push({ iso_a3: id, reason: 'Duplicate exact join key; all matching features omitted pending reconciliation.' }); }
  const features = [...accepted.values()], coverage = [];
  for (const parent of territories.filter(t => t.level !== 'country' && t.id !== 'WLD')) {
    const members = comparisons.find(c => c.parent_id === parent.id)?.member_ids || [];
    const mapped = members.filter(id => accepted.has(id)), omitted = members.filter(id => !accepted.has(id));
    coverage.push({ territory_id: parent.id, mapped_member_ids: mapped, omitted_member_ids: omitted });
    if (!mapped.length) continue;
    features.push({ type: 'Feature', properties: { territory_id: parent.id, name: parent.name, source_id: 'natural-earth', geometry_edition: config.boundary.commit, reference_only: true,
      display_only: true, construction: 'Concatenated polygons of exact-joined members from one Natural Earth edition; not a legal boundary or numerical aggregation.', mapped_member_ids: mapped, omitted_member_ids: omitted },
      geometry: { type: 'MultiPolygon', coordinates: mapped.flatMap(id => { const g = accepted.get(id).geometry; return g.type === 'Polygon' ? [g.coordinates] : g.coordinates; }) } });
  }
  return { features, unmatched, coverage, unmapped_country_ids: [...countries.keys()].filter(id => !accepted.has(id)) };
}

export async function collectWorld({ rawDir, fetchImpl = globalThis.fetch, onProgress = () => {}, sourceDir, startYear, endYear } = {}) {
  if (typeof rawDir !== 'string' || !rawDir.trim() || typeof fetchImpl !== 'function') throw new Error('rawDir and fetchImpl are required.');
  let replay;
  if (sourceDir) {
    replay = JSON.parse(await readFile(path.join(sourceDir, 'collection-receipt.json'), 'utf8'));
    if (replay.country !== 'WLD' || replay.config_sha256 !== sha(jsonText(WORLD_CONFIG))) throw new Error('Replay configuration differs from the archived world collection. Use the matching adapter configuration.');
  }
  endYear ??= replay?.options?.endYear ?? new Date().getUTCFullYear(); startYear ??= replay?.options?.startYear ?? endYear - 5;
  if (!Number.isInteger(startYear) || !Number.isInteger(endYear) || startYear < 1960 || endYear > new Date().getUTCFullYear() || startYear > endYear || endYear - startYear > 20) throw new Error('Use an annual range of at most 21 years, between 1960 and the current year.');
  await mkdir(rawDir, { recursive: true });
  const archive = new Archive(path.resolve(rawDir), fetchImpl, sourceDir && path.resolve(sourceDir));
  onProgress('UN M49: complete country/area membership registry');
  const registry = await archive.get(WORLD_CONFIG.registry_url, 'un-m49', 'html');
  const countries = parseM49(registry.value), membership = buildWorldMembership(countries);
  if (!WORLD_CONFIG.continents.every(code => membership.territories.some(t => t.id === `M49:${code}`))) throw new Error('UN M49 registry is missing one of the five configured regions.');
  await writeNew(path.join(rawDir, 'un-m49-extracted.json'), jsonText(countries));
  const unSource = { id: 'un-m49', name: 'United Nations M49 standard country/area codes and geographic regions', publisher: 'United Nations Statistics Division', url: WORLD_CONFIG.registry_url,
    status: 'ready', ...evidence([registry.receipt]), reference_period: 'Registry snapshot at retrieval time; not a historical boundary edition', license: 'UN website terms; table reuse conditions require review: https://www.un.org/en/about-us/terms-of-use',
    note: `${WORLD_CONFIG.custom_region.note} ${WORLD_CONFIG.americas_navigation.note} The five continental entries follow M49 Region (including Americas as one region). Antarctica is an unassigned country/area, not a sixth configured continent.` };
  onProgress('World Bank: exact economy-code correspondence');
  const directoryUrl = api('country'), directory = await pages(archive, directoryUrl, 'wb-countries');
  if (directory.error) throw new Error(`World Bank directory incomplete: ${directory.error}`);
  const countryMap = new Map(countries.map(c => [c.id, c])), economies = new Map(), excluded = [];
  for (const economy of directory.records) {
    if (!economy || !/^[A-Z0-9]{3}$/.test(economy.id) || typeof economy.iso2Code !== 'string' || !economy.region?.id) throw new Error('Invalid World Bank economy directory entry.');
    if (economy.id === 'WLD' && economy.region.id === 'NA' || economy.region.id !== 'NA' && countryMap.get(economy.id)?.iso2 === economy.iso2Code) {
      if (economies.has(economy.id)) throw new Error('Duplicate World Bank economy code.');
      economies.set(economy.id, economy);
    } else excluded.push({ id: economy.id, name: economy.name, reason: economy.region.id === 'NA' ? 'Provider aggregate other than WLD' : 'No exact M49 ISO-alpha3 and ISO-alpha2 match' });
  }
  if (!economies.has('WLD')) throw new Error('World Bank WLD economy directory entry is unavailable.');
  const directorySource = { id: 'wb-countries', name: 'World Bank economy directory', publisher: 'World Bank', url: directoryUrl, status: 'ready', ...evidence(directory.receipts), license: WB_LICENSE,
    note: 'Only exact ISO-alpha3 AND ISO-alpha2 matches to the UN M49 registry are accepted, plus the provider WLD aggregate. Other income/region aggregates and unmatched economies are excluded.' };
  const series = [];
  for (const indicator of WORLD_CONFIG.indicators) {
    onProgress(`World Bank: ${indicator.id}, ${startYear}–${endYear}`);
    series.push(await indicatorSeries(archive, economies, new Set(countries.map(c => c.id)), indicator, startYear, endYear));
  }
  const gaps = series.flatMap(s => s.gaps);
  gaps.push(gap('aggregate_scope', 'No exact-scope official series was acquired for UN continents/subregions or the custom Central America + Caribbean group. Their values are missing. Country sums, rate averages and World Bank/OWID regional proxies are not substituted.', 'un-m49'));
  gaps.push(gap('economy_reconciliation', `${countries.filter(c => !economies.has(c.id)).length} M49 countries/areas have no exact World Bank economy match. Unmatched provider economies are recorded in the collection receipt.`, 'wb-countries'));
  onProgress('Natural Earth: reference map units and display-only group outlines');
  let geography = { features: [], unmatched: [], coverage: [], unmapped_country_ids: countries.map(c => c.id) }, boundaryReceipt, boundaryError;
  try {
    const boundary = await archive.get(WORLD_CONFIG.boundary.url, 'natural-earth-map-units'); boundaryReceipt = boundary.receipt;
    geography = joinWorldBoundaries(boundary.value, membership.territories, membership.analysis.comparisons);
  } catch (error) { if (error.archive_failure) throw error; boundaryReceipt ||= error.receipt; boundaryError = error.message; }
  const boundarySource = { id: 'natural-earth', name: WORLD_CONFIG.boundary.name, url: WORLD_CONFIG.boundary.url, publisher: 'Natural Earth / NACIS', status: boundaryError ? 'failed' : 'ready',
    ...evidence(boundaryReceipt ? [boundaryReceipt] : []), license: 'Public domain', license_url: WORLD_CONFIG.boundary.license_url, source_url: WORLD_CONFIG.boundary.documentation_url,
    reference_period: `Repository release ${WORLD_CONFIG.boundary.release}; not a verified statistical boundary reference year`, boundary_version: WORLD_CONFIG.boundary.commit,
    note: `${WORLD_CONFIG.boundary.note} Upper-scope outlines concatenate accepted member polygons only, with omitted members listed; they neither dissolve political claims nor aggregate statistical values. ${boundaryError || ''}` };
  gaps.push(gap('boundary_reconciliation', `${geography.unmapped_country_ids.length} countries/areas have no exact-joined reference geometry; ${geography.unmatched.length} provider features are unresolved. Small islands, extension codes and differences of territorial scope remain unverified. ${boundaryError || ''}`, 'natural-earth', boundaryError ? 'failed' : 'partial'));
  gaps.push(gap('country_adapters', 'Domestic administrative registers, census/local statistics and planning materials belong in separate country datasets. This world collector does not fabricate national or local boundaries, values or country-site URLs.', 'un-m49', 'not_collected'));
  const observations = series.flatMap(s => s.observations);
  // Missing group values are explicit. Even additive-looking measures are not reconstructed.
  for (const territory of membership.territories.filter(t => !['WLD', ...countries.map(c => c.id)].includes(t.id))) {
    for (const indicator of series.map(s => s.indicator)) for (let year = startYear; year <= endYear; year++) observations.push({ territory_id: territory.id, indicator_id: indicator.id, period: String(year), value: null, status: 'missing', source_id: indicator.source_id, footnote: 'No exact-scope official aggregate acquired. No sum or mean is calculated.' });
  }
  const dataset = { schema_version: '0.2', generated_at: archive.receipts.map(r => r.retrieved_at).sort().at(-1), country: { id: 'WLD', name: 'World', requested_name: 'World', locale: 'en', national_territory_id: 'WLD',
    geography_note: 'World exploration uses the UN M49 country/area registry and five Region entries. The Americas navigation combines Central America + Caribbean as a custom group, including Mexico. This is not a sovereign-state list. WDI values refer to provider economies; World is the official WLD series only. Reference map units are Natural Earth de facto cartography with missing areas and unresolved statistical-boundary correspondence. Group outlines concatenate available shapes for navigation only; they do not calculate values.' },
    territories: membership.territories, analysis: membership.analysis, indicators: series.map(s => s.indicator), observations, sources: [unSource, directorySource, ...series.map(s => s.source), boundarySource],
    boundaries: { type: 'FeatureCollection', features: geography.features }, documents: [], gaps,
    collection: { status: 'partial', adapters: ['un-m49', 'world-bank', 'natural-earth'], notes: [`Annual period ${startYear}–${endYear}. Metadata definitions, original response bytes, pagination, SHA-256 and UTC timestamps retained.`, 'Null is not zero. Only directly reported World/country values are accepted; no regional or subnational values are derived.'], boundary_coverage: geography.coverage } };
  await writeNew(path.join(rawDir, 'collection-receipt.json'), jsonText({ country: 'WLD', generated_at: dataset.generated_at, options: { startYear, endYear }, config_sha256: sha(jsonText(WORLD_CONFIG)), status: dataset.collection.status, requests: archive.receipts,
    counts: { m49_countries_areas: countries.length, matched_wb_economies_including_world: economies.size, territories: dataset.territories.length, reported_values: observations.filter(o => o.status === 'observed').length },
    excluded_economies: excluded, excluded_indicator_codes: Object.fromEntries(series.map(s => [s.indicator.id, s.excluded_codes])), unresolved_boundaries: geography.unmatched, unmapped_country_ids: geography.unmapped_country_ids, boundary_coverage: geography.coverage, gaps }));
  onProgress(`Collected ${countries.length} UN countries/areas, ${observations.filter(o => o.status === 'observed').length} reported values, ${geography.features.length} reference/display shapes.`);
  return dataset;
}

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const defaultRoot = fileURLToPath(new URL('../', import.meta.url));
const COMMON_PATH = 'config/common-subnational-sources.json';
const COUNTRY_PATH = 'config/country-source-registry.json';

function invariant(value, message) {
  if (!value) throw new Error(`Invalid source catalog: ${message}`);
}

function normal(value) {
  return String(value ?? '').normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase('en')
    .replace(/[^\p{L}\p{N}]+/gu, '');
}

function httpsUrl(value, field) {
  let url;
  try { url = new URL(value); } catch { throw new Error(`Invalid source catalog: ${field} is not a URL`); }
  invariant(url.protocol === 'https:' && !url.username && !url.password, `${field} must be a public HTTPS URL without credentials`);
  return value;
}

async function readJson(root, relativePath) {
  return JSON.parse(await readFile(path.join(root, relativePath), 'utf8'));
}

function validateCommon(common) {
  invariant(common?.version && common?.as_of, 'common source version/as_of missing');
  invariant(Array.isArray(common.status_model) && common.status_model.length >= 5, 'common status model missing');
  invariant(Array.isArray(common.sources) && common.sources.length, 'common sources missing');
  const ids = new Set();
  for (const source of common.sources) {
    invariant(/^[a-z0-9][a-z0-9-]+$/.test(source?.id), 'common source id must be stable kebab-case');
    invariant(!ids.has(source.id), `duplicate common source ${source.id}`); ids.add(source.id);
    invariant(source.provider && source.title && source.authority_type, `${source.id} provider metadata missing`);
    invariant(Array.isArray(source.themes) && source.themes.length, `${source.id} themes missing`);
    invariant(Array.isArray(source.geography) && source.geography.length, `${source.id} geography missing`);
    httpsUrl(source.catalog_url, `${source.id}.catalog_url`);
    httpsUrl(source.documentation_url, `${source.id}.documentation_url`);
    invariant(source.coverage && source.availability_method, `${source.id} coverage/discovery method missing`);
    invariant(source.access?.mode && Array.isArray(source.access.formats), `${source.id} access metadata missing`);
    invariant(source.cache_policy && source.redistribution && source.adapter_status, `${source.id} reuse metadata missing`);
    invariant(Array.isArray(source.cautions) && source.cautions.length, `${source.id} cautions missing`);
  }
}

function validateCountrySource(source, prefix) {
  invariant(/^[A-Z0-9][A-Z0-9_]+$/.test(source?.id), `${prefix} source id invalid`);
  invariant(source.role && source.title && source.publisher && source.stage, `${prefix}.${source.id} metadata missing`);
  httpsUrl(source.url, `${prefix}.${source.id}.url`);
}

function inlineCountry(entry) {
  invariant(/^[A-Z]{3}$/.test(entry?.iso3), 'inline country ISO3 invalid');
  invariant(Array.isArray(entry.names) && entry.names.length, `${entry.iso3} names missing`);
  invariant(entry.research_status && entry.checked_at, `${entry.iso3} research status missing`);
  invariant(entry.census && entry.planning, `${entry.iso3} census/planning profile missing`);
  invariant(Array.isArray(entry.sources) && entry.sources.length, `${entry.iso3} sources missing`);
  const ids = new Set();
  for (const source of entry.sources) {
    validateCountrySource(source, entry.iso3);
    invariant(!ids.has(source.id), `duplicate ${entry.iso3} source ${source.id}`); ids.add(source.id);
  }
  return {
    iso3: entry.iso3,
    names: [...entry.names],
    research_status: entry.research_status,
    checked_at: entry.checked_at,
    origin_registry: 'country-source-registry',
    census: entry.census,
    planning: entry.planning,
    sources: entry.sources.map(source => ({ ...source })),
  };
}

function importedCountry(country, sourceMap, imported) {
  invariant(/^[A-Z]{3}$/.test(country?.iso), `${imported.id} contains invalid ISO3`);
  const ids = new Set([
    country.agency_source,
    ...(country.census_sources || []),
    ...(country.laws || []).map(item => item.source),
    ...(country.themes || []).map(item => item.source),
    ...(country.planning_profile?.relation_sources || []),
  ].filter(Boolean));
  const sources = [...ids].map(id => {
    const source = sourceMap.get(id);
    invariant(source, `${imported.id}/${country.iso} references missing source ${id}`);
    httpsUrl(source.url, `${imported.id}.${id}.url`);
    return {
      id: source.id,
      role: country.census_sources?.includes(id) ? 'census_catalog_or_product'
        : (country.laws || []).some(item => item.source === id) ? 'planning_law'
          : id === country.agency_source ? 'planning_institution' : 'supporting_evidence',
      title: source.title,
      publisher: null,
      source_type: source.kind,
      url: source.url,
      stage: 'desk_research_location',
      checked_at: source.checked || null,
      note: 'Imported from the Latin America 20-country desk-research registry; refresh and acquire the actual source for a country build.',
    };
  });
  return {
    iso3: country.iso,
    names: [country.country],
    research_status: imported.research_status,
    checked_at: sources.map(item => item.checked_at).filter(Boolean).sort().at(-1) || null,
    origin_registry: imported.id,
    census: {
      latest_census_year: country.census_year,
      usable_detailed_year: country.usable_year,
      status: country.census_status,
      published_geography: country.published_geography,
      finer_geography: country.finer_geography,
      formats: country.formats,
      caveat: country.caveat,
    },
    planning: {
      planning_level: country.planning_level,
      plan: country.plan,
      responsible_institution: country.agency,
      system: country.planning_profile?.system,
      process_summary: country.planning_profile?.chain,
      internal_analysis_geography: country.finer_geography,
      unresolved: country.planning_profile?.gaps,
    },
    sources,
  };
}

export async function loadSourceCatalog(root = defaultRoot) {
  const base = path.resolve(root);
  const [common, registry] = await Promise.all([readJson(base, COMMON_PATH), readJson(base, COUNTRY_PATH)]);
  validateCommon(common);
  invariant(registry?.version && registry?.as_of, 'country registry version/as_of missing');
  invariant(Array.isArray(registry.imports) && Array.isArray(registry.countries), 'country registry collections missing');
  const countries = registry.countries.map(inlineCountry);
  for (const imported of registry.imports) {
    invariant(imported?.id && imported?.path && Number.isInteger(imported.country_count), 'country import metadata missing');
    const resolved = path.resolve(base, imported.path);
    const relative = path.relative(base, resolved);
    invariant(relative && !relative.startsWith('..') && !path.isAbsolute(relative), `${imported.id} import leaves template root`);
    const research = JSON.parse(await readFile(resolved, 'utf8'));
    invariant(Array.isArray(research.countries) && research.countries.length === imported.country_count, `${imported.id} country count mismatch`);
    invariant(Array.isArray(research.sources), `${imported.id} sources missing`);
    const sourceMap = new Map(research.sources.map(source => [source.id, source]));
    countries.push(...research.countries.map(country => importedCountry(country, sourceMap, imported)));
  }
  const countryIds = new Set();
  for (const country of countries) {
    invariant(!countryIds.has(country.iso3), `duplicate country ${country.iso3}`); countryIds.add(country.iso3);
  }
  return {
    version: '1.0',
    as_of: [common.as_of, registry.as_of].sort().at(-1),
    common_sources: common.sources,
    countries,
    coverage: {
      country_records: countries.length,
      common_sources: common.sources.length,
      status_model: common.status_model,
    },
  };
}

export function findCountrySourceRecord(catalog, requested) {
  const query = normal(requested);
  if (!query) return null;
  const matches = catalog.countries.filter(country => normal(country.iso3) === query || country.names.some(name => normal(name) === query));
  if (matches.length > 1) throw new Error(`Ambiguous source-registry country: ${requested}`);
  return matches[0] || null;
}

export function buildSourcePreflight(catalog, country, { theme } = {}) {
  invariant(/^[A-Z]{3}$/.test(country?.id), 'preflight country.id must be ISO3');
  const record = findCountrySourceRecord(catalog, country.id);
  const themeKey = normal(theme);
  const common = catalog.common_sources.filter(source => !themeKey
    || source.themes.some(value => normal(value).includes(themeKey) || themeKey.includes(normal(value))));
  const researched = Boolean(record);
  return {
    schema_version: '1.0',
    generated_at: new Date().toISOString(),
    catalog_as_of: catalog.as_of,
    country: { iso3: country.id, name: country.name || record?.names?.[0] || country.id },
    country_research: researched ? {
      status: record.research_status,
      checked_at: record.checked_at,
      origin_registry: record.origin_registry,
      census: record.census,
      planning: record.planning,
      sources: record.sources,
    } : {
      status: 'source_locations_not_pre_researched',
      checked_at: null,
      origin_registry: null,
      census: null,
      planning: null,
      sources: [],
    },
    common_candidates: common.map(source => ({
      ...source,
      country_status: 'availability_not_checked_for_country',
    })),
    required_actions: [
      researched
        ? 'Refresh every country source location, law version, responsible institution and publication edition before adoption.'
        : 'Locate and verify the national census catalogue, planning law, planning guidance, planning-document repository and official geography/code sources.',
      'Identify the legal planning unit and the finer internal-analysis geography needed to prepare that plan.',
      'Check each common candidate by country, theme, period and geographic level; a catalogue entry is not an acquired observation.',
      'Acquire permitted originals with request details and hashes; record unavailable, restricted and failed sources separately.',
      'Match source geography to official codes and boundary versions before adding observations to data/dashboard.json.',
      'Record accepted and rejected indicators with definitions, denominators, periods, populations and reasons.',
    ],
    summary: {
      country_source_locations: record?.sources.length || 0,
      common_candidates: common.length,
      acquired_sources: 0,
      geography_matched_sources: 0,
      accepted_indicators: 0,
    },
  };
}

function md(value) {
  return String(value ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
}

export function renderSourcePreflightMarkdown(preflight) {
  const country = preflight.country;
  const lines = [
    `# Source preflight: ${country.name} (${country.iso3})`,
    '',
    `Generated from source catalog ${preflight.catalog_as_of}. This is a discovery plan. It does not mean the listed data were acquired, matched or accepted.`,
    '',
    '## Country-specific source locations',
    '',
    `Research status: **${preflight.country_research.status}**`,
    '',
  ];
  if (preflight.country_research.sources.length) {
    lines.push('| Role | Source | Evidence stage | Location |', '|---|---|---|---|');
    for (const source of preflight.country_research.sources) {
      lines.push(`| ${md(source.role)} | ${md(source.title)} | ${md(source.stage)} | [Open](${source.url}) |`);
    }
  } else {
    lines.push('No country-specific source locations are pre-researched yet. Complete the first required action below.');
  }
  if (preflight.country_research.census) {
    lines.push('', '### Census and geography starting point', '', '```json', JSON.stringify(preflight.country_research.census, null, 2), '```');
  }
  if (preflight.country_research.planning) {
    lines.push('', '### Planning starting point', '', '```json', JSON.stringify(preflight.country_research.planning, null, 2), '```');
  }
  lines.push('', '## Cross-country subnational candidates', '', '| Source | Themes | Geography | Country status |', '|---|---|---|---|');
  for (const source of preflight.common_candidates) {
    lines.push(`| [${md(source.title)}](${source.catalog_url}) | ${md(source.themes.join(', '))} | ${md(source.geography.join(', '))} | ${md(source.country_status)} |`);
  }
  lines.push('', '## Required work', '');
  for (const [index, action] of preflight.required_actions.entries()) lines.push(`${index + 1}. ${action}`);
  lines.push('', 'Do not copy a national value to a local area, treat a modeled grid as an official census count, or join areas only by name.', '');
  return lines.join('\n');
}

export async function writeSourcePreflight(outDir, country, options = {}) {
  const catalog = await loadSourceCatalog(options.root || defaultRoot);
  const preflight = buildSourcePreflight(catalog, country, options);
  const evidenceDir = path.join(outDir, 'evidence');
  await mkdir(evidenceDir, { recursive: true });
  await Promise.all([
    writeFile(path.join(evidenceDir, 'SOURCE_PREFLIGHT.json'), `${JSON.stringify(preflight, null, 2)}\n`, 'utf8'),
    writeFile(path.join(evidenceDir, 'SOURCE_PREFLIGHT.md'), renderSourcePreflightMarkdown(preflight), 'utf8'),
  ]);
  return preflight;
}

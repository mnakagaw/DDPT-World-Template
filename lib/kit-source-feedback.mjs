import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

export const KIT_SOURCE_FEEDBACK_VERSION = "1.0";
export const KIT_SOURCE_FEEDBACK_UPSTREAM = Object.freeze({
  version: "1.9.0",
  commit: "c67e2e2f2144cf59d6735ce26910933a481337ce",
  contract_url: "https://github.com/mnakagaw/Census-Dashboard-Kit/blob/c67e2e2f2144cf59d6735ce26910933a481337ce/docs/AREADATA_SOURCE_FEEDBACK.md",
  schema_url: "https://raw.githubusercontent.com/mnakagaw/Census-Dashboard-Kit/c67e2e2f2144cf59d6735ce26910933a481337ce/schemas/areadata-source-feedback.schema.json",
});

const ROLES = new Set([
  "official_statistics_office", "census_catalog", "census_results", "table_catalog",
  "machine_readable_data", "administrative_codes", "boundaries", "planning_law",
  "planning_guidance", "plans_budgets_implementation_evaluation", "international_complement",
]);
const AUTHORITY_TYPES = new Set([
  "official_national", "official_subnational", "official_territorial",
  "international_organization", "administering_authority",
]);
const STAGES = [
  "official_location_identified", "official_location_verified", "source_acquired",
  "content_inspected", "geography_matched", "indicator_adopted_in_areadata",
];
const STAGE_RANK = new Map(STAGES.map((stage, index) => [stage, index]));
const TOP_KEYS = new Set(["schema_version", "produced_by", "exported_at", "origin_commit", "sources"]);
const SOURCE_KEYS = new Set([
  "iso3", "source_id", "role", "title", "publisher", "url", "authority_type",
  "evidence_stage", "checked_at", "geographic_levels", "reference_periods", "formats",
  "license_or_terms", "reuse_note", "origin_evidence_path", "artifact_sha256",
]);
const REQUIRED_SOURCE_KEYS = [
  "iso3", "source_id", "role", "title", "publisher", "url", "authority_type",
  "evidence_stage", "checked_at", "geographic_levels", "reference_periods", "formats",
  "reuse_note", "origin_evidence_path",
];
const SECRET_QUERY_NAMES = /^(?:api[_-]?key|key|token|access[_-]?token|auth|authorization|credential|password|passwd|secret|signature|sig|x-amz-signature)$/i;
const INTERNATIONAL_HOSTS = new Set(["celade.cepal.org", "statistics.cepal.org", "unstats.un.org", "washdata.org"]);
const COMMIT_FILE_CACHE = new Map();

const STATISTICS_PUBLISHERS = Object.freeze({
  ARG: "Instituto Nacional de Estadística y Censos (INDEC)",
  BOL: "Instituto Nacional de Estadística de Bolivia",
  BRA: "Instituto Brasileiro de Geografia e Estatística (IBGE)",
  CHL: "Instituto Nacional de Estadísticas de Chile",
  COL: "Departamento Administrativo Nacional de Estadística (DANE)",
  CRI: "Instituto Nacional de Estadística y Censos de Costa Rica",
  CUB: "CEPAL/CELADE",
  ECU: "Instituto Nacional de Estadística y Censos del Ecuador",
  SLV: "Banco Central de Reserva de El Salvador — Oficina Nacional de Estadística y Censos",
  GTM: "Instituto Nacional de Estadística de Guatemala",
  HTI: "Institut Haïtien de Statistique et d’Informatique",
  HND: "Instituto Nacional de Estadística de Honduras",
  MEX: "Instituto Nacional de Estadística y Geografía (INEGI)",
  NIC: "Instituto Nacional de Información de Desarrollo (INIDE)",
  PAN: "Instituto Nacional de Estadística y Censo de Panamá",
  PRY: "Instituto Nacional de Estadística de Paraguay",
  PER: "Instituto Nacional de Estadística e Informática (INEI)",
  DOM: "Oficina Nacional de Estadística",
  URY: "Instituto Nacional de Estadística de Uruguay",
  VEN: "CEPAL/CELADE",
});

const HOST_PUBLISHERS = Object.freeze({
  "argentina.gob.ar": "Government of Argentina",
  "sea.gob.bo": "Government of Bolivia",
  "gob.bo": "Government of Bolivia",
  "planalto.gov.br": "Presidência da República do Brasil",
  "gov.br": "Government of Brazil",
  "bcn.cl": "Biblioteca del Congreso Nacional de Chile",
  "subdere.gob.cl": "Subsecretaría de Desarrollo Regional y Administrativo",
  "funcionpublica.gov.co": "Government of Colombia",
  "dnp.gov.co": "Departamento Nacional de Planeación",
  "pgrweb.go.cr": "Procuraduría General de la República de Costa Rica",
  "mideplan.go.cr": "Ministerio de Planificación Nacional y Política Económica",
  "gacetaoficial.gob.cu": "Gaceta Oficial de la República de Cuba",
  "planificacion.gob.ec": "Government of Ecuador — national planning authority",
  "presidencia.gob.ec": "Presidency of Ecuador",
  "asamblea.gob.sv": "Asamblea Legislativa de El Salvador",
  "transparencia.gob.sv": "Government of El Salvador",
  "segeplan.gob.gt": "Secretaría de Planificación y Programación de la Presidencia",
  "congreso.gob.gt": "Congreso de la República de Guatemala",
  "mict.gouv.ht": "Ministère de l’Intérieur et des Collectivités Territoriales",
  "mpce.gouv.ht": "Ministère de la Planification et de la Coopération Externe",
  "tsc.gob.hn": "Tribunal Superior de Cuentas de Honduras",
  "iaip.gob.hn": "Instituto de Acceso a la Información Pública de Honduras",
  "sefin.gob.hn": "Secretaría de Finanzas de Honduras",
  "diputados.gob.mx": "Cámara de Diputados de México",
  "sedatu.gob.mx": "Secretaría de Desarrollo Agrario, Territorial y Urbano",
  "edomex.gob.mx": "Government of the State of Mexico",
  "asamblea.gob.ni": "Asamblea Nacional de Nicaragua",
  "hacienda.gob.ni": "Ministerio de Hacienda y Crédito Público de Nicaragua",
  "descentralizacion.gob.pa": "Autoridad Nacional de Descentralización de Panamá",
  "mef.gob.pa": "Ministerio de Economía y Finanzas de Panamá",
  "bacn.gov.py": "Biblioteca y Archivo Central del Congreso Nacional de Paraguay",
  "mef.gov.py": "Ministerio de Economía y Finanzas de Paraguay",
  "gob.pe": "Government of Peru",
  "one.gob.do": "Oficina Nacional de Estadística",
  "presidencia.gob.do": "Presidency of the Dominican Republic",
  "hacienda.gob.do": "Ministry of Finance of the Dominican Republic",
  "comendador.gob.do": "Ayuntamiento de Comendador",
  "gub.uy": "Government of Uruguay",
  "impo.com.uy": "IMPO — Centro de Información Oficial",
  "opp.gub.uy": "Oficina de Planeamiento y Presupuesto",
  "mppp.gob.ve": "Ministerio del Poder Popular de Planificación",
  "npa.go.ug": "National Planning Authority of Uganda",
  "ubos.org": "Uganda Bureau of Statistics",
  "sib.org.bz": "Statistical Institute of Belize",
});

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function uniqueSorted(values) {
  return [...new Set((values || []).filter((value) => typeof value === "string" && value.trim()).map((value) => value.trim()))]
    .sort((a, b) => a.localeCompare(b, "en"));
}

function authorityFromUrl(url) {
  const host = new URL(url).hostname.toLowerCase();
  if (INTERNATIONAL_HOSTS.has(host)) return "international_organization";
  if (host.endsWith(".gob.do") && host !== "www.one.gob.do") return "official_subnational";
  return "official_national";
}

function isRecognizedAuthorityUrl(url) {
  const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
  // ULII/Laws.Africa is a useful secondary legal repository, but the feedback
  // contract is limited to official or international-authority endpoints.
  if (host === "ulii.org" || host.endsWith(".ulii.org")) return false;
  return true;
}

function publisherFromUrl(url, iso3, role) {
  const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
  if (["census_catalog", "census_results", "table_catalog", "machine_readable_data", "administrative_codes"].includes(role)) {
    if (STATISTICS_PUBLISHERS[iso3]) return STATISTICS_PUBLISHERS[iso3];
  }
  const match = Object.entries(HOST_PUBLISHERS).find(([suffix]) => host === suffix || host.endsWith(`.${suffix}`));
  return match?.[1] || host;
}

function roleForResearchSource(source, country) {
  const lawSources = new Set((country.laws || []).map((entry) => entry.source).filter(Boolean));
  if (lawSources.has(source.id) || /(?:^|_)L(?:\d+|_TEXT)?$/.test(source.id) || /法令|Constituci|Ley |Código |Decreto /i.test(source.title)) return "planning_law";
  if (source.id === country.agency_source || /(?:^|_)A$/.test(source.id) || /所管機関|制度運用/.test(source.title)) return "planning_guidance";
  if (/調査票|変数辞書|導入資料|questionnaire|dictionary/i.test(source.title)) return "table_catalog";
  if (/地理|lugares poblados|AGEB|manzana|district indicators/i.test(source.title)) return "administrative_codes";
  if (/(?:^|_)C$/.test(source.id) || /国勢調査・公表資料/.test(source.title)) return "census_catalog";
  if (/REDATAM|SIDRA|microdatos|tabulad|explorador/i.test(source.title)) return "machine_readable_data";
  return "census_results";
}

function formatsFor(source, role) {
  const pathname = new URL(source.url).pathname.toLowerCase();
  const formats = [];
  if (pathname.endsWith(".pdf")) formats.push("PDF");
  else if (/\.(xlsx|xls)$/.test(pathname)) formats.push("XLSX");
  else if (pathname.endsWith(".csv")) formats.push("CSV");
  else if (pathname.endsWith(".zip")) formats.push("ZIP");
  else formats.push("HTML");
  if (/redatam/i.test(source.title + source.url)) formats.push("REDATAM");
  if (role === "machine_readable_data" && formats.length === 1 && formats[0] === "HTML") formats.push("interactive query");
  return uniqueSorted(formats);
}

function periodsForResearchSource(source, country, role) {
  const periods = [];
  if (["census_catalog", "census_results", "table_catalog", "machine_readable_data", "administrative_codes"].includes(role)) {
    if (country.census_year) periods.push(`Census ${country.census_year}`);
    if (country.usable_year && country.usable_year !== country.census_year) periods.push(`usable detailed edition ${country.usable_year}`);
  }
  for (const law of country.laws || []) {
    if (law.source === source.id && law.year) periods.push(String(law.year));
  }
  return uniqueSorted(periods.length ? periods : [`checked ${source.checked}`]);
}

function levelsForResearchSource(country, role) {
  if (["planning_law", "planning_guidance", "plans_budgets_implementation_evaluation"].includes(role)) {
    return uniqueSorted([country.planning_level || country.planning_profile?.local_role || "national and subnational planning system"]);
  }
  return uniqueSorted([country.published_geography || "national", country.finer_geography]);
}

function isExportableResearchSource(source) {
  if (!source?.url || !source?.checked) return false;
  if (source.kind === "国際比較・探索入口") return false;
  return source.kind === "統計局・公式資料"
    || source.kind === "法令・政府の制度資料"
    || source.kind === "現行機関・政府資料"
    || source.kind === "現行法令条文"
    || source.kind === "法令原文";
}

function researchSources(research, evidencePath) {
  const sourceById = new Map((research.sources || []).map((source) => [source.id, source]));
  const result = [];
  for (const country of research.countries || []) {
    const referenced = new Set();
    for (const id of country.census_sources || []) referenced.add(id);
    for (const law of country.laws || []) if (law.source) referenced.add(law.source);
    if (country.agency_source) referenced.add(country.agency_source);
    for (const id of country.planning_profile?.relation_sources || []) referenced.add(id);
    for (const theme of country.themes || []) if (theme.source) referenced.add(theme.source);
    for (const id of [...referenced].sort()) {
      const source = sourceById.get(id);
      if (!isExportableResearchSource(source)) continue;
      const role = roleForResearchSource(source, country);
      result.push({
        iso3: country.iso,
        source_id: source.id,
        role,
        title: source.title,
        publisher: publisherFromUrl(source.url, country.iso, role),
        url: source.url,
        authority_type: authorityFromUrl(source.url),
        evidence_stage: "official_location_verified",
        checked_at: source.checked,
        geographic_levels: levelsForResearchSource(country, role),
        reference_periods: periodsForResearchSource(source, country, role),
        formats: formatsFor(source, role),
        license_or_terms: null,
        reuse_note: country.caveat || "Reconfirm the current edition, access conditions and geographic correspondence before reuse.",
        origin_evidence_path: evidencePath,
        artifact_sha256: null,
      });
    }
  }
  return result;
}

const REGISTRY_ROLE_MAP = Object.freeze({
  census_catalog: "census_catalog",
  census_report: "census_results",
  planning_law: "planning_law",
  planning_guidance: "planning_guidance",
  planning_documents: "plans_budgets_implementation_evaluation",
  boundary_directory: "boundaries",
});

const REGISTRY_STAGE_MAP = Object.freeze({
  source_location_identified: "official_location_identified",
  location_verified: "official_location_verified",
  location_and_catalog_content_verified: "content_inspected",
  content_verified: "content_inspected",
  data_acquired: "source_acquired",
  geography_matched: "geography_matched",
  adopted: "indicator_adopted_in_areadata",
});

export function mapRegistryEvidenceStage(stage) {
  return REGISTRY_STAGE_MAP[stage] || null;
}

function registrySources(registry, evidencePath) {
  const result = [];
  for (const country of registry.countries || []) {
    for (const source of country.sources || []) {
      const role = REGISTRY_ROLE_MAP[source.role];
      const evidenceStage = mapRegistryEvidenceStage(source.stage);
      if (!role || !evidenceStage || source.stage === "negative_availability_verified" || !isRecognizedAuthorityUrl(source.url)) continue;
      const isPlanning = role.startsWith("planning") || role === "plans_budgets_implementation_evaluation";
      result.push({
        iso3: country.iso3,
        source_id: source.id,
        role,
        title: source.title,
        publisher: source.publisher,
        url: source.url,
        authority_type: authorityFromUrl(source.url),
        evidence_stage: evidenceStage,
        checked_at: country.checked_at || registry.as_of,
        geographic_levels: uniqueSorted([isPlanning ? country.planning?.planning_level : country.census?.published_geography]),
        reference_periods: uniqueSorted([
          isPlanning ? `checked ${country.checked_at || registry.as_of}` : country.census?.latest_census_year ? `Census ${country.census.latest_census_year}` : null,
          !isPlanning && country.census?.usable_detailed_year && country.census.usable_detailed_year !== country.census.latest_census_year
            ? `usable detailed edition ${country.census.usable_detailed_year}` : null,
        ]),
        formats: uniqueSorted(source.url.toLowerCase().includes(".pdf") ? ["PDF"] : ["HTML"]),
        license_or_terms: null,
        reuse_note: source.note,
        origin_evidence_path: evidencePath,
        artifact_sha256: null,
      });
    }
  }
  return result;
}

export function assertPublicSourceUrl(value) {
  let parsed;
  try { parsed = new URL(value); } catch { throw new Error(`Source URL is invalid: ${value}`); }
  if (!/^https?:$/.test(parsed.protocol)) throw new Error(`Source URL must use public HTTP(S): ${value}`);
  if (parsed.username || parsed.password) throw new Error(`Source URL contains credentials: ${value}`);
  const host = parsed.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".local") || host === "::1" || host === "0.0.0.0" || host.startsWith("127.")) {
    throw new Error(`Source URL is local or loopback: ${value}`);
  }
  if (/^(?:10\.|192\.168\.|169\.254\.)/.test(host) || /^172\.(?:1[6-9]|2\d|3[01])\./.test(host)) {
    throw new Error(`Source URL uses a private address: ${value}`);
  }
  for (const name of parsed.searchParams.keys()) {
    if (SECRET_QUERY_NAMES.test(name)) throw new Error(`Source URL contains a secret query parameter: ${name}`);
  }
  return parsed.toString();
}

function assertEvidencePath(repoRoot, relativePath, originCommit, verifyGitEvidence) {
  if (typeof relativePath !== "string" || !relativePath.trim()) throw new Error("origin_evidence_path is required");
  const normalized = relativePath.replaceAll("\\", "/");
  if (path.isAbsolute(relativePath) || /^[A-Za-z]:/.test(relativePath) || normalized.split("/").includes("..")) {
    throw new Error(`Evidence path must be repository-relative: ${relativePath}`);
  }
  if (/(^|\/)raw(\/|$)/i.test(normalized)) throw new Error(`Raw artifact paths cannot be exported: ${relativePath}`);
  const absolute = path.join(repoRoot, ...normalized.split("/"));
  if (!fs.existsSync(absolute)) throw new Error(`Evidence path does not exist: ${relativePath}`);
  if (verifyGitEvidence) {
    const cacheKey = `${path.resolve(repoRoot)}\u0000${originCommit}`;
    if (!COMMIT_FILE_CACHE.has(cacheKey)) {
      const names = execFileSync("git", ["ls-tree", "-r", "--name-only", originCommit], { cwd: repoRoot, encoding: "utf8" });
      COMMIT_FILE_CACHE.set(cacheKey, new Set(names.split(/\r?\n/).filter(Boolean)));
    }
    if (!COMMIT_FILE_CACHE.get(cacheKey).has(normalized)) {
      throw new Error(`Evidence path is not present at origin_commit ${originCommit}: ${relativePath}`);
    }
  }
  return normalized;
}

function compareSources(a, b) {
  return a.iso3.localeCompare(b.iso3, "en")
    || a.role.localeCompare(b.role, "en")
    || a.url.localeCompare(b.url, "en")
    || a.source_id.localeCompare(b.source_id, "en");
}

function mergeDuplicate(current, candidate) {
  const stronger = (STAGE_RANK.get(candidate.evidence_stage) || 0) > (STAGE_RANK.get(current.evidence_stage) || 0) ? candidate : current;
  return {
    ...stronger,
    geographic_levels: uniqueSorted([...current.geographic_levels, ...candidate.geographic_levels]),
    reference_periods: uniqueSorted([...current.reference_periods, ...candidate.reference_periods]),
    formats: uniqueSorted([...current.formats, ...candidate.formats]),
  };
}

export function deduplicateFeedbackSources(sources) {
  const byKey = new Map();
  for (const source of [...sources].sort(compareSources)) {
    const canonicalUrl = assertPublicSourceUrl(source.url);
    const normalized = { ...source, url: canonicalUrl };
    const key = `${normalized.iso3}\u0000${normalized.role}\u0000${canonicalUrl}`;
    byKey.set(key, byKey.has(key) ? mergeDuplicate(byKey.get(key), normalized) : normalized);
  }
  return [...byKey.values()].sort(compareSources);
}

export function validateKitSourceFeedbackBundle(bundle, options = {}) {
  const repoRoot = options.repoRoot || process.cwd();
  const verifyGitEvidence = options.verifyGitEvidence !== false;
  if (!bundle || typeof bundle !== "object" || Array.isArray(bundle)) throw new Error("Feedback bundle must be an object");
  for (const key of Object.keys(bundle)) if (!TOP_KEYS.has(key)) throw new Error(`Unknown bundle field: ${key}`);
  for (const key of TOP_KEYS) if (!(key in bundle)) throw new Error(`Missing bundle field: ${key}`);
  if (bundle.schema_version !== KIT_SOURCE_FEEDBACK_VERSION) throw new Error("schema_version must be 1.0");
  if (bundle.produced_by !== "AreaData") throw new Error("produced_by must be AreaData");
  if (!/^\d{4}-\d{2}-\d{2}T/.test(bundle.exported_at) || Number.isNaN(Date.parse(bundle.exported_at))) throw new Error("exported_at must be an ISO date-time");
  if (!/^[0-9a-f]{40}$/.test(bundle.origin_commit)) throw new Error("origin_commit must be a 40-character lowercase commit hash");
  if (!Array.isArray(bundle.sources)) throw new Error("sources must be an array");
  const duplicateKeys = new Set();
  for (const [index, source] of bundle.sources.entries()) {
    if (!source || typeof source !== "object" || Array.isArray(source)) throw new Error(`sources[${index}] must be an object`);
    for (const key of Object.keys(source)) if (!SOURCE_KEYS.has(key)) throw new Error(`Unknown source field at ${index}: ${key}`);
    for (const key of REQUIRED_SOURCE_KEYS) if (!(key in source)) throw new Error(`Missing source field at ${index}: ${key}`);
    if (!/^[A-Z]{3}$/.test(source.iso3)) throw new Error(`Invalid ISO3 at ${index}`);
    if (!/^[A-Z0-9][A-Z0-9_.-]+$/.test(source.source_id)) throw new Error(`Invalid source_id at ${index}`);
    if (!ROLES.has(source.role)) throw new Error(`Invalid role at ${index}`);
    if (!AUTHORITY_TYPES.has(source.authority_type)) throw new Error(`Invalid authority_type at ${index}`);
    if (!STAGE_RANK.has(source.evidence_stage)) throw new Error(`Invalid evidence_stage at ${index}`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(source.checked_at) || Number.isNaN(Date.parse(`${source.checked_at}T00:00:00Z`))) throw new Error(`Invalid checked_at at ${index}`);
    for (const field of ["title", "publisher", "reuse_note"]) if (typeof source[field] !== "string" || !source[field].trim()) throw new Error(`${field} is required at ${index}`);
    for (const field of ["geographic_levels", "reference_periods", "formats"]) {
      if (!Array.isArray(source[field])) throw new Error(`${field} must be an array at ${index}`);
      if (source[field].some((value) => typeof value !== "string" || !value.trim())) throw new Error(`${field} contains an empty value at ${index}`);
      if (new Set(source[field]).size !== source[field].length) throw new Error(`${field} contains duplicates at ${index}`);
    }
    source.url = assertPublicSourceUrl(source.url);
    source.origin_evidence_path = assertEvidencePath(repoRoot, source.origin_evidence_path, bundle.origin_commit, verifyGitEvidence);
    if (source.artifact_sha256 != null && !/^[0-9a-f]{64}$/.test(source.artifact_sha256)) throw new Error(`Invalid artifact_sha256 at ${index}`);
    if (source.license_or_terms != null && typeof source.license_or_terms !== "string") throw new Error(`Invalid license_or_terms at ${index}`);
    const duplicateKey = `${source.iso3}\u0000${source.role}\u0000${source.url}`;
    if (duplicateKeys.has(duplicateKey)) throw new Error(`Duplicate country/role/URL at ${index}`);
    duplicateKeys.add(duplicateKey);
  }
  const sorted = [...bundle.sources].sort(compareSources);
  if (JSON.stringify(sorted) !== JSON.stringify(bundle.sources)) throw new Error("sources are not in deterministic order");
  return bundle;
}

export function buildKitSourceFeedbackBundle({
  repoRoot = process.cwd(),
  originCommit,
  exportedAt,
  countryRegistryPath = "config/country-source-registry.json",
  regionalResearchPath = "docs/research/latin-america-2026/research.json",
  verifyGitEvidence = true,
} = {}) {
  const commit = originCommit || execFileSync("git", ["rev-parse", "HEAD"], { cwd: repoRoot, encoding: "utf8" }).trim();
  const timestamp = exportedAt || new Date(execFileSync("git", ["show", "-s", "--format=%cI", commit], { cwd: repoRoot, encoding: "utf8" }).trim()).toISOString();
  const registry = readJson(path.join(repoRoot, countryRegistryPath));
  const research = readJson(path.join(repoRoot, regionalResearchPath));
  const sources = deduplicateFeedbackSources([
    ...registrySources(registry, countryRegistryPath.replaceAll("\\", "/")),
    ...researchSources(research, regionalResearchPath.replaceAll("\\", "/")),
  ]);
  const bundle = {
    schema_version: KIT_SOURCE_FEEDBACK_VERSION,
    produced_by: "AreaData",
    exported_at: timestamp,
    origin_commit: commit,
    sources,
  };
  return validateKitSourceFeedbackBundle(bundle, { repoRoot, verifyGitEvidence });
}

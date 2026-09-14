import {validatePlanning,isRawEvidencePath} from './planning-validation.mjs';
import {validateAnalysis} from './analysis-validation.mjs';

/** Validate the data contract before any dashboard is published or rebuilt. */
export function validateDataset(data) {
  const errors = [], warnings = [];
  const fail = message => errors.push(message);
  const string = value => typeof value === 'string' && value.trim().length > 0;
  const https = value => { try { const url=new URL(value);return url.protocol === 'https:' && !url.username && !url.password; } catch { return false; } };
  if (!data || typeof data !== 'object' || Array.isArray(data)) return { errors: ['Dataset must be an object'], warnings };
  if (data.schema_version !== '0.2') fail('schema_version must be 0.2');
  if (!string(data.generated_at) || !Number.isFinite(Date.parse(data.generated_at))) fail('generated_at must be a valid date');
  if (!data.country || !/^[A-Z0-9]{3}$/.test(data.country.id ?? '') || !string(data.country.name)) fail('country needs a three-character identifier and name');
  for (const key of ['territories', 'indicators', 'observations', 'sources', 'documents', 'gaps']) {
    if (!Array.isArray(data[key])) fail(`${key} must be an array`);
  }
  if (errors.length) return { errors, warnings };
  const unique = (list, label) => {
    const map = new Map();
    for (const row of list) {
      if (!row || !string(row.id)) { fail(`${label} needs an id`); continue; }
      if (map.has(row.id)) fail(`Duplicate ${label} id: ${row.id}`);
      map.set(row.id, row);
    }
    return map;
  };
  const territories = unique(data.territories, 'territory');
  const indicators = unique(data.indicators, 'indicator');
  const sources = unique(data.sources, 'source');
  unique(data.documents, 'document');
  const national = territories.get(data.country.national_territory_id);
  if (!national || national.level !== 'national') fail('country.national_territory_id must identify the national territory');
  for (const t of territories.values()) {
    if (!string(t.name) || !string(t.level) || !string(t.type)) fail(`Territory ${t.id} needs name, level and type`);
    if (t.parent_id != null && !territories.has(t.parent_id)) fail(`Unknown parent for ${t.id}`);
    if (t.id === t.parent_id) fail(`Territory ${t.id} cannot be its own parent`);
    const seen = new Set([t.id]);
    let parent = t.parent_id;
    while (parent && territories.has(parent)) {
      if (seen.has(parent)) { fail(`Territory cycle at ${t.id}`); break; }
      seen.add(parent); parent = territories.get(parent).parent_id;
    }
    if (t.official_code != null && !string(t.code_system)) fail(`Official code for ${t.id} needs a code_system`);
  }
  for (const i of indicators.values()) {
    for (const key of ['name', 'theme', 'unit', 'definition']) if (!string(i[key])) fail(`Indicator ${i.id} needs ${key}`);
    if (!sources.has(i.source_id)) fail(`Unknown source for indicator ${i.id}`);
    if (!['none', 'sum', 'weighted_rate', 'official_only'].includes(i.aggregation)) fail(`Invalid aggregation for ${i.id}`);
    if (i.series_family != null && !['census','international_reference','administrative','survey','humanitarian'].includes(i.series_family)) fail(`Invalid series_family for ${i.id}`);
    if (i.display_role != null && !['primary','context','supplementary'].includes(i.display_role)) fail(`Invalid display_role for ${i.id}`);
  }
  const sourceStates = new Set(['ready', 'partial', 'failed', 'unavailable', 'not_collected']);
  for (const s of sources.values()) {
    if (!string(s.name) || !https(s.url)) fail(`Source ${s.id} needs a name and HTTPS URL`);
    if (!sourceStates.has(s.status)) fail(`Unknown source status ${s.id}`);
    if (!string(s.retrieved_at) || !Number.isFinite(Date.parse(s.retrieved_at))) fail(`Source ${s.id} needs retrieval date`);
    if (s.sha256 != null && !/^[a-f0-9]{64}$/i.test(s.sha256)) fail(`Invalid source SHA-256 ${s.id}`);
    if (s.raw_path != null && !isRawEvidencePath(s.raw_path)) fail(`Unsafe raw_path for ${s.id}`);
    if (!s.license) warnings.push(`Source terms need review: ${s.id}`);
  }
  const observationKeys = new Set();
  const states = new Set(['observed', 'missing', 'not_applicable', 'suppressed']);
  for (const o of data.observations) {
    if (!o || typeof o !== 'object') { fail('Observation must be an object'); continue; }
    if (!territories.has(o.territory_id)) fail(`Unknown observation territory ${o.territory_id}`);
    if (!indicators.has(o.indicator_id)) fail(`Unknown observation indicator ${o.indicator_id}`);
    if (!sources.has(o.source_id)) fail(`Unknown observation source ${o.source_id}`);
    if (!string(o.period)) fail('Observation needs period');
    if (!states.has(o.status)) fail('Invalid observation status');
    if (o.status === 'observed' && (typeof o.value !== 'number' || !Number.isFinite(o.value))) fail('Observed value must be a finite number; null is not zero');
    if (o.status !== 'observed' && o.value !== null) fail('Missing, suppressed and inapplicable values must be null');
    if (o.dimension != null) fail('Observation dimensions require separate indicator IDs or an explicit renderer/schema extension');
    const key = JSON.stringify([o.territory_id, o.indicator_id, o.period]);
    if (observationKeys.has(key)) fail(`Duplicate observation ${key}`);
    observationKeys.add(key);
  }
  if (!data.boundaries || data.boundaries.type !== 'FeatureCollection' || !Array.isArray(data.boundaries.features)) fail('boundaries must be a GeoJSON FeatureCollection');
  else for (const feature of data.boundaries.features) {
    if (feature?.type !== 'Feature' || !territories.has(feature?.properties?.territory_id)) fail('Boundary needs a known territory_id');
    if (!['Polygon', 'MultiPolygon'].includes(feature?.geometry?.type)) fail('Boundary geometry must be Polygon or MultiPolygon');
    else {
      const polygons = feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
      if (!Array.isArray(polygons) || !polygons.length) { fail('Empty boundary geometry'); continue; }
      for (const rings of polygons) {
        if (!Array.isArray(rings) || !rings.length) { fail('Empty polygon'); continue; }
        for (const ring of rings) {
          if (!Array.isArray(ring) || ring.length < 4) { fail('Polygon ring needs four coordinates'); continue; }
          for (const xy of ring) if (!Array.isArray(xy) || xy.length < 2 || !Number.isFinite(xy[0]) || !Number.isFinite(xy[1]) || Math.abs(xy[0]) > 180 || Math.abs(xy[1]) > 90) fail('Invalid geographic coordinate');
          const a = ring[0], b = ring.at(-1);
          if (Array.isArray(a) && Array.isArray(b) && (a[0] !== b[0] || a[1] !== b[1])) fail('Polygon ring must be closed');
        }
      }
    }
  }
  for (const d of data.documents) {
    if (!d || typeof d !== 'object') continue; // unique() already reported this malformed row.
    if (!territories.has(d.territory_id)) fail(`Unknown document territory ${d.id}`);
    if (!string(d.title) || !https(d.url)) fail(`Document ${d.id} needs title and HTTPS URL`);
    if (!sources.has(d.source_id)) fail(`Document ${d.id} needs registered source`);
    if (!string(d.availability) || !string(d.official_status)) fail(`Document ${d.id} needs availability and official_status separately`);
  }
  if (!data.collection || !['complete', 'partial', 'failed'].includes(data.collection.status)) fail('collection.status must describe the collection outcome');
  const observed = data.observations.filter(o => o?.status === 'observed');
  if (!observed.length) warnings.push('No usable numeric observations collected');
  if (!observed.some(o => o.territory_id !== data.country.national_territory_id)) warnings.push('National statistics only: subnational collection is still required for local comparison');
  if (!data.documents.length) warnings.push('No verified country-specific planning documents collected');
  const planningResult=validatePlanning(data);
  errors.push(...planningResult.errors);warnings.push(...planningResult.warnings);
  const analysisResult=validateAnalysis(data);
  errors.push(...analysisResult.errors);warnings.push(...analysisResult.warnings);
  return { errors: [...new Set(errors)], warnings: [...new Set(warnings)] };
}

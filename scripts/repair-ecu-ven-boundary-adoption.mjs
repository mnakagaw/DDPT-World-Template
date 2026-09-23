import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const projectIndex = args.indexOf('--project');
const projectArg = projectIndex >= 0 ? args[projectIndex + 1] : null;
if (!projectArg) {
  console.error('Usage: node scripts/repair-ecu-ven-boundary-adoption.mjs --project <project>');
  process.exit(2);
}

const project = path.resolve(projectArg);
const preflightPath = path.join(project, 'evidence', 'SOURCE_PREFLIGHT.json');
const preflight = JSON.parse(fs.readFileSync(preflightPath, 'utf8'));
const expected = {
  ECU: {
    object_path: 'raw/ECU/reference-adm1.geojson',
    object_sha256: '6d98acf5a252ec34b77a750e77d880c72b92bdfd52da39cacec255d2d83239fa',
  },
  VEN: {
    object_path: 'raw/VEN/reference-adm1.geojson',
    object_sha256: '720239610e832cef12893939b27e0e3e548095b949b0f486071e640654143f5a',
  },
};

const hashFile = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const changes = [];
for (const [countryId, expectedEvidence] of Object.entries(expected)) {
  const country = preflight.countries.find(row => row.country_area_id === countryId);
  if (!country) throw new Error(`Missing preflight country: ${countryId}`);
  const domain = country.adm1_adm2_boundaries;
  const evidence = domain?.evidence?.find(row => row.object_path === expectedEvidence.object_path);
  if (!evidence) throw new Error(`Missing retained boundary evidence: ${countryId}`);
  const objectPath = path.join(project, evidence.object_path);
  if (!fs.existsSync(objectPath)) throw new Error(`Missing retained boundary object: ${evidence.object_path}`);
  const actual = hashFile(objectPath);
  if (actual !== expectedEvidence.object_sha256 || actual !== evidence.object_sha256) {
    throw new Error(`Boundary evidence hash mismatch: ${countryId}`);
  }
  if (!evidence.geography_match) throw new Error(`Missing geography_match: ${countryId}`);
  domain.status = 'adopted';
  domain.identified = true;
  domain.accessed = true;
  domain.acquired = true;
  domain.inspected = true;
  domain.geography_matched = true;
  domain.adopted = true;
  domain.completion_verified = true;
  evidence.disposition = 'adopted';
  changes.push({country_area_id: countryId, object_path: evidence.object_path, object_sha256: actual});
}

fs.writeFileSync(preflightPath, `${JSON.stringify(preflight)}\n`, 'utf8');
const receipt = {
  schema_version: '1.0',
  repaired_at: new Date().toISOString(),
  changes,
  note: 'Marks the retained and hash-verified ADM1 reference geometries as adopted display boundaries after explicit geography matching. This is not legal boundary certification and does not claim ADM2 coverage.',
};
fs.writeFileSync(path.join(project, 'evidence', 'ECU_VEN_BOUNDARY_ADOPTION_REPAIR.json'), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(receipt, null, 2));

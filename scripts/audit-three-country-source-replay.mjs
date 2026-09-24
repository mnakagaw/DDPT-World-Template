// Read-only replay preflight for the three local AreaData adaptations.
// It verifies retained source bytes and Kit-to-AreaData data arrays, not every workbook cell.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const projects = {
  BGD: 'generated/bangladesh-areadata-20260924-v2',
  LAO: 'generated/laos-areadata-20260924',
  UGA: 'generated/uganda-areadata-20260924',
};
const ubosWorkbookHash = '609d74158d2aeace11c2ca64df6ae882fd7482886f2184494628cf1e32f6b202';

function sha(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
async function json(file) { return JSON.parse(await readFile(file, 'utf8')); }
async function checkFile(base, relative, expected, errors) {
  if (path.isAbsolute(relative) || relative.split(/[\\/]/).includes('..')) throw new Error(`unsafe evidence path: ${relative}`);
  try {
    const actual = sha(await readFile(path.join(base, relative)));
    if (actual !== expected.toLowerCase()) errors.push(`${relative}: SHA-256 mismatch`);
    return actual === expected.toLowerCase();
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    errors.push(`${relative}: missing`);
    return false;
  }
}

async function auditInventory(project, catalogFilter, errors) {
  const inventory = await json(path.join(project, 'evidence/SOURCE_RESOURCE_INVENTORY.json'));
  const resources = inventory.catalogs.filter(catalog => !catalogFilter || catalog.catalog_id === catalogFilter)
    .flatMap(catalog => catalog.resources || []).filter(resource => resource.raw_path && resource.sha256);
  let matched = 0;
  for (const resource of resources) if (await checkFile(project, resource.raw_path, resource.sha256, errors)) matched++;
  return { inventoried: resources.length, hash_matched: matched };
}

async function auditKitArrays(areaProject, kitProject, errors) {
  const [area, kit] = await Promise.all([
    json(path.join(areaProject, 'data/dashboard.json')),
    json(path.join(kitProject, 'data/dashboard.json')),
  ]);
  const fields = ['territories', 'indicators', 'observations', 'sources', 'documents'];
  const matching = [];
  for (const field of fields) {
    if (sha(JSON.stringify(area[field])) === sha(JSON.stringify(kit[field]))) matching.push(field);
    else errors.push(`${area.country.id}.${field}: differs from current Kit country project`);
  }
  return { compared: fields, matching };
}

async function main() {
  const kitProjects = process.argv[2];
  if (!kitProjects) throw new Error('Usage: node scripts/audit-three-country-source-replay.mjs <Kit country-project parent directory>');
  const errors = [], warnings = [];
  const bgd = path.join(root, projects.BGD);
  const lao = path.join(root, projects.LAO);
  const uga = path.join(root, projects.UGA);
  const laoDataset = await json(path.join(lao, 'data/dashboard.json'));
  const result = {
    BGD: {
      community_workbooks: await auditInventory(bgd, 'bgd-bbs-phc-2022-district-community-series', errors),
      dataset_arrays: await auditKitArrays(bgd, path.join(kitProjects, 'bgd'), errors),
    },
    LAO: {
      source_artifacts: await auditInventory(lao, null, errors),
      dataset_arrays: await auditKitArrays(lao, path.join(kitProjects, 'lao'), errors),
      ready_without_local_raw: laoDataset.sources.filter(source => source.status === 'ready' && !source.raw_path).map(source => source.id),
    },
  };
  if (result.LAO.ready_without_local_raw.length) warnings.push(`${result.LAO.ready_without_local_raw.length} Lao sources are ready in the inherited dataset but have no local raw_path; check source-body evidence before release`);
  const origin = await json(path.join(uga, 'evidence/IMPORT_ORIGIN.json'));
  let ugandaMatched = 0;
  for (const file of origin.source_files) {
    if (await checkFile(uga, `raw/${file.name}`, file.sha256, errors)) ugandaMatched++;
  }
  const workbookMatched = await checkFile(uga, 'raw/NPHC-2024-Subcounty-Profiles-Excel-Tables.xlsx', ubosWorkbookHash, errors);
  const uganda = await json(path.join(uga, 'data/dashboard.json'));
  const readyWithoutRaw = uganda.sources.filter(source => source.status === 'ready' && !source.raw_path).map(source => source.id);
  if (readyWithoutRaw.length) warnings.push(`${readyWithoutRaw.length} Uganda sources are ready in the inherited dataset but have no local raw_path; check source-body evidence before release`);
  result.UGA = {
    normalized_source_files: { expected: origin.source_files.length, hash_matched: ugandaMatched },
    official_ubos_workbook: { hash_matched: workbookMatched, sha256: ubosWorkbookHash },
    ready_without_local_raw: readyWithoutRaw,
  };
  console.log(JSON.stringify({ audited_at: new Date().toISOString(), result, errors, warnings,
    verdict: errors.length ? 'FAIL' : 'SOURCE_BYTES_REPLAYABLE_BUT_INDEPENDENT_CONTENT_AUDIT_PENDING' }, null, 2));
  if (errors.length) process.exitCode = 1;
}

main().catch(error => { console.error(error); process.exitCode = 1; });

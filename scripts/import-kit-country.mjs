import path from 'node:path';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile, copyFile, lstat } from 'node:fs/promises';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';
import { validateDataset } from '../lib/validate.mjs';

const evidenceNames = [
  'ACCEPTANCE.md', 'COUNTRY_LESSON_AUDIT.md', 'DELIVERY.json',
  'GEOGRAPHY_REVIEW.md', 'PLANNING_CENSUS_AUDIT.md',
  'SOURCE_RESOURCE_INVENTORY.json', 'SOURCE_TABLE_INVENTORY.json',
  'SOURCES.md', 'THEME_COVERAGE.json', 'VALIDATION.md',
];
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

/** Import a previously acquired schema-0.2 country dataset without changing its values. */
export async function importKitCountry({ source, out }) {
  if (!source || !out) throw new Error('Provide --source <Kit country> --out <new AreaData project>');
  const from = path.resolve(source), target = path.resolve(out);
  if (await lstat(target).catch(error => error.code === 'ENOENT' ? null : Promise.reject(error))) {
    throw new Error(`Output already exists: ${target}`);
  }
  const original = await readFile(path.join(from, 'data', 'dashboard.json'));
  const dataset = JSON.parse(original.toString('utf8'));
  if (dataset.schema_version !== '0.2' || !dataset.country?.id) throw new Error('Source is not a country schema-0.2 dataset');
  const unsupportedOutputs = (dataset.planning?.outputs || []).filter(format => format === 'docx');
  if (dataset.planning?.outputs) dataset.planning.outputs = dataset.planning.outputs.filter(format => format !== 'docx');
  // The country validator requires acquired document evidence to remain
  // traceable to its exact source bytes. Copy only referenced raw files.
  const archivedRawPaths = dataset.sources.filter(item => item.raw_path).map(item => ({ source_id: item.id, path: item.raw_path }));
  const validation = validateDataset(dataset);
  if (validation.errors.length) throw new Error(`Imported dataset rejected: ${validation.errors.slice(0, 8).join('; ')}`);
  await mkdir(path.join(target, 'data'), { recursive: true });
  await mkdir(path.join(target, 'evidence'), { recursive: true });
  await mkdir(path.join(target, 'raw'), { recursive: true });
  for (const item of archivedRawPaths) {
    const sourceFile = path.resolve(from, item.path);
    const destination = path.resolve(target, item.path);
    if (!sourceFile.startsWith(from + path.sep) || !destination.startsWith(target + path.sep) || !/^(?:raw|evidence)\//.test(item.path.replaceAll('\\', '/'))) {
      throw new Error(`Unsafe raw source path: ${item.path}`);
    }
    await mkdir(path.dirname(destination), { recursive: true });
    await copyFile(sourceFile, destination);
  }
  const converted = Buffer.from(JSON.stringify(dataset));
  await writeFile(path.join(target, 'data', 'dashboard.json'), converted);
  const copied = [];
  for (const name of evidenceNames) {
    const oldFile = path.join(from, 'evidence', name);
    if (await lstat(oldFile).catch(error => error.code === 'ENOENT' ? null : Promise.reject(error))) {
      await copyFile(oldFile, path.join(target, 'evidence', name));
      copied.push(name);
    }
  }
  const manifest = {
    country_id: dataset.country.id,
    imported_at: new Date().toISOString(),
    origin_project: from,
    origin_dataset_sha256: sha256(original),
    areadata_dataset_sha256: sha256(converted),
    data_values_changed: false,
    changes: ['Removed unsupported DOCX from AreaData planning output settings', 'Retained calculation inputs in database while hiding them from diagnosis cards', 'Copied raw files referenced by adopted sources'],
    unsupported_outputs: unsupportedOutputs,
    copied_evidence: copied,
    copied_raw_paths: archivedRawPaths,
    validation,
    independent_areadata_audit: 'pending',
  };
  await writeFile(path.join(target, 'evidence', 'IMPORT_ORIGIN.json'), JSON.stringify(manifest, null, 2) + '\n');
  await writeFile(path.join(target, 'HANDOFF.md'), `# ${dataset.country.name} AreaData handoff\n\nThe AreaData schema-0.2 dataset was imported from the existing country Kit project at ${from}. See evidence/IMPORT_ORIGIN.json for hashes, evidence copies and adopted raw-file locations. The original project was not modified. DOCX is available only in the origin Kit; this AreaData build offers its supported planning exports.\n\nRun \`node scripts/validate-country.mjs --project ${target}\` and \`node scripts/build-country.mjs --project ${target}\` from the AreaData template root. Check actual maps, area selection, thematic comparison and exported content. This is an AreaData adaptation pending its own independent audit and is not authorized as a completed published edition.\n`);
  return { target, country: dataset.country.id, territories: dataset.territories.length, indicators: dataset.indicators.length, observations: dataset.observations.length, warnings: validation.warnings.length };
}

if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['source', 'out']);
    console.log(JSON.stringify(await importKitCountry(args), null, 2));
  } catch (error) { reportError(error); }
}

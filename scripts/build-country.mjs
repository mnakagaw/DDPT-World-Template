import path from 'node:path';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { generateSite } from '../lib/generate.mjs';
import { validateDataset } from '../lib/validate.mjs';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';
export async function buildCountry(project) {
  if (!project) throw new Error('Provide --project <country directory>');
  const outDir = path.resolve(project);
  const dataset = JSON.parse(await readFile(path.join(outDir, 'data', 'dashboard.json'), 'utf8'));
  const result = validateDataset(dataset);
  if (!dataset.observations?.some(o => o?.status === 'observed' && Number.isFinite(o.value))) result.errors.push('No usable numeric observations; an empty data build is not successful');
  await mkdir(path.join(outDir, 'evidence'), { recursive: true });
  await writeFile(path.join(outDir, 'evidence', 'validation.json'), JSON.stringify({ ...result, checked_at: new Date().toISOString(), dataset_sha256: createHash('sha256').update(JSON.stringify(dataset)).digest('hex') }, null, 2) + '\n');
  if (result.errors.length) throw new Error(result.errors.join('; '));
  await generateSite({ dataset, outDir });
  console.log(`Built: ${path.join(outDir, 'site')}`);
  return result;
}
if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['project']);
    if (args.help) console.log('node scripts/build-country.mjs --project generated/uganda');
    else await buildCountry(args.project);
  } catch (error) { reportError(error); }
}

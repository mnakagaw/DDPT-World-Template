import { mkdir, lstat, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { collectWorld } from '../lib/collect-world.mjs';
import { generateSite } from '../lib/generate.mjs';
import { validateDataset } from '../lib/validate.mjs';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';
import { readTemplateReference } from './create-country.mjs';

export async function createWorld({ out, sourceDir, startYear, endYear, collect = collectWorld, generate = generateSite } = {}) {
  const outDir = path.resolve(out || 'generated/world');
  try { await lstat(outDir); throw new Error(`Output already exists; choose a new directory: ${outDir}`); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  await mkdir(path.dirname(outDir), { recursive: true });
  await mkdir(outDir);
  const rawDir = path.join(outDir, 'raw'); await mkdir(rawDir);
  try {
    const dataset = await collect({ rawDir, sourceDir, startYear, endYear, onProgress: message => console.log(message) });
    const validation = validateDataset(dataset), content = JSON.stringify(dataset, null, 2) + '\n';
    await mkdir(path.join(outDir, 'evidence'));
    await writeFile(path.join(outDir, 'evidence/validation.json'), JSON.stringify({ ...validation, dataset_sha256: createHash('sha256').update(content).digest('hex'), checked_at: new Date().toISOString() }, null, 2) + '\n');
    // Preserve the collected draft even when a validator rejects it, for diagnosis and replay.
    await mkdir(path.join(outDir, 'data'));
    await writeFile(path.join(outDir, 'data/dashboard.json'), content);
    if (validation.errors.length) throw new Error(`Collected world data failed validation: ${validation.errors.join('; ')}`);
    if (!dataset.observations.some(o => o.status === 'observed')) throw new Error('No numeric data collected; an empty shell is not a successful world build.');
    await generate({ dataset, outDir });
    await writeFile(path.join(outDir, 'TEMPLATE_REFERENCE.json'), JSON.stringify(await readTemplateReference(), null, 2) + '\n');
    await writeFile(path.join(outDir, 'WORLD_ADAPTER.md'), await readFile(new URL('../docs/WORLD_ADAPTER.md', import.meta.url), 'utf8'));
    await writeFile(path.join(outDir, 'HANDOFF.md'), `# World exploration\n\nStart with WORLD_ADAPTER.md, TEMPLATE_REFERENCE.json, data/dashboard.json and raw/collection-receipt.json. This is a world exploration dataset, not a country administrative dashboard. Country sites are separately collected datasets and are linked only after their identity and local target are verified. Keep source code in the template/adapters; generated site files can be rebuilt.\n\nNo country sums or rate averages substitute for official World, continent or custom-region series. Boundary map units are cartographic reference material, not legal/statistical boundaries. Replay the archived request set with --source-dir <this project>/raw and a new --out. Local hosting and publication are separate actions.\n`);
    console.log(`Created: ${outDir}`);
    return { outDir, dataset, validation };
  } catch (error) {
    await writeFile(path.join(outDir, 'COLLECTION_FAILED.txt'), `${new Date().toISOString()}\n${error.message}\nAcquired raw evidence and any collected dataset are retained. Use a new output directory.\n`);
    throw error;
  }
}

if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['out', 'source-dir', 'start-year', 'end-year']);
    if (args.help) console.log('node scripts/create-world.mjs --out generated/world [--start-year 2021 --end-year 2026] [--source-dir previous-world/raw]\nCreates a new project only. --source-dir replays SHA-verified originals without network access. Default: current year and five preceding years. No deployment.');
    else await createWorld({ out: args.out, sourceDir: args['source-dir'], startYear: args['start-year'] === undefined ? undefined : Number(args['start-year']), endYear: args['end-year'] === undefined ? undefined : Number(args['end-year']) });
  } catch (error) { reportError(error); }
}

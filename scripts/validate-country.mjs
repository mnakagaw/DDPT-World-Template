import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { validateDataset } from '../lib/validate.mjs';
import { parseArgs, reportError } from '../lib/cli.mjs';
try {
  const args = parseArgs(process.argv.slice(2), ['project']);
  if (args.help) console.log('node scripts/validate-country.mjs --project generated/uganda');
  else {
    if (!args.project) throw new Error('Provide --project <country directory>');
    const data = JSON.parse(await readFile(path.resolve(args.project, 'data/dashboard.json'), 'utf8'));
    const result = validateDataset(data);
    console.log(JSON.stringify(result, null, 2));
    if (result.errors.length) process.exitCode = 1;
  }
} catch (error) { reportError(error); }

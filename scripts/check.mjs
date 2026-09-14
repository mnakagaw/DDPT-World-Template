import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const roots = ['lib', 'scripts', 'scaffold', 'tests', 'examples'];
let count = 0;
async function walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) await walk(file);
    else if (file.endsWith('.mjs')) {
      const result = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
      if (result.status !== 0) throw new Error(`Syntax error: ${file}`);
      count++;
    }
  }
}
for (const root of roots) await walk(root);
JSON.parse(await readFile('package.json', 'utf8'));
JSON.parse(await readFile('templates/country-profile.json', 'utf8'));
JSON.parse(await readFile('config/world-membership.json', 'utf8'));
JSON.parse(await readFile('config/common-subnational-sources.json', 'utf8'));
JSON.parse(await readFile('config/country-source-registry.json', 'utf8'));
console.log(`Syntax checked ${count} JavaScript modules and JSON templates.`);

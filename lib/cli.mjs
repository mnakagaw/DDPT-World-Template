import path from 'node:path';
import { fileURLToPath } from 'node:url';
export function parseArgs(argv, allowed) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (key === '--help' || key === '-h') { args.help = true; continue; }
    if (!key.startsWith('--') || !allowed.includes(key.slice(2))) throw new Error(`Unknown argument: ${key}`);
    if (Object.hasOwn(args, key.slice(2))) throw new Error(`Duplicate argument: ${key}`);
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error(`Missing value for ${key}`);
    args[key.slice(2)] = value;
  }
  return args;
}
export function isMain(metaUrl) { return process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(metaUrl); }
export function reportError(error) { console.error(`Error: ${error.message}`); process.exitCode = 1; }
export function safeSlug(value) {
  const slug = value.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}-]+/gu, '-').replace(/^-+|-+$/g, '').slice(0, 80);
  if (!slug) throw new Error('Country name or ISO code is required');
  return slug;
}

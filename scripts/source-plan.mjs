import { loadSourceCatalog, findCountrySourceRecord, buildSourcePreflight, renderSourcePreflightMarkdown } from '../lib/source-catalog.mjs';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';

export async function sourcePlan({ country, theme, format = 'markdown' }) {
  if (!country) throw new Error('Provide --country <ISO3 or a pre-researched country name>');
  if (!['markdown', 'json'].includes(format)) throw new Error('--format must be markdown or json');
  const catalog = await loadSourceCatalog();
  const record = findCountrySourceRecord(catalog, country);
  const iso3 = record?.iso3 || String(country).trim().toUpperCase();
  if (!/^[A-Z]{3}$/.test(iso3)) throw new Error('An unresearched country must be specified by ISO3 code.');
  const preflight = buildSourcePreflight(catalog, { id: iso3, name: record?.names?.[0] || iso3 }, { theme });
  return format === 'json' ? `${JSON.stringify(preflight, null, 2)}\n` : renderSourcePreflightMarkdown(preflight);
}

if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['country', 'theme', 'format']);
    if (args.help) console.log('node scripts/source-plan.mjs --country UGA [--theme refugees] [--format markdown|json]');
    else process.stdout.write(await sourcePlan(args));
  } catch (error) { reportError(error); }
}

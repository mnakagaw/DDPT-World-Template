import path from 'node:path';
import { mkdir, writeFile, lstat, readFile, realpath } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { collectCountry } from '../lib/collect.mjs';
import { generateSite } from '../lib/generate.mjs';
import { validateDataset } from '../lib/validate.mjs';
import { writeSourcePreflight } from '../lib/source-catalog.mjs';
import { parseArgs, safeSlug, isMain, reportError } from '../lib/cli.mjs';

const repositoryUrl = 'https://github.com/mnakagaw/DDPT-World-Template';
const templateRoot = fileURLToPath(new URL('../', import.meta.url));
const execFileAsync = promisify(execFile);
const sourcePaths = ['.gitattributes', '.github', '.gitignore', 'AGENTS.md', 'README.md', 'START_HERE.md', 'config', 'docs', 'lib', 'package.json', 'package-lock.json', 'prompts', 'references', 'scaffold', 'scripts', 'templates', 'tests'];
const hash = value => createHash('sha256').update(value).digest('hex');

/** Record portable provenance; an archive inside an unrelated checkout is not that checkout's source revision. */
export async function readTemplateReference(root = templateRoot) {
  const pkg = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
  const reference = {
    repository_url: repositoryUrl,
    package_version: pkg.version,
    git_commit: null,
    source_state: { status: 'unavailable', tracked_changes: null, untracked_source_files: null },
    recorded_at: new Date().toISOString(),
  };
  const git = async args => (await execFileAsync('git', args, { cwd: root, windowsHide: true, timeout: 10000, maxBuffer: 1024 * 1024 })).stdout;
  try {
    const gitRoot = (await git(['rev-parse', '--show-toplevel'])).trim();
    const normalize = value => process.platform === 'win32' ? value.toLowerCase() : value;
    if (normalize(await realpath(gitRoot)) !== normalize(await realpath(root))) return reference;
    try {
      const commit = (await git(['rev-parse', '--verify', 'HEAD'])).trim();
      if (/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(commit)) reference.git_commit = commit;
    } catch { /* A newly initialized checkout can have source changes but no commit yet. */ }
    const entries = (await git(['status', '--porcelain=v1', '-z', '--untracked-files=all', '--', ...sourcePaths])).split('\0');
    let tracked = false, untracked = 0;
    for (let i = 0; i < entries.length; i++) {
      if (!entries[i]) continue;
      const state = entries[i].slice(0, 2);
      if (state === '??') untracked++;
      else { tracked = true; if (/[RC]/.test(state)) i++; }
    }
    reference.source_state = { status: tracked || untracked ? 'dirty' : 'clean', tracked_changes: tracked, untracked_source_files: untracked };
  } catch { /* Do not include host paths or command error messages in a distributed artifact. */ }
  return reference;
}

function portableLinks(markdown, sourcePath, artifactPath, destinations, reference) {
  return markdown.replace(/(\[[^\]\n]*\]\()([^\s)]+)(\))/g, (match, before, target, after) => {
    if (/^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(target)) return match;
    const hashAt = target.indexOf('#'), file = hashAt < 0 ? target : target.slice(0, hashAt), anchor = hashAt < 0 ? '' : target.slice(hashAt);
    const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(sourcePath), file));
    if (resolved.startsWith('../') || path.posix.isAbsolute(resolved)) return match;
    const destination = destinations.get(resolved);
    const url = destination
      ? path.posix.relative(path.posix.dirname(artifactPath), destination) + anchor
      : `${repositoryUrl}/blob/${reference.git_commit || 'main'}/${resolved.split('/').map(encodeURIComponent).join('/')}${anchor}`;
    return before + url + after;
  });
}

async function writeContinuationBundle(outDir) {
  const reference = await readTemplateReference();
  const destinations = new Map([['docs/COUNTRY_AGENT_WORKFLOW.md', 'COUNTRY_AGENT_WORKFLOW.md']]);
  // Bundle the operative contract, not historical review files containing another project's machine paths.
  for (const source of ['docs/SOURCE_ADAPTER_GUIDE.md', 'docs/COMMON_DATA_AND_SOURCE_REGISTRY.md', 'docs/GOOD_GOVERNMENT_ARCHITECTURE.md', 'docs/IMPLEMENTATION_CONTRACT.md', 'docs/PLANNING_DATA_CONTRACT.md', 'docs/ANALYSIS_DATA_CONTRACT.md', 'docs/PLANNING_CENSUS_METHOD.md', 'docs/02_COMMON_SPEC.md', 'docs/03_COUNTRY_AND_DATA.md', 'templates/ACCEPTANCE.md', 'templates/COUNTRY_START.md', 'templates/TASK_AND_CHANGE.md', 'templates/PLANNING_CENSUS_AUDIT.md', 'templates/country-profile.json']) {
    destinations.set(source, `reference/${source}`);
  }
  reference.documentation = [];
  reference.notes = [
    'Bundled references are the source documents used by this generation. They do not establish UX acceptance or completed country collection.',
    reference.git_commit ? 'The recorded commit identifies the checkout base; dirty source changes are not represented by that commit.' : 'No template commit could be verified. Remote fallback links use main and cannot reproduce an exact source revision.',
  ];
  for (const [source, destination] of destinations) {
    const original = await readFile(path.join(templateRoot, source), 'utf8');
    let content = source.endsWith('.md') ? portableLinks(original, source, destination, destinations, reference) : original;
    if (source === 'docs/COUNTRY_AGENT_WORKFLOW.md') {
      content = content.replace(/^国別出力のルートへコピーされた[^\n]+/m,
        'この国別出力では補助資料を`reference/docs/`、開始・受入様式を`reference/templates/`に同梱している。`TEMPLATE_REFERENCE.json`にテンプレートURL・参照commit・未commit変更の状態を記録した。`scripts/`と`lib/`はそのテンプレートcheckout内で参照する。commitが不明またはsourceがdirtyなら完全な再現は未保証とし、同梱資料と現物を確認して再開する。国別データを初期化しない。');
      content = content.replace(/`templates\/COUNTRY_START\.md`/g, '`reference/templates/COUNTRY_START.md`');
    }
    await mkdir(path.dirname(path.join(outDir, destination)), { recursive: true });
    await writeFile(path.join(outDir, destination), content, 'utf8');
    reference.documentation.push({ source_path: source, artifact_path: destination, source_sha256: hash(original), artifact_sha256: hash(content) });
  }
  await writeFile(path.join(outDir, 'TEMPLATE_REFERENCE.json'), JSON.stringify(reference, null, 2) + '\n');
}

export async function createCountry({ country, out, collect = collectCountry, generate = generateSite }) {
  if (typeof country !== 'string' || !country.trim()) throw new Error('Provide --country <country name or ISO code>');
  const outDir = path.resolve(out || path.join('generated', safeSlug(country)));
  try { await lstat(outDir); throw new Error(`Output already exists; choose a new directory: ${outDir}`); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  await mkdir(path.dirname(outDir), { recursive: true });
  await mkdir(outDir); // Exclusive creation protects another concurrent invocation.
  const rawDir = path.join(outDir, 'raw');
  await mkdir(rawDir);
  try {
    const dataset = await collect({ country, rawDir, onProgress: message => console.log(message) });
    const validation = validateDataset(dataset);
    await mkdir(path.join(outDir, 'evidence'), { recursive: true });
    await writeFile(path.join(outDir, 'evidence', 'validation.json'), JSON.stringify({ ...validation, checked_at: new Date().toISOString(), dataset_sha256: createHash('sha256').update(JSON.stringify(dataset)).digest('hex') }, null, 2) + '\n');
    if (validation.errors.length) throw new Error(`Collected data failed validation: ${validation.errors.join('; ')}`);
    await mkdir(path.join(outDir, 'data'), { recursive: true });
    await writeFile(path.join(outDir, 'data', 'dashboard.json'), JSON.stringify(dataset, null, 2) + '\n');
    const sourcePreflight = await writeSourcePreflight(outDir, dataset.country);
    await generate({ dataset, outDir });
    // Store the continuation contract with the generated project so it is never lost after bootstrap.
    await writeContinuationBundle(outDir);
    await writeFile(path.join(outDir, 'AGENTS.md'), `# Country project\n\nCountry: ${dataset.country.name} (${dataset.country.id}).\n\nRead COUNTRY_AGENT_WORKFLOW.md, evidence/SOURCE_PREFLIGHT.md, TEMPLATE_REFERENCE.json, the bundled reference/docs and reference/templates, and HANDOFF.md if present. This is an initial collection, not a completed local planning dashboard. The template reference records a commit when available and flags dirty or unavailable source provenance. SOURCE_PREFLIGHT is a discovery plan, not proof that data were acquired or suitable. Refresh its country sources, check every common candidate for this country, then continue collecting official subnational statistics, verifying code/boundary correspondence and planning sources, and updating data/dashboard.json. Never distribute national values across local territories. Keep census, sample survey, humanitarian observation and modeled grid values as different evidence types. Keep the DDPT page roles and synchronized selection. Record gaps and unperformed verification. Reference: ${repositoryUrl}\n\nDo not overwrite the source template repository. Do not use host Microsoft Word COM. Publish only within the current user's requested destination and authorization.\n`);
    console.log(`Created: ${outDir}`);
    console.log(`Collection: ${dataset.collection.status}; observations: ${dataset.observations.filter(o => o.status === 'observed').length}; territories: ${dataset.territories.length}`);
    console.log('Next: follow COUNTRY_AGENT_WORKFLOW.md to collect official local data and complete the country project.');
    return { outDir, dataset, validation, sourcePreflight };
  } catch (error) {
    await writeFile(path.join(outDir, 'COLLECTION_FAILED.txt'), `${new Date().toISOString()}\n${error.message}\nExisting evidence has been retained. Use a new output directory for a fresh collection.\n`);
    throw error;
  }
}

if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['country', 'out']);
    if (args.help) console.log('node scripts/create-country.mjs --country "Uganda" [--out generated/uganda]\nCreates a new project only. Then continue the country agent workflow.');
    else {
      const result = await createCountry(args);
      if (!result.dataset.observations.some(o => o.status === 'observed')) { console.error('No numeric data collected; empty shell is not a successful data build.'); process.exitCode = 2; }
    }
  } catch (error) { reportError(error); }
}

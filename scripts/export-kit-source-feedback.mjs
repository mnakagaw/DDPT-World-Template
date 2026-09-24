import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, rename, unlink, writeFile } from 'node:fs/promises';

const root = fileURLToPath(new URL('../', import.meta.url));
const selectionPath = path.join(root, 'config/kit-source-feedback-selections.json');
const outputPath = path.join(root, 'evidence/KIT_SOURCE_FEEDBACK.json');

function requireValue(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`Missing ${label}`);
  return value.trim();
}

function publicUrl(value) {
  const url = new URL(requireValue(value, 'source URL'));
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    throw new Error(`Unsafe source URL: ${url.href}`);
  }
  for (const key of url.searchParams.keys()) {
    if (/(?:api[-_]?key|token|password|passwd|secret|signature|credential)/i.test(key)) {
      throw new Error(`Credential-like URL parameter: ${key}`);
    }
  }
  return url.href;
}

export async function buildKitSourceFeedback({ base = root, commit, exportedAt } = {}) {
  const selection = JSON.parse(await readFile(path.join(base, 'config/kit-source-feedback-selections.json'), 'utf8'));
  if (selection.schema_version !== '1.0' || !/^\d{4}-\d{2}-\d{2}$/.test(selection.checked_at)) {
    throw new Error('Invalid feedback selection version or checked_at');
  }
  if (!/^[0-9a-f]{40}$/.test(commit || '')) throw new Error('A committed AreaData SHA is required');
  const date = exportedAt || new Date().toISOString();
  if (selection.checked_at > date.slice(0, 10)) throw new Error('Feedback check date is after export date');
  const evidencePath = requireValue(selection.evidence_path, 'evidence_path').replaceAll('\\', '/');
  if (path.isAbsolute(evidencePath) || evidencePath.split('/').includes('..')) throw new Error('Unsafe evidence_path');
  await readFile(path.join(base, evidencePath));
  const sources = [];
  const seen = new Set();
  for (const project of selection.projects || []) {
    const projectPath = requireValue(project.path, 'project path').replaceAll('\\', '/');
    if (!projectPath.startsWith('generated/') || projectPath.split('/').includes('..')) throw new Error(`Unsafe project path: ${projectPath}`);
    if (!/^[A-Z]{3}$/.test(project.iso3 || '')) throw new Error('Invalid ISO3 in feedback selection');
    const projectEvidencePath = project.evidence_path ? requireValue(project.evidence_path, 'project evidence_path').replaceAll('\\', '/') : evidencePath;
    if (path.isAbsolute(projectEvidencePath) || projectEvidencePath.split('/').includes('..') || !projectEvidencePath.startsWith('docs/evidence/')) throw new Error('Unsafe project evidence_path');
    await readFile(path.join(base, projectEvidencePath));
    const dataset = JSON.parse(await readFile(path.join(base, projectPath, 'data/dashboard.json'), 'utf8'));
    if (dataset.country?.id !== project.iso3 || !Array.isArray(dataset.sources)) throw new Error(`Country dataset mismatch: ${projectPath}`);
    const datasetSources = new Map(dataset.sources.map(source => [source.id, source]));
    for (const chosen of project.sources || []) {
      const source = datasetSources.get(chosen.id);
      if (!source) throw new Error(`Selected source absent from ${projectPath}: ${chosen.id}`);
      const url = publicUrl(source.url);
      const key = `${project.iso3}|${chosen.role}|${url}`;
      if (seen.has(key)) throw new Error(`Duplicate feedback source: ${key}`);
      seen.add(key);
      sources.push({
        iso3: project.iso3,
        source_id: `${project.iso3}_${source.id.replace(/[^a-zA-Z0-9]+/g, '_').toUpperCase()}`,
        role: requireValue(chosen.role, 'role'),
        title: requireValue(source.name, 'source title'),
        publisher: requireValue(source.publisher, 'publisher'),
        url,
        authority_type: requireValue(chosen.authority_type, 'authority_type'),
        // These projects passed adaptation checks, not an independent source audit.
        evidence_stage: 'official_location_identified',
        checked_at: selection.checked_at,
        geographic_levels: chosen.geographic_levels || [],
        reference_periods: source.reference_period ? [String(source.reference_period)] : [],
        formats: chosen.formats || [],
        license_or_terms: source.license || null,
        reuse_note: requireValue(chosen.reuse_note, 'reuse_note'),
        origin_evidence_path: projectEvidencePath,
        artifact_sha256: null,
        ...(chosen.supersedes_url ? { supersedes_url: publicUrl(chosen.supersedes_url) } : {}),
      });
    }
  }
  sources.sort((a, b) => `${a.iso3}|${a.role}|${a.url}`.localeCompare(`${b.iso3}|${b.role}|${b.url}`, 'en'));
  return { schema_version: '1.0', produced_by: 'AreaData', exported_at: date, origin_commit: commit, sources };
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');
  if (process.argv.slice(2).some(arg => arg !== '--dry-run')) throw new Error('Only --dry-run is supported');
  const commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
  const bundle = await buildKitSourceFeedback({ commit });
  if (!dryRun) {
    await mkdir(path.dirname(outputPath), { recursive: true });
    const temporary = `${outputPath}.tmp-${process.pid}`;
    try {
      await writeFile(temporary, `${JSON.stringify(bundle, null, 2)}\n`, { flag: 'wx' });
      await rename(temporary, outputPath);
    } catch (error) {
      await unlink(temporary).catch(() => {});
      throw error;
    }
  }
  console.log(JSON.stringify({ output: outputPath, countries: [...new Set(bundle.sources.map(source => source.iso3))], sources: bundle.sources.length, dry_run: dryRun }, null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}

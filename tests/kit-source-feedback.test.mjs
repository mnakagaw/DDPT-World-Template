import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildKitSourceFeedback } from '../scripts/export-kit-source-feedback.mjs';

const repository = fileURLToPath(new URL('../', import.meta.url));

test('exporter reads a selected country source without publishing local paths or adoption state', async () => {
  const base = await mkdtemp(path.join(os.tmpdir(), 'areadata-kit-feedback-'));
  try {
    await mkdir(path.join(base, 'config'));
    await mkdir(path.join(base, 'docs/evidence'), { recursive: true });
    await mkdir(path.join(base, 'generated/sample/data'), { recursive: true });
    await writeFile(path.join(base, 'docs/evidence/sample.md'), '# Source location\n');
    await writeFile(path.join(base, 'docs/evidence/country.md'), '# Country source location\n');
    await writeFile(path.join(base, 'config/kit-source-feedback-selections.json'), JSON.stringify({
      schema_version: '1.0', checked_at: '2026-09-24', evidence_path: 'docs/evidence/sample.md',
      projects: [{ path: 'generated/sample', iso3: 'BGD', evidence_path: 'docs/evidence/country.md', sources: [{
        id: 'bbs-census', role: 'census_results', authority_type: 'official_national',
        geographic_levels: ['national'], formats: ['PDF'], reuse_note: 'Location only.',
      }] }],
    }));
    await writeFile(path.join(base, 'generated/sample/data/dashboard.json'), JSON.stringify({
      country: { id: 'BGD' }, sources: [{ id: 'bbs-census', name: 'Census report',
        publisher: 'BBS', url: 'https://bbs.gov.bd/census', reference_period: '2022', license: null }],
    }));
    const bundle = await buildKitSourceFeedback({ base, commit: 'a'.repeat(40), exportedAt: '2026-09-24T12:00:00Z' });
    assert.equal(bundle.sources.length, 1);
    assert.equal(bundle.sources[0].evidence_stage, 'official_location_identified');
    assert.equal(bundle.sources[0].artifact_sha256, null);
    assert.deepEqual(bundle.sources[0].reference_periods, ['2022']);
    assert.equal(bundle.sources[0].origin_evidence_path, 'docs/evidence/country.md');
    assert.ok(!JSON.stringify(bundle).includes(base));
  } finally {
    await rm(base, { recursive: true, force: true });
  }
});

test('committed bundle retains four country source-location leads', async () => {
  const bundle = JSON.parse(await readFile(path.join(repository, 'evidence/KIT_SOURCE_FEEDBACK.json'), 'utf8'));
  for (const iso3 of ['BFA', 'BGD', 'LAO', 'UGA']) assert.ok(bundle.sources.some(source => source.iso3 === iso3));
  assert.ok(bundle.sources.length >= 15);
  assert.equal(bundle.sources.filter(source => source.iso3 === 'BFA').length, 12);
  assert.ok(bundle.sources.some(source => source.source_id === 'BFA_BFA_CNS_LOCAL_FINANCE_CATALOGUE'));
  assert.ok(bundle.sources.some(source => source.source_id === 'BFA_BFA_INSD_NATIONAL_YEARBOOK_2024'));
  assert.ok(bundle.sources.filter(source => source.iso3 === 'BFA').every(source => source.origin_evidence_path === 'docs/evidence/burkina-faso-areadata-adaptation-2026-09-24.md'));
  assert.ok(bundle.sources.every(source => source.evidence_stage === 'official_location_identified'));
  assert.ok(bundle.sources.every(source => source.artifact_sha256 === null));
  assert.ok(bundle.sources.every(source => source.origin_evidence_path.startsWith('docs/evidence/')));
  assert.ok(bundle.sources.every(source => !JSON.stringify(source).includes('C:\\Users\\')));
  assert.equal(bundle.sources.find(source => source.source_id === 'LAO_LAO_PHC_2015')?.supersedes_url,
    'https://www.lsb.gov.la/sdg/en/17-19-2/');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { buildKitSourceFeedback } from '../scripts/export-kit-source-feedback.mjs';

test('three-country feedback exports only public source locations with conservative provenance', async () => {
  const bundle = await buildKitSourceFeedback({ commit: 'a'.repeat(40), exportedAt: '2026-09-24T12:00:00Z' });
  assert.equal(bundle.produced_by, 'AreaData');
  assert.deepEqual([...new Set(bundle.sources.map(source => source.iso3))], ['BGD', 'LAO', 'UGA']);
  assert.equal(bundle.sources.length, 7);
  assert.ok(bundle.sources.every(source => source.evidence_stage === 'official_location_identified'));
  assert.ok(bundle.sources.every(source => source.artifact_sha256 === null));
  assert.ok(bundle.sources.every(source => source.origin_evidence_path.startsWith('docs/evidence/')));
  assert.ok(bundle.sources.every(source => !JSON.stringify(source).includes('C:\\Users\\')));
  assert.ok(bundle.sources.every(source => ['http:', 'https:'].includes(new URL(source.url).protocol)));
});

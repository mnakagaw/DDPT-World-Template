import test from 'node:test';
import assert from 'node:assert/strict';
import { validateDataset } from '../lib/validate.mjs';
import { fixture } from './fixture.mjs';
test('zero and missing are distinct valid observations, same names do not merge IDs', () => {
  const result = validateDataset(fixture()); assert.deepEqual(result.errors, []);
});
test('null cannot masquerade as an observed value and missing cannot become zero', () => {
  const d=fixture(); d.observations[1].value=null; d.observations[2].value=0;
  const errors=validateDataset(d).errors.join(' '); assert.match(errors,/finite number/); assert.match(errors,/must be null/);
});
test('duplicates, dangling references and parent cycles are rejected', () => {
  const d=fixture(); d.observations.push({...d.observations[0]}); d.territories[0].parent_id='TST-A'; d.observations[1].source_id='absent';
  const errors=validateDataset(d).errors.join(' '); assert.match(errors,/Duplicate observation/); assert.match(errors,/cycle/); assert.match(errors,/Unknown observation source/);
});
test('national-only data emits an explicit limitation', () => {
  const d=fixture(); d.observations=d.observations.filter(o=>o.territory_id==='TST');
  assert.match(validateDataset(d).warnings.join(' '),/National statistics only/);
});
test('unsafe source URLs and raw evidence paths are rejected', () => {
  const d=fixture(); d.sources[0].url='javascript:alert(1)'; d.sources[0].raw_path='../secret.env';
  const errors=validateDataset(d).errors.join(' '); assert.match(errors,/HTTPS/); assert.match(errors,/Unsafe raw_path/);
});
test('invalid and unclosed boundary rings are rejected', () => {
  const d=fixture(); d.boundaries.features[0].geometry.coordinates[0][4]=[300,100];
  const errors=validateDataset(d).errors.join(' '); assert.match(errors,/coordinate/); assert.match(errors,/closed/);
});
test('a national source cannot be assigned to local observations', () => {
  const d=fixture(); d.sources[0].geographic_level='national';
  assert.match(validateDataset(d).errors.join(' '),/National source/);
});
test('malformed document rows are validation errors instead of validator exceptions', () => {
  const d=fixture(); d.documents=[null];
  assert.match(validateDataset(d).errors.join(' '),/document needs an id/);
});
test('unsupported dimensions cannot create ambiguous displayed observations', () => {
  const d=fixture(); d.observations[0].dimension='female';
  assert.match(validateDataset(d).errors.join(' '),/dimensions require/);
});

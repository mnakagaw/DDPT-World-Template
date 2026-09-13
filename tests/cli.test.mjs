import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { parseArgs, safeSlug } from '../lib/cli.mjs';
import { serveDirectory } from '../scripts/serve.mjs';
test('CLI validates options and keeps Unicode country names in safe directory slugs', () => {
  assert.deepEqual(parseArgs(['--country','ウガンダ'],['country']),{country:'ウガンダ'});
  assert.throws(()=>parseArgs(['--force'],['country']),/Unknown/);
  assert.throws(()=>parseArgs(['--country','--out'],['country','out']),/Missing/);
  assert.equal(safeSlug('../Uganda/../../'),'uganda');
  assert.equal(safeSlug('ウガンダ'),'ウガンダ');
});
test('local server serves the site only and rejects write methods', async t => {
  const dir=await mkdtemp(path.join(os.tmpdir(),'ddpt-server-'));
  await writeFile(path.join(dir,'index.html'),'<h1>Preview</h1>');
  const server=await serveDirectory(dir,0); t.after(()=>new Promise(resolve=>server.close(resolve)));
  const base=`http://127.0.0.1:${server.address().port}`;
  const response=await fetch(base); assert.equal(response.status,200); assert.match(await response.text(),/Preview/);
  assert.equal((await fetch(base,{method:'POST'})).status,405);
  assert.equal((await fetch(`${base}/%2e%2e%2fpackage.json`)).status,404);
  assert.match(response.headers.get('content-security-policy'),/object-src 'none'/);
});

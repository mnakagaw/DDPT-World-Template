import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, access } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import { createCountry, readTemplateReference } from '../scripts/create-country.mjs';
import { buildCountry } from '../scripts/build-country.mjs';
import { fixture } from './fixture.mjs';

test('creation does not overwrite existing work or start collection there', async () => {
  const out=await mkdtemp(path.join(os.tmpdir(),'ddpt-preserve-'));
  await writeFile(path.join(out,'notes.txt'),'Keep my notes');
  let called=false;
  await assert.rejects(createCountry({country:'Test',out,collect:async()=>{called=true; return fixture();}}),/already exists/);
  assert.equal(called,false);
  assert.equal(await readFile(path.join(out,'notes.txt'),'utf8'),'Keep my notes');
});
test('creation leaves the source evidence and error receipt on collection failure', async () => {
  const base=await mkdtemp(path.join(os.tmpdir(),'ddpt-failure-')),out=path.join(base,'country');
  await assert.rejects(createCountry({country:'Test',out,collect:async({rawDir})=>{await writeFile(path.join(rawDir,'evidence.txt'),'acquired before failure'); throw new Error('Required country lookup failed');}}),/lookup failed/);
  assert.match(await readFile(path.join(out,'COLLECTION_FAILED.txt'),'utf8'),/lookup failed/);
  assert.equal(await readFile(path.join(out,'raw/evidence.txt'),'utf8'),'acquired before failure');
});
test('bootstrap saves validated data, a working site and a continuation contract', async () => {
  const base=await mkdtemp(path.join(os.tmpdir(),'ddpt-created-')),out=path.join(base,'country');
  const result=await createCountry({country:'Test',out,collect:async()=>fixture()});
  assert.deepEqual(result.validation.errors,[]);
  await access(path.join(out,'site/territorial/index.html'));
  assert.match(await readFile(path.join(out,'COUNTRY_AGENT_WORKFLOW.md'),'utf8'),/初期生成であり/);
  assert.match(await readFile(path.join(out,'AGENTS.md'),'utf8'),/not a completed/);
  const reference=JSON.parse(await readFile(path.join(out,'TEMPLATE_REFERENCE.json'),'utf8'));
  assert.equal(reference.repository_url,'https://github.com/mnakagaw/DDPT-World-Template');
  assert.equal(reference.package_version,JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8')).version);
  assert.ok(reference.git_commit===null || /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(reference.git_commit));
  assert.ok(['clean','dirty','unavailable'].includes(reference.source_state.status));
  assert.doesNotMatch(JSON.stringify(reference),/"[A-Za-z]:[\\/]/);
  assert.equal(JSON.stringify(reference).includes(base),false);
  assert.ok(reference.documentation.some(doc=>doc.source_path==='docs/SOURCE_ADAPTER_GUIDE.md'));
  assert.ok(reference.documentation.some(doc=>doc.source_path==='templates/ACCEPTANCE.md'));
  assert.ok(reference.documentation.some(doc=>doc.source_path==='templates/COUNTRY_START.md'));
  for(const doc of reference.documentation) {
    const filename=path.join(out,doc.artifact_path),text=await readFile(filename,'utf8');
    assert.equal(createHash('sha256').update(text).digest('hex'),doc.artifact_sha256);
    if(!filename.endsWith('.md'))continue;
    for(const match of text.matchAll(/\[[^\]\n]*\]\(([^\s)]+)\)/g)) {
      const target=match[1];
      if(/^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(target))continue;
      const local=path.resolve(path.dirname(filename),target.split('#')[0]);
      const relative=path.relative(out,local);
      assert.ok(!relative.startsWith('..'+path.sep) && relative!=='..' && !path.isAbsolute(relative),`Link leaves portable artifact: ${target}`);
      await access(local);
    }
  }
  const instructions=await readFile(path.join(out,'COUNTRY_AGENT_WORKFLOW.md'),'utf8');
  assert.match(instructions,/\]\(reference\/docs\/SOURCE_ADAPTER_GUIDE\.md\)/);
  assert.match(instructions,/\]\(reference\/templates\/ACCEPTANCE\.md\)/);
  assert.match(instructions,/TEMPLATE_REFERENCE\.json/);
});

test('template provenance records the actual revision and dirty sources without inheriting an outer checkout', async t => {
  const run=promisify(execFile);
  try { await run('git',['--version'],{windowsHide:true}); } catch { t.skip('Git is optional for collection; unavailable in this test environment'); return; }
  const root=await mkdtemp(path.join(os.tmpdir(),'ddpt-template-reference-'));
  const git=async args=>(await run('git',args,{cwd:root,windowsHide:true})).stdout;
  await writeFile(path.join(root,'package.json'),JSON.stringify({version:'9.8.7'}));
  await writeFile(path.join(root,'README.md'),'Original template');
  await git(['init','-q']);
  await git(['add','package.json','README.md']);
  await git(['-c','user.name=Test Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgSign=false','commit','-qm','Fixture revision']);
  const commit=(await git(['rev-parse','HEAD'])).trim();
  const clean=await readTemplateReference(root);
  assert.equal(clean.git_commit,commit); assert.equal(clean.package_version,'9.8.7');
  assert.deepEqual(clean.source_state,{status:'clean',tracked_changes:false,untracked_source_files:0});
  await writeFile(path.join(root,'README.md'),'Changed template');
  await mkdir(path.join(root,'docs'));
  await writeFile(path.join(root,'docs/new-source.md'),'Untracked reference');
  const dirty=await readTemplateReference(root);
  assert.equal(dirty.git_commit,commit);
  assert.deepEqual(dirty.source_state,{status:'dirty',tracked_changes:true,untracked_source_files:1});
  const archive=path.join(root,'archive'); await mkdir(archive);
  await writeFile(path.join(archive,'package.json'),JSON.stringify({version:'9.8.7'}));
  const unrelated=await readTemplateReference(archive);
  assert.equal(unrelated.git_commit,null); assert.equal(unrelated.source_state.status,'unavailable');
});

test('an archive without a Git checkout records unknown provenance explicitly', async () => {
  const root=await mkdtemp(path.join(os.tmpdir(),'ddpt-no-git-reference-'));
  await writeFile(path.join(root,'package.json'),JSON.stringify({version:'0.2.0'}));
  const reference=await readTemplateReference(root);
  assert.equal(reference.git_commit,null);
  assert.deepEqual(reference.source_state,{status:'unavailable',tracked_changes:null,untracked_source_files:null});
});
test('failed rebuild records current failure and preserves the previous site', async () => {
  const out=await mkdtemp(path.join(os.tmpdir(),'ddpt-rebuild-'));
  await mkdir(path.join(out,'data')); await mkdir(path.join(out,'site')); await mkdir(path.join(out,'evidence'));
  await writeFile(path.join(out,'site/index.html'),'previous validated site');
  await writeFile(path.join(out,'evidence/validation.json'),JSON.stringify({errors:[]}));
  const d=fixture(); d.observations[0].value=null;
  await writeFile(path.join(out,'data/dashboard.json'),JSON.stringify(d));
  await assert.rejects(buildCountry(out),/finite number/);
  const receipt=JSON.parse(await readFile(path.join(out,'evidence/validation.json'),'utf8'));
  assert.ok(receipt.errors.length); assert.match(receipt.dataset_sha256,/^[a-f0-9]{64}$/);
  assert.equal(await readFile(path.join(out,'site/index.html'),'utf8'),'previous validated site');
});
test('a rebuild with no numeric observations is unsuccessful', async () => {
  const out=await mkdtemp(path.join(os.tmpdir(),'ddpt-empty-'));
  await mkdir(path.join(out,'data'));
  const d=fixture(); d.observations=[]; d.collection.status='failed';
  await writeFile(path.join(out,'data/dashboard.json'),JSON.stringify(d));
  await assert.rejects(buildCountry(out),/No usable numeric observations/);
});

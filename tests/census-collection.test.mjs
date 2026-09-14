import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm,writeFile,mkdir} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {collectCensusSources,loadCensusSourceManifest,validateCensusSourceManifest,validateFileSignature} from '../lib/collect-census.mjs';

const manifest=source=>({schema_version:'1.0',scope_id:'TEST',default_max_bytes:1000,sources:[{id:'TEST_XLSX',country_id:'BLZ',census_year:'2022',title:'Fixture',publisher:'Fixture publisher',catalog_url:'https://example.test/catalog',download_url:'https://example.test/file.xlsx',allowed_hosts:['example.test'],format:'xlsx',filename:'BLZ/2022/file.xlsx',role:'test',required:true,redistribution_status:'test_only',adoption_status:'test_only',...source}]});
const response=(body,{status=200,headers={}}={})=>new Response(body,{status,headers});

test('official Central America manifest is internally safe and unique',async()=>{
  const loaded=await loadCensusSourceManifest();
  assert.equal(loaded.sources.length,12);assert.deepEqual([...new Set(loaded.sources.map(row=>row.country_id))],['BLZ','GTM','SLV','HND','NIC','CRI','PAN']);
});

test('collector can reuse matching hash-verified evidence without fetching it again',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'areadata-census-')),prior=path.join(root,'prior'),out=path.join(root,'evidence');
  try{
    const bytes=Uint8Array.from([80,75,3,4,9,8,7]),digest='34b4ba8d513434137e09366a300fe94dc62c610206b8d95693746ba176fa6fcb';
    await mkdir(path.join(prior,'BLZ/2022'),{recursive:true});await writeFile(path.join(prior,'BLZ/2022/file.xlsx'),bytes);
    await writeFile(path.join(prior,'receipt.json'),JSON.stringify({retrieved_at:'2026-09-14T00:00:00Z',entries:[{source_id:'TEST_XLSX',status:'acquired',filename:'BLZ/2022/file.xlsx',requested_url:'https://example.test/file.xlsx',final_url:'https://example.test/file.xlsx',redirect_count:0,content_type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',sha256:digest}] }));
    let fetchCalls=0;const result=await collectCensusSources({outDir:out,reuseDir:prior,manifest:manifest(),fetchImpl:async()=>{fetchCalls++;throw new Error('must not fetch');},now:()=>new Date('2026-09-15T01:02:03Z')});
    assert.equal(fetchCalls,0);assert.equal(result.receipt.entries[0].sha256,digest);assert.equal(result.receipt.entries[0].reused_from.source_receipt_retrieved_at,'2026-09-14T00:00:00Z');
  }finally{await rm(root,{recursive:true,force:true});}
});

test('collector writes immutable bytes and a hash receipt',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'areadata-census-')),out=path.join(root,'evidence');
  try{
    const bytes=Uint8Array.from([80,75,3,4,1,2,3]);
    const result=await collectCensusSources({outDir:out,manifest:manifest(),fetchImpl:async()=>response(bytes,{headers:{'content-type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}}),now:()=>new Date('2026-09-15T01:02:03Z')});
    assert.equal(result.receipt.summary.acquired,1);assert.equal(result.receipt.entries[0].sha256,'e8b35476d2bd55232509d060f0e3b56737376d1848289eea711e974396ef2311');
    assert.deepEqual(new Uint8Array(await readFile(path.join(out,'BLZ/2022/file.xlsx'))),bytes);
    await assert.rejects(()=>collectCensusSources({outDir:out,manifest:manifest(),fetchImpl:async()=>response(bytes)}),/already exists/);
  }finally{await rm(root,{recursive:true,force:true});}
});

test('collector records invalid content without promoting it to acquired',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'areadata-census-')),out=path.join(root,'evidence');
  try{
    const result=await collectCensusSources({outDir:out,manifest:manifest(),fetchImpl:async()=>response('<html>blocked</html>',{headers:{'content-type':'text/html'}})});
    assert.equal(result.receipt.summary.required_failed,1);assert.match(result.receipt.entries[0].error,/ZIP signature/);
    await assert.rejects(()=>readFile(path.join(out,'BLZ/2022/file.xlsx')),/ENOENT/);
  }finally{await rm(root,{recursive:true,force:true});}
});

test('redirects may not leave the source allowlist',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'areadata-census-')),out=path.join(root,'evidence');
  try{
    const result=await collectCensusSources({outDir:out,manifest:manifest(),fetchImpl:async()=>response('',{status:302,headers:{location:'https://untrusted.test/file.xlsx'}})});
    assert.equal(result.receipt.summary.acquired,0);assert.match(result.receipt.entries[0].error,/Unapproved download host/);
  }finally{await rm(root,{recursive:true,force:true});}
});

test('manifest rejects path traversal and signature validation rejects fake files',()=>{
  assert.throws(()=>validateCensusSourceManifest(manifest({filename:'../secret.xlsx'})),/Unsafe filename/);
  assert.throws(()=>validateFileSignature(new TextEncoder().encode('not a workbook'),'xlsx'),/ZIP signature/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import {importAmericasEvidence} from '../scripts/create-americas.mjs';

const hash=value=>createHash('sha256').update(value).digest('hex');

test('Americas evidence import keeps census and WPP payloads, receipts and source paths inside the candidate',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'americas-evidence-'));
  try{
    const out=path.join(root,'out'),project=path.join(root,'central'),raw=path.join(root,'census'),wpp=path.join(root,'WPP.xlsx');
    await mkdir(path.join(out,'raw'),{recursive:true});await mkdir(path.join(out,'evidence'),{recursive:true});
    await mkdir(path.join(project,'evidence'),{recursive:true});await writeFile(path.join(project,'evidence','audit.json'),'{}');
    await mkdir(path.join(raw,'BLZ','2022'),{recursive:true});await mkdir(path.join(raw,'HND','2013','municipal-reports'),{recursive:true});
    await writeFile(path.join(raw,'BLZ','2022','table.xlsx'),'belize');await writeFile(path.join(raw,'normalized-census.json'),'normalized');await writeFile(path.join(raw,'manifest.snapshot.json'),'manifest');
    await writeFile(path.join(raw,'HND','2013','municipal-report-index.json'),'index');await writeFile(path.join(raw,'HND','2013','municipal-reports','a.pdf'),'report');
    await writeFile(path.join(raw,'HND','2013','municipal-receipt.json'),JSON.stringify({retrieved_at:'2026-09-17T00:00:00Z',entries:[{status:'acquired',filename:'HND/2013/municipal-reports/a.pdf',final_url:'https://example.org/a.pdf',sha256:hash('report'),bytes:6}]}));
    await writeFile(path.join(raw,'receipt.json'),JSON.stringify({entries:[{status:'acquired',source_id:'BLZ_SOURCE',filename:'BLZ/2022/table.xlsx',sha256:hash('belize'),bytes:6}]}));
    await writeFile(wpp,'wpp');
    const ids=['BLZ_SOURCE','HND_C2013_MUNICIPAL_REPORT_COLLECTION','areadata-ca7-census-series','areadata-ca7-scope','un-wpp2024-demographic-indicators-rev1'];
    const dataset={sources:ids.map(id=>({id,url:`https://example.org/${id}`}))};
    const summary=await importAmericasEvidence({dataset,outDir:out,centralAmericaProject:project,censusRawDir:raw,unWppFile:wpp});
    const source=id=>dataset.sources.find(item=>item.id===id);
    assert.equal(summary.imported_evidence_files,1);assert.equal(summary.wpp_raw_files,1);
    assert.equal(source('BLZ_SOURCE').raw_path,'raw/central-america-census/BLZ/2022/table.xlsx');
    assert.equal(source('BLZ_SOURCE').sha256,hash('belize'));
    assert.equal(source('HND_C2013_MUNICIPAL_REPORT_COLLECTION').raw_files.length,1);
    assert.equal(source('un-wpp2024-demographic-indicators-rev1').sha256,hash('wpp'));
    assert.equal(await readFile(path.join(out,'raw','central-america-census','HND','2013','municipal-reports','a.pdf'),'utf8'),'report');
    assert.deepEqual(JSON.parse(await readFile(path.join(out,'raw','un-wpp2024','receipt.json'),'utf8')).status,'copied_from_verified_evidence');
  }finally{
    const resolved=path.resolve(root),prefix=path.resolve(os.tmpdir())+path.sep;assert.ok(resolved.startsWith(prefix)&&path.basename(resolved).startsWith('americas-evidence-'));await rm(resolved,{recursive:true,force:true});
  }
});

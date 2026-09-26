import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const families={wpp:'un-wpp2024-global-rev1',sdg:'un-sdg-2026q2-archive',ama:'unsd-ama-2024',imf:'imf-weo-2026-04'};
const key=row=>`${row.territory_id}|${row.indicator_id}|${row.period}`;
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
function python(script,args){
  return new Promise((resolve,reject)=>{
    const child=spawn('python',[path.join(repo,'scripts',script),...args],{cwd:repo,stdio:'inherit'});
    child.on('error',reject);child.on('close',code=>code===0?resolve():reject(new Error(`${script} exited ${code}`)));
  });
}

/** Verify that every adopted Asia cell in four international domains replays from pinned originals. */
export async function verifyAsiaSourceReplay(project){
  const root=path.resolve(project),datasetBytes=await readFile(path.join(root,'data/dashboard.json')),
    data=JSON.parse(datasetBytes.toString('utf8')),
    manifest=JSON.parse(await readFile(path.join(root,'evidence/ASIA_SOURCE_RAW_MANIFEST.json'),'utf8'));
  assert.equal(data.country?.id,'ASI');
  assert.equal(manifest.dataset_sha256,sha256(datasetBytes));
  assert.deepEqual(manifest.failures,[]);
  for(const file of manifest.files){
    const bytes=await readFile(path.join(root,file.local_path));
    assert.equal(sha256(bytes),file.sha256,`Original changed: ${file.local_path}`);
    assert.equal(bytes.length,file.bytes,`Original size changed: ${file.local_path}`);
  }
  for(const source of data.sources){
    const expected=[...(source.raw_files||[]),...(source.source_files||[])].filter(file=>file.sha256&&file.url).map(file=>file.sha256);
    const actual=manifest.files.filter(file=>file.source_id===source.id).map(file=>file.sha256);
    assert.deepEqual(actual,expected,`Source register and raw manifest differ for ${source.id}`);
  }
  const scope=JSON.parse(await readFile(path.join(root,'evidence/ASIA_SCOPE.json'),'utf8'));
  const worldBytes=await readFile(scope.source_world_path);
  assert.equal(sha256(worldBytes),scope.source_world_sha256,'Pinned World input changed');
  const world=JSON.parse(worldBytes.toString('utf8'));
  const registryPath=path.join(root,'evidence/replay-registry.json');
  await writeFile(registryPath,JSON.stringify({territories:world.territories.filter(area=>area.source_id==='un-m49'&&String(area.official_code||'').length&&Number.isInteger(Number(area.official_code)))}));
  const originals=id=>manifest.files.filter(file=>file.source_id===id).map(file=>path.join(root,file.local_path));
  const [wppDemographic,wppMale,wppFemale]=originals(families.wpp),[sdgArchive]=originals(families.sdg),
    [amaCurrent,amaPerCapita,amaConstant]=originals(families.ama),[imfWorkbook]=originals(families.imf);
  assert.ok([wppDemographic,wppMale,wppFemale,sdgArchive,amaCurrent,amaPerCapita,amaConstant,imfWorkbook].every(Boolean));
  await python('extract-un-wpp-world.py',['--demographic',wppDemographic,'--age-male',wppMale,'--age-female',wppFemale,'--registry',scope.source_world_path,'--out',path.join(root,'evidence/replay-wpp.json')]);
  await python('extract-un-sdg-world.py',['--archive',sdgArchive,'--registry',registryPath,'--out',path.join(root,'evidence/replay-sdg.json')]);
  await python('extract-unsd-ama-world.py',['--current',amaCurrent,'--per-capita',amaPerCapita,'--constant',amaConstant,'--registry',registryPath,'--out',path.join(root,'evidence/replay-ama.json')]);
  await python('extract-imf-weo-inflation.py',['--workbook',imfWorkbook,'--registry',registryPath,'--out',path.join(root,'evidence/replay-imf.json')]);
  const areaIds=new Set(data.territories.map(row=>row.id));
  const results=[];
  for(const [name,sourceId] of Object.entries(families)){
    const replay=JSON.parse(await readFile(path.join(root,`evidence/replay-${name}.json`),'utf8'));
    const source=data.sources.find(row=>row.id===sourceId);
    assert.ok(source,`Missing source ${sourceId}`);
    const expected=data.observations.filter(row=>row.source_id===sourceId);
    const actual=replay.observations.filter(row=>areaIds.has(row.territory_id));
    const byKey=new Map(actual.map(row=>[key(row),row]));
    assert.equal(byKey.size,actual.length,`Duplicate replay key in ${name}`);
    assert.equal(expected.length,actual.length,`Asia observation count differs in ${name}`);
    for(const row of expected){
      const original=byKey.get(key(row));
      assert.ok(original,`No original for ${key(row)} (${name})`);
      assert.equal(row.status,original.status,`Status differs for ${key(row)} (${name})`);
      assert.equal(row.value,original.value,`Value differs for ${key(row)} (${name})`);
    }
    results.push({source_id:sourceId,adopted_asia_cells:expected.length,replayed_asia_cells:actual.length,
      original_files:manifest.files.filter(file=>file.source_id===sourceId).map(file=>({path:file.local_path,sha256:file.sha256})),
      locator:name==='wpp'?'Estimates / Medium variant sheets; ISO3 Alpha-code or SDMX code, Year, named demographic field; age-sex sheets use five-year age columns'
        :name==='sdg'?'CSV member in ZIP; SeriesCode, GeoAreaCode, TimePeriod and exact selected dimension slice in extract-un-sdg-world.py'
        :name==='ama'?'First worksheet; UN M49 code, GDP item and year header in each named UNSD AMA workbook'
        :'Countries / Country Groups sheets; exact ISO3 or group, PCPIPCH indicator and year column'});
  }
  const report={status:'all_adopted_asia_cells_replayed',dataset_sha256:sha256(datasetBytes),checked_at:new Date().toISOString(),
    source_file_count:manifest.files.length,sources:results,
    note:'Replay compares source-reported value and status for every adopted Asia cell in WPP, SDG, AMA and IMF. Country/area registry and World Bank raw API audit remain separate.'};
  await writeFile(path.join(root,'evidence/ASIA_SOURCE_REPLAY.json'),JSON.stringify(report,null,2)+'\n');
  return report;
}
if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(!args.project)throw new Error('Use --project <Asia project>');
    const report=await verifyAsiaSourceReplay(args.project);
    console.log(`${report.status}: ${report.sources.reduce((sum,row)=>sum+row.adopted_asia_cells,0)} cells from ${report.source_file_count} pinned source files`);
  }catch(error){reportError(error);}
}

import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {validateDataset} from '../lib/validate.mjs';
import {buildAsia} from '../lib/asia-adapter.mjs';
import {initialState,comparisonRows,territorialIndicatorState} from '../scaffold/site/model.mjs';
import {diagnosticCsv} from '../scaffold/site/diagnostic.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

export async function verifyAsiaCandidate(project){
  const root=path.resolve(project),scope=JSON.parse(await readFile(path.join(root,'evidence/ASIA_SCOPE.json'),'utf8'));
  const sourceBytes=await readFile(scope.source_world_path),source=JSON.parse(sourceBytes.toString('utf8'));
  assert.equal(hash(sourceBytes),scope.source_world_sha256,'Pinned World portfolio changed');
  const dataBytes=await readFile(path.join(root,'data/dashboard.json')),data=JSON.parse(dataBytes.toString('utf8'));
  assert.equal(hash(dataBytes),scope.dataset_sha256,'Asia dataset changed after build');
  assert.deepEqual(data,buildAsia(source),'Asia records no longer match the pinned World portfolio');
  const validation=validateDataset(data);assert.deepEqual(validation.errors,[]);
  const countries=data.territories.filter(area=>area.type==='country');
  const subregions=data.territories.filter(area=>area.parent_id==='M49:142');
  assert.equal(countries.length,50);assert.deepEqual(subregions.map(area=>area.id).sort(),['M49:030','M49:034','M49:035','M49:143','M49:145']);
  assert.equal(data.analysis.census_source_preflight.records.length,50);
  assert.equal(data.analysis.coverage.un_wpp_country_area_count,50);
  assert.equal(data.analysis.coverage.census_integrated_country_ids.length,0);
  const scopeDifferences=data.analysis.source_scope_differences;
  assert.deepEqual(scopeDifferences.map(row=>row.territory_id),['M49:142','M49:030']);
  assert.equal(scopeDifferences[1].difference,23011292,'Eastern Asia WPP/M49 Taiwan scope difference changed');
  assert.ok(Math.abs(scopeDifferences[0].difference-23011292)<=2,'Asia WPP/M49 scope difference changed');
  const countryIds=new Set(countries.map(area=>area.id));
  assert.ok(data.observations.every(row=>data.territories.some(area=>area.id===row.territory_id)));
  assert.ok(data.analysis.census_source_preflight.records.every(row=>countryIds.has(row.country_id)));
  assert.equal(data.observations.some(row=>row.territory_id==='USA'),false);
  for(const id of ['M49:142',...subregions.map(row=>row.id),'JPN','LAO','BGD','IND','CHN']){
    const total=territorialIndicatorState(data,id,'UN_WPP_POP_TOTAL','latest-available');
    assert.ok(Number.isFinite(total.result.value),`Missing selected population for ${id}`);
    assert.ok(total.result.row?.period,`Missing population year for ${id}`);
  }
  const region='M49:035',state=initialState(data,`?country=ASI&territory=${region}&metric=UN_WPP_POP_TOTAL&period=latest-available`);
  const comparison=comparisonRows(data,state).map(row=>row.area.id);
  assert.deepEqual(comparison.sort(),countries.filter(row=>row.parent_id===region).map(row=>row.id).sort());
  const diagnostic=diagnosticCsv(data,'JPN','latest-available');
  assert.match(diagnostic,/UN_WPP_POP_TOTAL/);assert.match(diagnostic,/2026/);
  assert.match(diagnostic,/JPN/);
  const asiaDiagnostic=diagnosticCsv(data,'M49:142','2026');
  assert.match(asiaDiagnostic,/Regional source scope note/);
  assert.match(asiaDiagnostic,/Taiwan/);
  const html=await readFile(path.join(root,'site/index.html'),'utf8');
  const app=await readFile(path.join(root,'site/assets/app.mjs'),'utf8');
  assert.match(html,/assets\/app\.mjs/);assert.match(app,/All Asia/);assert.match(app,/source-scope-note/);
  const evidence={status:'passed_dataset_and_static_site',checked_at:new Date().toISOString(),source_world_sha256:scope.source_world_sha256,
    dataset_sha256:scope.dataset_sha256,territory_count:data.territories.length,country_area_count:countries.length,
    subregion_count:subregions.length,indicator_count:data.indicators.length,observation_count:data.observations.length,
    warnings:validation.warnings,
    not_checked:['browser interaction','rendered map geometry','browser-downloaded CSV against source','independent acceptance','FTPS/public site']};
  await writeFile(path.join(root,'evidence/ASIA_CANDIDATE_VERIFICATION.json'),JSON.stringify(evidence,null,2)+'\n');
  return evidence;
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(!args.project)throw new Error('Use --project <Asia project>');
    const report=await verifyAsiaCandidate(args.project);
    console.log(`${report.status}: ${report.country_area_count} countries/areas, ${report.observation_count} observations`);
  }catch(error){reportError(error);}
}

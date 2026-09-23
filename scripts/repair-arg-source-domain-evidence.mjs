#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
const project=path.resolve(arg('--project')||'');
if(!project)throw new Error('--project is required');
const preflightPath=path.join(project,'evidence','SOURCE_PREFLIGHT.json');
const preflight=JSON.parse(await readFile(preflightPath,'utf8'));
const country=preflight.countries.find(row=>row.country_area_id==='ARG');
if(!country)throw new Error('ARG preflight entry is missing');
const shaFile=async relative=>createHash('sha256').update(await readFile(path.join(project,relative))).digest('hex');
const object=async(relative,expected,locator,geography_match)=>{
  const actual=await shaFile(relative);
  if(actual!==expected)throw new Error(`Hash mismatch for ${relative}`);
  return {object_path:relative,object_sha256:actual,locator,...(geography_match?{geography_match}:{})};
};
const catalogue=await object('raw/near-complete-depth/ARG/indec-censo2022-fragment.html','6f8559e8b28832bc4055044c5dc96a252d803708756447d226e6736b845efe3b','HTML lines 2-19 identify INDEC Censo 2022 and the Resultados definitivos section; lines 95 onward list the official statistical-table downloads.');
const summary=await object('raw/argentina-census-2022/c2022_tp_c_resumen.xlsx','7cdb0b44ee0370c487145b4ff383c0dc073244a09c274dd53556a75ef4c0006c','Worksheet cuadro_resumen: Total del país plus 24 jurisdiction rows; columns B-M report total population and sex-at-birth components for 2022.','All 24 jurisdiction labels are explicitly matched to retained AreaData province IDs; no department value is inferred from this table.');
const provinces=await object('raw/argentina-census-2022/provincias.ndjson','3858b0e92f84d70f680bdc1623732baa1e2201e6c0d4e1f93485fc1fc887e581','Georef API v13 NDJSON: metadata record cantidad=24 followed by province feature records with official id, nombre and geometry.','Official two-digit province IDs are preserved and joined exactly.');
const departments=await object('raw/argentina-census-2022/departamentos.ndjson','657b690d1373c02dced2165e12bb3ca379594286bc543d62319889e9f6dd5759','Georef API v13 NDJSON: metadata record cantidad=529 followed by department feature records with official id, nombre, parent province and geometry.','Official five-digit department IDs and parent province IDs are preserved and joined exactly.');
const domains={
  official_statistics_office:[catalogue],latest_census:[catalogue],census_results:[summary],
  table_catalog:[catalogue],machine_readable_data:[summary],administrative_codes:[provinces,departments],
  adm1_adm2_boundaries:[provinces,departments]
};
for(const [id,evidence] of Object.entries(domains))country[id]={...country[id],evidence,completion_verified:true};
const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'ARG',rule:'Each completed statistical source domain now points to a retained object with SHA-256 and an exact source locator. Geography domains also retain the official-code join statement.',domains:Object.fromEntries(Object.entries(domains).map(([id,rows])=>[id,rows.map(row=>({object_path:row.object_path,object_sha256:row.object_sha256,locator:row.locator}))]))};
await Promise.all([
  writeFile(preflightPath,JSON.stringify(preflight,null,2)+'\n'),
  writeFile(path.join(project,'evidence','ARG_SOURCE_DOMAIN_EVIDENCE_REPAIR.json'),JSON.stringify(audit,null,2)+'\n')
]);
console.log(JSON.stringify({ok:true,country_area_id:'ARG',domain_count:Object.keys(domains).length},null,2));

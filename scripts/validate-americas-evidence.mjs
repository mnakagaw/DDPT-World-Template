#!/usr/bin/env node
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export function parseCsv(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let index=0;index<text.length;index++){
    const character=text[index];
    if(quoted){
      if(character==='"'&&text[index+1]==='"'){cell+='"';index++;}
      else if(character==='"')quoted=false;
      else cell+=character;
    }else if(character==='"')quoted=true;
    else if(character===','){row.push(cell);cell='';}
    else if(character==='\n'){row.push(cell.replace(/\r$/,''));rows.push(row);row=[];cell='';}
    else cell+=character;
  }
  if(cell||row.length){row.push(cell.replace(/\r$/,''));rows.push(row);}
  const [rawHeaders,...data]=rows.filter(item=>item.some(value=>value!==''));
  const headers=rawHeaders.map((header,index)=>index===0?header.replace(/^\uFEFF/,''):header);
  return data.map(values=>Object.fromEntries(headers.map((header,index)=>[header,values[index]??''])));
}

export async function validateAmericasEvidence(project){
  const dataset=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
  const preflight=JSON.parse(await readFile(path.join(project,'evidence/SOURCE_PREFLIGHT.json'),'utf8'));
  const disposition=parseCsv(await readFile(path.join(project,'evidence/SOURCE_DISPOSITION.csv'),'utf8'));
  const registry=dataset.territories.filter(area=>area.type==='country').map(area=>area.id).sort();
  const wpp=disposition.filter(row=>row.record_type==='wpp_country_area_adoption');
  const ids=wpp.map(row=>row.country_area_id).sort();
  const errors=[];
  if(wpp.length!==registry.length)errors.push(`WPP disposition has ${wpp.length} rows; expected ${registry.length}.`);
  if(ids.some(id=>!id))errors.push('WPP disposition contains a blank country_area_id.');
  if(new Set(ids).size!==ids.length)errors.push('WPP disposition contains duplicate country_area_id values.');
  if(JSON.stringify(ids)!==JSON.stringify(registry))errors.push('WPP disposition country IDs do not match the Americas registry one-to-one.');
  if(wpp.some(row=>row.source_table_or_field!=='Total Population, as of 1 July (thousands)'))errors.push('WPP disposition field must be the 1 July population column.');
  if(wpp.some(row=>row.indicator_id!=='UN_WPP_POP_TOTAL'))errors.push('WPP disposition indicator must be UN_WPP_POP_TOTAL.');
  if(wpp.some(row=>row.source_id!=='un-wpp2024-demographic-indicators-rev1'))errors.push('WPP disposition source ID does not match the adopted dataset source.');
  const adopted=wpp.filter(row=>row.disposition==='adopted'),unavailable=wpp.filter(row=>row.disposition==='not_available_in_source');
  if(adopted.length!==55||unavailable.length!==2)errors.push(`WPP dispositions must be 55 adopted and 2 not_available_in_source; found ${adopted.length} and ${unavailable.length}.`);
  if(JSON.stringify(unavailable.map(row=>row.country_area_id).sort())!==JSON.stringify(['BVT','SGS']))errors.push('Only BVT and SGS may be unavailable in the WPP source.');
  if(preflight.countries.length!==registry.length)errors.push(`Source preflight has ${preflight.countries.length} entries; expected ${registry.length}.`);
  const currentYear=new Date().getUTCFullYear();
  for(const country of preflight.countries){
    const note=String(country.latest_census?.note||'');
    const futureYears=(country.recent_census_rounds||[]).map(row=>Number(row.year)).filter(year=>Number.isInteger(year)&&year>currentYear);
    if(futureYears.length&&/future|scheduled/i.test(note)===false)errors.push(`${country.country_area_id}: future census round is not labelled scheduled/future.`);
    if(futureYears.length&&/results are not acquired or usable|resultados no|未取得/i.test(note)===false)errors.push(`${country.country_area_id}: future census result is not explicitly unavailable.`);
    if(/identified\/usable/i.test(note))errors.push(`${country.country_area_id}: census schedule is incorrectly labelled identified/usable.`);
  }
  return {ok:errors.length===0,errors,summary:{registry:registry.length,wpp_rows:wpp.length,wpp_adopted:adopted.length,wpp_unavailable:unavailable.length,preflight:preflight.countries.length}};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
  const index=process.argv.indexOf('--project'),project=index>=0?process.argv[index+1]:'';
  if(!project)throw new Error('Usage: node scripts/validate-americas-evidence.mjs --project <directory>');
  const result=await validateAmericasEvidence(path.resolve(project));
  console.log(JSON.stringify(result,null,2));
  if(!result.ok)process.exitCode=1;
}

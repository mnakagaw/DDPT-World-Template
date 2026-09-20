#!/usr/bin/env node
import {access,readFile,readdir} from 'node:fs/promises';
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

async function listFiles(root,directory=''){
  const absolute=path.join(root,directory);let entries;
  try{entries=await readdir(absolute,{withFileTypes:true});}catch(error){if(error?.code==='ENOENT')return [];throw error;}
  const rows=[];
  for(const entry of entries){
    const relative=path.posix.join(directory.replaceAll('\\','/'),entry.name);
    if(entry.isDirectory())rows.push(...await listFiles(root,relative));
    else if(entry.isFile())rows.push(relative);
  }
  return rows.sort();
}

export async function validateAmericasEvidence(project){
  const dataset=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
  const preflight=JSON.parse(await readFile(path.join(project,'evidence/SOURCE_PREFLIGHT.json'),'utf8'));
  const inventory=JSON.parse(await readFile(path.join(project,'evidence/SOURCE_TABLE_INVENTORY.json'),'utf8'));
  let semantic=null;
  try{semantic=JSON.parse(await readFile(path.join(project,'evidence/COUNTRY_SEMANTIC_INVENTORY.json'),'utf8'));}catch{}
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
  const inventoryPaths=inventory.files.map(row=>String(row.path||''));
  if(inventory.file_count!==inventoryPaths.length)errors.push(`Source inventory declares ${inventory.file_count} files but contains ${inventoryPaths.length} rows.`);
  if(new Set(inventoryPaths).size!==inventoryPaths.length)errors.push('Source inventory contains duplicate paths.');
  const rawPaths=(await listFiles(path.join(project,'raw'))).map(relative=>`raw/${relative}`);
  const declaredPaths=[...inventoryPaths].sort();
  if(JSON.stringify(declaredPaths)!==JSON.stringify(rawPaths)){
    const missing=rawPaths.filter(relative=>!declaredPaths.includes(relative));
    const extra=declaredPaths.filter(relative=>!rawPaths.includes(relative));
    errors.push(`Source inventory must cover project/raw exactly; raw=${rawPaths.length}, declared=${declaredPaths.length}, missing=${missing.length}, extra=${extra.length}.`);
  }
  for(const relative of inventoryPaths){
    if(!relative||path.isAbsolute(relative)||relative.includes('\\')||relative.split('/').includes('..')){
      errors.push(`Source inventory path is not a safe project-relative POSIX path: ${relative||'(blank)'}.`);
      continue;
    }
    const absolute=path.resolve(project,relative);
    if(!absolute.startsWith(`${path.resolve(project)}${path.sep}`)){
      errors.push(`Source inventory path escapes the project: ${relative}.`);
      continue;
    }
    try{await access(absolute);}catch{errors.push(`Source inventory file does not exist inside the project: ${relative}.`);}
  }
  const rawXlsx=rawPaths.filter(relative=>relative.toLowerCase().endsWith('.xlsx'));
  if(!semantic)errors.push('Country semantic inventory is missing or invalid JSON.');
  else{
    const workbooks=Array.isArray(semantic.workbooks)?semantic.workbooks:[];
    const duplicateFiles=Array.isArray(semantic.duplicate_files)?semantic.duplicate_files:[];
    const semanticPaths=[...workbooks.map(row=>String(row.path||'')),...duplicateFiles.map(row=>String(row.path||''))].sort();
    if(new Set(semanticPaths).size!==semanticPaths.length)errors.push('Country semantic inventory contains duplicate workbook paths.');
    if(JSON.stringify(semanticPaths)!==JSON.stringify(rawXlsx)){
      const missing=rawXlsx.filter(relative=>!semanticPaths.includes(relative));
      const extra=semanticPaths.filter(relative=>!rawXlsx.includes(relative));
      errors.push(`Country semantic inventory must account for every raw XLSX as a unique workbook or byte-identical duplicate; raw=${rawXlsx.length}, declared=${semanticPaths.length}, missing=${missing.length}, extra=${extra.length}.`);
    }
    if(Number(semantic.xlsx_file_count)!==rawXlsx.length)errors.push(`Country semantic inventory xlsx_file_count is ${semantic.xlsx_file_count}; expected ${rawXlsx.length}.`);
    if(Number(semantic.workbook_count)!==workbooks.length)errors.push('Country semantic inventory workbook_count does not match its workbook rows.');
    if(Number(semantic.duplicate_file_count)!==duplicateFiles.length)errors.push('Country semantic inventory duplicate_file_count does not match its duplicate rows.');
  }
  const currentYear=new Date().getUTCFullYear();
  for(const country of preflight.countries){
    const note=String(country.latest_census?.note||'');
    const futureYears=(country.recent_census_rounds||[]).map(row=>Number(row.year)).filter(year=>Number.isInteger(year)&&year>currentYear);
    if(futureYears.length&&/future|scheduled/i.test(note)===false)errors.push(`${country.country_area_id}: future census round is not labelled scheduled/future.`);
    if(futureYears.length&&/results are not acquired or usable|resultados no|未取得/i.test(note)===false)errors.push(`${country.country_area_id}: future census result is not explicitly unavailable.`);
    if(/identified\/usable/i.test(note))errors.push(`${country.country_area_id}: census schedule is incorrectly labelled identified/usable.`);
  }
  return {ok:errors.length===0,errors,summary:{registry:registry.length,wpp_rows:wpp.length,wpp_adopted:adopted.length,wpp_unavailable:unavailable.length,preflight:preflight.countries.length,inventory_files:inventoryPaths.length,raw_files:rawPaths.length,raw_xlsx_files:rawXlsx.length,semantic_workbooks:semantic?.workbooks?.length??0,semantic_duplicate_workbooks:semantic?.duplicate_files?.length??0}};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
  const index=process.argv.indexOf('--project'),project=index>=0?process.argv[index+1]:'';
  if(!project)throw new Error('Usage: node scripts/validate-americas-evidence.mjs --project <directory>');
  const result=await validateAmericasEvidence(path.resolve(project));
  console.log(JSON.stringify(result,null,2));
  if(!result.ok)process.exitCode=1;
}

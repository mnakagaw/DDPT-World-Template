#!/usr/bin/env node
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import process from 'node:process';

function arg(name, fallback=null){
  const i=process.argv.indexOf(name);
  return i>=0?process.argv[i+1]:fallback;
}
function safeName(value){return String(value).replace(/[^A-Za-z0-9._-]+/g,'_').slice(0,120);}
function extension(contentType,url){
  const pathname=new URL(url).pathname.toLowerCase();
  for(const ext of ['.xlsx','.xls','.csv','.json','.pdf','.zip','.geojson','.html'])if(pathname.endsWith(ext))return ext;
  if(contentType.includes('spreadsheetml'))return '.xlsx';
  if(contentType.includes('ms-excel'))return '.xls';
  if(contentType.includes('text/csv'))return '.csv';
  if(contentType.includes('application/json'))return '.json';
  if(contentType.includes('application/pdf'))return '.pdf';
  if(contentType.includes('application/zip'))return '.zip';
  return '.html';
}
async function sha256(buffer){return crypto.createHash('sha256').update(buffer).digest('hex');}
async function fetchOne(task,outRoot,{maxBytes,timeoutMs,reusable,project}){
  const started=new Date().toISOString();
  const receipt={...task,requested_at:started,status:'failed_with_evidence'};
  try{
    const prior=reusable.get(task.url);
    if(prior){try{const buffer=await fs.readFile(path.join(project,prior.path));if(await sha256(buffer)===prior.sha256)return {...prior,...task,reused_at:new Date().toISOString()};}catch{}}
    const response=await fetch(task.url,{redirect:'follow',signal:AbortSignal.timeout(timeoutMs),headers:{'user-agent':'AreaData source audit/0.10 (+https://areadata.net/)','accept':'text/html,application/pdf,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,*/*'}});
    receipt.http_status=response.status;
    receipt.final_url=response.url;
    receipt.content_type=response.headers.get('content-type')||'';
    receipt.content_length=response.headers.get('content-length')?Number(response.headers.get('content-length')):null;
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    if(receipt.content_length&&receipt.content_length>maxBytes)throw new Error(`Content length ${receipt.content_length} exceeds ${maxBytes}`);
    const chunks=[]; let bytes=0;
    for await(const chunk of response.body){
      bytes+=chunk.length;
      if(bytes>maxBytes)throw new Error(`Response exceeds ${maxBytes} bytes`);
      chunks.push(chunk);
    }
    const buffer=Buffer.concat(chunks);
    const ext=extension(receipt.content_type,response.url);
    const countryDir=path.join(outRoot,task.country_area_id);
    await fs.mkdir(countryDir,{recursive:true});
    const filename=`${safeName(task.domain)}-${safeName(task.ordinal)}${ext}`;
    const filePath=path.join(countryDir,filename);
    await fs.writeFile(filePath,buffer);
    receipt.status='acquired';
    receipt.bytes=buffer.length;
    receipt.sha256=await sha256(buffer);
    receipt.path=path.relative(path.dirname(path.dirname(outRoot)),filePath).replaceAll('\\','/');
  }catch(error){
    receipt.error=`${error.name}: ${error.message}`;
  }
  receipt.completed_at=new Date().toISOString();
  return receipt;
}

const project=path.resolve(arg('--project',''));
if(!project)throw new Error('--project is required');
const concurrency=Number(arg('--concurrency','4'));
const maxBytes=Number(arg('--max-bytes',String(75*1024*1024)));
const timeoutMs=Number(arg('--timeout-ms','30000'));
const preflight=JSON.parse(await fs.readFile(path.join(project,'evidence','SOURCE_PREFLIGHT.json'),'utf8'));
const outRoot=path.join(project,'raw','country-source-pages');
await fs.mkdir(outRoot,{recursive:true});
const receiptPath=path.join(outRoot,'receipt.json');
let previous={receipts:[]};try{previous=JSON.parse(await fs.readFile(receiptPath,'utf8'));}catch{}
const reusable=new Map((previous.receipts||[]).filter(row=>row.status==='acquired'&&row.url&&row.path).map(row=>[row.url,row]));
const tasks=[];
for(const country of preflight.countries||[]){
  const seen=new Set();
  for(const domain of ['official_statistics_office','latest_census','census_results','table_catalog','machine_readable_data','administrative_codes','planning_law','planning_guidance','plans_budgets_implementation_evaluation']){
    let ordinal=0;
    for(const url of country[domain]?.urls||[]){
      if(!/^https?:/i.test(url)||seen.has(url))continue;
      seen.add(url); ordinal+=1;
      tasks.push({country_area_id:country.country_area_id,domain,ordinal,url});
    }
  }
  for(const round of country.recent_census_rounds||[]){
    if(!round.url||!/^https?:/i.test(round.url)||seen.has(round.url))continue;
    seen.add(round.url);
    tasks.push({country_area_id:country.country_area_id,domain:'recent_census_round',ordinal:round.year||tasks.length,url:round.url});
  }
}
const receipts=new Array(tasks.length);
let next=0;
async function worker(){
  while(true){
    const index=next++;
    if(index>=tasks.length)return;
    receipts[index]=await fetchOne(tasks[index],outRoot,{maxBytes,timeoutMs,reusable,project});
    process.stdout.write(`${index+1}/${tasks.length} ${tasks[index].country_area_id} ${receipts[index].status}\n`);
  }
}
await Promise.all(Array.from({length:Math.max(1,concurrency)},worker));
const summary={
  schema_version:'1.0',generated_at:new Date().toISOString(),collector:'collect-americas-country-sources.mjs',
  task_count:tasks.length,acquired_count:receipts.filter(x=>x.status==='acquired').length,
  failed_count:receipts.filter(x=>x.status!=='acquired').length,
  country_area_count:new Set(receipts.map(x=>x.country_area_id)).size,receipts
};
await fs.writeFile(receiptPath,JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({...summary,receipts:undefined},null,2));

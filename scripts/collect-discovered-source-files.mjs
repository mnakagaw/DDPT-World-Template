#!/usr/bin/env node
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import process from 'node:process';

function arg(name,fallback=null){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:fallback;}
function safe(value){return String(value).normalize('NFKD').replace(/[^A-Za-z0-9._-]+/g,'_').slice(0,150);}
function extFor(type,url){
  const pathname=new URL(url).pathname.toLowerCase();
  for(const ext of ['.xlsx','.xls','.csv','.geojson','.json','.pdf','.zip'])if(pathname.endsWith(ext))return ext;
  if(type.includes('spreadsheetml'))return '.xlsx'; if(type.includes('ms-excel'))return '.xls';
  if(type.includes('text/csv'))return '.csv'; if(type.includes('json'))return '.json';
  if(type.includes('pdf'))return '.pdf'; if(type.includes('zip'))return '.zip'; return '.bin';
}
const project=path.resolve(arg('--project',''));
if(!project)throw new Error('--project is required');
const countries=new Set(String(arg('--countries','')).split(',').map(x=>x.trim()).filter(Boolean));
if(!countries.size)throw new Error('--countries ISO3,ISO3 is required');
const concurrency=Number(arg('--concurrency','4')),maxBytes=Number(arg('--max-bytes',String(100*1024*1024)));
const timeoutMs=Number(arg('--timeout-ms','30000'));
const catalog=JSON.parse(await fs.readFile(path.join(project,'evidence','COUNTRY_SOURCE_LINK_CATALOG.json'),'utf8'));
const formats=/\.(?:xlsx?|csv|geojson|json|pdf|zip)$/i;
const seen=new Set(),tasks=[];
for(const page of catalog.records||[]){
  if(!countries.has(page.country_area_id)||page.domain!=='latest_census')continue;
  for(const link of page.eligible_links||[]){
    const pathname=new URL(link.url).pathname;
    if(!formats.test(pathname)||seen.has(link.url))continue;
    seen.add(link.url);tasks.push({country_area_id:page.country_area_id,domain:page.domain,page_url:page.final_url||page.source_url,label:link.label,url:link.url});
  }
}
const outRoot=path.join(project,'raw','discovered-source-files');await fs.mkdir(outRoot,{recursive:true});
const receiptPath=path.join(outRoot,'receipt.json');
let previous={receipts:[]};try{previous=JSON.parse(await fs.readFile(receiptPath,'utf8'));}catch{}
const reusable=new Map((previous.receipts||[]).filter(row=>row.status==='acquired'&&row.url&&row.path).map(row=>[row.url,row]));
const receipts=new Array(tasks.length);let next=0;
async function one(task,index){
  const r={...task,requested_at:new Date().toISOString(),status:'failed_with_evidence'};
  try{
    const prior=reusable.get(task.url);
    if(prior){try{const buffer=await fs.readFile(path.join(project,prior.path));if(crypto.createHash('sha256').update(buffer).digest('hex')===prior.sha256)return {...prior,...task,reused_at:new Date().toISOString()};}catch{}}
    const response=await fetch(task.url,{redirect:'follow',signal:AbortSignal.timeout(timeoutMs),headers:{'user-agent':'AreaData source audit/0.10 (+https://areadata.net/)','accept':'application/pdf,application/zip,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,*/*'}});
    r.http_status=response.status;r.final_url=response.url;r.content_type=response.headers.get('content-type')||'';
    r.content_length=response.headers.get('content-length')?Number(response.headers.get('content-length')):null;
    if(!response.ok)throw new Error(`HTTP ${response.status}`);if(r.content_length&&r.content_length>maxBytes)throw new Error(`Content length ${r.content_length} exceeds ${maxBytes}`);
    const chunks=[];let bytes=0;for await(const chunk of response.body){bytes+=chunk.length;if(bytes>maxBytes)throw new Error(`Response exceeds ${maxBytes} bytes`);chunks.push(chunk);}
    const buffer=Buffer.concat(chunks),ext=extFor(r.content_type,response.url),dir=path.join(outRoot,task.country_area_id);await fs.mkdir(dir,{recursive:true});
    const file=path.join(dir,`${String(index+1).padStart(3,'0')}-${safe(task.label||path.basename(new URL(task.url).pathname)||'source')}${ext}`);
    await fs.writeFile(file,buffer);r.status='acquired';r.bytes=buffer.length;r.sha256=crypto.createHash('sha256').update(buffer).digest('hex');r.path=path.relative(project,file).replaceAll('\\','/');
  }catch(error){r.error=`${error.name}: ${error.message}`;}r.completed_at=new Date().toISOString();return r;
}
async function worker(){while(true){const i=next++;if(i>=tasks.length)return;receipts[i]=await one(tasks[i],i);process.stdout.write(`${i+1}/${tasks.length} ${tasks[i].country_area_id} ${receipts[i].status}\n`);}}
await Promise.all(Array.from({length:Math.max(1,concurrency)},worker));
const result={schema_version:'1.0',generated_at:new Date().toISOString(),collector:'collect-discovered-source-files.mjs',country_area_ids:[...countries],task_count:tasks.length,acquired_count:receipts.filter(x=>x.status==='acquired').length,failed_count:receipts.filter(x=>x.status!=='acquired').length,receipts};
await fs.writeFile(receiptPath,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,receipts:undefined},null,2));

#!/usr/bin/env node
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import process from 'node:process';

const arg=name=>{const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;};
const project=path.resolve(arg('--project')||'');
const manifestPath=path.resolve(arg('--manifest')||'data/registries/americas-supplemental-sources.json');
if(!project)throw new Error('--project is required');
const manifest=JSON.parse(await fs.readFile(manifestPath,'utf8'));
const root=path.join(project,'raw','supplemental-country-sources');await fs.mkdir(root,{recursive:true});
const maxBytes=100*1024*1024,timeoutMs=30000,receipts=[];
const extension=(type,url)=>{const pathname=new URL(url).pathname.toLowerCase();for(const ext of ['.xlsx','.csv','.geojson','.json','.pdf','.zip','.html'])if(pathname.endsWith(ext))return ext;if(type.includes('pdf'))return '.pdf';if(type.includes('json'))return '.json';if(type.includes('csv'))return '.csv';return '.html';};
for(const source of manifest.sources||[]){
  const receipt={...source,requested_at:new Date().toISOString(),status:'failed_with_evidence'};
  try{
    const response=await fetch(source.url,{redirect:'follow',signal:AbortSignal.timeout(timeoutMs),headers:{'user-agent':'AreaData source audit/0.10 (+https://areadata.net/)','accept':'text/html,application/pdf,application/json,text/csv,*/*'}});
    receipt.http_status=response.status;receipt.final_url=response.url;receipt.content_type=response.headers.get('content-type')||'';
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const chunks=[];let size=0;for await(const chunk of response.body){size+=chunk.length;if(size>maxBytes)throw new Error(`Response exceeds ${maxBytes} bytes`);chunks.push(chunk);}const body=Buffer.concat(chunks);
    const dir=path.join(root,source.country_area_id);await fs.mkdir(dir,{recursive:true});const file=path.join(dir,`${source.domain}-${source.id}${extension(receipt.content_type,response.url)}`);
    await fs.writeFile(file,body);receipt.status='acquired';receipt.bytes=body.length;receipt.sha256=crypto.createHash('sha256').update(body).digest('hex');receipt.path=path.relative(project,file).replaceAll('\\','/');
  }catch(error){receipt.error=`${error.name}: ${error.message}`;}
  receipt.completed_at=new Date().toISOString();receipts.push(receipt);console.log(`${source.country_area_id} ${source.id} ${receipt.status}`);
}
const output={schema_version:'1.0',generated_at:new Date().toISOString(),manifest:path.relative(process.cwd(),manifestPath).replaceAll('\\','/'),receipts};
await fs.writeFile(path.join(root,'receipt.json'),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({acquired:receipts.filter(row=>row.status==='acquired').length,failed:receipts.filter(row=>row.status!=='acquired').length},null,2));

#!/usr/bin/env node
// Preserve public PSA PSGC API availability without requesting or recording credentials.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const output=join(project,'raw','psgc-q2-2025-api-probe');
const base='https://classification.psa.gov.ph/psgc/Q2_2025/';
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
await mkdir(output,{recursive:true});
const results=[];
for(const part of ['','regions','provinces','municipalities','city_class']){
  const url=base+part+'?format=json';
  const response=await fetch(url,{headers:{Accept:'application/json'}});
  const bytes=Buffer.from(await response.arrayBuffer());
  const file=(part||'index')+'.json';
  await writeFile(join(output,file),bytes);
  results.push({url,status:response.status,file,sha256:digest(bytes),bytes:bytes.length,
    reported_error:response.ok?null:JSON.parse(bytes.toString('utf8')).error||'unclassified'});
}
if(results[0].status!==200||results.slice(1).some(row=>row.status!==400||row.reported_error!=='Token is required.'))
  throw Error('PSGC API availability changed; inspect saved responses before updating evidence');
const receipt={checked_at:new Date().toISOString(),version:'Q2_2025',scope:'Unauthenticated public probe only; no token requested or stored',responses:results};
await writeFile(join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt,null,2));

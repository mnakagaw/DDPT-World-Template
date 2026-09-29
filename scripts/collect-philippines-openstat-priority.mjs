#!/usr/bin/env node
// Preserve a bounded cross-theme follow-up from the PSA catalogue; acquisition is not adoption.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const projectArg=process.argv.indexOf('--project');
if(projectArg<0||!process.argv[projectArg+1])throw Error('Usage: node scripts/collect-philippines-openstat-priority.mjs --project <directory>');
const raw=join(resolve(process.argv[projectArg+1]),'raw');
await mkdir(raw,{recursive:true});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const tables=[
  {id:'basic-literacy-2024',path:'3S/C10/0153E2BLRP0.px',selection:{Region:['*'],Characteristics:['Both Sexes'],Year:['2024']}},
  {id:'national-tax-allotment-2024',path:'3S/C15/0042K2BNTA0.px',selection:{Province:['*'],Year:['2024']}}
];
for(const table of tables){
  const url='https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/'+table.path;
  const metadataResponse=await fetch(url,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(25000)});
  if(!metadataResponse.ok)throw Error(`Metadata HTTP ${metadataResponse.status}: ${url}`);
  const metadataBytes=Buffer.from(await metadataResponse.arrayBuffer());
  const metadata=JSON.parse(metadataBytes.toString('utf8').replace(/^\uFEFF/,''));
  const query={query:metadata.variables.map(variable=>{
    const selection=table.selection[variable.code];
    if(!selection)throw Error(`Missing selection for ${variable.code}`);
    const values=selection[0]==='*'?variable.values:selection.map(label=>{
      const index=variable.valueTexts.indexOf(label);
      if(index<0)throw Error(`Absent ${variable.code}: ${label}`);
      return variable.values[index];
    });
    return {code:variable.code,selection:{filter:'item',values}};
  }),response:{format:'json'}};
  const dataResponse=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(query),signal:AbortSignal.timeout(45000)});
  if(!dataResponse.ok)throw Error(`Data HTTP ${dataResponse.status}: ${url}`);
  const dataBytes=Buffer.from(await dataResponse.arrayBuffer());
  const data=JSON.parse(dataBytes.toString('utf8').replace(/^\uFEFF/,''));
  if(!Array.isArray(data.data)||!data.data.length)throw Error(`Empty data: ${url}`);
  const stem=`psa-openstat-${table.id}`;
  await writeFile(join(raw,`${stem}-metadata.json`),metadataBytes);
  await writeFile(join(raw,`${stem}-data.json`),dataBytes);
  const receipt={source_url:url,method:'POST',retrieved_at:new Date().toISOString(),metadata_sha256:sha(metadataBytes),data_sha256:sha(dataBytes),metadata_bytes:metadataBytes.length,data_bytes:dataBytes.length,data_rows:data.data.length,query,adoption:'unassessed'};
  await writeFile(join(raw,`${stem}-receipt.json`),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({id:table.id,rows:receipt.data_rows,sha256:receipt.data_sha256}));
}

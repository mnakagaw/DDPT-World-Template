#!/usr/bin/env node
// Archive the official PSA OpenSTAT 2024 POPCEN catalogue and exact API slices.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw','popcen-catalogue-2024');
const base='https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/1A/PO_2024/';
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const checkedAt=new Date().toISOString();
await mkdir(raw,{recursive:true});
const get=async url=>{
  const response=await fetch(url,{headers:{Accept:'application/json'}});
  if(!response.ok)throw Error(`HTTP ${response.status}: ${url}`);
  return Buffer.from(await response.arrayBuffer());
};
const post=async(url,query)=>{
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(query)});
  if(!response.ok)throw Error(`HTTP ${response.status}: ${url}: ${(await response.text()).slice(0,300)}`);
  return Buffer.from(await response.arrayBuffer());
};
const catalogueBytes=await get(base);
const catalogue=JSON.parse(catalogueBytes);
if(catalogue.length!==24 || catalogue.some(row=>row.type!=='t'||!row.id.endsWith('.px')))
  throw Error('Unexpected PSA 2024 POPCEN catalogue');
await writeFile(join(raw,'catalogue.json'),catalogueBytes);
const receipt={source_url:base,retrieved_at:checkedAt,catalogue_sha256:digest(catalogueBytes),catalogue_bytes:catalogueBytes.length,table_count:catalogue.length,tables:[]};
for(const table of catalogue){
  const url=base+table.id;
  const stem=table.id.replace(/\.px$/,'');
  const metadataBytes=await get(url);
  const metadata=JSON.parse(metadataBytes);
  if(!Array.isArray(metadata.variables)||metadata.variables.length<2)throw Error('Unexpected metadata '+table.id);
  await writeFile(join(raw,stem+'-metadata.json'),metadataBytes);
  const parameter=metadata.variables.find(variable=>variable.code==='Parameter');
  const slices=stem==='0231A6DPUP0' && parameter?.values?.length>1
    ? parameter.values.map(value=>({label:'parameter-'+value,value}))
    : [{label:'all',value:null}];
  const tableReceipt={id:table.id,title:table.text,upstream_updated:table.updated,source_url:url,
    metadata_sha256:digest(metadataBytes),metadata_bytes:metadataBytes.length,
    variables:metadata.variables.map(variable=>({code:variable.code,text:variable.text,
      listed_value_count:variable.values?.length??null,value_texts:variable.valueTexts??null})),slices:[]};
  for(const slice of slices){
    const query={query:metadata.variables.map(variable=>({code:variable.code,
      selection:variable.code==='Parameter'&&slice.value!==null
        ? {filter:'item',values:[slice.value]} : {filter:'all',values:['*']}})),response:{format:'json'}};
    const bytes=await post(url,query);
    const parsed=JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));
    if(!Array.isArray(parsed.data)||parsed.data.length===0)throw Error('Empty data '+table.id+' '+slice.label);
    const filename=stem+'-'+slice.label+'-data.json';
    await writeFile(join(raw,filename),bytes);
    tableReceipt.slices.push({file:filename,query,sha256:digest(bytes),bytes:bytes.length,
      rows:parsed.data.length,columns:parsed.columns?.map(column=>column.code)??[]});
  }
  receipt.tables.push(tableReceipt);
  await writeFile(join(raw,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({id:table.id,slices:tableReceipt.slices.length,rows:tableReceipt.slices.reduce((n,row)=>n+row.rows,0)}));
}
console.log(JSON.stringify({tables:receipt.tables.length,rows:receipt.tables.reduce((n,table)=>n+table.slices.reduce((m,slice)=>m+slice.rows,0),0),receipt:'raw/popcen-catalogue-2024/receipt.json'}));

#!/usr/bin/env node
// Preserve official PSA OpenSTAT API responses and reproducible query receipts.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw');
await mkdir(raw,{recursive:true});
const tables=[
  {id:'popcen-households-2024',path:'1A/PO_2024/0191A6DTHP8.px',
   selection:{'Geographic Location':['*'],Parameter:['*']}},
  {id:'sdg-education-completion',path:'3I/G04/0023I3C0412.px',
   selection:{Indicator:['*'],Geolocation:['*'],'Level of Education':['*'],Sex:['*'],Year:['2024','2025']}},
  {id:'sdg-under-five-mortality',path:'3I/G03/0043I3B0321.px',
   selection:{Geolocation:['*'],Year:['2024','2025']}},
  {id:'sdg-basic-drinking-water',path:'3I/G06/0013I3E6111.px',
   selection:{Geolocation:['*'],Year:['2024 p','2025']}},
  {id:'sdg-electricity-access',path:'3I/G07/0013I5D0711.px',
   selection:{Indicator:['*'],Geolocation:['*'],Year:['2024','2025']}},
  {id:'sdg-unemployment',path:'3I/G08/0053I3A0852.px',
   selection:{'Age Group':['15 years and above'],Sex:['Both sexes'],Geolocation:['*'],Year:['2024','2025']}},
  {id:'poverty-incidence-2023',path:'1F/FY/0041F3DF02A.px',
   selection:{Geolocation:['*'],'Threshold/Incidence/Parameters':['Poverty Incidence among Population (%)'],Year:['2023']}},
  {id:'grdp-2025',path:'2B/GP/RG/GRD/0012B5BPGD1.px',
   selection:{Region:['*'],'Type of Valuation':['*'],Year:['2025']}}
];
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
for(const table of tables){
  const url='https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/'+table.path;
  const metadataResponse=await fetch(url,{headers:{Accept:'application/json'}});
  if(!metadataResponse.ok)throw Error('OpenSTAT metadata HTTP '+metadataResponse.status+' '+url);
  const metadataBytes=Buffer.from(await metadataResponse.arrayBuffer());
  const metadata=JSON.parse(metadataBytes.toString('utf8'));
  const query={query:metadata.variables.map(variable=>{
    const values=table.selection[variable.code];
    if(!values)throw Error('Missing selection for '+variable.code);
    const selected=values[0]==='*'?variable.values:values.map(text=>{
      const index=variable.valueTexts.indexOf(text);
      if(index<0)throw Error('Selected value absent from metadata: '+variable.code+' '+text);
      return variable.values[index];
    });
    return {code:variable.code,selection:{filter:'item',values:selected}};
  }),response:{format:'json'}};
  const dataResponse=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(query)});
  if(!dataResponse.ok)throw Error('OpenSTAT data HTTP '+dataResponse.status+' '+url);
  const dataBytes=Buffer.from(await dataResponse.arrayBuffer());
  const data=JSON.parse(dataBytes.toString('utf8').replace(/^\uFEFF/,''));
  if(!Array.isArray(data.data)||!data.data.length)throw Error('OpenSTAT returned no data '+url);
  const stem='psa-openstat-'+table.id;
  await writeFile(join(raw,stem+'-metadata.json'),metadataBytes);
  await writeFile(join(raw,stem+'-data.json'),dataBytes);
  const receipt={source_url:url,method:'POST',retrieved_at:new Date().toISOString(),
    metadata_sha256:sha(metadataBytes),metadata_bytes:metadataBytes.length,
    data_sha256:sha(dataBytes),data_bytes:dataBytes.length,
    data_rows:data.data.length,query,notes:'Raw PSA OpenSTAT API response; no geographic values adopted until exact PSGC-code and definition audit.'};
  await writeFile(join(raw,stem+'-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({table:table.id,rows:data.data.length,bytes:dataBytes.length,sha256:receipt.data_sha256}));
}

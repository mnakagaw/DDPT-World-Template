#!/usr/bin/env node
// Small read-only inventory of retained PSA OpenSTAT candidate tables.
import {readFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const raw=join(project,'raw');
const ids=['sdg-education-completion','sdg-under-five-mortality','sdg-basic-drinking-water',
  'sdg-electricity-access','sdg-unemployment','poverty-incidence-2023'];
for(const id of ids){
  const stem='psa-openstat-'+id;
  const metadata=JSON.parse((await readFile(join(raw,stem+'-metadata.json'),'utf8')).replace(/^\uFEFF/,''));
  const response=JSON.parse((await readFile(join(raw,stem+'-data.json'),'utf8')).replace(/^\uFEFF/,''));
  const labels=metadata.variables.map(variable=>new Map(variable.values.map((value,index)=>[value,variable.valueTexts[index]])));
  const rows=response.data.map(row=>({
    key:row.key.map((value,index)=>labels[index].get(value)||value),
    value:row.values[0]
  }));
  const yearIndex=metadata.variables.findIndex(variable=>variable.code==='Year');
  const geographyIndex=metadata.variables.findIndex(variable=>variable.code==='Geolocation');
  const byYear={};
  for(const row of rows){
    const year=row.key[yearIndex];
    if(!byYear[year])byYear[year]={numeric:0,missing:0,other:0,regions:[]};
    if(/^\d+(?:\.\d+)?$/.test(row.value)){
      byYear[year].numeric++;
      if(geographyIndex>=0 && row.key[geographyIndex].toLowerCase().includes('negros'))
        byYear[year].regions.push({label:row.key[geographyIndex],value:row.value,key:row.key});
    }else if(!row.value || /^\.\.?$/.test(row.value))byYear[year].missing++;
    else byYear[year].other++;
  }
  console.log(JSON.stringify({id,title:metadata.title,variables:metadata.variables.map(v=>({code:v.code,count:v.values.length})),
    byYear,sample:rows.slice(0,2),comments:response.comments?.length||0,
    geography_head:geographyIndex>=0?metadata.variables[geographyIndex].valueTexts.slice(0,19).map((label,index)=>({index,label,
      values:rows.filter(row=>row.key[geographyIndex]===label &&
        (id==='sdg-education-completion'?row.key[2]==='Elementary' && row.key[3]==='Both Sexes':true))
        .map(row=>({year:row.key[yearIndex],value:row.value}))})):null}));
}

#!/usr/bin/env node
// Check real exports against audited GSO/UNFPA 2019 census Table 1 cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/vietnam-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/VNM_CENSUS2019_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const fields={total:'VNM_GSO2019_POP',male:'VNM_GSO2019_MALE',female:'VNM_GSO2019_FEMALE',
  urban_total:'VNM_GSO2019_URBAN_POP',urban_male:'VNM_GSO2019_URBAN_MALE',
  urban_female:'VNM_GSO2019_URBAN_FEMALE',rural_total:'VNM_GSO2019_RURAL_POP',
  rural_male:'VNM_GSO2019_RURAL_MALE',rural_female:'VNM_GSO2019_RURAL_FEMALE'};
function csvRows(input){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=input.charCodeAt(0)===0xfeff?1:0;i<input.length;i++){
    const ch=input[i];
    if(quoted){if(ch==='"'&&input[i+1]==='"'){cell+='"';i++;}else if(ch==='"')quoted=false;else cell+=ch;}
    else if(ch==='"')quoted=true;else if(ch===','){row.push(cell);cell='';}
    else if(ch==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(x=>x!==''))rows.push(row);row=[];cell='';}
    else cell+=ch;
  }
  if(cell||row.length)rows.push([...row,cell]);
  return rows;
}
if(data.country.id!=='VNM'||data.territories.length!==64||data.boundaries?.features?.length!==0)
  fail('Expected 64 historical reporting areas and zero unsupported polygons');
const original=new Map(audit.table_1_rows.filter(row=>row.section==='census_province_city_2019')
  .map(row=>[`VNM:GSO2019:P${String(row.source_row_ordinal).padStart(2,'0')}`,row]));
original.set('VNM',audit.table_1_rows.find(row=>row.section==='country'));
const cases=['VNM','VNM:GSO2019:P01','VNM:GSO2019:P02',
  [...original].find(([,row])=>row.name==='Ho Chi Minh City')?.[0],
  [...original].find(([,row])=>row.name==='Ca Mau')?.[0]];
if(cases.some(x=>!x))fail('Representative source rows missing');
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const id of cases){
  const area=data.territories.find(row=>row.id===id),source=original.get(id);
  if(!area||!source)fail(`Missing area or source row ${id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,id,'2019'),
    'diagnostic.html':diagnosticHtml(data,id,'2019'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2019'),
    'planning.html':planningHtml(data,id,'2019','en'),
    'evidence.csv':evidenceCsv(data,id,'2019'),
  };
  const stem=`VNM-${sha(id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(out,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL',
    'Source locator','Territory ID'])if(col(key)<0)fail(`Missing CSV column ${key}`);
  const subset=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&
    row[col('Indicator ID')]===indicator);
  for(const [field,indicator] of Object.entries(fields)){
    const overall=subset('overall',indicator);
    if(overall.length!==1||overall[0][col('Status')]!=='observed'||
       Number(overall[0][col('Value')])!==source.values[field]||
       overall[0][col('Period')]!=='2019'||
       !overall[0][col('Source URL')].startsWith('https://vietnam.unfpa.org/')||
       !overall[0][col('Source locator')].includes(`column ${field}`))
      fail(`Export differs from original: ${id}/${field}`);
  }
  const childIds=data.territories.filter(row=>row.parent_id===id).map(row=>row.id);
  const within=subset('within_area',fields.total);
  if(JSON.stringify(within.map(row=>row[col('Territory ID')]))!==JSON.stringify(childIds))
    fail(`Internal comparison roster changed ${id}`);
  for(const row of within){
    const child=original.get(row[col('Territory ID')]);
    if(!child||Number(row[col('Value')])!==child.values.total)
      fail(`Internal comparison value differs ${id}/${row[col('Territory ID')]}`);
  }
  if(id==='VNM'){
    if(childIds.length!==63||childIds[0]!=='VNM:GSO2019:P01'||childIds.at(-1)!=='VNM:GSO2019:P63')
      fail('Country comparison is not all 63 historical province/city rows');
    const marker=`<section class="internal-comparison" data-internal-comparison="${fields.total}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail('Printable national comparison missing');
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)]
      .map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(childIds))
      fail('National HTML print omitted or reordered rows');
  }else if(outputs['planning.html'].includes('Hà Nội 2026–2030 socioeconomic plan')){
    fail(`Current local plan location leaked into historical province view ${id}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Selected territory absent from ${suffix}: ${id}`);
  checks.push({territory_id:id,name:area.name,source_total:source.values.total,
    internal_rows:childIds.length,first_internal_row:childIds[0]||null,
    last_internal_row:childIds.at(-1)||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([name,value])=>[name,sha(value)]))});
}
await writeFile(path.join(project,'evidence/OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['2019 administrative code and polygon correspondence missing',
    '2025 local jurisdictions and plans are separate from historical 2019 census rows',
    'District census original and report Tables 2-60 unassessed',
    'Applicable 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,name,source_total,internal_rows})=>
  ({territory_id,name,source_total,internal_rows})),null,2));

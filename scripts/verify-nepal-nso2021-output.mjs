#!/usr/bin/env node
// Check actual diagnostic and planning exports against selected NSO source cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/nepal-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const hash=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
if(data.country.id!=='NPL'||data.territories.length!==915||data.boundaries?.features?.length!==0)
  fail('Expected 915 NSO reporting units without an unverified polygon join');
const cases=[
  {area:'NPL',field:'INDV01_POPULATION',value:29164578,children:7,first:'NPL:NSO2021:P1',last:'NPL:NSO2021:P7',locator:'Indv01-Koshi!D6'},
  {area:'NPL:NSO2021:P1',field:'INDV01_POPULATION',value:4961412,children:14,first:'NPL:NSO2021:P1:D01',last:'NPL:NSO2021:P1:D14',locator:'Indv01-Koshi!D8'},
  {area:'NPL:NSO2021:P3:D06',field:'INDV01_POPULATION',value:2041587,children:12,first:'NPL:NSO2021:P3:D06:L01',last:'NPL:NSO2021:P3:D06:I',locator:'Indv01-Bagmati!D81'},
  {area:'NPL:NSO2021:P3:D06:L08',field:'INDV01_POPULATION',value:862400,children:0,locator:'Indv01-Bagmati!D90'},
  {area:'NPL:NSO2021:P3:D06:L08',field:'HHLD06_PIPED_INSIDE',value:114972,children:0},
  {area:'NPL:NSO2021:P3:D06:I',field:'INDV01_POPULATION',value:47032,children:0},
  {area:'NPL:NSO2021:P7:D09:L05',field:'HHLD09_NO_TOILET',value:712,children:0},
  {area:'NPL:NSO2021:P3:D03:L04',field:'INDV01_POPULATION',value:10115,children:0},
];
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
const outputDir=path.join(project,'evidence','output-verification');
await mkdir(outputDir,{recursive:true});
const checks=[];
for(const item of cases){
  const area=data.territories.find(row=>row.id===item.area);
  if(!area)fail(`Missing territory ${item.area}`);
  const iid='NPL_NSO2021_'+item.field;
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2021'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2021'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2021'),
    'planning.html':planningHtml(data,item.area,'2021','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2021'),
  };
  const stem=`NPL-${hash(item.area+iid).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=matching('overall'),within=matching('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
      overall[0][col('Period')]!=='2021'||overall[0][col('Status')]!=='observed')
    fail(`Value/period/status mismatch ${item.area} ${iid}`);
  if(item.locator&&!overall[0][col('Source locator')].includes(item.locator))
    fail(`Source cell locator mismatch ${item.area} ${iid}`);
  if(!overall[0][col('Source URL')].includes('censusresults.nsonepal.gov.np/files/province/'))
    fail(`Original NSO workbook URL missing ${item.area}`);
  if(within.length!==item.children)fail(`Child count mismatch ${item.area}: ${within.length}`);
  if(item.children){
    const actual=within.map(row=>row[col('Territory ID')]);
    if(actual[0]!==item.first||actual.at(-1)!==item.last)fail(`First/last child mismatch ${item.area}`);
    if(within.some(row=>row[col('Comparable')]!=='true'))fail(`Source-matched comparison excluded ${item.area}`);
    if(within.reduce((sum,row)=>sum+Number(row[col('Value')]),0)!==item.value)
      fail(`Child population sum mismatch ${item.area}`);
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${item.area}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(actual))fail(`Printed comparison drops/reorders rows ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selected area in ${suffix}: ${item.area}`);
  if(item.area==='NPL:NSO2021:P3:D06:L08'){
    if(!outputs['planning.html'].includes('Annual Action Plan 2083/84')||
       !outputs['planning.html'].includes('Annual Budget and Program 2083/84')||
       !outputs['planning.html'].includes('Annual Progress Report 2082/83'))
      fail('Kathmandu city planning documents missing');
  }else if(item.area==='NPL:NSO2021:P3:D06'){
    if(outputs['planning.html'].includes('Annual Action Plan 2083/84'))
      fail('Kathmandu city plan leaked into district selection');
  }
  checks.push({territory_id:item.area,indicator_id:iid,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,hash(value)]))});
}
for(const areaId of ['NPL:NSO2021:P3:D03:L04','NPL:NSO2021:P7:D09:L05']){
  const area=data.territories.find(row=>row.id===areaId);
  if(area?.official_code!==null||area?.reconciliation_status!=='name_conflict_unresolved')
    fail(`Unresolved official local code was asserted: ${areaId}`);
}
const na=data.observations.filter(row=>row.indicator_id.startsWith('NPL_NSO2021_')&&row.status==='not_applicable');
if(na.length!==1155||na.some(row=>row.value!==null||!row.territory_id.endsWith(':I')))
  fail('Institutional household universe was misrepresented');
if(data.documents.some(row=>row.territory_id==='NPL:NSO2021:P3:D06'&&['plan','budget','implementation'].includes(row.category)))
  fail('Kathmandu city planning body assigned to district');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:hash(bytes),cases:checks,
  institutional_amenity_not_applicable:na.length,
  constraints:['Two 2021/2023 local name conflicts have no asserted official code',
    'No NSO-compatible official polygon; generator provider shapes removed',
    'Only 21 selected census workbooks adopted; 7 literacy files remain unassessed and 85 other XLSX families per province remain unacquired',
    'Kathmandu city PDFs acquired but full planning content/approval and other palikas not audited',
    'All 42 scenarios, mobile/print/PDF/Word and independent acceptance are pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,indicator_id,value,internal_rows})=>
  ({territory_id,indicator_id,value,internal_rows})),null,2));

#!/usr/bin/env node
// Check selected PHCB source rows against the actual country export renderers.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/bhutan-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
if(data.country.id!=='BTN'||data.territories.length!==290||data.boundaries?.features?.length!==0)
  fail('Expected 290 PHCB reporting units and no unverified polygon join');
const indicator='BTN_PHCB2017_POPULATION';
const cases=[
  {area:'BTN',value:727145,children:20,first:'BTN:PHCB2017:D:bumthang',
    last:'BTN:PHCB2017:D:zhemgang',locator:'Table 2.1'},
  {area:'BTN:PHCB2017:D:haa',value:13655,children:8,
    first:'BTN:PHCB2017:D:haa:T01',last:'BTN:PHCB2017:D:haa:G06',locator:'Table A2.1'},
  {area:'BTN:PHCB2017:D:thimphu',value:138736,children:10,
    first:'BTN:PHCB2017:D:thimphu:T01',last:'BTN:PHCB2017:D:thimphu:G08',locator:'Table A2.1'},
  {area:'BTN:PHCB2017:D:haa:T01',value:2596,children:0,locator:'Haa Town row'},
  {area:'BTN:PHCB2017:D:haa:G01',value:3321,children:0,locator:'Bji row'},
  {area:'BTN:PHCB2017:D:thimphu:T01',value:114551,children:0,locator:'Thimphu Thromde row'},
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
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2017'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2017'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2017'),
    'planning.html':planningHtml(data,item.area,'2017','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2017'),
  };
  const stem=`BTN-${sha(item.area).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=(scope,iid)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=matching('overall',indicator),within=matching('within_area',indicator);
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
     overall[0][col('Period')]!=='2017'||overall[0][col('Status')]!=='observed')
    fail(`Value/period/status mismatch ${item.area}`);
  if(!overall[0][col('Source locator')].includes(item.locator)||
     !overall[0][col('Source URL')].startsWith('https://nsb.gov.bt/'))
    fail(`Official source page or URL missing ${item.area}`);
  if(within.length!==item.children)fail(`Child count mismatch ${item.area}: ${within.length}`);
  if(item.children){
    const actual=within.map(row=>row[col('Territory ID')]);
    if(actual[0]!==item.first||actual.at(-1)!==item.last)fail(`First/last child mismatch ${item.area}`);
    if(within.some(row=>row[col('Comparable')]!=='true'))fail(`Source-matched comparison excluded ${item.area}`);
    if(within.reduce((sum,row)=>sum+Number(row[col('Value')]),0)!==item.value)
      fail(`Child sum mismatch ${item.area}`);
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${item.area}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(actual))fail(`Printable comparison drops rows ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selected area in ${suffix}: ${item.area}`);
  if(outputs['planning.html'].includes('Adopted local plan')||
     outputs['planning.html'].includes('Approved local budget'))
    fail(`Unverified local plan or budget appeared at ${item.area}`);
  checks.push({territory_id:item.area,value:item.value,internal_rows:within.length,
    first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,sha(value)]))});
}
if(data.documents.length)fail('Unverified area-specific documents must remain absent');
const allFound='BTN_PHCB2017_ALL_FOUND_INCLUDING_HOTEL_VISITORS';
for(const area of ['BTN','BTN:PHCB2017:D:haa']){
  const [header,...rows]=csvRows(diagnosticCsv(data,area,'2017'));
  const col=key=>header.indexOf(key);
  const overall=rows.filter(row=>row[col('Record scope')]==='overall'&&row[col('Indicator ID')]===allFound);
  if(overall.length!==1)fail(`All-found indicator absent ${area}`);
  if(area==='BTN'){
    if(Number(overall[0][col('Value')])!==735553||overall[0][col('Status')]!=='observed')
      fail('National all-found count mismatches source');
    if(rows.some(row=>row[col('Record scope')]==='within_area'&&row[col('Indicator ID')]===allFound&&row[col('Comparable')]==='true'))
      fail('Hotel-inclusive national count has a comparable district partition');
  }else if(overall[0][col('Value')]!==''||overall[0][col('Status')]==='observed')
    fail('District all-found count was filled without a direct source');
}
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['Only Table A2.1 selected population/sex cells and national Table 2.1 adopted',
    'Other 641 district report table headings and their numeric fields remain priority_unassessed',
    'No compatible official 2017 codes/polygons or legal local-government geography crosswalk',
    'No area-specific adopted plan, budget, expenditure or official evaluation',
    'All 42 scenarios, mobile/print/PDF/Word and independent acceptance remain pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,value,internal_rows})=>
  ({territory_id,value,internal_rows})),null,2));

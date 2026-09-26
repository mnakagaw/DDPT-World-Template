#!/usr/bin/env node
// Producer-side content checks against pinned CYSTAT 2021 source cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/cyprus-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
if(data.country.id!=='CYP'||data.boundaries?.features?.length!==0||data.territories.length!==516)
  throw new Error('Expected Cyprus census candidate with unjoined provider geometry');
const cases=[
  {area:'CYP:CYSTAT:CTRL2021',indicator:'POP_TOTAL',value:923381,children:5,table:'1891108E'},
  {area:'CYP:CYSTAT:DIST:1',indicator:'POP_TOTAL',value:350035,children:113,table:'1891108E'},
  {area:'CYP:CYSTAT:LOC:1000',indicator:'POP_TOTAL',value:56479,children:19,table:'1891108E'},
  {area:'CYP:CYSTAT:QTR:100001',indicator:'HOUSING_TOTAL',value:2717,children:0,table:'1891164E'},
  {area:'CYP:CYSTAT:DIST:3',indicator:'HOUSING_TOTAL',value:40260,children:9,table:'1891161E'},
  {area:'CYP:CYSTAT:LOC:3100',indicator:'LAB_EMPLOYED',value:2300,children:0,table:'1891712E'},
  {area:'CYP:CYSTAT:LOC:1110',indicator:'POP_TOTAL',value:0,children:0,table:'1891108E'},
  {area:'CYP:CYSTAT:LOC:6126',indicator:'INSTITUTION_POP',value:1,children:0,table:'1891161E'},
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
  const territory=data.territories.find(row=>row.id===item.area);
  if(!territory)throw new Error(`Missing area ${item.area}`);
  const iid='CYP_CYSTAT_'+item.indicator,period='2021-10-01';
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,period),
    'diagnostic.html':diagnosticHtml(data,item.area,period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,period),
    'planning.html':planningHtml(data,item.area,period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,period),
  };
  const stem=`CYP-${sha(item.area+iid).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)throw new Error(`Missing CSV column ${key}`);
  const selected=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=selected('overall'),within=selected('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
      overall[0][col('Period')]!==period||overall[0][col('Status')]!=='observed')
    throw new Error(`Value/period error: ${item.area} ${iid}`);
  if(within.length!==item.children)throw new Error(`Wrong internal row count: ${item.area} ${iid}: ${within.length}`);
  if(item.children&&within.some(row=>row[col('Comparable')]!=='true'))
    throw new Error(`Same-concept child excluded: ${item.area} ${iid}`);
  if(!overall[0][col('Source URL')].includes('cystatdb.cystat.gov.cy')||
      !overall[0][col('Source locator')].includes(item.table))
    throw new Error(`Source table locator missing: ${item.area} ${iid}`);
  if(item.children){
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error(`Printable comparison missing: ${item.area}`);
    const actual=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(actual)!==JSON.stringify(expected))
      throw new Error(`Printable comparison omits or changes rows: ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(territory.name))throw new Error(`Wrong territory in ${suffix}: ${item.area}`);
  checks.push({territory_id:item.area,indicator:iid,value:item.value,internal_rows:within.length,
    first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,sha(value)]))});
}
const obs=(area,key)=>data.observations.find(row=>row.territory_id===area&&row.indicator_id==='CYP_CYSTAT_'+key);
if(obs('CYP','POP_TOTAL')||obs('CYP:CYSTAT:QTR:100001','LAB_EMPLOYED'))
  throw new Error('Census scope or quarter labour value was silently filled');
if(obs('CYP:CYSTAT:LOC:1110','HOUSING_TOTAL')||obs('CYP:CYSTAT:LOC:1110','CIT_CYPRIOT'))
  throw new Error('Unpublished zero-population locality fields were silently filled');
if(obs('CYP:CYSTAT:LOC:6126','HH_AVG_SIZE'))
  throw new Error('Pitargou average household size was invented');
const wdi=data.observations.find(row=>row.territory_id==='CYP'&&row.indicator_id==='SP.POP.TOTL'&&row.period==='2021');
if(!wdi||wdi.value===923381)throw new Error('WDI population and controlled-area census were merged');
const scopeOutput=await readFile(path.join(outputDir,
  `CYP-${sha('CYP:CYSTAT:CTRL2021CYP_CYSTAT_POP_TOTAL').slice(0,12)}-planning.html`),'utf8');
if(!scopeOutput.includes('Official development plan catalogue')||!scopeOutput.includes('Link verified'))
  throw new Error('Planning catalogue or acquisition stage missing from export');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  distinct_country_wdi_2021:wdi.value,
  constraints:['Census coverage is government-controlled area, not the country root',
    '39 census matrices remain location-only and seven selected matrices are only partly semantically adopted',
    '2024 legal geography, official matching polygons and planning document bodies require further verification',
    'All 42 scenarios, PDF/Word output and independent acceptance are pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,indicator,value,internal_rows})=>
  ({territory_id,indicator,value,internal_rows})),null,2));

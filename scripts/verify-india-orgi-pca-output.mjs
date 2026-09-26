#!/usr/bin/env node
// Actual producer-side export checks against pinned ORGI 2011 PCA cells.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/india-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const hash=value=>createHash('sha256').update(value).digest('hex');
if(data.country.id!=='IND'||data.territories.length!==676||data.boundaries?.features?.length!==0)
  throw new Error('Expected source-coded 2011 India candidate without joined provider geometry');
const cases=[
  {area:'IND',field:'TOT_P',value:1210854977,children:35},
  {area:'IND:ORGI2011:STATE:01',field:'TOT_P',value:12541302,children:22},
  {area:'IND:ORGI2011:STATE:28',field:'TOT_P',value:84580777,children:23},
  {area:'IND:ORGI2011:STATE:07',field:'TOT_P_URBAN',value:16368899,children:9},
  {area:'IND:ORGI2011:DIST:01:001',field:'TOT_P',value:870354,children:0},
  {area:'IND:ORGI2011:DIST:01:003',field:'TOT_P_RURAL',value:87816,children:0},
  {area:'IND:ORGI2011:DIST:07:094',field:'TOT_P_RURAL',value:0,children:0},
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
  if(!territory)throw new Error(`Missing ${item.area}`);
  const iid='IND_CENSUS2011_'+item.field;
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2011'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2011'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2011'),
    'planning.html':planningHtml(data,item.area,'2011','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2011'),
  };
  const stem=`IND-${hash(item.area+iid).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)throw new Error(`Missing CSV column ${key}`);
  const selected=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=selected('overall'),within=selected('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
      overall[0][col('Period')]!=='2011'||overall[0][col('Status')]!=='observed')
    throw new Error(`Value, period or status error: ${item.area} ${iid}`);
  if(within.length!==item.children)throw new Error(`Wrong internal row count: ${item.area} ${iid}: ${within.length}`);
  if(item.children&&within.some(row=>row[col('Comparable')]!=='true'))
    throw new Error(`Same-source child excluded: ${item.area} ${iid}`);
  if(!overall[0][col('Source URL')].includes('censusindia.gov.in')||
      !overall[0][col('Source locator')].includes('Sheet1!R'))
    throw new Error(`Original workbook locator absent: ${item.area} ${iid}`);
  if(item.children){
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error(`Printable comparison missing: ${item.area}`);
    const actual=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(actual)!==JSON.stringify(expected))
      throw new Error(`Printable comparison differs: ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(suffix.endsWith('.html')
      ?territory.name.replaceAll('&','&amp;'):territory.name))
      throw new Error(`Wrong target in ${suffix}: ${item.area}`);
  checks.push({territory_id:item.area,indicator_id:iid,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,hash(value)]))});
}
const wdi=data.observations.find(row=>row.territory_id==='IND'&&row.indicator_id==='SP.POP.TOTL'&&row.period==='2011');
if(!wdi||wdi.value===1210854977)throw new Error('WDI and census series conflated');
if(data.documents.some(row=>row.territory_id!=='IND'&&row.id.startsWith('ind-')))
  throw new Error('National guidance incorrectly attached as an area plan');
const sourceText=JSON.stringify(data);
if(!sourceText.includes('2026-27')||!sourceText.includes('District Panchayat'))
  throw new Error('Planning guidance not represented');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:hash(bytes),cases:checks,
  distinct_wdi_population_2011:wdi.value,
  constraints:['No 2011 source-compatible polygon or current LGD/Panchayat crosswalk',
    'Other official PCA source bodies and 231 field/reporting-row combinations remain unassessed',
    'Area-specific plans, budgets, expenditure, evaluations and legal applicability are not verified',
    'All 42 scenarios, mobile/print/PDF/Word and independent acceptance are pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,indicator_id,value,internal_rows})=>
  ({territory_id,indicator_id,value,internal_rows})),null,2));

#!/usr/bin/env node
// Check actual candidate exports against NSIA 1404 Table 4 source locators.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/afghanistan-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const hash=value=>createHash('sha256').update(value).digest('hex');
if(data.country.id!=='AFG'||data.territories.length!==36||data.boundaries?.features?.length!==0)
  throw new Error('Expected NSIA candidate without an unverified polygon join');
const cases=[
  {area:'AFG',field:'FULL_POP_EST',value:36435197,children:1,locator:'PDF p31 Table 4 Total Population',childStatus:'not_collected'},
  {area:'AFG:NSIA1404:SETTLED_PROVINCES',field:'SETTLED_POP_EST',value:34935197,children:34,locator:'PDF p31 Table 4 Total (settled provinces)'},
  {area:'AFG:NSIA1404:PROVINCE:01',field:'SETTLED_POP_EST',value:6173494,children:0,locator:'PDF p31 Table 4 serial 1 Kabul'},
  {area:'AFG:NSIA1404:PROVINCE:17',field:'SETTLED_FEMALE_EST',value:564381,children:0,locator:'PDF p31 Table 4 serial 17 Badakhshan'},
  {area:'AFG:NSIA1404:PROVINCE:27',field:'SETTLED_MALE_EST',value:798992,children:0,locator:'PDF p32 Table 4 serial 27 Kandahar'},
  {area:'AFG:NSIA1404:PROVINCE:32',field:'SETTLED_FEMALE_EST',value:1176238,children:0,locator:'PDF p32 Table 4 serial 32 Herat'},
  {area:'AFG:NSIA1404:PROVINCE:34',field:'SETTLED_POP_EST',value:201140,children:0,locator:'PDF p32 Table 4 serial 34 Nimroz'},
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
  if(!area)throw new Error(`Missing territory ${item.area}`);
  const iid='AFG_NSIA1404_'+item.field;
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2025-26'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2025-26'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2025-26'),
    'planning.html':planningHtml(data,item.area,'2025-26','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2025-26'),
  };
  const stem=`AFG-${hash(item.area+iid).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)throw new Error(`Missing diagnostic CSV column ${key}`);
  const matching=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=matching('overall'),within=matching('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
      overall[0][col('Period')]!=='2025-26'||overall[0][col('Status')]!=='observed')
    throw new Error(`Value/period/status mismatch: ${item.area} ${iid}`);
  if(within.length!==item.children)throw new Error(`Internal row count mismatch: ${item.area} ${iid}: ${within.length}`);
  if(item.childStatus){
    if(within[0][col('Status')]!==item.childStatus||within[0][col('Value')]!=='')
      throw new Error('Full national series was copied into the settled scope');
  } else if(item.children && within.some(row=>row[col('Comparable')]!=='true'))
    throw new Error(`Verified 34-province cohort excluded: ${item.area}`);
  if(!overall[0][col('Source URL')].includes('nsia.gov.af:8443')||
      !overall[0][col('Source locator')].includes(item.locator))
    throw new Error(`NSIA PDF source locator absent: ${item.area}`);
  if(item.children===34){
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error('Printable 34-province table missing');
    const actual=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(actual)!==JSON.stringify(expected)||actual[0]!=='AFG:NSIA1404:PROVINCE:01'||
        actual.at(-1)!=='AFG:NSIA1404:PROVINCE:34')
      throw new Error('Printable comparison first/last/full rows differ');
    if(within.reduce((sum,row)=>sum+Number(row[col('Value')]),0)!==item.value)
      throw new Error('Within-area province totals do not cover the settled subtotal');
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error(`Wrong target in ${suffix}: ${item.area}`);
  checks.push({territory_id:item.area,indicator_id:iid,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,hash(value)]))});
}
const wdi=data.observations.find(row=>row.territory_id==='AFG'&&row.indicator_id==='SP.POP.TOTL'&&row.period==='2025');
if(!wdi||wdi.value!==43844111||wdi.value===36435197)throw new Error('WDI and NSIA estimates conflated');
if(data.observations.some(row=>row.territory_id==='AFG'&&row.indicator_id.startsWith('AFG_NSIA1404_SETTLED_')))
  throw new Error('Settled estimate incorrectly assigned to full country');
if(data.observations.some(row=>row.territory_id!=='AFG'&&row.indicator_id.startsWith('AFG_NSIA1404_FULL_')))
  throw new Error('Nomadic-inclusive national estimate copied into a province');
if(data.documents.some(row=>row.id.startsWith('afg-')&&['plan','budget','implementation','evaluation'].includes(row.category)))
  throw new Error('City planning source location misrepresented as acquired area plan');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:hash(bytes),cases:checks,
  distinct_wdi_population_2025:wdi.value,
  constraints:['NSIA 1404 is a projection from an old base, not a new census; WDI is separate',
    'Nomadic population is unallocated to provinces; 34 provinces cover only the settled subtotal',
    'No official province codes or compatible polygons; no matched city or province plan body',
    'Other 75 NSIA tables and conflicting household totals remain unadopted',
    'TLS identity of NSIA source was not verified; re-acquisition and independent audit pending',
    'All 42 scenarios, mobile/print/PDF/Word and independent acceptance are pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,indicator_id,value,internal_rows})=>
  ({territory_id,indicator_id,value,internal_rows})),null,2));

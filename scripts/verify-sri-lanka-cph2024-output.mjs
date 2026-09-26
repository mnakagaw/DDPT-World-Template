#!/usr/bin/env node
// Compare rendered/exported census diagnostics with pinned DCS source cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/sri-lanka-areadata-20260927');
const datasetBytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(datasetBytes.toString('utf8'));
const hash=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
if(data.country.id!=='LKA'||data.territories.length!==375||data.boundaries?.features?.length!==0)
  fail('Expected 375 DCS reporting units and no unverified polygon join');

const cases=[
  {area:'LKA',field:'POPULATIONA_A5_POPULATION',value:21781800,children:9,
    first:'LKA:DCS2024:P1',last:'LKA:DCS2024:P9',locator:'A5!C8'},
  {area:'LKA:DCS2024:P1',field:'POPULATIONA_A5_POPULATION',value:6117341,children:3,
    first:'LKA:DCS2024:P1:D1',last:'LKA:DCS2024:P1:D3',locator:'Table 3.2'},
  {area:'LKA:DCS2024:P1:D1',field:'POPULATIONA_A5_POPULATION',value:2375415,children:13,
    first:'LKA:DCS2024:P1:D1:DS03',last:'LKA:DCS2024:P1:D1:DS36',locator:'A5!C10'},
  {area:'LKA:DCS2024:P1:D1:DS03',field:'POPULATIONA_A5_POPULATION',value:292089,
    children:0,locator:'A5!C12'},
  {area:'LKA:DCS2024:P1:D1:DS03',field:'HOUSINGA_A14_HOUSEHOLDS',value:72479,
    children:0,locator:'A14!B10'},
  {area:'LKA:DCS2024:P1:D1:DS03',field:'HOUSINGA_A14_WATER_BOARD_PIPED',value:69967,
    children:0,locator:'A14!H10'},
  {area:'LKA:DCS2024:P1:D1:DS03',field:'HOUSINGA_A16_NO_TOILET',value:37,
    children:0,locator:'A16!I10'},
  {area:'LKA:DCS2024:P1:D1:DS36',field:'POPULATIONA_A5_POPULATION',value:263541,
    children:0,locator:'A5!C24'},
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
  const iid='LKA_DCS2024_'+item.field;
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,'2024'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2024'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2024'),
    'planning.html':planningHtml(data,item.area,'2024','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2024'),
  };
  const stem=`LKA-${hash(item.area+iid).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===iid);
  const overall=matching('overall'),within=matching('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
      overall[0][col('Period')]!=='2024'||overall[0][col('Status')]!=='observed')
    fail(`Value/period/status mismatch ${item.area} ${iid}`);
  if(!overall[0][col('Source locator')].includes(item.locator))
    fail(`Source cell locator mismatch ${item.area} ${iid}`);
  if(!overall[0][col('Source URL')].includes('statistics.gov.lk/')||
     !overall[0][col('Source URL')].includes(item.area==='LKA:DCS2024:P1'?'/CPH_2024/CPH2024_Final_Eng.pdf':'/CPH2024/'))
    fail(`Original DCS URL missing ${item.area}`);
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
  if(outputs['planning.html'].includes('Colombo Municipal Council')||
     outputs['planning.html'].includes('2026 Budget'))
    fail(`Municipal document incorrectly attached to census area ${item.area}`);
  checks.push({territory_id:item.area,indicator_id:iid,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,hash(value)]))});
}
for(const areaId of ['LKA:DCS2024:P1','LKA:DCS2024:P2']){
  const obs=data.observations.find(row=>row.territory_id===areaId&&
    row.indicator_id==='LKA_DCS2024_HOUSINGA_A14_HOUSEHOLDS');
  if(obs)fail(`Province households were filled without a direct source or aggregation rule: ${areaId}`);
  const [header,...rows]=csvRows(diagnosticCsv(data,areaId,'2024'));
  const col=key=>header.indexOf(key);
  const overall=rows.find(row=>row[col('Record scope')]==='overall'&&
    row[col('Indicator ID')]==='LKA_DCS2024_HOUSINGA_A14_HOUSEHOLDS');
  if(!overall||overall[col('Value')]!==''||overall[col('Status')]==='observed')
    fail(`Province households should remain visibly missing: ${areaId}`);
}
if(data.documents.some(row=>row.territory_id?.startsWith('LKA:DCS2024')))
  fail('A local-authority document was assigned to a census reporting unit');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:hash(datasetBytes),cases:checks,
  constraints:['Only three of 23 numbered A workbooks have a detailed numeric-semantic audit',
    'GN workbooks remain unadopted; eight provisional GN age rows differ from final DS rows',
    'No DCS-compatible polygons or proven local-government geography crosswalk',
    'No area-specific adopted plan, budget body, expenditure or official evaluation',
    'All 42 scenarios, mobile/print/PDF/Word and independent acceptance remain pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,indicator_id,value,internal_rows})=>
  ({territory_id,indicator_id,value,internal_rows})),null,2));

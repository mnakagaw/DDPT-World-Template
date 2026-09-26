#!/usr/bin/env node
// Compare selected CPH source cells with actual country diagnostic and planning exports.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/maldives-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const iid=field=>`MDV_CPH2022_${field.toUpperCase()}`;
if(data.country.id!=='MDV'||data.territories.length!==218||data.boundaries?.features?.length!==0)
  fail('Expected 218 census reporting units and zero unverified polygon joins');
const cases=[
  {area:'MDV',value:515132,children:22,first:'MDV:CPH2022:MAALE',
    last:'MDV:CPH2022:NONADMIN',source:'p5'},
  {area:'MDV:CPH2022:MAALE',value:211908,children:9,
    first:'MDV:CPH2022:MAALE:P09',last:'MDV:CPH2022:MAALE:P17',source:'p5'},
  {area:'MDV:CPH2022:A:HA',value:14623,children:14,
    first:'MDV:CPH2022:A:HA:I020',last:'MDV:CPH2022:A:HA:I033',source:'p4'},
  {area:'MDV:CPH2022:A:L',value:14699,children:11,
    first:'MDV:CPH2022:A:L:I170',last:'MDV:CPH2022:A:L:I180',source:'p4'},
  {area:'MDV:CPH2022:A:L:I171',value:2986,children:0,source:'p5',plan:true},
  {area:'MDV:CPH2022:NONADMIN',value:66313,children:0,source:'p5'},
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
    'diagnostic.csv':diagnosticCsv(data,item.area,'2022'),
    'diagnostic.html':diagnosticHtml(data,item.area,'2022'),
    'diagnostic.md':diagnosticMarkdown(data,item.area,'2022'),
    'planning.html':planningHtml(data,item.area,'2022','en'),
    'evidence.csv':evidenceCsv(data,item.area,'2022'),
  };
  const stem=`MDV-${sha(item.area).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=(scope,id)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===id);
  const overall=matching('overall',iid('population')),
        within=matching('within_area',iid('population'));
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
     overall[0][col('Period')]!=='2022'||overall[0][col('Status')]!=='observed')
    fail(`Population value, period or status mismatch ${item.area}`);
  if(!overall[0][col('Source URL')].startsWith('https://statisticsmaldives.gov.mv/')||
     !overall[0][col('Source locator')].includes(`Table ${item.source.toUpperCase()} row`))
    fail(`Official source locator missing ${item.area}`);
  if(within.length!==item.children)fail(`Child count mismatch ${item.area}: ${within.length}`);
  if(item.children){
    const actual=within.map(row=>row[col('Territory ID')]);
    if(actual[0]!==item.first||actual.at(-1)!==item.last)fail(`First/last child mismatch ${item.area}`);
    if(within.some(row=>row[col('Comparable')]!=='true'))fail(`Source-matched comparison excluded ${item.area}`);
    if(within.reduce((sum,row)=>sum+Number(row[col('Value')]),0)!==item.value)
      fail(`Child population sum mismatch ${item.area}`);
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid('population')}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${item.area}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(actual))fail(`Printable comparison drops rows ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selected area in ${suffix}: ${item.area}`);
  const hasPlan=outputs['planning.html'].includes('Fonadhoo Council Development Plan');
  if(hasPlan!==Boolean(item.plan))fail(`Fonadhoo plan leaked or absent at ${item.area}`);
  if(outputs['planning.html'].includes('Approved local plan')||
     outputs['planning.html'].includes('Official evaluation complete'))
    fail(`Unverified status overstated at ${item.area}`);
  checks.push({territory_id:item.area,value:item.value,internal_rows:within.length,
    first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,plan_document:hasPlan,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,sha(value)]))});
}
const observed=(tid,field)=>data.observations.find(row=>row.territory_id===tid&&row.indicator_id===iid(field));
for(const [tid,field,value] of [
  ['MDV','households',94424],['MDV','safe_source_reported',70033],
  ['MDV','population_15_plus',411219],['MDV','maldivian_literate_mother_tongue',313917],
  ['MDV:CPH2022:A:HA','households',3182],
  ['MDV:CPH2022:A:L:I171','households',556],
  ['MDV:CPH2022:A:L:I171','employed',1282],
]) if(observed(tid,field)?.value!==value)fail(`Selected source field mismatch ${tid} ${field}`);
if(observed('MDV:CPH2022:MAALE:P17','maldivian_female'))
  fail('P5 source-blank G17 must not be inferred zero');
for(const tid of ['MDV:CPH2022:A:L:I180','MDV:CPH2022:A:GDH:I194'])
  for(const field of ['population_15_plus','maldivian_literate_mother_tongue'])
    if(observed(tid,field))fail(`Unmatched EC3/ED16 island name silently adopted: ${tid}`);
if(observed('MDV:CPH2022:A:HA','employed'))
  fail('Incomplete island employment was promoted to parent atoll');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['Only selected fields in P4/P5/H2/H7/EC3/ED16 adopted',
    'Other 52 source workbooks and unselected fields priority_unassessed',
    '2022 atoll reporting groups are not current council jurisdictions',
    'Two unmatched island names per EC3/ED16 held; P5 G17 blank retained',
    'Official island polygons/codes, current plans/budgets, all 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,value,internal_rows,plan_document})=>
  ({territory_id,value,internal_rows,plan_document})),null,2));

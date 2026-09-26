#!/usr/bin/env node
// Check real diagnostic and planning exports against pinned Chapter 1 cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/armenia-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='ARM'||data.boundaries?.features?.length!==0)
  throw new Error('Expected unjoined Armenia census candidate');
const cases=[
  {area:'ARM',indicator:'PERMANENT_TOTAL',value:2932731,children:11,cell:'D8'},
  {area:'ARM',indicator:'PRESENT_TOTAL',value:2689438,children:11,cell:'D8'},
  {area:'ARM:HD002:01001000',indicator:'PERMANENT_TOTAL',value:1086677,children:12,cell:'D11'},
  {area:'ARM:HD002:01001013',indicator:'PRESENT_TOTAL',value:103469,children:0,cell:'D12'},
  {area:'ARM:HD002:02000000',indicator:'PERMANENT_TOTAL',value:128941,children:8,cell:'D24'},
  {area:'ARM:HD002:02001000',indicator:'PERMANENT_TOTAL',value:61859,children:0,cell:'D28'},
  {area:'ARM:HD002:08000000',indicator:'PRESENT_MALE',value:93221,children:6,cell:'G154'},
  {area:'ARM:HD002:08001000',indicator:'PRESENT_MALE',value:45575,children:0,cell:'G158'},
  {area:'ARM:HD002:09001000',indicator:'PERMANENT_TOTAL',value:37868,children:0,cell:'D173'},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function parseCsv(input){
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
const out=path.join(project,'evidence','output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const territory=data.territories.find(x=>x.id===item.area);
  if(!territory)throw new Error('Missing territory '+item.area);
  const indicator='ARM_ARMSTAT2022_'+item.indicator,period='2022';
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,period),
    'diagnostic.html':diagnosticHtml(data,item.area,period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,period),
    'planning.html':planningHtml(data,item.area,period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,period),
  };
  const stem=`ARM-${sha(item.area+indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
     overall[0][col('Period')]!==period||overall[0][col('Status')]!=='observed')
    throw new Error('Census output value/status mismatch: '+item.area+' '+indicator);
  if(within.length!==item.children)throw new Error('Wrong internal row count: '+item.area);
  if(!overall[0][col('Source URL')].includes('armstat.am')||
     !overall[0][col('Source locator')].includes(item.cell))
    throw new Error('Missing original census locator: '+item.area+' '+indicator);
  if(item.children){
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker);
    const end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error('Printable comparison missing: '+item.area);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(x=>x[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(printed)!==JSON.stringify(expected))
      throw new Error('Full printable rows disagree with CSV: '+item.area);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(territory.name))throw new Error('Selected area wrong in '+suffix);
  if(item.area==='ARM:HD002:02001000'){
    const plan=outputs['planning.html'];
    for(const expected of ['Ashtarak Community Development Programme 2022-2026',
      'Institutional state: adopted','Acquisition: Link verified'])
      if(!plan.includes(expected))throw new Error('Ashtarak plan output missing '+expected);
    if(plan.includes('Acquisition: Content verified'))throw new Error('Unacquired plan content overstated');
  }
  if(item.area==='ARM:HD002:08000000'){
    const male=overall[0];
    if(!outputs['diagnostic.html'].includes('+2/-2')||male[col('Value')]!=='93221')
      throw new Error('Published Shirak sex discrepancy hidden');
  }
  checks.push({territory:territory.name,territory_id:item.area,indicator,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const wdi=data.observations.find(x=>x.territory_id==='ARM'&&x.indicator_id==='SP.POP.TOTL'&&x.period==='2022');
if(!wdi||wdi.value===2932731)throw new Error('WDI 2022 estimate silently harmonized to census');
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'ARM',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,separate_wdi_2022_value:wdi.value,
  source_quality:'Shirak present-population male/female marz rows differ by +2/-2 from six community sums; direct counts retained.',
  limitations:['All nine chapter archives inventoried, but most numeric columns not semantically adopted',
    'Official dated polygons not acquired or joined','Full Ashtarak plan PDF not acquired locally',
    'Rendered print/PDF, complete 42 scenarios and independent acceptance pending']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory,indicator,value,internal_rows})=>({territory,indicator,value,internal_rows})),null,2));

#!/usr/bin/env node
// Producer-side check of real Bahrain country exports against pinned iGA API cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/bahrain-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='BHR'||data.boundaries?.features?.length!==0)
  throw new Error('Expected Bahrain candidate without joined polygons');
const cases=[
  {area:'BHR',period:'2020',indicator:'CENSUS_POP_TOTAL',value:1501635,children:4,source:'population-by-governorate-nationality-and-sex-census-2020'},
  {area:'BHR:IGA:GOV:CAPITAL',period:'2020',indicator:'CENSUS_POP_TOTAL',value:548345,children:0,source:'population-by-governorate-nationality-and-sex-census-2020'},
  {area:'BHR:IGA:GOV:MUHARRAQ',period:'2020',indicator:'CENSUS_PRIVATE_HOUSEHOLDS',value:43156,children:0,source:'total-households-by-governorate-and-type-of-household-census-2020'},
  {area:'BHR:IGA:GOV:NORTHERN',period:'2020',indicator:'CENSUS_SCHOOL_ENROLLED_3PLUS',value:101102,children:0,source:'school-enrolled-population-3-years-and-above'},
  {area:'BHR:IGA:GOV:SOUTHERN',period:'2020',indicator:'CENSUS_UNEMPLOYED_15PLUS',value:2070,children:0,source:'population-15-years-and-above-by-governorate'},
  {area:'BHR',period:'2025',indicator:'JUNE_POP_TOTAL',value:1603260,children:4,source:'02-population-by-governorate-nationality-sex'},
  {area:'BHR:IGA:GOV:CAPITAL',period:'2025',indicator:'JUNE_POP_TOTAL',value:552684,children:0,source:'02-population-by-governorate-nationality-sex'},
  {area:'BHR:IGA:GOV:MUHARRAQ',period:'2024',indicator:'AREA_KM2_2024',value:74.1,children:0,source:'02-area-by-governorate-2023'},
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
  const territory=data.territories.find(row=>row.id===item.area);
  if(!territory)throw new Error(`Unknown area ${item.area}`);
  const indicator='BHR_IGA_'+item.indicator;
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,item.period),
    'diagnostic.html':diagnosticHtml(data,item.area,item.period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,item.period),
    'planning.html':planningHtml(data,item.area,item.period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,item.period),
  };
  const stem=`BHR-${sha(item.area+indicator+item.period).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID'])
    if(col(name)<0)throw new Error(`Missing CSV column ${name}`);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||
     overall[0][col('Period')]!==item.period||
     !['observed','calculated'].includes(overall[0][col('Status')]))
    throw new Error(`Exported value or period mismatch: ${item.area} ${indicator}`);
  if(within.length!==item.children)throw new Error(`Internal row count mismatch: ${item.area}`);
  if(within.some(row=>row[col('Comparable')]!=='true'))
    throw new Error(`Same-concept governorate cells excluded from comparison: ${item.area}`);
  if(!overall[0][col('Source URL')].includes('data.gov.bh')||
     !overall[0][col('Source locator')].includes(item.source)||
     !overall[0][col('Source locator')].includes('archived record indices'))
    throw new Error(`Missing original iGA API row provenance: ${item.area} ${indicator}`);
  if(item.children){
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker);
    const end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error(`Printable comparison absent: ${item.area}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(match=>match[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(printed)!==JSON.stringify(expected))
      throw new Error(`Printable table differs from all CSV rows: ${item.area}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(territory.name))throw new Error(`Wrong area in ${suffix}: ${item.area}`);
  if(item.indicator==='JUNE_POP_TOTAL'&&
     !outputs['diagnostic.csv'].includes('June')&&!outputs['diagnostic.html'].includes('June'))
    throw new Error('Annual population June label omitted');
  if(item.area==='BHR:IGA:GOV:CAPITAL'){
    const plan=outputs['planning.html'];
    if(!plan.includes('Capital Governorate approved zoning maps')||
       !plan.includes('Acquisition: Body acquired')||!plan.includes('Institutional state: unverified'))
      throw new Error('Historical Capital zoning source or acquisition/status missing');
  }
  checks.push({territory:territory.name,territory_id:item.area,indicator,period:item.period,value:item.value,
    internal_rows:within.length,first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const building=data.indicators.filter(item=>item.id.startsWith('BHR_IGA_')&&item.name.toLowerCase().includes('building'));
if(building.length)throw new Error('Conflicting governorate building indicators were exposed');
const wdi=data.observations.find(row=>row.territory_id==='BHR'&&row.indicator_id==='SP.POP.TOTL'&&row.period==='2020');
if(!wdi||wdi.value===1501635)throw new Error('WDI and census population concepts were harmonized');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',country:'BHR',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  separate_wdi_2020_value:wdi.value,
  source_conflict:'Governorate building-type/ownership totals conflict with building-current-usage; no building indicator adopted.',
  limitations:['27 Census-theme numeric fields remain semantically unassessed',
    'Official codes and compatible governorate polygons not acquired',
    '2017 Capital zoning map current applicability not established',
    'Printed PDF/Word, all 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory,indicator,period,value,internal_rows})=>
  ({territory,indicator,period,value,internal_rows})),null,2));

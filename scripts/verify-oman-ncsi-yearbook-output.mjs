#!/usr/bin/env node
// Compare generated exports with selected visible NCSI Year Book 2026 cells.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/oman-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='OMN'||data.boundaries?.features?.length!==0)throw new Error('Expected unjoined Oman yearbook candidate');
if(data.analysis?.population_context)throw new Error('WDI midyear and NCSI year-end populations silently merged');
const total='OMN_NCSI_REG_TOTAL',omani='OMN_NCSI_REG_OMANI',expat='OMN_NCSI_REG_EXPATRIATE';
const cases=[
  {area:'OMN',indicator:total,year:'2025',value:5359557,children:11,method:'calculated'},
  {area:'OMN',indicator:total,year:'2023',value:5165602,children:11,method:'calculated'},
  {area:'OMN:NCSI25:GOV:MUSCAT',indicator:total,year:'2025',value:1532486,children:6,method:'calculated'},
  {area:'OMN:NCSI25:GOV:MUSCAT:WILAYAT:MUSCAT',indicator:total,year:'2025',value:45167,children:0,method:'calculated'},
  {area:'OMN:NCSI25:GOV:DHOFAR',indicator:total,year:'2025',value:532897,children:10,method:'calculated'},
  {area:'OMN:NCSI25:GOV:DHOFAR:WILAYAT:SALALAH',indicator:total,year:'2025',value:430294,children:0,method:'calculated'},
  {area:'OMN:NCSI25:GOV:ASH-SHARQIYAH-NORTH',indicator:total,year:'2025',value:321045,children:7,method:'calculated'},
  {area:'OMN:NCSI25:GOV:ASH-SHARQIYAH-NORTH:WILAYAT:SINAW',indicator:total,year:'2025',value:37171,children:0,method:'calculated'},
  {area:'OMN:NCSI25:GOV:AL-WUSTA',indicator:total,year:'2025',value:64024,children:4,method:'calculated'},
  {area:'OMN:NCSI25:GOV:AL-WUSTA:WILAYAT:AD-DUQM',indicator:total,year:'2025',value:23566,children:0,method:'calculated'},
  {area:'OMN:NCSI25:GOV:MUSCAT:WILAYAT:BAWSHAR',indicator:omani,year:'2025',value:97713,children:0,method:'source_reported'},
  {area:'OMN:NCSI25:GOV:MUSCAT:WILAYAT:BAWSHAR',indicator:expat,year:'2025',value:347527,children:0,method:'source_reported'},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function parseCsv(input){
  let rows=[],row=[],cell='',quoted=false;
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
  const area=data.territories.find(x=>x.id===item.area);
  if(!area)throw new Error('Missing source area '+item.area);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,item.year),
    'diagnostic.html':diagnosticHtml(data,item.area,item.year),
    'diagnostic.md':diagnosticMarkdown(data,item.area,item.year),
    'planning.html':planningHtml(data,item.area,item.year,'en'),
    'evidence.csv':evidenceCsv(data,item.area,item.year),
  };
  const stem=`OMN-${sha(item.area+item.indicator+item.year).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Source URL','Source locator','Value provenance'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===item.indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!==item.year)
    throw new Error('NCSI source value/period mismatch for '+area.name+' '+item.year);
  if(within.length!==item.children)throw new Error('Wrong internal member count for '+area.name+': '+within.length);
  if(!overall[0][col('Source locator')].includes('Table 7-2')||!overall[0][col('Source URL')].includes('ncsi.gov.om'))
    throw new Error('Official NCSI locator/URL missing for '+area.name);
  if(item.method==='calculated'&&!overall[0][col('Value provenance')].includes('calculated'))
    throw new Error('Calculated Omani + expatriate total was not labelled calculated');
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))throw new Error('Wrong selected area in '+suffix);
  checks.push({area:area.name,area_id:item.area,indicator:item.indicator,period:item.year,value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'OMN',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['Table 7-2 contains year-end registration, not the 2020 eCensus or WDI midyear population',
    'Total is explicitly calculated from two mutually exclusive NCSI nationality columns; Table 6-2 independently matches parent values',
    'Seven provider reference ADM1 shapes are not joined to eleven yearbook governorates',
    'Official codes, current legal planning units, plan bodies, budget and evaluation are unverified',
    'Other yearbook fields, full-table print, 42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,indicator,period,value,internal_rows,total_csv_rows})=>({area,indicator,period,value,internal_rows,total_csv_rows})),null,2));

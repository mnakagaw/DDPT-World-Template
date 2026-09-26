#!/usr/bin/env node
// Verify representative Syrian historical-source values in every supported export.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2] || 'generated/syria-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='SYR')throw new Error('Expected Syrian Arab Republic candidate');
const pop='SYR_CBS_CENSUS_2004_POP';
const housing='SYR_CBS_CENSUS_2004_HOUSEHOLDS';
const cases=[
  {id:'SYR',name:'Syrian Arab Republic',value:17920844,children:14,households:3150358,locator:'national total'},
  {id:'SYR:gbOpen:ADM1:8384693B93490606690779',name:'Homs governorate',value:1529402,children:6,households:271500,locator:'p.1 row 5'},
  {id:'SYR:OCHA2004:ADM2:SY0401',name:'Homs district',value:1035055,children:12,households:null,locator:'p.19 total row'},
  {id:'SYR:OCHA2004:ADM3:SY040102',name:'Kherbet Tin Noor',value:52496,children:0,households:null,locator:'p.19 row 3'},
  {id:'SYR:gbOpen:ADM1:8384693B24866558579919',name:'Damascus governorate',value:1552161,children:1,households:340864,locator:'p.1 row 2'},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function csvRows(input){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=input.charCodeAt(0)===0xfeff?1:0;i<input.length;i++){
    const ch=input[i];
    if(quoted){if(ch==='"'&&input[i+1]==='"'){cell+='"';i++;}else if(ch==='"')quoted=false;else cell+=ch;}
    else if(ch==='"')quoted=true;else if(ch===','){row.push(cell);cell='';}
    else if(ch==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(value=>value!==''))rows.push(row);row=[];cell='';}
    else cell+=ch;
  }
  if(cell||row.length)rows.push([...row,cell]);
  return rows;
}
const out=path.join(project,'evidence','output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const area=data.territories.find(area=>area.id===item.id);
  if(!area)throw new Error(`Missing area ${item.id}`);
  const contents={
    'diagnostic.csv':diagnosticCsv(data,area.id,'latest-available'),
    'diagnostic.html':diagnosticHtml(data,area.id,'latest-available'),
    'diagnostic.md':diagnosticMarkdown(data,area.id,'latest-available'),
    'planning.html':planningHtml(data,area.id,'latest-available','en'),
    'evidence.csv':evidenceCsv(data,area.id,'latest-available'),
  };
  const stem=`SYR-${area.level}-${sha(area.id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(contents))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=csvRows(contents['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const required of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator'])
    if(col(required)<0)throw new Error(`Missing export column: ${required}`);
  const get=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=get('overall',pop), children=get('within_area',pop), housingRow=get('overall',housing);
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!=='2004')
    throw new Error(`${item.name}: population/year differs from CBS PDF`);
  if(children.length!==item.children||children.some(row=>row[col('Value')]===''||row[col('Period')]!=='2004'))
    throw new Error(`${item.name}: incomplete or wrong-year internal population rows`);
  if(!overall[0][col('Source URL')].includes('web.archive.org/web/')||
     !overall[0][col('Source locator')].includes(item.locator))
    throw new Error(`${item.name}: archived CBS PDF and page/row locator missing`);
  if(housingRow.length!==1)throw new Error(`${item.name}: housing indicator row absent`);
  if(item.households===null){
    if(housingRow[0][col('Value')]!==''||housingRow[0][col('Status')]==='observed')
      throw new Error(`${item.name}: unresolved lower-area housing count leaked`);
  }else if(Number(housingRow[0][col('Value')])!==item.households||housingRow[0][col('Period')]!=='2004'){
    throw new Error(`${item.name}: governorate/national household count differs`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!contents[suffix].includes(area.name))throw new Error(`${item.name}: ${suffix} uses wrong area`);
  if(item.id==='SYR'){
    const wdi=get('overall','SP.POP.TOTL');
    if(wdi.length!==1||wdi[0][col('Period')]==='2004'||
       wdi[0][col('Source URL')].includes('web.archive.org'))
      throw new Error('WDI estimate was silently harmonized with CBS census');
  }
  checks.push({area:item.name,id:area.id,population_2004:item.value,households_2004:item.households,
    population_internal_rows:children.length,diagnostic_csv_rows:rows.length,
    first_data_row:rows[0]?.slice(0,17),last_data_row:rows.at(-1)?.slice(0,17),
    hashes:Object.fromEntries(Object.entries(contents).map(([suffix,value])=>[suffix,sha(value)]))});
}
const result={status:'partial_candidate_output_check_not_independent_acceptance',country:'SYR',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['CBS census is from 2004 and cannot represent current resident distribution',
    'Archived OCHA workbook differs in 213 numeric fields; CBS PDFs control adopted values',
    'P-codes and 2017 display shapes are not verified current legal codes/boundaries',
    'Current local planning documents and budgets have not been acquired',
    'Producer checks cover representative areas, not 42 acceptance scenarios or an independent audit']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,population_2004,population_internal_rows,diagnostic_csv_rows})=>
  ({area,population_2004,population_internal_rows,diagnostic_csv_rows})),null,2));

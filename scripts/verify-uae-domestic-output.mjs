#!/usr/bin/env node
// Representative UAE federal-census / Abu Dhabi register export assertions.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/united-arab-emirates-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='ARE')throw new Error('Expected UAE candidate');
const historical='ARE_FCSC_CENSUS_2005_POP',scad='ARE_SCAD_REGISTER_POP';
const cases=[
  {id:'ARE',name:'United Arab Emirates',indicator:historical,year:'2005',value:4106427,children:7,missingScad:true},
  {id:'ARE:gbOpen:ADM1:86790563B99975224300185',name:'Abu Dhabi',indicator:scad,year:'2024',value:4135985,children:3},
  {id:'ARE:SCAD:REGION:ABU_DHABI',name:'Abu Dhabi Region',indicator:scad,year:'2024',value:2823340,children:0,missingHistorical:true},
  {id:'ARE:SCAD:REGION:AL_DHAFRA',name:'Al Dhafra Region',indicator:scad,year:'2023',value:306595,children:0,missingHistorical:true},
  {id:'ARE:gbOpen:ADM1:86790563B34058819691262',name:'Dubai',indicator:historical,year:'2005',value:1321453,children:0,missingScad:true},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function csvRows(input){
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
  const area=data.territories.find(x=>x.id===item.id);
  if(!area)throw new Error('Missing '+item.name);
  const period=item.year;
  const contents={
    'diagnostic.csv':diagnosticCsv(data,item.id,period),
    'diagnostic.html':diagnosticHtml(data,item.id,period),
    'diagnostic.md':diagnosticMarkdown(data,item.id,period),
    'planning.html':planningHtml(data,item.id,period,'en'),
    'evidence.csv':evidenceCsv(data,item.id,period)
  };
  const stem=`ARE-${area.level}-${sha(area.id+period).slice(0,12)}`;
  for(const [suffix,value] of Object.entries(contents))await writeFile(path.join(out,`${stem}-${suffix}`),value);
  const [head,...rows]=csvRows(contents['diagnostic.csv']);
  const col=name=>head.indexOf(name);
  for(const required of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator'])
    if(col(required)<0)throw new Error('Missing export column '+required);
  const select=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=select('overall',item.indicator),children=select('within_area',item.indicator);
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!==item.year)
    throw new Error(item.name+' source value/year mismatch');
  if(children.length!==item.children)throw new Error(item.name+' internal row count mismatch');
  if(item.indicator===historical&&!overall[0][col('Source locator')].includes('PDF p.9'))
    throw new Error(item.name+' FCSC locator absent');
  if(item.indicator===scad&&!overall[0][col('Source URL')].includes('census.scad.gov.ae'))
    throw new Error(item.name+' SCAD URL absent');
  if(item.missingScad){
    const other=select('overall',scad);
    if(other.length!==1||other[0][col('Value')]!==''||other[0][col('Status')]==='observed')
      throw new Error(item.name+' inherited Abu Dhabi register data');
  }
  if(item.missingHistorical){
    const other=select('overall',historical);
    if(other.length!==1||other[0][col('Value')]!==''||other[0][col('Status')]==='observed')
      throw new Error(item.name+' inherited 2005 emirate census data');
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!contents[suffix].includes(area.name))throw new Error(item.name+' wrong area in '+suffix);
  checks.push({area:item.name,period,value:item.value,internal_rows:children.length,total_csv_rows:rows.length,
    first_data_row:rows[0]?.slice(0,17),last_data_row:rows.at(-1)?.slice(0,17),
    hashes:Object.fromEntries(Object.entries(contents).map(([suffix,value])=>[suffix,sha(value)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'ARE',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['Federal 2005 census does not estimate present-day local population',
    'SCAD 2024 registers cover only Abu Dhabi and use a separate method',
    'SCAD region counts are rounded and source codes/boundaries are unverified',
    'No chosen-emirate planning documents have been content-audited',
    '42 scenarios and an independent acceptance review remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,period,value,internal_rows,total_csv_rows})=>({area,period,value,internal_rows,total_csv_rows})),null,2));

#!/usr/bin/env node
// Representative source-value, missingness and full internal-row export checks.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/azerbaijan-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='AZE')throw new Error('Expected Azerbaijan candidate');
if(data.analysis?.population_context)throw new Error('Cross-source population context cannot compare WDI people with SSC rounded thousands');
const current='AZE_SSC_RESIDENT_2026_THOUSANDS';
const census='AZE_SSC_CENSUS_2019_THOUSANDS';
const male='AZE_SSC_MALE_2026_THOUSANDS';
const female='AZE_SSC_FEMALE_2026_THOUSANDS';
const cases=[
  {id:'AZE',indicator:current,period:'2026-01-01',value:10262.4,children:14,sourceRow:5},
  {id:'AZE:SSC24:00000002',indicator:current,period:'2026-01-01',value:2356.2,children:12,sourceRow:7},
  {id:'AZE:SSC24:00100003',indicator:current,period:'2026-01-01',value:309.2,children:0,sourceRow:9},
  {id:'AZE:SSC:ECON:GARABAGH_ECONOMIC_REGION',indicator:current,period:'2026-01-01',value:751.1,children:10,sourceRow:55},
  {id:'AZE:SSC24:61200001',indicator:current,period:'2026-01-01',value:12.2,children:0,sourceRow:60,censusMissing:true},
  {id:'AZE:SSC:ECON:NAKHCHIVAN_ECONOMIC_REGION',indicator:current,period:'2026-01-01',value:472.4,children:8,sourceRow:22},
  {id:'AZE:SSC:ROW:89',indicator:current,period:'2026-01-01',value:228.6,children:0,sourceRow:89,codeHeld:true},
  {id:'AZE',indicator:census,period:'2019',value:9951.4,children:14,sourceRow:5},
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
  if(!area)throw new Error('Missing area '+item.id);
  if(item.codeHeld&&(area.official_code!==null||area.candidate_official_code!=='80200002'))
    throw new Error('Lankaran ambiguous code silently adopted');
  const contents={
    'diagnostic.csv':diagnosticCsv(data,item.id,item.period),
    'diagnostic.html':diagnosticHtml(data,item.id,item.period),
    'diagnostic.md':diagnosticMarkdown(data,item.id,item.period),
    'planning.html':planningHtml(data,item.id,item.period,'en'),
    'evidence.csv':evidenceCsv(data,item.id,item.period),
  };
  const stem=`AZE-${sha(area.id+item.period).slice(0,12)}`;
  for(const [suffix,value] of Object.entries(contents))await writeFile(path.join(out,`${stem}-${suffix}`),value);
  const [head,...rows]=csvRows(contents['diagnostic.csv']);
  const col=name=>head.indexOf(name);
  for(const required of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator'])
    if(col(required)<0)throw new Error('Missing export column '+required);
  const select=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=select('overall',item.indicator),children=select('within_area',item.indicator);
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!==item.period)
    throw new Error(area.name+' source value or period mismatch');
  if(children.length!==item.children)throw new Error(area.name+' internal row count mismatch: '+children.length);
  if(!overall[0][col('Source locator')].includes('Excel row '+item.sourceRow))
    throw new Error(area.name+' source row locator absent');
  if(!overall[0][col('Source URL')].includes('stat.gov.az'))
    throw new Error(area.name+' official source URL absent');
  if(item.censusMissing){
    const missing=select('overall',census);
    if(missing.length!==1||missing[0][col('Value')]!==''||missing[0][col('Status')]==='observed')
      throw new Error('Aghdara 2019 source ellipsis treated as value');
  }
  if(item.id==='AZE'&&item.indicator===current){
    const man=select('overall',male),woman=select('overall',female);
    if(Number(man[0][col('Value')])!==5108.2||Number(woman[0][col('Value')])!==5154.2)
      throw new Error('National male/female source fields differ');
    if(children.at(0)?.[col('Territory')]===undefined)throw new Error('Internal comparison missing first row');
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!contents[suffix].includes(area.name))throw new Error(area.name+' wrong area in '+suffix);
  checks.push({area:area.name,area_id:item.id,period:item.period,value:item.value,
    internal_rows:children.length,total_csv_rows:rows.length,
    first_internal_row:children[0]?.slice(0,17)||null,last_internal_row:children.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(contents).map(([suffix,value])=>[suffix,sha(value)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'AZE',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  limitations:['2019 Aghdara is a source ellipsis, not zero',
    '2024 classification has three unresolved city versus district label conflicts',
    'No official local polygon has been joined to 2026 statistics',
    '2019 census volumes and planning/fiscal documents remain unassessed',
    '42 scenarios and independent acceptance remain open']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,period,value,internal_rows,total_csv_rows})=>({area,period,value,internal_rows,total_csv_rows})),null,2));

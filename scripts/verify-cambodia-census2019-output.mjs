#!/usr/bin/env node
// Compare actual selected-area exports with the archived 2019 NIS source audit.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/cambodia-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/KHM_CENSUS2019_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const normal='KHM_NIS2019_REGULAR_POP',all='KHM_NIS2019_ALL_PERSON_POP';
const tid=code=>code==='KHM'?'KHM':`KHM:NIS2019:${code}`;
const cases=[
  {code:'KHM',all:15552211,normal:15184511},
  {code:'01',all:861883,normal:853252},
  {code:'0102',normal:187286},
  {code:'010201',normal:26418},
  {code:'03',all:899791,normal:887121,mismatch:true},
  {code:'0302',normal:null,mismatch:true},
  {code:'0314',normal:81687},
  {code:'08',all:1201581,normal:1180431,mismatch:true},
  {code:'0801',normal:null,mismatch:true},
  {code:'12',all:2281951,normal:2189460},
  {code:'1201',normal:70772},
  {code:'14',all:1057720,normal:1049361,mismatch:true},
  {code:'22',all:276038,normal:268638,mismatch:true},
  {code:'2202',normal:null,mismatch:true},
];
if(data.country.id!=='KHM'||data.territories.length!==1874||data.boundaries?.features?.length!==0)
  fail('Expected 1,874 2019 reporting territories and no unsupported polygon join');
const originalP=new Map(audit.p_table_rows.map(row=>[row.code,row]));
const originalProvinces=new Map(audit.p_table_province_subtotals
  .filter(row=>row.label==='Total').map(row=>[row.province_code,row]));
const originalAll=new Map(audit.table_2_1_1_all_person_rows.map((row,i)=>[
  i===0?'KHM':audit.p_table_province_heads[i-1].code,row]));
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
  const id=tid(item.code),area=data.territories.find(row=>row.id===id);
  if(!area)fail(`Area absent: ${id}`);
  if(item.code!=='KHM'){
    const original=item.code.length===2?originalProvinces.get(item.code):originalP.get(item.code);
    if(!original||item.normal!==null&&original.normal_household_population!==item.normal)
      fail(`P-table source row changed: ${id}`);
  }
  if(item.all!=null && originalAll.get(item.code)?.all_person_population!==item.all)
    fail(`All-person Table 2.1.1 source row changed: ${id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,id,'2019'),
    'diagnostic.html':diagnosticHtml(data,id,'2019'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2019'),
    'planning.html':planningHtml(data,id,'2019','en'),
    'evidence.csv':evidenceCsv(data,id,'2019'),
  };
  const stem=`KHM-${sha(id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const subset=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const normalOverall=subset('overall',normal),allOverall=subset('overall',all);
  if(normalOverall.length!==1||allOverall.length!==1)fail(`Missing overall indicator rows for ${id}`);
  if(item.normal==null){
    if(normalOverall[0][col('Status')]==='observed'||normalOverall[0][col('Value')]!=='')
      fail(`Conflicting printed district value was adopted: ${id}`);
  }else if(Number(normalOverall[0][col('Value')])!==item.normal||
           normalOverall[0][col('Status')]!=='observed'||
           !normalOverall[0][col('Source locator')].includes(item.code==='KHM'?'Appendix':'P-'))
    fail(`Normal-household value or locator differs for ${id}`);
  if(item.all==null){
    if(allOverall[0][col('Status')]==='observed'||allOverall[0][col('Value')]!=='')
      fail(`All-person province value was inherited by a lower area: ${id}`);
  }else if(Number(allOverall[0][col('Value')])!==item.all||
           !allOverall[0][col('Source locator')].includes('Table 2.1.1'))
    fail(`All-person value or locator differs for ${id}`);
  for(const row of [normalOverall[0],allOverall[0]])
    if(row[col('Status')]==='observed'&&
       !row[col('Source URL')].startsWith('https://nis.gov.kh/nis/Census2019/'))
      fail(`NIS source URL missing from exported row ${id}`);
  const childIds=data.territories.filter(row=>row.parent_id===id).map(row=>row.id);
  const within=subset('within_area',normal);
  if(JSON.stringify(within.map(row=>row[col('Territory ID')]))!==JSON.stringify(childIds))
    fail(`Full direct-child roster differs in export: ${id}`);
  for(const row of within){
    const childCode=row[col('Territory ID')].split(':').at(-1);
    const source=childCode.length===2?originalProvinces.get(childCode):originalP.get(childCode);
    if(!source)fail(`Child source row absent: ${childCode}`);
    const invalid=childCode==='0302'||childCode==='0801'||childCode==='2202';
    if(invalid){
      if(row[col('Status')]==='observed')fail(`Invalid child direct value included: ${childCode}`);
    }else if(Number(row[col('Value')])!==source.normal_household_population)
      fail(`Child direct value differs: ${childCode}`);
  }
  if(childIds.length){
    const marker=`<section class="internal-comparison" data-internal-comparison="${normal}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${id}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(childIds))
      fail(`Printable comparison omitted or reordered rows ${id}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selected area in ${suffix}: ${id}`);
  const nationalReference=outputs['planning.html'].includes('Capital/Provincial plan guideline catalogue');
  if(nationalReference!==(id==='KHM'))fail(`National planning reference leaks or is absent: ${id}`);
  if(item.mismatch&&!outputs['diagnostic.md'].includes('conflicts with the parent'))
    fail(`Known parent-child conflict is not explained in export: ${id}`);
  checks.push({territory_id:id,all_person:item.all??null,normal_household:item.normal??null,
    internal_rows:within.length,first_internal_row:childIds[0]||null,last_internal_row:childIds.at(-1)||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([name,value])=>[name,sha(value)]))});
}
await writeFile(path.join(project,'evidence/OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['P table source rows and parent-child conflicts withheld or disclosed',
    'Normal/regular-household population differs from final all-person population',
    'Official 2019-compatible polygons and local plan bodies not acquired',
    'Applicable 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,all_person,normal_household,internal_rows})=>
  ({territory_id,all_person,normal_household,internal_rows})),null,2));

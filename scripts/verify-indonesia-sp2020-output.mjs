#!/usr/bin/env node
// Compare original Table 1 rows with actual generated diagnostic/planning exports.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/indonesia-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/IDN_SP2020_TABLE1_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const iid=field=>`IDN_SP2020_${field.toUpperCase()}`;
const tid=code=>`IDN:SP2020:${code}`;
if(data.country.id!=='IDN'||data.territories.length!==549||data.boundaries?.features?.length!==0)
  fail('Expected 549 BPS reporting units and zero unverified polygon joins');
const cases=[
  {code:null,national:true,expected:270203917,children:34},
  {code:'11',expected:5274871,children:23},
  {code:'31',expected:10562088,children:6},
  {code:'32',expected:48274162,children:27},
  {code:'3201',expected:5427068,children:0},
  {code:'3271',expected:1043070,children:0},
  {code:'94',expected:4303707,children:29},
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
  const areaId=item.national?'IDN':tid(item.code);
  const area=data.territories.find(row=>row.id===areaId);
  if(!area)fail(`Missing territory ${areaId}`);
  const sourceRow=item.national?audit.country.at(-1):
    item.code.length===2?audit.country.find(row=>row.code===item.code):
    audit.provinces.find(p=>p.parent_code===item.code.slice(0,2))?.rows.find(row=>row.code===item.code);
  if(sourceRow?.fields.population!==item.expected)fail(`Unexpected original population ${areaId}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,areaId,'2020'),
    'diagnostic.html':diagnosticHtml(data,areaId,'2020'),
    'diagnostic.md':diagnosticMarkdown(data,areaId,'2020'),
    'planning.html':planningHtml(data,areaId,'2020','en'),
    'evidence.csv':evidenceCsv(data,areaId,'2020'),
  };
  const stem=`IDN-${sha(areaId).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=(scope,id)=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===id);
  const overall=matching('overall',iid('population')),
        within=matching('within_area',iid('population'));
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.expected||
     overall[0][col('Period')]!=='2020'||overall[0][col('Status')]!=='observed')
    fail(`Population value, period or status mismatch ${areaId}`);
  if(!overall[0][col('Source URL')].startsWith('https://sensus.bps.go.id/topik/tabular/sp2020/1')||
     !overall[0][col('Source locator')].includes('BPS Table 1'))
    fail(`Official Table 1 locator missing ${areaId}`);
  if(within.length!==item.children)fail(`Child count mismatch ${areaId}: ${within.length}`);
  if(item.children){
    const expectedRows=item.national?audit.country.slice(0,-1):
      audit.provinces.find(p=>p.parent_code===item.code).rows.slice(0,-1);
    const expectedIds=expectedRows.map(row=>tid(row.code));
    const actual=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(actual)!==JSON.stringify(expectedIds))fail(`Full child ID order mismatch ${areaId}`);
    if(within.some(row=>row[col('Comparable')]!=='true'))fail(`Source-matched comparison excluded ${areaId}`);
    for(const [row,original] of within.map((row,i)=>[row,expectedRows[i]]))
      if(Number(row[col('Value')])!==original.fields.population)fail(`Original child value differs ${areaId} ${original.code}`);
    if(within.reduce((sum,row)=>sum+Number(row[col('Value')]),0)!==item.expected)
      fail(`Child population sum mismatch ${areaId}`);
    const marker=`<section class="internal-comparison" data-internal-comparison="${iid('population')}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${areaId}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(expectedIds))fail(`Printable comparison drops rows ${areaId}`);
  }
  for(const field of ['male','female']){
    const record=matching('overall',iid(field));
    if(record.length!==1||Number(record[0][col('Value')])!==sourceRow.fields[field])
      fail(`Sex count mismatch ${areaId} ${field}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selected area in ${suffix}: ${areaId}`);
  const hasLaw=outputs['planning.html'].includes('Permendagri 86/2017 — regional development planning');
  if(hasLaw!==Boolean(item.national))fail(`National legal reference leaked or absent ${areaId}`);
  if(outputs['planning.html'].includes('RPJMD Provinsi Jawa Barat 2025-2029.pdf'))
    fail(`Unacquired Jawa Barat RPJMD body represented as a document ${areaId}`);
  checks.push({territory_id:areaId,population:item.expected,internal_rows:within.length,
    first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,law_reference:hasLaw,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([key,value])=>[key,sha(value)]))});
}
if(data.territories.find(t=>t.id===tid('3201'))?.name!==
   data.territories.find(t=>t.id===tid('3271'))?.name)
  fail('Bogor duplicate-name comparison fixture changed');
if(data.documents.some(d=>d.id==='idn-jabar-rpjmd-2025-2029'))
  fail('Unacquired Jawa Barat RPJMD attached as a local plan');
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['Only BPS SP2020 Table 1 male, female and total direct counts adopted',
    'Other SP2020 tables and all other census themes priority_unassessed',
    'BPS 2020 source codes are not current Kemendagri code or legal-boundary matches',
    'Jawa Barat RPJMD body, matching budgets/evaluation, all 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,population,internal_rows,law_reference})=>
  ({territory_id,population,internal_rows,law_reference})),null,2));

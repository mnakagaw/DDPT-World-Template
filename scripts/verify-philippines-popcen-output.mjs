#!/usr/bin/env node
// Check actual country exports against PSA 2024 POPCEN rows and scoped documents.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/philippines-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/PHL_POPCEN_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const indicator='PHL_POPCEN2024_POPULATION';
const tid=code=>code===null?'PHL:POPCEN:SGA-2024':`PHL:PSGC:${code}`;
const cases=[
  {id:'PHL',expected:112729484,children:18},
  {id:tid('1300000000'),expected:14001751,children:17},
  {id:tid('1381300000'),expected:3084270,children:0,qc:true},
  {id:tid('1380300000'),expected:309770,children:0},
  {id:tid('1381500000'),expected:1308085,children:0},
  {id:tid('1800000000'),expected:4904944,children:4},
  {id:tid('1900000000'),expected:5691583,children:7},
  {id:tid('1908700000'),expected:1124811,children:13},
  {id:tid('1906600000'),expected:1146097,children:19},
  {id:tid(null),expected:214703,children:8},
];
if(data.country.id!=='PHL'||data.territories.length!==1744||data.boundaries?.features?.length!==0)
  fail('Expected 1,744 2024 reporting territories and no unsupported polygon join');
const originalById=new Map(audit.table_b_rows.map(row=>[tid(row.code),row]));
const expectedByParent=new Map();
for(const row of audit.table_b_rows){
  const list=expectedByParent.get(row.parent_id)||[];
  list.push(row);expectedByParent.set(row.parent_id,list);
}
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
  const area=data.territories.find(row=>row.id===item.id);
  const original=item.id==='PHL'?null:originalById.get(item.id);
  if(!area||item.id!=='PHL'&&original?.population['2024']!==item.expected)
    fail(`Original reporting row missing or changed ${item.id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.id,'2024'),
    'diagnostic.html':diagnosticHtml(data,item.id,'2024'),
    'diagnostic.md':diagnosticMarkdown(data,item.id,'2024'),
    'planning.html':planningHtml(data,item.id,'2024','en'),
    'evidence.csv':evidenceCsv(data,item.id,'2024'),
  };
  const stem=`PHL-${sha(item.id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(outputDir,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Territory ID','Comparable'])
    if(col(key)<0)fail(`Missing CSV column ${key}`);
  const matching=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=matching('overall'),within=matching('within_area');
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.expected||
     overall[0][col('Period')]!=='2024'||overall[0][col('Status')]!=='observed')
    fail(`Observed 2024 population differs from PSA original ${item.id}`);
  if(!overall[0][col('Source URL')].startsWith('https://psa.gov.ph/system/files/phcd/')||
     !overall[0][col('Source locator')].includes(item.id==='PHL'?'Table A':'Table B'))
    fail(`PSA source locator absent ${item.id}`);
  if(within.length!==item.children)fail(`Child count differs ${item.id}: ${within.length}`);
  if(item.children){
    const expectedRows=expectedByParent.get(item.id)||[];
    const expectedIds=expectedRows.map(row=>tid(row.code));
    const actual=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(actual)!==JSON.stringify(expectedIds))
      fail(`Full child order or count differs ${item.id}`);
    if(within.some(row=>row[col('Comparable')]!=='true'))
      fail(`Direct same-year comparison unexpectedly excluded ${item.id}`);
    for(let i=0;i<within.length;i++)
      if(Number(within[i][col('Value')])!==expectedRows[i].population['2024'])
        fail(`Child value differs from PSA original ${item.id}/${expectedIds[i]}`);
    const sum=within.reduce((n,row)=>n+Number(row[col('Value')]),0);
    if(sum!==item.expected-(item.id==='PHL'?1708:0))
      fail(`Observed parent and child sum differ ${item.id}`);
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker);
    const end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)fail(`Printable comparison absent ${item.id}`);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
    if(JSON.stringify(printed)!==JSON.stringify(expectedIds))
      fail(`Printable comparison omitted or reordered rows ${item.id}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Wrong selection in ${suffix}: ${item.id}`);
  const qcDocuments=['Quezon City Comprehensive Development Plan 2026','Quezon City Local Development Investment Program 2027',
    'Quezon City FY2026 Annual Investment Program adoption','Quezon City calendar 2026 annual budget ordinance'];
  const visibleQc=qcDocuments.filter(title=>outputs['planning.html'].includes(title));
  if(visibleQc.length!==(item.qc?4:0))fail(`Quezon City documents leaked or absent ${item.id}`);
  const hasNationalLaw=outputs['planning.html'].includes('Republic Act No. 7160, Local Government Code');
  if(hasNationalLaw!==(item.id==='PHL'))fail(`National legal reference leaked or absent ${item.id}`);
  checks.push({territory_id:item.id,population:item.expected,internal_rows:within.length,
    first_internal_row:within[0]?.[col('Territory ID')]||null,
    last_internal_row:within.at(-1)?.[col('Territory ID')]||null,
    qc_documents:visibleQc.length,national_law_reference:hasNationalLaw,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([name,value])=>[name,sha(value)]))});
}
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['Table C barangay and other census fields priority_unassessed',
    '2024-compatible official polygons unverified',
    'Quezon City selected planning bodies only; full contents and fiscal actuals unassessed',
    'Applicable 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,population,internal_rows,qc_documents})=>
  ({territory_id,population,internal_rows,qc_documents})),null,2));

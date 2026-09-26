#!/usr/bin/env node
// Check representative source values and complete diagnostic exports for the Jordan candidate.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2] || 'generated/jordan-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='JOR')throw new Error('Expected a Jordan country dataset');
const indicator='JOR_DOS_EST_2025_POP';
const cases=[
  {name:'Jordan',level:'national',value:11937000,children:12,sourceCell:'الملخص !D122'},
  {name:'Amman',level:'adm1',value:5004600,children:9},
  {name:'Jizah District',level:'adm2',value:147365,children:2},
  {name:'Jizah Sub-District',level:'adm3',value:130085,children:0},
  {name:'Aqaba',level:'adm1',value:250900,children:0},
];
const hash=value=>createHash('sha256').update(value).digest('hex');
function records(input){
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
  const matches=data.territories.filter(area=>area.level===item.level&&area.name===item.name);
  if(matches.length!==1)throw new Error(`Ambiguous area: ${item.name}: ${matches.length}`);
  const area=matches[0];
  const contents={
    'diagnostic.csv':diagnosticCsv(data,area.id,'latest-available'),
    'diagnostic.html':diagnosticHtml(data,area.id,'latest-available'),
    'diagnostic.md':diagnosticMarkdown(data,area.id,'latest-available'),
    'planning.html':planningHtml(data,area.id,'latest-available','en'),
    'evidence.csv':evidenceCsv(data,area.id,'latest-available'),
  };
  const stem=`JOR-${item.level}-${hash(area.id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(contents))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [head,...rows]=records(contents['diagnostic.csv']);
  const col=name=>head.indexOf(name);
  for(const required of ['Record scope','Indicator ID','Value','Period','Source URL','Source locator'])
    if(col(required)<0)throw new Error(`Missing diagnostic column: ${required}`);
  const overall=rows.filter(row=>row[col('Record scope')]==='overall'&&row[col('Indicator ID')]===indicator);
  const children=rows.filter(row=>row[col('Record scope')]==='within_area'&&row[col('Indicator ID')]===indicator);
  if(overall.length!==1||Number(overall[0][col('Value')])!==item.value||overall[0][col('Period')]!=='2025')
    throw new Error(`${item.name}: overall output differs from the source`);
  if(children.length!==item.children)throw new Error(`${item.name}: ${children.length} child rows; expected ${item.children}`);
  if(!overall[0][col('Source URL')].includes('dosweb.dos.gov.jo/'))throw new Error(`${item.name}: no DoS source URL`);
  if(!overall[0][col('Source locator')])throw new Error(`${item.name}: no source cell locator`);
  if(item.sourceCell&&!overall[0].some(value=>value.includes(item.sourceCell)))throw new Error(`${item.name}: source cell missing`);
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!contents[suffix].includes(item.name))throw new Error(`${item.name}: ${suffix} has wrong area`);
  if(item.name==='Aqaba'&&children.length!==0)throw new Error('Aqaba lower rows were silently adopted');
  checks.push({area:item.name,territory_id:area.id,level:item.level,population:item.value,
               internal_population_rows:children.length,all_diagnostic_csv_rows:rows.length,
               first_data_row:rows[0]?.slice(0,17),last_data_row:rows.at(-1)?.slice(0,17),
               hashes:Object.fromEntries(Object.entries(contents).map(([suffix,value])=>[suffix,hash(value)]))});
}
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'JOR',
             checked_at:new Date().toISOString(),dataset_sha256:hash(bytes),checks,
             limitations:['Official administrative codes and current legal boundary equivalence remain unresolved',
                          'No verified country-specific planning document has been adopted',
                          'Detailed locality and municipality sheets and thematic census tables remain unassessed',
                          'Local browser checks cover representative areas, not all 42 acceptance scenarios']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({area,population,internal_population_rows,all_diagnostic_csv_rows})=>
  ({area,population,internal_population_rows,all_diagnostic_csv_rows})),null,2));

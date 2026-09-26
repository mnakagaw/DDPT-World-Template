#!/usr/bin/env node
// Save and inspect representative India output files from the app's output generators.
// This checks bytes on disk; it does not assert that a browser click downloaded a file.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve('generated/india-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const sha=content=>createHash('sha256').update(content).digest('hex');
const datasetHash=sha(bytes);
const census='IND_PCA_TOT_P';
if(datasetHash!=='81933e13f0636fdfa562d0b02e4c2cae8e49e3deb0a01e8295a51828361b2425')throw new Error(`Unreviewed India dataset: ${datasetHash}`);
if(data.country.id!=='IND')throw new Error('Wrong country');

function csvRows(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=text.charCodeAt(0)===0xfeff?1:0;i<text.length;i++){
    const c=text[i];
    if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}
    else if(c==='"')quoted=true;else if(c===','){row.push(cell);cell='';}
    else if(c==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(value=>value!==''))rows.push(row);row=[];cell='';}
    else cell+=c;
  }
  if(cell||row.length)rows.push([...row,cell]);
  return rows;
}

const cases=[
  {id:'IND',stem:'india-national',value:1210854977,children:35,comparable:35},
  {id:'IND:census2011:state:16',stem:'tripura-2011-state',value:3673917,children:4,comparable:4},
  {id:'IND:census2011:district:289',stem:'west-tripura-2011-district',value:1725739,children:17,comparable:0},
  {id:'IND:census2011:subdistrict:16-289-99999',stem:'west-tripura-unassigned-residual',value:485036,children:0,comparable:0},
];
const out=path.join(project,'evidence','output-verification',datasetHash.slice(0,12));
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const area=data.territories.find(row=>row.id===item.id);
  if(!area)throw new Error(`Area missing: ${item.id}`);
  const generated={
    'diagnostic.csv':diagnosticCsv(data,item.id,'2011'),
    'diagnostic.html':diagnosticHtml(data,item.id,'2011'),
    'planning.html':planningHtml(data,item.id,'2011','en'),
    'evidence.csv':evidenceCsv(data,item.id,'2011'),
  };
  const saved={};
  for(const [suffix,content] of Object.entries(generated)){
    const file=path.join(out,`${item.stem}-${suffix}`);
    await writeFile(file,content,{flag:'wx'});
    const disk=await readFile(file);
    if(sha(disk)!==sha(content))throw new Error(`Saved bytes changed: ${file}`);
    saved[suffix]={path:path.relative(project,file).replaceAll('\\','/'),bytes:disk.length,sha256:sha(disk)};
  }
  const rows=csvRows((await readFile(path.join(out,`${item.stem}-diagnostic.csv`))).toString('utf8'));
  const head=rows[0],records=rows.slice(1),index=name=>head.indexOf(name),cell=(row,name)=>row[index(name)];
  for(const name of ['Record scope','Territory ID','Type','Official code','Indicator ID','Period','Value','Status','Comparable','Source URL'])
    if(index(name)<0)throw new Error(`Missing output column ${name}`);
  const overall=records.filter(row=>cell(row,'Record scope')==='overall'&&cell(row,'Indicator ID')===census);
  const members=records.filter(row=>cell(row,'Record scope')==='within_area'&&cell(row,'Indicator ID')===census);
  const children=data.territories.filter(row=>row.parent_id===item.id);
  if(overall.length!==1||cell(overall[0],'Territory ID')!==item.id||Number(cell(overall[0],'Value'))!==item.value||cell(overall[0],'Period')!=='2011')
    throw new Error(`Direct Census value mismatch for ${item.id}`);
  if(!cell(overall[0],'Source URL').startsWith('https://censusindia.gov.in/'))throw new Error(`Census source missing for ${item.id}`);
  if(members.length!==item.children||children.length!==item.children||new Set(members.map(row=>cell(row,'Territory ID'))).size!==item.children)
    throw new Error(`Incomplete child output for ${item.id}`);
  const comparable=members.filter(row=>cell(row,'Comparable')==='true').length;
  if(comparable!==item.comparable)throw new Error(`Unexpected comparison admissibility for ${item.id}: ${comparable}`);
  if(item.id==='IND:census2011:district:289'){
    const residual=members.find(row=>cell(row,'Territory ID')==='IND:census2011:subdistrict:16-289-99999');
    if(!residual||cell(residual,'Official code')!=='99999'||cell(residual,'Type')!=='2011 Census unassigned district residual'||Number(cell(residual,'Value'))!==485036||cell(residual,'Comparable')!=='false')
      throw new Error('West Tripura residual was hidden or treated as an ordinary comparable unit');
    if(!generated['diagnostic.html'].includes('Area not under any Sub-district'))throw new Error('HTML omits residual');
  }
  const wdi=records.find(row=>cell(row,'Record scope')==='overall'&&cell(row,'Indicator ID')==='SP.POP.TOTL');
  if(!wdi)throw new Error(`WDI context row missing: ${item.id}`);
  if(item.id==='IND'){
    if(Number(cell(wdi,'Value'))!==1261224954)throw new Error('WDI national population mismatch');
  }else if(cell(wdi,'Value')!==''||cell(wdi,'Status')==='observed'){
    throw new Error(`National WDI value leaked into local area ${item.id}`);
  }
  if(!generated['diagnostic.html'].includes(area.name.trim())||!generated['planning.html'].includes(area.name.trim()))
    throw new Error(`HTML selected-area mismatch: ${item.id}`);
  checks.push({area_id:item.id,area_name:area.name,overall_value:item.value,period:'2011',indicator_id:census,
    member_rows:members.length,comparable_member_rows:comparable,csv_rows:records.length,
    first_data_row:records[0]?.slice(0,17),last_data_row:records.at(-1)?.slice(0,17),saved});
}
const receipt=path.join(project,'evidence',`IND_OUTPUT_VERIFICATION_${datasetHash.slice(0,12)}.json`);
await writeFile(receipt,JSON.stringify({status:'partial_saved_generator_output_check',dataset_sha256:datasetHash,checked_at:new Date().toISOString(),checks,
  limitations:['Saved files are generated by the same functions used by the browser app; the browser download event and user-visible saved file remain unverified.',
    'No physical print or complete 42-scenario acceptance.',
    '2011 Census geography is not crosswalked to current LGD legal authorities.']},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({receipt:path.relative(project,receipt).replaceAll('\\','/'),dataset_sha256:datasetHash,
  checks:checks.map(({area_id,overall_value,member_rows,comparable_member_rows,csv_rows})=>({area_id,overall_value,member_rows,comparable_member_rows,csv_rows}))},null,2));

#!/usr/bin/env node
// Compare actual exports with the independently read DOP 2024 workbook/PDF audit.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/myanmar-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/MMR_CENSUS2024_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const prefix='MMR_DOP24_';
if(data.country.id!=='MMR'||data.territories.length!==16||data.boundaries?.features?.length!==0||
   audit.areas.length!==16||audit.adopted_observations!==240)fail('DOP source scope or geometry changed');
const areaById=new Map(audit.areas.map(a=>[a.name==='Myanmar'?'MMR':`MMR:DOP2024:A1:R${a.source_row}`,a]));
const fields=['conventional_both','conventional_male','conventional_female',
  'institution_both','institution_male','institution_female',
  'estimated_both','estimated_male','estimated_female',
  'total_both','total_male','total_female'];
const fieldsById=new Map(fields.map((f,i)=>[`${prefix}${f.toUpperCase()}`,{field:f,col:String.fromCharCode(66+i)}]));
for(const [key,property] of [['ENUMERATED_BOTH','enumerated_both'],
  ['ENUMERATED_PCT','enumerated_pct'],['ESTIMATED_PCT','estimated_pct']])
  fieldsById.set(prefix+key,{property});
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
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const cases=['MMR','MMR:DOP2024:A1:R17','MMR:DOP2024:A1:R26',
  'MMR:DOP2024:A1:R41','MMR:DOP2024:A1:R50'];
const checks=[];
for(const id of cases){
  const source=areaById.get(id),area=data.territories.find(x=>x.id===id);
  if(!source||!area)fail(`Missing selected source row ${id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,id,'2024'),
    'diagnostic.html':diagnosticHtml(data,id,'2024'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2024'),
    'planning.html':planningHtml(data,id,'2024','en'),
    'evidence.csv':evidenceCsv(data,id,'2024'),
  };
  const stem=`MMR-${sha(id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL',
    'Source locator','Territory ID','Value provenance'])if(col(key)<0)fail(`Missing CSV column ${key}`);
  const subset=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&
    row[col('Indicator ID')]===indicator);
  for(const [indicator,info] of fieldsById){
    const original=info.field?source.fields[info.field]:source[info.property];
    const selected=subset('overall',indicator);
    const derivedZero=info.field?.startsWith('estimated_')&&source.source_dash_is_zero;
    if(selected.length!==1||selected[0][col('Status')]!==(derivedZero?'calculated':'observed')||
       Number(selected[0][col('Value')])!==original||selected[0][col('Period')]!=='2024'||
       !selected[0][col('Source URL')].includes('dop.gov.mm/')||
       selected[0][col('Territory ID')]!==id)
      fail(`Selected export differs from DOP source: ${id}/${indicator}`);
    const locator=selected[0][col('Source locator')];
    if(info.field&& !locator.startsWith(`Table A-1!${info.col}${source.source_row}`))
      fail(`Workbook locator differs: ${id}/${indicator}`);
    if(!info.field&& !locator.includes('Table'))fail(`Report locator absent: ${id}/${indicator}`);
    if(derivedZero&&
       (selected[0][col('Value provenance')]!=='calculated'||!locator.includes('source dash')))
      fail(`Source dash converted without explicit provenance: ${id}/${indicator}`);
  }
  if(id==='MMR'){
    for(const indicator of fieldsById.keys()){
      const compared=subset('within_area',indicator);
      if(compared.length!==15)fail(`National comparison has ${compared.length} rows for ${indicator}`);
      for(const row of compared){
        const original=areaById.get(row[col('Territory ID')]);
        if(!original)fail(`Comparison row not on DOP roster: ${indicator}`);
        const info=fieldsById.get(indicator),expected=info.field?original.fields[info.field]:original[info.property];
        if(Number(row[col('Value')])!==expected)fail(`Comparison differs from source: ${indicator}/${original.name}`);
      }
    }
    for(const original of audit.areas.slice(1)){
      if(!outputs['diagnostic.html'].includes(original.name))fail(`Print HTML hides ${original.name}`);
    }
  }
  for(const [suffix,content] of Object.entries(outputs)){
    if(content.includes('undefined')||content.includes('NaN'))fail(`${suffix} contains invalid literal: ${id}`);
    if(suffix.endsWith('.html')&&!content.includes(area.name))fail(`${suffix} lost selected area: ${id}`);
  }
  checks.push({id,name:area.name,total_population:source.fields.total_both,
    enumerated_share:source.enumerated_pct,estimated_share:source.estimated_pct,
    files:Object.keys(outputs)});
}
const report={dataset_sha256:sha(bytes),checked_cases:checks,
  national_comparison_rows:15*fieldsById.size,
  source_table:'DOP demographic appendix Table A-1 and Union Report Tables 2.2/3.1',
  independent_acceptance:false};
await writeFile(path.join(project,'evidence/MMR_OUTPUT_VERIFICATION.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({checked_cases:checks.length,
  national_comparison_rows:report.national_comparison_rows,
  dataset_sha256:report.dataset_sha256}));

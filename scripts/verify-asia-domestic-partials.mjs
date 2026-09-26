#!/usr/bin/env node
// Verify representative source values and complete internal tables in actual exports.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

function records(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=text.charCodeAt(0)===0xfeff?1:0;i<text.length;i++){
    const c=text[i];
    if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}
    else if(c==='"')quoted=true;else if(c===','){row.push(cell);cell='';}
    else if(c==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(x=>x!==''))rows.push(row);row=[];cell='';}
    else cell+=c;
  }
  if(cell||row.length)rows.push([...row,cell]);
  return rows;
}
const hash=value=>createHash('sha256').update(value).digest('hex');
const cases=[
  {path:'generated/iran-areadata-20260926',country:'IRN',indicator:'IRN_CENSUS_2016_POP_TOTAL',period:'2016',
   areas:[{level:'national',name:'Iran, Islamic Rep.',value:79926270,children:31},
          {level:'adm1',name:'Tehran',value:13267637,children:16},
          {level:'adm2',name:'Eslamshahr',value:548620,children:0}]},
  {path:'generated/turkey-areadata-20260926',country:'TUR',indicator:'TUR_ADNKS_2025_POP_TOTAL',period:'2025',
   areas:[{level:'national',name:'Turkiye',value:86092168,children:81},
          {level:'adm1',name:'İstanbul',value:15754053,children:39},
          {level:'adm2',name:'ESENYURT',value:1003905,children:0}]},
  {path:'generated/iraq-areadata-20260926',country:'IRQ',indicator:'IRQ_CENSUS_2024_POP_TABULATED',period:'2024',
   areas:[{level:'national',name:'Iraq',value:46118793,children:18},
          {level:'adm1',name:'Baghdad',value:9780429,children:0},
          {level:'adm1',name:'Al-Basrah',value:3664168,children:0}]},
  {path:'generated/saudi-arabia-areadata-20260926',country:'SAU',indicator:'SAU_CENSUS_2022_POP_REGION',period:'2022',
   areas:[{level:'national',name:'Saudi Arabia',value:32175224,children:13},
          {level:'adm1',name:'Riyadh Region',value:8591748,children:0},
          {level:'adm1',name:'Makkah Region',value:8021463,children:0}]},
];
const checks=[];
for(const item of cases){
  const project=path.resolve(item.path),bytes=await readFile(path.join(project,'data/dashboard.json'));
  const data=JSON.parse(bytes.toString('utf8'));
  if(data.country.id!==item.country)throw new Error(`${item.country}: wrong dataset`);
  const out=path.join(project,'evidence','output-verification');await mkdir(out,{recursive:true});
  for(const spec of item.areas){
    const candidates=data.territories.filter(area=>area.level===spec.level&&area.name===spec.name);
    if(candidates.length!==1)throw new Error(`${item.country}: area ambiguous: ${spec.name}: ${candidates.length}`);
    const area=candidates[0],stem=`${item.country}-${spec.level}-${hash(area.id).slice(0,12)}`;
    const csv=diagnosticCsv(data,area.id,'latest-available');
    const html=diagnosticHtml(data,area.id,'latest-available');
    const plan=planningHtml(data,area.id,'latest-available','en');
    const evidence=evidenceCsv(data,area.id,'latest-available');
    for(const [suffix,content] of [['diagnostic.csv',csv],['diagnostic.html',html],['planning.html',plan],['evidence.csv',evidence]])
      await writeFile(path.join(out,`${stem}-${suffix}`),content);
    const lines=records(csv),head=lines[0],values=lines.slice(1),col=name=>head.indexOf(name);
    const overall=values.filter(row=>row[col('Record scope')]==='overall'&&row[col('Indicator ID')]===item.indicator);
    const children=values.filter(row=>row[col('Record scope')]==='within_area'&&row[col('Indicator ID')]===item.indicator);
    if(overall.length!==1||Number(overall[0][col('Value')])!==spec.value||overall[0][col('Period')]!==item.period)
      throw new Error(`${item.country}/${spec.name}: overall export mismatch`);
    if(children.length!==spec.children)throw new Error(`${item.country}/${spec.name}: ${children.length} child rows, expected ${spec.children}`);
    if(overall[0][col('Source URL')].startsWith('http')===false)throw new Error(`${item.country}/${spec.name}: no source URL`);
    if(!html.includes(spec.name)||!plan.includes(spec.name)||!evidence.includes(spec.name))
      throw new Error(`${item.country}/${spec.name}: export area mismatch`);
    checks.push({country:item.country,area:spec.name,level:spec.level,territory_id:area.id,
                 selected_indicator:item.indicator,selected_period:item.period,overall_value:spec.value,
                 internal_rows:children.length,csv_rows:values.length,
                 first_data_row:values[0]?.slice(0,17),last_data_row:values.at(-1)?.slice(0,17),
                 diagnostic_csv_sha256:hash(csv),diagnostic_html_sha256:hash(html),
                 planning_html_sha256:hash(plan),evidence_csv_sha256:hash(evidence),
                 dataset_sha256:hash(bytes)});
  }
  await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),
                  JSON.stringify({status:'partial_candidate_output_check',country:item.country,
                                  checked_at:new Date().toISOString(),checks:checks.filter(x=>x.country===item.country),
                                  limitations:['No official planning document adopted','Not an independent acceptance audit']},null,2)+'\n');
}
console.log(JSON.stringify(checks.map(x=>({country:x.country,area:x.area,value:x.overall_value,
                                          children:x.internal_rows,csv_rows:x.csv_rows})),null,2));

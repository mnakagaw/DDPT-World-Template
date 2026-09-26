#!/usr/bin/env node
// Check actual country exports against selected Geostat source cells and scope.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/georgia-areadata-20260926');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
if(data.country.id!=='GEO'||data.boundaries?.features?.length!==0)
  throw new Error('Expected Georgia 2024 census candidate with unjoined reference geometry');
const prefix='GEO_GEOSTAT24_';
const cases=[
  {area:'GEO',indicator:'POP_TOTAL',value:3929581,children:11,table:'909-02'},
  {area:'GEO',indicator:'AGE_0_14',value:770823,children:11,table:'910-02',calculated:true},
  {area:'GEO',indicator:'EDU_HIGHER_10PLUS',value:1090938,children:11,table:'912-01'},
  {area:'GEO',indicator:'LABOUR_UNEMPLOYMENT_SHARE',value:13.02,children:11,table:'913-01',calculated:true},
  {area:'GEO',indicator:'PRIVATE_HOUSEHOLDS',value:1201564,children:11,table:'915-01'},
  {area:'GEO:GEOSTAT24:TBILISI',indicator:'POP_TOTAL',value:1331485,children:10,table:'909-02'},
  {area:'GEO:GEOSTAT24:TBILISI',indicator:'AGE_0_14',value:264762,children:10,table:'910-02',calculated:true},
  {area:'GEO:GEOSTAT24:TBILISI:DISTRICT:GLDANI-DISTRICT',indicator:'POP_TOTAL',value:209477,children:0,table:'909-02'},
  {area:'GEO:GEOSTAT24:TBILISI:DISTRICT:GLDANI-DISTRICT',indicator:'LABOUR_ACTIVE',value:null,children:0,table:'913-01'},
  {area:'GEO:GEOSTAT24:REGION:ADJARA-A-R',indicator:'POP_TOTAL',value:402929,children:6,table:'909-02'},
  {area:'GEO:GEOSTAT24:MUNICIPALITY:ADJARA-A-R:C-BATUMI',indicator:'POP_RURAL',value:0,children:0,table:'909-02'},
  {area:'GEO:GEOSTAT24:MUNICIPALITY:ADJARA-A-R:KEDA-MUNICIPALITY',indicator:'PRIVATE_HOUSEHOLDS',value:3776,children:0,table:'915-01'},
  {area:'GEO:GEOSTAT24:REGION:RACHA-LECHKHUMI-AND-KVEMO-SVANETI',indicator:'POP_TOTAL',value:29901,children:4,table:'909-02'},
];
const sha=value=>createHash('sha256').update(value).digest('hex');
function parseCsv(input){
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
const out=path.join(project,'evidence','output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const item of cases){
  const territory=data.territories.find(x=>x.id===item.area);
  if(!territory)throw new Error('Missing territory '+item.area);
  const indicator=prefix+item.indicator,period='2024';
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,item.area,period),
    'diagnostic.html':diagnosticHtml(data,item.area,period),
    'diagnostic.md':diagnosticMarkdown(data,item.area,period),
    'planning.html':planningHtml(data,item.area,period,'en'),
    'evidence.csv':evidenceCsv(data,item.area,period),
  };
  const stem=`GEO-${sha(item.area+indicator).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))await writeFile(path.join(out,`${stem}-${suffix}`),content);
  const [header,...rows]=parseCsv(outputs['diagnostic.csv']);
  const col=name=>header.indexOf(name);
  for(const name of ['Record scope','Indicator ID','Value','Period','Status','Source URL','Source locator','Value provenance','Territory ID'])
    if(col(name)<0)throw new Error('Missing CSV column '+name);
  const relevant=scope=>rows.filter(row=>row[col('Record scope')]===scope&&row[col('Indicator ID')]===indicator);
  const overall=relevant('overall'),within=relevant('within_area');
  if(overall.length!==1||overall[0][col('Period')]!==period)
    throw new Error('Wrong overall row/period for '+territory.name+' '+indicator);
  if(item.value===null){
    if(overall[0][col('Value')]!==''||overall[0][col('Status')]==='observed')
      throw new Error('Uncollected Tbilisi district value was filled from its parent');
  }else if(Number(overall[0][col('Value')])!==item.value||
            overall[0][col('Status')]!==(item.calculated?'calculated':'observed'))
    throw new Error('Geostat value/status mismatch for '+territory.name+' '+indicator);
  if(within.length!==item.children)throw new Error('Wrong internal row count for '+territory.name+' '+indicator+': '+within.length);
  if(item.area==='GEO'&&(within[0]?.[col('Territory ID')]!=='GEO:GEOSTAT24:TBILISI'||
      within.at(-1)?.[col('Territory ID')]!=='GEO:GEOSTAT24:REGION:SHIDA-KARTLI'))
    throw new Error('National comparison membership/order changed');
  if(item.value!==null&&(!overall[0][col('Source locator')].includes(item.table)||
     !overall[0][col('Source URL')].includes('geostat.ge')))
    throw new Error('Geostat source locator/URL missing for '+territory.name);
  if(item.calculated&&item.value!==null&&!overall[0][col('Value provenance')].includes('calculated'))
    throw new Error('Calculated value was not labelled for '+territory.name+' '+indicator);
  if(item.calculated&&within.some(row=>row[col('Status')]==='calculated'&&!row[col('Value provenance')].includes('calculated')))
    throw new Error('Calculated comparison row lost provenance for '+indicator);
  if(item.calculated&&item.children>0&&!outputs['diagnostic.html'].includes('AreaData calculated'))
    throw new Error('Calculated HTML comparison row shown as source reported');
  if(item.children>0){
    const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
    const start=outputs['diagnostic.html'].indexOf(marker),end=outputs['diagnostic.html'].indexOf('</section>',start);
    if(start<0||end<0)throw new Error('Printable internal table missing for '+territory.name+' '+indicator);
    const printed=[...outputs['diagnostic.html'].slice(start,end).matchAll(/data-internal-row="([^"]+)"/g)].map(x=>x[1]);
    const expected=within.map(row=>row[col('Territory ID')]);
    if(JSON.stringify(printed)!==JSON.stringify(expected))
      throw new Error('Printable first/last/full internal rows differ from CSV for '+territory.name+' '+indicator);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(territory.name))throw new Error('Wrong selected territory in '+suffix);
  checks.push({territory:territory.name,territory_id:item.area,indicator,period,value:item.value,
    internal_rows:within.length,total_csv_rows:rows.length,
    first_internal_row:within[0]?.slice(0,17)||null,last_internal_row:within.at(-1)?.slice(0,17)||null,
    hashes:Object.fromEntries(Object.entries(outputs).map(([suffix,content])=>[suffix,sha(content)]))});
}
const wdi=data.observations.find(x=>x.territory_id==='GEO'&&x.indicator_id==='SP.POP.TOTL'&&x.period==='2024');
if(!wdi||wdi.value===3929581)throw new Error('WDI and Geostat census populations were silently harmonized');
const audit={status:'partial_candidate_output_check_not_independent_acceptance',country:'GEO',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),checks,
  source_geography:{national:3929581,top_level:11,municipalities_below_regions:63,tbilisi_districts:10,
    official_code_and_polygon_join:false},separate_wdi_2024_value:wdi.value,
  limitations:['48 XLSX originals acquired and mechanically inventoried; 43 tables remain semantically unassessed',
    'Official administrative code and census-compatible boundary polygons not joined',
    'Current municipality-specific plans, 2026 amended budgets, implementation and evaluation unverified',
    'No rendered print/PDF, full 42 scenarios or independent acceptance']};
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory,indicator,value,internal_rows,total_csv_rows})=>({territory,indicator,value,internal_rows,total_csv_rows})),null,2));

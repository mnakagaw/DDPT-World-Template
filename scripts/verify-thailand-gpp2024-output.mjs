#!/usr/bin/env node
// Check real country/province exports against both audited NESDC source tables.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/thailand-areadata-20260927');
const bytes=await readFile(path.join(project,'data/dashboard.json'));
const data=JSON.parse(bytes.toString('utf8'));
const audit=JSON.parse(await readFile(path.join(project,'evidence/THA_GPP2024_AUDIT.json'),'utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const fail=message=>{throw new Error(message)};
const fields={gpp_million_baht:['THA_NESDC_GPP_MTHB','C'],
  population_thousand_persons:['THA_NESDC_GPP_POP_THOUSAND','D'],
  gpp_per_capita_baht:['THA_NESDC_GPP_PC_BAHT','E']};
const sectors=audit.sector_field_disposition.filter(x=>x.status==='adopted');
if(sectors.length!==21||audit.adopted_direct_observations!==1872||
   audit.numeric_cells_audited!==2210)fail('2024p sector audit scope changed');
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
if(data.country.id!=='THA'||data.territories.length!==78||data.boundaries?.features?.length!==0)
  fail('Expected 77 NESDC provinces, country and zero unsupported polygons');
const original=new Map(audit.provinces.map(row=>[`THA:NESDC2024:${row.nesdc_code}`,row]));
original.set('THA',audit.country);
const cases=['THA','THA:NESDC2024:0101','THA:NESDC2024:0201',
  'THA:NESDC2024:0301','THA:NESDC2024:0701'];
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const id of cases){
  const area=data.territories.find(row=>row.id===id),source=original.get(id);
  if(!area||!source)fail(`Missing selected source row ${id}`);
  const outputs={
    'diagnostic.csv':diagnosticCsv(data,id,'2024p'),
    'diagnostic.html':diagnosticHtml(data,id,'2024p'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2024p'),
    'planning.html':planningHtml(data,id,'2024p','en'),
    'evidence.csv':evidenceCsv(data,id,'2024p'),
  };
  const stem=`THA-${sha(id).slice(0,12)}`;
  for(const [suffix,content] of Object.entries(outputs))
    await writeFile(path.join(out,stem+'-'+suffix),content);
  const [header,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=key=>header.indexOf(key);
  for(const key of ['Record scope','Indicator ID','Value','Period','Status','Source URL',
    'Source locator','Territory ID'])if(col(key)<0)fail(`Missing CSV column ${key}`);
  const subset=(scope,indicator)=>rows.filter(row=>row[col('Record scope')]===scope&&
    row[col('Indicator ID')]===indicator);
  for(const [field,[indicator,letter]] of Object.entries(fields)){
    const overall=subset('overall',indicator);
    if(overall.length!==1||overall[0][col('Status')]!=='observed'||
       Number(overall[0][col('Value')])!==source.values[field]||
       overall[0][col('Period')]!=='2024p'||
       !overall[0][col('Source URL')].includes('nesdc.go.th/')||
       overall[0][col('Source locator')]!==`PER CAPITA!${letter}${source.row}`)
      fail(`Export differs from original: ${id}/${field}`);
  }
  const block=audit.sector_2024p_current_price[id==='THA'?'THA':id.split(':').at(-1)];
  if(!block)fail(`Missing current-price source block for ${id}`);
  for(const {label,indicator_id:indicator} of sectors){
    const originalCell=block.fields[label],overall=subset('overall',indicator);
    if(!originalCell||overall.length!==1||overall[0][col('Status')]!=='observed'||
       Number(overall[0][col('Value')])!==originalCell.value||
       overall[0][col('Period')]!=='2024p'||
       !overall[0][col('Source URL')].includes('nesdc.go.th/')||
       overall[0][col('Source locator')]!==originalCell.locator)
      fail(`Sector export differs from original: ${id}/${indicator}`);
  }
  const childIds=data.territories.filter(row=>row.parent_id===id).map(row=>row.id);
  const within=subset('within_area',fields.gpp_million_baht[0]);
  if(JSON.stringify(within.map(row=>row[col('Territory ID')]))!==JSON.stringify(childIds))
    fail(`Internal comparison roster changed ${id}`);
  for(const row of within){
    const child=original.get(row[col('Territory ID')]);
    if(!child||Number(row[col('Value')])!==child.values.gpp_million_baht)
      fail(`Internal GPP value differs ${id}/${row[col('Territory ID')]}`);
  }
  if(id==='THA'){
    if(childIds.length!==77||childIds[0]!=='THA:NESDC2024:0101'||
       childIds.at(-1)!=='THA:NESDC2024:0706')
      fail('Country comparison is not the complete 77-province roster');
    for(const indicator of [...Object.values(fields).map(x=>x[0]),
      ...sectors.map(x=>x.indicator_id)]){
      const marker=`<section class="internal-comparison" data-internal-comparison="${indicator}">`;
      const start=outputs['diagnostic.html'].indexOf(marker),
        end=outputs['diagnostic.html'].indexOf('</section>',start);
      if(start<0||end<0)fail(`Printable comparison missing for ${indicator}`);
      const printed=[...outputs['diagnostic.html'].slice(start,end)
        .matchAll(/data-internal-row="([^"]+)"/g)].map(hit=>hit[1]);
      if(JSON.stringify(printed)!==JSON.stringify(childIds))
        fail(`Country print omitted or reordered rows for ${indicator}`);
    }
  }else if(childIds.length!==0){
    fail(`Province acquired unexpected internal children: ${id}`);
  }
  for(const suffix of ['diagnostic.html','diagnostic.md','planning.html','evidence.csv'])
    if(!outputs[suffix].includes(area.name))fail(`Selected territory absent from ${suffix}: ${id}`);
  checks.push({territory_id:id,name:area.name,source_gpp_million_baht:source.values.gpp_million_baht,
    internal_rows:childIds.length,first_internal_row:childIds[0]||null,
    last_internal_row:childIds.at(-1)||null,
    output_hashes:Object.fromEntries(Object.entries(outputs).map(([name,value])=>[name,sha(value)]))});
}
await writeFile(path.join(project,'evidence/OUTPUT_VERIFICATION.json'),JSON.stringify({
  status:'partial_candidate_output_check_not_independent_acceptance',
  checked_at:new Date().toISOString(),dataset_sha256:sha(bytes),cases:checks,
  constraints:['DOPA legal code and matching current polygon unavailable',
    '2025 NSO census and BORA registration are distinct and unacquired',
    '1995-2023, CVM, Regions to GDP and cluster fields unassessed',
    'Province plan bodies, budget actuals, 42 scenarios and independent acceptance pending'],
},null,2)+'\n');
console.log(JSON.stringify(checks.map(({territory_id,name,source_gpp_million_baht,internal_rows})=>
  ({territory_id,name,source_gpp_million_baht,internal_rows})),null,2));

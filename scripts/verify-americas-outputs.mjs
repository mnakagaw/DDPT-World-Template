#!/usr/bin/env node
import {readFile,mkdir,rm,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {documentsCsv,evidenceCsv,planningHtml,planningMarkdown} from '../scaffold/site/model.mjs';

const arg=name=>{const index=process.argv.indexOf(name);return index<0?null:process.argv[index+1];};
const project=path.resolve(arg('--project')||'');
if(!arg('--project'))throw new Error('Provide --project <Americas project>');
const dataset=JSON.parse(await readFile(path.join(project,'data','dashboard.json'),'utf8'));
const outputDir=path.join(project,'evidence','output-verification');
await rm(outputDir,{recursive:true,force:true});await mkdir(outputDir,{recursive:true});

function csvRecords(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let index=text.charCodeAt(0)===0xfeff?1:0;index<text.length;index++){
    const char=text[index];
    if(quoted){if(char==='"'&&text[index+1]==='"'){cell+='"';index++;}else if(char==='"')quoted=false;else cell+=char;}
    else if(char==='"')quoted=true;
    else if(char===','){row.push(cell);cell='';}
    else if(char==='\n'){row.push(cell.replace(/\r$/,''));if(row.some(value=>value!==''))rows.push(row);row=[];cell='';}
    else cell+=char;
  }
  if(cell||row.length){row.push(cell);rows.push(row);}return rows;
}
const hash=value=>createHash('sha256').update(value).digest('hex');
const files=[];
async function save(name,content,extra={}){
  if(!content.length)throw new Error(`${name} is empty`);
  await writeFile(path.join(outputDir,name),content);
  const record={file:name,bytes:Buffer.byteLength(content),sha256:hash(content),...extra};files.push(record);return record;
}

// Output functions intentionally retain generic semantics and therefore scan
// the dataset they receive. Limit each verification view to the selected
// regional cohort or country branch so the audit scales with a continental
// dataset without changing the resulting rows.
function scopedDataset(dataset,territoryId){
  const selected=dataset.territories.find(row=>row.id===territoryId);
  if(!selected)throw new Error(`Missing verification territory ${territoryId}`);
  const countryId=selected.type==='country'?selected.id:selected.country_id;
  const ids=new Set();
  if(countryId){
    for(const area of dataset.territories)if(area.id===countryId||area.country_id===countryId)ids.add(area.id);
  }else{
    const children=new Map();
    for(const area of dataset.territories){let list=children.get(area.parent_id);if(!list){list=[];children.set(area.parent_id,list);}list.push(area);}
    const queue=[selected];
    while(queue.length){const area=queue.shift();if(ids.has(area.id))continue;ids.add(area.id);if(area.type!=='country')queue.push(...(children.get(area.id)||[]));}
    for(const comparison of dataset.analysis?.comparisons||[])if(ids.has(comparison.parent_id))for(const member of comparison.member_ids||[])ids.add(member);
  }
  let observations=dataset.observations.filter(row=>ids.has(row.territory_id));
  if(!countryId){
    const allowed=new Set(observations.filter(row=>row.territory_id===territoryId).map(row=>row.indicator_id));
    for(const rule of dataset.analysis?.aggregation?.rules||[])allowed.add(rule.indicator_id);
    observations=observations.filter(row=>allowed.has(row.indicator_id));
  }
  const indicatorIds=new Set(observations.map(row=>row.indicator_id));
  const indicators=dataset.indicators.filter(row=>indicatorIds.has(row.id));
  return {...dataset,territories:dataset.territories.filter(row=>ids.has(row.id)),indicators,observations,
    documents:(dataset.documents||[]).filter(row=>ids.has(row.territory_id)),
    boundaries:{...dataset.boundaries,features:(dataset.boundaries?.features||[]).filter(row=>ids.has(row.properties?.territory_id))},
    analysis:{...dataset.analysis,
      comparisons:(dataset.analysis?.comparisons||[]).filter(row=>ids.has(row.parent_id)).map(row=>({...row,member_ids:(row.member_ids||[]).filter(id=>ids.has(id))})),
      terminal_territory_ids:(dataset.analysis?.terminal_territory_ids||[]).filter(id=>ids.has(id)),
      default_period_by_indicator:Object.fromEntries(Object.entries(dataset.analysis?.default_period_by_indicator||{}).filter(([id])=>indicatorIds.has(id)))}
  };
}

const scopes=[
  ['americas','M49:019'],['central-america-caribbean','CUSTOM:CAM-CAR'],['belize','BLZ'],
  ['belize-district','BLZ:C2022:DIST:3'],['guatemala','GTM'],['el-progreso','GTM:C2018:DEP:2']
];
const scopeChecks=[];
for(const [slug,id] of scopes){
  const view=scopedDataset(dataset,id);
  const csv=diagnosticCsv(view,id,'latest-available'),records=csvRecords(csv),header=records[0],data=records.slice(1);
  const sourceIndex=header.indexOf('Source URL'),statusIndex=header.indexOf('Status');
  if(sourceIndex<0||statusIndex<0||!data.some(row=>/^https:\/\//.test(row[sourceIndex]||'')))throw new Error(`${id} diagnostic lacks source URL evidence`);
  const csvRecord=await save(`${slug}-diagnostic.csv`,csv,{rows:data.length,first_data_row:data[0],last_data_row:data.at(-1)});
  await save(`${slug}-diagnostic.md`,diagnosticMarkdown(view,id,'latest-available'));
  await save(`${slug}-diagnostic.html`,diagnosticHtml(view,id,'latest-available'));
  scopeChecks.push({slug,id,csv_rows:csvRecord.rows,first_data_row:csvRecord.first_data_row,last_data_row:csvRecord.last_data_row,statuses:[...new Set(data.map(row=>row[statusIndex]))].sort(),has_source_url:true});
}

const planningChecks=[];
for(const [slug,id] of [['belize','BLZ'],['guatemala','GTM']]){
  const view=scopedDataset(dataset,id),docs=view.documents.filter(document=>document.territory_id===id);
  if(!docs.length)throw new Error(`${id} has no planning references`);
  const evidence=evidenceCsv(view,id,'latest-available'),materials=documentsCsv(view,id);
  await save(`${slug}-evidence.csv`,evidence,{rows:csvRecords(evidence).length-1});
  await save(`${slug}-materials.csv`,materials,{rows:csvRecords(materials).length-1});
  for(const language of ['en','es','ja']){
    const markdown=planningMarkdown(view,id,'latest-available',language),html=planningHtml(view,id,'latest-available',language);
    if(!markdown.includes(docs[0].title)||!html.includes(docs[0].title))throw new Error(`${id} ${language} planning output lost its source material`);
    await save(`${slug}-planning-base-${language}.md`,markdown);
    await save(`${slug}-planning-base-${language}.html`,html);
    planningChecks.push({territory_id:id,language,document_count:docs.length,contains_material:true,html_language:html.includes(`lang="${language}"`)});
  }
}

const result={
  schema_version:'1.0',generated_at:new Date().toISOString(),data_edition:dataset.generated_at,
  dataset_sha256:hash(await readFile(path.join(project,'data','dashboard.json'))),requested_period:'latest-available',
  file_count:files.length,files,scope_checks:scopeChecks,planning_checks:planningChecks,
  assertions:{all_nonempty:files.every(file=>file.bytes>0),all_unique_hashes:new Set(files.map(file=>file.sha256)).size===files.length,guatemala_calculated_status:scopeChecks.find(row=>row.id==='GTM')?.statuses.includes('calculated')||false}
};
if(!Object.values(result.assertions).every(Boolean))throw new Error(`Output assertion failed: ${JSON.stringify(result.assertions)}`);
await writeFile(path.join(project,'evidence','OUTPUT_VERIFICATION.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({ok:true,file_count:files.length,scope_rows:Object.fromEntries(scopeChecks.map(row=>[row.id,row.csv_rows])),planning_records:planningChecks.length,assertions:result.assertions},null,2));

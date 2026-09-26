#!/usr/bin/env node
// Verify the limited Azerbaijan 2026 adoption in the actual country output path.
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml} from '../scaffold/site/diagnostic.mjs';
import {initialState, comparisonRows, comparisonCompatibility, planningHtml, hierarchyControls, selectHierarchyOption, observationState} from '../scaffold/site/model.mjs';
import {comparisonSet} from '../scaffold/site/analysis.mjs';

const index=process.argv.indexOf('--project');
if(index<0 || !process.argv[index+1] || process.argv.length!==4)throw new Error('Usage: node scripts/verify-azerbaijan-age2026-output.mjs --project <project>');
const project=path.resolve(process.argv[index+1]);
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
if(data.country.id!=='AZE')throw new Error('Expected Azerbaijan');
const source=data.sources.find(item=>item.id==='aze-ssc-resident-age-area-2026');
const sourceBytes=await readFile(path.join(project,source.raw_path));
if(source.sha256!=='6d47885ee89077fb2412ee8c145a32edefa6b873da680bfcb746b36ca33ebf3c' ||
   createHash('sha256').update(sourceBytes).digest('hex')!==source.sha256)throw new Error('2026 age original changed');
const domestic=data.observations.filter(row=>row.indicator_id.startsWith('AZE_SSC_2026_'));
if(data.territories.length!==102 || data.boundaries.features.length!==0 || data.documents.length!==1 ||
   domestic.length!==2023 || domestic.some(row=>row.status!=='observed') ||
   data.indicators.filter(item=>item.id.startsWith('AZE_SSC_2026_')).length!==23)throw new Error('Partial adoption scope changed');
const area=id=>data.territories.find(item=>item.id===id);
const observed=(id,metric)=>domestic.find(row=>row.territory_id===id&&row.indicator_id===metric);
const controls=[
  ['AZE',10262351],['AZE:SSC2026:AGE:R12',2356162],['AZE:SSC2026:AGE:R14',309187],
  ['AZE:SSC2026:AGE:R27',472429],['AZE:SSC2026:AGE:R60',751042],
  ['AZE:SSC2026:AGE:R89',949313],['AZE:SSC2026:AGE:R91',113646],
  ['AZE:SSC2026:AGE:R124',303731],['AZE:SSC2026:AGE:R138',140929],
];
for(const [id,total] of controls){
  if(!area(id)||observed(id,'AZE_SSC_2026_TOTAL')?.value!==total)throw new Error(`Source-control value changed: ${id}`);
}
if(area('AZE:SSC2026:SETTLEMENT:R325')?.official_code!=='80101014' ||
   area('AZE:SSC2026:SETTLEMENT:R325')?.parent_id!=='AZE:SSC2026:AGE:R91' ||
   observed('AZE:SSC2026:SETTLEMENT:R325','AZE_SSC_2026_SETTLEMENT_TOTAL')?.value!==18.0 ||
   observed('AZE:SSC2026:AGE:R91','AZE_SSC_2026_SETTLEMENT_TOTAL'))throw new Error('Astara city/district identity or precision changed');
const districtId='AZE:SSC2026:AGE:R91',cityId='AZE:SSC2026:SETTLEMENT:R325';
if(data.analysis.terminal_territory_ids.includes(districtId) || !data.analysis.incomplete_child_cover_ids?.includes(districtId) ||
   comparisonSet(data,districtId).members.length)throw new Error('Partial Astara city register must be navigable without whole-district comparison');
const districtState=initialState(data,`?territory=${districtId}&metric=AZE_SSC_2026_TOTAL&period=2026-01-01`);
const cityOption=hierarchyControls(data,districtId).find(item=>item.parent.id===districtId)?.options.find(item=>item.targetId===cityId);
if(!cityOption)throw new Error('Astara city is absent from the normal district hierarchy');
const chosenCity=selectHierarchyOption(data,districtState,districtId,cityOption.value);
if(chosenCity.selected!==cityId || chosenCity.metric!==districtState.metric || chosenCity.period!==districtState.period ||
   !planningHtml(data,chosenCity.selected,chosenCity.period,'en').includes('Astara city master plan through 2039 — Cabinet approval No. 291')){
  throw new Error('Astara city selection did not update the area and its plan together');
}
const backDistrict=selectHierarchyOption(data,chosenCity,districtId,'');
if(backDistrict.selected!==districtId || backDistrict.metric!==chosenCity.metric || backDistrict.period!==chosenCity.period ||
   planningHtml(data,backDistrict.selected,backDistrict.period,'en').includes('Astara city master plan through 2039 — Cabinet approval No. 291') ||
   observationState(data,districtId,'AZE_SSC_2026_SETTLEMENT_TOTAL','2026-01-01').value!==null ||
   comparisonRows(data,backDistrict).length!==0)throw new Error('Astara parent reselection retained city evidence or incomplete comparison');
const top=data.territories.filter(item=>item.parent_id==='AZE');
if(top.length!==14 || top.reduce((sum,item)=>sum+observed(item.id,'AZE_SSC_2026_TOTAL').value,0)!==10262351)throw new Error('National 14-member source cover changed');
for(const parent of top){
  const children=data.analysis.comparisons.find(item=>item.parent_id===parent.id)?.member_ids||[];
  if(!children.length || children.reduce((sum,id)=>sum+observed(id,'AZE_SSC_2026_TOTAL').value,0)!==observed(parent.id,'AZE_SSC_2026_TOTAL').value){
    throw new Error(`Reporting-group cover changed: ${parent.id}`);
  }
}
for(const selected of ['AZE','AZE:SSC2026:AGE:R89']){
  const state=initialState(data,`?territory=${selected}&metric=AZE_SSC_2026_TOTAL&period=2026-01-01&level=statistical_reporting_region`);
  const rows=comparisonRows(data,state);
  if(!comparisonCompatibility(data,state).comparable || rows.length!==14 || rows.some(row=>row.value===null || row.status!=='observed')){
    throw new Error(`Mixed-type source-backed thematic cohort failed: ${selected}`);
  }
}
function parseCsv(csv){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=csv.charCodeAt(0)===0xfeff?1:0;i<csv.length;i++){
    const char=csv[i];
    if(quoted){if(char==='"'&&csv[i+1]==='"'){cell+='"';i++;}else if(char==='"')quoted=false;else cell+=char;}
    else if(char==='"')quoted=true;
    else if(char===','){row.push(cell);cell='';}
    else if(char==='\n'){rows.push([...row,cell.replace(/\r$/,'')]);row=[];cell='';}
    else cell+=char;
  }
  return rows.filter(item=>item.some(value=>value!==''));
}
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const results=[];
for(const [id,total] of [...controls,['AZE:SSC2026:SETTLEMENT:R325',18.0]]){
  const csv=diagnosticCsv(data,id,'latest-available');
  const html=diagnosticHtml(data,id,'latest-available');
  const planning=planningHtml(data,id,'latest-available','en');
  await writeFile(path.join(out,`${id.replaceAll(':','_')}-diagnostic.csv`),csv);
  await writeFile(path.join(out,`${id.replaceAll(':','_')}-diagnostic.html`),html);
  await writeFile(path.join(out,`${id.replaceAll(':','_')}-planning.html`),planning);
  const [header,...rows]=parseCsv(csv);
  const col=name=>{const result=header.indexOf(name);if(result<0)throw new Error(`Missing CSV column ${name}`);return result;};
  const metric=id.endsWith('R325')?'AZE_SSC_2026_SETTLEMENT_TOTAL':'AZE_SSC_2026_TOTAL';
  const overall=rows.filter(row=>row[col('Record scope')]==='overall'&&row[col('Territory ID')]===id&&row[col('Indicator ID')]===metric);
  if(overall.length!==1 || Number(overall[0][col('Value')])!==total || overall[0][col('Period')]!=='2026-01-01')throw new Error(`Diagnostic output differs: ${id}`);
  const cityPlan=planning.includes('Astara city master plan through 2039 — Cabinet approval No. 291');
  if(cityPlan!==id.endsWith('R325'))throw new Error(`Astara city plan leaked or missing: ${id}`);
  results.push({territory_id:id,rows:rows.length,indicator:metric,value:total,planning_city_document:cityPlan});
}
console.log(JSON.stringify(results,null,2));

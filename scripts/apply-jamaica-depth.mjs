#!/usr/bin/env node
import {access,cp,mkdir,readFile,stat,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

function arg(name){const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;}
const project=path.resolve(arg('--project')||'');
const staging=path.resolve(arg('--staging')||'.work/staging/caribbean-north-depth');
const dryRun=process.argv.includes('--dry-run');
if(!project)throw new Error('--project is required');

const shaBuffer=body=>createHash('sha256').update(body).digest('hex');
const shaFile=async filename=>shaBuffer(await readFile(filename));
const dataPath=path.join(project,'data','dashboard.json');
const evidenceDir=path.join(project,'evidence');
const packagePath=path.join(staging,'JAM_LOCAL_DEPTH_PACKAGE.json');
const ledgerPath=path.join(staging,'JAM_ADOPTION_LEDGER.json');
const lawReceiptPath=path.join(staging,'JAM_PLANNING_LAW_RECEIPT.json');
const sourceRoot=path.join(staging,'raw','JAM');
const [dataset,pkg,ledger,lawReceipt,sourceReceipts,semantic,preflight]=await Promise.all([
  readFile(dataPath,'utf8').then(JSON.parse),
  readFile(packagePath,'utf8').then(JSON.parse),
  readFile(ledgerPath,'utf8').then(JSON.parse),
  readFile(lawReceiptPath,'utf8').then(JSON.parse),
  readFile(path.join(staging,'SOURCE_RECEIPTS.json'),'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
]);
if(pkg.country_area_id!=='JAM')throw new Error('Package is not JAM');

const local=dataset.territories.filter(row=>row.country_id==='JAM'&&row.id!=='JAM');
const expected=new Map(pkg.geography_crosswalk.map(row=>[row.territory_id,row]));
if(local.length!==14||local.some(row=>!expected.has(row.id)))throw new Error('Target JAM parish registry does not match the audited 14-parish crosswalk');
for(const source of pkg.sources){
  const filename=path.join(sourceRoot,path.basename(source.raw_path));
  if(await shaFile(filename)!==source.sha256)throw new Error(`Source hash mismatch: ${filename}`);
}

const sourceIds=new Set(pkg.sources.map(row=>row.id)),indicatorIds=new Set(pkg.indicators.map(row=>row.id));
dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...pkg.sources];
dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...pkg.indicators];
dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...pkg.observations];
for(const area of local){const x=expected.get(area.id);area.official_code=x.iso_3166_2;area.code_system='ISO 3166-2:JM parish code';area.geography_note=`STATIN 2011 parish name matched explicitly to ${x.iso_3166_2}; the existing boundary remains reference display geometry.`;}
for(const feature of dataset.boundaries?.features||[]){const x=expected.get(feature.properties?.territory_id);if(x){feature.properties.official_code=x.iso_3166_2;feature.properties.code_system='ISO 3166-2:JM parish code';feature.properties.join_method='explicit normalized STATIN parish-name to ISO 3166-2 crosswalk';}}
dataset.analysis=dataset.analysis||{};
dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),...Object.fromEntries(pkg.indicators.map(row=>[row.id,'2011']))};
dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'jam-2011-official-parish-depth'])];
dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),'JAM 2011: 19 official parish indicators from STATIN tables; each uses a complete 14-parish set and its published denominator.'])];
const validation=validateDataset(dataset);
if(validation.errors.length)throw new Error(validation.errors.join('; '));

const result={country_area_id:'JAM',dry_run:dryRun,local_territories:local.length,added_indicators:pkg.indicators.length,added_observations:pkg.observations.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
if(dryRun){console.log(JSON.stringify(result,null,2));process.exit(0);}

const rawDestination=path.join(project,'raw','caribbean-north','JAM');
await mkdir(rawDestination,{recursive:true});
await cp(sourceRoot,rawDestination,{recursive:true,force:true});
for(const source of pkg.sources)await access(path.join(project,source.raw_path));

const sourceById=new Map(pkg.sources.map(row=>[row.id,row]));
const receiptByFilename=new Map((sourceReceipts.entries||[]).map(row=>[row.filename,row]));
const indexReceipt=receiptByFilename.get('index.html');
if(!indexReceipt)throw new Error('Jamaica Census index receipt is missing');
sourceById.set('jam-stat-in-2011-index',{id:'jam-stat-in-2011-index',url:indexReceipt.url,raw_path:'raw/caribbean-north/JAM/index.html',sha256:indexReceipt.sha256,bytes:indexReceipt.bytes});
const sourceEvidence=row=>{
  const source=sourceById.get(row.source_id);
  return {path:source.raw_path,sha256:source.sha256,bytes:source.bytes??null,url:source.url,locator:row.table_locator,geography_match:'All 14 STATIN parish names are explicitly crosswalked to ISO 3166-2:JM and stable AreaData territory IDs.'};
};
const adoptedRows=(pkg.semantic_catalog||[]).map((row,index)=>({
  country_area_id:'JAM',source_id:row.source_id,source_path:row.source_path,source_url:row.source_url,
  table_id:row.table_locator||`STATIN-2011-${index+1}`,table_title:row.table_locator||row.source_id,
  field_id:row.indicator_id,field_label:dataset.indicators.find(item=>item.id===row.indicator_id)?.name||row.indicator_id,
  numeric_cell_count:15,theme:row.theme,disposition:'integrated',reason:`Official STATIN 2011 value integrated for the country and all 14 parishes. ${row.definition}`,
  indicator_id:row.indicator_id,coverage_complete:true,country_edition_eligible:true,evidence:[sourceEvidence(row)]
}));
const pendingRows=(pkg.terminal_local_gaps||[]).map((row,index)=>({
  country_area_id:'JAM',source_id:row.source_id,source_path:row.raw_path,source_url:row.source_url,
  table_id:row.table_id||'STATIN 2011 Census published-table index',table_title:'STATIN 2011 Census published-table index',
  field_id:`pending-${row.theme}-${index+1}`,field_label:`Pending ${row.theme} review`,numeric_cell_count:0,theme:row.theme,
  disposition:'follow_up_required',reason:row.reason,coverage_complete:false,country_edition_eligible:false,
  evidence:[{...sourceEvidence({source_id:row.source_id,table_locator:row.table_id}),scope_note:row.evidence}]
}));
semantic.records=[...(semantic.records||[]).filter(row=>row.country_area_id!=='JAM'),...adoptedRows,...pendingRows];
semantic.record_count=semantic.records.length;
semantic.generated_at=new Date().toISOString();
semantic.adjudication={...(semantic.adjudication||{}),JAM:{reviewed_numeric_fields:adoptedRows.length,terminal_dispositions:adoptedRows.length,pending_theme_reviews:pendingRows.map(row=>row.theme),covered_themes:[...new Set(adoptedRows.map(row=>row.theme))].sort(),method:'Official STATIN 2011 parish tables with complete 14-parish coverage, retained hashes, exact table locators and explicit ISO 3166-2:JM crosswalk.',audit:'evidence/JAM_DEPTH_ADOPTION_AUDIT.json'}};

const jam=preflight.countries.find(row=>row.country_area_id==='JAM');
if(!jam)throw new Error('JAM preflight entry is missing');
const indexSource=sourceById.get('jam-stat-in-2011-index');
const allAdoptedEvidence=adoptedRows.flatMap(row=>row.evidence);
const exactEvidence=(source,locator,geography=false)=>({path:source.raw_path,sha256:source.sha256,bytes:source.bytes??null,url:source.url,locator,...(geography?{geography_match:'All 14 parish names are explicitly crosswalked to ISO 3166-2:JM and stable AreaData territory IDs.'}:{})});
const setDomain=(id,{status='inspected',urls,evidence,note,geography=false,verified=true})=>{
  const order=['identified','accessed','acquired','inspected','geography_matched','adopted'],at=Math.max(0,order.indexOf(status));
  jam[id]={...(jam[id]||{}),status,urls, note,evidence,completion_verified:verified};
  for(const [i,key] of order.entries())jam[id][key]=i<=at;
  jam[id].geography_matched=geography||status==='geography_matched'||status==='adopted';
  jam[id].adopted=status==='adopted';
};
setDomain('official_statistics_office',{status:'inspected',urls:[indexSource.url],evidence:[exactEvidence(indexSource,'Official STATIN 2011 Census published-table index and publisher identity')],note:'Official STATIN Census catalogue acquired and inspected with a retained hash and exact index locator.'});
setDomain('census_results',{status:'adopted',urls:[...new Set(pkg.sources.map(row=>row.url))],evidence:allAdoptedEvidence,note:'Nineteen indicators are integrated from official STATIN 2011 country/parish tables with retained hashes and exact locators.',geography:true});
setDomain('table_catalog',{status:'inspected',urls:[indexSource.url],evidence:[exactEvidence(indexSource,'Official STATIN 2011 Census published-table index')],note:'The official 2011 Census table index is retained. Four themes remain explicitly follow-up-required rather than being declared unavailable.'});
setDomain('machine_readable_data',{status:'adopted',urls:[...new Set(pkg.sources.map(row=>row.url))],evidence:allAdoptedEvidence,note:'Official HTML tables and fixed PDF tables were normalized to a reproducible JSON bundle; original bytes, hashes and table locators are retained.',geography:true});
setDomain('administrative_codes',{status:'geography_matched',urls:[indexSource.url],evidence:[exactEvidence(indexSource,'Explicit STATIN parish-name to ISO 3166-2:JM crosswalk for all 14 parishes',true)],note:'Every adopted parish name is explicitly matched to ISO 3166-2:JM and an existing AreaData territory ID.',geography:true});
// Planning-law bytes are retained, but identity acquisition is not treated as completed legal interpretation.
jam.planning_law={...(jam.planning_law||{}),status:'acquired',identified:true,accessed:true,acquired:true,inspected:false,geography_matched:false,adopted:false,completion_verified:false,note:'Official Local Governance Act 2016 page/PDF acquired and hashed. The PDF is scanned and the legal-duty interpretation remains pending.',evidence:lawReceipt.files||lawReceipt.acquisitions||[]};
jam.country_adapter_status='local_depth_integrated_source_review_open';

dataset.generated_at=new Date().toISOString();
const body=JSON.stringify(dataset)+'\n';
const datasetSha=shaBuffer(Buffer.from(body));
const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'JAM',dataset_sha256_before_completion_sync:datasetSha,package_path:path.relative(process.cwd(),packagePath).replaceAll('\\','/'),package_sha256:await shaFile(packagePath),adopted_indicator_count:pkg.indicators.length,observation_count:pkg.observations.length,local_territory_count:14,integrated_themes:[...new Set(adoptedRows.map(row=>row.theme))].sort(),pending_theme_reviews:pendingRows.map(row=>row.theme),source_objects:pkg.sources.map(row=>({path:row.raw_path,sha256:row.sha256,url:row.url})),geography_crosswalk:pkg.geography_crosswalk,validation};
await Promise.all([
  writeFile(dataPath,body),
  writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(semantic,null,2)+'\n'),
  writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
  writeFile(path.join(evidenceDir,'JAM_DEPTH_ADOPTION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),
]);
await generateSite({dataset,outDir:project});
result.dataset_sha256=datasetSha;result.raw_destination=rawDestination;result.semantic_integrated_rows=adoptedRows.length;result.pending_theme_reviews=pendingRows.length;
console.log(JSON.stringify(result,null,2));

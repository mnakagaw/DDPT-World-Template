import path from 'node:path';
import {readFile,writeFile,rename,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {resolvedObservation} from '../scaffold/site/aggregation.mjs';

const sha256=value=>createHash('sha256').update(value).digest('hex');

export async function applyAmericasWppRegion({project,normalizedPath}) {
  const datasetPath=path.resolve(project,'data/dashboard.json');
  const normalized=JSON.parse(await readFile(path.resolve(normalizedPath),'utf8'));
  const original=await readFile(datasetPath),dataset=JSON.parse(original.toString('utf8'));
  if(dataset.country?.id!=='AMR'||normalized.scope_id!=='M49:019')throw new Error('The input is not the Americas dataset and its matching WPP normalization.');
  const countrySource=dataset.sources.find(source=>source.id===normalized.source?.id);
  const regional=normalized.regional_source,rows=normalized.regional_observations;
  if(!countrySource||countrySource.sha256!==normalized.source.sha256||regional?.sha256!==countrySource.sha256||regional?.territory_id!=='M49:005'||regional?.geographic_level!=='world_region_series'||rows?.length!==4)throw new Error('UN WPP regional source identity, hash or periods do not match.');
  if(dataset.sources.some(source=>source.id===regional.id)||dataset.observations.some(row=>row.territory_id==='M49:005'&&row.indicator_id==='UN_WPP_POP_TOTAL')||dataset.analysis.aggregation.coverage_sets?.length)throw new Error('Regional WPP evidence is already present; refusing to apply it twice.');
  if(rows.some(row=>row.territory_id!=='M49:005'||row.indicator_id!=='UN_WPP_POP_TOTAL'||row.source_id!==regional.id)||new Set(rows.map(row=>row.period)).size!==4||['2023','2024','2025','2026'].some(year=>!rows.some(row=>row.period===year)))throw new Error('South America WPP regional observations are incomplete or mismatched.');
  dataset.sources.push({...regional,raw_path:countrySource.raw_path,receipt_path:countrySource.receipt_path});
  dataset.observations.push(...rows);
  dataset.analysis.aggregation.coverage_sets=[{parent_id:'M49:019',indicator_id:'UN_WPP_POP_TOTAL',member_ids:['M49:021','CUSTOM:CAM-CAR','M49:005'],source_ids:['un-m49'],membership_note:'The three non-overlapping direct Americas regions cover M49 019. South America uses the exact published UN WPP subregion value; Northern America and Central America + Caribbean use complete same-period country/area values.'}];
  dataset.analysis.aggregation.rules.find(rule=>rule.indicator_id==='UN_WPP_POP_TOTAL').note='Sum exact country/area observations or a matching source-reported UN subregion observation for one WPP period and variant. Every non-overlapping member must be covered; country-level missing values remain missing.';
  dataset.collection.notes.push('UN WPP South America subregion observations are adopted directly for 2023-2026. BVT and SGS have no country WPP rows and remain missing at country level; the Americas total uses three complete non-overlapping regional components.');
  dataset.generated_at=new Date().toISOString();
  const values=Object.fromEntries(['2023','2024','2025','2026'].map(period=>{
    const south=resolvedObservation(dataset,'M49:005','UN_WPP_POP_TOTAL',period);
    const central=resolvedObservation(dataset,'CUSTOM:CAM-CAR','UN_WPP_POP_TOTAL',period);
    const north=resolvedObservation(dataset,'M49:021','UN_WPP_POP_TOTAL',period);
    const americas=resolvedObservation(dataset,'M49:019','UN_WPP_POP_TOTAL',period);
    if(south.status!=='observed'||central.status!=='calculated'||north.status!=='calculated'||americas.status!=='calculated'||americas.value!==south.value+central.value+north.value)throw new Error(`Incomplete or inconsistent WPP regional cover in ${period}.`);
    return [period,{south_america:south.value,central_america_caribbean:central.value,northern_america:north.value,americas:americas.value,components:americas.components.map(item=>item.territory_id)}];
  }));
  const encoded=Buffer.from(JSON.stringify(dataset)+'\n'),temp=path.join(path.dirname(datasetPath),`.dashboard-wpp-region-${process.pid}.json`);
  await writeFile(temp,encoded);await rename(temp,datasetPath);
  const receipt={schema_version:'1.0',applied_at:dataset.generated_at,previous_dataset_sha256:sha256(original),new_dataset_sha256:sha256(encoded),source_sha256:countrySource.sha256,source_id:regional.id,source_location_code:931,source_sdmx_code:'005',source_periods:rows.map(row=>row.period),country_rows_remain_missing:normalized.summary.missing_country_ids,regional_totals:values,note:'South America is a source-reported UN WPP subregion observation. Americas is an AreaData calculation from three non-overlapping regions. Census series is unchanged.'};
  const evidence=path.resolve(project,'evidence');await mkdir(evidence,{recursive:true});
  await writeFile(path.join(evidence,'UN_WPP_REGIONAL_EXTENSION.json'),JSON.stringify(receipt,null,2)+'\n');
  return receipt;
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','normalized']);if(!args.project||!args.normalized)throw new Error('Usage: node scripts/apply-americas-wpp-region.mjs --project <Americas project> --normalized <WPP normalized JSON>');console.log(JSON.stringify(await applyAmericasWppRegion({project:args.project,normalizedPath:args.normalized}),null,2));}
  catch(error){reportError(error);}
}

import {readFile,writeFile,mkdir,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const sha256=value=>createHash('sha256').update(value).digest('hex');
const readJson=async filename=>JSON.parse(await readFile(path.resolve(filename),'utf8'));

/** Merge existing country depth into the M49 World registry without
 * promoting national Census series to supranational observations. */
export function buildWorldPortfolio(world,americas,wpp,sdg=null,ama=null,weo=null){
  if(world?.analysis?.kind!=='world'||world.country?.id!=='WLD')throw new Error('Expected the validated M49 World dataset');
  if(americas?.analysis?.kind!=='regional'||americas.country?.id!=='AMR')throw new Error('Expected the existing Americas country-depth dataset');
  const rootIds=new Set(world.territories.map(area=>area.id));
  const local=americas.territories.filter(area=>!rootIds.has(area.id));
  if(local.some(area=>!area.country_id||!rootIds.has(area.country_id)))throw new Error('A domestic area has no matching World country identity');
  const localIds=new Set(local.map(area=>area.id));
  const oldWppIds=new Set(americas.indicators.filter(item=>item.id.startsWith('UN_WPP_')).map(item=>item.id));
  const countryRootIds=new Set(world.territories.filter(area=>area.type==='country').map(area=>area.id));
  const sources=new Map(world.sources.map(row=>[row.id,row]));
  for(const source of americas.sources)if(!source.id.startsWith('un-wpp2024-')){
    if(sources.has(source.id)&&JSON.stringify(sources.get(source.id))!==JSON.stringify(source))throw new Error(`Source conflict: ${source.id}`);
    const copy={...source};
    if(copy.geographic_level==='national'&&!copy.country_id){
      const referenced=new Set(americas.documents.filter(row=>row.source_id===copy.id&&countryRootIds.has(row.territory_id)).map(row=>row.territory_id));
      if(referenced.size!==1)throw new Error(`Cannot assign national source ${copy.id} to one documented country`);
      copy.country_id=[...referenced][0];
    }
    sources.set(source.id,copy);
  }
  if(sources.has(wpp.source.id))throw new Error('Duplicate new WPP source');
  sources.set(wpp.source.id,wpp.source);
  for(const pack of [sdg,ama,weo])if(pack){if(sources.has(pack.source.id))throw new Error(`Duplicate international source ${pack.source.id}`);sources.set(pack.source.id,pack.source);}
  const indicators=new Map(world.indicators.map(row=>[row.id,row]));
  for(const indicator of americas.indicators)if(!oldWppIds.has(indicator.id)){
    if(indicators.has(indicator.id)&&JSON.stringify(indicators.get(indicator.id))!==JSON.stringify(indicator))throw new Error(`Indicator conflict: ${indicator.id}`);
    indicators.set(indicator.id,indicator);
  }
  for(const indicator of wpp.indicators)indicators.set(indicator.id,indicator);
  for(const pack of [sdg,ama,weo])for(const indicator of pack?.indicators||[]){if(indicators.has(indicator.id))throw new Error(`Duplicate international indicator ${indicator.id}`);indicators.set(indicator.id,indicator);}
  const observations=[...world.observations,...americas.observations.filter(row=>(localIds.has(row.territory_id)||countryRootIds.has(row.territory_id))&&!oldWppIds.has(row.indicator_id)&&!world.indicators.some(item=>item.id===row.indicator_id)),...wpp.observations,...(sdg?.observations||[]),...(ama?.observations||[]),...(weo?.observations||[])];
  const keys=new Set();
  for(const row of observations){const key=`${row.territory_id}\u001f${row.indicator_id}\u001f${row.period}`;if(keys.has(key))throw new Error(`Duplicate observation ${key}`);keys.add(key);}
  const boundaryMap=new Map(world.boundaries.features.map(feature=>[feature.properties.territory_id,feature]));
  for(const feature of americas.boundaries.features)if(localIds.has(feature.properties.territory_id)||countryRootIds.has(feature.properties.territory_id))boundaryMap.set(feature.properties.territory_id,feature);
  const comparisons=new Map(world.analysis.comparisons.map(row=>[row.parent_id,row]));
  for(const item of americas.analysis.comparisons)if(localIds.has(item.parent_id)||countryRootIds.has(item.parent_id))comparisons.set(item.parent_id,item);
  const countriesWithDepth=new Set(local.map(area=>area.country_id));
  const terminals=new Set([...world.analysis.terminal_territory_ids.filter(id=>!countriesWithDepth.has(id)),...americas.analysis.terminal_territory_ids.filter(id=>localIds.has(id))]);
  const portfolioIds=[...wpp.indicators,...(sdg?.indicators||[]),...(ama?.indicators||[]),...(weo?.indicators||[])].map(item=>item.id);
  const portfolioPeriods=Object.fromEntries([...wpp.indicators.map(item=>[item.id,'2026']),...(sdg?.indicators||[]).map(item=>[item.id,'2024']),...(ama?.indicators||[]).map(item=>[item.id,'2024']),...(weo?.indicators||[]).map(item=>[item.id,'2024'])]);
  const existingCountries=new Set(wpp.observations.filter(row=>countryRootIds.has(row.territory_id)).map(row=>row.territory_id));
  return {
    ...world,
    generated_at:wpp.generated_at,
    territories:[...world.territories,...local],
    indicators:[...indicators.values()],observations,sources:[...sources.values()],
    boundaries:{type:'FeatureCollection',features:[...boundaryMap.values()]},
    documents:americas.documents,
    gaps:[...world.gaps.filter(row=>row.category!=='aggregate_scope'),
      {category:'un_wpp_country_area_coverage',status:'partial',detail:`UN WPP Rev.1 has an exact ISO3 row for ${existingCountries.size} of ${countryRootIds.size} M49 countries/areas. The other records remain in the geography registry without a fabricated value.`,next_action:'Keep missing international cells explicit; do not use a partial country subtotal in place of published UN region values.',source_id:wpp.source.id},
      {category:'domestic_census_coverage',status:'partial',detail:`Existing country-depth evidence has been carried from the Americas edition for ${countriesWithDepth.size} countries/areas. Other domestic Census editions are not yet integrated.`,next_action:'Add verified national and local Census evidence country by country without changing the harmonized supranational portfolio.',source_id:'un-m49'}],
    analysis:{...world.analysis,kind:'world',comparisons:[...comparisons.values()],terminal_territory_ids:[...terminals],
      default_period_by_indicator:{...world.analysis.default_period_by_indicator,...americas.analysis.default_period_by_indicator,...portfolioPeriods},
      supranational_indicator_ids:portfolioIds,population_pyramids:wpp.age_profiles,
      coverage:{scope:'UN M49 World and five regions',country_area_count:countryRootIds.size,un_wpp_country_area_count:existingCountries.size,un_wpp_missing_country_area_ids:[...countryRootIds].filter(id=>!existingCountries.has(id)),census_integrated_country_ids:[...countriesWithDepth]}},
    collection:{...world.collection,status:'partial',adapters:[...new Set([...world.collection.adapters,...americas.collection.adapters,'un-wpp2024-global-rev1',...(sdg?['un-sdg-2026q2-archive']:[]),...(ama?['unsd-ama-2024']:[]),...(weo?['imf-weo-2026-04']:[])])],notes:[...world.collection.notes,'Supra-country diagnostic cards use a separate international portfolio; country-depth Census source data are retained separately.','UN WPP exact world, M49 region/subregion and country rows remain source observations. M49 019 and the custom Central America + Caribbean navigation region use separately labelled same-year sums of disjoint published UN regional count values.',...(sdg?['UN SDG custodian series use exact published geographic rows and explicitly fixed dimensions. Rates are never calculated for custom geographic groups.']:[]),...(ama?['UNSD National Accounts exact M49 world, region and country GDP rows retain their current- or constant-price concept; country GDP per capita values are never averaged.']:[]),...(weo?['IMF WEO inflation retains its published World and country values. Its non-M49 groups are not projected onto UN M49 regions.']:[])]}
  };
}

export async function writeWorldPortfolio({world,americas,wpp,sdg,ama,weo,out}={}){
  const outDir=path.resolve(out||'generated/world-portfolio');
  try{await lstat(outDir);throw new Error(`Output already exists: ${outDir}`);}catch(error){if(error.code!=='ENOENT')throw error;}
  const dataset=buildWorldPortfolio(await readJson(world),await readJson(americas),await readJson(wpp),sdg?await readJson(sdg):null,ama?await readJson(ama):null,weo?await readJson(weo):null);
  const validation=validateDataset(dataset);
  await mkdir(path.join(outDir,'data'),{recursive:true});await mkdir(path.join(outDir,'evidence'),{recursive:true});
  const content=JSON.stringify(dataset)+'\n',hash=sha256(content);
  await writeFile(path.join(outDir,'data','dashboard.json'),content,'utf8');
  await writeFile(path.join(outDir,'evidence','validation.json'),JSON.stringify({...validation,dataset_sha256:hash,checked_at:new Date().toISOString()},null,2)+'\n');
  if(validation.errors.length)throw new Error(`World portfolio validation failed: ${validation.errors.slice(0,20).join('; ')}${validation.errors.length>20?` (+${validation.errors.length-20} more)`:''}`);
  await generateSite({dataset,outDir,canonicalSha256:hash});
  await writeFile(path.join(outDir,'HANDOFF.md'),`# AreaData worldwide international portfolio\n\nUN WPP 2024 Rev.1 supplies world, matching M49 regions and ${dataset.analysis.coverage.un_wpp_country_area_count}/${dataset.analysis.coverage.country_area_count} country/area rows for 2000 and 2023–2026. 2000 and selected-year age-sex profiles are normalized from separate UN male/female five-year age workbooks. ${sdg?`${(await readJson(sdg)).indicators.length} fixed-slice series are drawn from the official 2026 Q2.2 SDG archive; custodian agencies are recorded per observation. `:''}${ama?'UNSD AMA supplies published GDP and per-capita GDP rows. ':''}${weo?'IMF WEO supplies World and country inflation; other WEO group definitions are not mapped to UN M49 regions. ':''}Missing area-series cells remain uncollected.\n\nThe browser receives international observations and age profiles in data/supranational.json. Domestic Census country-depth evidence is in data/countries/*.json. Canonical data/dashboard.json retains source identity, provenance and records for audit.\n`);
  console.log(`Created ${outDir}: ${dataset.territories.length} territories; ${dataset.analysis.supranational_indicator_ids.length} international indicators; ${dataset.observations.length} observations`);
  return {outDir,dataset,validation};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['world','americas','wpp','sdg','ama','weo','out']);if(!args.world||!args.americas||!args.wpp)throw new Error('Use --world file --americas file --wpp file [--sdg file] [--ama file] [--weo file] --out new-directory');await writeWorldPortfolio(args);}catch(error){reportError(error);}
}

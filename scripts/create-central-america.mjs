import {mkdir,lstat,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {collectWorld} from '../lib/collect-world.mjs';
import {buildRegionalPilot,buildCensusPilotPreflight,renderCensusPilotPreflight} from '../lib/regional-pilot.mjs';
import {loadNormalizedCensus,mergeCensusPilot,updateCensusPreflight,renderCensusAdapterAudit} from '../lib/census-pilot-adapter.mjs';
import {loadCensusHistory,mergeCensusHistory} from '../lib/census-history-adapter.mjs';
import {loadNormalizedUnPopulation,mergeUnPopulation} from '../lib/un-population-adapter.mjs';
import {loadSourceCatalog} from '../lib/source-catalog.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {readTemplateReference} from './create-country.mjs';
import {attachWorldCensusListings,loadBundledWorldCensusListings} from '../lib/world-census-preflight.mjs';

export async function createCentralAmerica({out,sourceDir,censusData,censusHistoryData,unPopulationData}={}) {
  if(!sourceDir)throw new Error('--source-dir must point to a verified world raw archive.');
  const outDir=path.resolve(out||'generated/central-america');
  try{await lstat(outDir);throw new Error(`Output already exists; choose a new directory: ${outDir}`);}catch(error){if(error.code!=='ENOENT')throw error;}
  await mkdir(path.join(outDir,'raw'),{recursive:true});
  try{
    const world=await collectWorld({rawDir:path.join(outDir,'raw'),sourceDir:path.resolve(sourceDir),onProgress:message=>console.log(message)});
    const normalized=censusData?await loadNormalizedCensus(path.resolve(censusData)):null;
    const censusHistory=censusHistoryData?await loadCensusHistory(path.resolve(censusHistoryData)):null;
    const normalizedUn=unPopulationData?await loadNormalizedUnPopulation(path.resolve(unPopulationData)):null;
    let dataset=normalized?mergeCensusPilot(buildRegionalPilot(world),normalized):buildRegionalPilot(world);
    if(censusHistory){
      const countryIds=new Set(world.territories.filter(area=>area.level==='country').map(area=>area.id));
      const referenceBoundaries={type:'FeatureCollection',features:(world.boundaries?.features||[]).filter(feature=>countryIds.has(feature.properties?.territory_id))};
      dataset=mergeCensusHistory(dataset,censusHistory,referenceBoundaries);
    }
    if(normalizedUn)dataset=mergeUnPopulation(dataset,normalizedUn);
    dataset=attachWorldCensusListings(dataset,await loadBundledWorldCensusListings());
    const validation=validateDataset(dataset),content=JSON.stringify(dataset,null,2)+'\n';
    const censusPlan=normalized?updateCensusPreflight(buildCensusPilotPreflight(await loadSourceCatalog()),normalized):buildCensusPilotPreflight(await loadSourceCatalog());
    await mkdir(path.join(outDir,'data'));await mkdir(path.join(outDir,'evidence'));
    await writeFile(path.join(outDir,'data/dashboard.json'),content);
    await writeFile(path.join(outDir,'evidence/validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/CENSUS_SOURCE_PREFLIGHT.json'),JSON.stringify(censusPlan,null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/CENSUS_SOURCE_PREFLIGHT.md'),renderCensusPilotPreflight(censusPlan));
    if(normalized){await writeFile(path.join(outDir,'evidence/CENSUS_NORMALIZATION.json'),JSON.stringify(normalized,null,2)+'\n');await writeFile(path.join(outDir,'evidence/CENSUS_ADAPTER_AUDIT.md'),renderCensusAdapterAudit(normalized));}
    if(censusHistory)await writeFile(path.join(outDir,'evidence/CENSUS_HISTORY.json'),JSON.stringify(censusHistory,null,2)+'\n');
    if(normalizedUn)await writeFile(path.join(outDir,'evidence/UN_WPP_POPULATION_NORMALIZATION.json'),JSON.stringify(normalizedUn,null,2)+'\n');
    if(validation.errors.length)throw new Error(`Central America pilot failed validation: ${validation.errors.join('; ')}`);
    await generateSite({dataset,outDir});
    await writeFile(path.join(outDir,'TEMPLATE_REFERENCE.json'),JSON.stringify(await readTemplateReference(),null,2)+'\n');
    await writeFile(path.join(outDir,'AREADATA_ARCHITECTURE.md'),await readFile(new URL('../docs/AREADATA_ARCHITECTURE.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'CENSUS_SERIES_CONTRACT.md'),await readFile(new URL('../docs/CENSUS_SERIES_CONTRACT.md',import.meta.url),'utf8'));
    const censusHandoff=normalized
      ? normalized.summary.countries_pending.length
        ? `Census population is integrated for ${normalized.summary.countries_acquired.join(', ')}; ${normalized.summary.countries_pending.join(', ')} remain pending, so no regional census total is claimed.`
        : `Census population is integrated for all seven countries. The displayed mixed-reference-year regional total is ${new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(normalized.summary.regional_total)} people; its country years are ${Object.entries(normalized.summary.regional_total_component_periods).map(([id,period])=>`${id} ${period}`).join(', ')}. It is calculated from exact national observations, not from lower-area sums; source precision remains in the data files.`
      : 'The current generated values are a separate international-reference scaffold until the census source preflight is acquired, matched and accepted.';
    const unHandoff=normalizedUn?` UN WPP 2024 Rev.1 is displayed as a separate same-period context series: ${normalizedUn.summary.default_display_period} medium projection ${new Intl.NumberFormat('en-US').format(normalizedUn.summary.regional_totals[normalizedUn.summary.default_display_period])} people.`:'';
    await writeFile(path.join(outDir,'HANDOFF.md'),`# AreaData Central America pilot\n\nThis runtime covers the seven-country Central America pilot: Belize, Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica and Panama. Official census data are the primary intended series. ${censusHandoff}${unHandoff} Country-specific source exceptions remain in evidence/CENSUS_ADAPTER_AUDIT.md. Different census years are permitted only with every country year shown; missing country coverage never becomes a regional total.\n`);
    console.log(`Created: ${outDir}`);return {outDir,dataset,validation};
  }catch(error){await writeFile(path.join(outDir,'COLLECTION_FAILED.txt'),`${new Date().toISOString()}\n${error.message}\n`);throw error;}
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['out','source-dir','census-data','census-history-data','un-population-data']);if(args.help)console.log('node scripts/create-central-america.mjs --source-dir previous-world/raw --census-data acquisition/normalized-census.json --census-history-data data/census/central-america-census-history-v0.9.json --un-population-data data/international/un-wpp2024-central-america-population.json --out generated/central-america');else await createCentralAmerica({out:args.out,sourceDir:args['source-dir'],censusData:args['census-data'],censusHistoryData:args['census-history-data'],unPopulationData:args['un-population-data']});}catch(error){reportError(error);}
}

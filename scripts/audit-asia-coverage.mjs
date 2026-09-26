import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const hash=content=>createHash('sha256').update(content).digest('hex');
const csv=value=>`"${String(value??'').replaceAll('"','""')}"`;
const latest=rows=>rows.sort((a,b)=>String(b.period).localeCompare(String(a.period),'en',{numeric:true}))[0]||null;

export async function auditAsiaCoverage(project){
  const root=path.resolve(project),bytes=await readFile(path.join(root,'data/dashboard.json'));
  const data=JSON.parse(bytes.toString('utf8'));
  if(data.country?.id!=='ASI'||data.country?.national_territory_id!=='M49:142')throw new Error('Expected an Asia scope dataset');
  const countries=data.territories.filter(area=>area.type==='country');
  const subregions=data.territories.filter(area=>area.parent_id==='M49:142');
  const international=new Set(data.analysis?.supranational_indicator_ids||[]);
  const indicators=data.indicators;
  const observations=data.observations.filter(row=>row.status==='observed'&&Number.isFinite(row.value));
  const byKey=new Map();
  for(const row of observations){const key=`${row.territory_id}\u001f${row.indicator_id}`;if(!byKey.has(key))byKey.set(key,[]);byKey.get(key).push(row);}
  const latestFor=(areaId,id)=>latest([...(byKey.get(`${areaId}\u001f${id}`)||[])]);
  const indicatorCoverage=indicators.map(indicator=>{
    const countryRows=countries.map(area=>({area,observation:latestFor(area.id,indicator.id)}));
    const subregionRows=subregions.map(area=>({area,observation:latestFor(area.id,indicator.id)}));
    return {indicator_id:indicator.id,theme:indicator.theme,unit:indicator.unit,
      countries_with_value:countryRows.filter(row=>row.observation).length,
      countries_missing_value:countryRows.filter(row=>!row.observation).map(row=>row.area.id),
      subregions_with_source_value:subregionRows.filter(row=>row.observation).map(row=>({id:row.area.id,period:row.observation.period,source_id:row.observation.source_id})),
      asia_source_value:latestFor('M49:142',indicator.id)?{period:latestFor('M49:142',indicator.id).period,source_id:latestFor('M49:142',indicator.id).source_id}:null};
  });
  const preflight=new Map((data.analysis?.census_source_preflight?.records||[]).map(row=>[row.country_id,row]));
  const countryRows=countries.map(area=>{
    const included=observations.filter(row=>row.territory_id===area.id);
    const source=preflight.get(area.id);
    return {country_id:area.id,name:area.name,subregion_id:area.parent_id,
      indicators_with_value:new Set(included.map(row=>row.indicator_id)).size,
      international_indicators_with_value:new Set(included.filter(row=>international.has(row.indicator_id)).map(row=>row.indicator_id)).size,
      wpp_population_latest_year:latestFor(area.id,'UN_WPP_POP_TOTAL')?.period||null,
      census_preflight_listed_year:source?.latest_un_census_listing?.date_text||null,
      census_preflight_link_status:source?.latest_un_census_linked_listing?.link_status||null,
      domestic_branch:data.analysis?.coverage?.census_integrated_country_ids?.includes(area.id)||false};
  });
  const report={scope_id:'M49:142',dataset_sha256:hash(bytes),data_edition:data.generated_at,
    country_area_count:countries.length,subregion_ids:subregions.map(area=>area.id),
    indicator_count:indicators.length,international_indicator_count:international.size,
    census_preflight_record_count:countryRows.filter(row=>preflight.has(row.country_id)).length,
    domestic_branch_country_count:countryRows.filter(row=>row.domestic_branch).length,
    interpretation:'An international country value is not a completed domestic census edition. A catalogue date or link is not acquired or adopted data. A missing source-reported region value is not replaced by a partial subtotal or an average of country rates.',
    indicator_coverage:indicatorCoverage,countries:countryRows};
  await writeFile(path.join(root,'evidence/ASIA_COVERAGE.json'),JSON.stringify(report,null,2)+'\n');
  const headers=['country_id','name','subregion_id','indicators_with_value','international_indicators_with_value','wpp_population_latest_year','census_preflight_listed_year','census_preflight_link_status','domestic_branch'];
  await writeFile(path.join(root,'evidence/ASIA_COUNTRY_COVERAGE.csv'),[headers.map(csv).join(','),...countryRows.map(row=>headers.map(key=>csv(row[key])).join(','))].join('\n')+'\n');
  return report;
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(!args.project)throw new Error('Use --project <Asia project>');
    const result=await auditAsiaCoverage(args.project);
    console.log(`Audited ${result.country_area_count} countries/areas and ${result.international_indicator_count} international indicators; ${result.domestic_branch_country_count} domestic branches`);
  }catch(error){reportError(error);}
}

import {readFile} from 'node:fs/promises';
import {CENTRAL_AMERICA_CONFIG} from './regional-pilot.mjs';

const finite=value=>typeof value==='number'&&Number.isFinite(value);

export async function loadNormalizedUnPopulation(file){
  const data=JSON.parse(await readFile(file,'utf8'));validateNormalizedUnPopulation(data);return data;
}

export function validateNormalizedUnPopulation(data,config=CENTRAL_AMERICA_CONFIG){
  if(data?.schema_version!=='1.0'||data.scope_id!==config.id)throw new Error('UN population scope or schema mismatch');
  if(data.indicator?.id!=='UN_WPP_POP_TOTAL'||data.indicator.series_family!=='international_reference'||data.indicator.period_policy!=='same_period'||data.indicator.aggregation!=='sum')throw new Error('UN population indicator contract is invalid');
  if(!data.source?.id||data.indicator.source_id!==data.source.id||!/^https:\/\//.test(data.source.url||'')||!data.source.sha256)throw new Error('UN population source metadata is incomplete');
  const periods=data.summary?.periods||[],expected=new Set(config.member_ids.flatMap(id=>periods.map(period=>`${id}|${period}`))),seen=new Set();
  for(const row of data.observations||[]){
    const key=`${row.territory_id}|${row.period}`;
    if(!expected.has(key)||seen.has(key)||row.indicator_id!==data.indicator.id||row.source_id!==data.source.id||row.status!=='observed'||!finite(row.value))throw new Error(`Invalid UN population observation: ${key}`);
    if(row.series_stage!==(String(row.period)==='2023'?'estimate':'medium_projection'))throw new Error(`Invalid UN population stage: ${key}`);
    seen.add(key);
  }
  if(seen.size!==expected.size)throw new Error(`UN population coverage is incomplete: ${seen.size} of ${expected.size}`);
  for(const period of periods){const expectedStage=period==='2023'?'estimate':'medium_projection';if(data.indicator.series_stage_by_period?.[period]!==expectedStage)throw new Error(`UN population indicator stage is invalid: ${period}`);}
  for(const period of periods){
    const total=data.observations.filter(row=>row.period===period).reduce((sum,row)=>sum+row.value,0);
    if(total!==data.summary.regional_totals?.[period])throw new Error(`UN population total mismatch: ${period}`);
  }
  if(!periods.includes(data.summary.default_display_period))throw new Error('UN population default period is unavailable');
  return data;
}

export function mergeUnPopulation(dataset,normalized,config=CENTRAL_AMERICA_CONFIG){
  validateNormalizedUnPopulation(normalized,config);
  const result=structuredClone(dataset),oldId=normalized.replaces_indicator_id;
  const oldSourceIds=new Set(result.indicators.filter(indicator=>indicator.id===oldId).map(indicator=>indicator.source_id));
  result.indicators=result.indicators.filter(indicator=>indicator.id!==oldId);
  result.observations=result.observations.filter(row=>row.indicator_id!==oldId);
  result.analysis.aggregation.rules=result.analysis.aggregation.rules.filter(rule=>rule.indicator_id!==oldId);
  delete result.analysis.default_period_by_indicator[oldId];
  result.gaps=result.gaps.filter(gap=>!(gap.category==='indicator_coverage'&&oldSourceIds.has(gap.source_id)));
  const remainingSourceIds=new Set([
    ...result.indicators.map(indicator=>indicator.source_id),...result.observations.map(row=>row.source_id),...result.documents.map(document=>document.source_id),...result.gaps.map(gap=>gap.source_id),
    ...(result.boundaries?.features||[]).map(feature=>feature.properties?.source_id),...result.analysis.comparisons.flatMap(comparison=>comparison.source_ids||[])
  ].filter(Boolean));
  result.sources=result.sources.filter(source=>!oldSourceIds.has(source.id)||remainingSourceIds.has(source.id));
  if(result.indicators.some(indicator=>indicator.id===normalized.indicator.id)||result.sources.some(source=>source.id===normalized.source.id))throw new Error('UN population series collides with an existing dataset record');
  const insertAfter=result.indicators.findIndex(indicator=>indicator.series_family==='census');
  result.indicators.splice(insertAfter<0?0:insertAfter+1,0,structuredClone(normalized.indicator));
  result.sources.push(structuredClone(normalized.source));
  result.observations.push(...normalized.observations.map(row=>structuredClone(row)));
  for(const period of normalized.summary.periods)result.observations.push({territory_id:config.id,indicator_id:normalized.indicator.id,period,value:null,status:'missing',source_id:normalized.source.id,series_stage:period==='2023'?'estimate':'medium_projection',footnote:'No source-published seven-country value. AreaData calculates it only from the complete, non-overlapping seven-country UN WPP cover.'});
  result.analysis.aggregation.rules.push({indicator_id:normalized.indicator.id,method:'sum',completeness:'full_cover',period_policy:'same_period',label:'AreaData calculated UN population context',note:'Sum the seven exact country observations for the same UN WPP period and variant. Never mix estimate and projection periods or use lower-area census rows.'});
  result.analysis.default_period_by_indicator[normalized.indicator.id]=normalized.summary.default_display_period;
  result.analysis.population_context={primary_indicator_id:'CENSUS_POP_TOTAL',reference_indicator_id:normalized.indicator.id,reference_period:normalized.summary.default_display_period,label:'UN WPP 2024 Rev.1 medium projection',note:'The difference reflects reference year and method; it is not an error margin.'};
  result.gaps.unshift({category:'un_population_context',status:'ready',detail:`UN WPP 2024 Rev.1 provides a complete seven-country same-period population series. The ${normalized.summary.default_display_period} medium projection totals ${new Intl.NumberFormat('en-US').format(normalized.summary.regional_totals[normalized.summary.default_display_period])} people.`,next_action:'Keep the UN estimate/projection separate from official census observations and label the scenario and year in every screen and export.',source_id:normalized.source.id});
  result.collection.adapters.push('un-wpp2024-central-america-population-v1');
  result.collection.notes.push(`UN WPP 2024 Rev.1 population context covers ${normalized.summary.periods.join(', ')}; 2023 is an estimate and 2024-2026 are medium-variant projections. This series does not replace country census observations.`);
  return result;
}

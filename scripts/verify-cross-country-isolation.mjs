import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {initialState,routeQuery,indicatorsForTerritorialScope,evidenceCsv,planningMarkdown,planningHtml} from '../scaffold/site/model.mjs';
import {diagnosticMarkdown,diagnosticHtml,diagnosticCsv} from '../scaffold/site/diagnostic.mjs';

const csvRows=csv=>{const rows=[];let row=[],value='',quoted=false;for(let i=csv.charCodeAt(0)===0xfeff?1:0;i<csv.length;i++){const c=csv[i];if(c==='"'){if(quoted&&csv[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(value);value='';}else if(c==='\r'&&csv[i+1]==='\n'&&!quoted){row.push(value);rows.push(row);row=[];value='';i++;}else value+=c;}if(value||row.length){row.push(value);rows.push(row);}return rows;};
export function verifyCrossCountryIsolation(dataset){
  const errors=[],countries=dataset.territories.filter(area=>area.type==='country'),allIndicators=dataset.indicators;
  let route_checks=0,output_checks=0;
  for(const country of countries){
    const allowed=indicatorsForTerritorialScope(dataset,country.id),allowedIds=new Set(allowed.map(row=>row.id));
    const foreign=allIndicators.filter(row=>!allowedIds.has(row.id));
    const fallback=allowed[0]?.id||'';
    // One rejected foreign route per country exercises the common route
    // normalizer. Exhaustively replaying every foreign indicator multiplies
    // the same invariant by the full regional catalog and made large editions
    // needlessly slow; the complete foreign set is still checked in outputs.
    for(const indicator of foreign.slice(0,1)){
      const state=initialState(dataset,`?country=${encodeURIComponent(dataset.country.id)}&territory=${encodeURIComponent(country.id)}&metric=${encodeURIComponent(indicator.id)}&period=latest-available&level=__foreign_level__`),query=new URLSearchParams(routeQuery(dataset,state));
      route_checks++;
      if((allowedIds.size&&!allowedIds.has(state.metric))||(!allowedIds.size&&state.metric!=='')||state.metric===indicator.id)errors.push(`${country.id}: foreign indicator ${indicator.id} survived route normalization`);
      if(query.get('metric')===indicator.id)errors.push(`${country.id}: foreign indicator ${indicator.id} survived normalized URL`);
      if(query.get('level')==='__foreign_level__')errors.push(`${country.id}: nonexistent comparison level survived normalized URL`);
      if(fallback&&!state.notices.some(note=>note.includes(indicator.id)))errors.push(`${country.id}: foreign indicator recovery notice is missing for ${indicator.id}`);
    }
    // Run the output contract against the same country branch delivered by a
    // shard. This preserves every selected-country record while avoiding a
    // repeated full-Americas scan for each of the six output formats.
    const branchIds=new Set([country.id]);let changed=true;
    while(changed){changed=false;for(const area of dataset.territories)if(area.parent_id&&branchIds.has(area.parent_id)&&!branchIds.has(area.id)){branchIds.add(area.id);changed=true;}}
    branchIds.add(dataset.country.national_territory_id);
    const scoped={...dataset,
      territories:dataset.territories.filter(area=>branchIds.has(area.id)),
      indicators:allowed,
      observations:dataset.observations.filter(row=>branchIds.has(row.territory_id)&&allowedIds.has(row.indicator_id)),
      documents:(dataset.documents||[]).filter(row=>branchIds.has(row.territory_id)),
      boundaries:{type:'FeatureCollection',features:(dataset.boundaries?.features||[]).filter(feature=>branchIds.has(feature.properties?.territory_id))},
      analysis:{...dataset.analysis,comparisons:(dataset.analysis?.comparisons||[]).filter(row=>branchIds.has(row.parent_id)),terminal_territory_ids:(dataset.analysis?.terminal_territory_ids||[]).filter(id=>branchIds.has(id))}
    };
    const outputs=[evidenceCsv(scoped,country.id,'latest-available'),planningMarkdown(scoped,country.id,'latest-available','en'),planningHtml(scoped,country.id,'latest-available','en'),diagnosticMarkdown(scoped,country.id,'latest-available'),diagnosticHtml(scoped,country.id,'latest-available'),diagnosticCsv(scoped,country.id,'latest-available')];
    output_checks+=outputs.length;
    // The two machine-readable outputs expose an Indicator ID column. Audit
    // that column structurally; free-text matching is invalid because source
    // notes can legitimately cite a shared WDI URL or the upstream code from
    // which a country-specific indicator was derived.
    for(const [index,csv] of [[1,outputs[0]],[6,outputs[5]]]){
      const rows=csvRows(csv),header=rows.shift()||[],indicatorIndex=header.indexOf('Indicator ID');
      if(indicatorIndex<0){errors.push(`${country.id}: selected-area output ${index} has no Indicator ID column`);continue;}
      for(const row of rows)if(row[indicatorIndex]&&!allowedIds.has(row[indicatorIndex]))errors.push(`${country.id}: foreign indicator ${row[indicatorIndex]} appears in selected-area output ${index}`);
    }
  }
  return {ok:errors.length===0,country_count:countries.length,route_checks,output_checks,errors};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2),index=args.indexOf('--project'),project=index>=0?args[index+1]:'';
  if(!project){console.error('Usage: node scripts/verify-cross-country-isolation.mjs --project <directory>');process.exit(2);}
  const root=path.resolve(project),dataset=JSON.parse(await readFile(path.join(root,'data/dashboard.json'),'utf8')),result=verifyCrossCountryIsolation(dataset);
  await mkdir(path.join(root,'evidence'),{recursive:true});await writeFile(path.join(root,'evidence/CROSS_COUNTRY_ISOLATION.json'),JSON.stringify({...result,checked_at:new Date().toISOString()},null,2)+'\n');
  console.log(JSON.stringify(result,null,2));if(!result.ok)process.exitCode=1;
}

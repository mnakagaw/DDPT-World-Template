import {escapeHtml as e, effectivePeriodForIndicator, areaObservationState} from './model.mjs';

const n=value=>typeof value==='number'&&Number.isFinite(value)?value:0;
const group=(en,es,ja,language)=>language==='ja'?ja:language==='es'?es:en;

function pyramidSvg(profile,max,baseline,language){
  const ages=profile.ages,rows=ages.map((age,index)=>{
    const y=27+(ages.length-1-index)*20,male=n(profile.male[index]),female=n(profile.female[index]);
    const mw=Math.max(0,Math.round(male/max*196)),fw=Math.max(0,Math.round(female/max*196));
    return `<g><rect x="${218-mw}" y="${y}" width="${mw}" height="15" class="${baseline?'pyramid-past':'pyramid-male'}"><title>${e(age)} · ${e(group('Male','Hombres','男性',language))}: ${male.toLocaleString()}</title></rect><rect x="282" y="${y}" width="${fw}" height="15" class="${baseline?'pyramid-past-light':'pyramid-female'}"><title>${e(age)} · ${e(group('Female','Mujeres','女性',language))}: ${female.toLocaleString()}</title></rect><text x="250" y="${y+12}" text-anchor="middle">${e(age)}</text></g>`;
  }).join('');
  return `<svg viewBox="0 0 500 485" role="img" aria-label="${e(group('Population pyramid','Pirámide de población','人口ピラミッド',language))} ${e(profile.period)}"><line x1="218" x2="218" y1="23" y2="458" class="pyramid-axis"/><line x1="282" x2="282" y1="23" y2="458" class="pyramid-axis"/><text x="120" y="17" text-anchor="middle">${e(group('Male','Hombres','男性',language))}</text><text x="380" y="17" text-anchor="middle">${e(group('Female','Mujeres','女性',language))}</text>${rows}</svg>`;
}

export function renderCensusPyramid(dataset,areaId,language='en'){
  const profiles=dataset.analysis?.census_population_pyramids;
  const profileKey=Object.keys(profiles||{}).filter(key=>key.startsWith(`${areaId}@`)).sort((a,b)=>Number(b.split('@').at(-1))-Number(a.split('@').at(-1)))[0];
  const profile=profiles?.[profileKey];
  if(!profile||!Array.isArray(profile.ages)||profile.ages.length!==profile.male?.length||profile.ages.length!==profile.female?.length)return '';
  const area=dataset.territories.find(row=>row.id===areaId);
  const source=dataset.sources.find(row=>row.id===profile.source_id);
  const max=Math.max(...profile.male,...profile.female);
  const male=profile.male.reduce((sum,value)=>sum+n(value),0),female=profile.female.reduce((sum,value)=>sum+n(value),0);
  const sourceLink=source?.url?`<a href="${e(source.url)}" target="_blank" rel="noopener noreferrer">${e(group('Source table','Tabla fuente','出典表',language))}</a>`:'';
  return `<section class="panel un-demographics census-demographics"><div class="un-demographics-heading"><div><p class="eyebrow">${e(source?.name||'Census')} · ${e(group('AGE AND SEX STRUCTURE','ESTRUCTURA POR EDAD Y SEXO','年齢・男女別構成',language))}</p><h2>${e(group('Population pyramid','Pirámide de población','人口ピラミッド',language))} — ${e(area?.name||dataset.country.name)}</h2></div><strong>${e(profile.period)}</strong></div><div class="pyramid-grid census-pyramid-grid"><figure><figcaption>${e(group('Census resident population','Población residente censal','国勢調査の常住人口',language))}<small>${e(group('Male','Hombres','男性',language))}: ${male.toLocaleString()} · ${e(group('Female','Mujeres','女性',language))}: ${female.toLocaleString()}</small></figcaption>${pyramidSvg(profile,max,false,language)}</figure></div><p class="small-note">${e(group(`Five-year age groups use published ${profile.period} census counts for this area. No lower-area profile is inferred.`,`Los grupos quinquenales usan recuentos censales publicados para ${profile.period}; no se infiere el perfil de áreas menores.`,`${profile.period}年国勢調査の公表値を5歳階級で表示しています。下位地域の値は推定していません。`,language))} ${sourceLink}</p></section>`;
}

export function renderWppDemographics(dataset,areaId,requestedPeriod,language='en'){
  const profiles=dataset.analysis?.population_pyramids;
  if(!profiles)return '';
  const period=effectivePeriodForIndicator(dataset,'UN_WPP_POP_TOTAL',requestedPeriod);
  const current=profiles[`${areaId}@${period}`],past=profiles[`${areaId}@2000`];
  if(!current||!past)return '';
  const male=areaObservationState(dataset,areaId,'UN_WPP_POP_MALE',period);
  const female=areaObservationState(dataset,areaId,'UN_WPP_POP_FEMALE',period);
  if(!Number.isFinite(male.value)||!Number.isFinite(female.value))return '';
  const total=male.value+female.value,share=male.value/total*100;
  const max=Math.max(...current.male,...current.female,...past.male,...past.female);
  const source=dataset.sources.find(row=>row.id==='un-wpp2024-global-rev1');
  const stage=Number(period)>2023?group('UN medium projection','Proyección media ONU','国連中位推計',language):group('UN estimate','Estimación ONU','国連推計',language);
  const calculated=profile=>profile.provenance==='areadata_calculated';
  const method=calculated(current)||calculated(past)?group('AreaData calculated the selected region from complete, non-overlapping UN regional age counts.','AreaData calculó la región seleccionada con recuentos de edad regionales de la ONU completos y sin solapamiento.','選択した広域は、重複しない国連の地域別年齢人口をAreaDataが合計した値です。',language):'';
  return `<section class="panel un-demographics" aria-labelledby="un-demographics-title"><div class="un-demographics-heading"><div><p class="eyebrow">UN WORLD POPULATION PROSPECTS 2024</p><h2 id="un-demographics-title">${e(group('Population by age and sex','Población por edad y sexo','年齢・男女別人口',language))}</h2></div><small>${e(group('2000 estimate compared with the selected year','Estimación de 2000 comparada con el año seleccionado','2000年の推計値と選択年を比較',language))}</small></div><div class="pyramid-grid"><figure class="pyramid-old"><figcaption>2000 <small>${e(group('UN estimate','Estimación ONU','国連推計',language))}${calculated(past)?` · ${e(group('AreaData sum','Suma de AreaData','AreaData合計',language))}`:''}</small></figcaption>${pyramidSvg(past,max,true,language)}</figure><figure><figcaption>${e(period)} <small>${e(stage)}${calculated(current)?` · ${e(group('AreaData sum','Suma de AreaData','AreaData合計',language))}`:''}</small></figcaption>${pyramidSvg(current,max,false,language)}</figure></div><div class="sex-composition"><svg viewBox="0 0 120 120" role="img" aria-label="${e(group('Male','Hombres','男性',language))} ${share.toFixed(1)}%; ${e(group('Female','Mujeres','女性',language))} ${(100-share).toFixed(1)}%"><circle cx="60" cy="60" r="44" class="sex-pie-base"/><circle cx="60" cy="60" r="44" class="sex-pie-male" stroke-dasharray="${(share/100*276.46).toFixed(2)} 276.46" transform="rotate(-90 60 60)"/></svg><div><h3>${e(group('Sex composition','Composición por sexo','男女の構成比',language))} · ${e(period)}</h3><p><i class="sex-key male"></i>${e(group('Male','Hombres','男性',language))} <strong>${male.value.toLocaleString()} (${share.toFixed(1)}%)</strong></p><p><i class="sex-key female"></i>${e(group('Female','Mujeres','女性',language))} <strong>${female.value.toLocaleString()} (${(100-share).toFixed(1)}%)</strong></p><small>${e(group('The two pyramids use the same horizontal scale. Counts are UN estimates/projections, not census enumeration.','Ambas pirámides usan la misma escala horizontal. Son estimaciones/proyecciones ONU, no recuentos censales.','2つのピラミッドは同じ横軸尺度です。国勢調査の実査数ではなく国連推計・将来推計です。',language))} ${e(method)} ${source?.url?`<a href="${e(source.url)}" target="_blank" rel="noopener noreferrer">${e(group('Source','Fuente','出典',language))}</a>`:''}</small></div></div></section>`;
}

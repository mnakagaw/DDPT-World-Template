import {
  finite, escapeHtml as e, safeUrl, displayValue, statusLabel, sourceFor,
  periodsFor, observationState, areaObservationState, effectivePeriodForIndicator, territorialIndicatorState, localLevels, levelLabel, nationalOnly, initialState,
  selectTerritory, territoryLineage, territoryOptionLabel, hierarchyControls, selectHierarchyOption, routeQuery, countryDiagnosticUrl, comparisonLevelForArea, comparisonRows, comparisonCompatibility, rankedRows, searchRows, rankingReveal, rankingScrollTop, distribution,
  seriesFor, observedValue, makeCsv, evidenceCsv, safeFilename, planningMarkdown,
  planningHtml, documentsCsv, mapGeometry, seriesGeometry
} from './model.mjs';
import {planningSettings,planningDocuments,documentGroups,documentPeriod,officialMapState,hasDocumentReference,selectedGaps,relatedResourceUrl,categoryLabels} from './planning.mjs';
import {renderDocumentGroups,renderDocument} from './planning-view.mjs';
import {comparisonSet,observationMeaning,observationContext,isTerminalTerritory} from './analysis.mjs';
import {renderInternalComparison,diagnosticMarkdown,diagnosticHtml,diagnosticCsv,renderSourceAttribution,seriesSourceLabel} from './diagnostic.mjs';
import {resolveLanguage,languageLocale,translateInterface,translateText,SUPPORTED_LANGUAGES} from './i18n.mjs';
import {censusAge,censusRecencyClass,censusIntervals} from './census-history.mjs';

const base = new URL('../', import.meta.url);
const app = document.getElementById('app');
const page = document.body.dataset.page || 'home';
const pageNames = {home:'Explore',territorial:'Territorial diagnostic',thematic:'Thematic diagnostic',database:'Database',planning:'Planning and resources'};
const storedLanguage=()=>{try{return localStorage.getItem('areadata-language')||'';}catch{return '';}};
let language=resolveLanguage({query:new URLSearchParams(location.search).get('lang'),stored:storedLanguage(),browserLanguages:navigator.languages||[navigator.language]});
let dataset, state, updateStatus;
let areaSearch='', rankSearch='', rankOrder='desc', wholeMap=false, allAreaOpen=false, comparisonFocusId='';
const fmt = (value,indicator=currentMetric()) => displayValue(value,languageLocale(language),indicator?.display_decimals ?? 2);
const areaFor = id => dataset.territories.find(area => area.id === id);
const metricFor = id => dataset.indicators.find(indicator => indicator.id === id);
const currentArea = () => areaFor(state.selected);
const currentMetric = () => metricFor(state.metric);
const worldMode = () => ['world','regional'].includes(dataset?.analysis?.kind);
const displayAreaName = area => area?.id===dataset.country.national_territory_id && dataset.analysis?.pilot?.stage==='central_america_7' ? 'Central America (7 countries)' : area?.name;
const link = (url, label, classes='') => safeUrl(url) ? `<a class="${e(classes)}" href="${e(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${e(label)}<span class="sr-only"> (opens a new tab)</span></a>` : `<span>${e(label)} · No verified link</span>`;
const button = (action, label, attributes='', classes='button secondary') => `<button type="button" class="${classes}" data-action="${action}" ${attributes}>${label}</button>`;
const routeWithLanguage=(next=state)=>{const query=new URLSearchParams(routeQuery(dataset,next));query.set('lang',language);return query.toString();};
const pageUrl = target => {const url = new URL(target==='home' ? './' : `${target}/`,base);url.search=routeWithLanguage();return url.href;};
const pageLink = (target, label, classes='button secondary') => `<a class="${classes}" href="${e(pageUrl(target))}">${e(label)}</a>`;
const localCopy=(en,es,ja)=>language==='ja'?ja:language==='es'?es:en;
const REGIONAL_GAP_COPY={
  americas_regional_observation:{
    category:['Americas regional observation','Observación regional de las Américas','アメリカ大陸全体の観測値'],
    detail:['No exact source-reported observation for the full UN M49 Americas scope has been adopted. Country values remain visible, but they are not silently summed into an Americas value.','No se ha adoptado una observación publicada por la fuente para todo el ámbito de las Américas de UN M49. Los valores nacionales siguen visibles, pero no se suman silenciosamente como valor continental.','UN M49アメリカ大陸全体と同じ範囲の出典公表値は採用していません。各国値は表示しますが、アメリカ大陸値として無断で合計しません。'],
    next:['Acquire an exact-scope official regional series, or approve a complete non-overlapping aggregation rule with every component and period exposed.','Adquirir una serie regional oficial del mismo ámbito o aprobar una regla de agregación completa y sin solapamiento que muestre todos los componentes y períodos.','同一範囲の公式地域系列を取得するか、全構成地域と期間を示す完全・非重複の集計規則を承認する。']
  },
  census_country_coverage:{
    category:['Census country coverage','Cobertura censal por país','国別Censusの収録範囲'],
    detail:['Official census population and domestic hierarchy are integrated for 7 of 57 UN M49 countries/areas in this Americas scope. Unintegrated does not mean that a census does not exist.','La población censal oficial y la jerarquía interna están integradas para 7 de las 57 entradas UN M49 de este ámbito. No integrado no significa que no exista un censo.','この範囲のUN M49 57件中7件で公式Census人口と国内階層を統合しています。未統合はCensusが存在しないという意味ではありません。'],
    next:['Use the country adapter workflow to inventory official census tables, codes, compatible boundaries and recent census rounds for each remaining country or area.','Usar el flujo del adaptador nacional para inventariar tablas censales oficiales, códigos, límites compatibles y rondas recientes de cada país o área restante.','残る国・地域ごとに国別アダプターを使い、公式Census表、コード、対応可能な境界、直近の調査を棚卸しする。']
  },
  boundary_reconciliation:{
    category:['Boundary reconciliation','Conciliación de límites','境界の照合'],
    detail:['32 of 57 countries/areas have exact-joined Natural Earth reference map units. Missing shapes stay in the registry and tables.','32 de 57 países/áreas tienen una unión exacta con las unidades cartográficas de referencia de Natural Earth. Las geometrías faltantes permanecen en el registro y las tablas.','57の国・地域のうち32件をNatural Earth参照図形へ完全一致で結合しています。図形がない地域も台帳と表から削除しません。'],
    next:['Reconcile suitable display geometry without name-only joins; do not use the reference map as a legal or statistical boundary.','Conciliar geometrías de visualización adecuadas sin unir solo por nombre; no usar el mapa de referencia como límite legal o estadístico.','名称だけで結合せず、表示用図形を照合する。参照地図を法定・統計境界として使わない。']
  },
  planning_materials:{
    category:['Planning materials','Materiales de planificación','計画資料'],
    detail:['The Americas exploration scope is not a legal planning authority. Country and local planning laws, plans, budgets and evaluation materials have not been generalized across the region.','El ámbito de exploración de las Américas no es una autoridad legal de planificación. Las leyes, planes, presupuestos y evaluaciones nacionales y locales no se han generalizado para toda la región.','アメリカ大陸の探索範囲は法定計画主体ではありません。各国・地域の計画法、計画、予算、評価資料を地域全体へ一般化していません。'],
    next:['Collect planning evidence in each country adapter and keep the legal planning unit separate from lower diagnostic geography.','Recopilar evidencia de planificación en cada adaptador nacional y separar la unidad legal de planificación de la geografía diagnóstica inferior.','国別アダプターで計画根拠を収集し、法定計画単位と内部診断に使う下位地域を区別する。']
  },
  un_wpp_country_area_coverage:{
    category:['UN WPP country/area coverage','Cobertura por país/área de UN WPP','UN WPPの国・地域被覆'],
    detail:['UN WPP 2024 country/area rows are available for 55 of 57 Americas registry entries. Missing: BVT, SGS. These entries remain missing, not zero.','UN WPP 2024 contiene filas para 55 de las 57 entradas del registro. Faltan BVT y SGS; permanecen como datos faltantes, no como cero.','UN WPP 2024は57件中55件に国・地域行があります。BVTとSGSは欠測のままで、ゼロとして扱いません。'],
    next:['Retain missing status unless a definition-compatible UN source row becomes available; do not use a partial sum as the regional total.','Mantener el estado faltante hasta disponer de una fila compatible de la ONU; no usar una suma parcial como total regional.','定義が対応する国連データ行を取得するまで欠測を保持し、不完全小計を地域全体値として使わない。']
  }
};
function localizedGap(gap){
  const copy=worldMode()?REGIONAL_GAP_COPY[gap.category]:null,index=language==='es'?1:language==='ja'?2:0;
  return copy?{category:copy.category[index],detail:copy.detail[index],next_action:copy.next[index]}:{category:gap.category.replaceAll('_',' '),detail:gap.detail,next_action:gap.next_action||localCopy('Verify with the responsible source.','Verificar con la fuente responsable.','所管する出典で確認する。')};
}
const localized=value=>typeof value==='object'&&value?value[language]||value.en||Object.values(value)[0]:value;
const scopeEntryHeading=(children,countryCount)=>dataset.analysis?.pilot?.stage==='central_america_7'
  ? language==='ja'?`<span class="pilot-scope-highlight">中米7か国</span>から選ぶ`:language==='es'?`Elige entre los <span class="pilot-scope-highlight">7 países de Centroamérica</span>`:`Choose from the <span class="pilot-scope-highlight">7 Central American countries</span>`
  : language==='ja'?`<span class="pilot-scope-highlight">アメリカ大陸</span>の${children.length}地域から選ぶ`:language==='es'?`Elige entre ${children.length} regiones de <span class="pilot-scope-highlight">América</span>`:`Choose from ${children.length} regions of the <span class="pilot-scope-highlight">Americas</span>`;
const sourceNote = (indicator, observation, prefix='Source') => {
  const source=sourceFor(dataset,indicator,observation);
  const sourcePeriod=observation?.period || dataset.analysis?.default_period_by_indicator?.[indicator?.id] || state?.period;
  const locator=observation?.footnote || indicator?.source_locator;
  return `<div class="source-note source-note-block"><span>${e(prefix)}</span>${source ? renderSourceAttribution(indicator,observation,source,sourcePeriod,language) : 'No verified source collected'}${source?.retrieved_at ? `<span>Retrieved ${e(source.retrieved_at.slice(0,10))}.</span>` : ''}${locator ? `<span>Source table: ${e(locator)}.</span>` : ''}</div>`;
};
function periodControl(id='period-select') {
  const options = periodsFor(dataset,state.metric);
  if (state.period && !options.includes(state.period)) options.unshift(state.period);
  return `<label class="field" for="${id}"><span>Source period</span><select id="${id}" data-control="period">${options.length?options.map(period=>`<option value="${e(period)}" ${period===state.period?'selected':''}>${e(period)}${periodsFor(dataset,state.metric).includes(period)?'':' · no observation for this indicator'}</option>`).join(''):'<option value="">No periods acquired</option>'}</select></label>`;
}
function indicatorControl() {
  const themes=[...new Set(dataset.indicators.map(indicator=>indicator.theme || 'Other'))];
  return `<label class="field grow" for="indicator-select"><span>Theme / indicator</span><select id="indicator-select" data-control="metric">${themes.map(theme=>`<optgroup label="${e(theme)}">${dataset.indicators.filter(indicator=>(indicator.theme||'Other')===theme).map(indicator=>`<option value="${e(indicator.id)}" ${indicator.id===state.metric?'selected':''}>${e(indicator.name)}</option>`).join('')}</optgroup>`).join('')}</select></label>`;
}
function areaControls() {
  const areas=dataset.territories.filter(area=>!territoryLineage(dataset,area.id).slice(0,-1).some(parent=>isTerminalTerritory(dataset,parent)));
  const groups=[...new Set(areas.map(area=>area.level))];
  const hits=areaSearch ? areas.filter(area=>[area.name,area.id,area.official_code].some(value=>String(value||'').toLocaleLowerCase().includes(areaSearch.toLocaleLowerCase()))) : [];
  const hierarchy=(['territorial','planning'].includes(page)||worldMode())?hierarchyControls(dataset,state.selected).filter(control=>!comparisonSet(dataset,control.parent.id).terminal):[];
  const flatSelector=`<label class="field" for="area-select"><span>Selected area${hierarchy.length?' · all records':''}</span><select id="area-select" data-control="area">${groups.map(level=>`<optgroup label="${e(levelLabel(level))}">${areas.filter(area=>area.level===level).map(area=>`<option value="${e(area.id)}" ${area.id===state.selected?'selected':''}>${e(territoryOptionLabel(dataset,area))}${area.level==='national'?(dataset.analysis?.kind==='world'?' · world':worldMode()?' · whole scope':' · national'):''}</option>`).join('')}</optgroup>`).join('')}</select></label>`;
  return `<div class="area-controls">${hierarchy.length?`<div class="hierarchy-controls"><p class="small-note">Showing <strong>${e(currentArea().name)}</strong>. Choose “Whole …” to make that parent the selected area and clear its lower-area selection.</p>${hierarchy.map((control,index)=>`<label class="field" for="hierarchy-${index}"><span>${e(control.levels.map(levelLabel).join(' / '))} · within ${e(control.parent.name)}</span><select id="hierarchy-${index}" data-control="hierarchy" data-parent="${e(control.parent.id)}">${control.context?`<option value="context" selected disabled>${e(control.context.label)}</option>`:''}${control.options.map(option=>`<option value="${e(option.value)}" ${option.value===control.value?'selected':''}>${e(option.label)}</option>`).join('')}</select></label>`).join('')}</div><details class="micro-details" data-all-area-selector ${allAreaOpen?'open':''}><summary>All-area selector</summary>${flatSelector}</details>`:flatSelector}
  <label class="field" for="area-search"><span>Find an area by name or code</span><input id="area-search" type="search" data-control="area-search" value="${e(areaSearch)}" autocomplete="off" placeholder="Name or code"></label>
  ${areaSearch?`<div class="search-results" aria-label="Area search results">${hits.length?hits.slice(0,50).map(area=>button('select',`${e(area.name)}<small>${e(levelLabel(area.level))} · ${e(area.official_code || area.id)}</small>`,`data-id="${e(area.id)}"`,'result-button')).join(''):'<p>No matching areas.</p>'}${hits.length>50?`<p>${hits.length} matches; narrow your search to see more.</p>`:''}</div>`:''}
  ${state.selected!==dataset.country.national_territory_id?button('national',dataset.analysis?.kind==='world'?'Return to world view':worldMode()?`Return to ${e(dataset.country.name)} view`:'Return to national view','','text-button'):''}</div>`;
}
function hierarchyNavigation() {
  const lineage=territoryLineage(dataset,state.selected),children=comparisonSet(dataset,state.selected).terminal?[]:dataset.territories.filter(area=>area.parent_id===state.selected);
  return `<nav class="hierarchy-navigation" aria-label="Area hierarchy">${lineage.map(area=>area.id===state.selected?`<span aria-current="location">${e(area.name)}</span>`:button('select',e(area.name),`data-id="${e(area.id)}"`,'text-button')).join('<span aria-hidden="true"> › </span>')}</nav>${children.length?`<details class="child-navigation"><summary>Explore lower areas (${children.length})</summary><div>${children.map(area=>button('select',e(territoryOptionLabel(dataset,area)),`data-id="${e(area.id)}"`,'text-button')).join('')}</div></details>`:''}`;
}
function countryDetailLink() {
  const target=countryDiagnosticUrl(dataset,state,base);
  if(!target)return '';
  const localized=new URL(target);localized.searchParams.set('lang',language);
  return `<p class="country-detail-link"><a class="button secondary" href="${e(localized.href)}">Open ${e(currentArea().name)} country diagnostic</a><small>The selected period is retained. An indicator is carried across only through an explicit concept mapping; otherwise the country edition explains its separate default indicator. Country data are not estimated from world values. Browser Back returns to this world selection.</small></p>`;
}
function identity(area=currentArea()) {
  return `<p class="identity">${e(levelLabel(area.level))} · ${e(area.type)}${area.official_code ? ` · Code ${e(area.official_code)}` : ` · Provider ID ${e(area.id)}`}</p><details class="micro-details"><summary>Area identity and boundary edition</summary><p>Code system: ${e(area.code_system || 'Not specified')}. Boundary edition: ${e(area.boundary_version || 'Not verified')}. ${e(dataset.country.geography_note || '')}</p></details>`;
}
function stateMessage(result, local = currentArea().level !== 'national') {
  if (finite(result.value)) return '';
  const explanation = result.status==='not_collected' ? `${local?'Local observations':'Observations'} for this indicator have not been collected.` : result.status==='missing' ? 'No observation is available for the selected source period.' : `This observation is ${statusLabel(result.status).toLowerCase()}.`;
  return `<p class="missing-note">${e(explanation)} The selected area, indicator and period are retained.</p>`;
}
function countCoverage() {
  const local=dataset.territories.filter(area=>area.level!=='national');
  return {local:local.length, observed:new Set(dataset.observations.filter(row=>row.territory_id!==dataset.country.national_territory_id&&observedValue(row)!==null).map(row=>row.territory_id)).size};
}
function scopeBanner() {
  const coverage=countCoverage();
  const pilot=dataset.analysis?.pilot;
  if(pilot?.primary_series_family==='census' && !pilot.available_series_families?.includes('census'))return '<div class="scope-banner"><strong>Census data are the primary AreaData series and have not yet been integrated in this pilot build.</strong> Values currently shown are international reference series for country context. They are kept separate from future census observations. A census total using different country years will identify every country year and will appear only with complete coverage.</div>';
  if(pilot?.primary_series_family==='census' && pilot.census_adapter_status==='partial')return `<div class="scope-banner"><strong>The primary census population series currently covers ${e(pilot.census_country_ids.join(', '))}; the seven-country total is unavailable.</strong> ${e(pilot.census_pending_country_ids.join(', '))} remain pending. Country years, methods and source precision are retained. International reference indicators remain separate context series.</div>`;
  if(worldMode())return '';
  return nationalOnly(dataset) ? `<div class="scope-banner"><strong>National statistics; local statistics not yet collected.</strong> ${coverage.local ? `${coverage.local} reference areas are selectable.` : 'No local area registry has been collected.'} Local selections show their own gaps and available documents; national figures are not local estimates.</div>` : `<div class="scope-banner"><strong>Acquired evidence, with explicit gaps.</strong> ${coverage.observed} of ${coverage.local} local areas have at least one observation. Coverage varies by indicator and period.</div>`;
}
function updateBanner() {
  const sourceUpdate=planningSettings(dataset).update;
  const stopped=updateStatus?.status==='stopped'?updateStatus:sourceUpdate?.status==='stopped'?sourceUpdate:null;
  return stopped?`<p class="notice update-stopped" role="status"><strong>Update stopped — showing the last verified data.</strong> ${e(stopped.message)} Last successful update: ${e(stopped.last_success_at || 'Not recorded')}. Data edition: ${e(dataset.generated_at)}. Checked ${e(stopped.checked_at)}.</p>`:'';
}
function mapPanel({thematic=false,planning=false}={}) {
  const allFeatures=dataset.boundaries?.features || [];
  const selected=currentArea();
  const worldLocation=worldMode()&&!thematic&&!planning;
  // Location follows the navigation hierarchy, independently of lower comparison cohorts.
  const childIds=new Set(worldLocation&&!isTerminalTerritory(dataset,selected)?dataset.territories.filter(area=>area.parent_id===selected.id).map(area=>area.id):[]);
  const targetLevel = worldLocation&&childIds.size?areaFor([...childIds][0])?.level:thematic ? state.level : selected.level==='national' ? localLevels(dataset)[0] : selected.level;
  const rows=thematic?comparisonRows(dataset,state):[];
  const comparisonIds=new Set(rows.map(row=>row.area.id));
  // A thematic map is the spatial rendering of the same comparison registry used
  // by the table, coverage and ranking. Never expose out-of-scope shapes merely
  // because they share the same administrative level.
  const features=allFeatures.filter(feature=>{
    const id=feature.properties?.territory_id;
    if(thematic)return comparisonIds.has(id);
    return worldLocation&&childIds.size?childIds.has(id):areaFor(id)?.level===targetLevel;
  });
  const fitId = wholeMap || selected.level==='national' || worldLocation&&childIds.size ? '' : selected.id;
  const geometry=mapGeometry(features,fitId);
  const stats=distribution(rows);
  const values=new Map(rows.map(row=>[row.area.id,row.value]));
  const comparisonById=new Map(rows.map(row=>[row.area.id,row]));
  const mapSettings=planningSettings(dataset).map;
  const colour = id => {
    if(planning)return officialMapState(dataset,id).color;
    if(!thematic)return '#c1d9d1';
    const value=values.get(id);
    if(!finite(value))return '#dedfdf';
    if(stats.min===stats.max)return '#47937e';
    const colours=['#dcece5','#bad8ca','#85bba5','#4a977c','#226c57'];
    return colours[Math.min(4,Math.floor(5*(value-stats.min)/(stats.max-stats.min)))];
  };
  const title=planning?(mapSettings.mode==='official_status'?`Documented institutional states · ${categoryLabels[mapSettings.category]} · ${mapSettings.period}`:'Material references by area'+(mapSettings.category?' · '+categoryLabels[mapSettings.category]:'')+(mapSettings.period?' · '+mapSettings.period:'')):thematic?`${currentMetric()?.name || 'Indicator'} · ${state.period || 'No period'}`:page==='home'?'Explore the map':'Location';
  const sourceIds=[...new Set(features.map(feature=>feature.properties?.source_id).filter(Boolean))];
  const boundarySources=dataset.sources.filter(source=>sourceIds.includes(source.id) || /boundary|boundaries/i.test(source.id+' '+source.name));
  const highlightedId=thematic?comparisonFocusId:state.selected;
  const chosenTab=geometry.paths.find(path=>path.id===highlightedId)?.id || geometry.paths[0]?.id;
  return `<section class="panel map-panel" aria-labelledby="map-title"><div class="panel-heading"><div><p class="eyebrow">${page==='home'?e(displayAreaName(areaFor(dataset.country.national_territory_id))):`${e(levelLabel(targetLevel))} reference boundaries`}</p><h2 id="map-title">${e(title)}</h2></div>${selected.level!=='national'&&geometry.paths.length?button('map-extent',wholeMap?'Fit selected area':'Show whole country','','text-button'):''}</div>
  ${geometry.paths.length ? `<svg class="geographic-map" viewBox="0 0 760 400" role="group" aria-label="${e(title)}. ${e(thematic?localCopy('Focus a comparison area with Enter.','Enfoque un área de comparación con Enter.','Enterキーで比較する地域を注目します。'):localCopy('Select an area with Enter.','Seleccione un área con Enter.','Enterキーで地域を選択します。'))} ${e(localCopy('Arrow keys move between boundaries.','Las flechas recorren los límites.','矢印キーで境界間を移動します。'))}"><title>${e(title)} — ${e(dataset.country.name)}; ${fitId&&geometry.selectedHasGeometry?`view fitted to ${e(selected.name)}`:'whole available boundary layer'}</title><rect width="760" height="400" fill="#f4f8f7"/>${geometry.paths.map(path=>{const area=areaFor(path.id),value=values.get(path.id),comparisonRow=comparisonById.get(path.id);const label=`${area?.name || path.id}${thematic?`: ${finite(value)?fmt(value)+' '+currentMetric().unit:'No data'} for ${comparisonRow?.period || state.period}`:''}`;return `<path d="${path.d}" fill="${colour(path.id)}" fill-rule="evenodd" class="map-area ${path.id===highlightedId?'selected':''}" role="button" aria-label="${e(label)}" aria-pressed="${path.id===highlightedId}" tabindex="${path.id===chosenTab?'0':'-1'}" data-action="${thematic?'focus-comparison':'select'}" data-id="${e(path.id)}" data-map-id="${e(path.id)}"><title>${e(label)}</title></path>`;}).join('')}</svg>` : '<div class="map-unavailable"><strong>No verified boundaries available for this level.</strong><p>Use the area selector and search. Acquired statistics and documents remain accessible.</p></div>'}
  ${selected.level!=='national'&&!childIds.size&&!features.some(feature=>feature.properties?.territory_id===selected.id)?`<p class="missing-note">No boundary is joined to ${e(selected.name)} at this map level. No nearby polygon is substituted.</p>`:''}
  <p class="map-legend">${planning?(mapSettings.mode==='official_status'?`${mapSettings.statuses.map(status=>`<span class="legend-item"><svg width="12" height="12" aria-hidden="true"><rect width="12" height="12" fill="${e(status.color)}"/></svg> ${e(status.label)}</span>`).join(' · ')}. Gray = no matched evidence; amber = conflicting evidence. States apply only to ${e(mapSettings.period)} and this document category. Select an area to inspect the cited evidence.`:`Green = a verified material reference is available; gray = no verified reference collected. ${mapSettings.period?'Applies only to '+e(mapSettings.period)+'.':'Includes different document periods.'}${mapSettings.category?' Category: '+e(categoryLabels[mapSettings.category])+'.':''} These are collection states, not counts of approved plans.`):thematic?`Colors use five equal value intervals across all ${e(levelLabel(state.level).toLowerCase())} areas for this indicator and period; search does not change the scale. Gray = No data. High values are not automatically better.`:'A location map. Fill colors do not represent population or service levels.'} <span class="legend-selected">${e(localCopy('Gold outline','Contorno dorado','金色の枠線'))}</span> = ${e(thematic?localCopy('focused comparison area; the diagnostic area remains unchanged','área de comparación enfocada; el área de diagnóstico no cambia','比較内で注目中の地域。分析対象は変わりません'):localCopy('selected area','área seleccionada','選択地域'))}.</p>
  <p class="source-note">Boundary source: ${boundarySources.length?boundarySources.map(source=>link(source.url,source.name)).join(' · '):'See the source register; boundary authority and edition must be verified.'} Reference boundaries are not a legal boundary certification. Keyboard: arrows / Home / End, then Enter or Space.</p>${dataset.country.geography_note?`<p class="source-note"><strong>Geographic scope:</strong> ${e(dataset.country.geography_note)}</p>`:''}</section>`;
}
function facts() {
  const priority=dataset.indicators.filter(indicator=>/population|household/i.test(indicator.name)).slice(0,3);
  const indicators=priority.length?priority:dataset.indicators.slice(0,3);
  return `<div class="basic-facts">${indicators.map(indicator=>{const current=territorialIndicatorState(dataset,state.selected,indicator.id,state.period),result=current.result;return `<div class="fact"><span>${e(indicator.name)}</span><strong>${fmt(result.value,indicator)}</strong><small>${e(result.row?.unit || indicator.unit)} · ${e(current.period || 'No source period')} · ${e(statusLabel(result.status))}</small>${result.provenance==='areadata_calculated'?`<small>${e(result.note)}</small>`:''}</div>`;}).join('')}</div>`;
}
function seriesFigure(indicator, territoryId=state.selected) {
  const series=seriesFor(dataset,territoryId,indicator.id);
  const observed=series.filter(row=>observedValue(row)!==null);
  if(!observed.length)return '<p class="small-note">No acquired time series for this area. National series are not substituted.</p>';
  const area=areaFor(territoryId);
  const geo=seriesGeometry(series.map(row=>observationContext(dataset,area,indicator,row).comparable?row:{...row,status:'missing',value:null}));
  const sourceIds=[...new Set(observed.map(row=>row.source_id))];
  const sources=sourceIds.map(id=>dataset.sources.find(source=>source.id===id)).filter(Boolean);
  return `<figure class="series"><figcaption>${e(area.name)} · ${e(indicator.name)} · ${e(series[0].period)}${series.length>1?`–${e(series.at(-1).period)}`:''} · ${e(indicator.unit)}</figcaption>
  ${geo&&geo.points.length>1?`<svg viewBox="0 0 600 170" role="img" aria-label="${e(indicator.name)} time series for ${e(area.name)}. Exact values and sources are in the table below."><title>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</title><line x1="40" y1="140" x2="580" y2="140" stroke="#c8d5d7"/>${geo.segments.map(points=>`<polyline points="${points}" fill="none" stroke="#267966" stroke-width="2.5"/>`).join('')}${geo.points.map(point=>`<circle cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" r="3" fill="#267966"><title>${e(point.row.period)}: ${e(fmt(point.row.value,indicator))} ${e(indicator.unit)}</title></circle>`).join('')}<text x="3" y="21">${e(fmt(geo.max,indicator))}</text><text x="3" y="135">${e(fmt(geo.min,indicator))}</text><text x="40" y="161">${e(series[0].period)}</text><text x="580" y="161" text-anchor="end">${e(series.at(-1).period)}</text></svg><p class="small-note">Source periods in sequence. Missing or incompatible observations break the line; no missing values are estimated.</p>`:'<p class="small-note">Fewer than two comparable observations; no trend is inferred.</p>'}
  <p class="source-note">Series: ${e([...new Set(observed.map(row=>seriesSourceLabel(indicator,row,row.period,language)))].join(', '))}. Exact sources follow.</p>
  <details><summary>Time-series values and sources (${series.length})</summary><div class="table-scroll"><table><caption>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</caption><thead><tr><th scope="col">Period</th><th scope="col">Value</th><th scope="col">Status</th><th scope="col">Source</th></tr></thead><tbody>${series.map(row=>{const source=sourceFor(dataset,indicator,row);return `<tr><td>${e(row.period)}</td><td>${fmt(observedValue(row),indicator)} ${e(observationMeaning(indicator,row).unit)}</td><td>${e(statusLabel(row.status))}${observationContext(dataset,area,indicator,row).comparable?'':'<br>'+e(observationContext(dataset,area,indicator,row).reason)}</td><td>${renderSourceAttribution(indicator,row,source,row.period,language)}</td></tr>`;}).join('')}</tbody></table></div></details>
  ${button('series-csv','Time series CSV',`data-id="${e(indicator.id)}" data-territory="${e(territoryId)}"`,'text-button')}</figure>`;
}
function populationContext(indicator,result) {
  const config=dataset.analysis?.population_context,area=currentArea();
  if(!config||indicator.id!==config.primary_indicator_id||!['national','country'].includes(area.level))return '';
  const reference=metricFor(config.reference_indicator_id);
  if(!reference)return '';
  const referenceResult=areaObservationState(dataset,area.id,reference.id,config.reference_period);
  if(!finite(referenceResult.value))return '';
  const source=sourceFor(dataset,reference,referenceResult.row),stage={period:config.reference_period,series_stage:'medium_projection'};
  const difference=finite(result.value)?referenceResult.value-result.value:null;
  const percent=finite(difference)&&result.value!==0?difference/result.value*100:null;
  const comparisonText=language==='es'?'personas frente al total censal con años distintos. La diferencia refleja el año de referencia y el método; no es un margen de error.':language==='ja'?'人、国ごとに年が異なる国勢調査合計より多い値です。この差は基準年と算出方法の違いであり、誤差幅ではありません。':'people compared with the mixed-year census total. The difference reflects reference year and method; it is not an error margin.';
  return `<aside class="population-context" aria-label="UN population context"><div><span>Same-year international context</span><strong>${fmt(referenceResult.value,reference)}</strong><small>people · ${e(seriesSourceLabel(reference,referenceResult.row || stage,config.reference_period,language))}</small></div><div>${renderSourceAttribution(reference,referenceResult.row || stage,source,config.reference_period,language)}</div>${finite(difference)?`<p><strong>${difference>=0?'+':''}${fmt(difference,reference)}</strong> ${finite(percent)?`(${difference>=0?'+':''}${e(percent.toLocaleString(languageLocale(language),{maximumFractionDigits:1}))}%) `:''}${comparisonText}</p>`:`<p>${e(config.note)}</p>`}</aside>`;
}
function metricCard(indicator) {
  const selectedState=territorialIndicatorState(dataset,state.selected,indicator.id,state.period),effectivePeriod=selectedState.period;
  const result=selectedState.result;
  const national=areaObservationState(dataset,dataset.country.national_territory_id,indicator.id,effectivePeriod);
  const meaning=result.provenance==='areadata_calculated'?{...observationMeaning(indicator),comparable:true,reason:''}:observationContext(dataset,currentArea(),indicator,result.row),referenceMeaning=observationContext(dataset,areaFor(dataset.country.national_territory_id),indicator,national.row);
  const local=currentArea().level!=='national';
  return `<article class="indicator-card"><div class="indicator-heading"><h3>${e(indicator.name)}</h3><span class="unit">${e(meaning.unit)}</span></div><div class="value-row"><strong>${fmt(result.value,indicator)}</strong><span>${e(statusLabel(result.status))} · ${e(result.row?.period || effectivePeriod || 'No source period')}</span></div>${stateMessage(result)}${populationContext(indicator,result)}
  ${local?`<p class="national-reference">${worldMode()?'World reference':'National reference'} — ${e(dataset.country.name)}: <strong>${fmt(national.value,indicator)}</strong> ${e(referenceMeaning.unit)} · ${e(national.row?.period || effectivePeriod)}. ${e(statusLabel(national.status))}.${referenceMeaning.comparable?'':` ${e(referenceMeaning.reason)}`}</p>`:''}
  ${result.status==='calculated'?`<p class="aggregation-note"><strong>Calculated value.</strong> ${e(result.note)} ${result.provenance==='areadata_calculated'&&result.components.length?`Components: ${e(result.components.map(item=>`${areaFor(item.territory_id)?.name || item.territory_id} (${item.period})`).join(', '))}.`:''}</p>`:result.status==='incomplete'?`<p class="missing-note">${e(result.note)}${finite(result.covered_value)?` Covered subtotal: ${e(fmt(result.covered_value,indicator))} ${e(indicator.unit)}.`:''}</p>`:''}<p class="definition">${e(meaning.definition || 'Definition not acquired.')}</p>${meaning.comparable?'':`<p class="missing-note">${e(meaning.reason)} Its original value remains visible; a comparable trend is not inferred.</p>`}${sourceNote(indicator,result.row,finite(result.value)&&result.row?'Selected-area source':'Indicator sources; see calculation or gap details')}
  ${seriesFigure(indicator)}<div class="actions">${button('compare','Compare this indicator',`data-id="${e(indicator.id)}" data-period="${e(effectivePeriod)}"`,'text-button')}${button('indicator-csv','Selected-period CSV',`data-id="${e(indicator.id)}" data-period="${e(effectivePeriod)}"`,'text-button')}</div>${renderInternalComparison(dataset,state.selected,indicator.id,effectivePeriod,{language})}</article>`;
}
function territorial() {
  const contextualId=dataset.analysis?.population_context?.reference_indicator_id;
  const territorialIndicators=dataset.indicators.filter(indicator=>indicator.id!==contextualId);
  const themes=[...new Set(territorialIndicators.map(indicator=>indicator.theme || 'Other'))];
  return `<div class="page-actions">${periodControl('territorial-period')}${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}</div>
  <div class="territorial-top"><section class="panel selected-profile"><h2>${e(currentArea().name)}</h2>${hierarchyNavigation()}${areaControls()}${identity()}${facts()}</section>${mapPanel()}</div>${countryDetailLink()}
  <nav class="section-index" aria-label="Diagnostic sections">${themes.map((theme,index)=>`<a href="#theme-${index}">${e(theme)}</a>`).join('')}<a href="#source-register">Sources and gaps</a></nav>
  ${themes.map((theme,index)=>`<section id="theme-${index}" class="theme-section"><h2 class="section-title">${e(theme)} <small>${e(currentArea().name)} · ${e(state.period || 'No period')}</small></h2><div class="indicator-grid">${territorialIndicators.filter(indicator=>(indicator.theme||'Other')===theme).map(metricCard).join('')}</div></section>`).join('')}
  <section class="panel diagnostic-outputs"><h2>Diagnostic report — ${e(currentArea().name)}</h2><p>Whole-area evidence and internal differences use the same period, definitions, membership and sources as this screen. Every member row is included, even when the on-screen table scrolls. This is a diagnostic working report; planning authority, priority hypotheses, resident agreement and approval remain separate.</p><div class="download-actions">${button('diagnostic-markdown','Editable Diagnostic report')}${button('diagnostic-html','Diagnostic report HTML')}${button('diagnostic-csv','Full diagnostic data CSV')}</div><p class="small-note">Print the HTML report to include legends, sources and every row. No resident agreement or formal approval is inferred.</p></section><div class="end-actions">${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}<a href="#top">Back to top</a></div>`;
}
function rankingContent(rows) {
  const ranked=rankedRows(rows,rankOrder), visible=searchRows(ranked,rankSearch);
  const missing=searchRows(rows.filter(row=>!finite(row.value)),rankSearch);
  return `<p class="small-note">${ranked.length} observed / ${rows.length} comparable areas. Search narrows displayed rows only. Ties share a rank.</p>
  <div class="ranking-scroll" role="region" aria-label="Full ranking and unranked areas" tabindex="0"><ol class="ranking-list">${visible.map(row=>`<li class="${row.area.id===comparisonFocusId?'selected':''}" data-ranking-id="${e(row.area.id)}"><span class="rank-number">${row.rank}</span>${button('focus-comparison',e(row.area.name),`data-id="${e(row.area.id)}" data-rank-id="${e(row.area.id)}"`,'rank-area')}<strong>${fmt(row.value)}</strong><small>${e(row.period || state.period)}</small></li>`).join('')}</ol>
  ${!visible.length?'<p class="missing-note">No observed values match this search. No rank is assigned to missing data.</p>':''}
  ${missing.length?`<details><summary>Unranked areas (${missing.length})</summary><ul class="missing-list">${missing.map(row=>`<li class="${row.area.id===comparisonFocusId?'selected':''}" data-ranking-id="${e(row.area.id)}" data-unranked="true">${button('focus-comparison',e(row.area.name),`data-id="${e(row.area.id)}" data-rank-id="${e(row.area.id)}"`,'text-button')}<span>${observedValue(row.row)!==null?`${fmt(observedValue(row.row))} ${e(observationMeaning(currentMetric(),row.row).unit)} · ${e(row.period || state.period)} · `:''}${e(statusLabel(row.status))} · unranked${row.reason?` · ${e(row.reason)}`:''}</span></li>`).join('')}</ul></details>`:''}</div>`;
}
function thematic() {
  const indicator=currentMetric();
  if(!indicator)return '<p class="missing-note">No indicators have been collected. See the source register and acquisition gaps.</p>';
  const effectivePeriod=effectivePeriodForIndicator(dataset,state.metric,state.period);
  const rows=comparisonRows(dataset,state), stats=distribution(rows);
  const compatibility=comparisonCompatibility(dataset,state);
  const national=areaObservationState(dataset,dataset.country.national_territory_id,state.metric,effectivePeriod);
  const selected=areaObservationState(dataset,state.selected,state.metric,effectivePeriod),selectedMeaning=observationContext(dataset,currentArea(),indicator,selected.row),nationalMeaning=observationContext(dataset,areaFor(dataset.country.national_territory_id),indicator,national.row);
  const levels=localLevels(dataset);
  const rank=rankedRows(rows,rankOrder).find(row=>row.area.id===state.selected)?.rank;
  return `<section class="panel controls-panel"><div class="control-row">${indicatorControl()}${periodControl()}<label class="field" for="comparison-level"><span>Comparable geographic level</span><select id="comparison-level" data-control="level">${levels.length?levels.map(level=>`<option value="${e(level)}" ${level===state.level?'selected':''}>${e(levelLabel(level))}</option>`).join(''):'<option value="">No local areas acquired</option>'}</select></label></div><p class="definition">${e(indicator.definition)} Unit: ${e(indicator.unit)}. All comparisons use this indicator and period policy; changing an area retains both. Mixed-period rows show each area's actual source year.</p></section>
  <div class="summary-grid"><article class="summary"><span>${worldMode()?'World':'National'} value · source-reported</span><strong>${fmt(national.value)}</strong><small>${e(dataset.country.name)} · ${e(national.row?.period || effectivePeriod)} · ${e(nationalMeaning.unit)}</small></article><article class="summary"><span>Median of comparable local areas</span><strong>${fmt(stats.median)}</strong><small>${e(levelLabel(state.level))}; observed values only</small></article><article class="summary"><span>Local data coverage</span><strong>${stats.count} / ${rows.length}</strong><small>${rows.length-stats.count} unranked or missing</small></article><article class="summary"><span>Observed local range</span><strong>${stats.count?`${fmt(stats.min)}–${fmt(stats.max)}`:'No data'}</strong><small>${e(indicator.unit)} · ${e(effectivePeriod)} · same comparison set</small></article></div>
  ${!compatibility.comparable?`<p class="notice">${e(compatibility.reason)}</p>`:!stats.count?`<p class="notice"><strong>No comparable local observations for ${e(indicator.name)} · ${e(state.period)}.</strong> ${nationalOnly(dataset)?'Local statistics have not yet been collected.':'This level and period have no observed local values for the selected indicator.'} The national source value is shown separately; no local ranking or local estimates are created.</p>`:''}
  <div class="thematic-grid">${mapPanel({thematic:true})}<section class="panel explorer" aria-labelledby="ranking-title"><h2 id="ranking-title">Find and compare areas</h2><p class="small-note">${e(levelLabel(state.level))} · ${e(indicator.name)} · ${e(effectivePeriod)} · ${e(indicator.unit)}</p>
  <label class="field" for="ranking-search"><span>Search ranking by name or code</span><input id="ranking-search" type="search" data-control="ranking-search" value="${e(rankSearch)}" placeholder="Name or code"></label><div class="control-row"><label class="field" for="ranking-order"><span>Order</span><select id="ranking-order" data-control="rank-order"><option value="desc" ${rankOrder==='desc'?'selected':''}>Highest first</option><option value="asc" ${rankOrder==='asc'?'selected':''}>Lowest first</option></select></label>${button('show-selected','Show selected in ranking','','text-button')}</div><div id="ranking-content">${rankingContent(rows)}</div></section></div>
  <section class="panel selection-detail"><div><h2>${e(currentArea().name)} — selected area</h2>${identity()}${areaControls()}</div><div><p class="eyebrow">${e(indicator.name)} · ${e(selected.row?.period || state.period)} · ${e(selectedMeaning.unit)}</p>${!selectedMeaning.comparable?`<p class="notice">${e(selectedMeaning.reason)}</p>`:''}<p class="definition">${e(selectedMeaning.definition)}</p><p class="selected-value">${fmt(selected.value)}</p><p>${e(statusLabel(selected.status))}. ${currentArea().level==='national'?'National observations are not part of the local ranking.':rank?`Rank ${rank} of ${stats.count} observed areas (${rankOrder==='desc'?'highest':'lowest'} first).`:currentArea().level!==state.level?'Selected area is outside the comparable geographic level.':'No local rank.'}</p>${stateMessage(selected)}${sourceNote(indicator,selected.row)}<div class="actions">${pageLink('territorial','Open territorial diagnostic')}${pageLink('planning','Open planning resources')}${button('comparison-csv','Comparison CSV')}</div></div></section>
  <section class="panel"><h2>Selected-area history</h2>${seriesFigure(indicator)}</section>`;
}
function planning() {
  const settings=planningSettings(dataset),documents=planningDocuments(dataset,state.selected);
  const nationalDocuments=state.selected===dataset.country.national_territory_id?[]:planningDocuments(dataset,dataset.country.national_territory_id);
  const refs=new Set(dataset.documents.filter(hasDocumentReference).map(doc=>doc.territory_id));
  const groups=documentGroups(dataset,state.selected);
  const local=dataset.territories.filter(area=>area.level!=='national');
  const observed=dataset.indicators.filter(indicator=>territorialIndicatorState(dataset,state.selected,indicator.id,state.period).result.value!==null).length;
  const outputs={markdown:button('planning-markdown','Download editable Markdown','','button'),html:button('planning-html','Print-ready HTML'),evidence_csv:button('planning-csv','Evidence CSV'),documents_csv:button('documents-csv','Materials and findings CSV')};
  const links=settings.related_links.filter(item=>!item.territory_id||item.territory_id===state.selected).map(item=>({label:item.label,url:relatedResourceUrl(item.url,base,routeWithLanguage())})).filter(item=>item.url);
  const gaps=selectedGaps(dataset,state.selected);
  if(worldMode()&&currentArea().type!=='country'){
    const integrated=dataset.analysis?.coverage?.census_integrated_country_ids?.length||0,total=dataset.analysis?.coverage?.country_area_count||dataset.territories.filter(area=>area.type==='country').length;
    const authorityWarning=localCopy(
      'This selected area is an analysis scope, not a verified legal planning authority.',
      'Esta área seleccionada es un ámbito de análisis, no una autoridad legal de planificación verificada.',
      '選択中の地域は分析対象であり、確認済みの法定計画主体ではありません。'
    );
    const completenessWarning=localCopy(
      `This regional portal is not ${total} completed country editions. Official census and domestic hierarchy are integrated for ${integrated} of ${total} registry entries; country planning laws, plans, budgets and evaluations remain country-adapter work. No planning draft or official-material attribution is generated for this regional scope.`,
      `Este portal regional no representa ${total} ediciones nacionales terminadas. El censo oficial y la jerarquía interna están integrados para ${integrated} de ${total} entradas del registro; las leyes, planes, presupuestos y evaluaciones de planificación deben incorporarse mediante cada adaptador nacional. No se genera para este ámbito regional ningún borrador de plan ni atribución a materiales oficiales.`,
      `この地域ポータルは${total}の国別版が完成したことを意味しません。公式国勢調査と国内階層の統合は${total}件中${integrated}件で、計画法、計画、予算、実施・評価資料は国別アダプターで追加します。この広域分析対象について、計画草案や公式資料への帰属を生成しません。`
    );
    const regionalPurpose=localCopy('Review official materials for the selected area and prepare evidence for plan preparation or revision.','Revise los materiales oficiales del área seleccionada y prepare evidencia para elaborar o revisar el plan.','選択地域の公式資料を確認し、計画の策定・見直しに使う根拠を準備します。');
    return '<section class="panel planning-overview"><h2>'+e(settings.title)+'</h2><p>'+e(regionalPurpose)+'</p></section><section class="panel planning-controls"><h2>'+e(localCopy('Choose one planning territory','Elegir un territorio de planificación','計画対象地域を1つ選択'))+'</h2>'+areaControls()+identity()+'</section><div class="planning-grid">'+mapPanel({planning:true})+'<section class="panel planning-resources"><h2>'+e(currentArea().name)+'</h2><p class="notice planning-scope-warning"><strong>'+e(authorityWarning)+'</strong> '+e(completenessWarning)+'</p><div class="actions">'+pageLink('territorial',localCopy('Review territorial evidence','Revisar evidencia territorial','地域データを確認'))+pageLink('thematic',localCopy('Compare countries','Comparar países','国を比較'))+pageLink('database',localCopy('Inspect source data','Consultar datos fuente','元データを確認'))+'</div></section></div>';
  }
  return '<section class="panel planning-overview"><h2>'+e(settings.title)+'</h2><p>'+e(settings.purpose)+'</p><p class="small-note">Verified material references for '+local.filter(area=>refs.has(area.id)).length+' of '+local.length+' local records'+(refs.has(dataset.country.national_territory_id)?'; national reference materials also available':'')+'. Coverage varies by category and period; this is not a count of completed or approved plans.</p></section>'+
  '<section class="panel planning-controls"><h2>Choose an area</h2>'+areaControls()+identity()+'</section>'+
  '<div class="planning-grid">'+mapPanel({planning:true})+'<section class="panel planning-resources"><h2>'+e(currentArea().name)+' — available materials</h2><p>Materials keep their own plan period, fiscal year or quarter. The statistical year below does not filter or relabel them.</p>'+
  (groups.some(group=>group.documents.length)?'<nav class="document-contents" aria-label="Available material categories">'+groups.filter(group=>group.documents.length).map(group=>'<a href="#documents-'+e(group.id)+'">'+e(group.label)+'</a>').join('')+'</nav>':'')+
  renderDocumentGroups(dataset,state.selected)+'</section></div>'+
  '<section class="panel planning-output"><h2>Prepare a working evidence base</h2><p class="notice compact"><strong>Generated working material — unapproved.</strong> These outputs bring together selected-area statistics and collected references. They do not replace the published originals or establish official approval, targets or resident agreement.</p><div class="control-row">'+periodControl('planning-period')+'</div><p>'+observed+' of '+dataset.indicators.length+' statistical indicators have an observed value for '+e(currentArea().name)+' in '+e(state.period || 'the selected period')+'. '+documents.length+' selected-area material records retain their own periods.</p><div class="download-actions">'+settings.outputs.map(format=>outputs[format] || '').join('')+'</div>'+
  (settings.outputs.length?'<p class="small-note">Evidence CSV contains the selected statistical year. Materials CSV, when adopted, contains the original document periods and findings. Markdown and HTML include both with source definitions and explicit gaps.</p>':'<p class="missing-note">No generated download format is adopted for this project. Use the original references and territorial evidence; record the country-specific output workflow in the handoff.</p>')+
  (settings.outputs.includes('markdown')||settings.outputs.includes('html')?'<details><summary>Preview planning base</summary><pre class="planning-preview">'+e(planningMarkdown(dataset,state.selected,state.period,language))+'</pre></details>':'')+
  (gaps.length?'<details><summary>Outstanding evidence and next actions</summary><ul>'+gaps.map(gap=>'<li><strong>'+e(statusLabel(gap.status))+'</strong> — '+e(gap.detail)+'<p class="small-note">Next: '+e(gap.next_action || 'Verify the responsible source.')+'</p></li>').join('')+'</ul></details>':'')+'</section>'+
  (links.length?'<section class="panel"><h2>Related investment, finance and official services</h2><ul>'+links.map(item=>'<li><a href="'+e(item.url)+'">'+e(item.label)+'</a></li>').join('')+'</ul></section>':'')+
  (nationalDocuments.length?'<section class="panel"><h2>National reference materials — '+e(dataset.country.name)+'</h2><p>National materials are shown separately and are not attributed to '+e(currentArea().name)+'.</p>'+nationalDocuments.map(doc=>renderDocument(dataset,doc)).join('')+'</section>':'')+
  (settings.system?'<section class="panel"><h2>Country planning framework</h2><p>'+e(settings.system.label)+' · '+e(settings.system.scope)+'</p><p>'+e(settings.system.cycle)+'</p>'+settings.system.source_ids.map(id=>sourceNote(null,{source_id:id})).join('')+'</section>':'')+
  '<div class="end-actions">'+pageLink('territorial','Review territorial evidence')+pageLink('thematic','Compare across areas')+'</div>';
}
function home() {
  if(worldMode()) {
    const root=areaFor(dataset.country.national_territory_id),children=dataset.territories.filter(area=>area.parent_id===root.id);
    const countryCount=dataset.analysis?.coverage?.country_area_count||dataset.territories.filter(area=>area.type==='country').length;
    const allCountriesUrl=new URL(`territorial/?${routeWithLanguage({...state,selected:root.id,level:comparisonLevelForArea(dataset,root.id,root.level)})}`,base).href;
    const wholeLabel=dataset.analysis?.pilot?.stage==='central_america_7'?localCopy('All 7 Central American countries','Los 7 países de Centroamérica','中米7か国すべて'):localCopy(`All Americas — ${countryCount} countries and areas`,`Toda América — ${countryCount} países y áreas`,`アメリカ大陸全体・${countryCount}の国・地域`);
    const allCountriesEntry=`<a class="region-entry pilot-all-entry" href="${e(allCountriesUrl)}"><strong>${e(wholeLabel)}</strong><span>${e(localCopy('View the whole region','Ver toda la región','地域全体を見る'))} →</span></a>`;
    const integrated=dataset.analysis?.coverage?.census_integrated_country_ids?.length||0;
    const completionNote=localCopy(`This is a regional exploration entry, not ${countryCount} completed country editions. Official census and domestic hierarchy are integrated for ${integrated} of ${countryCount}; country planning evidence is added by each country adapter.`,`Esta es una entrada de exploración regional, no ${countryCount} ediciones nacionales terminadas. El censo oficial y la jerarquía interna están integrados para ${integrated} de ${countryCount}; la evidencia de planificación se añade en cada adaptador nacional.`,`これは広域探索の入口であり、${countryCount}の国別版が完成したという意味ではありません。公式Censusと国内階層の統合は${integrated}/${countryCount}で、計画資料は国別アダプターで追加します。`);
    return `<section class="home-intro world-intro"><p class="home-lead">Explore population and everyday life through census data. Follow the map from countries to local areas, compare places, and find data for research and regional planning.</p><p class="small-note home-coverage"><strong>Available coverage:</strong> <span>${e(displayAreaName(areaFor(dataset.country.national_territory_id)))}</span><span>. Available topics, years and local detail vary by country.</span></p><p class="notice compact">${e(completionNote)}</p><div class="actions">${pageLink('territorial','Explore territorial data','button')}${pageLink('thematic','Compare an indicator')}${pageLink('database','Open data database')}</div></section>
    <div class="territorial-top">${mapPanel()}<section class="panel"><h2>${scopeEntryHeading(children,countryCount)}</h2><p class="small-note">${e(localCopy('Start with a region, then continue to a country and any acquired local areas.','Empiece por una región y continúe hacia un país y las áreas locales disponibles.','大地域から国へ進み、収録済みの国では県・市町村までたどれます。'))}</p><div class="region-entry-grid">${allCountriesEntry}${children.map(area=>{const lower=dataset.territories.filter(item=>item.parent_id===area.id),label=lower.length?(lower.every(item=>item.type==='country')?`${lower.length} countries and areas`:`${lower.length} areas to explore`):'Open country';return `<a class="region-entry" href="${e(new URL(`territorial/?${routeWithLanguage({...state,selected:area.id,level:comparisonLevelForArea(dataset,area.id,area.level)})}`,base).href)}"><strong>${e(area.name)}</strong><span><span>${e(label)}</span> →</span></a>`;}).join('')}</div></section></div>
    <div class="entry-grid three"><a class="entry-card" href="${e(pageUrl('territorial'))}"><span class="entry-number">01</span><h2>Territorial diagnostic</h2><p>Explore population, health and living conditions in one place, with maps, charts and census sources.</p><strong>Explore a place →</strong></a><a class="entry-card" href="${e(pageUrl('thematic'))}"><span class="entry-number">02</span><h2>Thematic diagnostic</h2><p>Compare places by topic to understand differences in population and living conditions.</p><strong>Compare a theme →</strong></a><a class="entry-card" href="${e(pageUrl('planning'))}"><span class="entry-number">03</span><h2>Planning materials</h2><p>Use regional statistics to prepare planning materials. Availability of official plans and legal sources varies by country.</p><strong>Open planning →</strong></a></div>
    <section class="panel home-planning"><div><h2>Data for your research</h2><p>Find indicators, check their years and definitions, and download data with sources for your own analysis.</p></div>${pageLink('database','Find and download data','button')}</section>`;
  }
  const coverage=countCoverage();
  return `<section class="home-intro"><p class="eyebrow">Territorial information and planning</p><h2>Start with an area.<br>Or start with a question.</h2><p>Explore acquired evidence for ${e(dataset.country.name)}, compare like geographic areas when observations are available, and prepare a source-grounded planning outline.</p></section>
  <div class="entry-grid"><a class="entry-card" href="${e(pageUrl('territorial'))}"><span class="entry-number">01</span><h2>Explore an area</h2><p>Geographic selection, basic facts and sector evidence in one territorial diagnostic.</p><strong>Open territorial diagnostic →</strong></a><a class="entry-card" href="${e(pageUrl('thematic'))}"><span class="entry-number">02</span><h2>Compare a theme</h2><p>Choose an indicator and period. Check national context, local coverage, maps and rankings.</p><strong>Open thematic diagnostic →</strong></a></div>
  <section class="panel home-planning"><div><h2>Turn evidence into planning work</h2><p>Find acquired documents for the same area and download a generic, unapproved planning base with explicit evidence gaps.</p></div>${pageLink('planning','Open planning resources','button')}</section>
  <div class="summary-grid three"><article class="summary"><span>Acquired indicator definitions</span><strong>${dataset.indicators.length}</strong><small>Values and periods vary by indicator</small></article><article class="summary"><span>Reference local areas</span><strong>${coverage.local}</strong><small>${coverage.observed} have one or more acquired observations</small></article><article class="summary"><span>Data edition</span><strong class="date-value">${e(dataset.generated_at.slice(0,10))}</strong><small>Collection status: ${e(statusLabel(dataset.collection?.status))}</small></article></div>
  <section class="panel"><h2>Choose the area to carry into each page</h2>${areaControls()}${identity()}</section>`;
}
function database() {
  const periods=[...new Set(dataset.observations.map(row=>String(row.period)))].sort((a,b)=>b.localeCompare(a,'en',{numeric:true}));
  const observed=dataset.observations.filter(row=>observedValue(row)!==null).length;
  const censusPilot=dataset.analysis?.pilot,scopeCoverage=dataset.analysis?.coverage;
  const currentStage=scopeCoverage
    ? `Current Americas scope: international reference series cover ${scopeCoverage.international_series_country_area_count} countries/areas; official census and domestic hierarchy are integrated for ${scopeCoverage.census_integrated_country_ids.length}. The remaining countries/areas are explicit acquisition work, not evidence that no census exists.`
    : censusPilot?.census_adapter_status==='partial'
    ? `Current pilot: official census population is active for ${censusPilot.census_country_ids.join(', ')} at national and adopted lower levels; ${censusPilot.census_pending_country_ids.join(', ')} remain pending. International country indicators remain a separate context series.`
    : 'Current scaffold: international country reference series, M49 membership, reference map and transparent same-year aggregation.';
  return `<section class="home-intro"><p class="eyebrow">AreaData database</p><h2>Inspect the data behind the dashboard.</h2><p>This pilot exposes the complete static dataset, its indicator dictionary and source register. A cross-country census table builder and public API are later phases; their absence is not shown as completed functionality.</p></section>
  <div class="summary-grid three"><article class="summary"><span>Territories</span><strong>${dataset.territories.length}</strong><small>Registered identities and hierarchy</small></article><article class="summary"><span>Source-reported values</span><strong>${observed}</strong><small>Zero is counted; missing is excluded</small></article><article class="summary"><span>Periods</span><strong>${periods.length}</strong><small>${e(periods.at(-1) || '—')}–${e(periods[0] || '—')}</small></article></div>
  <section class="panel"><div class="panel-heading"><div><p class="eyebrow">Variable dictionary</p><h2>${dataset.indicators.length} acquired indicators</h2></div><div class="actions">${button('catalog-csv','Indicator catalog CSV')}${button('observations-csv','All observations CSV')}${button('territories-csv','Territory register CSV')}</div></div><div class="internal-table-scroll" tabindex="0"><table class="internal-table"><thead><tr><th>Theme / indicator</th><th>Definition and population</th><th>Series / unit / aggregation</th><th>Source</th></tr></thead><tbody>${dataset.indicators.map(indicator=>{const source=sourceFor(dataset,indicator);return `<tr><th>${e(indicator.theme)}<small>${e(indicator.name)} · ${e(indicator.id)}</small></th><td>${e(indicator.definition || 'Not acquired')}<small>${e(indicator.population || 'Population not recorded')}</small></td><td>${e(indicator.series_family || 'Not classified')} · ${e(indicator.display_role || 'Not classified')}<small>${e(indicator.unit)} · ${e(indicator.aggregation || 'none')}${dataset.analysis?.aggregation?.rules?.some(rule=>rule.indicator_id===indicator.id)?' · calculated only with full coverage':''}</small></td><td>${source?link(source.url,source.name):'No source registered'}</td></tr>`;}).join('')}</tbody></table></div><p class="small-note">Downloads retain source IDs, value status, series family and data edition. The dashboard’s calculated values are produced at use time and include their component years and audit trail in selected-area evidence exports.</p></section>
  <section class="panel"><h2>Build the regional database in stages</h2><ol><li>${e(currentStage)}</li><li>Primary data: official census tables, census years, administrative codes and compatible boundaries for every country or area in the selected scope.</li><li>Country depth: municipalities and finer planning-analysis geographies, followed by variable harmonization, table builder, extracts, API, boundary history and reproducibility packages.</li></ol></section>`;
}
function censusHistoryPanel(){
  const history=dataset.analysis?.census_history;
  if(!history?.countries?.length)return '';
  const catalogTotal=history.catalog_scope_country_ids?.length||history.countries.length,cataloged=history.countries.length;
  const byId=new Map(history.countries.map(country=>[country.country_id,country]));
  const referenceFeatures=history.reference_boundaries?.features||[],geometry=mapGeometry(referenceFeatures,'',760,360);
  const ageText=age=>age===0?localCopy('this year','este año','今年'):localCopy(`${age} years old`,`${age} años de antigüedad`,`${age}年前`);
  const statusText=status=>({results_adopted:localCopy('results adopted','resultados adoptados','結果を採用'),official_corrected_estimate_adopted:localCopy('official corrected estimate adopted','estimación oficial corregida adoptada','公式補正推計を採用'),round_reported_results_not_integrated:localCopy('round reported; results not integrated','ronda reportada; resultados no integrados','実施情報あり・結果未統合'),historical_round:localCopy('historical round','ronda histórica','過去の調査'),preparation:localCopy('preparation','preparación','準備中')}[status]||status);
  const countryName=country=>localized(country.names)||areaFor(country.country_id)?.name||country.country_id;
  const intervalText=country=>{const values=censusIntervals(country.recent_rounds);return values.length?values.map(value=>localCopy(`${value} years`,`${value} años`,`${value}年`)).join(' · '):localCopy('Not enough verified rounds','No hay suficientes rondas verificadas','確認済み調査回が不足');};
  const tooltipText=country=>{
    const rounds=country.recent_rounds.map(round=>`${round.year}${round.status.includes('not_integrated')?localCopy(' (not integrated)',' (no integrado)','（未統合）'):''}`).join(' · ');
    const upcoming=country.upcoming?`\n${localCopy('Next information','Información siguiente','次回情報')}: ${country.upcoming.year} (${statusText(country.upcoming.status)})`:'';
    return `${countryName(country)}\n${localCopy('Data used','Datos utilizados','採用データ')}: Census ${country.adopted_data_year} (${ageText(censusAge(country.adopted_data_year,history.as_of_year))})\n${localCopy('Recent rounds','Rondas recientes','直近の調査')}: ${rounds}\n${localCopy('Intervals','Intervalos','実施間隔')}: ${intervalText(country)}${upcoming}\n${localized(country.note)}`;
  };
  const renderPaths=(paths,{showUnregistered=true,interactive=true}={})=>paths.map(path=>{
    const country=byId.get(path.id);
    if(!country)return showUnregistered?`<path class="census-country census-country-unregistered" d="${e(path.d)}" aria-hidden="true"></path>`:'';
    const tooltip=tooltipText(country),recency=censusRecencyClass(country.adopted_data_year,history.as_of_year);
    if(!interactive)return `<path class="census-country census-country-${e(recency)}" d="${e(path.d)}"></path>`;
    return `<path class="census-country census-country-${e(recency)}" d="${e(path.d)}" tabindex="0" data-census-country="${e(country.country_id)}" data-census-tooltip="${e(tooltip)}" aria-label="${e(tooltip)}"><title>${e(tooltip)}</title></path>`;
  }).join('');
  const paths=renderPaths(geometry.paths),pilotGeometry=mapGeometry(referenceFeatures.filter(feature=>byId.has(feature.properties?.territory_id)),'',280,170),pilotPaths=renderPaths(pilotGeometry.paths,{showUnregistered:false,interactive:false});
  const rows=history.countries.map(country=>{
    const adopted=link(country.adopted_source_url,`Census ${country.adopted_data_year}`,'census-year-link');
    const rounds=country.recent_rounds.map(round=>`${link(round.url,String(round.year),'census-round-link')}<small>${e(statusText(round.status))}</small>`).join('<span class="round-separator" aria-hidden="true"> · </span>');
    const upcoming=country.upcoming?`<small>${link(country.upcoming.url,`${country.upcoming.year} ${statusText(country.upcoming.status)}`)}</small>`:'';
    return `<tr><th>${e(countryName(country))}<small>${e(country.country_id)}</small></th><td><strong>${adopted}</strong><small>${e(ageText(censusAge(country.adopted_data_year,history.as_of_year)))}</small></td><td><div class="census-rounds">${rounds}</div>${upcoming}</td><td>${e(intervalText(country))}<small>${e(localized(country.note))}</small><small>${link(country.official_census_url,localCopy('Latest official Census page','Página oficial del Censo más reciente','最新の公式Censusページ'))}</small></td></tr>`;
  }).join('');
  const catalogDescription=localCopy(`${cataloged} of ${catalogTotal} countries/areas are colored from integrated census evidence; the rest are gray and still require source cataloging. Hover or focus a colored country for its census history.`,`${cataloged} de ${catalogTotal} países/áreas están coloreados con evidencia censal integrada; el resto aparece en gris y requiere catalogación. Pase el puntero o enfoque un país para consultar su historia.`,`${catalogTotal}の国・地域のうち、Censusを統合済みの${cataloged}か国を色分けしています。灰色は未収録であり、Censusが存在しないという意味ではありません。`);
  return `<article class="census-history-panel" aria-labelledby="census-history-title"><div class="census-history-heading"><div><p class="eyebrow">${e(localCopy('Census recency','Actualidad censal','Censusの更新状況'))}</p><h3 id="census-history-title">${e(localCopy('Census data year by country','Año de los datos censales por país','各国のCensus採用データ年'))}</h3></div><p>${e(localCopy(`As of ${history.as_of_year}`,`Al año ${history.as_of_year}`,`${history.as_of_year}年時点`))}</p></div><p>${e(localCopy('Darker green means a newer census dataset is currently used by AreaData. Pale red identifies data that are at least 10 years old. A newer announced or conducted round does not change the color until its results are verified and integrated.','El verde más oscuro indica que AreaData usa datos censales más recientes. El rojo claro identifica datos con al menos 10 años de antigüedad. Una ronda anunciada o realizada no cambia el color hasta que sus resultados se verifiquen e integren.','濃い緑ほどAreaDataで使っているCensusデータが新しく、10年以上前のデータは薄赤です。新しい調査の実施・準備情報があっても、結果を確認して統合するまでは地図の色を更新しません。'))}</p><div class="census-history-layout"><figure class="census-history-map"><div class="census-map-wrap"><svg viewBox="0 0 760 360" role="img" aria-labelledby="census-map-title census-map-desc"><title id="census-map-title">${e(localCopy('World map of adopted census data years','Mapa mundial de los años de datos censales adoptados','Census採用データ年の世界地図'))}</title><desc id="census-map-desc">${e(catalogDescription)}</desc>${paths}</svg><div class="census-map-inset"><strong>${e(localCopy(`${cataloged} countries cataloged`,`${cataloged} países catalogados`,`${cataloged}か国を収録`))}</strong><svg viewBox="0 0 280 170" aria-hidden="true">${pilotPaths}</svg></div><div class="census-map-tooltip" role="status" hidden></div></div><figcaption><span><i class="legend-current"></i>${e(localCopy('0–3 years','0–3 años','0～3年前'))}</span><span><i class="legend-recent"></i>${e(localCopy('4–6 years','4–6 años','4～6年前'))}</span><span><i class="legend-aging"></i>${e(localCopy('7–9 years','7–9 años','7～9年前'))}</span><span><i class="legend-overdue"></i>${e(localCopy('10+ years','10 años o más','10年以上前'))}</span><span><i class="legend-unknown"></i>${e(localCopy('Not yet cataloged','Aún no catalogado','未収録'))}</span></figcaption></figure><div class="census-history-table-scroll" tabindex="0"><table class="census-history-table"><caption>${e(localCopy(`Census histories cataloged: ${cataloged} of ${catalogTotal} countries/areas`,`Historias censales catalogadas: ${cataloged} de ${catalogTotal} países/áreas`,`Census履歴の収録：${catalogTotal}の国・地域のうち${cataloged}か国`))}</caption><thead><tr><th>${e(localCopy('Country','País','国'))}</th><th>${e(localCopy('Data used','Datos utilizados','採用データ'))}</th><th>${e(localCopy('Recent rounds','Rondas recientes','直近の調査'))}</th><th>${e(localCopy('Intervals and status','Intervalos y estado','実施間隔・状況'))}</th></tr></thead><tbody>${rows}</tbody></table></div></div><p class="small-note">${e(catalogDescription)} ${e(localCopy('Intervals describe the spacing between recorded rounds. They do not by themselves establish why a census was delayed or omitted; follow the official links for each country.','Los intervalos describen el tiempo entre rondas registradas. Por sí solos no determinan por qué se retrasó u omitió un censo; consulte los enlaces oficiales de cada país.','実施間隔は確認できた調査年の差を示します。遅延・未実施の理由を断定するものではないため、各国の公式リンクも確認してください。'))}</p></article>`;
}
function register() {
  return `<section id="source-register" class="source-register"><h2>Sources and data coverage</h2>${censusHistoryPanel()}${worldMode()?`<details><summary>How regional totals are calculated</summary><p>An exact observation for the selected area has priority. Only indicators with an approved method may be calculated from a complete, non-overlapping membership cover. A country total makes missing municipalities beneath it irrelevant. Percentages and non-additive measures are never simply averaged.</p></details>`:''}<details><summary>Source register (${dataset.sources.length})</summary><ul class="source-list">${dataset.sources.map(source=>`<li><h3>${link(source.url,source.name)}</h3><p>${e(source.publisher)} · ${e(statusLabel(source.status))} · Retrieved ${e(source.retrieved_at || 'Not recorded')} · Reference period ${e(source.reference_period || 'Not recorded')}</p><p>${e(source.note || '')}</p>${source.boundary_source?`<p>Original boundary provider: ${e(source.boundary_source)}${safeUrl(source.source_url)?` · ${link(source.source_url,'Original source')}`:''}</p>`:''}<p>License: ${safeUrl(source.license)?link(source.license,'Source terms'):e(source.license || 'Not recorded')}${safeUrl(source.license_url)?` · ${link(source.license_url,'License source')}`:''}${source.license_detail?` · ${e(source.license_detail)}`:''}</p><small>Raw-file SHA-256: ${e(source.sha256 || 'Not available')}</small></li>`).join('')}</ul></details>
  <details ${dataset.gaps.length?'open':''}><summary>Remaining acquisition gaps (${dataset.gaps.length})</summary><ul class="gap-list">${dataset.gaps.map(gap=>{const display=localizedGap(gap);return `<li><strong>${e(display.category)} — ${e(translateText(statusLabel(gap.status),language))}</strong><p>${e(display.detail)}</p><p class="small-note">${e(localCopy('Next:','Siguiente:','次の対応：'))} ${e(display.next_action)}</p></li>`;}).join('') || '<li>No acquisition gaps are listed. This is not a certification of complete national coverage.</li>'}</ul></details><p class="small-note">Data edition ${e(dataset.generated_at)} · Schema ${e(dataset.schema_version)}. Source values, proposals and formal decisions are separate records. Source geography and release dates can differ.</p></section>`;
}
function updateHeader() {
  document.getElementById('dataset-name').textContent='Explore the world through census data';
  document.title=page==='home'?`AreaData — ${translateText('From the world to your community.',language)}`:`${translateText(pageNames[page],language)} — ${translateText(displayAreaName(currentArea()),language)} | AreaData`;
  document.querySelectorAll('[data-page-link]').forEach(anchor=>{const target=anchor.dataset.pageLink;anchor.href=pageUrl(target);anchor.dataset.i18n=pageNames[target];anchor.textContent=pageNames[target];if(target===page)anchor.setAttribute('aria-current','page');else anchor.removeAttribute('aria-current');});
  document.querySelectorAll('[data-brand-link]').forEach(anchor=>{anchor.href=new URL('./',base).href;anchor.setAttribute('aria-label','Return to the AreaData start');});
}
function render() {
  const active=document.activeElement;
  const focusId=active?.id, mapId=active?.dataset.mapId, rankId=active?.dataset.rankId;
  const previousDisclosure=document.querySelector('[data-all-area-selector]');
  if(previousDisclosure)allAreaOpen=previousDisclosure.open;
  const selection=active instanceof HTMLInputElement ? [active.selectionStart,active.selectionEnd] : null;
  updateHeader();
  app.innerHTML=`<div class="page-heading ${page==='home'?'home-heading':''}"><div><p class="eyebrow">${page==='home'?'AreaData · Census & regional statistics':`${e(displayAreaName(areaFor(dataset.country.national_territory_id)))} · ${e(pageNames[page])}`}</p><h1>${page==='home'?'From the world to your community.':e(displayAreaName(currentArea()))}</h1></div><div class="actions">${button('share','Share selection')}${button('print','Print page')}</div></div><p id="selection-status" class="sr-only" aria-live="polite">${e(language==='ja'?`選択地域：${translateText(displayAreaName(currentArea()),language)}。指標：${translateText(currentMetric()?.name || 'no indicator',language)}。期間：${translateText(state.period,language)}。`:language==='es'?`Área seleccionada: ${translateText(displayAreaName(currentArea()),language)}. Indicador: ${translateText(currentMetric()?.name || 'no indicator',language)}. Período: ${translateText(state.period,language)}.`:`Selected ${displayAreaName(currentArea())}, ${currentMetric()?.name || 'no indicator'}, ${state.period}.`)}</p><p id="action-status" class="action-status" role="status"></p>${state.notices.map(notice=>`<p class="notice">${e(notice)}</p>`).join('')}${updateBanner()}${page==='planning'?'':scopeBanner()}${({home,territorial,thematic,database,planning}[page] || home)()}${register()}`;
  translateInterface(document,language);
  if(focusId) {const next=document.getElementById(focusId);const disclosure=next?.closest('details');if(disclosure)disclosure.open=true;next?.focus({preventScroll:true});if(selection&&next instanceof HTMLInputElement)try{next.setSelectionRange(...selection);}catch{}}
  if(mapId) [...document.querySelectorAll('[data-map-id]')].find(node=>node.dataset.mapId===(page==='thematic'?comparisonFocusId:state.selected))?.focus({preventScroll:true});
  if(rankId) {
    const next=[...document.querySelectorAll('[data-rank-id]')].find(node=>node.dataset.rankId===rankId);
    const disclosure=next?.closest('details');if(disclosure)disclosure.open=true;
    next?.focus({preventScroll:true});revealRankingSelection();
  }
}
function commit(next, {replace=false}={}) {
  state=next;
  const url=new URL(location.href);url.search=routeWithLanguage(state);
  history[replace?'replaceState':'pushState']({},'',url);
  render();
}
let deferredCommitSequence=0;
function commitAfterInput(next) {
  const sequence=++deferredCommitSequence;
  document.documentElement.setAttribute('aria-busy','true');
  setTimeout(()=>{
    if(sequence!==deferredCommitSequence)return;
    try {commit(next);}
    finally {document.documentElement.removeAttribute('aria-busy');}
  },0);
}
function revealRankingSelection({focus=false,id=state.selected}={}) {
  const row=[...document.querySelectorAll('#ranking-content [data-ranking-id]')].find(node=>node.dataset.rankingId===id);
  const container=row?.closest('.ranking-scroll');
  if(!row || !container)return false;
  const details=row.closest('details');if(details)details.open=true;
  const containerRect=container.getBoundingClientRect(),rowRect=row.getBoundingClientRect();
  container.scrollTop=rankingScrollTop({scrollTop:container.scrollTop,clientHeight:container.clientHeight,scrollHeight:container.scrollHeight,rowTop:rowRect.top-containerRect.top+container.scrollTop,rowHeight:rowRect.height});
  if(focus)row.querySelector('button')?.focus({preventScroll:true});
  return true;
}
function choose(id,{fromMap=false}={}) {
  wholeMap=false;areaSearch='';comparisonFocusId='';
  const next=selectTerritory(dataset,state,id);
  if(page==='home')next.level=comparisonLevelForArea(dataset,id,next.level);
  if(fromMap && page==='thematic') {
    // Map highlighting does not redefine the comparison cohort.
    next.level=state.level;
    rankSearch=rankingReveal(comparisonRows(dataset,next),id,rankSearch).query;
  }
  commit(next);
  if(fromMap && page==='thematic')revealRankingSelection();
}
function focusComparison(id,{fromMap=false}={}) {
  const rows=comparisonRows(dataset,state);
  if(!rows.some(row=>row.area.id===id))return;
  comparisonFocusId=id;
  rankSearch=rankingReveal(rows,id,rankSearch).query;
  render();
  revealRankingSelection({id,focus:!fromMap});
  if(fromMap)[...document.querySelectorAll('[data-map-id]')].find(node=>node.dataset.mapId===id)?.focus({preventScroll:true});
  const focusName=displayAreaName(areaFor(id)),diagnosticName=displayAreaName(currentArea());
  actionStatus(localCopy(`${focusName} is highlighted for comparison. The diagnostic area remains ${diagnosticName}.`,`${focusName} está resaltada para la comparación. El área de diagnóstico sigue siendo ${diagnosticName}.`,`${focusName}を比較内で注目しています。分析対象は${diagnosticName}のままです。`));
}
function inspectInternal(target) {
  const panel=target.closest('[data-internal-comparison]');
  if(!panel)return;
  const id=target.dataset.internalId;
  const rows=[...panel.querySelectorAll('[data-internal-row]')];
  for(const row of rows)row.classList.toggle('inspected',row.dataset.internalRow===id);
  for(const shape of panel.querySelectorAll('.internal-area'))shape.classList.toggle('inspected',shape.dataset.internalId===id);
  const row=rows.find(item=>item.dataset.internalRow===id);
  const status=panel.querySelector('.internal-inspection');
  if(status&&row)status.textContent=`${row.querySelector('th').innerText.trim().replace(/\s+/g,' ')} — ${row.querySelector('td').innerText.trim().replace(/\s+/g,' ')}. Diagnostic area remains ${currentArea().name}.`;
}
function actionStatus(text) {const target=document.getElementById('action-status');target.textContent=text;}
function download(text, filename, type) {
  const object=URL.createObjectURL(new Blob([text],{type}));
  const anchor=document.createElement('a');anchor.href=object;anchor.download=filename;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(object),1000);actionStatus(`Prepared ${filename} for ${currentArea().name}.`);
}
function seriesCsv(indicatorId, territoryId) {
  const indicator=metricFor(indicatorId), area=areaFor(territoryId);
  const rows=seriesFor(dataset,territoryId,indicatorId),extended=!!dataset.analysis || rows.some(row=>!observationContext(dataset,area,indicator,row).comparable);
  return makeCsv([['Country','Territory','Territory ID','Level','Indicator','Indicator ID','Period','Value','Unit','Status','Source URL','Retrieved at','Data edition',...(extended?['Definition ID','Definition','Population','Method','Comparable context','Comparison reason','Observation boundary edition']:[])],...rows.map(row=>{const context=observationContext(dataset,area,indicator,row),source=context.source;return [dataset.country.name,area.name,area.id,area.level,indicator.name,indicator.id,row.period,observedValue(row),context.unit,row.status,safeUrl(source?.url),source?.retrieved_at,dataset.generated_at,...(extended?[context.definition_id,context.definition,context.population,context.method,context.comparable,context.reason,row.boundary_version]:[])];})]);
}
function catalogCsv() {
  return makeCsv([['Theme','Indicator ID','Indicator','Series family','Display role','Definition','Population','Unit','Measurement method','Configured aggregation','Period policy','Source ID','Data edition'],...dataset.indicators.map(indicator=>[indicator.theme,indicator.id,indicator.name,indicator.series_family,indicator.display_role,indicator.definition,indicator.population,indicator.unit,indicator.measurement_method,indicator.aggregation,indicator.period_policy,indicator.source_id,dataset.generated_at])]);
}
function observationsCsv() {
  return makeCsv([['Territory ID','Indicator ID','Period','Value','Unit','Status','Source ID','Definition ID','Definition','Population','Measurement method','Boundary edition','Footnote','Data edition'],...dataset.observations.map(row=>{const indicator=metricFor(row.indicator_id);return [row.territory_id,row.indicator_id,row.period,observedValue(row),row.unit || indicator?.unit,row.status,row.source_id,row.definition_id || indicator?.definition_id,row.definition || indicator?.definition,row.population || indicator?.population,row.measurement_method || indicator?.measurement_method,row.boundary_version,row.footnote,dataset.generated_at];})]);
}
function territoriesCsv() {
  return makeCsv([['Territory ID','Name','Level','Type','Parent ID','Country ID','Official code','Code system','Boundary edition','Source ID','Data edition'],...dataset.territories.map(area=>[area.id,area.name,area.level,area.type,area.parent_id,area.country_id,area.official_code,area.code_system,area.boundary_version,area.source_id,dataset.generated_at])]);
}
function showCensusTooltip(target,event){
  const wrap=target.closest('.census-map-wrap'),tip=wrap?.querySelector('.census-map-tooltip');
  if(!tip)return;
  tip.textContent=target.dataset.censusTooltip||'';tip.hidden=false;
  const wrapRect=wrap.getBoundingClientRect(),targetRect=target.getBoundingClientRect();
  const x=event?.clientX??(targetRect.left+targetRect.width/2),y=event?.clientY??targetRect.top;
  tip.style.left=`${Math.min(Math.max(x-wrapRect.left,130),Math.max(130,wrapRect.width-130))}px`;
  tip.style.top=`${Math.max(8,y-wrapRect.top-12)}px`;
}
function hideCensusTooltip(target){
  const tip=target.closest('.census-map-wrap')?.querySelector('.census-map-tooltip');
  if(tip)tip.hidden=true;
}
app.addEventListener('pointerover',event=>{const target=event.target.closest('[data-census-tooltip]');if(target)showCensusTooltip(target,event);});
app.addEventListener('pointermove',event=>{const target=event.target.closest('[data-census-tooltip]');if(target)showCensusTooltip(target,event);});
app.addEventListener('pointerout',event=>{const target=event.target.closest('[data-census-tooltip]');if(target&&!target.contains(event.relatedTarget))hideCensusTooltip(target);});
app.addEventListener('focusin',event=>{const target=event.target.closest('[data-census-tooltip]');if(target)showCensusTooltip(target);});
app.addEventListener('focusout',event=>{const target=event.target.closest('[data-census-tooltip]');if(target)hideCensusTooltip(target);});
app.addEventListener('change',event=>{
  const control=event.target.dataset.control;
  if(control==='area')choose(event.target.value);
  if(control==='hierarchy') {
    wholeMap=false;areaSearch='';comparisonFocusId='';
    // Large country pages can contain hundreds of map paths and indicator cards.
    // Let the native select event finish before rebuilding the page so choosing a
    // parent always completes instead of leaving a parent URL over child content.
    commitAfterInput(selectHierarchyOption(dataset,state,event.target.dataset.parent,event.target.value));
  }
  if(control==='metric') {comparisonFocusId='';const metric=event.target.value;commit({...state,metric,requestedMetric:undefined,sourceDataset:undefined,notices:[]});}
  if(control==='period'){comparisonFocusId='';commit({...state,period:event.target.value,notices:[]});}
  if(control==='level'){wholeMap=true;comparisonFocusId='';commit({...state,level:event.target.value,notices:[]});}
  if(control==='rank-order'){rankOrder=event.target.value;render();}
});
app.addEventListener('input',event=>{
  if(event.target.dataset.control==='area-search'){areaSearch=event.target.value;render();}
  if(event.target.dataset.control==='ranking-search'){rankSearch=event.target.value;document.getElementById('ranking-content').innerHTML=rankingContent(comparisonRows(dataset,state));}
});
app.addEventListener('keydown',event=>{
  const internalTarget=event.target.closest('.internal-area[data-internal-id]');
  if(internalTarget&&['Enter',' '].includes(event.key)){event.preventDefault();inspectInternal(internalTarget);return;}
  const target=event.target.closest('[data-map-id]');
  if(!target)return;
  if(['Enter',' '].includes(event.key)){event.preventDefault();if(page==='thematic')focusComparison(target.dataset.id,{fromMap:true});else choose(target.dataset.id,{fromMap:true});return;}
  const keys=['ArrowDown','ArrowRight','ArrowUp','ArrowLeft','Home','End'];
  if(!keys.includes(event.key))return;
  event.preventDefault();const paths=[...target.ownerSVGElement.querySelectorAll('[data-map-id]')],index=paths.indexOf(target);
  const next=event.key==='Home'?0:event.key==='End'?paths.length-1:(index+(['ArrowDown','ArrowRight'].includes(event.key)?1:-1)+paths.length)%paths.length;
  paths.forEach(path=>path.setAttribute('tabindex','-1'));paths[next].setAttribute('tabindex','0');paths[next].focus();
});
app.addEventListener('click',async event=>{
  const target=event.target.closest('[data-action]');if(!target)return;
  const action=target.dataset.action;
  const stem=safeFilename(`${dataset.country.id}-${state.selected}-${state.period || 'no-period'}`);
  try {
    if(action==='inspect-internal')inspectInternal(target);
    else if(action==='focus-comparison')focusComparison(target.dataset.id,{fromMap:!!target.dataset.mapId});
    else if(action==='select')choose(target.dataset.id,{fromMap:!!target.dataset.mapId});
    else if(action==='national')choose(dataset.country.national_territory_id);
    else if(action==='map-extent'){wholeMap=!wholeMap;render();}
    else if(action==='compare'){state={...state,metric:target.dataset.id,period:target.dataset.period || state.period};location.href=pageUrl('thematic');}
    else if(action==='show-selected'){
      rankSearch=rankingReveal(comparisonRows(dataset,state),state.selected,rankSearch).query;render();
      if(revealRankingSelection({focus:true}))actionStatus('The selected area is visible in the ranking panel. Missing observations remain unranked.');
      else actionStatus('The selected area has no rank in this comparison set. Its details remain below the map.');
    }
    else if(action==='share'){
      const url=new URL(location.href);url.search=routeQuery(dataset,state);
      if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(url.href);actionStatus('Selection link copied.');return;}catch{}}
      const input=document.createElement('input');input.value=url.href;input.readOnly=true;input.setAttribute('aria-label','Selection link to copy');const status=document.getElementById('action-status');status.textContent='Copy this selection link: ';status.append(input);input.focus();input.select();
    }
    else if(action==='print')window.print();
    else if(action==='diagnostic-markdown')download(diagnosticMarkdown(dataset,state.selected,state.period),`${stem}-diagnostic.md`,'text/markdown;charset=utf-8');
    else if(action==='diagnostic-html')download(diagnosticHtml(dataset,state.selected,state.period),`${stem}-diagnostic.html`,'text/html;charset=utf-8');
    else if(action==='diagnostic-csv')download(diagnosticCsv(dataset,state.selected,state.period),`${stem}-diagnostic.csv`,'text/csv;charset=utf-8');
    else if(action==='planning-markdown')download(planningMarkdown(dataset,state.selected,state.period,language),`${stem}-planning-base.md`,'text/markdown;charset=utf-8');
    else if(action==='planning-html')download(planningHtml(dataset,state.selected,state.period,language),`${stem}-planning-base.html`,'text/html;charset=utf-8');
    else if(action==='documents-csv')download(documentsCsv(dataset,state.selected),`${safeFilename(dataset.country.id+'-'+state.selected)}-materials.csv`,'text/csv;charset=utf-8');
    else if(action==='planning-csv')download(evidenceCsv(dataset,state.selected,state.period),`${stem}-evidence.csv`,'text/csv;charset=utf-8');
    else if(action==='indicator-csv'){
      const period=target.dataset.period || state.period;
      download(evidenceCsv(dataset,state.selected,period,[target.dataset.id]),`${safeFilename(`${dataset.country.id}-${state.selected}-${period || 'no-period'}`)}-${safeFilename(target.dataset.id)}.csv`,'text/csv;charset=utf-8');
    }
    else if(action==='series-csv')download(seriesCsv(target.dataset.id,target.dataset.territory),`${safeFilename(target.dataset.territory)}-${safeFilename(target.dataset.id)}-history.csv`,'text/csv;charset=utf-8');
    else if(action==='catalog-csv')download(catalogCsv(),`${safeFilename(dataset.country.id)}-indicator-catalog.csv`,'text/csv;charset=utf-8');
    else if(action==='observations-csv')download(observationsCsv(),`${safeFilename(dataset.country.id)}-observations.csv`,'text/csv;charset=utf-8');
    else if(action==='territories-csv')download(territoriesCsv(),`${safeFilename(dataset.country.id)}-territories.csv`,'text/csv;charset=utf-8');
    else if(action==='comparison-csv'){
      const indicator=currentMetric();
      const entries=comparisonRows(dataset,state),extended=!!dataset.analysis || entries.some(row=>row.status==='incomparable');
      const rows=[['Country','Level','Territory ID','Territory','Code','Indicator ID','Indicator','Period','Value','Unit','Status','Source URL','Data edition',...(extended?['Comparison eligible','Comparison reason','Definition ID','Definition','Population','Method']:[])],...entries.map(row=>{const context=observationContext(dataset,row.area,indicator,row.row);return [dataset.country.name,row.area.level,row.area.id,row.area.name,row.area.official_code,indicator.id,indicator.name,row.period || state.period,observedValue(row.row),context.unit,row.row?.status || row.status,safeUrl(context.source?.url),dataset.generated_at,...(extended?[finite(row.value),row.reason || context.reason,context.definition_id,context.definition,context.population,context.method]:[])];})];
      download(makeCsv(rows),`${safeFilename(dataset.country.id+'-'+state.level+'-'+state.metric+'-'+state.period)}-comparison.csv`,'text/csv;charset=utf-8');
    }
  } catch(error) {actionStatus(`Could not complete this action: ${error.message}. Your selection and evidence are retained.`);}
});
document.querySelectorAll('[data-language]').forEach(control=>control.addEventListener('click',()=>{
  const next=control.dataset.language;if(!SUPPORTED_LANGUAGES.includes(next)||next===language)return;
  language=next;try{localStorage.setItem('areadata-language',language);}catch{}
  const url=new URL(location.href);url.searchParams.set('lang',language);history.replaceState({},'',url);if(dataset&&state)render();else translateInterface(document,language);
}));

window.addEventListener('popstate',()=>{language=resolveLanguage({query:new URLSearchParams(location.search).get('lang'),stored:storedLanguage(),browserLanguages:navigator.languages||[navigator.language]});state=initialState(dataset,location.search);wholeMap=false;areaSearch='';rankSearch='';comparisonFocusId='';render();});

translateInterface(document,language);
try {
  const response=await fetch(new URL('data/dashboard.json',base));
  if(!response.ok)throw new Error(`Data request returned HTTP ${response.status}`);
  dataset=await response.json();
  if(dataset.schema_version!=='0.2'||!dataset.country||!Array.isArray(dataset.territories)||!Array.isArray(dataset.indicators)||!Array.isArray(dataset.observations))throw new Error('Unsupported or incomplete dataset');
  const statusResponse=await fetch(new URL('data/update-status.json',base),{cache:'no-store'}).catch(()=>null);
  if(statusResponse?.ok)updateStatus=await statusResponse.json().catch(()=>null);
  state=initialState(dataset,location.search);
  render();
} catch(error) {
  app.innerHTML=`<section class="panel error-panel"><h1>Dashboard data could not be loaded</h1><p>${e(error.message)}</p><p>Serve this folder over HTTP using the project’s local server, then reload. The dataset is stored at <code>data/dashboard.json</code>; no remote service is required after collection.</p><button class="button" id="reload-page">Reload</button></section>`;
  translateInterface(document,language);
  document.getElementById('reload-page').addEventListener('click',()=>location.reload());
}

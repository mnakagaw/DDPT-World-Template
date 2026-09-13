import {
  finite, escapeHtml as e, safeUrl, displayValue, statusLabel, sourceFor,
  periodsFor, observationState, localLevels, levelLabel, nationalOnly, initialState,
  selectTerritory, territoryLineage, territoryOptionLabel, hierarchyControls, selectHierarchyOption, routeQuery, countryDiagnosticUrl, comparisonRows, comparisonCompatibility, rankedRows, searchRows, rankingReveal, rankingScrollTop, distribution,
  seriesFor, observedValue, makeCsv, evidenceCsv, safeFilename, planningMarkdown,
  planningHtml, documentsCsv, mapGeometry, seriesGeometry
} from './model.mjs';
import {planningSettings,planningDocuments,documentGroups,documentPeriod,officialMapState,hasDocumentReference,selectedGaps,relatedResourceUrl,categoryLabels} from './planning.mjs';
import {renderDocumentGroups,renderDocument} from './planning-view.mjs';
import {comparisonSet,observationMeaning,observationContext,isTerminalTerritory} from './analysis.mjs';
import {renderInternalComparison,diagnosticMarkdown,diagnosticHtml,diagnosticCsv} from './diagnostic.mjs';

const base = new URL('../', import.meta.url);
const app = document.getElementById('app');
const page = document.body.dataset.page || 'home';
const pageNames = {home:'Explore',territorial:'Territorial diagnostic',thematic:'Thematic diagnostic',planning:'Planning and resources'};
let dataset, state, updateStatus;
let areaSearch='', rankSearch='', rankOrder='desc', wholeMap=false, allAreaOpen=false;
const fmt = value => displayValue(value, dataset?.country.locale || 'en');
const areaFor = id => dataset.territories.find(area => area.id === id);
const metricFor = id => dataset.indicators.find(indicator => indicator.id === id);
const currentArea = () => areaFor(state.selected);
const currentMetric = () => metricFor(state.metric);
const worldMode = () => dataset?.analysis?.kind==='world';
const link = (url, label, classes='') => safeUrl(url) ? `<a class="${e(classes)}" href="${e(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${e(label)}<span class="sr-only"> (opens a new tab)</span></a>` : `<span>${e(label)} · No verified link</span>`;
const button = (action, label, attributes='', classes='button secondary') => `<button type="button" class="${classes}" data-action="${action}" ${attributes}>${label}</button>`;
const pageUrl = target => {const url = new URL(target==='home' ? './' : `${target}/`,base);url.search=routeQuery(dataset,state);return url.href;};
const pageLink = (target, label, classes='button secondary') => `<a class="${classes}" href="${e(pageUrl(target))}">${e(label)}</a>`;
const sourceNote = (indicator, observation, prefix='Source') => {
  const source=sourceFor(dataset,indicator,observation);
  return `<p class="source-note">${prefix}: ${source ? link(source.url,source.name) : 'No verified source collected'}. ${source?.retrieved_at ? `Retrieved ${e(source.retrieved_at.slice(0,10))}.` : ''}</p>`;
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
  const flatSelector=`<label class="field" for="area-select"><span>Selected area${hierarchy.length?' · all records':''}</span><select id="area-select" data-control="area">${groups.map(level=>`<optgroup label="${e(levelLabel(level))}">${areas.filter(area=>area.level===level).map(area=>`<option value="${e(area.id)}" ${area.id===state.selected?'selected':''}>${e(territoryOptionLabel(dataset,area))}${area.level==='national'?(worldMode()?' · world':' · national'):''}</option>`).join('')}</optgroup>`).join('')}</select></label>`;
  return `<div class="area-controls">${hierarchy.length?`<div class="hierarchy-controls"><p class="small-note">Showing <strong>${e(currentArea().name)}</strong>. Choose “Whole …” to make that parent the selected area and clear its lower-area selection.</p>${hierarchy.map((control,index)=>`<label class="field" for="hierarchy-${index}"><span>${e(control.levels.map(levelLabel).join(' / '))} · within ${e(control.parent.name)}</span><select id="hierarchy-${index}" data-control="hierarchy" data-parent="${e(control.parent.id)}">${control.context?`<option value="context" selected disabled>${e(control.context.label)}</option>`:''}${control.options.map(option=>`<option value="${e(option.value)}" ${option.value===control.value?'selected':''}>${e(option.label)}</option>`).join('')}</select></label>`).join('')}</div><details class="micro-details" data-all-area-selector ${allAreaOpen?'open':''}><summary>All-area selector</summary>${flatSelector}</details>`:flatSelector}
  <label class="field" for="area-search"><span>Find an area by name or code</span><input id="area-search" type="search" data-control="area-search" value="${e(areaSearch)}" autocomplete="off" placeholder="Name or code"></label>
  ${areaSearch?`<div class="search-results" aria-label="Area search results">${hits.length?hits.slice(0,50).map(area=>button('select',`${e(area.name)}<small>${e(levelLabel(area.level))} · ${e(area.official_code || area.id)}</small>`,`data-id="${e(area.id)}"`,'result-button')).join(''):'<p>No matching areas.</p>'}${hits.length>50?`<p>${hits.length} matches; narrow your search to see more.</p>`:''}</div>`:''}
  ${state.selected!==dataset.country.national_territory_id?button('national',worldMode()?'Return to world view':'Return to national view','','text-button'):''}</div>`;
}
function hierarchyNavigation() {
  const lineage=territoryLineage(dataset,state.selected),children=comparisonSet(dataset,state.selected).terminal?[]:dataset.territories.filter(area=>area.parent_id===state.selected);
  return `<nav class="hierarchy-navigation" aria-label="Area hierarchy">${lineage.map(area=>area.id===state.selected?`<span aria-current="location">${e(area.name)}</span>`:button('select',e(area.name),`data-id="${e(area.id)}"`,'text-button')).join('<span aria-hidden="true"> › </span>')}</nav>${children.length?`<details class="child-navigation"><summary>Explore lower areas (${children.length})</summary><div>${children.map(area=>button('select',e(territoryOptionLabel(dataset,area)),`data-id="${e(area.id)}"`,'text-button')).join('')}</div></details>`:''}`;
}
function countryDetailLink() {
  const target=countryDiagnosticUrl(dataset,state,base);
  if(!target)return '';
  return `<p class="country-detail-link"><a class="button secondary" href="${e(target)}">Open ${e(currentArea().name)} country diagnostic</a><small>The selected period is retained. An indicator is carried across only through an explicit concept mapping; otherwise the country edition explains its separate default indicator. Country data are not estimated from world values. Browser Back returns to this world selection.</small></p>`;
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
  if(worldMode())return '<div class="scope-banner"><strong>World, continental and country evidence.</strong> Exploration groups have explicit membership and do not establish legal planning authorities. Whole-area values are shown only when a matching source observation exists; member values are not averaged or substituted.</div>';
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
  const features=allFeatures.filter(feature=>worldLocation&&childIds.size?childIds.has(feature.properties?.territory_id):areaFor(feature.properties?.territory_id)?.level===targetLevel);
  const fitId = wholeMap || selected.level==='national' || worldLocation&&childIds.size ? '' : selected.id;
  const geometry=mapGeometry(features,fitId);
  const rows=thematic?comparisonRows(dataset,state):[];
  const stats=distribution(rows);
  const values=new Map(rows.map(row=>[row.area.id,row.value]));
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
  const title=planning?(mapSettings.mode==='official_status'?`Documented institutional states · ${categoryLabels[mapSettings.category]} · ${mapSettings.period}`:'Material references by area'+(mapSettings.category?' · '+categoryLabels[mapSettings.category]:'')+(mapSettings.period?' · '+mapSettings.period:'')):thematic?`${currentMetric()?.name || 'Indicator'} · ${state.period || 'No period'}`:'Location';
  const sourceIds=[...new Set(features.map(feature=>feature.properties?.source_id).filter(Boolean))];
  const boundarySources=dataset.sources.filter(source=>sourceIds.includes(source.id) || /boundary|boundaries/i.test(source.id+' '+source.name));
  const chosenTab=geometry.paths.find(path=>path.id===state.selected)?.id || geometry.paths[0]?.id;
  return `<section class="panel map-panel" aria-labelledby="map-title"><div class="panel-heading"><div><p class="eyebrow">${e(levelLabel(targetLevel))} reference boundaries</p><h2 id="map-title">${e(title)}</h2></div>${selected.level!=='national'&&geometry.paths.length?button('map-extent',wholeMap?'Fit selected area':'Show whole country','','text-button'):''}</div>
  ${geometry.paths.length ? `<svg class="geographic-map" viewBox="0 0 760 400" role="group" aria-label="${e(title)}. Select an area with Enter. Arrow keys move between boundaries."><title>${e(title)} — ${e(dataset.country.name)}; ${fitId&&geometry.selectedHasGeometry?`view fitted to ${e(selected.name)}`:'whole available boundary layer'}</title><rect width="760" height="400" fill="#f4f8f7"/>${geometry.paths.map(path=>{const area=areaFor(path.id),value=values.get(path.id);const label=`${area?.name || path.id}${thematic?`: ${finite(value)?fmt(value)+' '+currentMetric().unit:'No data'} for ${state.period}`:''}`;return `<path d="${path.d}" fill="${colour(path.id)}" fill-rule="evenodd" class="map-area ${path.id===state.selected?'selected':''}" role="button" aria-label="${e(label)}" aria-pressed="${path.id===state.selected}" tabindex="${path.id===chosenTab?'0':'-1'}" data-action="select" data-id="${e(path.id)}" data-map-id="${e(path.id)}"><title>${e(label)}</title></path>`;}).join('')}</svg>` : '<div class="map-unavailable"><strong>No verified boundaries available for this level.</strong><p>Use the area selector and search. Acquired statistics and documents remain accessible.</p></div>'}
  ${selected.level!=='national'&&!childIds.size&&!features.some(feature=>feature.properties?.territory_id===selected.id)?`<p class="missing-note">No boundary is joined to ${e(selected.name)} at this map level. No nearby polygon is substituted.</p>`:''}
  <p class="map-legend">${planning?(mapSettings.mode==='official_status'?`${mapSettings.statuses.map(status=>`<span class="legend-item"><svg width="12" height="12" aria-hidden="true"><rect width="12" height="12" fill="${e(status.color)}"/></svg> ${e(status.label)}</span>`).join(' · ')}. Gray = no matched evidence; amber = conflicting evidence. States apply only to ${e(mapSettings.period)} and this document category. Select an area to inspect the cited evidence.`:`Green = a verified material reference is available; gray = no verified reference collected. ${mapSettings.period?'Applies only to '+e(mapSettings.period)+'.':'Includes different document periods.'}${mapSettings.category?' Category: '+e(categoryLabels[mapSettings.category])+'.':''} These are collection states, not counts of approved plans.`):thematic?`Colors use five equal value intervals across all ${e(levelLabel(state.level).toLowerCase())} areas for this indicator and period; search does not change the scale. Gray = No data. High values are not automatically better.`:'A location map. Fill colors do not represent population or service levels.'} <span class="legend-selected">Gold outline</span> = selected area.</p>
  <p class="source-note">Boundary source: ${boundarySources.length?boundarySources.map(source=>link(source.url,source.name)).join(' · '):'See the source register; boundary authority and edition must be verified.'} Reference boundaries are not a legal boundary certification. Keyboard: arrows / Home / End, then Enter or Space.</p>${dataset.country.geography_note?`<p class="source-note"><strong>Geographic scope:</strong> ${e(dataset.country.geography_note)}</p>`:''}</section>`;
}
function facts() {
  const priority=dataset.indicators.filter(indicator=>/population|household/i.test(indicator.name)).slice(0,3);
  const indicators=priority.length?priority:dataset.indicators.slice(0,3);
  return `<div class="basic-facts">${indicators.map(indicator=>{const result=observationState(dataset,state.selected,indicator.id,state.period);return `<div class="fact"><span>${e(indicator.name)}</span><strong>${fmt(result.value)}</strong><small>${e(result.row?.unit || indicator.unit)} · ${e(state.period || 'No source period')} · ${e(statusLabel(result.status))}</small></div>`;}).join('')}</div>`;
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
  ${geo&&geo.points.length>1?`<svg viewBox="0 0 600 170" role="img" aria-label="${e(indicator.name)} time series for ${e(area.name)}. Exact values and sources are in the table below."><title>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</title><line x1="40" y1="140" x2="580" y2="140" stroke="#c8d5d7"/>${geo.segments.map(points=>`<polyline points="${points}" fill="none" stroke="#267966" stroke-width="2.5"/>`).join('')}${geo.points.map(point=>`<circle cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" r="3" fill="#267966"><title>${e(point.row.period)}: ${e(fmt(point.row.value))} ${e(indicator.unit)}</title></circle>`).join('')}<text x="3" y="21">${e(fmt(geo.max))}</text><text x="3" y="135">${e(fmt(geo.min))}</text><text x="40" y="161">${e(series[0].period)}</text><text x="580" y="161" text-anchor="end">${e(series.at(-1).period)}</text></svg><p class="small-note">Source periods in sequence. Missing or incompatible observations break the line; no missing values are estimated.</p>`:'<p class="small-note">Fewer than two comparable observations; no trend is inferred.</p>'}
  <p class="source-note">Source: ${sources.map(source=>link(source.url,source.name)).join(' · ') || 'See source register'}.</p>
  <details><summary>Time-series values and sources (${series.length})</summary><div class="table-scroll"><table><caption>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</caption><thead><tr><th scope="col">Period</th><th scope="col">Value</th><th scope="col">Status</th><th scope="col">Source</th></tr></thead><tbody>${series.map(row=>{const source=sourceFor(dataset,indicator,row);return `<tr><td>${e(row.period)}</td><td>${fmt(observedValue(row))} ${e(observationMeaning(indicator,row).unit)}</td><td>${e(statusLabel(row.status))}${observationContext(dataset,area,indicator,row).comparable?'':'<br>'+e(observationContext(dataset,area,indicator,row).reason)}</td><td>${source?link(source.url,source.name):'Not recorded'}</td></tr>`;}).join('')}</tbody></table></div></details>
  ${button('series-csv','Time series CSV',`data-id="${e(indicator.id)}" data-territory="${e(territoryId)}"`,'text-button')}</figure>`;
}
function metricCard(indicator) {
  const result=observationState(dataset,state.selected,indicator.id,state.period);
  const national=observationState(dataset,dataset.country.national_territory_id,indicator.id,state.period);
  const meaning=observationContext(dataset,currentArea(),indicator,result.row),referenceMeaning=observationContext(dataset,areaFor(dataset.country.national_territory_id),indicator,national.row);
  const local=currentArea().level!=='national';
  return `<article class="indicator-card"><div class="indicator-heading"><h3>${e(indicator.name)}</h3><span class="unit">${e(meaning.unit)}</span></div><div class="value-row"><strong>${fmt(result.value)}</strong><span>${e(statusLabel(result.status))} · ${e(state.period || 'No source period')}</span></div>${stateMessage(result)}
  ${local?`<p class="national-reference">${worldMode()?'World reference':'National reference'} — ${e(dataset.country.name)}: <strong>${fmt(national.value)}</strong> ${e(referenceMeaning.unit)} · ${e(state.period)}. ${e(statusLabel(national.status))}.${referenceMeaning.comparable?'':` ${e(referenceMeaning.reason)}`}</p>`:''}
  <p class="definition">${e(meaning.definition || 'Definition not acquired.')}</p>${meaning.comparable?'':`<p class="missing-note">${e(meaning.reason)} Its original value remains visible; a comparable trend is not inferred.</p>`}${sourceNote(indicator,result.row,finite(result.value)?'Selected-area source':'Available indicator source; selected-area value not acquired')}
  ${seriesFigure(indicator)}<div class="actions">${button('compare','Compare this indicator',`data-id="${e(indicator.id)}"`,'text-button')}${button('indicator-csv','Selected-period CSV',`data-id="${e(indicator.id)}"`,'text-button')}</div>${renderInternalComparison(dataset,state.selected,indicator.id,state.period)}</article>`;
}
function territorial() {
  const themes=[...new Set(dataset.indicators.map(indicator=>indicator.theme || 'Other'))];
  return `<div class="page-actions">${periodControl('territorial-period')}${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}</div>
  <div class="territorial-top"><section class="panel selected-profile"><h2>${e(currentArea().name)}</h2>${hierarchyNavigation()}${areaControls()}${identity()}${facts()}</section>${mapPanel()}</div>${countryDetailLink()}
  <nav class="section-index" aria-label="Diagnostic sections">${themes.map((theme,index)=>`<a href="#theme-${index}">${e(theme)}</a>`).join('')}<a href="#source-register">Sources and gaps</a></nav>
  ${themes.map((theme,index)=>`<section id="theme-${index}" class="theme-section"><h2 class="section-title">${e(theme)} <small>${e(currentArea().name)} · ${e(state.period || 'No period')}</small></h2><div class="indicator-grid">${dataset.indicators.filter(indicator=>(indicator.theme||'Other')===theme).map(metricCard).join('')}</div></section>`).join('')}
  <section class="panel diagnostic-outputs"><h2>Diagnostic report — ${e(currentArea().name)}</h2><p>Whole-area evidence and internal differences use the same period, definitions, membership and sources as this screen. Every member row is included, even when the on-screen table scrolls. This is a diagnostic working report; planning authority, priority hypotheses, resident agreement and approval remain separate.</p><div class="download-actions">${button('diagnostic-markdown','Editable Diagnostic report')}${button('diagnostic-html','Diagnostic report HTML')}${button('diagnostic-csv','Full diagnostic data CSV')}</div><p class="small-note">Print the HTML report to include legends, sources and every row. No resident agreement or formal approval is inferred.</p></section><div class="end-actions">${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}<a href="#top">Back to top</a></div>`;
}
function rankingContent(rows) {
  const ranked=rankedRows(rows,rankOrder), visible=searchRows(ranked,rankSearch);
  const missing=searchRows(rows.filter(row=>!finite(row.value)),rankSearch);
  return `<p class="small-note">${ranked.length} observed / ${rows.length} comparable areas. Search narrows displayed rows only. Ties share a rank.</p>
  <div class="ranking-scroll" role="region" aria-label="Full ranking and unranked areas" tabindex="0"><ol class="ranking-list">${visible.map(row=>`<li class="${row.area.id===state.selected?'selected':''}" data-ranking-id="${e(row.area.id)}"><span class="rank-number">${row.rank}</span>${button('select',e(row.area.name),`data-id="${e(row.area.id)}" data-rank-id="${e(row.area.id)}"`,'rank-area')}<strong>${fmt(row.value)}</strong></li>`).join('')}</ol>
  ${!visible.length?'<p class="missing-note">No observed values match this search. No rank is assigned to missing data.</p>':''}
  ${missing.length?`<details><summary>Unranked areas (${missing.length})</summary><ul class="missing-list">${missing.map(row=>`<li class="${row.area.id===state.selected?'selected':''}" data-ranking-id="${e(row.area.id)}" data-unranked="true">${button('select',e(row.area.name),`data-id="${e(row.area.id)}" data-rank-id="${e(row.area.id)}"`,'text-button')}<span>${observedValue(row.row)!==null?`${fmt(observedValue(row.row))} ${e(observationMeaning(currentMetric(),row.row).unit)} · `:''}${e(statusLabel(row.status))} · unranked${row.reason?` · ${e(row.reason)}`:''}</span></li>`).join('')}</ul></details>`:''}</div>`;
}
function thematic() {
  const indicator=currentMetric();
  if(!indicator)return '<p class="missing-note">No indicators have been collected. See the source register and acquisition gaps.</p>';
  const rows=comparisonRows(dataset,state), stats=distribution(rows);
  const compatibility=comparisonCompatibility(dataset,state);
  const national=observationState(dataset,dataset.country.national_territory_id,state.metric,state.period);
  const selected=observationState(dataset,state.selected,state.metric,state.period),selectedMeaning=observationContext(dataset,currentArea(),indicator,selected.row),nationalMeaning=observationContext(dataset,areaFor(dataset.country.national_territory_id),indicator,national.row);
  const levels=localLevels(dataset);
  const rank=rankedRows(rows,rankOrder).find(row=>row.area.id===state.selected)?.rank;
  return `<section class="panel controls-panel"><div class="control-row">${indicatorControl()}${periodControl()}<label class="field" for="comparison-level"><span>Comparable geographic level</span><select id="comparison-level" data-control="level">${levels.length?levels.map(level=>`<option value="${e(level)}" ${level===state.level?'selected':''}>${e(levelLabel(level))}</option>`).join(''):'<option value="">No local areas acquired</option>'}</select></label></div><p class="definition">${e(indicator.definition)} Unit: ${e(indicator.unit)}. All comparisons use this indicator and period; changing an area retains both.</p></section>
  <div class="summary-grid"><article class="summary"><span>${worldMode()?'World':'National'} value · source-reported</span><strong>${fmt(national.value)}</strong><small>${e(dataset.country.name)} · ${e(state.period)} · ${e(nationalMeaning.unit)}</small></article><article class="summary"><span>Median of comparable local areas</span><strong>${fmt(stats.median)}</strong><small>${e(levelLabel(state.level))}; observed values only</small></article><article class="summary"><span>Local data coverage</span><strong>${stats.count} / ${rows.length}</strong><small>${rows.length-stats.count} unranked or missing</small></article><article class="summary"><span>Observed local range</span><strong>${stats.count?`${fmt(stats.min)}–${fmt(stats.max)}`:'No data'}</strong><small>${e(indicator.unit)} · same comparison set</small></article></div>
  ${!compatibility.comparable?`<p class="notice">${e(compatibility.reason)}</p>`:!stats.count?`<p class="notice"><strong>No comparable local observations for ${e(indicator.name)} · ${e(state.period)}.</strong> ${nationalOnly(dataset)?'Local statistics have not yet been collected.':'This level and period have no observed local values for the selected indicator.'} The national source value is shown separately; no local ranking or local estimates are created.</p>`:''}
  <div class="thematic-grid">${mapPanel({thematic:true})}<section class="panel explorer" aria-labelledby="ranking-title"><h2 id="ranking-title">Find and compare areas</h2><p class="small-note">${e(levelLabel(state.level))} · ${e(indicator.name)} · ${e(state.period)} · ${e(indicator.unit)}</p>
  <label class="field" for="ranking-search"><span>Search ranking by name or code</span><input id="ranking-search" type="search" data-control="ranking-search" value="${e(rankSearch)}" placeholder="Name or code"></label><div class="control-row"><label class="field" for="ranking-order"><span>Order</span><select id="ranking-order" data-control="rank-order"><option value="desc" ${rankOrder==='desc'?'selected':''}>Highest first</option><option value="asc" ${rankOrder==='asc'?'selected':''}>Lowest first</option></select></label>${button('show-selected','Show selected in ranking','','text-button')}</div><div id="ranking-content">${rankingContent(rows)}</div></section></div>
  <section class="panel selection-detail"><div><h2>${e(currentArea().name)} — selected area</h2>${identity()}${areaControls()}</div><div><p class="eyebrow">${e(indicator.name)} · ${e(state.period)} · ${e(selectedMeaning.unit)}</p>${!selectedMeaning.comparable?`<p class="notice">${e(selectedMeaning.reason)}</p>`:''}<p class="definition">${e(selectedMeaning.definition)}</p><p class="selected-value">${fmt(selected.value)}</p><p>${e(statusLabel(selected.status))}. ${currentArea().level==='national'?'National observations are not part of the local ranking.':rank?`Rank ${rank} of ${stats.count} observed areas (${rankOrder==='desc'?'highest':'lowest'} first).`:currentArea().level!==state.level?'Selected area is outside the comparable geographic level.':'No local rank.'}</p>${stateMessage(selected)}${sourceNote(indicator,selected.row)}<div class="actions">${pageLink('territorial','Open territorial diagnostic')}${pageLink('planning','Open planning resources')}${button('comparison-csv','Comparison CSV')}</div></div></section>
  <section class="panel"><h2>Selected-area history</h2>${seriesFigure(indicator)}</section>`;
}
function planning() {
  const settings=planningSettings(dataset),documents=planningDocuments(dataset,state.selected);
  const nationalDocuments=state.selected===dataset.country.national_territory_id?[]:planningDocuments(dataset,dataset.country.national_territory_id);
  const refs=new Set(dataset.documents.filter(hasDocumentReference).map(doc=>doc.territory_id));
  const groups=documentGroups(dataset,state.selected);
  const local=dataset.territories.filter(area=>area.level!=='national');
  const observed=dataset.indicators.filter(indicator=>observationState(dataset,state.selected,indicator.id,state.period).value!==null).length;
  const outputs={markdown:button('planning-markdown','Download editable Markdown','','button'),html:button('planning-html','Print-ready HTML'),evidence_csv:button('planning-csv','Evidence CSV'),documents_csv:button('documents-csv','Materials and findings CSV')};
  const links=settings.related_links.filter(item=>!item.territory_id||item.territory_id===state.selected).map(item=>({label:item.label,url:relatedResourceUrl(item.url,base,routeQuery(dataset,state))})).filter(item=>item.url);
  const gaps=selectedGaps(dataset,state.selected);
  return '<section class="panel planning-overview"><h2>'+e(settings.title)+'</h2><p>'+e(settings.purpose)+'</p><p class="small-note">Verified material references for '+local.filter(area=>refs.has(area.id)).length+' of '+local.length+' local records'+(refs.has(dataset.country.national_territory_id)?'; national reference materials also available':'')+'. Coverage varies by category and period; this is not a count of completed or approved plans.</p></section>'+
  '<section class="panel planning-controls"><h2>Choose an area</h2>'+areaControls()+identity()+'</section>'+
  '<div class="planning-grid">'+mapPanel({planning:true})+'<section class="panel planning-resources"><h2>'+e(currentArea().name)+' — available materials</h2><p>Materials keep their own plan period, fiscal year or quarter. The statistical year below does not filter or relabel them.</p>'+
  (groups.some(group=>group.documents.length)?'<nav class="document-contents" aria-label="Available material categories">'+groups.filter(group=>group.documents.length).map(group=>'<a href="#documents-'+e(group.id)+'">'+e(group.label)+'</a>').join('')+'</nav>':'')+
  renderDocumentGroups(dataset,state.selected)+'</section></div>'+
  '<section class="panel planning-output"><h2>Prepare a working evidence base</h2><p class="notice compact"><strong>Generated working material — unapproved.</strong> These outputs bring together selected-area statistics and collected references. They do not replace the published originals or establish official approval, targets or resident agreement.</p><div class="control-row">'+periodControl('planning-period')+'</div><p>'+observed+' of '+dataset.indicators.length+' statistical indicators have an observed value for '+e(currentArea().name)+' in '+e(state.period || 'the selected period')+'. '+documents.length+' selected-area material records retain their own periods.</p><div class="download-actions">'+settings.outputs.map(format=>outputs[format] || '').join('')+'</div>'+
  (settings.outputs.length?'<p class="small-note">Evidence CSV contains the selected statistical year. Materials CSV, when adopted, contains the original document periods and findings. Markdown and HTML include both with source definitions and explicit gaps.</p>':'<p class="missing-note">No generated download format is adopted for this project. Use the original references and territorial evidence; record the country-specific output workflow in the handoff.</p>')+
  (settings.outputs.includes('markdown')||settings.outputs.includes('html')?'<details><summary>Preview planning base</summary><pre class="planning-preview">'+e(planningMarkdown(dataset,state.selected,state.period))+'</pre></details>':'')+
  (gaps.length?'<details><summary>Outstanding evidence and next actions</summary><ul>'+gaps.map(gap=>'<li><strong>'+e(statusLabel(gap.status))+'</strong> — '+e(gap.detail)+'<p class="small-note">Next: '+e(gap.next_action || 'Verify the responsible source.')+'</p></li>').join('')+'</ul></details>':'')+'</section>'+
  (links.length?'<section class="panel"><h2>Related investment, finance and official services</h2><ul>'+links.map(item=>'<li><a href="'+e(item.url)+'">'+e(item.label)+'</a></li>').join('')+'</ul></section>':'')+
  (nationalDocuments.length?'<section class="panel"><h2>National reference materials — '+e(dataset.country.name)+'</h2><p>National materials are shown separately and are not attributed to '+e(currentArea().name)+'.</p>'+nationalDocuments.map(doc=>renderDocument(dataset,doc)).join('')+'</section>':'')+
  (settings.system?'<section class="panel"><h2>Country planning framework</h2><p>'+e(settings.system.label)+' · '+e(settings.system.scope)+'</p><p>'+e(settings.system.cycle)+'</p>'+settings.system.source_ids.map(id=>sourceNote(null,{source_id:id})).join('')+'</section>':'')+
  '<div class="end-actions">'+pageLink('territorial','Review territorial evidence')+pageLink('thematic','Compare across areas')+'</div>';
}
function home() {
  if(worldMode())return territorial();
  const coverage=countCoverage();
  return `<section class="home-intro"><p class="eyebrow">Territorial information and planning</p><h2>Start with an area.<br>Or start with a question.</h2><p>Explore acquired evidence for ${e(dataset.country.name)}, compare like geographic areas when observations are available, and prepare a source-grounded planning outline.</p></section>
  <div class="entry-grid"><a class="entry-card" href="${e(pageUrl('territorial'))}"><span class="entry-number">01</span><h2>Explore an area</h2><p>Geographic selection, basic facts and sector evidence in one territorial diagnostic.</p><strong>Open territorial diagnostic →</strong></a><a class="entry-card" href="${e(pageUrl('thematic'))}"><span class="entry-number">02</span><h2>Compare a theme</h2><p>Choose an indicator and period. Check national context, local coverage, maps and rankings.</p><strong>Open thematic diagnostic →</strong></a></div>
  <section class="panel home-planning"><div><h2>Turn evidence into planning work</h2><p>Find acquired documents for the same area and download a generic, unapproved planning base with explicit evidence gaps.</p></div>${pageLink('planning','Open planning resources','button')}</section>
  <div class="summary-grid three"><article class="summary"><span>Acquired indicator definitions</span><strong>${dataset.indicators.length}</strong><small>Values and periods vary by indicator</small></article><article class="summary"><span>Reference local areas</span><strong>${coverage.local}</strong><small>${coverage.observed} have one or more acquired observations</small></article><article class="summary"><span>Data edition</span><strong class="date-value">${e(dataset.generated_at.slice(0,10))}</strong><small>Collection status: ${e(statusLabel(dataset.collection?.status))}</small></article></div>
  <section class="panel"><h2>Choose the area to carry into each page</h2>${areaControls()}${identity()}</section>`;
}
function register() {
  return `<section id="source-register" class="source-register"><h2>Sources, definitions and acquisition gaps</h2><details><summary>Source register (${dataset.sources.length})</summary><ul class="source-list">${dataset.sources.map(source=>`<li><h3>${link(source.url,source.name)}</h3><p>${e(source.publisher)} · ${e(statusLabel(source.status))} · Retrieved ${e(source.retrieved_at || 'Not recorded')} · Reference period ${e(source.reference_period || 'Not recorded')}</p><p>${e(source.note || '')}</p>${source.boundary_source?`<p>Original boundary provider: ${e(source.boundary_source)}${safeUrl(source.source_url)?` · ${link(source.source_url,'Original source')}`:''}</p>`:''}<p>License: ${safeUrl(source.license)?link(source.license,'Source terms'):e(source.license || 'Not recorded')}${safeUrl(source.license_url)?` · ${link(source.license_url,'License source')}`:''}${source.license_detail?` · ${e(source.license_detail)}`:''}</p><small>Raw-file SHA-256: ${e(source.sha256 || 'Not available')}</small></li>`).join('')}</ul></details>
  <details ${dataset.gaps.length?'open':''}><summary>Remaining acquisition gaps (${dataset.gaps.length})</summary><ul class="gap-list">${dataset.gaps.map(gap=>`<li><strong>${e(gap.category.replaceAll('_',' '))} — ${e(statusLabel(gap.status))}</strong><p>${e(gap.detail)}</p><p class="small-note">Next: ${e(gap.next_action || 'Verify with the responsible source.')}</p></li>`).join('') || '<li>No acquisition gaps are listed. This is not a certification of complete national coverage.</li>'}</ul></details><p class="small-note">Data edition ${e(dataset.generated_at)} · Schema ${e(dataset.schema_version)}. Source values, proposals and formal decisions are separate records. Source geography and release dates can differ.</p></section>`;
}
function updateHeader() {
  document.getElementById('country-name').textContent=dataset.country.name;
  document.title=`${pageNames[page]} — ${currentArea().name} | ${dataset.country.name}`;
  document.querySelectorAll('[data-page-link]').forEach(anchor=>{const target=anchor.dataset.pageLink;anchor.href=pageUrl(target);if(target===page)anchor.setAttribute('aria-current','page');else anchor.removeAttribute('aria-current');});
  document.querySelectorAll('[data-brand-link]').forEach(anchor=>{anchor.href=new URL('./',base).href;anchor.setAttribute('aria-label',`${dataset.country.name} · return to ${worldMode()?'world':'national'} start with default conditions`);});
}
function render() {
  const active=document.activeElement;
  const focusId=active?.id, mapId=active?.dataset.mapId, rankId=active?.dataset.rankId;
  const previousDisclosure=document.querySelector('[data-all-area-selector]');
  if(previousDisclosure)allAreaOpen=previousDisclosure.open;
  const selection=active instanceof HTMLInputElement ? [active.selectionStart,active.selectionEnd] : null;
  updateHeader();
  app.innerHTML=`<div class="page-heading"><div><p class="eyebrow">${e(dataset.country.name)} · ${e(pageNames[page])}</p><h1>${page==='home'&&!worldMode()?e(dataset.country.name):e(currentArea().name)}</h1></div><div class="actions">${button('share','Share selection')}${button('print','Print page')}</div></div><p id="selection-status" class="sr-only" aria-live="polite">Selected ${e(currentArea().name)}, ${e(currentMetric()?.name || 'no indicator')}, ${e(state.period)}.</p><p id="action-status" class="action-status" role="status"></p>${state.notices.map(notice=>`<p class="notice">${e(notice)}</p>`).join('')}${updateBanner()}${page==='planning'?'':scopeBanner()}${({home,territorial,thematic,planning}[page] || home)()}${register()}`;
  if(focusId) {const next=document.getElementById(focusId);const disclosure=next?.closest('details');if(disclosure)disclosure.open=true;next?.focus({preventScroll:true});if(selection&&next instanceof HTMLInputElement)try{next.setSelectionRange(...selection);}catch{}}
  if(mapId) [...document.querySelectorAll('[data-map-id]')].find(node=>node.dataset.mapId===state.selected)?.focus({preventScroll:true});
  if(rankId) {
    const next=[...document.querySelectorAll('[data-rank-id]')].find(node=>node.dataset.rankId===rankId);
    const disclosure=next?.closest('details');if(disclosure)disclosure.open=true;
    next?.focus({preventScroll:true});revealRankingSelection();
  }
}
function commit(next, {replace=false}={}) {
  state=next;
  const url=new URL(location.href);url.search=routeQuery(dataset,state);
  history[replace?'replaceState':'pushState']({},'',url);
  render();
}
function revealRankingSelection({focus=false}={}) {
  const row=[...document.querySelectorAll('#ranking-content [data-ranking-id]')].find(node=>node.dataset.rankingId===state.selected);
  const container=row?.closest('.ranking-scroll');
  if(!row || !container)return false;
  const details=row.closest('details');if(details)details.open=true;
  const containerRect=container.getBoundingClientRect(),rowRect=row.getBoundingClientRect();
  container.scrollTop=rankingScrollTop({scrollTop:container.scrollTop,clientHeight:container.clientHeight,scrollHeight:container.scrollHeight,rowTop:rowRect.top-containerRect.top+container.scrollTop,rowHeight:rowRect.height});
  if(focus)row.querySelector('button')?.focus({preventScroll:true});
  return true;
}
function choose(id,{fromMap=false}={}) {
  wholeMap=false;areaSearch='';
  const next=selectTerritory(dataset,state,id);
  if(fromMap && page==='thematic') {
    // Map highlighting does not redefine the comparison cohort.
    next.level=state.level;
    rankSearch=rankingReveal(comparisonRows(dataset,next),id,rankSearch).query;
  }
  commit(next);
  if(fromMap && page==='thematic')revealRankingSelection();
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
app.addEventListener('change',event=>{
  const control=event.target.dataset.control;
  if(control==='area')choose(event.target.value);
  if(control==='hierarchy') {wholeMap=false;areaSearch='';commit(selectHierarchyOption(dataset,state,event.target.dataset.parent,event.target.value));}
  if(control==='metric') {const metric=event.target.value;commit({...state,metric,requestedMetric:undefined,sourceDataset:undefined,notices:[]});}
  if(control==='period')commit({...state,period:event.target.value,notices:[]});
  if(control==='level'){wholeMap=true;commit({...state,level:event.target.value,notices:[]});}
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
  if(['Enter',' '].includes(event.key)){event.preventDefault();choose(target.dataset.id,{fromMap:true});return;}
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
    else if(action==='select')choose(target.dataset.id,{fromMap:!!target.dataset.mapId});
    else if(action==='national')choose(dataset.country.national_territory_id);
    else if(action==='map-extent'){wholeMap=!wholeMap;render();}
    else if(action==='compare'){state={...state,metric:target.dataset.id};location.href=pageUrl('thematic');}
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
    else if(action==='planning-markdown')download(planningMarkdown(dataset,state.selected,state.period),`${stem}-planning-base.md`,'text/markdown;charset=utf-8');
    else if(action==='planning-html')download(planningHtml(dataset,state.selected,state.period),`${stem}-planning-base.html`,'text/html;charset=utf-8');
    else if(action==='documents-csv')download(documentsCsv(dataset,state.selected),`${safeFilename(dataset.country.id+'-'+state.selected)}-materials.csv`,'text/csv;charset=utf-8');
    else if(action==='planning-csv')download(evidenceCsv(dataset,state.selected,state.period),`${stem}-evidence.csv`,'text/csv;charset=utf-8');
    else if(action==='indicator-csv')download(evidenceCsv(dataset,state.selected,state.period,[target.dataset.id]),`${stem}-${safeFilename(target.dataset.id)}.csv`,'text/csv;charset=utf-8');
    else if(action==='series-csv')download(seriesCsv(target.dataset.id,target.dataset.territory),`${safeFilename(target.dataset.territory)}-${safeFilename(target.dataset.id)}-history.csv`,'text/csv;charset=utf-8');
    else if(action==='comparison-csv'){
      const indicator=currentMetric();
      const entries=comparisonRows(dataset,state),extended=!!dataset.analysis || entries.some(row=>row.status==='incomparable');
      const rows=[['Country','Level','Territory ID','Territory','Code','Indicator ID','Indicator','Period','Value','Unit','Status','Source URL','Data edition',...(extended?['Comparison eligible','Comparison reason','Definition ID','Definition','Population','Method']:[])],...entries.map(row=>{const context=observationContext(dataset,row.area,indicator,row.row);return [dataset.country.name,row.area.level,row.area.id,row.area.name,row.area.official_code,indicator.id,indicator.name,state.period,observedValue(row.row),context.unit,row.row?.status || row.status,safeUrl(context.source?.url),dataset.generated_at,...(extended?[finite(row.value),row.reason || context.reason,context.definition_id,context.definition,context.population,context.method]:[])];})];
      download(makeCsv(rows),`${safeFilename(dataset.country.id+'-'+state.level+'-'+state.metric+'-'+state.period)}-comparison.csv`,'text/csv;charset=utf-8');
    }
  } catch(error) {actionStatus(`Could not complete this action: ${error.message}. Your selection and evidence are retained.`);}
});
window.addEventListener('popstate',()=>{state=initialState(dataset,location.search);wholeMap=false;areaSearch='';rankSearch='';render();});

try {
  const response=await fetch(new URL('data/dashboard.json',base));
  if(!response.ok)throw new Error(`Data request returned HTTP ${response.status}`);
  dataset=await response.json();
  if(dataset.schema_version!=='0.2'||!dataset.country||!Array.isArray(dataset.territories)||!Array.isArray(dataset.indicators)||!Array.isArray(dataset.observations))throw new Error('Unsupported or incomplete dataset');
  const statusResponse=await fetch(new URL('data/update-status.json',base),{cache:'no-store'}).catch(()=>null);
  if(statusResponse?.ok)updateStatus=await statusResponse.json().catch(()=>null);
  pageNames.planning=planningSettings(dataset).title;
  document.querySelectorAll('[data-page-link="planning"]').forEach(anchor=>anchor.textContent=pageNames.planning);
  state=initialState(dataset,location.search);
  render();
} catch(error) {
  app.innerHTML=`<section class="panel error-panel"><h1>Dashboard data could not be loaded</h1><p>${e(error.message)}</p><p>Serve this folder over HTTP using the project’s local server, then reload. The dataset is stored at <code>data/dashboard.json</code>; no remote service is required after collection.</p><button class="button" id="reload-page">Reload</button></section>`;
  document.getElementById('reload-page').addEventListener('click',()=>location.reload());
}

import {
  finite, escapeHtml as e, safeUrl, displayValue, statusLabel, sourceFor,
  periodsFor, observationState, localLevels, levelLabel, nationalOnly, initialState,
  selectTerritory, routeQuery, comparisonRows, comparisonCompatibility, rankedRows, searchRows, distribution,
  seriesFor, observedValue, makeCsv, evidenceCsv, safeFilename, planningMarkdown,
  planningHtml, mapGeometry, seriesGeometry
} from './model.mjs';

const base = new URL('../', import.meta.url);
const app = document.getElementById('app');
const page = document.body.dataset.page || 'home';
const pageNames = {home:'Explore',territorial:'Territorial diagnostic',thematic:'Thematic diagnostic',planning:'Planning and resources'};
let dataset, state;
let areaSearch='', rankSearch='', rankOrder='desc', wholeMap=false;
const fmt = value => displayValue(value, dataset?.country.locale || 'en');
const areaFor = id => dataset.territories.find(area => area.id === id);
const metricFor = id => dataset.indicators.find(indicator => indicator.id === id);
const currentArea = () => areaFor(state.selected);
const currentMetric = () => metricFor(state.metric);
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
  const groups=[...new Set(dataset.territories.map(area=>area.level))];
  const hits=areaSearch ? dataset.territories.filter(area=>[area.name,area.id,area.official_code].some(value=>String(value||'').toLocaleLowerCase().includes(areaSearch.toLocaleLowerCase()))) : [];
  return `<div class="area-controls"><label class="field" for="area-select"><span>Selected area</span><select id="area-select" data-control="area">${groups.map(level=>`<optgroup label="${e(levelLabel(level))}">${dataset.territories.filter(area=>area.level===level).map(area=>`<option value="${e(area.id)}" ${area.id===state.selected?'selected':''}>${e(area.name)}${area.level==='national'?' · national':''}</option>`).join('')}</optgroup>`).join('')}</select></label>
  <label class="field" for="area-search"><span>Find an area by name or code</span><input id="area-search" type="search" data-control="area-search" value="${e(areaSearch)}" autocomplete="off" placeholder="Name or code"></label>
  ${areaSearch?`<div class="search-results" aria-label="Area search results">${hits.length?hits.slice(0,50).map(area=>button('select',`${e(area.name)}<small>${e(levelLabel(area.level))} · ${e(area.official_code || area.id)}</small>`,`data-id="${e(area.id)}"`,'result-button')).join(''):'<p>No matching areas.</p>'}${hits.length>50?`<p>${hits.length} matches; narrow your search to see more.</p>`:''}</div>`:''}
  ${state.selected!==dataset.country.national_territory_id?button('national','Return to national view','','text-button'):''}</div>`;
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
  return nationalOnly(dataset) ? `<div class="scope-banner"><strong>National statistics; local statistics not yet collected.</strong> ${coverage.local ? `${coverage.local} reference areas are selectable.` : 'No local area registry has been collected.'} Local selections show their own gaps and available documents; national figures are not local estimates.</div>` : `<div class="scope-banner"><strong>Acquired evidence, with explicit gaps.</strong> ${coverage.observed} of ${coverage.local} local areas have at least one observation. Coverage varies by indicator and period.</div>`;
}
function mapPanel({thematic=false,planning=false}={}) {
  const allFeatures=dataset.boundaries?.features || [];
  const selected=currentArea();
  const targetLevel = thematic ? state.level : selected.level==='national' ? localLevels(dataset)[0] : selected.level;
  const features=allFeatures.filter(feature=>areaFor(feature.properties?.territory_id)?.level===targetLevel);
  const fitId = wholeMap || selected.level==='national' ? '' : selected.id;
  const geometry=mapGeometry(features,fitId);
  const rows=thematic?comparisonRows(dataset,state):[];
  const stats=distribution(rows);
  const values=new Map(rows.map(row=>[row.area.id,row.value]));
  const docAreas = new Set(dataset.documents.map(doc=>doc.territory_id));
  const colour = id => {
    if(planning)return docAreas.has(id)?'#2e806d':'#e3e7e8';
    if(!thematic)return '#c1d9d1';
    const value=values.get(id);
    if(!finite(value))return '#dedfdf';
    if(stats.min===stats.max)return '#47937e';
    const colours=['#dcece5','#bad8ca','#85bba5','#4a977c','#226c57'];
    return colours[Math.min(4,Math.floor(5*(value-stats.min)/(stats.max-stats.min)))];
  };
  const title=planning?'Acquired documents by area':thematic?`${currentMetric()?.name || 'Indicator'} · ${state.period || 'No period'}`:'Location';
  const sourceIds=[...new Set(features.map(feature=>feature.properties?.source_id).filter(Boolean))];
  const boundarySources=dataset.sources.filter(source=>sourceIds.includes(source.id) || /boundary|boundaries/i.test(source.id+' '+source.name));
  const chosenTab=geometry.paths.find(path=>path.id===state.selected)?.id || geometry.paths[0]?.id;
  return `<section class="panel map-panel" aria-labelledby="map-title"><div class="panel-heading"><div><p class="eyebrow">${e(levelLabel(targetLevel))} reference boundaries</p><h2 id="map-title">${e(title)}</h2></div>${selected.level!=='national'&&geometry.paths.length?button('map-extent',wholeMap?'Fit selected area':'Show whole country','','text-button'):''}</div>
  ${geometry.paths.length ? `<svg class="geographic-map" viewBox="0 0 760 400" role="group" aria-label="${e(title)}. Select an area with Enter. Arrow keys move between boundaries."><title>${e(title)} — ${e(dataset.country.name)}; ${fitId&&geometry.selectedHasGeometry?`view fitted to ${e(selected.name)}`:'whole available boundary layer'}</title><rect width="760" height="400" fill="#f4f8f7"/>${geometry.paths.map(path=>{const area=areaFor(path.id),value=values.get(path.id);const label=`${area?.name || path.id}${thematic?`: ${finite(value)?fmt(value)+' '+currentMetric().unit:'No data'} for ${state.period}`:''}`;return `<path d="${path.d}" fill="${colour(path.id)}" fill-rule="evenodd" class="map-area ${path.id===state.selected?'selected':''}" role="button" aria-label="${e(label)}" aria-pressed="${path.id===state.selected}" tabindex="${path.id===chosenTab?'0':'-1'}" data-action="select" data-id="${e(path.id)}" data-map-id="${e(path.id)}"><title>${e(label)}</title></path>`;}).join('')}</svg>` : '<div class="map-unavailable"><strong>No verified boundaries available for this level.</strong><p>Use the area selector and search. Acquired statistics and documents remain accessible.</p></div>'}
  ${selected.level!=='national'&&!features.some(feature=>feature.properties?.territory_id===selected.id)?`<p class="missing-note">No boundary is joined to ${e(selected.name)} at this map level. No nearby polygon is substituted.</p>`:''}
  <p class="map-legend">${planning?'Green = a document record has been collected; gray = no document collected. These are acquisition states, not plan approval states.':thematic?`Colors use five equal value intervals across all ${e(levelLabel(state.level).toLowerCase())} areas for this indicator and period; search does not change the scale. Gray = No data. High values are not automatically better.`:'A location map. Fill colors do not represent population or service levels.'} <span class="legend-selected">Gold outline</span> = selected area.</p>
  <p class="source-note">Boundary source: ${boundarySources.length?boundarySources.map(source=>link(source.url,source.name)).join(' · '):'See the source register; boundary authority and edition must be verified.'} Reference boundaries are not a legal boundary certification. Keyboard: arrows / Home / End, then Enter or Space.</p>${dataset.country.geography_note?`<p class="source-note"><strong>Geographic scope:</strong> ${e(dataset.country.geography_note)}</p>`:''}</section>`;
}
function facts() {
  const priority=dataset.indicators.filter(indicator=>/population|household/i.test(indicator.name)).slice(0,3);
  const indicators=priority.length?priority:dataset.indicators.slice(0,3);
  return `<div class="basic-facts">${indicators.map(indicator=>{const result=observationState(dataset,state.selected,indicator.id,state.period);return `<div class="fact"><span>${e(indicator.name)}</span><strong>${fmt(result.value)}</strong><small>${e(indicator.unit)} · ${e(state.period || 'No source period')} · ${e(statusLabel(result.status))}</small></div>`;}).join('')}</div>`;
}
function seriesFigure(indicator, territoryId=state.selected) {
  const series=seriesFor(dataset,territoryId,indicator.id);
  const observed=series.filter(row=>observedValue(row)!==null);
  if(!observed.length)return '<p class="small-note">No acquired time series for this area. National series are not substituted.</p>';
  const geo=seriesGeometry(series);
  const area=areaFor(territoryId);
  const sourceIds=[...new Set(observed.map(row=>row.source_id))];
  const sources=sourceIds.map(id=>dataset.sources.find(source=>source.id===id)).filter(Boolean);
  return `<figure class="series"><figcaption>${e(area.name)} · ${e(indicator.name)} · ${e(series[0].period)}${series.length>1?`–${e(series.at(-1).period)}`:''} · ${e(indicator.unit)}</figcaption>
  ${observed.length>1?`<svg viewBox="0 0 600 170" role="img" aria-label="${e(indicator.name)} time series for ${e(area.name)}. Exact values and sources are in the table below."><title>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</title><line x1="40" y1="140" x2="580" y2="140" stroke="#c8d5d7"/>${geo.segments.map(points=>`<polyline points="${points}" fill="none" stroke="#267966" stroke-width="2.5"/>`).join('')}${geo.points.map(point=>`<circle cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" r="3" fill="#267966"><title>${e(point.row.period)}: ${e(fmt(point.row.value))} ${e(indicator.unit)}</title></circle>`).join('')}<text x="3" y="21">${e(fmt(geo.max))}</text><text x="3" y="135">${e(fmt(geo.min))}</text><text x="40" y="161">${e(series[0].period)}</text><text x="580" y="161" text-anchor="end">${e(series.at(-1).period)}</text></svg><p class="small-note">Source periods in sequence. Missing observations break the line; no missing values are estimated.</p>`:'<p class="small-note">One observed source period; no trend is inferred.</p>'}
  <p class="source-note">Source: ${sources.map(source=>link(source.url,source.name)).join(' · ') || 'See source register'}.</p>
  <details><summary>Time-series values and sources (${series.length})</summary><div class="table-scroll"><table><caption>${e(area.name)} · ${e(indicator.name)} · ${e(indicator.unit)}</caption><thead><tr><th scope="col">Period</th><th scope="col">Value</th><th scope="col">Status</th><th scope="col">Source</th></tr></thead><tbody>${series.map(row=>{const source=sourceFor(dataset,indicator,row);return `<tr><td>${e(row.period)}</td><td>${fmt(observedValue(row))}</td><td>${e(statusLabel(row.status))}</td><td>${source?link(source.url,source.name):'Not recorded'}</td></tr>`;}).join('')}</tbody></table></div></details>
  ${button('series-csv','Time series CSV',`data-id="${e(indicator.id)}" data-territory="${e(territoryId)}"`,'text-button')}</figure>`;
}
function metricCard(indicator) {
  const result=observationState(dataset,state.selected,indicator.id,state.period);
  const national=observationState(dataset,dataset.country.national_territory_id,indicator.id,state.period);
  const local=currentArea().level!=='national';
  return `<article class="indicator-card"><div class="indicator-heading"><h3>${e(indicator.name)}</h3><span class="unit">${e(indicator.unit)}</span></div><div class="value-row"><strong>${fmt(result.value)}</strong><span>${e(statusLabel(result.status))} · ${e(state.period || 'No source period')}</span></div>${stateMessage(result)}
  ${local?`<p class="national-reference">National reference — ${e(dataset.country.name)}: <strong>${fmt(national.value)}</strong> ${e(indicator.unit)} · ${e(state.period)}. ${e(statusLabel(national.status))}.</p>`:''}
  <p class="definition">${e(indicator.definition || 'Definition not acquired.')}</p>${sourceNote(indicator,result.row,finite(result.value)?'Selected-area source':'Available indicator source; selected-area value not acquired')}
  ${seriesFigure(indicator)}<div class="actions">${button('compare','Compare this indicator',`data-id="${e(indicator.id)}"`,'text-button')}${button('indicator-csv','Selected-period CSV',`data-id="${e(indicator.id)}"`,'text-button')}</div></article>`;
}
function territorial() {
  const themes=[...new Set(dataset.indicators.map(indicator=>indicator.theme || 'Other'))];
  return `<div class="page-actions">${periodControl('territorial-period')}${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}</div>
  <div class="territorial-top"><section class="panel selected-profile"><h2>${e(currentArea().name)}</h2>${areaControls()}${identity()}${facts()}</section>${mapPanel()}</div>
  <nav class="section-index" aria-label="Diagnostic sections">${themes.map((theme,index)=>`<a href="#theme-${index}">${e(theme)}</a>`).join('')}<a href="#source-register">Sources and gaps</a></nav>
  ${themes.map((theme,index)=>`<section id="theme-${index}" class="theme-section"><h2 class="section-title">${e(theme)} <small>${e(currentArea().name)} · ${e(state.period || 'No period')}</small></h2><div class="indicator-grid">${dataset.indicators.filter(indicator=>(indicator.theme||'Other')===theme).map(metricCard).join('')}</div></section>`).join('')}
  <div class="end-actions">${pageLink('thematic','Compare across areas')}${pageLink('planning','Open planning resources')}<a href="#top">Back to top</a></div>`;
}
function rankingContent(rows) {
  const ranked=rankedRows(rows,rankOrder), visible=searchRows(ranked,rankSearch);
  const missing=searchRows(rows.filter(row=>!finite(row.value)),rankSearch);
  return `<p class="small-note">${ranked.length} observed / ${rows.length} comparable areas. Search narrows displayed rows only. Ties share a rank.</p>
  <ol class="ranking-list">${visible.map(row=>`<li class="${row.area.id===state.selected?'selected':''}" data-ranking-id="${e(row.area.id)}"><span class="rank-number">${row.rank}</span>${button('select',e(row.area.name),`data-id="${e(row.area.id)}"`,'rank-area')}<strong>${fmt(row.value)}</strong></li>`).join('')}</ol>
  ${!visible.length?'<p class="missing-note">No observed values match this search. No rank is assigned to missing data.</p>':''}
  ${missing.length?`<details><summary>Areas with no observed value (${missing.length})</summary><ul class="missing-list">${missing.map(row=>`<li>${button('select',e(row.area.name),`data-id="${e(row.area.id)}"`,'text-button')}<span>${e(statusLabel(row.status))}</span></li>`).join('')}</ul></details>`:''}`;
}
function thematic() {
  const indicator=currentMetric();
  if(!indicator)return '<p class="missing-note">No indicators have been collected. See the source register and acquisition gaps.</p>';
  const rows=comparisonRows(dataset,state), stats=distribution(rows);
  const compatibility=comparisonCompatibility(dataset,state);
  const national=observationState(dataset,dataset.country.national_territory_id,state.metric,state.period);
  const selected=observationState(dataset,state.selected,state.metric,state.period);
  const levels=localLevels(dataset);
  const rank=rankedRows(rows,rankOrder).find(row=>row.area.id===state.selected)?.rank;
  return `<section class="panel controls-panel"><div class="control-row">${indicatorControl()}${periodControl()}<label class="field" for="comparison-level"><span>Comparable geographic level</span><select id="comparison-level" data-control="level">${levels.length?levels.map(level=>`<option value="${e(level)}" ${level===state.level?'selected':''}>${e(levelLabel(level))}</option>`).join(''):'<option value="">No local areas acquired</option>'}</select></label></div><p class="definition">${e(indicator.definition)} Unit: ${e(indicator.unit)}. All comparisons use this indicator and period; changing an area retains both.</p></section>
  <div class="summary-grid"><article class="summary"><span>National value · source-reported</span><strong>${fmt(national.value)}</strong><small>${e(dataset.country.name)} · ${e(state.period)} · ${e(indicator.unit)}</small></article><article class="summary"><span>Median of comparable local areas</span><strong>${fmt(stats.median)}</strong><small>${e(levelLabel(state.level))}; observed values only</small></article><article class="summary"><span>Local data coverage</span><strong>${stats.count} / ${rows.length}</strong><small>${rows.length-stats.count} with no observed value</small></article><article class="summary"><span>Observed local range</span><strong>${stats.count?`${fmt(stats.min)}–${fmt(stats.max)}`:'No data'}</strong><small>${e(indicator.unit)} · same comparison set</small></article></div>
  ${!compatibility.comparable?`<p class="notice">${e(compatibility.reason)}</p>`:!stats.count?`<p class="notice"><strong>No comparable local observations for ${e(indicator.name)} · ${e(state.period)}.</strong> ${nationalOnly(dataset)?'Local statistics have not yet been collected.':'This level and period have no observed local values for the selected indicator.'} The national source value is shown separately; no local ranking or local estimates are created.</p>`:''}
  <div class="thematic-grid">${mapPanel({thematic:true})}<section class="panel explorer" aria-labelledby="ranking-title"><h2 id="ranking-title">Find and compare areas</h2><p class="small-note">${e(levelLabel(state.level))} · ${e(indicator.name)} · ${e(state.period)} · ${e(indicator.unit)}</p>
  <label class="field" for="ranking-search"><span>Search ranking by name or code</span><input id="ranking-search" type="search" data-control="ranking-search" value="${e(rankSearch)}" placeholder="Name or code"></label><div class="control-row"><label class="field" for="ranking-order"><span>Order</span><select id="ranking-order" data-control="rank-order"><option value="desc" ${rankOrder==='desc'?'selected':''}>Highest first</option><option value="asc" ${rankOrder==='asc'?'selected':''}>Lowest first</option></select></label>${button('show-selected','Show selected in ranking','','text-button')}</div><div id="ranking-content">${rankingContent(rows)}</div></section></div>
  <section class="panel selection-detail"><div><h2>${e(currentArea().name)} — selected area</h2>${identity()}${areaControls()}</div><div><p class="eyebrow">${e(indicator.name)} · ${e(state.period)} · ${e(indicator.unit)}</p><p class="selected-value">${fmt(selected.value)}</p><p>${e(statusLabel(selected.status))}. ${currentArea().level==='national'?'National observations are not part of the local ranking.':rank?`Rank ${rank} of ${stats.count} observed areas (${rankOrder==='desc'?'highest':'lowest'} first).`:currentArea().level!==state.level?'Selected area is outside the comparable geographic level.':'No local rank.'}</p>${stateMessage(selected)}${sourceNote(indicator,selected.row)}<div class="actions">${pageLink('territorial','Open territorial diagnostic')}${pageLink('planning','Open planning resources')}${button('comparison-csv','Comparison CSV')}</div></div></section>
  <section class="panel"><h2>Selected-area history</h2>${seriesFigure(indicator)}</section>`;
}
function documentList(documents) {
  return documents.length ? `<ul class="document-list">${documents.map(doc=>`<li><h3>${link(doc.url,doc.title)}</h3><p>${e(doc.kind)} · ${e(doc.period || 'Period not recorded')}</p><p><span class="status-badge">Acquisition: ${e(statusLabel(doc.availability))}</span> <span class="status-badge neutral">Official status: ${e(statusLabel(doc.official_status || 'unverified'))}</span></p>${doc.source_id?sourceNote(null,{source_id:doc.source_id}):''}</li>`).join('')}</ul>` : '<p class="missing-note">No documents have been collected for this area. This does not establish whether a plan exists or whether it is approved.</p>';
}
function planning() {
  const local=dataset.territories.filter(area=>area.level!=='national');
  const documentIds=new Set(dataset.documents.map(doc=>doc.territory_id));
  const documents=dataset.documents.filter(doc=>doc.territory_id===state.selected);
  const nationalDocuments=state.selected===dataset.country.national_territory_id?[]:dataset.documents.filter(doc=>doc.territory_id===dataset.country.national_territory_id);
  const observed=dataset.indicators.filter(indicator=>observationState(dataset,state.selected,indicator.id,state.period).value!==null).length;
  return `<div class="summary-grid three"><article class="summary"><span>Reference local areas</span><strong>${local.length}</strong><small>Provider registry; identity and edition remain visible</small></article><article class="summary"><span>Local areas with document records</span><strong>${local.filter(area=>documentIds.has(area.id)).length} / ${local.length}</strong><small>Acquisition coverage; not plan approval counts</small></article><article class="summary"><span>Acquired document records</span><strong>${dataset.documents.length}</strong><small>Includes separately identified national documents</small></article></div>
  <section class="panel planning-controls">${areaControls()}${periodControl('planning-period')}</section><div class="planning-grid">${mapPanel({planning:true})}<section class="panel planning-resources"><h2>${e(currentArea().name)}</h2>${identity()}<h3>Planning base document</h3><p class="notice compact"><strong>Generic, unapproved outline.</strong> The country’s official form has not yet been verified. Use this editable evidence aid to begin local review; it does not record official approval or resident agreement.</p><p>${observed} of ${dataset.indicators.length} indicators have an observed value for this area in ${e(state.period || 'the selected period')}. Missing evidence is identified inside each download.</p><div class="download-actions">${button('planning-markdown','Download editable Markdown','','button')}${button('planning-csv','Evidence CSV')}${button('planning-html','Print-ready HTML')}</div><p class="small-note">Ready to download from the current area and period. Markdown and HTML share the same text and evidence. HTML can be printed using your browser. These are generic aids, not official country forms.</p><details><summary>Preview planning base</summary><pre class="planning-preview">${e(planningMarkdown(dataset,state.selected,state.period))}</pre></details><h3>Acquired local documents</h3>${documentList(documents)}</section></div>
  ${nationalDocuments.length?`<section class="panel"><h2>National reference documents — ${e(dataset.country.name)}</h2><p>National references remain separate from the selected area’s documents.</p>${documentList(nationalDocuments)}</section>`:''}<div class="end-actions">${pageLink('territorial','Review territorial evidence')}${pageLink('thematic','Compare across areas')}</div>`;
}
function home() {
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
}
function render() {
  const active=document.activeElement;
  const focusId=active?.id, mapId=active?.dataset.mapId;
  const selection=active instanceof HTMLInputElement ? [active.selectionStart,active.selectionEnd] : null;
  updateHeader();
  app.innerHTML=`<div class="page-heading"><div><p class="eyebrow">${e(dataset.country.name)} · ${e(pageNames[page])}</p><h1>${page==='home'?e(dataset.country.name):e(currentArea().name)}</h1></div><div class="actions">${button('share','Share selection')}${button('print','Print page')}</div></div><p id="selection-status" class="sr-only" aria-live="polite">Selected ${e(currentArea().name)}, ${e(currentMetric()?.name || 'no indicator')}, ${e(state.period)}.</p><p id="action-status" class="action-status" role="status"></p>${state.notices.map(notice=>`<p class="notice">${e(notice)}</p>`).join('')}${scopeBanner()}${({home,territorial,thematic,planning}[page] || home)()}${register()}`;
  if(focusId) {const next=document.getElementById(focusId);next?.focus({preventScroll:true});if(selection&&next instanceof HTMLInputElement)try{next.setSelectionRange(...selection);}catch{}}
  if(mapId) [...document.querySelectorAll('[data-map-id]')].find(node=>node.dataset.mapId===state.selected)?.focus({preventScroll:true});
}
function commit(next, {replace=false}={}) {
  state=next;
  const url=new URL(location.href);url.search=routeQuery(dataset,state);
  history[replace?'replaceState':'pushState']({},'',url);
  render();
}
function choose(id) {wholeMap=false;areaSearch='';commit(selectTerritory(dataset,state,id));}
function actionStatus(text) {const target=document.getElementById('action-status');target.textContent=text;}
function download(text, filename, type) {
  const object=URL.createObjectURL(new Blob([text],{type}));
  const anchor=document.createElement('a');anchor.href=object;anchor.download=filename;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(object),1000);actionStatus(`Prepared ${filename} for ${currentArea().name}.`);
}
function seriesCsv(indicatorId, territoryId) {
  const indicator=metricFor(indicatorId), area=areaFor(territoryId);
  return makeCsv([['Country','Territory','Territory ID','Level','Indicator','Indicator ID','Period','Value','Unit','Status','Source URL','Retrieved at','Data edition'],...seriesFor(dataset,territoryId,indicatorId).map(row=>{const source=sourceFor(dataset,indicator,row);return [dataset.country.name,area.name,area.id,area.level,indicator.name,indicator.id,row.period,observedValue(row),indicator.unit,row.status,safeUrl(source?.url),source?.retrieved_at,dataset.generated_at];})]);
}
app.addEventListener('change',event=>{
  const control=event.target.dataset.control;
  if(control==='area')choose(event.target.value);
  if(control==='metric') {const metric=event.target.value;commit({...state,metric,notices:[]});}
  if(control==='period')commit({...state,period:event.target.value,notices:[]});
  if(control==='level'){wholeMap=true;commit({...state,level:event.target.value,notices:[]});}
  if(control==='rank-order'){rankOrder=event.target.value;render();}
});
app.addEventListener('input',event=>{
  if(event.target.dataset.control==='area-search'){areaSearch=event.target.value;render();}
  if(event.target.dataset.control==='ranking-search'){rankSearch=event.target.value;document.getElementById('ranking-content').innerHTML=rankingContent(comparisonRows(dataset,state));}
});
app.addEventListener('keydown',event=>{
  const target=event.target.closest('[data-map-id]');
  if(!target)return;
  if(['Enter',' '].includes(event.key)){event.preventDefault();choose(target.dataset.id);return;}
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
    if(action==='select')choose(target.dataset.id);
    else if(action==='national')choose(dataset.country.national_territory_id);
    else if(action==='map-extent'){wholeMap=!wholeMap;render();}
    else if(action==='compare'){state={...state,metric:target.dataset.id};location.href=pageUrl('thematic');}
    else if(action==='show-selected'){
      rankSearch='';render();const selected=[...document.querySelectorAll('[data-ranking-id]')].find(row=>row.dataset.rankingId===state.selected);
      if(selected){selected.scrollIntoView({block:'center',behavior:'smooth'});selected.querySelector('button')?.focus({preventScroll:true});}
      else actionStatus('The selected area has no rank in this comparison set. Its details remain below the map.');
    }
    else if(action==='share'){
      const url=new URL(location.href);url.search=routeQuery(dataset,state);
      if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(url.href);actionStatus('Selection link copied.');return;}catch{}}
      const input=document.createElement('input');input.value=url.href;input.readOnly=true;input.setAttribute('aria-label','Selection link to copy');const status=document.getElementById('action-status');status.textContent='Copy this selection link: ';status.append(input);input.focus();input.select();
    }
    else if(action==='print')window.print();
    else if(action==='planning-markdown')download(planningMarkdown(dataset,state.selected,state.period),`${stem}-planning-base.md`,'text/markdown;charset=utf-8');
    else if(action==='planning-html')download(planningHtml(dataset,state.selected,state.period),`${stem}-planning-base.html`,'text/html;charset=utf-8');
    else if(action==='planning-csv')download(evidenceCsv(dataset,state.selected,state.period),`${stem}-evidence.csv`,'text/csv;charset=utf-8');
    else if(action==='indicator-csv')download(evidenceCsv(dataset,state.selected,state.period,[target.dataset.id]),`${stem}-${safeFilename(target.dataset.id)}.csv`,'text/csv;charset=utf-8');
    else if(action==='series-csv')download(seriesCsv(target.dataset.id,target.dataset.territory),`${safeFilename(target.dataset.territory)}-${safeFilename(target.dataset.id)}-history.csv`,'text/csv;charset=utf-8');
    else if(action==='comparison-csv'){
      const indicator=currentMetric();
      const rows=[['Country','Level','Territory ID','Territory','Code','Indicator ID','Indicator','Period','Value','Unit','Status','Source URL','Data edition'],...comparisonRows(dataset,state).map(row=>[dataset.country.name,row.area.level,row.area.id,row.area.name,row.area.official_code,indicator.id,indicator.name,state.period,row.value,indicator.unit,row.status,safeUrl(sourceFor(dataset,indicator,row.row)?.url),dataset.generated_at])];
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
  state=initialState(dataset,location.search);
  render();
} catch(error) {
  app.innerHTML=`<section class="panel error-panel"><h1>Dashboard data could not be loaded</h1><p>${e(error.message)}</p><p>Serve this folder over HTTP using the project’s local server, then reload. The dataset is stored at <code>data/dashboard.json</code>; no remote service is required after collection.</p><button class="button" id="reload-page">Reload</button></section>`;
  document.getElementById('reload-page').addEventListener('click',()=>location.reload());
}

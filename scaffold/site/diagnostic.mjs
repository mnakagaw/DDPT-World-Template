import {escapeHtml as e, displayValue, finite, areaObservationState, statusLabel, territoryLineage, indicatorsForTerritorialScope, mapGeometry, seriesFor, seriesGeometry, observedValue, makeCsv, safeUrl, documentMarkdown, effectivePeriodForTerritoryIndicator} from './model.mjs';
import {internalComparison, colorForComparison, observationContext} from './analysis.mjs';
import {planningDocuments, selectedGaps} from './planning.mjs';
import {sourceSeriesLabel} from './i18n.mjs';

const md = value => String(value ?? '').replaceAll('\\','\\\\').replace(/[|<>\[\]]/g,c=>'\\'+c).replace(/[\r\n]+/g,' ');
const externalLink = (url,label,classes='') => safeUrl(url) ? `<a class="${e(classes)}" href="${e(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${e(label)}<span class="sr-only"> (opens a new tab)</span></a>` : e(label);
const sourceLink = source => source ? externalLink(source.url,source.name) : 'Source not recorded';
const sourcePage = source => safeUrl(source?.catalog_url) || safeUrl(source?.url);
export function seriesSourceLabel(indicator,observation,period=observation?.period,language='en'){
  return sourceSeriesLabel(indicator,observation,period,language);
}
export function renderSourceAttribution(indicator,observation,source,period=observation?.period,language='en'){
  if(!source)return '<span>Source not recorded</span>';
  const page=sourcePage(source),series=seriesSourceLabel(indicator,observation,period,language),same=page===safeUrl(source.url);
  return `<div class="source-attribution"><strong>${externalLink(page,series,'series-source-link')}</strong><small>${e(observation?.source_publisher || source.publisher || 'Publisher not recorded')}</small>${same?`<span class="source-document">${e(source.name)}</span>`:externalLink(source.url,source.name,'source-document')}</div>`;
}
const valueText = (data,value,indicator) => displayValue(value,data.country.locale || 'en',indicator?.display_decimals ?? 2);
const rowUnit = (row,indicator) => row.unit || row.observation?.unit || indicator.unit;
const rowDefinition = (row,indicator) => row.definition || row.observation?.definition || indicator.definition;
const meaningText = meaning => `Definition ID: ${meaning.definition_id || 'not declared'}. Definition: ${meaning.definition || 'not declared'}. Population: ${meaning.population || 'not declared'}. Method: ${meaning.method || 'not declared'}.${meaning.reason?` Comparison context: ${meaning.reason}`:''}`;
const observedBoundary = observation => observation && Object.hasOwn(observation,'boundary_version') ? observation.boundary_version ?? 'unverified' : 'not recorded';
const overallEntry = (data,area,indicator,period) => {
  const result=areaObservationState(data,area.id,indicator.id,period),context=observationContext(data,area,indicator,result.row);
  return {area,...result,observation:result.row,...context,comparable:null};
};
const legendText = scale => `${scale.mode==='fixed'?'Common fixed thresholds':'Intervals calculated within the selected area'}. ${scale.label || ''}: ${(scale.legend || []).map(item=>item.label).join('; ')}`.trim();
const legendHtml = scale => `${e(scale.mode==='fixed'?'Common fixed thresholds':'Intervals calculated within the selected area')}. ${e(scale.label || '')} ${(scale.legend || []).map(item=>`<span class="legend-item"><svg width="12" height="12" aria-hidden="true"><rect width="12" height="12" fill="${e(item.color)}"/></svg> ${e(item.label)}</span>`).join(' · ')}`;
const identityText = area => `${area.name} · ${area.type} · ID ${area.id} · ${area.code_system || 'Code system not recorded'}: ${area.official_code || 'unverified'} · parent ${area.parent_id || 'none'} · boundary ${area.boundary_version || 'unverified'}`;
export function sourceScopeNote(data,territoryId,indicatorId,language='en') {
  const indicator=data.indicators.find(row=>row.id===indicatorId);
  const difference=data.analysis?.source_scope_differences?.find(row=>row.territory_id===territoryId&&row.source_id===indicator?.source_id&&(!row.indicator_id||row.indicator_id===indicatorId));
  if(!difference)return '';
  const delta=new Intl.NumberFormat(language==='ja'?'ja-JP':language==='es'?'es-ES':'en-US').format(Math.round(Math.abs(difference.difference)));
  if(difference.kind==='published_vs_listed_sum_unreconciled'){
    if(language==='ja')return `UNSD AMAの${difference.reference_period}年の広域GDP公表値は、下のM49掲載${difference.listed_member_count}か国・地域の値の合計と約${delta}米ドル異なります。公表値の構成・調整方法は取得済み資料だけでは照合できていません。広域の公表値をこの表の合計とみなさないでください。`;
    if(language==='es')return `El PIB regional publicado por UNSD AMA en ${difference.reference_period} difiere en unos ${delta} dólares de la suma de los ${difference.listed_member_count} países/áreas M49 mostrados abajo. La composición y los ajustes del agregado no se han conciliado con las fuentes obtenidas. No interprete el valor regional como la suma de estas filas.`;
    return `The UNSD AMA ${difference.reference_period} regional GDP differs by about US$${delta} from the sum of the ${difference.listed_member_count} M49 countries/areas listed below. The acquired sources do not yet reconcile the aggregate composition and adjustments. Do not read the regional value as a sum of these rows.`;
  }
  if(language==='ja')return `国連WPPのこの広域公表値には台湾（WPP location 158）が含まれます。一方、下の国別比較はUN M49の掲載地域${difference.listed_member_count}件で、台湾を独立した行として含みません。2026年総人口では公表値と掲載国・地域の合計の差は${delta}人です。広域値を下の行の合計として読まないでください。`;
  if(language==='es')return `El valor regional publicado por UN WPP incluye Taiwán (ubicación WPP 158). La comparación inferior usa ${difference.listed_member_count} países/áreas del registro UN M49 y no muestra Taiwán por separado. Para la población total de 2026, la diferencia con la suma de las filas mostradas es ${delta} personas. El valor regional no es la suma de estas filas.`;
  return `The UN WPP published regional value includes Taiwan (WPP location 158). The comparison below uses ${difference.listed_member_count} countries/areas in the UN M49 registry and does not list Taiwan separately. For 2026 total population, the difference from the displayed member sum is ${delta} people. Do not read the regional value as a sum of these rows.`;
}

export function comparisonSummary(data,comparison,language='en') {
  const rows=comparison.rows.filter(row=>row.comparable && finite(row.value));
  if(!rows.length)return language==='ja'?'この指標・年で比較できる下位地域の値はありません。':language==='es'?'No hay valores comparables de áreas inferiores para este indicador y año.':comparison.reason || 'No comparable lower-area observations are available for this indicator and period. The overall diagnosis remains available.';
  const minimum=rows.reduce((best,row)=>row.value<best.value?row:best),maximum=rows.reduce((best,row)=>row.value>best.value?row:best);
  const nameCounts=new Map();for(const row of rows)nameCounts.set(row.area.name,(nameCounts.get(row.area.name)||0)+1);
  const areaLabel=row=>nameCounts.get(row.area.name)>1?`${row.area.name} (${row.area.official_code || row.area.id})`:row.area.name;
  const unit=comparison.indicator.unit,percentage=unit==='%'||unit.startsWith('% ');
  const showPeriod=new Set(rows.map(row=>String(row.period))).size>1;
  const periodLabel=row=>showPeriod?` (${row.period})`:'';
  const delta=valueText(data,maximum.value-minimum.value,comparison.indicator);
  const decimals=comparison.indicator.display_decimals??2;
  const rounding=new Intl.NumberFormat('en-US',{useGrouping:false,maximumFractionDigits:Math.max(0,Math.min(10,decimals))});
  const rounded=value=>Number(rounding.format(value));
  const roundingNote=rows.length>1&&rounded(rounded(maximum.value)-rounded(minimum.value))!==rounded(maximum.value-minimum.value);
  if(language==='ja')return `${comparison.rows.length}地域中${rows.length}地域を比較できます。最小：${areaLabel(minimum)}${periodLabel(minimum)} ${valueText(data,minimum.value,comparison.indicator)} ${unit}。最大：${areaLabel(maximum)}${periodLabel(maximum)} ${valueText(data,maximum.value,comparison.indicator)} ${unit}。${rows.length>1?`差：${delta} ${percentage?'ポイント':unit}${roundingNote?'（丸め前の値から計算）':''}。`:''}比較できる地域間の差であり、欠測地域を含む全体の差や原因を示すものではありません。`;
  if(language==='es')return `${rows.length} de ${comparison.rows.length} áreas tienen valores comparables. Mínimo: ${areaLabel(minimum)}${periodLabel(minimum)}, ${valueText(data,minimum.value,comparison.indicator)} ${unit}; máximo: ${areaLabel(maximum)}${periodLabel(maximum)}, ${valueText(data,maximum.value,comparison.indicator)} ${unit}.${rows.length>1?` Diferencia: ${delta} ${percentage?'puntos porcentuales':unit}${roundingNote?' (calculada antes del redondeo)':''}.`:''} La diferencia solo describe las áreas comparables y no explica sus causas.`;
  const gap=rows.length>1?` Gap ${delta} ${percentage?'percentage points':unit}${roundingNote?' (calculated before rounding)':''}.`:'';
  return `${rows.length} of ${comparison.rows.length} member areas have comparable observations. Minimum ${areaLabel(minimum)}${periodLabel(minimum)}: ${valueText(data,minimum.value,comparison.indicator)} ${unit}; maximum ${areaLabel(maximum)}${periodLabel(maximum)}: ${valueText(data,maximum.value,comparison.indicator)} ${unit}.${gap} This describes the available comparable members, not necessarily the whole region, and does not establish causes or agreed priorities.`;
}

export function renderInternalComparison(data,parentId,indicatorId,period,{interactive=true,language='en',suppressEmpty=false}={}) {
  const comparison=internalComparison(data,parentId,indicatorId,period),indicator=comparison.indicator;
  if(!indicator)return '';
  if(comparison.set.terminal)return '<p class="internal-stop small-note">Internal comparison stops at this area. Its own observations remain the diagnostic evidence.</p>';
  if(!comparison.rows.length)return `<p class="internal-unavailable missing-note">${e(comparison.reason || 'No lower-area comparison set is configured. Overall evidence is retained.')}</p>`;
  if(suppressEmpty&&!comparison.rows.some(row=>row.comparable&&finite(row.value)))return `<p class="internal-unavailable small-note">${e(comparisonSummary(data,comparison,language))} The full member register remains available from indicators with lower-area observations and from data downloads.</p>`;
  const geometry=mapGeometry(comparison.features),byId=new Map(comparison.rows.map(row=>[row.area.id,row]));
  const label=`${comparison.set.label} · ${indicator.name} · ${period} · ${indicator.unit}`;
  const map=geometry.paths.length?`<svg class="internal-map" viewBox="0 0 760 400" role="group" aria-label="${e(label)}. Inspect values without changing the analysis area."><title>${e(label)}</title><rect width="760" height="400" fill="#f4f8f7"/>${geometry.paths.map(path=>{
    const row=byId.get(path.id),text=`${row.area.name}: ${valueText(data,row.value,indicator)} ${rowUnit(row,indicator)} · ${statusLabel(row.status)}${row.comparable?'':' · comparison not established'}`;
    return `<path d="${path.d}" fill="${e(colorForComparison(comparison,row))}" fill-rule="evenodd" class="internal-area"${interactive?` tabindex="0" role="button" data-action="inspect-internal" data-internal-id="${e(path.id)}" aria-label="${e(text)}"`:''}><title>${e(text)}</title></path>`;
  }).join('')}</svg>`:'<p class="map-unavailable">No matched lower-area boundaries are available. The full member table remains available.</p>';
  const boundarySources=[...new Set(comparison.features.map(feature=>feature.properties?.source_id).filter(Boolean))].map(id=>data.sources.find(source=>source.id===id)).filter(Boolean);
  const rows=comparison.rows.map(row=>`<tr data-internal-row="${e(row.area.id)}"><th scope="row">${interactive?`<button type="button" class="inspect-row" data-action="inspect-internal" data-internal-id="${e(row.area.id)}">${e(row.area.name)}</button>`:e(row.area.name)}<small>${e(row.area.type)} · ${e(row.area.official_code || row.area.id)}</small></th><td><strong>${e(valueText(data,row.value,indicator))}</strong><small>${e(rowUnit(row,indicator))} · ${e(row.period || period)}<br>${e(statusLabel(row.status))}${!row.comparable?'<br>Comparison not established':''}</small></td><td>${renderSourceAttribution(indicator,row.observation,row.source,row.period || period,language)}<details${interactive?'':' open'}><summary>Identity and evidence</summary><p>${e(identityText(row.area))}</p><p>${e(meaningText({...row,reason:''}))}</p><p>Observation boundary edition: ${e(observedBoundary(row.observation))}.</p><p>Retrieved ${e(row.source?.retrieved_at || 'not recorded')}. ${e(row.reason || '')}</p><p>${e(row.boundary_reason || '')}</p></details></td></tr>`).join('');
  return `<section class="internal-comparison" data-internal-comparison="${e(indicatorId)}"><h4>Within the selected area — ${e(comparison.set.label)}</h4><p class="small-note">${e(comparison.set.note || '')}</p><p class="comparison-summary">${e(comparisonSummary(data,comparison,language))}</p><div class="internal-grid"><div class="internal-map-wrap">${map}<p class="internal-legend">${legendHtml(comparison.scale)} Gray = missing or not comparable. High values are not automatically better.</p><p class="source-note">Boundary sources: ${boundarySources.length?boundarySources.map(sourceLink).join(' · '):'not available'}. Boundary editions and codes are listed for every member.</p>${comparison.set.source_ids?.length?`<p class="source-note">Membership sources: ${comparison.set.source_ids.map(id=>sourceLink(data.sources.find(source=>source.id===id))).join(' · ')}</p>`:''}${interactive?'<p class="internal-inspection small-note" role="status">Inspect a map area or table row to highlight its value. The diagnostic area stays unchanged.</p>':''}</div><div class="internal-table-scroll" tabindex="0" role="region" aria-label="${e(label)} — all ${comparison.rows.length} areas"><table class="internal-table"><caption>All ${comparison.rows.length} member areas — including missing values</caption><thead><tr><th scope="col">Area</th><th scope="col">Value</th><th scope="col">Source</th></tr></thead><tbody>${rows}</tbody></table></div></div></section>`;
}

function seriesReport(data,area,indicator) {
  const series=seriesFor(data,area.id,indicator.id),geometry=seriesGeometry(series.map(row=>observationContext(data,area,indicator,row).comparable?row:{...row,status:'missing',value:null}));
  if(!series.length)return '<p>No acquired history for this area and indicator.</p>';
  const graph=geometry?`<svg viewBox="0 0 600 170" role="img" class="diagnostic-history" aria-label="${e(indicator.name)} history; exact periods and values follow"><title>${e(indicator.name)} — ${e(area.name)}</title>${geometry.segments.map(points=>`<polyline points="${points}" fill="none" stroke="#267966" stroke-width="2"/>`).join('')}${geometry.points.map(point=>`<circle cx="${point.x}" cy="${point.y}" r="3" fill="#267966"><title>${e(point.row.period)}: ${e(valueText(data,point.row.value,indicator))}</title></circle>`).join('')}</svg>`:'';
  return `${graph}<table class="history-table"><thead><tr><th>Period</th><th>Value / unit</th><th>Status / meaning</th><th>Source</th></tr></thead><tbody>${series.map(row=>{
    const meaning=observationContext(data,area,indicator,row),source=meaning.source;
    return `<tr><td>${e(row.period)}</td><td>${e(valueText(data,observedValue(row),indicator))} ${e(meaning.unit)}</td><td>${e(statusLabel(row.status))}<p>${e(meaningText(meaning))}</p><p>Observation boundary edition: ${e(observedBoundary(row))}.</p></td><td>${renderSourceAttribution(indicator,row,source,row.period)}<p>Retrieved ${e(source?.retrieved_at || 'not recorded')}.</p></td></tr>`;
  }).join('')}</tbody></table>`;
}

export function diagnosticMarkdown(data,territoryId,period) {
  const area=data.territories.find(row=>row.id===territoryId);
  if(!area)throw new Error('Unknown diagnostic area');
  const lines=[`# Territorial diagnostic — ${md(area.name)}`,'',`Analysis area: ${md(identityText(area))}`,`Hierarchy: ${territoryLineage(data,territoryId).map(row=>md(row.name)).join(' → ')}`,`Selected period: ${md(period)}. Data edition: ${md(data.generated_at)}. Schema: ${md(data.schema_version)}.`, '',
    'This is an editable diagnostic evidence report. The analysis area does not establish a legal planning or approval authority. Observations, priority hypotheses, resident agreements and formal approvals are different records. No priorities, consent or approval are inferred.', '',
    'An exact whole-area observation has priority. A calculated value is allowed only for an approved indicator and a complete, source-backed, non-overlapping membership cover. Exact country or province totals are used before lower-area values, so missing municipalities beneath an available total do not distort a larger-area total. Percentages and non-additive measures are never simply averaged.',''];
  for(const indicator of indicatorsForTerritorialScope(data,territoryId)) {
    const effectivePeriod=effectivePeriodForTerritoryIndicator(data,territoryId,indicator.id,period);
    const result=overallEntry(data,area,indicator,effectivePeriod),source=result.source,comparison=internalComparison(data,territoryId,indicator.id,effectivePeriod);
    lines.push(`## ${md(indicator.theme)} — ${md(indicator.name)}`,'',`Overall: ${md(valueText(data,result.value,indicator))} ${md(result.unit)} · ${md(statusLabel(result.status))} · ${md(result.observation?.period || effectivePeriod)}`,result.provenance==='areadata_calculated'?`Aggregation: ${md(result.note)} Components: ${md(result.components.map(item=>`${item.territory_id}@${item.period}`).join(', '))}. Missing areas: ${md(result.missing_ids.join(', ') || 'none')}. Covered subtotal: ${md(result.covered_value)}.`:'Source-reported exact-area observation or explicit gap.',...(sourceScopeNote(data,territoryId,indicator.id)?[md(sourceScopeNote(data,territoryId,indicator.id))]:[]),md(meaningText(result)),`Observation boundary edition: ${md(observedBoundary(result.observation))}.`,`Source: ${md(source?.name)} · ${md(source?.url)} · retrieved ${md(source?.retrieved_at)}`,'','### Acquired history','','| Period | Value | Unit | Status | Definition / population / method / comparison context | Observation boundary | Source / retrieved |','|---|---:|---|---|---|---|---|');
    for(const row of seriesFor(data,territoryId,indicator.id)) {
      const meaning=observationContext(data,area,indicator,row),historySource=meaning.source;
      lines.push(`| ${md(row.period)} | ${md(valueText(data,observedValue(row),indicator))} | ${md(meaning.unit)} | ${md(statusLabel(row.status))} | ${md(meaningText(meaning))} | ${md(observedBoundary(row))} | ${md(historySource?.url)} / ${md(historySource?.retrieved_at)} |`);
    }
    if(comparison.set.terminal)lines.push('','Internal comparison stops at this area; no lower areas are included.');
    else {
      lines.push('',`### Within the selected area — ${md(comparison.set.label)}`,md(comparison.set.note),md(comparisonSummary(data,comparison)),`Map legend: ${md(legendText(comparison.scale))} Gray = missing or not comparable.`,'',`All ${comparison.rows.length} member areas are listed, including missing observations.`,'','| Area / ID | Type / code system / code / parent / boundary | Value | Unit / period | Status / comparison | Definition / population / method | Observation boundary / geometry join | Source / retrieved |','|---|---|---:|---|---|---|---|---|');
      for(const row of comparison.rows)lines.push(`| ${md(row.area.name)} / ${md(row.area.id)} | ${md(row.area.type)} / ${md(row.area.code_system)} / ${md(row.area.official_code || 'unverified')} / ${md(row.area.parent_id)} / ${md(row.area.boundary_version || 'unverified')} | ${md(valueText(data,row.value,indicator))} | ${md(rowUnit(row,indicator))} / ${md(row.period || effectivePeriod)} | ${md(statusLabel(row.status))} / ${row.comparable?'comparable':md(row.reason || 'not comparable')} | ${md(meaningText({...row,reason:''}))} | ${md(observedBoundary(row.observation))} / ${md(row.boundary_reason || 'Matched geometry')} | ${md(row.source?.url)} / ${md(row.source?.retrieved_at)} |`);
      for(const id of [...new Set([...comparison.set.source_ids,...comparison.features.map(feature=>feature.properties?.source_id).filter(Boolean)])]) {
        const item=data.sources.find(source=>source.id===id);if(item)lines.push(`Geography/membership source: ${md(item.name)} · ${md(item.url)} · ${md(item.retrieved_at)}`);
      }
    }
    lines.push('');
  }
  lines.push('## Selected-area official materials','');
  const documents=planningDocuments(data,territoryId);
  lines.push(...(documents.length?documents.map(doc=>documentMarkdown(data,doc)):['No selected-area official material collected. This does not establish whether a plan exists or is approved.']));
  lines.push('','## Evidence gaps and next actions','',...selectedGaps(data,territoryId).map(gap=>`- ${md(gap.category)} · ${md(gap.status)}: ${md(gap.detail)} Next: ${md(gap.next_action)}`),'','## Priority hypotheses and agreements','','Use the cited differences to prepare questions for local review. Record proposed explanations, meeting evidence, priorities and approval separately. None are generated from a colour or rank.','');
  return lines.join('\n');
}

export function diagnosticCsv(data,territoryId,period) {
  const parent=data.territories.find(row=>row.id===territoryId);
  if(!parent)throw new Error('Unknown diagnostic area');
  const rows=[['Dataset','Analysis area ID','Analysis area','Record scope','Territory ID','Territory','Type','Code system','Official code','Parent ID','Boundary edition','Indicator ID','Indicator','Period','Value','Unit','Status','Value provenance','Aggregation note','Aggregation components','Aggregation component periods','Missing area IDs','Covered subtotal','Comparable','Comparison reason','Definition ID','Definition','Population','Method','Meaning matches indicator','Observation boundary edition','Boundary join','Source ID','Source name','Source URL','Retrieved at','Data edition','Regional source scope note']];
  for(const indicator of indicatorsForTerritorialScope(data,territoryId)){
    const effectivePeriod=effectivePeriodForTerritoryIndicator(data,territoryId,indicator.id,period);
    const overall=overallEntry(data,parent,indicator,effectivePeriod);
    for(const [scope,entry] of [['overall',overall],...internalComparison(data,territoryId,indicator.id,effectivePeriod).rows.map(row=>['within_area',row])])rows.push([data.country.id,territoryId,parent.name,scope,entry.area.id,entry.area.name,entry.area.type,entry.area.code_system,entry.area.official_code,entry.area.parent_id,entry.area.boundary_version,indicator.id,indicator.name,entry.period || entry.observation?.period || effectivePeriod,entry.value,rowUnit(entry,indicator),entry.status,entry.provenance,entry.note,entry.components?.map(item=>item.territory_id).join('; '),entry.components?.map(item=>`${item.territory_id}@${item.period}`).join('; '),entry.missing_ids?.join('; '),entry.covered_value,entry.comparable,entry.reason,entry.definition_id,rowDefinition(entry,indicator),entry.population,entry.method,entry.meaning_comparable,observedBoundary(entry.observation),scope==='overall'?'Not applicable to an overall statistical record':entry.boundary_reason || 'Matched geometry',entry.source?.id,entry.source?.name,entry.source?.url,entry.source?.retrieved_at,data.generated_at,sourceScopeNote(data,territoryId,indicator.id)]);
  }
  return makeCsv(rows);
}

export const diagnosticPrintCss=`body{font:15px/1.5 system-ui,sans-serif;color:#19342c;margin:32px auto;max-width:1100px;padding:0 20px}h1{font-size:27px}h2{border-bottom:2px solid #abcbbd;margin-top:30px}h3{margin-top:24px}p,td,th{overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #cad5d0;padding:7px;text-align:left;vertical-align:top}td small,th small{display:block;font-weight:normal}a{color:#216453}svg{max-width:100%;height:auto}.internal-grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:15px}.internal-area{stroke:white;stroke-width:.8px}.internal-table-scroll{overflow:visible}.internal-legend,.small-note,.source-note{font-size:12px}.diagnostic-history{max-height:170px}.material-report{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 system-ui}details>*{display:block!important}summary{font-weight:600}.internal-inspection{display:none}@media(max-width:700px){body{margin:16px auto;padding:0 12px}.internal-grid{grid-template-columns:1fr}}@media print{body{margin:0;padding:0;font-size:10pt;max-width:none}.internal-grid{display:block}.internal-map{max-height:200px}.internal-table-scroll{max-height:none!important;overflow:visible!important}table{font-size:8pt}thead{display:table-header-group}tr{break-inside:avoid}section,article,.internal-comparison{break-inside:auto}h2,h3,h4{break-after:avoid}svg{print-color-adjust:exact;-webkit-print-color-adjust:exact}a{color:inherit}@page{size:A4;margin:14mm}}`;

export function diagnosticHtml(data,territoryId,period) {
  const area=data.territories.find(row=>row.id===territoryId);
  if(!area)throw new Error('Unknown diagnostic area');
  const sections=indicatorsForTerritorialScope(data,territoryId).map(indicator=>{
    const effectivePeriod=effectivePeriodForTerritoryIndicator(data,territoryId,indicator.id,period);
    const result=overallEntry(data,area,indicator,effectivePeriod);
    return `<section><h2>${e(indicator.theme)} — ${e(indicator.name)}</h2><p><strong>Overall: ${e(valueText(data,result.value,indicator))} ${e(result.unit)}</strong> · ${e(statusLabel(result.status))} · ${e(result.observation?.period || effectivePeriod)}</p>${sourceScopeNote(data,territoryId,indicator.id)?`<p class="notice">${e(sourceScopeNote(data,territoryId,indicator.id))}</p>`:''}<p>${e(meaningText(result))}</p><p>Observation boundary edition: ${e(observedBoundary(result.observation))}.</p><p>Source: ${sourceLink(result.source)} · Retrieved ${e(result.source?.retrieved_at || 'not recorded')}.</p><h3>Acquired history</h3>${seriesReport(data,area,indicator)}${renderInternalComparison(data,territoryId,indicator.id,effectivePeriod,{interactive:false})}</section>`;
  }).join('');
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Territorial diagnostic — ${e(area.name)}</title><style>${diagnosticPrintCss}</style></head><body><h1>Territorial diagnostic — ${e(area.name)}</h1><p>${e(territoryLineage(data,territoryId).map(row=>row.name).join(' → '))}</p><p>${e(identityText(area))}</p><p>Selected period ${e(period)} · Data edition ${e(data.generated_at)} · Schema ${e(data.schema_version)}</p><p>This diagnostic describes the selected analysis area. It does not establish a legal planning authority, resident agreement or official approval. Exact whole-area observations have priority. Approved calculations require a complete, non-overlapping cover and remain labelled separately. Recorded statistical differences and hypotheses for local review remain separate.</p>${sections}<h2>Selected-area official materials</h2><div class="material-report">${e(planningDocuments(data,territoryId).map(doc=>documentMarkdown(data,doc)).join('\n\n') || 'No selected-area material collected; plan existence and approval remain unverified.')}</div><h2>Evidence gaps and next actions</h2><ul>${selectedGaps(data,territoryId).map(gap=>`<li>${e(gap.category)} · ${e(gap.status)}: ${e(gap.detail)} Next: ${e(gap.next_action)}</li>`).join('')}</ul><h2>Priority hypotheses and agreements</h2><p>Use these source-grounded differences to prepare questions for local review. Proposed causes, priorities, meeting evidence and approvals must be recorded separately. No such agreement is generated from a colour or rank.</p></body></html>`;
}

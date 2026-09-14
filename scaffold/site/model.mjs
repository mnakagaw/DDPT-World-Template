// Shared, dependency-free data and export semantics. Safe to import in Node tests.
import {planningSettings, planningDocuments, documentPeriod, periodText, categoryFor, categoryLabels, findingLabels, officialStatus, documentEvidence, findingValue, selectedGaps, acquisitionLabel} from './planning.mjs';
import {observationMeaning,observationContext,isTerminalTerritory} from './analysis.mjs';
import {resolvedObservation,aggregationRule,LATEST_AVAILABLE_PERIOD} from './aggregation.mjs';
export const finite = value => typeof value === 'number' && Number.isFinite(value);
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
export function safeUrl(value) {
  try { const url = new URL(String(value)); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
}
export function displayValue(value, locale = 'en', maximumFractionDigits = 2) {
  if (!finite(value)) return 'No data';
  const digits=Number.isInteger(maximumFractionDigits)&&maximumFractionDigits>=0&&maximumFractionDigits<=10?maximumFractionDigits:2;
  try { return new Intl.NumberFormat(locale, {maximumFractionDigits: digits}).format(value); }
  catch { return new Intl.NumberFormat('en', {maximumFractionDigits: digits}).format(value); }
}
export function statusLabel(status) {
  return ({observed:'Source reported', calculated:'AreaData calculated', incomplete:'Incomplete coverage', missing:'No data', not_collected:'Not collected', not_available:'Not available', unavailable:'Unavailable', not_applicable:'Not applicable', incomparable:'Comparison not established', unverified:'Unverified', failed:'Acquisition failed', error:'Acquisition failed', ready:'Acquired', link_verified:'Link verified', downloaded:'Body acquired', body_acquired:'Body acquired', content_extracted:'Content extracted; not cross-checked', content_verified:'Content cross-checked', extracted:'Extracted', pending:'Pending'})[status] || String(status || 'Not collected').replaceAll('_', ' ');
}
export function sourceFor(dataset, indicator, observation) {
  return dataset.sources.find(source => source.id === (observation?.source_id || indicator?.source_id));
}
export function periodsFor(dataset, indicatorId) {
  const periods=[...new Set(dataset.observations.filter(row => !indicatorId || row.indicator_id === indicatorId).map(row => String(row.period)))].sort((a,b) => b.localeCompare(a, 'en', {numeric:true}));
  if(indicatorId && aggregationRule(dataset,indicatorId)?.period_policy==='latest_available_by_component')periods.unshift(LATEST_AVAILABLE_PERIOD);
  return periods;
}
export function latestObservedPeriod(dataset, indicatorId) {
  return [...new Set(dataset.observations.filter(row => row.indicator_id === indicatorId && observedValue(row) !== null).map(row => String(row.period)))].sort((a,b) => b.localeCompare(a, 'en', {numeric:true}))[0] || '';
}
export function observationFor(dataset, territoryId, indicatorId, period) {
  return dataset.observations.find(row => row.territory_id === territoryId && row.indicator_id === indicatorId && String(row.period) === String(period));
}
export function observedValue(observation) { return observation?.status === 'observed' && finite(observation.value) ? observation.value : null; }
export function observationState(dataset, territoryId, indicatorId, period) {
  const indicator=dataset.indicators.find(item=>item.id===indicatorId);
  const rows=dataset.observations.filter(item=>item.territory_id===territoryId&&item.indicator_id===indicatorId);
  const mixed=String(period)===LATEST_AVAILABLE_PERIOD&&indicator?.period_policy==='latest_available_by_component';
  const row = mixed?[...rows].filter(item=>observedValue(item)!==null).sort((a,b)=>String(b.period).localeCompare(String(a.period),'en',{numeric:true}))[0] || null:observationFor(dataset, territoryId, indicatorId, period);
  if (row) return {row, value:observedValue(row), status:row.status || 'unverified'};
  const hasSeries = rows.length>0;
  return {row:null, value:null, status:hasSeries ? 'missing' : 'not_collected'};
}
export function areaObservationState(dataset, territoryId, indicatorId, period) {
  return resolvedObservation(dataset,territoryId,indicatorId,period);
}
export function localLevels(dataset) { return [...new Set(dataset.territories.filter(row => row.level !== 'national').map(row => row.level))]; }
export function levelLabel(level) { return level === 'national' ? 'National' : /^adm\d$/i.test(level) ? `Administrative level ${level.slice(3)}` : String(level || 'Local areas').replaceAll('_',' '); }
export function nationalOnly(dataset) { return !dataset.observations.some(row => row.territory_id !== dataset.country.national_territory_id && observedValue(row) !== null); }
export function countryDiagnosticUrl(dataset, state, base) {
  const site=dataset.analysis?.country_sites?.find(item=>item.territory_id===state.selected);
  if(!site)return '';
  const target=new URL(site.url,base);
  const query=new URLSearchParams({country:site.country_id,territory:site.target_territory_id || site.country_id,period:state.period});
  const mapped=site.indicator_map?.[state.metric];
  if(mapped)query.set('metric',mapped);
  else {query.set('requested_metric',state.metric);query.set('source_dataset',dataset.country.id);}
  target.search=query.toString();
  return target.href;
}
export function initialState(dataset, search = '') {
  const query = new URLSearchParams(search), notices = [];
  const suppliedTerritory = query.get('territory');
  const wrongCountry = query.has('country') && query.get('country') !== dataset.country.id;
  const territory = wrongCountry ? null : dataset.territories.find(row => row.id === suppliedTerritory);
  if (wrongCountry) notices.push(`This link refers to country “${query.get('country')}”, but this dataset is “${dataset.country.id}”. Its area cannot be restored here. This country’s national view is shown.`);
  if (suppliedTerritory && !territory) notices.push(`The linked area “${suppliedTerritory}” is not in this data edition. The national view is shown; select an available area.`);
  if (territory) for (const [parameter,field,label] of [['type','type','area type'],['code','official_code','official code'],['boundary','boundary_version','boundary edition']]) {
    if (query.has(parameter) && query.get(parameter) !== String(territory[field] || '')) notices.push(`The linked ${label} “${query.get(parameter)}” differs from this record’s ${label} “${territory[field] || 'not verified'}”. The current record is shown; verify its identity before using the evidence.`);
  }
  const suppliedMetric = query.get('metric');
  const requestedMetric=query.get('requested_metric');
  if(requestedMetric)notices.push(`No verified indicator mapping was supplied for “${requestedMetric}” from dataset “${query.get('source_dataset') || 'not specified'}”. The displayed country indicator is a separate concept. The requested period is retained.`);
  const indicator = dataset.indicators.find(row => row.id === suppliedMetric);
  if (suppliedMetric && !indicator) notices.push(`The linked indicator “${suppliedMetric}” is unavailable in this edition. The first available indicator is shown.`);
  const firstObservedIndicator = dataset.indicators.find(item => dataset.observations.some(row => row.indicator_id === item.id && observedValue(row) !== null));
  const metric = indicator?.id || firstObservedIndicator?.id || dataset.indicators[0]?.id || '';
  const requestedPeriod = query.get('period');
  // A syntactically valid requested period remains selected even when its value is missing.
  const validPeriod = requestedPeriod && /^[\p{L}\p{N} ._/:–-]{1,40}$/u.test(requestedPeriod);
  if (requestedPeriod && !validPeriod) notices.push('The linked period is invalid. The most recent available source period is shown.');
  const configuredPeriod=dataset.analysis?.default_period_by_indicator?.[metric];
  const period = validPeriod ? requestedPeriod : configuredPeriod || latestObservedPeriod(dataset, metric) || periodsFor(dataset, metric)[0] || '';
  const levels = localLevels(dataset);
  const selected = territory?.id || dataset.country.national_territory_id;
  const selectedLevel = territory?.level;
  const level = levels.includes(query.get('level')) ? query.get('level') : selectedLevel && selectedLevel !== 'national' ? selectedLevel : levels[0] || '';
  return {selected, metric, period, level, notices,...(requestedMetric?{requestedMetric,sourceDataset:query.get('source_dataset') || ''}:{})};
}
export function selectTerritory(dataset, state, id) {
  const territory = dataset.territories.find(row => row.id === id);
  if (!territory) return {...state, notices:[`Area “${id}” is unavailable. The current selection was retained.`]};
  return {...state, selected:id, level:territory.level === 'national' ? state.level : territory.level, notices:[]};
}
export function territoryLineage(dataset, selectedId) {
  const byId=new Map(dataset.territories.map(area=>[area.id,area]));
  const lineage=[],visited=new Set();
  let area=byId.get(selectedId);
  while(area) {
    if(visited.has(area.id))return [];
    visited.add(area.id);lineage.unshift(area);
    if(area.id===dataset.country.national_territory_id)return lineage;
    if(!area.parent_id)return [];
    area=byId.get(area.parent_id);
  }
  return [];
}
// An ancestor shown as context is NOT the active geographic choice. Its selectable
// "Whole …" option has a different value, so selecting the SAME ancestor fires change.
export function territoryOptionLabel(dataset,area) {
  return dataset.territories.filter(row=>row.name===area.name).length>1?`${area.name} · ${area.type} · ${area.official_code || area.id}${area.boundary_version?` · ${area.boundary_version}`:''}`:area.name;
}
export function hierarchyControls(dataset, selectedId) {
  const byId=new Map(dataset.territories.map(area=>[area.id,area]));
  const hasMultipleTiers=dataset.territories.some(area=>area.parent_id && area.parent_id!==dataset.country.national_territory_id && byId.has(area.parent_id));
  const lineage=territoryLineage(dataset,selectedId);
  if(!hasMultipleTiers || !lineage.length)return [];
  return lineage.flatMap((parent,index)=>{
    if(isTerminalTerritory(dataset,parent))return [];
    const children=dataset.territories.filter(area=>area.parent_id===parent.id);
    if(!children.length)return [];
    const child=lineage[index+1];
    const descendantSelected=child && child.id!==selectedId;
    const context=descendantSelected?{value:'context',label:`Belongs to ${child.name} · a lower area is selected`}:null;
    return [{parent,levels:[...new Set(children.map(area=>area.level))],context,
      value:context?'context':child?`area:${child.id}`:'',
      options:[{value:'',targetId:parent.id,label:`Whole ${territoryOptionLabel(dataset,parent)} · no lower area selected`},...children.map(area=>({value:`area:${area.id}`,targetId:area.id,label:`Whole ${territoryOptionLabel(dataset,area)}`}))]}];
  });
}
export function selectHierarchyOption(dataset,state,parentId,value) {
  const control=hierarchyControls(dataset,state.selected).find(item=>item.parent.id===parentId);
  const option=control?.options.find(item=>item.value===value);
  if(!option)return {...state,notices:['This hierarchy choice is no longer available. The current area was retained.']};
  // There is one selected ID. Choosing a parent replaces it; no descendant state
  // survives, and missing parent observations remain missing rather than being summed.
  return selectTerritory(dataset,state,option.targetId);
}
export function routeQuery(dataset, state) {
  const territory = dataset.territories.find(row => row.id === state.selected);
  const query = new URLSearchParams({country:dataset.country.id, territory:state.selected, metric:state.metric, period:state.period, level:state.level || ''});
  if(state.requestedMetric){query.set('requested_metric',state.requestedMetric);query.set('source_dataset',state.sourceDataset || '');}
  if (territory) {
    query.set('type', territory.type || territory.level);
    if (territory.official_code) query.set('code', territory.official_code);
    if (territory.boundary_version) query.set('boundary', territory.boundary_version);
  }
  return query.toString();
}
export function comparisonCompatibility(dataset, state) {
  const areas = dataset.territories.filter(area => area.level !== 'national' && area.level === state.level);
  const types = [...new Set(areas.map(area => area.type || 'unspecified'))];
  const editions = [...new Set(areas.map(area => area.boundary_version || 'unverified'))];
  const reasons=[];
  if(types.length>1)reasons.push(`different administrative types (${types.join(', ')})`);
  if(editions.length>1)reasons.push(`different boundary editions (${editions.join(', ')})`);
  return {comparable:!reasons.length, reason:reasons.length?`Local comparison is not established: this geographic level contains ${reasons.join(' and ')}. Verify a compatible geographic cohort before enabling ranks, median or map value classes. Selected-area observations remain available.`:''};
}
export function comparisonRows(dataset, state) {
  const compatibility=comparisonCompatibility(dataset,state);
  const indicator=dataset.indicators.find(item=>item.id===state.metric);
  return dataset.territories.filter(area => area.level !== 'national' && area.level === state.level).map(area => {
    const result=observationState(dataset,area.id,state.metric,state.period);
    const meaning=observationContext(dataset,area,indicator,result.row);
    return {area,...result,period:result.row?.period || state.period,...(!compatibility.comparable || !meaning.comparable?{value:null,status:'incomparable',reason:[compatibility.reason,meaning.reason].filter(Boolean).join(' ')}:{})};
  });
}
export function rankedRows(rows, order = 'desc') {
  return rows.filter(row => finite(row.value)).sort((a,b) => (order === 'asc' ? a.value - b.value : b.value - a.value) || a.area.name.localeCompare(b.area.name)).map((row, index, sorted) => ({...row, rank:sorted.findIndex(other => other.value === row.value) + 1, position:index + 1}));
}
export function searchRows(rows, query) {
  const text = query.trim().toLocaleLowerCase();
  return rows.filter(row => !text || [row.area.name, row.area.id, row.area.official_code].some(value => String(value || '').toLocaleLowerCase().includes(text)));
}
export function rankingReveal(rows,selectedId,query) {
  const selected=rows.find(row=>row.area.id===selectedId);
  const masked=!!selected && searchRows([selected],query).length===0;
  return {query:masked?'':query,clearSearch:masked,inCohort:!!selected,ranked:!!selected && finite(selected.value)};
}
export function rankingScrollTop({scrollTop,clientHeight,scrollHeight,rowTop,rowHeight}) {
  const padding=8,max=Math.max(0,scrollHeight-clientHeight);
  if(rowTop>=scrollTop+padding && rowTop+rowHeight<=scrollTop+clientHeight-padding)return Math.min(max,Math.max(0,scrollTop));
  return Math.min(max,Math.max(0,rowTop-(clientHeight-rowHeight)/2));
}
export function distribution(rows) {
  const values = rows.map(row => row.value).filter(finite).sort((a,b) => a-b);
  if (!values.length) return {count:0, min:null, max:null, median:null};
  const middle = Math.floor(values.length / 2);
  return {count:values.length, min:values[0], max:values.at(-1), median:values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2};
}
export function seriesFor(dataset, territoryId, indicatorId) {
  return dataset.observations.filter(row => row.territory_id === territoryId && row.indicator_id === indicatorId).sort((a,b) => String(a.period).localeCompare(String(b.period), 'en', {numeric:true}));
}

// Treat downloaded strings as spreadsheet text, including formulas hidden behind whitespace.
export function csvCell(value) {
  let text = value == null ? '' : String(value);
  if (typeof value !== 'number' && (/^[\s\uFEFF]*[=+\-@]/u.test(text) || /^[\t\r\n]/u.test(text))) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}
export function makeCsv(rows) { return '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n'; }
export function evidenceRows(dataset, territoryId, period, indicatorIds = dataset.indicators.map(row => row.id)) {
  const area = dataset.territories.find(row => row.id === territoryId);
  return dataset.indicators.filter(indicator => indicatorIds.includes(indicator.id)).map(indicator => {
    const current = areaObservationState(dataset, territoryId, indicator.id, period), source = sourceFor(dataset, indicator, current.row);
    return {area, indicator, ...current, source, period};
  });
}
export function evidenceCsv(dataset, territoryId, period, indicatorIds) {
  const rows=evidenceRows(dataset, territoryId, period, indicatorIds);
  const extended=!!dataset.analysis || rows.some(({indicator,row})=>indicator.definition_id || indicator.population || ['definition_id','definition','unit','population','method','measurement_method'].some(key=>row?.[key]!==undefined));
  const aggregation=!!dataset.analysis?.aggregation;
  return makeCsv([
    ['Country','Territory ID','Territory','Level','Code','Code system','Boundary edition','Indicator ID','Indicator','Period','Value','Unit','Status',...(aggregation?['Value provenance','Aggregation note','Component IDs','Component periods','Missing area IDs','Covered subtotal']:[]),'Definition','Source','Source URL','Retrieved at','Data edition',...(extended?['Definition ID','Population','Measurement method','Comparable concept','Comparison note']:[])],
    ...rows.map(({area, indicator, row, value, status, source}) => {
      const meaning=observationContext(dataset,area,indicator,row);
      const aggregate=areaObservationState(dataset,area.id,indicator.id,period);
      return [dataset.country.name, area?.id, area?.name, area?.level, area?.official_code, area?.code_system, area?.boundary_version, indicator.id, indicator.name, period, value, meaning.unit, status,...(aggregation?[aggregate.provenance, aggregate.note, aggregate.components.map(item=>item.territory_id).join('; '), aggregate.components.map(item=>`${item.territory_id}@${item.period}`).join('; '), aggregate.missing_ids.join('; '), aggregate.covered_value]:[]), meaning.definition, source?.name, safeUrl(source?.url), source?.retrieved_at, dataset.generated_at,...(extended?[meaning.definition_id,meaning.population,meaning.method,meaning.comparable,meaning.reason]:[])];
    })
  ]);
}
export function safeFilename(value) { return String(value).replace(/[^\p{L}\p{N}._-]/gu,'-').replace(/-+/g,'-').slice(0,100) || 'dashboard'; }
const markdownText = value => String(value ?? '').replaceAll('\\','\\\\').replace(/[\[\]<>]/g, character => `\\${character}`).replaceAll('|','\\|').replace(/[\r\n]+/g,' ');
export function documentMarkdown(dataset,doc) {
  const official=officialStatus(dataset,doc),lines=[
    `### ${markdownText(doc.title)}`,'',
    `${markdownText(categoryLabels[categoryFor(doc)])} · ${markdownText(doc.target_period?periodText(doc.target_period):documentPeriod(doc))}`,'',
    safeUrl(doc.url)?`Original material / official reference: <${safeUrl(doc.url)}>`:'No verified link.',
    `Institutional state: ${markdownText(official.label)} (${official.verified?'documented evidence':'unverified; no approval inferred'}).`,
    ...(official.verified?[`State evidence: ${markdownText(documentEvidence(dataset,official.evidence))}`]:[]),''
  ];
  if(doc.content)lines.push(markdownText(doc.content.summary),...doc.content.priorities?.map(value=>`- Reported priority: ${markdownText(value)}`)||[],...doc.content.objectives?.map(value=>`- Reported objective: ${markdownText(value)}`)||[],`Content evidence: ${markdownText(documentEvidence(dataset,doc.content.evidence))}`,'');
  for(const finding of doc.findings || [])lines.push(`- ${markdownText(findingLabels[finding.kind])} — ${markdownText(finding.label)}: ${markdownText(findingValue(finding))}${finding.statement&&Object.hasOwn(finding,'value')?`. ${markdownText(finding.statement)}`:''}.`,
    `  Period: ${markdownText(periodText(finding.period))}. Definition: ${markdownText(finding.definition)}. Scope: ${markdownText(finding.scope)}.`,
    ...(finding.scale?[`  Scale: ${markdownText(finding.scale.label)} (${finding.scale.min}–${finding.scale.max}).`]:[]),
    `  Evidence: ${markdownText(documentEvidence(dataset,finding.evidence))}`);
  const source=dataset.sources.find(row=>row.id===doc.source_id),match=doc.territory_match;
  lines.push('',`Acquisition: ${markdownText(acquisitionLabel(doc))}. Source: ${markdownText(source?.name)}; retrieved ${markdownText(source?.retrieved_at)}.`,
    ...(match?[`Territory match: ${markdownText(match.country_id)} / ${markdownText(match.type)} / ${markdownText(match.code_system)} / ${markdownText(match.official_code??'official code not verified')} / ${markdownText(match.boundary_version??'boundary edition not verified')}; validity ${markdownText(match.valid_from||'not recorded')} to ${markdownText(match.valid_to||'not recorded')}; ${markdownText(match.method)}. ${markdownText(documentEvidence(dataset,match))}`]:['Legacy record: identity matching evidence has not been recorded in the extended contract.']), '');
  return lines.join('\n');
}
export function documentsCsv(dataset,territoryId) {
  const area=dataset.territories.find(row=>row.id===territoryId);
  const columns=['Country','Territory ID','Territory','Type','Code system','Official code','Boundary edition','Document ID','Document','Category','Document period','Period kind','Period start','Period end','Acquisition','Institutional state','State evidence verified','Document URL','Source','Source URL','State evidence','Content summary','Reported priorities','Reported objectives','Content evidence','Finding kind','Finding','Value','Value status','Unit','Finding statement','Finding period','Finding period kind','Finding start','Finding end','Definition','Scope','Scale','Finding evidence','Identity evidence','Data edition'];
  const rows=planningDocuments(dataset,territoryId).flatMap(doc=>{
    const source=dataset.sources.find(row=>row.id===doc.source_id),official=officialStatus(dataset,doc);
    return (doc.findings?.length?doc.findings:[null]).map(finding=>[
      dataset.country.id,area?.id,area?.name,area?.type,area?.code_system,area?.official_code,area?.boundary_version,doc.id,doc.title,categoryFor(doc),documentPeriod(doc),doc.target_period?.kind,doc.target_period?.start,doc.target_period?.end,doc.availability,official.label,official.verified,doc.url,source?.name,source?.url,official.verified?documentEvidence(dataset,official.evidence):'Unverified',doc.content?.summary,doc.content?.priorities?.join('; '),doc.content?.objectives?.join('; '),doc.content?documentEvidence(dataset,doc.content.evidence):'',finding?.kind,finding?.label,finding?.value_status==='observed'?finding.value:null,finding?.value_status,finding?.unit,finding?.statement,finding?.period?.label,finding?.period?.kind,finding?.period?.start,finding?.period?.end,finding?.definition,finding?.scope,finding?.scale?`${finding.scale.label} (${finding.scale.min}–${finding.scale.max})`:'',finding?documentEvidence(dataset,finding.evidence):'',doc.territory_match?documentEvidence(dataset,doc.territory_match):'Not recorded',dataset.generated_at]);
  });
  return makeCsv([columns,...rows]);
}
export function planningMarkdown(dataset, territoryId, period) {
  const area = dataset.territories.find(row => row.id === territoryId);
  if (!area) throw new Error('Unknown planning territory');
  const documents = planningDocuments(dataset,territoryId), settings=planningSettings(dataset);
  const evidence = evidenceRows(dataset, territoryId, period);
  const lines = [
    `# Planning base — ${markdownText(area.name)}`, '',
    '**Generic, unapproved working outline.** The country’s official planning form and required procedure have not been verified by this template. Complete this outline against official guidance before formal use. It does not record approval or community agreement.', '',
    '## 1. Area and evidence scope', '',
    `- Country: ${markdownText(dataset.country.name)} (${markdownText(dataset.country.id)})`,
    `- Area: ${markdownText(area.name)}; ID: ${markdownText(area.id)}; level: ${markdownText(area.level)}; type: ${markdownText(area.type)}`,
    `- Code: ${markdownText(area.official_code || 'Not verified')}; code system: ${markdownText(area.code_system || 'Not specified')}`,
    `- Boundary edition: ${markdownText(area.boundary_version || 'Not verified')}`,
    `- Requested evidence period: ${markdownText(period || 'No source period available')}`,
    `- Data edition: ${markdownText(dataset.generated_at)}`, '',
    ...(settings.system?[`- Planning framework: ${markdownText(settings.system.label)}; scope: ${markdownText(settings.system.scope)}; cycle: ${markdownText(settings.system.cycle)}.`,...settings.system.source_ids.map(id=>{const source=dataset.sources.find(row=>row.id===id);return `- Framework source: ${markdownText(source?.name)} <${safeUrl(source?.url)}>`;}),'']:[]),
    ...(settings.update?.status==='stopped'?[`- SOURCE UPDATE STOPPED: ${markdownText(settings.update.message)}. Last success: ${markdownText(settings.update.last_success_at||'Not recorded')}; checked ${markdownText(settings.update.checked_at)}.`,'']:[]),
    '## 2. Acquired statistical evidence', '',
    'Only observations for this area and period appear below. National observations are not substituted for local gaps. Different indicators can have different definitions and coverage.', '',
    '| Indicator | Value | Unit | Status | Source |', '|---|---:|---|---|---|',
    ...evidence.map(({indicator, row, value, status, source}) => `| ${markdownText(indicator.name)} | ${value === null ? '—' : String(value)} | ${markdownText(row?.unit || indicator.unit)} | ${markdownText(statusLabel(status))} | ${markdownText(source?.name || 'No source acquired')} |`), '',
    ...evidence.map(({indicator, row, source}) => `- ${markdownText(indicator.name)}: ${markdownText(row?.definition || indicator.definition || 'Definition not acquired')}. ${safeUrl(source?.url) ? `Source: <${safeUrl(source.url)}>.` : 'No verified source link.'} Retrieved: ${markdownText(source?.retrieved_at || 'Not recorded')}.`), '',
    ...evidence.flatMap(({indicator,row})=>{
      const meaning=observationContext(dataset,area,indicator,row);
      return dataset.analysis || !meaning.comparable || indicator.definition_id || indicator.population ? [`- Meaning of ${markdownText(indicator.name)}: definition ID ${markdownText(meaning.definition_id || 'Not recorded')}; population ${markdownText(meaning.population || 'Not recorded')}; method ${markdownText(meaning.method || 'Not recorded')}. ${markdownText(meaning.reason || 'No explicit concept difference recorded; verify source compatibility.')}`]:[];
    }),
    '## Official materials and verified findings', '',
    'Document plan periods, fiscal years and quarters below are their own source periods. They are not filtered or relabelled as the statistical evidence period. Published materials remain distinct from this generated working outline.', '',
    ...(documents.length?documents.map(doc=>documentMarkdown(dataset,doc)):['No local documents have been collected for this area. This does not establish whether a plan exists.']), '',
    '## 3. Working issues to investigate', '',
    '| Proposed issue | Evidence and gaps | Who proposed it | Verification needed |', '|---|---|---|---|', '| [Complete locally] | [Cite source and period] | [Record actual proposer] | [Complete locally] |', '',
    '## 4. Proposed objectives and indicators', '',
    '| Proposed objective | Indicator and definition | Verified baseline | Proposed target and period |', '|---|---|---|---|', '| [Complete locally] | [Complete locally] | [Do not assume missing = zero] | [Proposal, not an approved commitment] |', '',
    '## 5. Proposed actions and resources', '',
    '| Proposed action | Area and intended beneficiaries | Responsible body to confirm | Timing | Cost and funding evidence |', '|---|---|---|---|---|', '| [Complete locally] | [Complete locally] | [Confirm mandate] | [Proposal] | [Keep estimates, budgets and expenditure separate] |', '',
    '## 6. Participation and decisions', '',
    'Record statistical facts, staff proposals, resident proposals, consultations and formal decisions separately. No agreement or approval is inferred from this document.', '',
    '| Record type | Date | Participants or responsible body | What was actually recorded | Evidence |', '|---|---|---|---|---|', '| [Proposal / consultation / decision] | [Complete] | [Complete] | [Complete] | [Source] |', '',
    '## 7. Implementation and monitoring to confirm', '',
    '- Confirm the legally required planning structure, competent authority and review process.',
    '- Assign responsibilities only after confirming mandates and participation.',
    '- Record indicator definitions, update frequency, data owner and review dates.', '',
    '## 8. Remaining evidence gaps', '',
    ...selectedGaps(dataset,territoryId).map(gap => `- ${markdownText(gap.category)} — ${markdownText(statusLabel(gap.status))}: ${markdownText(gap.detail)} Next: ${markdownText(gap.next_action)}`), '',
    'Prepared from the same dataset and selected area/period used by the dashboard. This editable Markdown is a generic planning aid, not a DOCX file or an official country form.', ''
  ];
  return lines.join('\n');
}
export function planningHtml(dataset, territoryId, period) {
  const area = dataset.territories.find(row => row.id === territoryId);
  const markdown = planningMarkdown(dataset, territoryId, period);
  // Render the exact downloadable Markdown as readable pre-wrapped text; no unsafe Markdown HTML execution.
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Planning base — ${escapeHtml(area.name)}</title><style>body{font:15px/1.6 system-ui,sans-serif;color:#172d3e;max-width:1000px;margin:28px auto;padding:0 20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}h1{font-size:24px}.note{border-left:4px solid #267868;padding:10px 16px;background:#eff6f3}@media print{body{margin:0;max-width:none;font-size:11pt}pre{white-space:pre-wrap}@page{margin:18mm}}</style><body><h1>Planning base — ${escapeHtml(area.name)}</h1><p class="note">Generic, unapproved working outline. Use your browser’s Print command to print or save as PDF. Its evidence and content match the editable Markdown download.</p><pre>${escapeHtml(markdown)}</pre></body></html>`;
}

// Polygon/MultiPolygon only. Numeric paths cannot execute source content. Dateline
// longitudes are unwrapped using the largest circular gap instead of a 358° extent.
function ringsOf(geometry) {
  if (geometry?.type === 'Polygon') return Array.isArray(geometry.coordinates) ? geometry.coordinates : [];
  if (geometry?.type === 'MultiPolygon') return Array.isArray(geometry.coordinates) ? geometry.coordinates.flatMap(polygon => Array.isArray(polygon) ? polygon : []) : [];
  return [];
}
function validRing(ring) {
  if (!Array.isArray(ring) || ring.length < 3) return null;
  if (!ring.every(point => Array.isArray(point) && finite(point[0]) && finite(point[1]) && Math.abs(point[0]) <= 180 && Math.abs(point[1]) <= 90)) return null;
  return ring;
}
export function mapGeometry(features, selectedId = '', width = 760, height = 400) {
  const shapes = features.map(feature => ({id:String(feature.properties?.territory_id || ''), rings:ringsOf(feature.geometry).map(validRing).filter(Boolean)})).filter(shape => shape.id && shape.rings.length);
  const points = shapes.flatMap(shape => shape.rings.flat());
  if (!points.length) return {paths:[], selectedHasGeometry:false, bounds:null};
  const longitudes = [...new Set(points.map(point => (point[0] + 360) % 360))].sort((a,b) => a-b);
  let cut = longitudes[0], largestGap = -1;
  for (let i=0;i<longitudes.length;i++) {
    const next = i === longitudes.length-1 ? longitudes[0] + 360 : longitudes[i+1], gap = next - longitudes[i];
    if (gap > largestGap) { largestGap = gap; cut = next % 360; }
  }
  const project = point => { const longitude = (point[0] + 360) % 360; return [longitude < cut ? longitude + 360 : longitude, -point[1]]; };
  const projected = shapes.map(shape => ({...shape, rings:shape.rings.map(ring => ring.map(project))}));
  const selected = projected.filter(shape => shape.id === selectedId);
  const boundPoints = (selected.length ? selected : projected).flatMap(shape => shape.rings.flat());
  let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
  for (const [x,y] of boundPoints) {minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}
  const midLatitude = -(minY+maxY)/2, latitudeScale = Math.max(0.15, Math.cos(midLatitude * Math.PI/180));
  const dx = Math.max(0.00001,(maxX-minX)*latitudeScale), dy = Math.max(0.00001,maxY-minY);
  const padding = 24, scale = Math.min((width-padding*2)/dx, (height-padding*2)/dy);
  const ox = (width-dx*scale)/2, oy=(height-dy*scale)/2;
  const pathPoint = point => `${((point[0]-minX)*latitudeScale*scale+ox).toFixed(2)},${((point[1]-minY)*scale+oy).toFixed(2)}`;
  return {paths:projected.map(shape => ({id:shape.id,d:shape.rings.map(ring => 'M'+ring.map(pathPoint).join('L')+'Z').join('')})), selectedHasGeometry:selected.length>0, bounds:{minX,minY,maxX,maxY,width,height}};
}
export function seriesGeometry(series, width=600, height=170) {
  const values = series.map(row => observedValue(row)).filter(finite);
  if (!values.length) return null;
  const min=Math.min(...values),max=Math.max(...values),span=max-min || Math.max(Math.abs(max)*0.05,1);
  const points = series.map((row,index) => {const value=observedValue(row);return value === null ? null : {x:40+(width-60)*(series.length===1?0.5:index/(series.length-1)),y:16+(height-46)*(max-value)/span,row};});
  const segments=[]; let segment=[];
  for (const point of points) {if(point){segment.push(point);}else if(segment.length){segments.push(segment);segment=[];}}
  if(segment.length)segments.push(segment);
  return {min,max,points:points.filter(Boolean),segments:segments.map(line => line.map(point=>`${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')),width,height};
}

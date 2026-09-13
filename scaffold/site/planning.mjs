// Optional planning contract helpers. No browser or network dependencies.
export const documentCategories = ['plan','budget','implementation','evaluation','reference'];
export const categoryLabels = {plan:'Development plans',budget:'Budgets and annual plans',implementation:'Implementation and financial results',evaluation:'Official assessments',reference:'Reference materials'};
export const findingLabels = {budget:'Budget',revenue:'Revenue',expenditure:'Expenditure',implementation_result:'Implementation result',official_evaluation:'Official assessment',budget_execution:'Budget execution',plan_achievement:'Plan achievement'};
export function categoryFor(doc) {
  if(documentCategories.includes(doc.category))return doc.category;
  return ({'published-plan':'plan','development-plan':'plan',budget:'budget','annual-plan':'budget','execution-report':'implementation','performance-report':'implementation',evaluation:'evaluation'})[doc.kind] || 'reference';
}
export const documentPeriod = doc => doc.target_period?.label || doc.period || 'Period not recorded';
export function periodText(period) {
  if(!period)return 'Period not recorded';
  return `${period.label}${period.kind?` · ${period.kind.replaceAll('_',' ')}`:''}${period.start||period.end?` · ${period.start || '?'} to ${period.end || '?'}`:''}`;
}
export function planningSettings(dataset) {
  const config=dataset.planning || {};
  return {title:config.title || 'Planning and resources',purpose:config.purpose || 'Review official materials for the selected area and prepare evidence for plan preparation or revision.',
    sections:config.sections || documentCategories.map(id=>({id,label:categoryLabels[id]})),
    explicitSections:Array.isArray(config.sections),outputs:config.outputs || ['markdown','html','evidence_csv'],
    map:config.map || {mode:'coverage'},related_links:config.related_links || [],system:config.system,update:config.update};
}
export function planningDocuments(dataset,territoryId) {return dataset.documents.filter(doc=>doc.territory_id===territoryId);}
export function documentGroups(dataset,territoryId) {
  const settings=planningSettings(dataset),documents=planningDocuments(dataset,territoryId);
  const groups=settings.sections.map(section=>({...section,documents:documents.filter(doc=>categoryFor(doc)===section.id)}));
  const assigned=new Set(groups.flatMap(group=>group.documents.map(doc=>doc.id)));
  const remaining=documents.filter(doc=>!assigned.has(doc.id));
  if(remaining.length)groups.push({id:'other',label:'Other acquired resources',documents:remaining});
  return groups.filter(group=>group.documents.length || settings.explicitSections);
}
export function hasDocumentReference(doc) {return ['link_verified','body_acquired','content_extracted','content_verified'].includes(doc.availability);}
export function acquisitionLabel(doc) {
  return ({link_verified:'Link verified',body_acquired:'Body acquired',content_extracted:'Content extracted; not cross-checked',content_verified:'Content cross-checked',not_collected:'Not collected',unavailable:'Unavailable',not_applicable:'Not applicable',unverified:'Unverified',failed:'Acquisition failed'})[doc.availability] || `Legacy / unverified: ${doc.availability || 'Not recorded'}`;
}
export function officialStatus(dataset,doc) {
  const evidence=doc.official_evidence;
  const verified=Boolean(!['unverified','unknown'].includes(doc.official_status)&&evidence?.source_id&&evidence.locator&&evidence.checked_at&&doc.territory_match&&dataset.sources.some(source=>source.id===evidence.source_id&&['ready','partial'].includes(source.status)));
  const configured=planningSettings(dataset).map.statuses?.find(status=>status.id===doc.official_status);
  return {verified,label:configured?.label || doc.official_status || 'unverified',evidence};
}
export function officialMapState(dataset,territoryId) {
  const settings=planningSettings(dataset),all=planningDocuments(dataset,territoryId).filter(doc=>(!settings.map.category||categoryFor(doc)===settings.map.category)&&(!settings.map.period||documentPeriod(doc)===settings.map.period));
  if(settings.map.mode!=='official_status') {
    const referenced=all.some(hasDocumentReference);
    return {key:referenced?'reference':'no_reference',label:referenced?'A material reference is available':'No verified material reference collected',color:referenced?'#2e806d':'#e3e7e8',documents:all};
  }
  const documents=all.filter(doc=>categoryFor(doc)===settings.map.category&&documentPeriod(doc)===settings.map.period&&officialStatus(dataset,doc).verified);
  const statuses=[...new Set(documents.map(doc=>doc.official_status))];
  if(statuses.length>1)return {key:'conflict',label:'Conflicting documented states — review sources',color:'#d6ad63',documents};
  const status=settings.map.statuses?.find(row=>row.id===statuses[0]);
  if(!status)return {key:'unknown',label:'No matched official-state evidence',color:'#e3e7e8',documents};
  return {key:status.id,label:status.label,color:status.color,documents};
}
export function selectedGaps(dataset,territoryId) {return dataset.gaps.filter(gap=>!gap.territory_id||gap.territory_id===territoryId);}
export function documentEvidence(dataset,evidence) {
  const source=dataset.sources.find(row=>row.id===evidence?.source_id);
  return source?`${source.name}; ${evidence.locator}; checked ${evidence.checked_at}${evidence.authority?`; authority: ${evidence.authority}`:''}; ${source.url}`:'Evidence not recorded';
}
export function findingValue(finding) {
  if(!Object.hasOwn(finding,'value'))return finding.statement || '';
  return finding.value_status==='observed'&&typeof finding.value==='number'&&Number.isFinite(finding.value)?`${finding.value} ${finding.unit || ''}`:`${finding.value_status || 'unverified'} (no value)`;
}
export function relatedResourceUrl(value,base,query) {
  try {
    if(/^https:\/\//i.test(value)) {const url=new URL(value);return url.username||url.password?'':url.href;}
    if(!/^\.\//.test(value)||/[\\\u0000-\u0020]/.test(value))return '';
    const url=new URL(value,base);
    if(url.origin!==new URL(base).origin||!url.pathname.startsWith(new URL(base).pathname))return '';
    for(const [key,entry] of new URLSearchParams(query))url.searchParams.set(key,entry);
    return url.href;
  } catch {return '';}
}

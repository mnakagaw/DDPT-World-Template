import {escapeHtml as e,safeUrl,statusLabel,displayValue} from './model.mjs';
import {categoryLabels,categoryFor,documentPeriod,periodText,officialStatus,documentGroups,findingLabels,acquisitionLabel} from './planning.mjs';

const external=(url,label)=>safeUrl(url)?`<a href="${e(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${e(label)}<span class="sr-only"> (opens a new tab)</span></a>`:`<span>${e(label)} · No verified link</span>`;
export function renderEvidence(dataset,evidence) {
  const source=dataset.sources.find(row=>row.id===evidence?.source_id);
  return `<p class="source-note">${source?external(source.url,source.name):'Evidence not recorded'}${evidence?` · ${e(evidence.locator)} · Checked ${e(evidence.checked_at)}${evidence.authority?` · ${e(evidence.authority)}`:''}`:''}</p>`;
}
export function renderDocument(dataset,doc) {
  const official=officialStatus(dataset,doc),source=dataset.sources.find(row=>row.id===doc.source_id),match=doc.territory_match;
  const content=doc.content;
  return `<article class="document-entry" id="document-${e(doc.id)}" data-document-id="${e(doc.id)}">
    <p class="eyebrow">${e(categoryLabels[categoryFor(doc)])}</p><h3>${e(doc.title)}</h3>
    <p class="document-period">${e(doc.target_period?periodText(doc.target_period):documentPeriod(doc))}</p>
    <p>${external(doc.url,['body_acquired','content_extracted','content_verified'].includes(doc.availability)?'Open original material':'Open source reference')}</p>
    <p class="institutional-state">${official.verified?`Documented institutional state: <strong>${e(official.label)}</strong>`:`Institutional state: ${e(statusLabel(official.label))} · not verified; no approval inferred`}</p>
    ${official.verified?renderEvidence(dataset,official.evidence):''}
    ${content?`<p class="document-summary">${e(content.summary)}</p>${content.priorities?.length?`<h4>Reported priorities</h4><ul>${content.priorities.map(text=>`<li>${e(text)}</li>`).join('')}</ul>`:''}${content.objectives?.length?`<h4>Reported objectives</h4><ul>${content.objectives.map(text=>`<li>${e(text)}</li>`).join('')}</ul>`:''}${renderEvidence(dataset,content.evidence)}`:''}
    ${(doc.findings || []).map(finding=>`<section class="document-finding"><h4>${e(findingLabels[finding.kind])} · ${e(finding.label)}</h4>${Object.hasOwn(finding,'value')?`<p class="finding-value"><strong>${finding.value_status==='observed'?e(displayValue(finding.value,dataset.country.locale)):e(statusLabel(finding.value_status))}</strong>${finding.value_status==='observed'?` ${e(finding.unit)}`:''}</p>`:''}${finding.statement?`<p>${e(finding.statement)}</p>`:''}<p>${e(periodText(finding.period))}</p><p class="small-note"><strong>Definition:</strong> ${e(finding.definition)} <strong>Scope:</strong> ${e(finding.scope)}${finding.scale?` <strong>Scale:</strong> ${e(finding.scale.label)} (${e(finding.scale.min)}–${e(finding.scale.max)})`:''}</p>${renderEvidence(dataset,finding.evidence)}</section>`).join('')}
    <details class="document-process"><summary>Source and acquisition details · ${e(acquisitionLabel(doc))}</summary><p>${e(source?.publisher)} · ${source?external(source.url,source.name):'Source not recorded'} · Retrieved ${e(source?.retrieved_at || 'Not recorded')}</p><p>Acquisition: ${e(acquisitionLabel(doc))}. This describes collection, not legal approval or performance.</p>${!content?'<p>No cross-checked content summary is available. Consult the source reference; no plan content is inferred.</p>':''}${match?`<p>Matched identity: ${e(match.country_id)} · ${e(match.type)} · ${e(match.code_system)} · ${e(match.official_code??'Official code not verified')} · Boundary ${e(match.boundary_version??'Not verified')}. Validity: ${e(match.valid_from||'Not recorded')} to ${e(match.valid_to||'Not recorded')}. Method: ${e(match.method)}.</p>${renderEvidence(dataset,match)}`:'<p>Legacy record: extended identity evidence has not been recorded.</p>'}<p class="small-note">Original SHA-256: ${e(source?.sha256 || 'Body not archived')}</p></details>
  </article>`;
}
export function renderDocumentGroups(dataset,territoryId) {
  const groups=documentGroups(dataset,territoryId);
  return groups.length?groups.map(group=>`<section class="document-group" aria-labelledby="documents-${e(group.id)}"><h2 id="documents-${e(group.id)}">${e(group.label)}</h2>${group.documents.length?group.documents.map(doc=>renderDocument(dataset,doc)).join(''):`<p class="missing-note">${e(group.empty_message || 'No material in this category has been collected for this area. This does not establish whether it exists or is approved.')}</p>`}</section>`).join(''):'<p class="missing-note">No documents have been collected for this area. Available statistics and working outputs below can still be used. Missing documents do not establish whether a plan exists or is approved.</p>';
}

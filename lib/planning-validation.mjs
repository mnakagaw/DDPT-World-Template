/** Optional planning contract for schema 0.2. Never upgrades legacy assertions. */
export const PLANNING_CATEGORIES=['plan','budget','implementation','evaluation','reference'];
export const DOCUMENT_AVAILABILITY=['link_verified','body_acquired','content_extracted','content_verified','not_collected','unavailable','not_applicable','unverified','failed'];
const PERIOD_KINDS=['calendar_year','fiscal_year','quarter','multi_year','as_of','other'];
const FINDING_KINDS=['budget','revenue','expenditure','implementation_result','official_evaluation','budget_execution','plan_achievement'];
const VALUE_STATES=['observed','missing','not_applicable','unverified','failed'];
const OUTPUTS=['markdown','html','evidence_csv','documents_csv'];
const BODY_STAGES=new Set(['body_acquired','content_extracted','content_verified']);
const EXTENSION_FIELDS=['category','target_period','territory_match','official_evidence','content','findings'];
const own=(object,key)=>Object.prototype.hasOwnProperty.call(object,key);
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const text=value=>typeof value==='string' && value.trim().length>0;
const number=value=>typeof value==='number' && Number.isFinite(value);
export function isRawEvidencePath(value) {
  return text(value) && !/(^[/\\]|^[A-Za-z][A-Za-z0-9+.-]*:|[\u0000-\u001f\u007f]|(^|[/\\])\.\.([/\\]|$))/.test(value);
}
export function isIsoDate(value) {
  if(typeof value!=='string' || !/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
  const parsed=new Date(value+'T00:00:00Z');
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0,10)===value;
}
function checkedDate(value) {
  return typeof value==='string' && isIsoDate(value.slice(0,10)) && (value.length===10 || /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)) && Number.isFinite(Date.parse(value));
}
export function isPlanningLink(value) {
  if(!text(value) || /[\u0000-\u0020\u007f\\]/.test(value))return false;
  if(/^https:/i.test(value)) {
    try {const url=new URL(value);return url.protocol==='https:' && !url.username && !url.password;}catch{return false;}
  }
  if(!value.startsWith('./') || /^[a-z][a-z0-9+.-]*:/i.test(value))return false;
  let pathname=value.split(/[?#]/,1)[0];
  try {for(let i=0;i<3;i++){const next=decodeURIComponent(pathname);if(next===pathname)break;pathname=next;}}catch{return false;}
  return !pathname.startsWith('/') && !/[\\\u0000-\u0020\u007f]/.test(pathname) && !pathname.split('/').includes('..') && !/^[a-z][a-z0-9+.-]*:/i.test(pathname);
}

export function validatePlanning(data) {
  const errors=[],warnings=[];
  const fail=message=>errors.push(message),warn=message=>warnings.push(message);
  if(!object(data))return {errors:['Planning validation needs a dataset object'],warnings};
  const registry=(items)=>new Map((Array.isArray(items)?items:[]).filter(row=>object(row)&&text(row.id)).map(row=>[row.id,row]));
  const territories=registry(data.territories),sources=registry(data.sources);
  const country=object(data.country)?data.country:{};
  const required=(record,key,path)=>{if(!text(record[key]))fail(`${path}.${key} must be a nonempty string`);};
  const strings=(value,path,{nonempty=false}={})=>{
    if(!Array.isArray(value)){fail(`${path} must be an array of strings`);return [];}
    if(nonempty&&!value.length)fail(`${path} needs at least one value`);
    if(value.some(item=>!text(item)))fail(`${path} must contain nonempty strings`);
    const valid=value.filter(text);
    if(new Set(valid).size!==valid.length)fail(`${path} contains duplicate values`);
    return valid;
  };
  const interval=(record,path,startKey='start',endKey='end')=>{
    for(const key of [startKey,endKey])if(own(record,key)&&!isIsoDate(record[key]))fail(`${path}.${key} must be an ISO calendar date`);
    if(isIsoDate(record[startKey])&&isIsoDate(record[endKey])&&record[startKey]>record[endKey])fail(`${path} date interval is reversed`);
  };
  const period=(value,path)=>{
    if(!object(value)){fail(`${path} must be a period object`);return null;}
    required(value,'label',path);
    if(!PERIOD_KINDS.includes(value.kind))fail(`${path}.kind must identify a calendar year, fiscal year, quarter, multi-year, as-of or other period`);
    interval(value,path);return value;
  };
  const evidence=(value,path)=>{
    if(!object(value)){fail(`${path} must be an evidence object`);return;}
    required(value,'source_id',path);required(value,'locator',path);
    if(!checkedDate(value.checked_at))fail(`${path}.checked_at must be an ISO date or timestamp`);
    const source=sources.get(value.source_id);
    if(!source)fail(`${path}.source_id must reference a registered source`);
    else if(!['ready','partial'].includes(source.status))fail(`${path} cannot verify evidence from a ${source.status || 'missing-status'} source`);
    if(own(value,'authority')&&!text(value.authority))fail(`${path}.authority must be a nonempty string when supplied`);
  };
  const rawEvidence=(sourceId,path)=>{
    const source=sources.get(sourceId);
    if(!source || !isRawEvidencePath(source.raw_path) || !/^[a-f0-9]{64}$/i.test(typeof source.sha256==='string'?source.sha256:''))fail(`${path} requires its document source raw_path and SHA-256`);
  };
  for(const [id,area] of territories)interval(area,`territories[${id}]`,'valid_from','valid_to');

  if(own(data,'planning')) {
    const planning=data.planning;
    if(!object(planning))fail('planning must be an object when supplied');
    else {
      for(const key of ['title','purpose'])if(own(planning,key)&&!text(planning[key]))fail(`planning.${key} must be a nonempty string`);
      if(own(planning,'sections')) {
        if(!Array.isArray(planning.sections))fail('planning.sections must be an array');
        else {
          const seen=new Set();
          planning.sections.forEach((section,index)=>{
            const path=`planning.sections[${index}]`;
            if(!object(section)){fail(`${path} must be an object`);return;}
            if(!PLANNING_CATEGORIES.includes(section.id))fail(`${path}.id must be a known planning category`);
            if(seen.has(section.id))fail(`${path} has a duplicate category`);seen.add(section.id);
            required(section,'label',path);
            if(own(section,'empty_message')&&!text(section.empty_message))fail(`${path}.empty_message must be a nonempty string`);
          });
        }
      }
      if(own(planning,'system')) {
        if(!object(planning.system))fail('planning.system must be an object');
        else {
          for(const key of ['label','scope','cycle'])required(planning.system,key,'planning.system');
          for(const id of strings(planning.system.source_ids,'planning.system.source_ids',{nonempty:true}))if(!sources.has(id))fail(`planning.system references unknown source ${id}`);
        }
      }
      if(own(planning,'outputs')) {
        for(const output of strings(planning.outputs,'planning.outputs'))if(!OUTPUTS.includes(output))fail(`planning.outputs contains unsupported format ${output}`);
        if(Array.isArray(planning.outputs)&&!planning.outputs.length)warn('planning.outputs is empty: the page must explain the available source or local-work alternative');
      }
      if(own(planning,'map')) {
        const map=planning.map;
        if(!object(map))fail('planning.map must be an object');
        else {
          if(!['coverage','official_status'].includes(map.mode))fail('planning.map.mode must be coverage or official_status');
          if(own(map,'category')&&!PLANNING_CATEGORIES.includes(map.category))fail('planning.map.category must be a known document category');
          if(own(map,'period')&&!text(map.period))fail('planning.map.period must be an exact document-period label');
          if(map.mode==='official_status') {
            if(!PLANNING_CATEGORIES.includes(map.category))fail('Official-status map requires a document category');
            if(!text(map.period))fail('Official-status map requires an exact document-period label');
            if(!Array.isArray(map.statuses)||!map.statuses.length)fail('Official-status map requires country-specific status definitions');
          }
          if(own(map,'statuses')) {
            if(!Array.isArray(map.statuses))fail('planning.map.statuses must be an array');
            else {
              const seen=new Set();
              map.statuses.forEach((status,index)=>{
                const path=`planning.map.statuses[${index}]`;
                if(!object(status)){fail(`${path} must be an object`);return;}
                required(status,'id',path);required(status,'label',path);
                if(seen.has(status.id))fail(`${path} has a duplicate status id`);seen.add(status.id);
                if(!/^#(?:[a-f0-9]{3}|[a-f0-9]{6}|[a-f0-9]{8})$/i.test(typeof status.color==='string'?status.color:''))fail(`${path}.color must be a hexadecimal color`);
                if(['unverified','unknown','conflict'].includes(status.id))fail(`${path} cannot redefine a reserved unknown or conflict state as a country-specific verified status`);
              });
            }
          }
        }
      }
      if(own(planning,'related_links')) {
        if(!Array.isArray(planning.related_links))fail('planning.related_links must be an array');
        else planning.related_links.forEach((item,index)=>{
          const path=`planning.related_links[${index}]`;
          if(!object(item)){fail(`${path} must be an object`);return;}
          required(item,'label',path);
          if(!isPlanningLink(item.url))fail(`${path}.url must be HTTPS or a safe site-root-relative path without traversal`);
          if(own(item,'territory_id')&&!territories.has(item.territory_id))fail(`${path}.territory_id must reference a registered territory`);
        });
      }
      if(own(planning,'update')) {
        const update=planning.update;
        if(!object(update))fail('planning.update must be an object');
        else {
          if(!['current','stopped'].includes(update.status))fail('planning.update.status must be current or stopped');
          required(update,'message','planning.update');
          if(!checkedDate(update.checked_at))fail('planning.update.checked_at must be an ISO date or timestamp');
          if(own(update,'last_success_at')&&!checkedDate(update.last_success_at))fail('planning.update.last_success_at must be an ISO date or timestamp');
          if(checkedDate(update.last_success_at)&&checkedDate(update.checked_at)&&Date.parse(update.last_success_at)>Date.parse(update.checked_at))fail('planning.update.last_success_at cannot be after checked_at');
        }
      }
    }
  }

  if(Array.isArray(data.documents))data.documents.forEach((doc,index)=>{
    const path=`documents[${object(doc)&&text(doc.id)?doc.id:index}]`;
    if(!object(doc)){fail(`${path} must be an object`);return;}
    const extended=EXTENSION_FIELDS.some(key=>own(doc,key)) || BODY_STAGES.has(doc.availability);
    const area=territories.get(doc.territory_id);
    if(own(doc,'category')&&!PLANNING_CATEGORIES.includes(doc.category))fail(`${path}.category must be a known planning category`);
    if(!DOCUMENT_AVAILABILITY.includes(doc.availability))warn(`${path}.availability is a legacy or unknown string; display it as unverified and do not infer an acquisition stage`);
    if(own(doc,'extraction_status')||own(doc,'extraction_stage'))fail(`${path} must use availability as the single acquisition axis; no extraction_status or extraction_stage`);
    let target=null;
    if(own(doc,'target_period')) {
      target=period(doc.target_period,`${path}.target_period`);
      if(target&&own(doc,'period')&&doc.period!==target.label)fail(`${path}.period must equal target_period.label literally`);
    }
    if(BODY_STAGES.has(doc.availability))rawEvidence(doc.source_id,path);
    const hasClaims=['official_evidence','content','findings'].some(key=>own(doc,key));
    if(hasClaims&&!own(doc,'territory_match'))fail(`${path} evidence-backed content or status requires territory_match`);
    if(own(doc,'territory_match')) {
      const match=doc.territory_match,matchPath=`${path}.territory_match`;
      if(!object(match))fail(`${matchPath} must be an object`);
      else {
        required(match,'territory_id',matchPath);
        if(match.territory_id!==doc.territory_id)fail(`${matchPath}.territory_id must exactly match document.territory_id; shared null codes do not establish identity`);
        if(!territories.has(match.territory_id))fail(`${matchPath}.territory_id must reference the registered matched territory`);
        if(match.country_id!==country.id)fail(`${matchPath}.country_id must match the dataset country`);
        for(const key of ['type','code_system']) {
          required(match,key,matchPath);
          if(!area || match[key]!==area[key])fail(`${matchPath}.${key} must exactly match the linked territory`);
        }
        for(const key of ['official_code','boundary_version']) {
          if(!own(match,key) || !(match[key]===null || text(match[key])))fail(`${matchPath}.${key} must be explicit text or null`);
          if(!area || match[key]!== (area[key] ?? null))fail(`${matchPath}.${key} must exactly match the linked territory; null only when absent in the registry`);
        }
        required(match,'method',matchPath);evidence(match,matchPath);interval(match,matchPath,'valid_from','valid_to');
        for(const key of ['valid_from','valid_to'])if(own(match,key)&&area&&own(area,key)&&match[key]!==area[key])fail(`${matchPath}.${key} must match the registered historical validity date`);
        const validFrom=area?.valid_from ?? match.valid_from,validTo=area?.valid_to ?? match.valid_to;
        if(target&&isIsoDate(target.start)&&isIsoDate(target.end)&&isIsoDate(validFrom)&&isIsoDate(validTo)&&(target.end<validFrom || target.start>validTo))fail(`${path} target period does not overlap the matched territory validity; use the correct historical registry record`);
      }
    }
    const asserted=text(doc.official_status)&&!['unverified','unknown'].includes(doc.official_status);
    if(asserted&&!own(doc,'official_evidence')) {
      if(extended)fail(`${path} asserted official_status requires official_evidence`);
      else warn(`${path} legacy official_status is not evidence-verified and cannot color an official-status map`);
    }
    if(own(doc,'official_evidence'))evidence(doc.official_evidence,`${path}.official_evidence`);
    if(own(doc,'content')) {
      if(doc.availability!=='content_verified')fail(`${path}.content requires availability content_verified`);
      if(!object(doc.content))fail(`${path}.content must be an object`);
      else {
        required(doc.content,'summary',`${path}.content`);
        for(const key of ['priorities','objectives'])if(own(doc.content,key))strings(doc.content[key],`${path}.content.${key}`);
        evidence(doc.content.evidence,`${path}.content.evidence`);
      }
    }
    if(own(doc,'findings')) {
      if(doc.availability!=='content_verified')fail(`${path}.findings requires availability content_verified`);
      if(!Array.isArray(doc.findings))fail(`${path}.findings must be an array`);
      else doc.findings.forEach((finding,findingIndex)=>{
        const findingPath=`${path}.findings[${findingIndex}]`;
        if(!object(finding)){fail(`${findingPath} must be an object`);return;}
        if(!FINDING_KINDS.includes(finding.kind))fail(`${findingPath}.kind must preserve the published budget, financial, implementation or evaluation meaning`);
        for(const key of ['label','definition','scope'])required(finding,key,findingPath);
        period(finding.period,`${findingPath}.period`);evidence(finding.evidence,`${findingPath}.evidence`);
        if(own(finding,'statement')&&!text(finding.statement))fail(`${findingPath}.statement must be nonempty text`);
        if(own(finding,'value_status')&&!VALUE_STATES.includes(finding.value_status))fail(`${findingPath}.value_status is invalid`);
        if(own(finding,'value')) {
          if(!VALUE_STATES.includes(finding.value_status))fail(`${findingPath}.value requires an explicit value_status`);
          if(finding.value_status==='observed'&&!number(finding.value))fail(`${findingPath}.observed value must be finite; null is not zero`);
          if(finding.value_status!=='observed'&&finding.value!==null)fail(`${findingPath}.non-observed value must be null, never zero`);
          if(number(finding.value))required(finding,'unit',findingPath);
        } else {
          if(!text(finding.statement))fail(`${findingPath} needs a statement or an explicit value and value_status`);
          if(finding.value_status==='observed')fail(`${findingPath}.observed value_status requires a numeric value`);
        }
        if(own(finding,'unit')&&!text(finding.unit))fail(`${findingPath}.unit must be a nonempty string`);
        if(own(finding,'scale')) {
          const scale=finding.scale;
          if(!object(scale))fail(`${findingPath}.scale must be an object`);
          else {
            required(scale,'label',`${findingPath}.scale`);
            if(!number(scale.min)||!number(scale.max)||scale.min>=scale.max)fail(`${findingPath}.scale requires finite ordered min and max`);
            if(number(finding.value)&&number(scale.min)&&number(scale.max)&&(finding.value<scale.min || finding.value>scale.max))fail(`${findingPath}.value is outside the declared source scale`);
          }
        }
      });
    }
  });
  if(Array.isArray(data.gaps))data.gaps.forEach((gap,index)=>{
    if(!object(gap)){fail(`gaps[${index}] must be an object`);return;}
    if(own(gap,'territory_id')&&!territories.has(gap.territory_id))fail(`gaps[${index}].territory_id must reference a registered territory`);
    if(own(gap,'source_id')&&!sources.has(gap.source_id))fail(`gaps[${index}].source_id must reference a registered source`);
  });
  return {errors:[...new Set(errors)],warnings:[...new Set(warnings)]};
}

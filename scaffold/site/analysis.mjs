// Pure, dependency-free internal comparison. Never changes the selected geography.
const list=value=>Array.isArray(value)?value:[];
const own=(value,key)=>value!=null && Object.prototype.hasOwnProperty.call(value,key);
const finite=value=>typeof value==='number' && Number.isFinite(value);
const normalized=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim().replace(/[ -]+/g,'_');
const terminalTypes=new Set(['city','municipality','municipio','municipalidad','commune','comuna','municipal_district','distrito_municipal','town','town_council','village']);
export const COMPARISON_COLORS=['#e7f1e8','#b6d7be','#79b58e','#3b8763','#155d46'];
export const NO_COMPARISON_COLOR='#dce1e6';

export function isTerminalTerritory(data,areaOrId) {
  const area=typeof areaOrId==='string'?list(data?.territories).find(item=>item?.id===areaOrId):areaOrId;
  return !!area && (list(data?.analysis?.terminal_territory_ids).includes(area.id) || terminalTypes.has(normalized(area.type)) || terminalTypes.has(normalized(area.level)));
}
export function isDescendant(territories,childId,parentId) {
  const byId=new Map(list(territories).filter(Boolean).map(area=>[area.id,area])),seen=new Set([childId]);
  let next=byId.get(childId)?.parent_id;
  while(next!=null) {
    if(next===parentId)return childId!==parentId;
    if(seen.has(next))return false;
    seen.add(next);next=byId.get(next)?.parent_id;
  }
  return false;
}
export function comparisonSet(data,parentId) {
  const areas=list(data?.territories),parent=areas.find(area=>area?.id===parentId);
  const config=list(data?.analysis?.comparisons).find(item=>item?.parent_id===parentId);
  const terminal=isTerminalTerritory(data,parent);
  const ids=list(config?.member_ids);
  const members=!parent || terminal?[]:config?ids.map(id=>areas.find(area=>area?.id===id)).filter(area=>area && isDescendant(areas,area.id,parentId)):areas.filter(area=>area?.parent_id===parentId);
  return {parent:parent||null,members,label:config?.label || `Internal comparison · ${parent?.name||parentId}`,
    note:terminal?'Internal comparison stops at this base municipality or explicitly terminal area.':config?.membership_note || 'Direct child areas in the registered geographic hierarchy. Membership is not inferred from names.',
    terminal,source_ids:list(config?.source_ids),explicit:!!config,color_scale:config?.color_scale || {mode:'within_selection'}};
}

// National statistics may populate a matching country, never its local areas.
// A legacy single-country root without country_id remains supported.
export function nationalSourceMatches(data,source,area) {
  if(source?.geographic_level!=='national')return true;
  if(!area || normalized(area.type)!=='country')return false;
  if(data?.analysis?.kind==='world')return typeof source.country_id==='string' && !!source.country_id && area.country_id===source.country_id;
  if(area.id===data?.country?.national_territory_id)return !source.country_id || source.country_id===(area.country_id || data.country.id);
  return typeof source.country_id==='string' && !!source.country_id && area.country_id===source.country_id;
}
export function worldSeriesSourceMatches(data,source,area) {
  if(source?.geographic_level!=='world_country_series')return true;
  return data?.analysis?.kind==='world' && (!!area && area.type==='country' && /^[A-Z0-9]{3}$/.test(area.country_id || '') || area?.id==='WLD' && area.id===data?.country?.national_territory_id && area.type==='exploration_scope');
}
export function boundaryIdentity(feature,area) {
  if(!area || feature?.properties?.territory_id!==area.id)return {matches:false,reason:'Boundary territory ID does not match the registered area.'};
  for(const [property,field] of [['code','official_code'],['official_code','official_code'],['code_system','code_system'],['boundary_version','boundary_version']]) {
    if(own(feature.properties,property) && feature.properties[property]!==area[field])return {matches:false,reason:`Boundary ${property} does not match the registered area.`};
  }
  return {matches:true,reason:''};
}

const metadata=(indicator,observation)=>({
  definition_id:observation?.definition_id ?? indicator?.definition_id ?? indicator?.id ?? null,
  definition:observation?.definition ?? indicator?.definition ?? '',
  unit:observation?.unit ?? indicator?.unit ?? '',
  population:observation?.population ?? indicator?.population ?? null,
  method:observation?.measurement_method ?? observation?.method ?? indicator?.measurement_method ?? indicator?.method ?? null
});
function meaningReasons(indicator,observation) {
  if(!observation)return [];
  const canonical=metadata(indicator,null),actual=metadata(indicator,observation),reasons=[];
  for(const key of ['definition_id','definition','unit','population','method']) {
    if(actual[key]!==canonical[key])reasons.push(`${key} differs from the shared indicator definition${canonical[key]==null?' (canonical value is not declared)':''}.`);
  }
  if(own(observation,'measurement_method') && own(observation,'method') && observation.method!==observation.measurement_method)reasons.push('Observation method aliases disagree.');
  return reasons;
}
export function observationMeaning(indicator,observation) {
  const reasons=meaningReasons(indicator,observation);
  return {...metadata(indicator,observation),comparable:reasons.length===0,reason:reasons.join(' ')};
}
// Comparison context is separate from whether a numeric observation exists.
// Never replaces value/status; callers retain the source row even when its
// context excludes it from comparison or a connected history line.
export function observationContext(data,area,indicator,observation) {
  const meaning=observationMeaning(indicator,observation);
  const source=list(data?.sources).find(item=>item?.id===(observation?.source_id || indicator?.source_id))||null;
  const reasons=[meaning.reason];
  if(observation && !source)reasons.push('Observation source is unavailable.');
  if(source && !['ready','partial'].includes(source.status))reasons.push('Observation source has no acquired usable data.');
  if(!nationalSourceMatches(data,source,area))reasons.push('National source country identity does not match this area.');
  if(!worldSeriesSourceMatches(data,source,area))reasons.push('World country series does not supply regional or local observations.');
  if(observation && own(observation,'boundary_version') && observation.boundary_version!==area?.boundary_version)reasons.push('Observation boundary edition does not match the registered area.');
  return {...meaning,source,meaning_comparable:meaning.comparable,comparable:reasons.every(reason=>!reason),reason:reasons.filter(Boolean).join(' ')};
}
function cohortReason(set) {
  if(set.explicit || set.members.length<2)return '';
  const fields=['type','level'];
  // Different countries have independent boundary editions; this is not an epoch mix within one country.
  if(!set.members.every(area=>normalized(area.type)==='country'))fields.push('boundary_version');
  const mixed=fields.filter(field=>new Set(set.members.map(area=>area[field]??null)).size>1);
  return mixed.length?`Comparison membership needs an explicit source-backed declaration: direct children have different ${mixed.join(', ')}.`:'';
}
function buildScale(config,rows) {
  const colors=[...COMPARISON_COLORS],values=rows.filter(row=>row.comparable && finite(row.value)).map(row=>row.value);
  const mode=config?.mode==='fixed'?'fixed':'within_selection';
  const label=config?.label || (mode==='fixed'?'Fixed thresholds':'Equal intervals within this selection');
  let breaks=[];
  if(mode==='fixed')breaks=list(config.breaks).filter(finite);
  else if(values.length) {
    const min=values.reduce((a,b)=>Math.min(a,b),Infinity),max=values.reduce((a,b)=>Math.max(a,b),-Infinity);
    if(min===max)return {mode,breaks:[],colors,label,constant_value:min,legend:[{color:colors[2],label:`= ${numberText(min)}`,lower:min,upper:max}]};
    breaks=[1,2,3,4].map(step=>min*(1-step/5)+max*(step/5));
  }
  if(breaks.length!==4 || breaks.some((value,index)=>index>0 && value<=breaks[index-1]))return {mode,breaks:[],colors,label,legend:[]};
  const legend=colors.map((color,index)=>({color,lower:index?breaks[index-1]:null,upper:index<4?breaks[index]:null,
    label:index===0?`≤ ${numberText(breaks[0])}`:index===4?`> ${numberText(breaks[3])}`:`> ${numberText(breaks[index-1])} to ≤ ${numberText(breaks[index])}`}));
  return {mode,breaks,legend,colors,label};
}
const numberText=value=>Number(value.toPrecision(6)).toLocaleString('en',{maximumSignificantDigits:6});
export function colorForComparison(comparison,row) {
  const scale=comparison?.scale;
  if(!row?.comparable || !finite(row.value) || !scale?.legend?.length)return NO_COMPARISON_COLOR;
  if(finite(scale.constant_value))return scale.colors[2];
  const index=scale.breaks.findIndex(value=>row.value<=value);
  return scale.colors[index<0?4:index];
}

export function internalComparison(data,parentId,indicatorId,period) {
  const set=comparisonSet(data,parentId),indicator=list(data?.indicators).find(item=>item?.id===indicatorId)||null;
  const commonReason=cohortReason(set),sources=list(data?.sources),observations=list(data?.observations),boundaries=list(data?.boundaries?.features);
  const membershipUnavailable=set.source_ids.some(id=>!['ready','partial'].includes(sources.find(source=>source?.id===id)?.status));
  const rows=set.members.map(area=>{
    const observation=observations.find(row=>row?.territory_id===area.id && row.indicator_id===indicatorId && String(row.period)===String(period))||null;
    const value=observation?.status==='observed' && finite(observation.value)?observation.value:null;
    const status=observation?.status || (observations.some(row=>row?.territory_id===area.id && row.indicator_id===indicatorId)?'missing':'not_collected');
    const candidates=boundaries.filter(feature=>feature?.properties?.territory_id===area.id);
    const match=candidates.length===1?boundaryIdentity(candidates[0],area):null;
    const boundary=match?.matches?candidates[0]:null;
    const boundary_reason=candidates.length>1?'Multiple boundaries share this territory ID; no geometry was joined.':candidates.length===0?'No boundary collected for this area.':match.reason;
    const context=observationContext(data,area,indicator,observation);
    const reasons=[!indicator?'Indicator is unavailable.':'',commonReason,membershipUnavailable?'Comparison membership source is not available.':'',context.reason];
    if(value===null)reasons.push(status==='not_collected'?'No observations collected for this indicator and area.':`No observed value in the exact requested period (${status}).`);
    return {area,observation,value,status,...context,comparable:reasons.every(reason=>!reason),reason:reasons.filter(Boolean).join(' '),boundary,boundary_reason};
  });
  const scale=buildScale(set.color_scale,rows);
  const reason=!set.parent?'Selected area is unavailable.':set.terminal?set.note:!set.members.length?'No internal comparison areas are configured or collected.':commonReason || (!rows.some(row=>row.comparable)?'No comparable numeric values are available for this exact indicator and period.':'');
  return {set,rows,features:rows.map(row=>row.boundary).filter(Boolean),scale,reason,indicator,period:String(period??'')};
}

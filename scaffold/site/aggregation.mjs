// Source-first, non-overlapping aggregation for AreaData.
// An exact observation always wins. Calculations are allowed only by an
// explicit indicator rule and a complete, source-backed membership cover.
import {comparisonSet,isDescendant,observationContext} from './analysis.mjs';

const list=value=>Array.isArray(value)?value:[];
const finite=value=>typeof value==='number' && Number.isFinite(value);
export const LATEST_AVAILABLE_PERIOD='latest-available';

export function aggregationRule(data,indicatorId) {
  return list(data?.analysis?.aggregation?.rules).find(rule=>rule?.indicator_id===indicatorId) || null;
}

function latestObserved(rows) {
  return [...rows].filter(row=>row?.status==='observed' && finite(row.value)).sort((a,b)=>String(b.period).localeCompare(String(a.period),'en',{numeric:true}))[0] || null;
}

function direct(data,territoryId,indicatorId,period,rule=null) {
  const area=list(data?.territories).find(item=>item?.id===territoryId) || null;
  const indicator=list(data?.indicators).find(item=>item?.id===indicatorId) || null;
  const areaRows=list(data?.observations).filter(item=>item?.territory_id===territoryId && item.indicator_id===indicatorId);
  const mixed=String(period)===LATEST_AVAILABLE_PERIOD && rule?.period_policy==='latest_available_by_component';
  const row=mixed?latestObserved(areaRows):areaRows.find(item=>String(item.period)===String(period)) || null;
  const value=row?.status==='observed' && finite(row.value)?row.value:null;
  const context=observationContext(data,area,indicator,row);
  const status=row?.status || (areaRows.length?'missing':'not_collected');
  return {area,indicator,row,value,status,context,period:row?String(row.period):String(period)};
}

function completeCover(data,territoryId,indicatorId,period,rule,visiting=new Set()) {
  if(visiting.has(territoryId))return {complete:false,components:[],missing_ids:[territoryId],reason:'Geographic hierarchy contains a cycle.'};
  const exact=direct(data,territoryId,indicatorId,period,rule);
  if(exact.value!==null && exact.context.comparable)return {complete:true,components:[{territory_id:territoryId,value:exact.value,period:exact.period,row:exact.row,source_id:exact.row?.source_id,scope:'exact'}],missing_ids:[],reason:''};
  const cover=list(data?.analysis?.aggregation?.coverage_sets).find(item=>item.parent_id===territoryId&&item.indicator_id===indicatorId);
  const directChildren=list(data?.territories).filter(item=>item.parent_id===territoryId);
  const exactChildren=cover && cover.member_ids.length===directChildren.length && directChildren.every(child=>cover.member_ids.includes(child.id));
  const set=cover?{explicit:Boolean(exactChildren),members:list(cover.member_ids).map(id=>data.territories.find(item=>item.id===id)).filter(Boolean),source_ids:list(cover.source_ids)}:comparisonSet(data,territoryId);
  const membershipReady=set.explicit && set.members.length>0 && set.source_ids.length>0 && set.source_ids.every(id=>['ready','partial'].includes(data.sources.find(source=>source.id===id)?.status));
  if(!membershipReady)return {complete:false,components:[],missing_ids:[territoryId],reason:cover?'Aggregation cover is not an exact, source-backed set of direct children.':set.explicit?'Membership evidence is unavailable or has no members.':'No explicit source-backed complete membership is configured.'};
  const next=new Set(visiting);next.add(territoryId);
  const parts=set.members.map(area=>completeCover(data,area.id,indicatorId,period,rule,next));
  const components=parts.flatMap(part=>part.components),missing_ids=[...new Set(parts.flatMap(part=>part.missing_ids))];
  return {complete:parts.every(part=>part.complete),components,missing_ids,reason:parts.filter(part=>!part.complete).map(part=>part.reason).filter(Boolean).join(' ')};
}

function validateSelection(data,ids) {
  const unique=[...new Set(list(ids).filter(id=>data.territories.some(area=>area.id===id)))];
  const overlap=unique.some(id=>unique.some(other=>id!==other && (isDescendant(data.territories,id,other)||isDescendant(data.territories,other,id))));
  return {ids:unique,overlap};
}

/** Resolve one area or a user-defined group without double counting.
 * Returns value=null for incomplete coverage; covered_value remains a labelled subtotal.
 */
export function resolvedObservation(data,territoryIds,indicatorId,period) {
  const selection=validateSelection(data,Array.isArray(territoryIds)?territoryIds:[territoryIds]);
  const indicator=data.indicators.find(item=>item.id===indicatorId) || null;
  const rule=aggregationRule(data,indicatorId);
  const mixedRequested=String(period)===LATEST_AVAILABLE_PERIOD;
  if(!selection.ids.length)return {value:null,status:'not_collected',provenance:'none',row:null,components:[],missing_ids:[],covered_value:null,complete:false,note:'No valid analysis area is selected.'};
  if(selection.overlap)return {value:null,status:'incomparable',provenance:'none',row:null,components:[],missing_ids:selection.ids,covered_value:null,complete:false,note:'The selection overlaps an ancestor and its descendant; no total is calculated.'};
  if(mixedRequested && rule?.period_policy!=='latest_available_by_component')return {value:null,status:'not_available',provenance:'none',row:null,components:[],missing_ids:selection.ids,covered_value:null,complete:false,period_policy:rule?.period_policy || 'same_period',note:'Latest-available component periods are not approved for this indicator. Select one exact source period.'};
  if(selection.ids.length===1) {
    const exact=direct(data,selection.ids[0],indicatorId,period,rule);
    if(exact.value!==null){
      const provenance=exact.row?.provenance==='calculated'?'calculated':'source_reported';
      return {value:exact.value,status:provenance==='calculated'?'calculated':exact.status,provenance,row:exact.row,components:[{territory_id:selection.ids[0],value:exact.value,period:exact.period,row:exact.row,source_id:exact.row?.source_id,scope:'exact'}],missing_ids:[],covered_value:exact.value,complete:true,period_policy:rule?.period_policy || 'same_period',component_periods:[exact.period],note:provenance==='calculated'&&exact.row?.footnote?exact.row.footnote:mixedRequested?`Exact observation for the selected area from its latest available period (${exact.period}).`:'Exact observation for the selected area; lower-area gaps do not affect it.'};
    }
  }
  if(!rule || rule.method!=='sum') {
    const exact=selection.ids.length===1?direct(data,selection.ids[0],indicatorId,period,rule):null;
    return {value:null,status:exact?.status || 'not_available',provenance:'none',row:exact?.row || null,components:[],missing_ids:selection.ids,covered_value:null,complete:false,note:rule?.method==='ratio'?'A rate requires compatible numerator and denominator totals; percentages are never averaged.':'No approved aggregation method exists for this indicator; averages are not calculated.'};
  }
  const covers=selection.ids.map(id=>completeCover(data,id,indicatorId,period,rule));
  const components=covers.flatMap(item=>item.components),missing_ids=[...new Set(covers.flatMap(item=>item.missing_ids))];
  const duplicate=new Set(),seen=new Set();
  for(const component of components){if(seen.has(component.territory_id))duplicate.add(component.territory_id);seen.add(component.territory_id);}
  if(duplicate.size)return {value:null,status:'incomparable',provenance:'none',row:null,components,missing_ids:[...duplicate],covered_value:null,complete:false,note:'The available cover contains duplicate areas; no total is calculated.'};
  const covered_value=components.reduce((sum,item)=>sum+item.value,0);
  const complete=covers.every(item=>item.complete);
  const component_periods=[...new Set(components.map(item=>String(item.period)))];
  const periodSummary=components.map(item=>`${item.territory_id} ${item.period}`).join(', ');
  const periodNote=mixedRequested?` Mixed reference periods by component: ${periodSummary || 'none'}. This is not a same-year total.`:'';
  return {value:complete?covered_value:null,status:complete?'calculated':'incomplete',provenance:'areadata_calculated',row:null,components,missing_ids,covered_value,complete,period_policy:rule.period_policy || 'same_period',component_periods,
    note:(complete?`AreaData sum from ${components.length} non-overlapping source observations. Exact higher-level observations were used before lower areas.`:`No full-coverage total. The labelled covered subtotal uses ${components.length} source observations; ${missing_ids.length} areas remain uncovered.`)+periodNote};
}

export function aggregationAuditRows(data,territoryIds,indicatorId,period) {
  const result=resolvedObservation(data,territoryIds,indicatorId,period);
  return result.components.map(component=>{
    const area=data.territories.find(item=>item.id===component.territory_id),source=data.sources.find(item=>item.id===component.source_id);
    return {area,source,value:component.value,period:String(component.period),requested_period:String(period),indicator_id:indicatorId,scope:component.scope};
  });
}

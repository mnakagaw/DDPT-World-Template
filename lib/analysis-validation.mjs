import {boundaryIdentity,isDescendant,isTerminalTerritory,nationalSourceMatches,worldSeriesSourceMatches} from '../scaffold/site/analysis.mjs';
import {isPlanningLink} from './planning-validation.mjs';
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const text=value=>typeof value==='string' && value.trim().length>0;
const own=(value,key)=>object(value) && Object.prototype.hasOwnProperty.call(value,key);
const array=value=>Array.isArray(value)?value:[];
const iso=value=>typeof value==='string' && /^[A-Z0-9]{3}$/.test(value);
const finite=value=>typeof value==='number' && Number.isFinite(value);

/** Optional schema 0.2 analysis extension. Validation never proves source truth. */
export function validateAnalysis(data) {
  const errors=[],warnings=[],fail=message=>errors.push(message);
  if(!object(data))return {errors:['Analysis validation needs a dataset object'],warnings};
  const territories=new Map(array(data.territories).filter(object).map(area=>[area.id,area]));
  const sources=new Map(array(data.sources).filter(object).map(source=>[source.id,source]));
  const config=data.analysis,world=config?.kind==='world';
  const strings=(value,path,{nonempty=false}={})=>{
    if(!Array.isArray(value)){fail(`${path} must be an array of strings`);return [];}
    if(nonempty && !value.length)fail(`${path} must not be empty`);
    if(value.some(item=>!text(item)))fail(`${path} must contain nonempty strings`);
    const valid=value.filter(text);
    if(new Set(valid).size!==valid.length)fail(`${path} contains duplicate IDs`);
    return valid;
  };
  for(const area of territories.values()) {
    if(own(area,'country_id') && !iso(area.country_id))fail(`Territory ${area.id}.country_id must be a three-character country identifier`);
    if(world && area.type==='country' && !iso(area.country_id))fail(`World country territory ${area.id} needs explicit country_id`);
    if(area.country_id && area.type!=='country') {
      const seen=new Set([area.id]);let parent=territories.get(area.parent_id);
      while(parent && !seen.has(parent.id)) {
        seen.add(parent.id);
        if(parent.type==='country') {
          if(area.country_id!==(parent.country_id || data.country?.id))fail(`Territory ${area.id}.country_id disagrees with its country ancestor`);
          break;
        }
        parent=territories.get(parent.parent_id);
      }
    }
  }
  const countryIds=array(data.territories).filter(area=>area?.type==='country' && area.country_id).map(area=>area.country_id);
  if(new Set(countryIds).size!==countryIds.length)fail('Country territories must not duplicate country_id');
  for(const source of sources.values()) {
    if(own(source,'country_id') && !iso(source.country_id))fail(`Source ${source.id}.country_id must be a three-character country identifier`);
    if(world && source.geographic_level==='national' && !iso(source.country_id))fail(`National source ${source.id} in a world dataset needs explicit country_id`);
  }
  for(const observation of array(data.observations).filter(object)) {
    const source=sources.get(observation.source_id),area=territories.get(observation.territory_id);
    if(!nationalSourceMatches(data,source,area))fail(`National source ${observation.source_id} cannot supply this local or different-country observation ${observation.territory_id}`);
    if(observation.status==='observed' && !worldSeriesSourceMatches(data,source,area))fail(`World country series ${source.id} cannot supply a regional or local observation ${observation.territory_id}`);
  }
  // Metadata disagreement is valid evidence, but the runtime excludes it from colors/comparative results.
  for(const [label,items] of [['Indicator',data.indicators],['Observation',data.observations]])for(const row of array(items).filter(object)) {
    const id=row.id || `${row.territory_id}/${row.indicator_id}/${row.period}`;
    for(const key of ['definition_id','definition','unit','population','method','measurement_method'])if(own(row,key) && !text(row[key]))fail(`${label} ${id}.${key} must be a nonempty string`);
    if(own(row,'method') && own(row,'measurement_method') && row.method!==row.measurement_method)fail(`${label} ${id} method aliases disagree`);
    if(own(row,'boundary_version') && row.boundary_version!==null && !text(row.boundary_version))fail(`${label} ${id}.boundary_version must be a string or null`);
  }
  const boundaryIds=new Set();
  for(const feature of array(data.boundaries?.features)) {
    const id=feature?.properties?.territory_id,area=territories.get(id);
    if(!area)continue; // The base validator reports unknown IDs and invalid geometry.
    if(boundaryIds.has(id))fail(`Duplicate boundary territory ID ${id}; use one MultiPolygon feature`);
    boundaryIds.add(id);
    const identity=boundaryIdentity(feature,area);
    if(!identity.matches)fail(`Boundary ${id}: ${identity.reason}`);
    if(own(feature.properties,'source_id') && !sources.has(feature.properties.source_id))fail(`Boundary ${id} needs a registered source_id`);
  }
  if(config===undefined)return {errors,warnings};
  if(!object(config))return {errors:[...errors,'analysis must be an object'],warnings};
  if(!['world','regional','country'].includes(config.kind))fail('analysis.kind must be world, regional or country');
  if(world) {
    const root=territories.get(data.country?.national_territory_id);
    if(data.country?.id!=='WLD' || data.country?.national_territory_id!=='WLD' || root?.type!=='exploration_scope' || root?.level!=='national' || root?.parent_id!=null)fail('World analysis requires WLD metadata and a root WLD national exploration_scope');
  }
  for(const id of strings(config.terminal_territory_ids,'analysis.terminal_territory_ids'))if(!territories.has(id))fail(`Unknown terminal territory ${id}`);
  if(!Array.isArray(config.comparisons))fail('analysis.comparisons must be an array');
  const parents=new Set();
  for(const [index,item] of array(config.comparisons).entries()) {
    const path=`analysis.comparisons[${index}]`;
    if(!object(item)){fail(`${path} must be an object`);continue;}
    const parent=territories.get(item.parent_id);
    if(!text(item.parent_id) || !parent)fail(`${path} needs a known parent_id`);
    if(parents.has(item.parent_id))fail(`Duplicate comparison parent_id ${item.parent_id}`);
    parents.add(item.parent_id);
    if(parent && isTerminalTerritory(data,parent))fail(`${path} cannot compare children of a terminal territory`);
    for(const key of ['label','membership_note'])if(!text(item[key]))fail(`${path}.${key} must be a nonempty string`);
    const ids=strings(item.member_ids,`${path}.member_ids`,{nonempty:true});
    for(const id of ids) {
      if(!territories.has(id))fail(`${path} has unknown member ${id}`);
      else if(!isDescendant(data.territories,id,item.parent_id))fail(`${path} member ${id} must be a descendant of its parent`);
      if(ids.some(other=>other!==id && isDescendant(data.territories,id,other)))fail(`${path} has overlapping ancestor/descendant members`);
    }
    for(const id of strings(item.source_ids,`${path}.source_ids`,{nonempty:true})) {
      if(!sources.has(id))fail(`${path} has unknown membership source ${id}`);
      else if(!['ready','partial'].includes(sources.get(id).status))fail(`${path} membership source ${id} must have acquired usable evidence`);
    }
    if(own(item,'color_scale')) {
      const scale=item.color_scale;
      if(!object(scale)){fail(`${path}.color_scale must be an object`);continue;}
      if(!['within_selection','fixed'].includes(scale.mode))fail(`${path}.color_scale.mode must be within_selection or fixed`);
      if(own(scale,'label') && !text(scale.label))fail(`${path}.color_scale.label must be a nonempty string`);
      if(scale.mode==='fixed' || own(scale,'breaks')) {
        if(!Array.isArray(scale.breaks) || scale.breaks.length!==4 || scale.breaks.some((value,i)=>!finite(value) || i>0 && value<=scale.breaks[i-1]))fail(`${path}.color_scale.breaks must be four finite strictly ascending thresholds`);
        if(scale.mode==='within_selection')fail(`${path}.within_selection must not include fixed breaks`);
      }
    }
  }
  if(own(config,'aggregation')) {
    if(!object(config.aggregation))fail('analysis.aggregation must be an object');
    else {
      if(config.aggregation.policy!=='exact_then_complete_cover')fail('analysis.aggregation.policy must be exact_then_complete_cover');
      if(!Array.isArray(config.aggregation.rules))fail('analysis.aggregation.rules must be an array');
      const configured=new Set();
      for(const [index,rule] of array(config.aggregation.rules).entries()) {
        const path=`analysis.aggregation.rules[${index}]`;
        if(!object(rule)){fail(`${path} must be an object`);continue;}
        if(!text(rule.indicator_id) || !array(data.indicators).some(item=>item.id===rule.indicator_id))fail(`${path}.indicator_id must identify a known indicator`);
        if(configured.has(rule.indicator_id))fail(`${path} duplicates indicator ${rule.indicator_id}`);configured.add(rule.indicator_id);
        if(!['sum','ratio','weighted_mean'].includes(rule.method))fail(`${path}.method must be sum, ratio or weighted_mean`);
        if(rule.completeness!=='full_cover')fail(`${path}.completeness must be full_cover`);
        if(own(rule,'period_policy') && !['same_period','latest_available_by_component'].includes(rule.period_policy))fail(`${path}.period_policy must be same_period or latest_available_by_component`);
        if(!text(rule.label) || !text(rule.note))fail(`${path}.label and note must be nonempty strings`);
        if(rule.method==='sum' && data.indicators.find(item=>item.id===rule.indicator_id)?.aggregation!=='sum')fail(`${path} requires indicators[].aggregation=sum`);
        if(rule.method!=='sum')warnings.push(`${path} is declared but this runtime does not calculate it without its compatible component series; it remains unavailable.`);
      }
    }
  }
  if(own(config,'country_sites')) {
    if(!Array.isArray(config.country_sites))fail('analysis.country_sites must be an array');
    const linked=new Set();
    for(const [index,site] of array(config.country_sites).entries()) {
      const path=`analysis.country_sites[${index}]`;
      if(!object(site)){fail(`${path} must be an object`);continue;}
      const area=territories.get(site.territory_id);
      if(!area || area.type!=='country')fail(`${path}.territory_id must identify a country territory`);
      if(linked.has(site.territory_id))fail(`${path} has a duplicate country site`);
      linked.add(site.territory_id);
      if(!iso(site.country_id) || site.country_id!==area?.country_id)fail(`${path}.country_id must match the country territory`);
      if(!isPlanningLink(site.url))fail(`${path}.url must be safe HTTPS or a ./ child path`);
      if(own(site,'target_territory_id') && !text(site.target_territory_id))fail(`${path}.target_territory_id must be a nonempty string`);
      if(own(site,'indicator_map')) {
        if(!object(site.indicator_map) || Object.entries(site.indicator_map).some(([key,value])=>!text(key) || !text(value)))fail(`${path}.indicator_map must map nonempty indicator IDs to nonempty IDs`);
      }
    }
  }
  return {errors:[...new Set(errors)],warnings};
}

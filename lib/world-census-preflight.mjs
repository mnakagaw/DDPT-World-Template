import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';

export const KIT_WORLD_PREFLIGHT_COMMIT='6622118aa702a6f1d8eeaa84e1c5982a0fb954b5';
export const KIT_WORLD_PREFLIGHT_URL=`https://raw.githubusercontent.com/mnakagaw/Census-Dashboard-Kit/${KIT_WORLD_PREFLIGHT_COMMIT}/config/world-source-preflight.json`;
export const KIT_WORLD_PREFLIGHT_SHA256='448d4b5ec264191ae45dc1fc75a19c346b4dee5d8594ca86bb4f45f664846a95';
export const KIT_VALIDATION_URL=`https://github.com/mnakagaw/Census-Dashboard-Kit/blob/${KIT_WORLD_PREFLIGHT_COMMIT}/docs/VALIDATION_v1.8.1.md`;
export const BUNDLED_CENSUS_LISTINGS_URL=new URL('../data/census/world-census-listings-v1.8.1.json',import.meta.url);

const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const text=value=>typeof value==='string'&&value.trim().length>0;
const iso3=value=>typeof value==='string'&&/^[A-Z0-9]{3}$/.test(value);
const webUrl=value=>{try{return ['http:','https:'].includes(new URL(value).protocol);}catch{return false;}};
const sha256=value=>createHash('sha256').update(value).digest('hex');

function normalizeListing(value,{linked=false}={}){
  if(value==null)return null;
  if(!object(value)||!Number.isInteger(value.round)||!text(value.round_period)||!text(value.date_text)||!text(value.country_label))throw new Error('Invalid UNSD census listing');
  const links=Array.isArray(value.links)?value.links.filter(webUrl):[];
  const primaryUrl=webUrl(value.primary_url)?new URL(value.primary_url).href:null;
  if(linked&&(!primaryUrl||!links.length))throw new Error(`Linked UNSD census listing lacks a usable link: ${value.country_label}`);
  return {
    round:value.round,
    round_period:value.round_period,
    date_text:value.date_text,
    country_label:value.country_label,
    links,
    primary_url:primaryUrl,
    link_status:primaryUrl?'unsd_link_listed':'no_unsd_link_listed',
    acquisition_status:'not_acquired_by_preflight',
    content_verification_status:'not_verified_by_preflight',
    adoption_status:'not_adopted_by_preflight'
  };
}

export function validateKitWorldSourcePreflight(data){
  if(data?.schema_version!=='1.1'||!Array.isArray(data.records))throw new Error('Unsupported Census Dashboard Kit world-source-preflight schema');
  const ids=new Set();
  for(const record of data.records){
    if(!iso3(record?.iso3)||ids.has(record.iso3))throw new Error(`Duplicate or invalid Kit country identity: ${record?.iso3||'unknown'}`);
    ids.add(record.iso3);
    const census=record.national_statistics_and_census;
    if(!object(census)||!Object.hasOwn(census,'latest_un_census_listing')||!Object.hasOwn(census,'latest_un_census_linked_listing'))throw new Error(`${record.iso3}: Kit census listings are incomplete`);
    normalizeListing(census.latest_un_census_listing);
    normalizeListing(census.latest_un_census_linked_listing,{linked:true});
  }
  return data;
}

export function normalizeKitWorldSourcePreflight(data,{sourceSha256=null}={}){
  validateKitWorldSourcePreflight(data);
  const records=data.records.map(record=>{
    const census=record.national_statistics_and_census;
    return {
      country_id:record.iso3,
      iso2:record.iso2||null,
      m49:record.m49||null,
      name:record.name_en,
      checked_at:record.checked_at||data.as_of,
      national_statistics_office:object(census.national_statistics_office)?{
        agency:census.national_statistics_office.agency||null,
        url:webUrl(census.national_statistics_office.url)?new URL(census.national_statistics_office.url).href:null,
        origin:census.national_statistics_office.origin||null,
        authority_relation:census.national_statistics_office.authority_relation||null,
        scope_note:census.national_statistics_office.scope_note||null
      }:null,
      unsd_census_dates_source:webUrl(census.un_census_dates_source)?new URL(census.un_census_dates_source).href:null,
      latest_un_census_listing:normalizeListing(census.latest_un_census_listing),
      latest_un_census_linked_listing:normalizeListing(census.latest_un_census_linked_listing,{linked:true})
    };
  }).sort((a,b)=>a.country_id.localeCompare(b.country_id));
  return {
    schema_version:'1.0',
    checked_at:data.as_of,
    source:{
      repository:'https://github.com/mnakagaw/Census-Dashboard-Kit',
      commit:KIT_WORLD_PREFLIGHT_COMMIT,
      path:'config/world-source-preflight.json',
      raw_url:KIT_WORLD_PREFLIGHT_URL,
      sha256:sourceSha256||KIT_WORLD_PREFLIGHT_SHA256,
      validation_url:KIT_VALIDATION_URL
    },
    semantics:{
      latest_un_census_listing:data.census_listing_semantics.latest_un_census_listing,
      latest_un_census_linked_listing:data.census_listing_semantics.latest_un_census_linked_listing,
      evidence_rule:'A listing, link, acquired body, verified content and adopted observation are separate states. This registry adopts no census value.'
    },
    country_rules:{
      DZA:{
        adopted_census_data_year:2008,
        prohibited_unverified_census_data_years:[2022],
        note:'The UNSD 2020-round listing dated 25 September 2022 has no UNSD link. AreaData may use only separately acquired and verified 2008 census data until a newer source body is acquired, verified and explicitly approved.'
      }
    },
    records
  };
}

export function validateWorldCensusListings(registry){
  const errors=[];
  if(!object(registry)||registry.schema_version!=='1.0')return ['analysis.census_source_preflight must use schema_version 1.0'];
  if(registry.source?.commit!==KIT_WORLD_PREFLIGHT_COMMIT)errors.push('Census source preflight is not pinned to Census Dashboard Kit v1.8.1 commit');
  if(registry.source?.sha256!==KIT_WORLD_PREFLIGHT_SHA256)errors.push('Census source preflight source hash does not match the pinned Kit registry');
  const ids=new Set();
  for(const record of Array.isArray(registry.records)?registry.records:[]){
    if(!iso3(record?.country_id)||ids.has(record.country_id)){errors.push(`Duplicate or invalid census preflight country: ${record?.country_id||'unknown'}`);continue;}
    ids.add(record.country_id);
    const latest=record.latest_un_census_listing,linked=record.latest_un_census_linked_listing;
    if(linked&&(!webUrl(linked.primary_url)||linked.link_status!=='unsd_link_listed'))errors.push(`${record.country_id}: linked census listing needs its own UNSD link`);
    for(const listing of [latest,linked].filter(Boolean)){
      if(!Number.isInteger(listing.round)||!text(listing.date_text))errors.push(`${record.country_id}: census listing needs round and date_text`);
      if(listing.acquisition_status!=='not_acquired_by_preflight'||listing.content_verification_status!=='not_verified_by_preflight'||listing.adoption_status!=='not_adopted_by_preflight')errors.push(`${record.country_id}: census listing states must remain distinct`);
    }
  }
  return errors;
}

export function attachWorldCensusListings(dataset,registry){
  const errors=validateWorldCensusListings(registry);if(errors.length)throw new Error(errors.join('; '));
  const countryIds=new Set((dataset.territories||[]).filter(area=>area.type==='country'&&iso3(area.country_id||area.id)).map(area=>area.country_id||area.id));
  if(!countryIds.size&&iso3(dataset.country?.id)&&!['WLD','AMR','CAM'].includes(dataset.country.id))countryIds.add(dataset.country.id);
  const records=registry.records.filter(record=>countryIds.has(record.country_id));
  const missing=[...countryIds].filter(id=>!records.some(record=>record.country_id===id));
  const matched=[...countryIds].filter(id=>records.some(record=>record.country_id===id)).sort();
  const result=structuredClone(dataset);result.analysis=result.analysis||{kind:'country',terminal_territory_ids:[],comparisons:[],country_sites:[]};
  result.analysis.census_source_preflight={...structuredClone(registry),records,requested_country_ids:[...countryIds].sort(),scope_country_ids:matched,missing_country_ids:missing.sort()};
  result.collection=result.collection||{status:'partial',adapters:[],notes:[]};
  result.collection.adapters=[...new Set([...(result.collection.adapters||[]),'census-dashboard-kit-world-source-preflight-v1.8.1'])];
  result.collection.notes=[...(result.collection.notes||[]),'UNSD latest completed listing and latest linked listing remain separate discovery metadata. Neither a listing nor a link is evidence of acquisition, verification or adoption.'];
  return result;
}

export function validateWorldCensusListingsAgainstDataset(dataset){
  const registry=dataset.analysis?.census_source_preflight;if(!registry)return [];
  const errors=validateWorldCensusListings(registry),records=new Map((registry.records||[]).map(record=>[record.country_id,record]));
  for(const id of registry.scope_country_ids||[])if(!records.has(id))errors.push(`Census source preflight is missing in-scope country ${id}`);
  const dza=records.get('DZA');
  if(dza){
    const latest=dza.latest_un_census_listing,linked=dza.latest_un_census_linked_listing;
    if(latest?.round!==2020||latest?.date_text!=='25 September 2022'||latest?.primary_url!==null)errors.push('DZA latest UNSD listing must remain 2020 round / 25 September 2022 / no UNSD link');
    if(linked?.round!==2010||linked?.date_text!=='16-30 April 2008'||linked?.primary_url!=='http://rgph2008.ons.dz/')errors.push('DZA linked listing must remain 2010 round / 16-30 April 2008 / rgph2008.ons.dz');
    const censusIds=new Set((dataset.indicators||[]).filter(indicator=>indicator.series_family==='census').map(indicator=>indicator.id));
    const dzaTerritories=new Set((dataset.territories||[]).filter(area=>(area.country_id||dataset.country?.id)==='DZA').map(area=>area.id));
    for(const row of dataset.observations||[]){
      if(dzaTerritories.has(row.territory_id)&&censusIds.has(row.indicator_id)&&Number.parseInt(String(row.period),10)>2008)errors.push(`DZA census observation ${row.territory_id}/${row.indicator_id}/${row.period} exceeds the adopted 2008 source year`);
    }
    const history=(dataset.analysis?.census_history?.countries||[]).find(row=>row.country_id==='DZA');
    if(history&&history.adopted_data_year!==2008)errors.push('DZA census history adopted_data_year must remain 2008');
  }
  return [...new Set(errors)];
}

export async function loadBundledWorldCensusListings(){
  return JSON.parse(await readFile(BUNDLED_CENSUS_LISTINGS_URL,'utf8'));
}

export async function importKitWorldSourcePreflight(bytes){
  const content=Buffer.isBuffer(bytes)?bytes:Buffer.from(bytes),actual=sha256(content);
  if(actual!==KIT_WORLD_PREFLIGHT_SHA256)throw new Error(`Pinned Kit registry hash mismatch: ${actual}`);
  return normalizeKitWorldSourcePreflight(JSON.parse(content.toString('utf8')),{sourceSha256:actual});
}

import {readFile} from 'node:fs/promises';

const list=value=>Array.isArray(value)?value:[];
const isHttps=value=>{try{return new URL(value).protocol==='https:';}catch{return false;}};

export async function loadCensusHistory(file){
  return validateCensusHistory(JSON.parse(await readFile(file,'utf8')));
}

export function validateCensusHistory(data){
  if(data?.schema_version!=='1.0'||!data.scope_id)throw new Error('Unsupported census history catalog');
  if(!Number.isInteger(data.as_of_year))throw new Error('Census history needs an integer as_of_year');
  const countries=list(data.countries),ids=new Set();
  if(!countries.length)throw new Error('Census history has no countries');
  for(const country of countries){
    if(!country.country_id||ids.has(country.country_id))throw new Error(`Duplicate or missing census history country: ${country.country_id||'unknown'}`);
    ids.add(country.country_id);
    if(!Number.isInteger(country.adopted_data_year)||country.adopted_data_year>data.as_of_year)throw new Error(`Invalid adopted census year: ${country.country_id}`);
    if(!isHttps(country.adopted_source_url)||!isHttps(country.official_census_url))throw new Error(`Census history needs official HTTPS links: ${country.country_id}`);
    const rounds=list(country.recent_rounds);
    if(!rounds.length||rounds.length>3)throw new Error(`Census history needs one to three recent rounds: ${country.country_id}`);
    const years=rounds.map(round=>round.year);
    if(years.some(year=>!Number.isInteger(year)||year>data.as_of_year)||new Set(years).size!==years.length)throw new Error(`Invalid census round years: ${country.country_id}`);
    if(years.some((year,index)=>index&&year>=years[index-1]))throw new Error(`Census round years must be newest first: ${country.country_id}`);
    if(rounds.some(round=>!round.status||!isHttps(round.url)))throw new Error(`Census rounds need a status and official HTTPS link: ${country.country_id}`);
    if(!rounds.some(round=>round.year===country.adopted_data_year))throw new Error(`Adopted year must appear in recent rounds: ${country.country_id}`);
    if(country.upcoming&&(!Number.isInteger(country.upcoming.year)||!country.upcoming.status||!isHttps(country.upcoming.url)))throw new Error(`Invalid upcoming census record: ${country.country_id}`);
  }
  return data;
}

export function mergeCensusHistory(dataset,history,referenceBoundaries={type:'FeatureCollection',features:[]}){
  validateCensusHistory(history);
  const result=structuredClone(dataset),pilotIds=result.analysis?.pilot?.country_ids||[],historyIds=history.countries.map(country=>country.country_id);
  if(history.scope_id!==result.country.national_territory_id)throw new Error('Census history scope does not match the dataset');
  if(pilotIds.some(id=>!historyIds.includes(id))||historyIds.some(id=>!pilotIds.includes(id)))throw new Error('Census history must cover the exact pilot country set');
  for(const country of history.countries){
    const adopted=result.observations.find(row=>row.territory_id===country.country_id&&row.indicator_id==='CENSUS_POP_TOTAL'&&String(row.period)===String(country.adopted_data_year)&&row.status==='observed');
    if(!adopted)throw new Error(`Census history adopted year has no active country observation: ${country.country_id} ${country.adopted_data_year}`);
  }
  result.analysis.census_history={schema_version:history.schema_version,as_of_year:history.as_of_year,checked_at:history.checked_at,countries:structuredClone(history.countries),reference_boundaries:structuredClone(referenceBoundaries)};
  result.collection.adapters.push('official-census-round-history-v1');
  result.collection.notes.push(`Census recency colors use the adopted AreaData data year as of ${history.as_of_year}. Conducted, planned or reported rounds without integrated results remain separate records.`);
  return result;
}

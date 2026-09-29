#!/usr/bin/env node
// Adopt the PSA 2024 POPCEN web extract without joining outdated ADM1 shapes.
import {readFile,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const dataPath=join(project,'data','dashboard.json');
const raw=join(project,'raw');
const extractPath=join(raw,'psa-psgc-regions-2025-extraction.json');
const excerptPath=join(raw,'psa-psgc-regions-2025-web-excerpt.txt');
const domesticPath=join(raw,'psa-2024-popcen-domestic-web-excerpt.txt');
const nationalPath=join(raw,'psa-2024-popcen-national-web-excerpt.txt');
const cityPath=join(raw,'psa-psgc-iloilo-city-web-excerpt.txt');
const provincePath=join(raw,'psa-psgc-provinces-2026-web-excerpt.txt');
const provinceExtractPath=join(raw,'psa-psgc-provinces-2026-extraction.json');
const citiesPath=join(raw,'psa-psgc-cities-2025-web-excerpt.txt');
const citiesExtractPath=join(raw,'psa-psgc-cities-2025-extraction.json');
const municipalitiesPath=join(raw,'psa-psgc-municipalities-2025-web-excerpt.txt');
const municipalitiesExtractPath=join(raw,'psa-psgc-municipalities-2025-extraction.json');
const cityTypesPath=join(raw,'psa-psgc-city-types-2025-web-excerpt.txt');
const cityTypesExtractPath=join(raw,'psa-psgc-city-types-2025-extraction.json');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const sourceFile=async path=>{const bytes=await readFile(path);return {sha256:sha(bytes),bytes:bytes.length}};
const [extractText,excerpt,domestic,national,city,provinceExcerpt,provinceExtractText,
  citiesExcerpt,citiesExtractText,municipalitiesExcerpt,municipalitiesExtractText,
  cityTypesExcerpt,cityTypesExtractText,dataText]=await Promise.all([
  readFile(extractPath,'utf8'),readFile(excerptPath,'utf8'),readFile(domesticPath,'utf8'),
  readFile(nationalPath,'utf8'),readFile(cityPath,'utf8'),readFile(provincePath,'utf8'),
  readFile(provinceExtractPath,'utf8'),readFile(citiesPath,'utf8'),readFile(citiesExtractPath,'utf8'),
  readFile(municipalitiesPath,'utf8'),readFile(municipalitiesExtractPath,'utf8'),
  readFile(cityTypesPath,'utf8'),readFile(cityTypesExtractPath,'utf8'),readFile(dataPath,'utf8')
]);
const extract=JSON.parse(extractText),provinceExtract=JSON.parse(provinceExtractText),data=JSON.parse(dataText);
const citiesExtract=JSON.parse(citiesExtractText);
const municipalitiesExtract=JSON.parse(municipalitiesExtractText);
const cityTypesExtract=JSON.parse(cityTypesExtractText);
if(data.country?.id!=='PHL')throw Error('Expected PHL project');
if(extract.rows.length!==18 || new Set(extract.rows.map(r=>r.code)).size!==18)throw Error('PSGC region count/code uniqueness failed');
for(const row of extract.rows){
  if(!/^\d{10}$/.test(row.code)||!Number.isInteger(row.population)||row.population<=0)throw Error('Invalid PSGC code/population');
  const name=row.name.replace(/[.*+?^$\{\}()|[\]\\]/g,'\\$&');
  const match=excerpt.match(new RegExp(name+'\\s+\\|\\s+10 Digit Code:\\s*\\n'+row.code+'\\s+\\| Correspondence Code:[\\s\\S]*?\\(2024 POPCEN\\)\\s+\\|\\s+'+row.population));
  if(!match)throw Error('Extracted row not reproduced in saved web excerpt: '+row.code);
}
const regionalTotal=extract.rows.reduce((sum,row)=>sum+row.population,0);
if(provinceExtract.source_url!=='https://psa.gov.ph/classification/psgc/provinces' ||
   provinceExtract.rows.length!==82 || new Set(provinceExtract.rows.map(r=>r.code)).size!==82)
  throw Error('PSGC province source/count/code uniqueness failed');
const provinceLines=provinceExcerpt.split(/\r?\n/);
for(const row of provinceExtract.rows){
  if(!/^\d{10}$/.test(row.code)||!Number.isInteger(row.population)||row.population<=0||
     !extract.rows.some(region=>region.code===row.code.slice(0,2)+'00000000'))
    throw Error('Invalid PSGC province row: '+row.code);
  const found=provinceLines.some(line=>{
    const parts=line.split('|').map(part=>part.trim());
    return parts.length===5 && parts[0].includes('†'+row.name+'') &&
      parts[1]===row.code && parts[2]===(row.correspondence_code||'') &&
      Number(parts[4])===row.population;
  });
  if(!found)throw Error('Province row absent from official rendered excerpt: '+row.code);
}
if(provinceExtract.rows.reduce((sum,row)=>sum+row.population,0)!==88375900)
  throw Error('PSGC province checksum total changed; review the source edition');
const localSources=[
  {rows:citiesExtract.rows,excerpt:citiesExcerpt,count:149,url:'https://psa.gov.ph/classification/psgc/cities'},
  {rows:municipalitiesExtract.rows,excerpt:municipalitiesExcerpt,count:1493,url:'https://psa.gov.ph/classification/psgc/municipalities'}
];
for(const source of localSources){
  if(source.rows.length!==source.count || !source.excerpt.includes(source.url) ||
     new Set(source.rows.map(row=>row.code)).size!==source.count)
    throw Error('PSGC city/municipality source count or code uniqueness failed: '+source.url);
  const lines=source.excerpt.split(/\r?\n/);
  for(const row of source.rows){
    if(!/^\d{10}$/.test(row.code) || !Number.isInteger(row.population) || row.population<=0)
      throw Error('Invalid PSGC city/municipality row: '+row.code);
    const found=lines.some(line=>{
      const parts=line.split('|').map(part=>part.trim());
      return parts.length===5 && parts[0].includes('†'+row.name+'') &&
        parts[1]===row.code && parts[2]===(row.correspondence_code||'') &&
        parts[3]===row.income_class && Number(parts[4])===row.population;
    });
    if(!found)throw Error('Local row absent from official rendered excerpt: '+row.code);
  }
}
const cityCodes=new Set(citiesExtract.rows.map(row=>row.code));
const localCodes=new Set([...cityCodes,...municipalitiesExtract.rows.map(row=>row.code)]);
if(localCodes.size!==1642 || !cityCodes.has('0631000000'))
  throw Error('PSGC local code inventory is incomplete');
const cityTypes=cityTypesExtract.codes;
const cityTypeSets=Object.fromEntries(Object.entries(cityTypes).map(([kind,codes])=>[kind,new Set(codes)]));
if(cityTypes.huc.length!==33 || cityTypes.icc.length!==5 || cityTypes.cc.length!==111 ||
   new Set([...cityTypes.huc,...cityTypes.icc,...cityTypes.cc]).size!==149 ||
   ![...cityCodes].every(code=>Object.values(cityTypeSets).some(set=>set.has(code))))
  throw Error('PSGC city-type categories do not partition all cities');
for(const [kind,codes] of Object.entries(cityTypes)){
  if(!cityTypesExcerpt.includes(cityTypesExtract.sources[kind]) ||
     !codes.every(code=>cityTypesExcerpt.includes(' | '+code+' ')))
    throw Error('PSGC city-type source excerpt mismatch: '+kind);
}
const allLocalRows=[...citiesExtract.rows,...municipalitiesExtract.rows];
if(allLocalRows.reduce((sum,row)=>sum+row.population,0)!==regionalTotal)
  throw Error('All city/municipality populations do not reconcile to domestic population');
for(const region of extract.rows){
  const sum=allLocalRows.filter(row=>row.code.slice(0,2)===region.code.slice(0,2))
    .reduce((total,row)=>total+row.population,0);
  if(sum!==region.population)throw Error('PSGC local population does not reconcile to region '+region.code);
}
const provincePrefixSet=new Set(provinceExtract.rows.map(row=>row.code.slice(0,5)));
const provinceChildren=row=>allLocalRows.filter(local=>
  local.code.slice(0,5)===row.code.slice(0,5) && !cityTypeSets.huc.has(local.code));
for(const province of provinceExtract.rows){
  const sum=provinceChildren(province).reduce((total,row)=>total+row.population,0);
  if(sum!==province.population)throw Error('PSGC local population does not reconcile to province '+province.code);
}
if(regionalTotal!==112727776||extract.national_published!==112729484||
   extract.national_published-regionalTotal!==1708||
   !domestic.includes('112,727,776')||!domestic.includes('1,708')||
   !national.includes('112,729,484')||
   !city.includes('0631000000')||!city.includes('473728')){
  throw Error('PSA national/region/city reconciliation failed');
}
const prefix='PHL:PSGC:';
const regionIds=extract.rows.map(row=>prefix+row.code);
data.territories=data.territories.filter(t=>t.id==='PHL' && t.type==='country');
data.territories.push(...extract.rows.map(row=>({
  id:prefix+row.code,name:row.name,level:'region',type:'region',parent_id:'PHL',
  official_code:row.code,code_system:'PSGC 10-digit',code_edition:'2025-07-31',
  boundary_version:null,source_id:'psa-psgc-2025-regions',
  reconciliation_status:'official_code_and_population_verified_polygon_unavailable'
})));
data.territories.push(...provinceExtract.rows.map(row=>({
  id:prefix+row.code,name:row.name,level:'province',type:'province',
  parent_id:prefix+row.code.slice(0,2)+'00000000',
  official_code:row.code,correspondence_code:row.correspondence_code,
  code_system:'PSGC 10-digit',code_edition:'undated PSA province table; captured 2026-09-29',
  boundary_version:null,source_id:'psa-psgc-2026-provinces',
  reconciliation_status:'official_code_and_population_verified_polygon_unavailable'
})));
const parentId=row=>{
  const provincePrefix=row.code.slice(0,5);
  return cityTypeSets.huc.has(row.code) || !provincePrefixSet.has(provincePrefix)
    ? prefix+row.code.slice(0,2)+'00000000'
    : prefix+provincePrefix+'00000';
};
data.territories.push(...allLocalRows.map(row=>{
  const city=cityCodes.has(row.code);
  const cityType=city ? Object.entries(cityTypeSets).find(([,codes])=>codes.has(row.code))?.[0] : null;
  return {
    id:prefix+row.code,name:row.name,level:city?'city':'municipality',type:city?'city':'municipality',
    parent_id:parentId(row),official_code:row.code,
    correspondence_code:row.correspondence_code,code_system:'PSGC 10-digit',
    code_edition:'2025-07-31',boundary_version:null,
    city_classification:cityType,
    statistical_parent_note:cityType==='icc'
      ? 'Provincial 2024 POPCEN table includes this independent component city; its city government remains a separate planning authority.'
      : null,
    source_id:city?'psa-psgc-2025-cities':'psa-psgc-2025-municipalities',
    reconciliation_status:'official_code_and_population_verified_polygon_unavailable'
  };
}));
data.boundaries={type:'FeatureCollection',features:[]};
data.indicators=data.indicators.filter(i=>!i.id.startsWith('PHL_POPCEN_2024_'));
data.indicators.push(
  {id:'PHL_POPCEN_2024_DOMESTIC',name:'2024 census population in the Philippines',
   theme:'Population',unit:'people',
   definition:'Persons enumerated within the 18 Philippine regions as of 1 July 2024; excludes 1,708 Filipinos in Philippine embassies, consulates and missions abroad.',
   source_id:'psa-popcen-2024-domestic',aggregation:'none',measurement_method:'source_reported',
   population:'persons in Philippine regions',metadata_status:'ready',
   display_role:'primary',series_family:'census'},
  {id:'PHL_POPCEN_2024_TOTAL',name:'2024 census population including missions abroad',
   theme:'Population',unit:'people',
   definition:'Official Philippine population as of 1 July 2024, including 1,708 Filipinos in Philippine embassies, consulates and missions abroad.',
   source_id:'psa-popcen-2024-national',aggregation:'none',measurement_method:'source_reported',
   population:'Philippines including missions abroad',metadata_status:'ready'}
);
data.observations=data.observations.filter(o=>!o.indicator_id.startsWith('PHL_POPCEN_2024_'));
const observed=(territory_id,indicator_id,value,source_id)=>({
  territory_id,indicator_id,period:'2024',value,status:'observed',source_id,
  reference_date:'2024-07-01'
});
data.observations.push(
  observed('PHL','PHL_POPCEN_2024_DOMESTIC',regionalTotal,'psa-popcen-2024-domestic'),
  observed('PHL','PHL_POPCEN_2024_TOTAL',extract.national_published,'psa-popcen-2024-national'),
  ...extract.rows.map(row=>observed(prefix+row.code,'PHL_POPCEN_2024_DOMESTIC',row.population,'psa-psgc-2025-regions')),
  ...provinceExtract.rows.map(row=>observed(prefix+row.code,'PHL_POPCEN_2024_DOMESTIC',row.population,'psa-psgc-2026-provinces')),
  ...citiesExtract.rows.map(row=>observed(prefix+row.code,'PHL_POPCEN_2024_DOMESTIC',row.population,'psa-psgc-2025-cities')),
  ...municipalitiesExtract.rows.map(row=>observed(prefix+row.code,'PHL_POPCEN_2024_DOMESTIC',row.population,'psa-psgc-2025-municipalities'))
);
const adoptedSourceIds=new Set(['psa-psgc-2025-regions','psa-popcen-2024-domestic',
  'psa-popcen-2024-national','psa-psgc-2025-iloilo-city','psa-psgc-2026-provinces',
  'psa-psgc-2025-cities','psa-psgc-2025-municipalities','psa-psgc-2025-city-types','official-gazette-ra-7160',
  'iloilo-city-cdp-2023-2028']);
data.sources=data.sources.filter(s=>!adoptedSourceIds.has(s.id));
const checkedAt=new Date().toISOString();
data.sources.push(
  {id:'psa-psgc-2025-regions',name:'PSA PSGC Regions and 2024 POPCEN',publisher:'Philippine Statistics Authority',
   url:extract.source_url,reference_period:'PSGC as of 31 July 2025; POPCEN 1 July 2024',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-regions-2025-web-excerpt.txt',
   ...await sourceFile(excerptPath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'Rendered-text capture from web.run; original HTML/XLSX direct download blocked. Region values reconcile to official domestic count. No current polygon acquired.'},
  {id:'psa-popcen-2024-domestic',name:'PSA 2024 POPCEN domestic population',publisher:'Philippine Statistics Authority',
   url:'https://psa.gov.ph/statistics/population-and-housing/node/1684081344',
   reference_period:'1 July 2024',status:'ready',retrieved_at:checkedAt,
   raw_path:'raw/psa-2024-popcen-domestic-web-excerpt.txt',...await sourceFile(domesticPath),
   license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'Indexed official excerpt; no raw origin HTML. Domestic count excludes 1,708 Filipinos in missions abroad.'},
  {id:'psa-popcen-2024-national',name:'PSA 2024 POPCEN official national total',publisher:'Philippine Statistics Authority',
   url:'https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president',
   reference_period:'1 July 2024',status:'ready',retrieved_at:checkedAt,
   raw_path:'raw/psa-2024-popcen-national-web-excerpt.txt',...await sourceFile(nationalPath),
   license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'Rendered official press-release excerpt; total includes missions abroad.'},
  {id:'psa-psgc-2025-iloilo-city',name:'PSA PSGC City of Iloilo and 2024 POPCEN',publisher:'Philippine Statistics Authority',
   url:'https://psa.gov.ph/classification/psgc/barangays/0631000000',
   reference_period:'PSGC as of 31 July 2025; POPCEN 1 July 2024',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-iloilo-city-web-excerpt.txt',
   ...await sourceFile(cityPath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'One city planning case only; Region VI city coverage is incomplete.'},
  {id:'psa-psgc-2026-provinces',name:'PSA PSGC provinces and 2024 POPCEN',publisher:'Philippine Statistics Authority',
   url:provinceExtract.source_url,reference_period:'PSGC provinces page checked 29 September 2026; POPCEN 1 July 2024',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-provinces-2026-web-excerpt.txt',
   ...await sourceFile(provincePath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'82 coded province rows from official rendered web excerpt; original HTML/masterlist unavailable. Provinces do not include all independent HUCs, so their sums must not replace region observations.'},
  {id:'psa-psgc-2025-cities',name:'PSA PSGC 149 cities and 2024 POPCEN',publisher:'Philippine Statistics Authority',
   url:citiesExtract.source_url,reference_period:'PSGC as of 31 July 2025; POPCEN 1 July 2024',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-cities-2025-web-excerpt.txt',
   ...await sourceFile(citiesPath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'All 149 coded city rows from official rendered web text. Original HTML/masterlist unavailable. City classification is a separate official source.'},
  {id:'psa-psgc-2025-municipalities',name:'PSA PSGC 1,493 municipalities and 2024 POPCEN',publisher:'Philippine Statistics Authority',
   url:municipalitiesExtract.source_url,reference_period:'PSGC as of 31 July 2025; POPCEN 1 July 2024',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-municipalities-2025-web-excerpt.txt',
   ...await sourceFile(municipalitiesPath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'All 1,493 coded municipality rows from official rendered web text, including eight BARMM Special Geographic Area municipalities. Original HTML/masterlist unavailable.'},
  {id:'psa-psgc-2025-city-types',name:'PSA PSGC city classifications',publisher:'Philippine Statistics Authority',
   url:cityTypesExtract.sources.huc,reference_period:'PSGC as of 31 July 2025',
   status:'ready',retrieved_at:checkedAt,raw_path:'raw/psa-psgc-city-types-2025-web-excerpt.txt',
   ...await sourceFile(cityTypesPath),license:'CC BY 4.0 unless otherwise stated (PSA site footer)',
   note:'Official HUC, ICC and CC lists classify all 149 cities as 33, 5 and 111 respectively; source URLs for all three are retained in raw extraction.'},
  {id:'official-gazette-ra-7160',name:'Local Government Code of 1991, sections 106 and 109',
   publisher:'Official Gazette of the Republic of the Philippines',
   url:'https://officialgazette.gov.ph/1991/10/10/republic-act-no-7160/',
   reference_period:'1991 law; current amendment effect not fully audited',status:'partial',
   retrieved_at:checkedAt,note:'Official legal text location verified; law and current amendments require full legal review.'},
  {id:'iloilo-city-cdp-2023-2028',name:'Iloilo City Comprehensive Development Plan 2023-2028',
   publisher:'Iloilo City Government',
   url:'https://iloilocity.gov.ph/main/wp-content/uploads/2023/05/CDP2023-2028_4-13_Final-Document.pdf',
   reference_period:'2023-2028',status:'partial',retrieved_at:checkedAt,
   note:'Official URL indexed but direct PDF acquisition returned HTTP 403. Plan body, approval, budget and evaluation are not adopted.'}
);
data.documents=data.documents.filter(d=>!d.id.startsWith('phl-'));
data.documents.push({
  id:'phl-iloilo-cdp-link',territory_id:prefix+'0631000000',category:'plan',
  title:'Iloilo City Comprehensive Development Plan 2023-2028 (official link)',
  kind:'plan',url:'https://iloilocity.gov.ph/main/wp-content/uploads/2023/05/CDP2023-2028_4-13_Final-Document.pdf',
  period:'2023-2028',target_period:{label:'2023-2028',kind:'multi_year'},
  availability:'link_verified',official_status:'unverified',source_id:'iloilo-city-cdp-2023-2028',
  territory_match:{territory_id:prefix+'0631000000',country_id:'PHL',type:'city',
    code_system:'PSGC 10-digit',official_code:'0631000000',boundary_version:null,
    method:'PSA names City of Iloilo with PSGC code 0631000000; official city-domain PDF title identifies the same city.',
    source_id:'iloilo-city-cdp-2023-2028',locator:'Official URL/title and PSA PSGC city record',checked_at:checkedAt}
});
data.planning={
  title:'Planning materials and links',
  purpose:'Locate materials for the selected Philippine area. A linked plan is not a verified plan body or proof of approval. Budget, spending and evaluation are shown only when separately verified.',
  sections:[
    {id:'plan',label:'Development plans'},
    {id:'budget',label:'Budgets and spending'},
    {id:'implementation',label:'Implementation reports'},
    {id:'evaluation',label:'Published evaluations'}
  ],
  outputs:['markdown','html','evidence_csv','documents_csv'],
  map:{mode:'coverage'},
  update:{status:'stopped',checked_at:checkedAt,last_success_at:checkedAt,
    message:'Fixed 29 September 2026 source review; no ongoing document monitor is configured.'}
};
const childIds=new Map();
for(const territory of data.territories){
  if(territory.parent_id){
    if(!childIds.has(territory.parent_id))childIds.set(territory.parent_id,[]);
    childIds.get(territory.parent_id).push(territory.id);
  }
}
const popById=new Map(data.observations.filter(row=>row.indicator_id==='PHL_POPCEN_2024_DOMESTIC')
  .map(row=>[row.territory_id,row.value]));
for(const [parentId,members] of childIds){
  const parent=popById.get(parentId);
  const sum=members.reduce((total,id)=>total+(popById.get(id)||0),0);
  if(parent!==sum)throw Error('Adopted hierarchy fails complete 2024 POPCEN coverage for '+parentId);
}
const comparisons=[...childIds].filter(([,members])=>members.length>1).map(([parent_id,member_ids])=>({
  parent_id,member_ids,
  label:parent_id==='PHL'?'2024 POPCEN by 18 PSGC regions':
    parent_id.endsWith('00000000')?'Provinces and independent local areas within the region':'Cities and municipalities within the province',
  membership_note:'Complete non-overlapping 2024 POPCEN reporting hierarchy assembled from PSA PSGC region and local tables dated 31 July 2025 and an undated province table captured 29 September 2026. A single common PSGC edition is not verified. ICCs are included in PSA province population tables while remaining separate city planning authorities; HUCs and province-free areas report directly under their regions.',
  source_ids:['psa-psgc-2025-regions','psa-psgc-2026-provinces','psa-psgc-2025-cities','psa-psgc-2025-municipalities','psa-psgc-2025-city-types'],
  color_scale:{mode:'within_selection'}
}));
data.analysis={...data.analysis,kind:'country',
  incomplete_child_cover_ids:[],
  terminal_territory_ids:allLocalRows.map(row=>prefix+row.code),
  comparisons};
data.country.geography_note='2024 POPCEN counts cover 18 regions, 82 provinces, 149 cities and 1,493 municipalities. The PSA region and local pages state 31 July 2025; the province rows were captured 29 September 2026 without an explicit table edition. A single common PSGC edition has not been verified. All 1,642 city/municipality counts reconcile to the 112,727,776 domestic population. ICCs are included in province census totals but are separate planning authorities; HUCs and areas without a province report directly under regions. No current official polygons are joined. Initial 2020 geoBoundaries ADM1 shapes remain private raw references only.';
data.collection.status='partial';
data.collection.adapters=[...new Set([...data.collection.adapters,'psa-psgc-2025-regions-web-extract'])];
data.collection.adapters=[...new Set([...data.collection.adapters,'psa-psgc-2026-provinces-web-extract'])];
data.collection.adapters=[...new Set([...data.collection.adapters,'psa-psgc-2025-local-web-extract'])];
const addedNotes=['Official PSA 2024 POPCEN region, province and all city/municipality counts adopted from saved rendered-text excerpts; original HTML/XLSX and full thematic catalogue audit remain open.',
  'Current region polygons and plans for all but the Iloilo City link are not acquired. Iloilo City PDF body is not acquired.'];
data.collection.notes=[...new Set([...data.collection.notes,...addedNotes])];
for(const gap of data.gaps){
  if(gap.category==='subnational_statistics'){
    gap.status='partial';
    gap.detail='2024 POPCEN population is observed for 18 regions, 82 provinces, 149 cities and 1,493 municipalities; other local themes are not collected.';
    delete gap.description;
    gap.next_action='Acquire official local census and sector tables, then audit every value and code before adding observations.';
  }
  if(gap.category==='planning_documents'){
    gap.status='partial';
    gap.detail='One City of Iloilo CDP location is linked, but its PDF body, approval, budget, spending and evaluation were not acquired.';
    delete gap.description;
    gap.next_action='Acquire the official plan and distinct investment, budget, spending and evaluation originals for matched authorities.';
  }
}
data.gaps=data.gaps.filter(g=>g.id!=='phl-current-polygon-and-local-cover');
data.gaps.push({
  id:'phl-current-polygon-and-local-cover',category:'geography',
  detail:'The rendered 31 July 2025 PSGC region/city/municipality tables and an undated province table captured 29 September 2026 reconcile arithmetically to 2024 POPCEN counts; a single common code edition and current polygons are not verified. 2020 provider ADM1 geometry is not used for these counts.',
  status:'partial',next_action:'Acquire dated authoritative current boundary and original PSGC/POPCEN Table B, then verify geometry and NIR/Sulu geographic joins.'
});
await writeFile(dataPath,JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify({project,territories:data.territories.length,regional_sum:regionalTotal,
  observations:data.observations.length,psa_population_rows:extract.rows.length+provinceExtract.rows.length+allLocalRows.length+2,
  boundaries:data.boundaries.features.length,documents:data.documents.length},null,2));

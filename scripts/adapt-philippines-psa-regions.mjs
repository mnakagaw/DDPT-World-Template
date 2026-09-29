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
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const sourceFile=async path=>{const bytes=await readFile(path);return {sha256:sha(bytes),bytes:bytes.length}};
const [extractText,excerpt,domestic,national,city,dataText]=await Promise.all([
  readFile(extractPath,'utf8'),readFile(excerptPath,'utf8'),readFile(domesticPath,'utf8'),
  readFile(nationalPath,'utf8'),readFile(cityPath,'utf8'),readFile(dataPath,'utf8')
]);
const extract=JSON.parse(extractText),data=JSON.parse(dataText);
if(data.country?.id!=='PHL')throw Error('Expected PHL project');
if(extract.rows.length!==18 || new Set(extract.rows.map(r=>r.code)).size!==18)throw Error('PSGC region count/code uniqueness failed');
for(const row of extract.rows){
  if(!/^\d{10}$/.test(row.code)||!Number.isInteger(row.population)||row.population<=0)throw Error('Invalid PSGC code/population');
  const name=row.name.replace(/[.*+?^$\{\}()|[\]\\]/g,'\\$&');
  const match=excerpt.match(new RegExp(name+'\\s+\\|\\s+10 Digit Code:\\s*\\n'+row.code+'\\s+\\| Correspondence Code:[\\s\\S]*?\\(2024 POPCEN\\)\\s+\\|\\s+'+row.population));
  if(!match)throw Error('Extracted row not reproduced in saved web excerpt: '+row.code);
}
const regionalTotal=extract.rows.reduce((sum,row)=>sum+row.population,0);
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
data.territories.push({
  id:prefix+'0631000000',name:'City of Iloilo',level:'city',type:'city',
  parent_id:prefix+'0600000000',official_code:'0631000000',
  correspondence_code:'063022000',code_system:'PSGC 10-digit',code_edition:'2025-07-31',
  boundary_version:null,source_id:'psa-psgc-2025-iloilo-city',
  reconciliation_status:'official_code_and_population_verified_polygon_unavailable'
});
data.boundaries={type:'FeatureCollection',features:[]};
data.indicators=data.indicators.filter(i=>!i.id.startsWith('PHL_POPCEN_2024_'));
data.indicators.push(
  {id:'PHL_POPCEN_2024_DOMESTIC',name:'2024 census population in the Philippines',
   theme:'Population',unit:'people',
   definition:'Persons enumerated within the 18 Philippine regions as of 1 July 2024; excludes 1,708 Filipinos in Philippine embassies, consulates and missions abroad.',
   source_id:'psa-popcen-2024-domestic',aggregation:'none',measurement_method:'source_reported',
   population:'persons in Philippine regions',metadata_status:'ready'},
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
  observed(prefix+'0631000000','PHL_POPCEN_2024_DOMESTIC',473728,'psa-psgc-2025-iloilo-city')
);
const adoptedSourceIds=new Set(['psa-psgc-2025-regions','psa-popcen-2024-domestic',
  'psa-popcen-2024-national','psa-psgc-2025-iloilo-city','official-gazette-ra-7160',
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
data.analysis={...data.analysis,kind:'country',
  incomplete_child_cover_ids:[prefix+'0600000000'],
  comparisons:[{parent_id:'PHL',member_ids:regionIds,
    label:'2024 POPCEN by 18 PSGC regions',
    membership_note:'All 18 regions in the PSA PSGC register of 31 July 2025. Regional sum excludes 1,708 persons in missions abroad.',
    source_ids:['psa-psgc-2025-regions'],color_scale:{mode:'within_selection'}}]};
data.country.geography_note='2024 POPCEN values use PSA PSGC 18-region register (31 July 2025). No current official polygons are joined. Initial 2020 geoBoundaries ADM1 shapes remain private raw references only. Iloilo City is a single planning case, not complete city coverage.';
data.collection.status='partial';
data.collection.adapters=[...new Set([...data.collection.adapters,'psa-psgc-2025-regions-web-extract'])];
const addedNotes=['Official PSA 2024 POPCEN regional counts adopted from saved rendered-text excerpts; XLSX origin and full catalogue audit remain open.',
  'Current region polygons and complete province/city/municipality planning authorities are not acquired. Iloilo City PDF is link-only.'];
data.collection.notes=[...new Set([...data.collection.notes,...addedNotes])];
data.gaps=data.gaps.filter(g=>g.id!=='phl-current-polygon-and-local-cover');
data.gaps.push({
  id:'phl-current-polygon-and-local-cover',category:'geography',
  description:'Current 18-region polygons and complete province/city/municipality PSGC hierarchy are not joined; 2020 provider ADM1 geometry is not used for current counts.',
  status:'open',next_action:'Acquire dated authoritative current boundary and full PSGC/POPCEN Table B, then reconcile NIR and Sulu reassignment.'
});
await writeFile(dataPath,JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify({project,territories:data.territories.length,regional_sum:regionalTotal,
  observations:data.observations.length,psa_population_rows:extract.rows.length+3,
  boundaries:data.boundaries.features.length,documents:data.documents.length},null,2));

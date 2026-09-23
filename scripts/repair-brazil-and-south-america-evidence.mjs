#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const arg=name=>{const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;};
const project=path.resolve(arg('--project')||'');
if(!project)throw new Error('--project is required');
const evidenceDir=path.join(project,'evidence');
const dataPath=path.join(project,'data','dashboard.json');
const rawBra=path.join(project,'raw','south-america','BRA');
await mkdir(rawBra,{recursive:true});

const shaBuffer=buffer=>createHash('sha256').update(buffer).digest('hex');
const shaFile=async file=>shaBuffer(await readFile(file));
const rel=file=>path.relative(project,file).replaceAll('\\','/');
const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const sidraNumber=value=>value==='-'?0:(Number.isFinite(Number(value))?Number(value):null);
const fetchJson=async url=>{
  const response=await fetch(url,{signal:AbortSignal.timeout(60000),headers:{'user-agent':'AreaData source audit/0.10 (+https://areadata.net/)','accept':'application/json'}});
  if(!response.ok)throw new Error(`${url}: HTTP ${response.status}`);
  return {body:Buffer.from(await response.arrayBuffer()),finalUrl:response.url};
};

const specs=[
  {table:6326,variable:1000381,classification:'125[6815]',denominatorVariable:381,denominatorClassification:'125[2932]',indicator:'BRA_C2022_HOUSE_PCT',theme:'households_housing',uiTheme:'Housing',name:'Occupied permanent private dwellings that are houses',unit:'%',population:'Occupied permanent private dwellings',definition:'Share of occupied permanent private dwellings classified as a house.',category:'Tipo de domicílio: Casa'},
  {table:6803,variable:1000381,classification:'1821[72144]',denominatorVariable:381,denominatorClassification:'1821[72129]',indicator:'BRA_C2022_MAIN_WATER_NETWORK_PCT',theme:'drinking_water',uiTheme:'Basic services',name:'Dwellings using the general water network as the main source',unit:'%',population:'Occupied permanent private dwellings',definition:'Share of occupied permanent private dwellings connected to the general distribution network and using it as the main water source.',category:'Ligação à rede geral e uso como forma principal'},
  {table:6805,variable:1000381,classification:'11558[46290]',denominatorVariable:381,denominatorClassification:'11558[46292]',indicator:'BRA_C2022_SEWER_NETWORK_PCT',theme:'sanitation',uiTheme:'Basic services',name:'Dwellings with sewerage connected to a network',unit:'%',population:'Occupied permanent private dwellings',definition:'Share of occupied permanent private dwellings using the general sewer network, storm-water network, or a septic/filter system connected to a network.',category:'Rede geral, rede pluvial ou fossa ligada à rede'},
  {table:9605,variable:1000093,classification:'86[2777]',denominatorVariable:93,denominatorClassification:'86[95251]',indicator:'BRA_C2022_BLACK_PCT',theme:'ethnicity',uiTheme:'Population',name:'Population identifying as Black',unit:'%',population:'Resident population',definition:'Share of the resident population recorded in the source category Preta (Black).',category:'Cor ou raça: Preta'},
  {table:9543,variable:2513,classification:'2[6794]|86[95251]|287[100362]',indicator:'BRA_C2022_LITERACY_15PLUS_PCT',theme:'education_literacy',uiTheme:'Education',name:'Literacy rate, age 15 and over',unit:'%',population:'People aged 15 years and over',definition:'Literacy rate among people aged 15 years and over, both sexes and all race/colour groups.',category:'Sexo total; cor ou raça total; idade total'},
  {table:10125,variable:13403,classification:'2[6794]|58[95253]',denominatorVariable:11852,denominatorClassification:'2[6794]|58[95253]',indicator:'BRA_C2022_DISABILITY_2PLUS_PCT',theme:'disability',uiTheme:'Population',name:'People age 2 and over with a disability',unit:'%',population:'People aged 2 years and over',definition:'Share of people aged 2 years and over recorded as having a disability.',category:'Sexo total; grupo de idade total'},
  {table:9923,variable:1000093,classification:'1[1]',denominatorVariable:93,denominatorClassification:'1[6795]',indicator:'BRA_C2022_URBAN_PCT',theme:'urban_rural',uiTheme:'Population',name:'Urban population',unit:'%',population:'Resident population',definition:'Share of the resident population living in areas classified as urban.',category:'Situação do domicílio: Urbana'},
  {table:9517,variable:1001641,classification:'629[32387]|2[6794]|86[95251]|1568[120704]',denominatorVariable:1641,denominatorClassification:'629[32385]|2[6794]|86[95251]|1568[120704]',indicator:'BRA_C2022_EMPLOYED_14PLUS_PCT',theme:'employment',uiTheme:'Economy',name:'Employed population, age 14 and over',unit:'%',population:'People aged 14 years and over',definition:'Share of people aged 14 years and over who were employed in the reference week.',category:'Força de trabalho ocupada; sexo/cor ou raça/instrução total'},
  {table:10158,variable:13338,classification:'305[77807]|3014[95320]',indicator:'BRA_C2022_RECENT_MUNICIPAL_MIGRANTS',theme:'migration',uiTheme:'Population',name:'Residents with less than 10 uninterrupted years in the municipality',unit:'people',population:'People who had lived in the municipality for less than 10 uninterrupted years',definition:'Source-reported count of people who had lived continuously in their municipality for less than 10 years.',category:'Tempo total; lugar de residência anterior total'},
];

const [dataset,preflight,inventory,countryReceipt]=await Promise.all([
  readFile(dataPath,'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
  readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),
  readFile(path.join(project,'raw','country-source-pages','receipt.json'),'utf8').then(JSON.parse),
]);

const stateCodeToIso={11:'RO',12:'AC',13:'AM',14:'RR',15:'PA',16:'AP',17:'TO',21:'MA',22:'PI',23:'CE',24:'RN',25:'PB',26:'PE',27:'AL',28:'SE',29:'BA',31:'MG',32:'ES',33:'RJ',35:'SP',41:'PR',42:'SC',43:'RS',50:'MS',51:'MT',52:'GO',53:'DF'};
const braTerritories=new Map(dataset.territories.filter(row=>row.country_id==='BRA').map(row=>[row.official_code?.split('-')[1],row]));
const territoryIdSet=new Set(dataset.territories.map(row=>row.id));
const acquired=[];
for(const spec of specs){
  const classification=spec.classification.split('|').map(part=>part.match(/^(\d+)\[(\d+)\]$/)).map(match=>({id:match[1],category:match[2]}));
  const query=classification.map(item=>`${item.id}[${item.category}]`).join('|');
  const metadataUrl=`https://servicodados.ibge.gov.br/api/v3/agregados/${spec.table}/metadados`;
  const dataUrl=`https://servicodados.ibge.gov.br/api/v3/agregados/${spec.table}/periodos/2022/variaveis/${spec.variable}?localidades=N3[all]&classificacao=${query}`;
  const municipalityUrl=`https://servicodados.ibge.gov.br/api/v3/agregados/${spec.table}/periodos/2022/variaveis/${spec.variable}?localidades=N6[all]&classificacao=${query}&view=flat`;
  const denominatorUrl=spec.denominatorVariable?`https://servicodados.ibge.gov.br/api/v3/agregados/${spec.table}/periodos/2022/variaveis/${spec.denominatorVariable}?localidades=N6[all]&classificacao=${spec.denominatorClassification}&view=flat`:null;
  const [metadataResult,dataResult,municipalityResult,denominatorResult]=await Promise.all([fetchJson(metadataUrl),fetchJson(dataUrl),fetchJson(municipalityUrl),denominatorUrl?fetchJson(denominatorUrl):Promise.resolve(null)]);
  const metadataPath=path.join(rawBra,`ibge-sidra-${spec.table}-metadata.json`),rawPath=path.join(rawBra,`ibge-sidra-${spec.table}-states.json`);
  const municipalityPath=path.join(rawBra,`ibge-sidra-${spec.table}-municipalities.json`),denominatorPath=denominatorResult?path.join(rawBra,`ibge-sidra-${spec.table}-municipality-denominators.json`):null;
  await Promise.all([writeFile(metadataPath,metadataResult.body),writeFile(rawPath,dataResult.body),writeFile(municipalityPath,municipalityResult.body),denominatorResult?writeFile(denominatorPath,denominatorResult.body):Promise.resolve()]);
  const metadata=JSON.parse(metadataResult.body.toString('utf8')),payload=JSON.parse(dataResult.body.toString('utf8'));
  const rows=(payload||[]).flatMap(variable=>(variable.resultados||[]).flatMap(result=>result.series||[]));
  const observations=[];
  for(const row of rows){
    const territory=braTerritories.get(stateCodeToIso[Number(row.localidade?.id)]);
    const value=sidraNumber(row.serie?.['2022']);
    if(!territory||value===null)continue;
    observations.push({territory_id:territory.id,indicator_id:spec.indicator,period:'2022',value,status:'observed',source_id:'bra-census-2022',definition:spec.definition,definition_id:spec.indicator,unit:spec.unit,population:spec.population,measurement_method:'source_reported',source_locator:`SIDRA table ${spec.table}; variable ${spec.variable}; ${spec.category}; N3 Unidade da Federação`});
  }
  if(observations.length!==27)throw new Error(`${spec.indicator}: expected 27 state observations, received ${observations.length}`);
  const denominatorByCode=new Map((denominatorResult?JSON.parse(denominatorResult.body.toString('utf8')):[]).slice(1).map(row=>[String(row.D1C),sidraNumber(row.V)]).filter(([,value])=>value!==null));
  const municipalityRows=JSON.parse(municipalityResult.body.toString('utf8')).slice(1);
  for(const row of municipalityRows){
    const code=String(row.D1C||''),state=braTerritories.get(stateCodeToIso[Number(code.slice(0,2))]),value=sidraNumber(row.V);
    if(!state||value===null)continue;
    const territoryId=`BRA:C2022:MUN:${code}`;
    if(!territoryIdSet.has(territoryId)){dataset.territories.push({id:territoryId,country_id:'BRA',name:row.D1N,level:'municipality',type:'municipality',parent_id:state.id,official_code:code,code_system:'IBGE municipality code',boundary_version:'Census 2022 statistical geography; geometry not acquired in this repair',geography_note:'Official IBGE municipality code and state parent. No polygon is claimed until a matching IBGE boundary edition is acquired.'});territoryIdSet.add(territoryId);}
    observations.push({territory_id:territoryId,indicator_id:spec.indicator,period:'2022',value,status:'observed',source_id:'bra-census-2022',definition:spec.definition,definition_id:spec.indicator,unit:spec.unit,population:spec.population,measurement_method:'source_reported',source_locator:`SIDRA table ${spec.table}; variable ${spec.variable}; ${spec.category}; N6 Município`,denominator_value:denominatorByCode.get(code)??null,denominator_definition:spec.denominatorVariable?`SIDRA table ${spec.table}; variable ${spec.denominatorVariable}; ${spec.denominatorClassification}`:null});
  }
  const municipalityCount=new Set(observations.filter(row=>row.territory_id.includes(':MUN:')).map(row=>row.territory_id)).size;
  if(municipalityCount<5560)throw new Error(`${spec.indicator}: expected national municipality coverage, received ${municipalityCount}`);
  const indicator={id:spec.indicator,name:spec.name,theme:spec.uiTheme,unit:spec.unit,definition:spec.definition,definition_id:spec.indicator,population:spec.population,measurement_method:'source_reported',aggregation:spec.unit==='people'?'sum':'none',period_policy:'fixed_source_period',series_family:'census',display_role:'primary',source_id:'bra-census-2022',source_locator:`SIDRA table ${spec.table}; variable ${spec.variable}; ${spec.category}; N3 Unidade da Federação`};
  dataset.indicators=[...dataset.indicators.filter(row=>row.id!==spec.indicator),indicator];
  dataset.observations=[...dataset.observations.filter(row=>row.indicator_id!==spec.indicator),...observations];
  dataset.analysis.default_period_by_indicator={...(dataset.analysis.default_period_by_indicator||{}),[spec.indicator]:'2022'};
  const metadataSha=shaBuffer(metadataResult.body),dataSha=shaBuffer(dataResult.body),municipalitySha=shaBuffer(municipalityResult.body),denominatorSha=denominatorResult?shaBuffer(denominatorResult.body):null;
  acquired.push({table_id:String(spec.table),table_title:metadata.nome,indicator_id:spec.indicator,theme:spec.theme,variable_id:String(spec.variable),classification_locator:spec.category,geography:`N3 Unidade da Federação (27) and N6 Município (${municipalityCount})`,source_url:`https://sidra.ibge.gov.br/tabela/${spec.table}`,api_url:dataResult.finalUrl,municipality_api_url:municipalityResult.finalUrl,denominator_api_url:denominatorResult?.finalUrl||null,metadata_path:rel(metadataPath),metadata_sha256:metadataSha,data_path:rel(rawPath),data_sha256:dataSha,bytes:dataResult.body.length,municipality_path:rel(municipalityPath),municipality_sha256:municipalitySha,municipality_bytes:municipalityResult.body.length,denominator_path:denominatorPath?rel(denominatorPath):null,denominator_sha256:denominatorSha,denominator_bytes:denominatorResult?.body.length||null,observation_count:observations.length,municipality_count:municipalityCount,geography_match:'IBGE state code mapped explicitly to ISO 3166-2 state suffix; seven-digit official municipality code mapped to its two-digit state prefix and an explicit BRA ADM1 parent',disposition:'integrated'});
}

const braMunicipalities=dataset.territories.filter(row=>row.country_id==='BRA'&&row.level==='municipality');
const braStateIds=new Set(dataset.territories.filter(row=>row.country_id==='BRA'&&row.level==='adm1').map(row=>row.id));
dataset.analysis.terminal_territory_ids=[...new Set([...(dataset.analysis.terminal_territory_ids||[]).filter(id=>!braStateIds.has(id)),...braMunicipalities.map(row=>row.id)])];
dataset.analysis.comparisons=[...(dataset.analysis.comparisons||[]).filter(row=>!braStateIds.has(row.parent_id)),...dataset.territories.filter(row=>braStateIds.has(row.id)).map(state=>({parent_id:state.id,member_ids:braMunicipalities.filter(row=>row.parent_id===state.id).map(row=>row.id),label:`${state.name} municipalities`,membership_note:'Official IBGE municipality codes grouped by their state prefix. Values remain source-reported; municipalities without a published value stay explicit missing.',source_ids:['bra-census-2022']}))];

const braSource=dataset.sources.find(row=>row.id==='bra-census-2022');
if(!braSource)throw new Error('bra-census-2022 source is missing');
braSource.url='https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html';
braSource.catalog_url='https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022';
braSource.retrieved_at=new Date().toISOString();
braSource.raw_files=acquired.flatMap(row=>[
  {raw_path:row.metadata_path,sha256:row.metadata_sha256,url:`https://servicodados.ibge.gov.br/api/v3/agregados/${row.table_id}/metadados`,kind:'official_api_metadata'},
  {raw_path:row.data_path,sha256:row.data_sha256,url:row.api_url,bytes:row.bytes,kind:'official_api_observations'},
  {raw_path:row.municipality_path,sha256:row.municipality_sha256,url:row.municipality_api_url,bytes:row.municipality_bytes,kind:'official_api_municipality_observations'},
  ...(row.denominator_path?[{raw_path:row.denominator_path,sha256:row.denominator_sha256,url:row.denominator_api_url,bytes:row.denominator_bytes,kind:'official_api_municipality_denominators'}]:[]),
]);
braSource.note='Official IBGE Census 2022 SIDRA tables. Each adopted indicator retains the table, variable, selected categories, geographic level, raw response hash, and explicit state-code crosswalk.';

const repairedThemes=new Set(specs.map(row=>row.theme));
inventory.records=(inventory.records||[]).filter(row=>!(row.country_area_id==='BRA'&&repairedThemes.has(row.theme)&&row.disposition!=='integrated'));
for(const row of acquired)inventory.records.push({country_area_id:'BRA',source_id:'bra-census-2022',source_path:row.municipality_path,source_url:row.source_url,table_id:row.table_id,table_title:row.table_title,field_id:row.indicator_id,field_label:dataset.indicators.find(x=>x.id===row.indicator_id)?.name,numeric_cell_count:row.observation_count,theme:row.theme,disposition:'integrated',reason:`Official IBGE SIDRA 2022 values are integrated for all 27 N3 state/Federal District units and ${row.municipality_count} N6 municipalities. Locator: variable ${row.variable_id}; ${row.classification_locator}.`,indicator_id:row.indicator_id,coverage_complete:true,country_edition_eligible:true,evidence:[{path:row.data_path,sha256:row.data_sha256,bytes:row.bytes,api_url:row.api_url,locator:`table ${row.table_id}; variable ${row.variable_id}; ${row.classification_locator}; N3`,geography_match:row.geography_match},{path:row.municipality_path,sha256:row.municipality_sha256,bytes:row.municipality_bytes,api_url:row.municipality_api_url,locator:`table ${row.table_id}; variable ${row.variable_id}; ${row.classification_locator}; N6`,geography_match:row.geography_match},...(row.denominator_path?[{path:row.denominator_path,sha256:row.denominator_sha256,bytes:row.denominator_bytes,api_url:row.denominator_api_url,locator:`table ${row.table_id}; denominator variable ${specs.find(x=>x.indicator===row.indicator_id)?.denominatorVariable}; ${specs.find(x=>x.indicator===row.indicator_id)?.denominatorClassification}; N6`}]:[])]});
inventory.record_count=inventory.records.length;
inventory.generated_at=new Date().toISOString();
inventory.adjudication={...(inventory.adjudication||{}),BRA:{reviewed_numeric_fields:acquired.length,terminal_dispositions:inventory.records.filter(row=>row.country_area_id==='BRA').length,covered_themes:[...new Set(inventory.records.filter(row=>row.country_area_id==='BRA'&&row.disposition==='integrated').map(row=>row.theme))].sort(),method:'Official IBGE SIDRA tables are acquired through the v3 API; table metadata, selected variable/category, raw response hash and state-code crosswalk are retained.',audit:'evidence/BRA_SOURCE_REPAIR_AUDIT.json'}};

const targetIds=new Set(['BOL','BRA','COL','ECU','FLK','GUY','PRY','PER','SUR','URY','VEN']);
const receiptRows=countryReceipt.receipts||[];
const evidenceObject=async(file,{sourceUrl,locator,disposition='inspected',geographyMatch=null}={})=>{
  const full=path.join(project,file),s=await stat(full),receipt=file.endsWith('.receipt.json')?JSON.parse(await readFile(full,'utf8')):null;
  return {object_path:file,object_sha256:await shaFile(full),object_bytes:s.size,upstream_sha256:receipt?.upstream_sha256||null,upstream_bytes:receipt?.bytes||null,source_url:sourceUrl||receipt?.source_url||null,locator,disposition,geography_match:geographyMatch};
};
const firstAcquired=(id,domain)=>receiptRows.find(row=>row.country_area_id===id&&row.domain===domain&&row.status==='acquired'&&row.path);
const sourceEvidenceByCountry={};
for(const id of targetIds){
  const sourceIds=[...new Set(dataset.observations.filter(row=>(row.territory_id===id||row.territory_id.startsWith(`${id}:`))&&!String(row.source_id).startsWith('wb-')&&!String(row.source_id).startsWith('un-wpp')).map(row=>row.source_id))];
  const source=dataset.sources.find(row=>sourceIds.includes(row.id));
  if(!source?.raw_path)continue;
  sourceEvidenceByCountry[id]=await evidenceObject(source.raw_path,{sourceUrl:source.url,locator:`${source.id}; ${dataset.observations.find(row=>row.source_id===source.id)?.source_locator||'source-attributed adopted observation'}; adopted indicator IDs: ${[...new Set(dataset.observations.filter(row=>row.source_id===source.id).map(row=>row.indicator_id))].join(', ')}`,disposition:'integrated',geographyMatch:`Observed values are linked to explicit ${id} territory IDs; see evidence/GEOGRAPHY_CROSSWALK.csv and the source-specific integration audit.`});
}
const boundaryEvidenceByCountry={};
for(const id of targetIds){
  const dir=path.join(project,'raw','south-america',id);
  const file=`raw/south-america/${id}/${id}-adm1.geojson.receipt.json`;
  try{boundaryEvidenceByCountry[id]=await evidenceObject(file,{locator:`geoBoundaries ${id} ADM1 API receipt; upstream payload hash and byte count retained`,disposition:'adopted',geographyMatch:`Features adopted only where explicitly joined to ${id} territory IDs.`});}catch{}
}
const repairedDomains=[];
for(const country of preflight.countries||[]){
  if(!targetIds.has(country.country_area_id))continue;
  const id=country.country_area_id,integrated=sourceEvidenceByCountry[id],boundary=boundaryEvidenceByCountry[id];
  for(const key of ['official_statistics_office','latest_census','census_results','table_catalog','machine_readable_data','administrative_codes','adm1_adm2_boundaries','planning_law','planning_guidance','plans_budgets_implementation_evaluation']){
    const domain=country[key]; if(!domain)continue;
    let evidence=[];
    const acquiredReceipt=firstAcquired(id,key);
    if(acquiredReceipt)evidence.push(await evidenceObject(acquiredReceipt.path,{sourceUrl:acquiredReceipt.url,locator:`Acquired ${key} object from the recorded official URL. This proves only the content of this object, not an entire national catalog.`,disposition:'inspected'}));
    if(['latest_census','census_results','table_catalog','machine_readable_data'].includes(key)&&integrated)evidence.push(integrated);
    if(key==='administrative_codes'&&integrated)evidence.push({...integrated,locator:`${integrated.locator}; explicit territory IDs and source-to-AreaData geography match`});
    if(key==='adm1_adm2_boundaries'&&boundary)evidence.push(boundary);
    if(id==='BRA'&&['latest_census','census_results','table_catalog','machine_readable_data'].includes(key))evidence.push(...acquired.map(row=>({object_path:row.municipality_path,object_sha256:row.municipality_sha256,object_bytes:row.municipality_bytes,source_url:row.source_url,api_url:row.municipality_api_url,locator:`SIDRA table ${row.table_id}; variable ${row.variable_id}; ${row.classification_locator}; N6 Município`,denominator_object_path:row.denominator_path,denominator_sha256:row.denominator_sha256,denominator_locator:row.denominator_path?`SIDRA table ${row.table_id}; denominator variable ${specs.find(x=>x.indicator===row.indicator_id)?.denominatorVariable}; ${specs.find(x=>x.indicator===row.indicator_id)?.denominatorClassification}; N6 Município`:null,disposition:'integrated',geography_match:row.geography_match})));
    const verified=evidence.length>0&&key!=='plans_budgets_implementation_evaluation';
    domain.evidence=evidence;
    domain.completion_verified=verified;
    if(!verified){
      domain.adopted=false;domain.geography_matched=false;domain.inspected=false;domain.acquired=false;
      domain.status=domain.urls?.length?'accessed':'identified';
      domain.note=`${domain.note||''} Completion is not verified: no acquired domain-specific object with hash and exact locator is currently retained. An inspected start URL is not treated as an integrated plan, budget, implementation report, evaluation, guidance, or data product.`.trim();
    }
    repairedDomains.push({country_area_id:id,domain:key,completion_verified:verified,evidence_count:evidence.length,status:domain.status});
  }
  country.country_adapter_status=id==='BRA'?'broad_local_edition_11_integrated_themes':'source_review_reopened_evidence_bound';
}
preflight.generated_at=new Date().toISOString();
preflight.summary={...(preflight.summary||{}),integrated_country_adapters:(preflight.countries||[]).filter(row=>String(row.country_adapter_status||'').includes('broad_local_edition')||String(row.country_adapter_status||'').startsWith('integrated_')).length,evidence_repair_note:'Completion flags are now conditional on retained acquired objects with hashes and locators for the eleven re-audited South America entries; planning start URLs alone are not complete.'};

dataset.generated_at=new Date().toISOString();
dataset.collection.notes=[...new Set([...(dataset.collection.notes||[]),'Brazil Census 2022: nine additional IBGE SIDRA themes are integrated at N3 state/Federal District level with raw API responses, metadata and explicit code matching.'])];
const validation=validateDataset(dataset);
if(validation.errors.length)throw new Error(validation.errors.join('; '));
const content=JSON.stringify(dataset)+'\n',datasetSha=shaBuffer(Buffer.from(content));
await Promise.all([
  writeFile(dataPath,content),
  writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
  writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),
  writeFile(path.join(evidenceDir,'BRA_SOURCE_REPAIR_AUDIT.json'),JSON.stringify({schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'BRA',source:'IBGE Censo Demográfico 2022 / SIDRA official v3 API',dataset_sha256:datasetSha,integrated_theme_count:acquired.length,integrated_tables:acquired,validation},null,2)+'\n'),
  writeFile(path.join(evidenceDir,'SOUTH_AMERICA_SOURCE_DOMAIN_REPAIR.json'),JSON.stringify({schema_version:'1.0',generated_at:new Date().toISOString(),dataset_sha256:datasetSha,country_area_ids:[...targetIds],rule:'completion_verified is true only when evidence contains a retained acquired object with SHA-256 and an exact locator. The combined planning domain remains incomplete until actual plan/budget/implementation/evaluation documents are acquired and classified.',domains:repairedDomains},null,2)+'\n'),
]);
await generateSite({dataset,outDir:project});
console.log(JSON.stringify({dataset_sha256:datasetSha,brazil_integrated_theme_count:new Set(inventory.records.filter(row=>row.country_area_id==='BRA'&&row.disposition==='integrated'&&row.country_edition_eligible===true).map(row=>row.theme)).size,brazil_added_indicators:specs.length,repaired_domain_rows:repairedDomains.length,completion_verified_without_evidence:repairedDomains.filter(row=>row.completion_verified&&row.evidence_count===0).length,validation_errors:validation.errors},null,2));

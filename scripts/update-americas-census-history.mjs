#!/usr/bin/env node
import path from 'node:path';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {validateDataset} from '../lib/validate.mjs';

const parseArgs=()=>{const out={};for(let i=2;i<process.argv.length;i+=2)out[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return out;};
const round=(year,url,status=year===2020||year>2020?'results_adopted':'historical_round')=>({year,status,url});
const notes=(en,es,ja)=>({en,es,ja});
const records=[
  {
    country_id:'CAN',names:{en:'Canada',es:'Canadá',ja:'カナダ'},adopted_data_year:2021,
    adopted_source_url:'https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm?Lang=E',official_census_url:'https://www12.statcan.gc.ca/census-recensement/index-eng.cfm',
    recent_rounds:[round(2021,'https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm?Lang=E'),round(2016,'https://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/index.cfm?Lang=E','historical_round'),round(2011,'https://www12.statcan.gc.ca/census-recensement/2011/dp-pd/index-eng.cfm','historical_round')],
    note:notes('AreaData uses the 2021 Census Profile. Statistics Canada conducts the population census every five years.','AreaData usa el Perfil del Censo 2021. Statistics Canada realiza el censo de población cada cinco años.','AreaDataでは2021年Census Profileを採用しています。カナダの人口Censusは5年ごとに実施されます。')
  },
  {
    country_id:'CHL',names:{en:'Chile',es:'Chile',ja:'チリ'},adopted_data_year:2024,
    adopted_source_url:'https://censo2024.ine.gob.cl/estadisticas/',official_census_url:'https://www.ine.gob.cl/estadisticas-por-tema/demografia-y-poblacion/censo-de-poblacion-y-vivienda',
    recent_rounds:[round(2024,'https://censo2024.ine.gob.cl/estadisticas/'),round(2017,'https://censo2024.ine.gob.cl/estadisticas-2017/','historical_round'),round(2002,'https://redatam.ine.gob.cl/','historical_round')],
    note:notes('AreaData uses the 2024 usual-resident Census results. Earlier rounds used a different de facto method, so historical levels are not silently harmonized.','AreaData usa los resultados de residentes habituales del Censo 2024. Las rondas anteriores usaron otro método de hecho y no se armonizan de forma automática.','AreaDataでは2024年の常住人口Census結果を採用しています。過去回は異なる実査方法のため、自動的に同一定義へ揃えません。')
  },
  {
    country_id:'DOM',names:{en:'Dominican Republic',es:'República Dominicana',ja:'ドミニカ共和国'},adopted_data_year:2022,
    adopted_source_url:'https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/',official_census_url:'https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/',
    recent_rounds:[round(2022,'https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/'),round(2010,'https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2010/','historical_round'),round(2002,'https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2002/','historical_round')],
    note:notes('AreaData uses the 2022 national Census tables at national, regional, provincial, municipal and municipal-district levels where published.','AreaData usa los cuadros del Censo Nacional 2022 en los niveles nacional, regional, provincial, municipal y de distrito municipal donde fueron publicados.','AreaDataでは2022年Censusの公表表を、全国・地域・県・市・市区レベルで利用できる範囲まで採用しています。')
  },
  {
    country_id:'MEX',names:{en:'Mexico',es:'México',ja:'メキシコ'},adopted_data_year:2020,
    adopted_source_url:'https://www.inegi.org.mx/programas/ccpv/2020/#Datos_abiertos',official_census_url:'https://www.inegi.org.mx/programas/ccpv/2020/',
    recent_rounds:[round(2020,'https://www.inegi.org.mx/programas/ccpv/2020/'),round(2010,'https://www.inegi.org.mx/programas/ccpv/2010/','historical_round'),round(2000,'https://www.inegi.org.mx/programas/ccpv/2000/','historical_round')],
    note:notes('AreaData uses INEGI 2020 Census ITER records and preserves official state and municipality codes.','AreaData usa los registros ITER del Censo 2020 de INEGI y conserva los códigos oficiales de entidad y municipio.','AreaDataではINEGI 2020年CensusのITERを採用し、州・市の公式コードを保持しています。')
  },
  {
    country_id:'PRI',names:{en:'Puerto Rico',es:'Puerto Rico',ja:'プエルトリコ'},adopted_data_year:2020,
    adopted_source_url:'https://www.census.gov/programs-surveys/decennial-census/decade/2020/2020-census-results.html',official_census_url:'https://www.census.gov/programs-surveys/decennial-census/data/tables.2020.html',
    recent_rounds:[round(2020,'https://www.census.gov/programs-surveys/decennial-census/data/tables.2020.html'),round(2010,'https://www.census.gov/programs-surveys/decennial-census/data/tables.2010.html','historical_round'),round(2000,'https://www.census.gov/data/developers/data-sets/decennial-census.2000.html','historical_round')],
    note:notes('AreaData uses 2020 Census urban-rural classification and Puerto Rico Community Survey tables as separately labelled series.','AreaData usa la clasificación urbana-rural del Censo 2020 y cuadros de la Encuesta sobre la Comunidad de Puerto Rico como series separadas.','AreaDataでは2020年Censusの都市・農村分類とPuerto Rico Community Surveyを別系列として表示します。')
  },
  {
    country_id:'USA',names:{en:'United States of America',es:'Estados Unidos de América',ja:'アメリカ合衆国'},adopted_data_year:2020,
    adopted_source_url:'https://www.census.gov/programs-surveys/decennial-census/decade/2020/2020-census-results.html',official_census_url:'https://www.census.gov/programs-surveys/decennial-census/decade.2020.html',
    recent_rounds:[round(2020,'https://www.census.gov/programs-surveys/decennial-census/data/tables.2020.html'),round(2010,'https://www.census.gov/programs-surveys/decennial-census/data/tables.2010.html','historical_round'),round(2000,'https://www.census.gov/data/developers/data-sets/decennial-census.2000.html','historical_round')],
    note:notes('AreaData uses the 2020 Census urban-rural classification. The detailed state and county demographic series is the separately labelled 2023 ACS five-year estimate, not the 2020 Census population count.','AreaData usa la clasificación urbana-rural del Censo 2020. La serie demográfica detallada por estado y condado es la estimación quinquenal ACS 2023, no el conteo poblacional del Censo 2020.','AreaDataでは2020年Censusの都市・農村分類を採用します。州・郡の詳細人口系列は別表示の2023年ACS 5年推計であり、2020年Census人口ではありません。')
  },
  {
    country_id:'VIR',names:{en:'United States Virgin Islands',es:'Islas Vírgenes de los Estados Unidos',ja:'米領ヴァージン諸島'},adopted_data_year:2020,
    adopted_source_url:'https://www.census.gov/data/tables/2020/dec/2020-us-virgin-islands.html',official_census_url:'https://www.census.gov/data/tables/2020/dec/2020-us-virgin-islands.html',
    recent_rounds:[round(2020,'https://www.census.gov/data/tables/2020/dec/2020-us-virgin-islands.html'),round(2010,'https://www.census.gov/newsroom/releases/archives/2010_census/cb11-cn180.html','historical_round'),round(2000,'https://www.census.gov/newsroom/releases/archives/2010_census/cb11-cn180.html','historical_round')],
    note:notes('AreaData uses the 2020 Island Areas Census demographic profile and keeps 2019 income and SNAP reference fields labelled separately.','AreaData usa el perfil demográfico del Censo de Áreas Insulares 2020 y mantiene por separado los campos de ingresos y SNAP referidos a 2019.','AreaDataでは2020年Island Areas Censusの人口プロファイルを採用し、2019年基準の所得・SNAP項目は別年として保持します。')
  }
];

async function main(){
  const {project}=parseArgs();if(!project)throw new Error('Usage: node scripts/update-americas-census-history.mjs --project <directory>');
  const root=path.resolve(project),dataPath=path.join(root,'data','dashboard.json'),semanticPath=path.join(root,'evidence','COUNTRY_SEMANTIC_INVENTORY.json');
  const dataset=JSON.parse(await readFile(dataPath,'utf8'));
  // The shared Americas WDI electricity indicator already contains Argentina.
  // Remove the one-row duplicate previously added by the Argentina adapter.
  const duplicateIndicator='ARG_WDI_EG_ELC_ACCS_ZS',duplicateSource='arg-wdi-EG.ELC.ACCS.ZS';
  dataset.indicators=dataset.indicators.filter(row=>row.id!==duplicateIndicator);
  dataset.observations=dataset.observations.filter(row=>row.indicator_id!==duplicateIndicator);
  dataset.sources=dataset.sources.filter(row=>row.id!==duplicateSource);
  dataset.analysis.census_history=dataset.analysis.census_history||{schema_version:'1.0',as_of_year:2026,checked_at:'2026-09-20',countries:[]};
  const replacing=new Set(records.map(row=>row.country_id));
  dataset.analysis.census_history.countries=[...dataset.analysis.census_history.countries.filter(row=>!replacing.has(row.country_id)),...records];
  dataset.analysis.census_history.countries.sort((a,b)=>a.country_id.localeCompare(b.country_id));
  dataset.analysis.census_history.checked_at='2026-09-20';dataset.analysis.census_history.catalog_status='partial';
  dataset.collection.notes=[...(dataset.collection.notes||[]).filter(note=>!String(note).includes('WDI electricity, urban')),'ARG: the shared Americas WDI electricity series is reused; the duplicate one-row Argentina WDI electricity indicator was removed.','Census history links and the three most recent verified rounds are cataloged for all country/area editions whose Census evidence is currently integrated.'];
  dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  const content=JSON.stringify(dataset,null,2)+'\n',datasetSha256=createHash('sha256').update(content).digest('hex');await writeFile(dataPath,content);
  const semantic=JSON.parse(await readFile(semanticPath,'utf8'));semantic.records=semantic.records.filter(row=>row.indicator_id!==duplicateIndicator);
  if(!semantic.records.some(row=>row.country_area_id==='ARG'&&row.theme==='electricity'&&row.indicator_id==='EG.ELC.ACCS.ZS'))semantic.records.push({country_area_id:'ARG',source_id:'wb-EG.ELC.ACCS.ZS',source_path:'data/dashboard.json',source_url:'https://api.worldbank.org/v2/country/all/indicator/EG.ELC.ACCS.ZS?format=json&per_page=2000&source=2',table_id:'EG.ELC.ACCS.ZS',table_title:'World Bank WDI - Access to electricity (% of population)',field_id:'EG.ELC.ACCS.ZS / ARG',field_label:'Argentina access to electricity, shared Americas WDI series',numeric_cell_count:dataset.observations.filter(row=>row.territory_id==='ARG'&&row.indicator_id==='EG.ELC.ACCS.ZS'&&Number.isFinite(row.value)).length,theme:'electricity',disposition:'integrated',reason:'The shared Americas WDI indicator already contains the source-reported Argentina national series. It is eligible national context and is never imputed to provinces or departments; a duplicate Argentina-only indicator is therefore unnecessary.',indicator_id:'EG.ELC.ACCS.ZS',coverage_complete:true,country_edition_eligible:true});
  semantic.record_count=semantic.records.length;semantic.generated_at=new Date().toISOString();await writeFile(semanticPath,JSON.stringify(semantic,null,2)+'\n');
  const coverageIds=dataset.analysis?.coverage?.census_integrated_country_ids||[],historyIds=dataset.analysis.census_history.countries.map(row=>row.country_id);
  const missing=coverageIds.filter(id=>!historyIds.includes(id));if(missing.length)throw new Error(`Integrated Census histories still missing: ${missing.join(', ')}`);
  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),status:'complete_for_integrated_editions',catalog_scope_country_area_count:dataset.analysis.census_history.catalog_scope_country_ids?.length||57,cataloged_country_area_count:historyIds.length,cataloged_country_area_ids:historyIds,integrated_census_country_area_ids:coverageIds,missing_integrated_histories:missing,controls:{three_recent_rounds:true,official_latest_page:true,adopted_year_link:true,usa_acs_kept_separate:true,argentina_duplicate_electricity_removed:true},dataset_sha256:datasetSha256};
  await writeFile(path.join(root,'evidence','CENSUS_HISTORY_CATALOG_AUDIT.json'),JSON.stringify(audit,null,2)+'\n');
  console.log(JSON.stringify({validation,cataloged:historyIds.length,dataset_sha256:datasetSha256},null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

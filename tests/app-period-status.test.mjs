import test from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {fixture} from './fixture.mjs';
import {diagnosticCsv} from '../scaffold/site/diagnostic.mjs';

const appUrl=pathToFileURL(resolve('scaffold/site/app.mjs')).href;
let renderSequence=0;

function mixedPeriodFixture() {
  const data=fixture();
  const indicator=(id,name,theme,unit='people')=>({id,name,theme,unit,definition:`Synthetic ${name}`,source_id:'test',aggregation:'none',measurement_method:'source_reported'});
  data.indicators=[indicator('people','Census population','Population'),indicator('water','Water service','Services','%'),indicator('schools','Schools','Education'),indicator('rural','Rural population','Population'),indicator('urban','Urban population','Population')];
  data.observations=[
    {territory_id:'TST',indicator_id:'people',period:'2022',value:100,status:'observed',source_id:'test'},
    {territory_id:'TST-A',indicator_id:'people',period:'2022',value:60,status:'observed',source_id:'test'},
    {territory_id:'TST-A',indicator_id:'water',period:'2024',value:0,status:'observed',source_id:'test'},
    {territory_id:'TST-A',indicator_id:'schools',period:'2025',value:4,status:'observed',source_id:'test'},
    {territory_id:'TST-B',indicator_id:'rural',period:'2026-01-01',value:0,status:'observed',source_id:'test'},
    {territory_id:'TST-B',indicator_id:'urban',period:'2026-01-01',value:null,status:'not_applicable',source_id:'test'}
  ];
  return data;
}

async function renderPage(data,page,search='') {
  const listeners=new Map();
  const app={innerHTML:'',addEventListener:(name,handler)=>listeners.set(name,handler)};
  const location={href:`https://example.org/${page}/${search}`,search};
  globalThis.location=location;
  globalThis.document={
    body:{dataset:{page}},activeElement:null,title:'',
    getElementById:id=>id==='app'?app:{textContent:''},
    querySelector:()=>null,querySelectorAll:()=>[]
  };
  globalThis.HTMLInputElement=class {};
  globalThis.window={addEventListener:()=>{}};
  globalThis.history={
    replaceState:(_state,_title,url)=>{location.href=String(url);location.search=new URL(url).search;},
    pushState:(_state,_title,url)=>{location.href=String(url);location.search=new URL(url).search;}
  };
  globalThis.localStorage={getItem:()=>null,setItem:()=>{}};
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{languages:['en'],language:'en'}});
  globalThis.fetch=async url=>String(url).endsWith('/data/dashboard.json')?{ok:true,json:async()=>data}:{ok:false,status:404};
  await import(`${appUrl}?render-test=${page}-${++renderSequence}`);
  assert.doesNotMatch(app.innerHTML,/Dashboard data could not be loaded/);
  return {app,listeners};
}

const periodOptions=(html,id)=>html.match(new RegExp(`<select id="${id}"[^>]*>([\\s\\S]*?)<\\/select>`))?.[1] || '';
const indicatorCard=(html,name)=>html.match(new RegExp(`<article class="indicator-card">(?:(?!<\\/article>)[\\s\\S])*?<h3>${name}<\\/h3>[\\s\\S]*?<\\/article>`))?.[0] || '';

test('territorial and planning years cover their multi-indicator evidence while thematic stays indicator-specific',async()=>{
  const data=mixedPeriodFixture();
  const territorial=await renderPage(data,'territorial','?territory=TST-B&metric=people&period=2022');
  const years=periodOptions(territorial.app.innerHTML,'territorial-period');
  for(const year of ['2022','2024','2025','2026-01-01','latest-available'])assert.match(years,new RegExp(`value="${year}"`));
  assert.doesNotMatch(years,/2026-01-01 · no observation for this indicator/);
  assert.match(indicatorCard(territorial.app.innerHTML,'Urban population'),/No data/);
  await territorial.listeners.get('change')({target:{dataset:{control:'period'},value:'2026-01-01'}});
  assert.match(indicatorCard(territorial.app.innerHTML,'Urban population'),/Not applicable/);
  assert.match(indicatorCard(territorial.app.innerHTML,'Rural population'),/<strong>0<\/strong>/);
  const csv=diagnosticCsv(data,'TST-B','2026-01-01');
  const urbanRow=csv.split('\n').find(row=>row.includes('"urban"')&&row.includes('"TST-B"'));
  const ruralRow=csv.split('\n').find(row=>row.includes('"rural"')&&row.includes('"TST-B"'));
  assert.match(urbanRow,/"not_applicable"/);
  assert.match(ruralRow,/"0".*"observed"/);

  const latest=await renderPage(data,'territorial','?territory=TST-A&metric=people&period=2022');
  await latest.listeners.get('change')({target:{dataset:{control:'period'},value:'latest-available'}});
  assert.match(indicatorCard(latest.app.innerHTML,'Census population'),/Source reported · 2022/);
  assert.match(indicatorCard(latest.app.innerHTML,'Water service'),/Source reported · 2024/);
  assert.match(indicatorCard(latest.app.innerHTML,'Schools'),/Source reported · 2025/);

  const planning=await renderPage(data,'planning','?territory=TST-B&metric=people&period=2022');
  const planningYears=periodOptions(planning.app.innerHTML,'planning-period');
  for(const year of ['2022','2024','2025','2026-01-01','latest-available'])assert.match(planningYears,new RegExp(`value="${year}"`));

  const thematic=await renderPage(data,'thematic','?territory=TST-B&metric=people&period=2022');
  const thematicYears=periodOptions(thematic.app.innerHTML,'period-select');
  assert.match(thematicYears,/value="2022"/);
  assert.doesNotMatch(thematicYears,/value="2024"|value="2025"|value="2026-01-01"/);

  const thematicLatest=await renderPage(data,'thematic','?territory=TST-A&metric=people&period=latest-available');
  const thematicLatestYears=periodOptions(thematicLatest.app.innerHTML,'period-select');
  assert.match(thematicLatestYears,/<option value="latest-available" selected>Latest year for each indicator<\/option>/);
  assert.match(thematicLatestYears,/value="2022"/);
  assert.doesNotMatch(thematicLatestYears,/Latest year for each indicator · no observation for this indicator/);
  assert.match(thematicLatest.app.innerHTML,/<span>National value<\/span><strong>100<\/strong><small>Test country · 2022/);
});

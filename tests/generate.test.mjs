import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {generateSite,pageShell} from '../lib/generate.mjs';
import {initialState,selectTerritory,territoryLineage,hierarchyControls,selectHierarchyOption,routeQuery,observationState,latestObservedPeriod,effectivePeriodForIndicator,nationalOnly,comparisonRows,comparisonCompatibility,rankedRows,searchRows,rankingReveal,rankingScrollTop,distribution,mapGeometry,seriesGeometry,seriesFor,safeUrl,csvCell,makeCsv,evidenceRows,evidenceCsv,planningMarkdown,planningHtml} from '../scaffold/site/model.mjs';
import {hierarchyFixture} from './hierarchy-fixture.mjs';

function fixture() {
  return {
    schema_version:'0.2',generated_at:'2026-09-13T00:00:00.000Z',
    country:{id:'TST',iso2:'TS',name:'Test country',requested_name:'Test',locale:'en',national_territory_id:'TST',geography_note:'2017 provider regions; official code mapping pending.'},
    territories:[
      {id:'TST',name:'Test country',level:'national',type:'country',parent_id:null,official_code:null,code_system:'World Bank economy code',boundary_version:null},
      {id:'a',name:'Arua District',level:'ADM1',type:'district',parent_id:'TST',official_code:'301',code_system:'official',boundary_version:'edition-1'},
      {id:'b',name:'Mukono',level:'ADM1',type:'district',parent_id:'TST',official_code:'108',code_system:'official',boundary_version:'edition-1'},
      {id:'c',name:'Unmatched area',level:'ADM1',type:'district',parent_id:'TST',official_code:null,code_system:'provider',boundary_version:'edition-1'}
    ],
    indicators:[{id:'population',name:'Population',theme:'Population',unit:'people',definition:'Source-reported resident population',source_id:'s1',aggregation:'none',measurement_method:'source_reported'},{id:'water',name:'Water access',theme:'Services',unit:'%',definition:'Access among surveyed households',source_id:'s2',aggregation:'none',measurement_method:'source_reported'}],
    observations:[
      {territory_id:'TST',indicator_id:'population',period:'2026',value:null,status:'missing',source_id:'s1'},
      {territory_id:'TST',indicator_id:'population',period:'2025',value:null,status:'missing',source_id:'s1'},
      {territory_id:'TST',indicator_id:'population',period:'2024',value:1000,status:'observed',source_id:'s1'},
      {territory_id:'TST',indicator_id:'population',period:'2023',value:900,status:'observed',source_id:'s1'},
      {territory_id:'TST',indicator_id:'water',period:'2024',value:70,status:'observed',source_id:'s2'}
    ],
    sources:[{id:'s1',name:'National source',publisher:'Statistics publisher',url:'https://example.org/population',status:'ready',retrieved_at:'2026-09-13T00:00:00Z',reference_period:'2023:2026',sha256:'a'.repeat(64),license:'https://example.org/terms'},{id:'s2',name:'Water source',publisher:'Statistics publisher',url:'https://example.org/water',status:'ready',retrieved_at:'2026-09-13T00:00:00Z',reference_period:'2024',sha256:'b'.repeat(64),license:'ODbL 1.0',license_url:'https://example.org/license'}],
    boundaries:{type:'FeatureCollection',features:[polygon('a',[[0,0],[1,0],[1,1],[0,1],[0,0]]),polygon('b',[[5,0],[6,0],[6,1],[5,1],[5,0]])]},
    documents:[{id:'d1',territory_id:'a',title:'Published reference plan',url:'https://example.org/plan',period:'2024–2029',kind:'published-plan',availability:'link_verified',official_status:'unverified',source_id:'s1'}],
    gaps:[{category:'subnational_statistics',status:'not_collected',detail:'Local statistics have not been collected.',next_action:'Acquire census tables.'}],
    collection:{status:'partial',adapters:['test-fixture'],notes:[]}
  };
}
function polygon(id,coordinates) {return {type:'Feature',properties:{territory_id:id},geometry:{type:'Polygon',coordinates:[coordinates]}};}
function localValues(data) {data.observations.push({territory_id:'a',indicator_id:'water',period:'2024',value:0,status:'observed',source_id:'s2'},{territory_id:'b',indicator_id:'water',period:'2024',value:20,status:'observed',source_id:'s2'},{territory_id:'c',indicator_id:'water',period:'2024',value:null,status:'missing',source_id:'s2'});return data;}

test('first view opens an observed period and skips a failed first indicator; explicit missing choices remain',()=>{
  const data=fixture();
  assert.equal(latestObservedPeriod(data,'population'),'2024');
  assert.equal(initialState(data).period,'2024');
  assert.equal(initialState(data,'?metric=population&period=2026').period,'2026');
  data.observations=data.observations.filter(row=>row.indicator_id!=='population');
  assert.equal(initialState(data).metric,'water');
  assert.equal(initialState(data).period,'2024');
  const explicit=initialState(data,'?metric=population&period=2024');
  assert.equal(explicit.metric,'population');
  assert.equal(observationState(data,'TST',explicit.metric,explicit.period).status,'not_collected');
});

test('latest-available resolves to each indicator default while mixed-year indicators retain the sentinel',()=>{
  const data=fixture();
  data.analysis={default_period_by_indicator:{population:'2024',water:'2024'}};
  data.indicators[0].period_policy='latest_available_by_component';
  assert.equal(effectivePeriodForIndicator(data,'population','latest-available'),'latest-available');
  assert.equal(effectivePeriodForIndicator(data,'water','latest-available'),'2024');
  assert.equal(evidenceRows(data,'TST','latest-available').find(row=>row.indicator.id==='water').value,70);
  assert.match(evidenceCsv(data,'TST','latest-available'),/"water","Water access","2024","70"/);
});

test('area changes, national return and query round trips preserve selected analytical question',()=>{
  const data=fixture();
  const start=initialState(data,'?territory=a&metric=water&period=2024');
  for(const id of ['b','c','TST','a']) {
    const next=selectTerritory(data,start,id), restored=initialState(data,routeQuery(data,next));
    assert.equal(restored.selected,id);assert.equal(restored.metric,'water');assert.equal(restored.period,'2024');assert.equal(restored.notices.length,0);
  }
  assert.equal(selectTerritory(data,start,'unknown').selected,'a');
});

test('last explicit parent choice wins even when city belongs to the SAME subregion or region',()=>{
  const data=hierarchyFixture();
  const city=initialState(data,'?territory=city&metric=water&period=2024');
  assert.deepEqual(territoryLineage(data,city.selected).map(area=>area.id),['TST','north','nile','city']);
  const cityControls=hierarchyControls(data,city.selected);
  for(const [parentId,targetId] of [['north','nile'],['TST','north']]) {
    const control=cityControls.find(item=>item.parent.id===parentId);
    const wholeParent=control.options.find(option=>option.targetId===targetId);
    assert.equal(control.value,'context','Displayed ancestry is context, not the selected parent value');
    assert.notEqual(wholeParent.value,control.value,'Choosing the current ancestor must be a real select-value change');
    const parent=selectHierarchyOption(data,city,parentId,wholeParent.value);
    assert.equal(parent.selected,targetId);assert.equal(parent.metric,'water');assert.equal(parent.period,'2024');
    assert.equal(parent.level,data.territories.find(area=>area.id===targetId).level);
    assert.ok(!territoryLineage(data,parent.selected).some(area=>area.id==='city'));
    assert.ok(hierarchyControls(data,parent.selected).every(item=>item.value!=='area:city'),'No city remains selected after parent reset');
    const lowerControl=hierarchyControls(data,parent.selected).find(item=>item.parent.id===targetId);
    assert.equal(lowerControl?.value,'','The parent’s child selector returns to its empty whole-parent option');
    const restored=initialState(data,routeQuery(data,parent));
    assert.equal(restored.selected,targetId);assert.equal(restored.metric,'water');assert.equal(restored.period,'2024');
  }
});

test('empty child selection selects its parent; all evidence and outputs use parent source or parent missing',()=>{
  const data=hierarchyFixture();
  const city=initialState(data,'?territory=city&metric=population&period=2024');
  const subregion=selectHierarchyOption(data,city,'nile','');
  assert.equal(subregion.selected,'nile');assert.equal(observationState(data,subregion.selected,subregion.metric,subregion.period).value,400);
  assert.ok(evidenceRows(data,subregion.selected,'2024').every(row=>row.area.id==='nile'));
  assert.match(planningMarkdown(data,subregion.selected,'2024'),/Planning base — River Test Subregion/);
  assert.doesNotMatch(planningMarkdown(data,subregion.selected,'2024'),/city-only-plan/);
  const region=selectHierarchyOption(data,city,'TST','area:north');
  assert.equal(region.selected,'north');
  assert.deepEqual(observationState(data,region.selected,'population','2024'),{row:null,value:null,status:'not_collected'});
  assert.equal(seriesFor(data,region.selected,'population').length,0);
  assert.ok(evidenceRows(data,region.selected,'2024').every(row=>row.area.id==='north'&&row.value===null));
  assert.match(evidenceCsv(data,region.selected,'2024'),/Northern Test Region/);
  assert.doesNotMatch(evidenceCsv(data,region.selected,'2024'),/River Test City|"100"|"400"/);
  assert.match(planningHtml(data,region.selected,'2024'),/Planning base — Northern Test Region/);
  assert.doesNotMatch(planningHtml(data,region.selected,'2024'),/city-only-plan|\| 100 \||\| 400 \|/);
  assert.equal(mapGeometry(data.boundaries.features,region.selected).selectedHasGeometry,true);
  assert.equal(mapGeometry(data.boundaries.features,region.selected).bounds.maxX,8);
  assert.equal(initialState(data,routeQuery(data,city)).selected,'city','A browser-back route restores the city only when its own URL is revisited');
});

test('district to same parent and incomplete hierarchies retain generic, non-country-specific behavior',()=>{
  const data=hierarchyFixture(),district=initialState(data,'?territory=district&metric=water&period=2024');
  const region=selectHierarchyOption(data,district,'TST','area:north');assert.equal(region.selected,'north');
  assert.equal(selectHierarchyOption(data,district,'north','area:nile').selected,'nile');
  assert.deepEqual(hierarchyControls(fixture(),'a'),[],'One-level registry keeps the simple selector');
  data.territories.find(area=>area.id==='city').parent_id='missing';
  assert.deepEqual(hierarchyControls(data,'city'),[],'Unresolved ancestry is not fabricated');
  data.territories.find(area=>area.id==='city').parent_id='city';assert.deepEqual(territoryLineage(data,'city'),[]);
});

test('map-selected ranking row is revealed by clearing only a masking search; missing remains unranked',()=>{
  const data=localValues(fixture()),state=initialState(data,'?metric=water&period=2024'),rows=comparisonRows(data,state);
  const baseline=JSON.stringify(rows);
  assert.deepEqual(rankingReveal(rows,'a','Mukono'),{query:'',clearSearch:true,inCohort:true,ranked:true});
  assert.deepEqual(rankingReveal(rows,'a','301'),{query:'301',clearSearch:false,inCohort:true,ranked:true});
  assert.deepEqual(rankingReveal(rows,'c','Arua'),{query:'',clearSearch:true,inCohort:true,ranked:false});
  assert.deepEqual(rankingReveal(rows,'TST','Mukono'),{query:'Mukono',clearSearch:false,inCohort:false,ranked:false});
  assert.equal(JSON.stringify(rows),baseline);assert.equal(rankedRows(rows).length,2);assert.equal(distribution(rows).median,10);
});

test('rank reveal computes bounded scroll within the ranking viewport only',()=>{
  assert.equal(rankingScrollTop({scrollTop:0,clientHeight:300,scrollHeight:1200,rowTop:900,rowHeight:40}),770);
  assert.equal(rankingScrollTop({scrollTop:500,clientHeight:300,scrollHeight:1200,rowTop:560,rowHeight:40}),500);
  assert.equal(rankingScrollTop({scrollTop:500,clientHeight:300,scrollHeight:1200,rowTop:5,rowHeight:40}),0);
  assert.equal(rankingScrollTop({scrollTop:0,clientHeight:300,scrollHeight:1200,rowTop:1190,rowHeight:40}),900);
});

test('stale identity and wrong-country links receive explicit recovery notices',()=>{
  const data=fixture();
  const stale=initialState(data,'?country=TST&territory=a&type=city&code=999&boundary=old');
  assert.equal(stale.selected,'a');assert.equal(stale.notices.length,3);
  assert.match(stale.notices.join(' '),/boundary edition/);
  const other=initialState(data,'?country=OTHER&territory=a&metric=water&period=2024');
  assert.equal(other.selected,'TST');assert.match(other.notices.join(' '),/country/);
  const unknown=initialState(data,'?territory=deleted');assert.equal(unknown.selected,'TST');assert.match(unknown.notices.join(' '),/not in this data edition/);
});

test('national observations never produce local values or fabricated rankings',()=>{
  const data=fixture(),state=initialState(data,'?territory=a&metric=water&period=2024');
  const local=observationState(data,'a','water','2024');
  assert.equal(local.value,null);assert.equal(local.status,'not_collected');assert.equal(nationalOnly(data),true);
  assert.equal(rankedRows(comparisonRows(data,state)).length,0);
  assert.deepEqual(distribution(comparisonRows(data,state)),{count:0,min:null,max:null,median:null});
  assert.equal(observationState(data,'TST','water','2024').value,70);
});

test('zero participates in rank and median, missing does not, search never changes comparison population',()=>{
  const data=localValues(fixture()),state=initialState(data,'?territory=a&metric=water&period=2024');
  const rows=comparisonRows(data,state), ranked=rankedRows(rows);
  assert.equal(rows.length,3);assert.equal(ranked.length,2);assert.equal(ranked[1].value,0);assert.equal(ranked[1].rank,2);
  assert.deepEqual(distribution(rows),{count:2,min:0,max:20,median:10});
  assert.deepEqual(searchRows(ranked,'301').map(row=>row.area.id),['a']);
  assert.equal(rows.length,3);assert.equal(nationalOnly(data),false);
});

test('mixed same-level types or boundary editions cannot silently become a comparable cohort',()=>{
  const data=localValues(fixture()),state=initialState(data,'?metric=water&period=2024');
  data.territories[2].type='city';
  assert.equal(comparisonCompatibility(data,state).comparable,false);
  assert.match(comparisonCompatibility(data,state).reason,/different administrative types/);
  assert.equal(rankedRows(comparisonRows(data,state)).length,0);
  assert.equal(observationState(data,'b','water','2024').value,20);
  data.territories[2].type='district';data.territories[2].boundary_version='edition-2';
  assert.match(comparisonCompatibility(data,state).reason,/different boundary editions/);
  assert.equal(distribution(comparisonRows(data,state)).count,0);
});

test('map uses safe polygon coordinates, fits selection immediately and retains full national extent on return',()=>{
  const data=fixture();
  const all=mapGeometry(data.boundaries.features),selected=mapGeometry(data.boundaries.features,'a');
  assert.equal(all.paths.length,2);assert.equal(selected.selectedHasGeometry,true);
  assert.equal(all.bounds.maxX-all.bounds.minX,6);assert.equal(selected.bounds.maxX-selected.bounds.minX,1);
  assert.notEqual(all.paths[0].d,selected.paths[0].d);
  assert.equal(mapGeometry(data.boundaries.features,'c').selectedHasGeometry,false);
  const unsafe=polygon('bad',[[Infinity,0],[1,0],[0,1]]);
  assert.equal(mapGeometry([unsafe]).paths.length,0);
  const malicious={type:'Feature',properties:{territory_id:'x'},geometry:{type:'Point',coordinates:[0,0]}};
  assert.equal(mapGeometry([malicious]).paths.length,0);
  assert.ok(selected.paths.every(shape=>/^[MLZ0-9.,-]+$/.test(shape.d)));
});

test('dateline polygons and multipolygons do not create a nearly global false extent',()=>{
  const dateline=polygon('dateline',[[179,0],[-179,0],[-179,2],[179,2],[179,0]]);
  const mapped=mapGeometry([dateline]);assert.equal(mapped.bounds.maxX-mapped.bounds.minX,2);
  const multi={type:'Feature',properties:{territory_id:'multi'},geometry:{type:'MultiPolygon',coordinates:[[[[10,0],[11,0],[11,1],[10,0]]],[[[12,0],[13,0],[13,1],[12,0]]]]}};
  assert.equal((mapGeometry([multi]).paths[0].d.match(/M/g)||[]).length,2);
});

test('time-series gaps break the line and numeric zero remains visible',()=>{
  const series=[{period:'2020',value:0,status:'observed'},{period:'2021',value:null,status:'missing'},{period:'2022',value:10,status:'observed'}];
  const result=seriesGeometry(series);assert.equal(result.points.length,2);assert.equal(result.segments.length,2);assert.equal(result.min,0);
  assert.equal(seriesGeometry([{value:null,status:'missing'}]),null);
});

test('CSV quotes source strings and blocks formula prefixes without changing numeric negative values',()=>{
  for(const value of ['=SUM(A1:A2)','+1','-2+3','@SUM(A1:A2)','   =HYPERLINK("x")','\tformula'])assert.ok(csvCell(value).startsWith('"\''));
  assert.equal(csvCell(-12),'"-12"');assert.equal(csvCell(0),'"0"');assert.equal(csvCell('A,"B"'),'"A,""B"""');
  assert.ok(makeCsv([['x',0,null]]).startsWith('\uFEFF'));
  const data=fixture();data.territories[1].name='=HYPERLINK("unsafe")';
  const csv=evidenceCsv(data,'a','2024');assert.match(csv,/'=HYPERLINK/);assert.doesNotMatch(csv,/,"70",/);
});

test('document outputs have selected identity, missing evidence, correct sources and explicit generic status',()=>{
  const data=fixture(),markdown=planningMarkdown(data,'a','2024');
  assert.match(markdown,/Planning base — Arua District/);assert.match(markdown,/Generic, unapproved working outline/);
  assert.match(markdown,/official planning form/);assert.match(markdown,/Not collected/);assert.match(markdown,/https:\/\/example.org\/plan/);
  assert.doesNotMatch(markdown,/\| 1000 \||\| 70 \|/);
  assert.doesNotMatch(planningMarkdown(data,'b','2024'),/https:\/\/example.org\/plan/);
  data.territories[1].name='<img src=x onerror=alert(1)>';
  const html=planningHtml(data,'a','2024');assert.doesNotMatch(html,/<img/);assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<script/);
  assert.equal(safeUrl('javascript:alert(1)'),'');assert.equal(safeUrl('https://user:password@example.org/'),'');assert.equal(safeUrl('https://example.org/'),'https://example.org/');
});

test('generator writes five independent portable pages, same data and local-only runtime without overwriting canonical data',async()=>{
  const directory=await mkdtemp(path.join(os.tmpdir(),'ddpt-generate-'));
  try {
    await mkdir(path.join(directory,'data'));await writeFile(path.join(directory,'data','dashboard.json'),'canonical sentinel');
    await mkdir(path.join(directory,'site'));await writeFile(path.join(directory,'site','unrelated.txt'),'preserve');
    const data=fixture(),result=await generateSite({dataset:data,outDir:directory});
    assert.equal(result.files.length,18);
    assert.match(await readFile(path.join(result.siteDir,'.htaccess'),'utf8'),/AddType text\/javascript \.mjs/);
    assert.deepEqual(JSON.parse(await readFile(path.join(result.siteDir,'data','dashboard.json'),'utf8')),data);
    assert.equal(await readFile(path.join(directory,'data','dashboard.json'),'utf8'),'canonical sentinel');
    assert.equal(await readFile(path.join(result.siteDir,'unrelated.txt'),'utf8'),'preserve');
    const expectedVersion=JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8')).version;
    for(const page of ['home','territorial','thematic','database','planning']) {
      const html=await readFile(path.join(result.siteDir,page==='home'?'':page,'index.html'),'utf8');
      assert.match(html,new RegExp(`data-page="${page}"`));assert.match(html,/Content-Security-Policy/);
      assert.match(html,/data-language="en"/);assert.match(html,/data-language="es"/);assert.match(html,/data-language="ja"/);
      const assetPath=html.match(/src="([^\"]+app\.mjs[^\"]*)"/)[1];
      const publicUrl=new URL(assetPath,`https://example.org/nested/country/${page==='home'?'':page+'/'}`);
      assert.equal(publicUrl.pathname,'/nested/country/assets/app.mjs');
      assert.equal(publicUrl.searchParams.get('v'),expectedVersion);
      assert.match(html,new RegExp(`styles\\.css\\?v=${expectedVersion.replaceAll('.','\\.')}`));
      assert.doesNotMatch(html,/<script[^>]+src="https?:/);
    }
    const app=await readFile(path.join(result.siteDir,'assets','app.mjs'),'utf8');
    assert.match(app,/census-history\.mjs\?v=/);
    assert.match(await readFile(path.join(result.siteDir,'assets','census-history.mjs'),'utf8'),/censusRecencyColor/);
    for(const file of result.files.filter(file=>file.endsWith('.mjs'))) {
      const source=await readFile(file,'utf8');
      for(const match of source.matchAll(/\bfrom\s*['"](\.\/[^'"]+)['"]/g)) {
        const moduleUrl=new URL(match[1],'https://example.org/nested/country/assets/app.mjs');
        assert.equal(moduleUrl.searchParams.get('v'),expectedVersion,'Nested modules must refresh with the entry point');
      }
    }
    assert.match(app,/new URL\('data\/dashboard.json',base\)/);assert.match(app,/local statistics not yet collected/i);
    assert.match(await readFile(path.join(result.siteDir,'assets','i18n.mjs'),'utf8'),/resolveLanguage/);
    assert.match(await readFile(result.handoffPath,'utf8'),/national observations only/);
  } finally {
    const resolved=path.resolve(directory),temporaryRoot=path.resolve(os.tmpdir())+path.sep;
    assert.ok(resolved.startsWith(temporaryRoot)&&path.basename(resolved).startsWith('ddpt-generate-'),'Cleanup target must remain the created test directory under the system temporary folder');
    await rm(resolved,{recursive:true,force:true});
  }
});

test('static shell escapes external country names and never loads third-party scripts',()=>{
  const html=pageShell({country:{name:'</title><script>alert(1)</script>',locale:'en" onclick="x'},page:'territorial'});
  assert.doesNotMatch(html,/<script>alert/);assert.match(html,/&lt;script&gt;/);assert.match(html,/<html lang="en">/);
  assert.throws(()=>pageShell({country:{name:'x'},page:'unknown'}),/Unknown generated page/);
  const brand=html.match(/<a class="brand"[^>]*>/)[0];
  assert.match(brand,/data-brand-link/);assert.doesNotMatch(brand,/data-page-link/);assert.match(brand,/href="\.\.\/"/);
  assert.match(html,/<a href="\.\.\/" data-page-link="home"[^>]*>/,'Ordinary home navigation remains separate from the brand reset');
  const data=hierarchyFixture(),fresh=initialState(data);
  assert.equal(fresh.selected,'TST');assert.equal(fresh.metric,'population');assert.equal(fresh.period,'2024');
});

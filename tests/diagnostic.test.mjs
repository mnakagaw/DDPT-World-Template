import test from 'node:test';
import assert from 'node:assert/strict';
import {diagnosticMarkdown,diagnosticHtml,diagnosticCsv,renderInternalComparison,comparisonSummary,seriesSourceLabel} from '../scaffold/site/diagnostic.mjs';
import {internalComparison} from '../scaffold/site/analysis.mjs';
import {countryDiagnosticUrl,initialState,routeQuery,selectHierarchyOption} from '../scaffold/site/model.mjs';
import {analysisFixture} from './analysis-fixture.mjs';
import {hierarchyFixture} from './hierarchy-fixture.mjs';
import {fixture} from './fixture.mjs';

function csvRecords(csv) {
  const records=[];let record=[],value='',quoted=false;
  for(let i=csv.charCodeAt(0)===0xfeff?1:0;i<csv.length;i++) {
    const c=csv[i];
    if(c==='"') {if(quoted && csv[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}
    else if(c===',' && !quoted){record.push(value);value='';}
    else if(c==='\r' && csv[i+1]==='\n' && !quoted){record.push(value);records.push(record);record=[];value='';i++;}
    else value+=c;
  }
  if(value || record.length){record.push(value);records.push(record);}
  const headers=records.shift();return records.map(row=>Object.fromEntries(headers.map((header,i)=>[header,row[i]])));
}
const freeze=value=>{if(value && typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const statistic=(data,id,period='2024')=>data.observations.find(row=>row.territory_id===id && row.indicator_id==='people' && row.period===period);
const metricBlock=html=>html.split('<h2>Population — Test population</h2>')[1]?.split('<h2>')[0] || html;

test('all thirty members, exact zero and missing are retained in HTML, Markdown and CSV',()=>{
  const data=freeze(analysisFixture()),comparison=internalComparison(data,'river','people','2024');
  const html=renderInternalComparison(data,'river','people','2024',{interactive:false});
  const markdown=diagnosticMarkdown(data,'river','2024'),csv=csvRecords(diagnosticCsv(data,'river','2024'));
  assert.match(html,/All 30 member areas/);assert.match(markdown,/All 30 member areas/);
  assert.equal((html.match(/data-internal-row=/g)||[]).length,30);
  const numericRows=csv.filter(row=>row['Indicator ID']==='people' && row['Record scope']==='within_area');
  assert.equal(numericRows.length,30);assert.deepEqual(numericRows.map(row=>row['Territory ID']),comparison.rows.map(row=>row.area.id));
  for(const row of comparison.rows) {
    assert.ok(html.includes(`data-internal-row="${row.area.id}"`));assert.ok(markdown.includes(`/ ${row.area.id} |`));
  }
  assert.equal(numericRows.find(row=>row['Territory ID']==='city').Value,'0');
  assert.equal(numericRows.find(row=>row['Territory ID']==='city').Comparable,'true');
  const missing=numericRows.find(row=>row['Territory ID']==='missing-city');
  assert.equal(missing.Value,'');assert.equal(missing.Status,'not_collected');assert.equal(missing.Comparable,'false');
  assert.match(missing['Boundary join'],/No boundary/);
  assert.equal(numericRows.filter(row=>row.Territory==='Same name').length,2);
  assert.match(comparisonSummary(data,comparison),/29 of 30.*Range 0–100 people/);
});
test('same-parent selection exports its own missing value and its own direct child set',()=>{
  const data=analysisFixture(),city=initialState(data,'?territory=city&metric=people&period=2024');
  const region=selectHierarchyOption(data,city,'TST','area:north');
  const html=diagnosticHtml(data,region.selected,region.period),markdown=diagnosticMarkdown(data,region.selected,region.period),csv=csvRecords(diagnosticCsv(data,region.selected,region.period));
  assert.equal(region.selected,'north');assert.match(html,/Overall: No data people/);assert.match(markdown,/Overall: No data people/);
  const rows=csv.filter(row=>row['Indicator ID']==='people');assert.equal(rows.length,3);
  assert.deepEqual(rows.map(row=>row['Territory ID']),['north','river','lake']);
  assert.equal(rows[0].Value,'');assert.equal(rows[0].Status,'not_collected');assert.equal(rows[1].Value,'400');assert.equal(rows[2].Status,'missing');
  assert.ok(csv.every(row=>row['Analysis area ID']==='north'));assert.doesNotMatch(html,/data-internal-row="city"/);
});
test('base city and explicitly terminal country export their own evidence without false lower-area diagnosis',()=>{
  const data=analysisFixture();
  for(const id of ['city','TST']) {
    if(id==='TST')data.analysis.terminal_territory_ids.push('TST');
    const html=diagnosticHtml(data,id,'2024'),markdown=diagnosticMarkdown(data,id,'2024'),csv=csvRecords(diagnosticCsv(data,id,'2024'));
    assert.match(html,/Internal comparison stops at this area/);assert.match(markdown,/Internal comparison stops at this area/);
    assert.doesNotMatch(html,/data-internal-row=/);assert.ok(csv.every(row=>row['Record scope']==='overall' && row['Territory ID']===id));
    if(id==='city')assert.equal(csv.find(row=>row['Indicator ID']==='people').Value,'0');
    else assert.doesNotMatch(html,/Base municipality/);
  }
});
test('actual meaning metadata and reasons survive selected overall and internal rows in every export',()=>{
  const data=analysisFixture();Object.assign(statistic(data,'municipality'),{unit:'thousands',definition_id:'adults-only',definition:'Synthetic adult count',population:'Adult residents',method:'modeled'});
  const html=diagnosticHtml(data,'municipality','2024'),markdown=diagnosticMarkdown(data,'municipality','2024'),overall=csvRecords(diagnosticCsv(data,'municipality','2024')).find(row=>row['Indicator ID']==='people');
  for(const text of ['thousands','adults-only','Synthetic adult count','Adult residents','modeled','differs from the shared indicator definition']) {assert.ok(html.includes(text),text);assert.ok(markdown.includes(text),text);}
  assert.equal(overall.Value,'100');assert.equal(overall.Unit,'thousands');assert.equal(overall['Definition ID'],'adults-only');assert.equal(overall.Definition,'Synthetic adult count');assert.equal(overall.Population,'Adult residents');assert.equal(overall.Method,'modeled');assert.equal(overall['Meaning matches indicator'],'false');assert.equal(overall.Comparable,'');assert.match(overall['Comparison reason'],/differs/);
  const children=csvRecords(diagnosticCsv(data,'river','2024')),child=children.find(row=>row['Territory ID']==='municipality' && row['Indicator ID']==='people');
  assert.equal(child.Value,'100');assert.equal(child.Comparable,'false');
  for(const field of ['Unit','Definition ID','Definition','Population','Method','Meaning matches indicator'])assert.equal(child[field],overall[field]);
  const internalHtml=renderInternalComparison(data,'river','people','2024');assert.match(internalHtml,/adults-only/);assert.match(internalHtml,/Comparison not established/);
});
test('meaning-changing history keeps original values and methods in tables and breaks the plot',()=>{
  const data=analysisFixture();Object.assign(statistic(data,'city','2023'),{definition_id:'historical-adults',population:'Adults in 2023',method:'historic-model',unit:'thousands'});
  const html=metricBlock(diagnosticHtml(data,'city','2024')),markdown=diagnosticMarkdown(data,'city','2024');
  assert.match(html,/90 thousands/);assert.match(html,/historical-adults/);assert.match(html,/Adults in 2023/);assert.match(html,/historic-model/);
  assert.match(markdown,/2023 \| 90 \| thousands/);assert.match(markdown,/historical-adults/);assert.match(markdown,/differs from the shared indicator definition/);
  const graph=html.match(/<svg[^>]*class="diagnostic-history"[\s\S]*?<\/svg>/)?.[0];assert.ok(graph);
  assert.equal((graph.match(/<circle /g)||[]).length,1);assert.doesNotMatch(graph,/>2023: 90/);assert.match(graph,/>2024: 0/);
  assert.match(html,/Retrieved 2026-09-13T00:00:00Z/);
});
test('historical boundary changes keep original values and explicit context while breaking the history plot',()=>{
  const data=analysisFixture(),historical=statistic(data,'city','2023');historical.boundary_version='historic-city-1900';
  const html=metricBlock(diagnosticHtml(data,'city','2024')),markdown=diagnosticMarkdown(data,'city','2024');
  assert.match(html,/90 people/);assert.match(html,/historic-city-1900/);assert.match(html,/Observation boundary edition does not match/);
  assert.match(markdown,/2023 \| 90 \| people/);assert.match(markdown,/historic-city-1900/);assert.match(markdown,/Observation boundary edition does not match/);
  const graph=html.match(/<svg[^>]*class="diagnostic-history"[\s\S]*?<\/svg>/)?.[0];assert.ok(graph);assert.equal((graph.match(/<circle /g)||[]).length,1);assert.match(graph,/>2024: 0/);assert.doesNotMatch(graph,/>2023: 90/);
  const selected=metricBlock(diagnosticHtml(data,'city','2023'));assert.match(selected,/Overall: 90 people/);assert.match(selected,/Observation boundary edition does not match/);
  const csv=csvRecords(diagnosticCsv(data,'city','2023')).find(row=>row['Indicator ID']==='people');assert.equal(csv.Value,'90');assert.equal(csv.Status,'observed');assert.equal(csv['Observation boundary edition'],'historic-city-1900');assert.equal(csv['Meaning matches indicator'],'true');assert.match(csv['Comparison reason'],/Observation boundary edition does not match/);
});
test('failed or error history sources cannot create a line but the acquired row remains readable',()=>{
  for(const status of ['failed','error']) {
    const data=analysisFixture();data.sources.push({...data.sources.find(row=>row.id==='local'),id:'failed-history',name:'Failed historical source',status});statistic(data,'city','2023').source_id='failed-history';
    const html=metricBlock(diagnosticHtml(data,'city','2024')),markdown=diagnosticMarkdown(data,'city','2024');assert.match(html,/90 people/);assert.match(html,/Failed historical source/);assert.match(html,/no acquired usable data/);assert.match(markdown,/2023 \| 90 \| people/);assert.match(markdown,/no acquired usable data/);
    const graph=html.match(/<svg[^>]*class="diagnostic-history"[\s\S]*?<\/svg>/)?.[0];assert.ok(graph);assert.equal((graph.match(/<circle /g)||[]).length,1);assert.doesNotMatch(graph,/>2023: 90/);
    const csv=csvRecords(diagnosticCsv(data,'city','2023')).find(row=>row['Indicator ID']==='people');assert.equal(csv.Value,'90');assert.equal(csv['Source ID'],'failed-history');assert.match(csv['Comparison reason'],/no acquired usable data/);
  }
});
test('history with unrecorded boundary versions retains legacy line behavior',()=>{
  const data=analysisFixture(),html=metricBlock(diagnosticHtml(data,'city','2024'));
  const graph=html.match(/<svg[^>]*class="diagnostic-history"[\s\S]*?<\/svg>/)?.[0];assert.ok(graph);assert.equal((graph.match(/<circle /g)||[]).length,2);assert.match(graph,/>2023: 90/);assert.match(graph,/>2024: 0/);assert.doesNotMatch(html,/Observation boundary edition does not match/);
});
test('boundary mismatch remains distinct from value absence in all internal outputs',()=>{
  const data=analysisFixture();data.boundaries.features.find(feature=>feature.properties.territory_id==='city').properties.boundary_version='wrong-map-edition';
  const html=renderInternalComparison(data,'river','people','2024',{interactive:false}),markdown=diagnosticMarkdown(data,'river','2024'),csv=csvRecords(diagnosticCsv(data,'river','2024'));
  const row=csv.find(item=>item['Indicator ID']==='people' && item['Territory ID']==='city');assert.equal(row.Value,'0');assert.match(row['Boundary join'],/Boundary boundary_version does not match/);
  assert.match(html,/Boundary boundary_version does not match/);assert.match(markdown,/Boundary boundary_version does not match/);
  assert.equal((html.match(/class="internal-area"/g)||[]).length,28);assert.equal((html.match(/data-internal-row=/g)||[]).length,30);
});
test('print HTML contains full opened evidence and no clickable selection controls or scripts',()=>{
  const html=diagnosticHtml(analysisFixture(),'river','2024');
  assert.equal((html.match(/data-internal-row=/g)||[]).length,60);assert.equal((html.match(/<details open>/g)||[]).length,60);
  assert.doesNotMatch(html,/<script\b|data-action="inspect-internal"|role="button"/);
  assert.match(html,/@media print/);assert.match(html,/overflow:visible/);assert.match(html,/Membership sources/);
});
test('CSV quoting protects every source text field while negative numeric observations remain numeric',()=>{
  const data=analysisFixture(),area=data.territories.find(row=>row.id==='city');area.name='=HYPERLINK("https://example.org","test")';
  const row=statistic(data,'city');row.value=-4;row.definition=' @SUM(1,2)\nQuoted "evidence"';row.population='\t=population';row.method='-method';
  data.sources.find(source=>source.id==='local').name='+source';
  const csv=diagnosticCsv(data,'river','2024');assert.equal(csv.charCodeAt(0),0xfeff);
  const entry=csvRecords(csv).find(item=>item['Territory ID']==='city' && item['Indicator ID']==='people');
  assert.equal(entry.Value,'-4');assert.equal(entry.Territory,`'${area.name}`);assert.equal(entry.Definition,`'${row.definition}`);assert.equal(entry.Population,`'${row.population}`);assert.equal(entry.Method,"'-method");assert.equal(entry['Source name'],"'+source");
});
test('untrusted names and definitions render as text and never executable HTML',()=>{
  const data=analysisFixture();data.territories.find(area=>area.id==='city').name='<img src=x onerror=alert(1)>';
  statistic(data,'city').definition='<script>alert(1)</script> | [bad](javascript:alert(1))';
  const html=diagnosticHtml(data,'city','2024'),markdown=diagnosticMarkdown(data,'city','2024');
  assert.doesNotMatch(html,/<img\b|<script\b|href="javascript:/);assert.match(html,/&lt;script&gt;/);assert.match(html,/&lt;img/);
  assert.ok(markdown.includes('\\<script\\>'));assert.ok(markdown.includes('\\[bad\\]'));
});
test('census comparison rows link the visible Census year to the official census page',()=>{
  const data=analysisFixture(),indicator=data.indicators.find(row=>row.id==='people'),source=data.sources.find(row=>row.id==='local');
  indicator.series_family='census';source.name='Official census population table';source.publisher='National Statistical Office';source.catalog_url='https://example.org/census/2024';
  const html=renderInternalComparison(data,'river','people','2024');
  assert.match(html,/href="https:\/\/example\.org\/census\/2024"[^>]*>Census 2024/);
  assert.match(html,/National Statistical Office/);
  assert.match(html,/href="https:\/\/example\.org\/local"[^>]*>Official census population table/);
});
test('a regional latest-available census aggregate is labelled as a mixed-year series',()=>{
  const indicator={series_family:'census'};
  assert.equal(seriesSourceLabel(indicator,null,'latest-available'),'Mixed-year Census series');
  assert.equal(seriesSourceLabel(indicator,{period:'2024'},'2024'),'Census 2024');
  assert.equal(seriesSourceLabel(indicator,{period:'2024'},'2024','es'),'Censo 2024');
  assert.equal(seriesSourceLabel(indicator,{period:'2024'},'2024','ja'),'国勢調査 2024年');
});
test('world to country links require explicit mapping, preserve period, and discard world identity fields',()=>{
  const world=analysisFixture(),state={selected:'TST',metric:'people',period:'2021',level:'country'};
  const mapped=new URL(countryDiagnosticUrl(world,state,'https://example.org/world/'));
  assert.equal(mapped.pathname,'/world/countries/TST/territorial/');assert.equal(mapped.searchParams.get('country'),'TST');assert.equal(mapped.searchParams.get('territory'),'TST');assert.equal(mapped.searchParams.get('period'),'2021');assert.equal(mapped.searchParams.get('metric'),'population');
  for(const key of ['type','code','boundary','level','requested_metric'])assert.equal(mapped.searchParams.has(key),false);
  const country=hierarchyFixture(),restored=initialState(country,mapped.search);assert.equal(restored.selected,'TST');assert.equal(restored.metric,'population');assert.equal(restored.period,'2021');
  world.analysis.country_sites[0].target_territory_id='north';assert.equal(new URL(countryDiagnosticUrl(world,state,'https://example.org/world/')).searchParams.get('territory'),'north');
  assert.equal(countryDiagnosticUrl(world,{...state,selected:'north'},'https://example.org/world/'),'');
});
test('same-looking unmapped indicator IDs are not copied and handoff notice survives reload and navigation',()=>{
  const world=analysisFixture();delete world.analysis.country_sites[0].indicator_map;
  world.analysis.country_sites[0].url='./countries/TST/territorial/?metric=people&type=old&code=wrong&boundary=old';
  const url=new URL(countryDiagnosticUrl(world,{selected:'TST',metric:'people',period:'2020'},'https://example.org/world/'));
  assert.equal(url.searchParams.has('metric'),false);assert.equal(url.searchParams.get('requested_metric'),'people');assert.equal(url.searchParams.get('source_dataset'),'WLD');
  for(const key of ['type','code','boundary'])assert.equal(url.searchParams.has(key),false);
  const country=fixture();country.indicators.unshift({...country.indicators[0],id:'domestic-default'});country.observations.push({...country.observations[0],indicator_id:'domestic-default'});
  const restored=initialState(country,url.search);assert.equal(restored.metric,'domestic-default');assert.equal(restored.period,'2020');assert.match(restored.notices.join(' '),/No verified indicator mapping/);
  const reloaded=initialState(country,routeQuery(country,restored));assert.equal(reloaded.metric,'domestic-default');assert.equal(reloaded.period,'2020');assert.match(reloaded.notices.join(' '),/separate concept/);assert.equal(reloaded.requestedMetric,'people');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {planningFixture} from './planning-fixture.mjs';
import {fixture} from './fixture.mjs';
import {planningSettings,planningDocuments,documentGroups,officialMapState,relatedResourceUrl} from '../scaffold/site/planning.mjs';
import {renderDocumentGroups} from '../scaffold/site/planning-view.mjs';
import {initialState,selectHierarchyOption,planningMarkdown,planningHtml,documentsCsv,hierarchyControls} from '../scaffold/site/model.mjs';

test('plan, fiscal and assessment evidence keeps its own periods, definitions and observed zero across screen and outputs',()=>{
  const data=planningFixture('A');
  const html=renderDocumentGroups(data,'city'),md=planningMarkdown(data,'city','2024'),print=planningHtml(data,'city','2024'),csv=documentsCsv(data,'city');
  for(const text of [html,md,print,csv]) {
    assert.match(text,/2025\/26/);assert.match(text,/2029\/30/);assert.match(text,/Synthetic published definition for expenditure/);assert.match(text,/budget execution|Budget execution/);assert.match(text,/plan achievement|Plan achievement/);assert.match(text,/evaluation|assessment/);assert.match(text,/PDF page 4/);
  }
  assert.match(html,/<strong>0<\/strong> test currency thousands/);
  assert.match(md,/Cumulative expenditure: 0 test currency thousands/);
  assert.match(csv,/"expenditure","Cumulative expenditure","0","observed"/);
  assert.match(md,/Requested evidence period: 2024/);assert.match(md,/generic planning aid/);
  assert.doesNotMatch(html,/Synthetic district plan/);
});
test('all adopted and extra material categories remain reachable without imposing separate pages',()=>{
  const data=planningFixture('B'),groups=documentGroups(data,'city');
  assert.deepEqual(groups.map(row=>row.id),['plan','budget','other']);
  assert.equal(groups.flatMap(row=>row.documents).length,planningDocuments(data,'city').length);
  assert.match(renderDocumentGroups(data,'city'),/Synthetic official evaluation/);
  assert.deepEqual(planningSettings(fixture()).outputs,['markdown','html','evidence_csv']);
  assert.deepEqual(planningSettings(planningFixture('C')).outputs,[]);
});
test('same-named district and city, missing parent and same-parent reselection never inherit another area materials',()=>{
  const data=planningFixture('A'),city=initialState(data,'?territory=city&metric=water&period=2024');
  const parent=selectHierarchyOption(data,city,'TST','area:north');
  const choices=hierarchyControls(data,'city').flatMap(control=>control.options);
  assert.notEqual(choices.find(option=>option.targetId==='city').label,choices.find(option=>option.targetId==='district').label);
  assert.equal(parent.selected,'north');assert.equal(parent.metric,'water');assert.equal(parent.period,'2024');
  for(const id of ['district','north']) {
    const md=planningMarkdown(data,id,'2024'),html=renderDocumentGroups(data,id),csv=documentsCsv(data,id);
    for(const text of [md,html,csv])assert.doesNotMatch(text,/Synthetic city budget|Synthetic city development plan|Synthetic implementation results/);
  }
  assert.match(planningMarkdown(data,'district','2024'),/Synthetic district plan/);
  assert.doesNotMatch(planningMarkdown(data,'city','2024'),/District plan body has not/);
  assert.equal(officialMapState(data,'north').key,'unknown');
});
test('official map uses exact category and material period, never link counts or legacy status assertions',()=>{
  const data=planningFixture('A');
  assert.equal(officialMapState(data,'city').key,'council_adopted');
  data.planning.map.period='2020/21';assert.equal(officialMapState(data,'city').key,'unknown');
  data.planning.map.period='2025/26–2029/30';
  data.documents.push({...data.documents[0],id:'conflicting-plan',official_status:'draft_published'});
  assert.equal(officialMapState(data,'city').key,'conflict');
  data.documents.pop();delete data.documents[0].official_evidence;
  assert.equal(officialMapState(data,'city').key,'unknown');
  assert.match(renderDocumentGroups(data,'city'),/not verified; no approval inferred/);
  data.planning.map={mode:'coverage',category:'budget',period:'2020/21'};
  assert.equal(officialMapState(data,'city').key,'no_reference');
});
test('source content stays inert in HTML and source strings are guarded in materials CSV',()=>{
  const data=planningFixture('A');data.documents[0].content.summary='<img src=x onerror=alert(1)>';
  data.documents[0].title='=HYPERLINK("https://example.org")';
  assert.doesNotMatch(renderDocumentGroups(data,'city'),/<img src=x/);
  assert.match(renderDocumentGroups(data,'city'),/&lt;img/);
  assert.match(documentsCsv(data,'city'),/"'=HYPERLINK/);
});
test('legacy extraction labels are retained for review but never upgraded into verified reference coverage',()=>{
  const data=planningFixture('A');data.planning.map={mode:'coverage'};
  data.documents=data.documents.filter(doc=>doc.id==='city-plan');
  data.documents[0].availability='downloaded';delete data.documents[0].content;delete data.documents[0].official_evidence;delete data.documents[0].territory_match;
  assert.equal(officialMapState(data,'city').key,'no_reference');
  assert.match(renderDocumentGroups(data,'city'),/Legacy \/ unverified: downloaded/);
  assert.match(planningMarkdown(data,'city','2024'),/Legacy \/ unverified: downloaded/);
});
test('related local services preserve identity and periods under hosting subpaths without credential or path escape',()=>{
  const query='territory=city&metric=water&period=2024';
  assert.equal(relatedResourceUrl('./thematic/','https://example.org/project/',query),'https://example.org/project/thematic/?'+query);
  assert.equal(relatedResourceUrl('https://example.org/official','https://example.org/project/',query),'https://example.org/official');
  assert.equal(relatedResourceUrl('HTTPS://example.org/official','https://example.org/project/',query),'https://example.org/official');
  for(const bad of ['javascript:alert(1)','//evil.example/','../outside/','./%2e%2e/outside/','https://user:pass@example.org/'])assert.equal(relatedResourceUrl(bad,'https://example.org/project/',query),'');
});

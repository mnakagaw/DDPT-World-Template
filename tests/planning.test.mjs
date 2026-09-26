import test from 'node:test';
import assert from 'node:assert/strict';
import {validateDataset} from '../lib/validate.mjs';
import {validatePlanning,isIsoDate,isPlanningLink} from '../lib/planning-validation.mjs';
import {hierarchyFixture} from './hierarchy-fixture.mjs';
import {planningFixture,planningScenarios} from './planning-fixture.mjs';
import {planningSettings,planningDocuments,documentGroups,officialMapState,selectedGaps,documentPeriod,findingValue} from '../scaffold/site/planning.mjs';

const errorText=(mutate,scenario='integrated')=>{const data=planningFixture(scenario);mutate(data);return validateDataset(data).errors.join('\n');};
const plan=data=>data.documents.find(doc=>doc.id==='city-plan');
const budget=data=>data.documents.find(doc=>doc.id==='city-budget');

test('schema 0.2 legacy documents remain compatible without promoting assertions or acquisition aliases',()=>{
  const data=hierarchyFixture();
  delete data.planning;
  data.documents[0].availability='downloaded';data.documents[0].official_status='approved';
  const result=validateDataset(data);assert.deepEqual(result.errors,[]);
  assert.match(result.warnings.join(' '),/legacy or unknown string/);assert.match(result.warnings.join(' '),/cannot color an official-status map/);
  assert.deepEqual(planningSettings(data).outputs,['markdown','html','evidence_csv']);
  data.documents[0].availability='extracted';assert.deepEqual(validateDataset(data).errors,[]);
});

test('synthetic integrated, scattered and partial scenarios validate while adoption never drops acquired documents',()=>{
  for(const [name,data] of Object.entries(planningScenarios())) {
    assert.deepEqual(validateDataset(data).errors,[],name);
    assert.ok(data.collection.notes.some(note=>/fictional test evidence/.test(note)));
    assert.deepEqual(documentGroups(data,'city').flatMap(group=>group.documents).map(doc=>doc.id).sort(),planningDocuments(data,'city').map(doc=>doc.id).sort());
  }
  const scattered=planningFixture('scattered');
  assert.ok(documentGroups(scattered,'city').some(group=>group.id==='other'&&group.documents.some(doc=>doc.category==='evaluation')));
  const partial=planningFixture('partial');
  assert.deepEqual(planningSettings(partial).outputs,[]);assert.match(validateDataset(partial).warnings.join(' '),/must explain/);
});

test('configuration rejects unknown categories, unsupported outputs and malformed section/system fields',()=>{
  assert.match(errorText(data=>data.planning.sections=[{id:'approval-workflow',label:'Invented'}]),/known planning category/);
  assert.match(errorText(data=>data.planning.sections.push({...data.planning.sections[0]})),/duplicate category/);
  assert.match(errorText(data=>data.planning.outputs=['docx','pdf','ai']),/unsupported format/);
  assert.match(errorText(data=>data.planning.system.source_ids=[]),/at least one/);
  assert.match(errorText(data=>data.planning.system.source_ids=['unknown']),/unknown source/);
  assert.match(errorText(data=>data.planning.sections[0].label=0),/label must be/);
  assert.match(errorText(data=>data.planning.purpose=[]),/purpose must be/);
});

test('official-state maps require exact document-period category and controlled local status definitions',()=>{
  assert.match(errorText(data=>delete data.planning.map.category),/requires a document category/);
  assert.match(errorText(data=>delete data.planning.map.period),/requires an exact document-period/);
  assert.match(errorText(data=>data.planning.map.statuses=[]),/country-specific status definitions/);
  assert.match(errorText(data=>data.planning.map.statuses[0].color='url(javascript:alert(1))'),/hexadecimal color/);
  assert.match(errorText(data=>data.planning.map.statuses.push({...data.planning.map.statuses[0]})),/duplicate status id/);
  assert.match(errorText(data=>data.planning.map.statuses[0].id='unknown'),/reserved unknown or conflict state/);
  const data=planningFixture();
  assert.equal(officialMapState(data,'city').key,'council_adopted');
  data.planning.map.period='2025';assert.equal(officialMapState(data,'city').key,'unknown','Fiscal/multi-year label cannot be reduced to a statistical year');
  assert.deepEqual(validateDataset(data).errors,[],'An unmatched exact period is legal and renders unknown, not a fabricated match');
});

test('new official claims need documentary proof and never infer approval from acquisition',()=>{
  assert.match(errorText(data=>delete plan(data).official_evidence),/asserted official_status requires official_evidence/);
  assert.match(errorText(data=>delete plan(data).territory_match),/requires territory_match/);
  assert.match(errorText(data=>plan(data).official_evidence.locator=''),/locator must be/);
  assert.match(errorText(data=>plan(data).official_evidence.source_id='absent'),/registered source/);
  assert.match(errorText(data=>data.sources.find(source=>source.id==='plan-body').status='failed'),/cannot verify evidence from a failed source/);
  const data=planningFixture();
  const conflict=structuredClone(plan(data));conflict.id='city-second-plan';conflict.official_status='draft_published';data.documents.push(conflict);
  assert.deepEqual(validateDataset(data).errors,[],'Conflicting sourced records must remain inspectable');
  assert.equal(officialMapState(data,'city').key,'conflict');
  assert.equal(officialMapState(data,'district').key,'unknown','Body acquisition is not official approval');
});

test('same-name city and district use exact identity evidence, not names or neighbouring records',()=>{
  const data=planningFixture();
  assert.equal(data.territories.find(row=>row.id==='city').name,data.territories.find(row=>row.id==='district').name);
  plan(data).territory_id='district';
  const errors=validateDataset(data).errors.join(' ');assert.match(errors,/type must exactly match/);assert.match(errors,/official_code must exactly match/);
  assert.match(errorText(data=>plan(data).territory_match.country_id='OTHER'),/country_id must match/);
  assert.match(errorText(data=>plan(data).territory_match.code_system='another registry'),/code_system must exactly match/);
  assert.match(errorText(data=>plan(data).territory_match.boundary_version='old-edition'),/boundary_version must exactly match/);
});

test('null identity fields are explicit and permitted only when absent in the exact territory registry',()=>{
  assert.match(errorText(data=>plan(data).territory_match.official_code=null),/official_code must exactly match/);
  assert.match(errorText(data=>delete plan(data).territory_match.official_code),/explicit text or null/);
  const data=planningFixture();
  data.territories.find(row=>row.id==='city').official_code=null;
  for(const doc of data.documents.filter(doc=>doc.territory_id==='city'))doc.territory_match.official_code=null;
  assert.deepEqual(validateDataset(data).errors,[]);
});

test('same-type areas with null official codes cannot receive each other’s documents by changing only the target ID',()=>{
  const data=planningFixture();
  const original=data.territories.find(row=>row.id==='city'),other=data.territories.find(row=>row.id==='other-city');
  for(const area of [original,other])area.official_code=null;
  for(const doc of data.documents.filter(doc=>doc.territory_id==='city'))doc.territory_match.official_code=null;
  for(const key of ['type','code_system','official_code','boundary_version'])assert.equal(original[key],other[key]);
  assert.deepEqual(validateDataset(data).errors,[],'The correctly matched source is valid without official codes');
  plan(data).territory_id='other-city';
  assert.equal(plan(data).territory_match.territory_id,'city','The source identity record still names the original area');
  assert.match(validateDataset(data).errors.join(' '),/territory_match.territory_id must exactly match document.territory_id/);
  assert.match(errorText(data=>delete plan(data).territory_match.territory_id),/territory_id must be a nonempty string/);
  assert.match(errorText(data=>plan(data).territory_match.territory_id='not-registered'),/registered matched territory/);
  assert.match(errorText(data=>plan(data).territory_match.territory_id=null),/territory_id must be a nonempty string/);
});

test('literal fiscal periods, ordered real dates and historical territory validity remain separate from statistics years',()=>{
  assert.equal(documentPeriod(plan(planningFixture())),'2025/26–2029/30');
  assert.match(errorText(data=>plan(data).period='2025'),/must equal target_period.label literally/);
  assert.match(errorText(data=>plan(data).target_period.start='2025-02-30'),/ISO calendar date/);
  assert.match(errorText(data=>plan(data).target_period.end='2020-01-01'),/interval is reversed/);
  assert.match(errorText(data=>{plan(data).target_period={label:'1990/91',kind:'fiscal_year',start:'1990-07-01',end:'1991-06-30'};plan(data).period='1990/91';}),/does not overlap/);
  assert.match(errorText(data=>plan(data).territory_match.valid_to='2040-12-31'),/registered historical validity date/);
  assert.equal(isIsoDate('2024-02-29'),true);assert.equal(isIsoDate('2025-02-29'),false);assert.equal(isIsoDate('2026-13-01'),false);
  const old=planningFixture();const city=old.territories.find(row=>row.id==='city');city.valid_from='1990-01-01';city.valid_to='2030-12-31';
  for(const doc of old.documents.filter(doc=>doc.territory_id==='city'))doc.territory_match.valid_from=city.valid_from;
  plan(old).target_period={label:'1990/91',kind:'fiscal_year',start:'1990-07-01',end:'1991-06-30'};plan(old).period='1990/91';
  assert.deepEqual(validateDataset(old).errors,[],'Documented historical identity permits historical plans');
});

test('source-backed summaries and findings require content verification and retained source bodies',()=>{
  assert.match(errorText(data=>plan(data).availability='content_extracted'),/content requires availability content_verified/);
  assert.match(errorText(data=>budget(data).availability='body_acquired'),/findings requires availability content_verified/);
  assert.match(errorText(data=>delete data.sources.find(source=>source.id==='budget-body').raw_path),/requires its document source raw_path and SHA-256/);
  assert.match(errorText(data=>delete data.sources.find(source=>source.id==='plan-body').sha256),/requires its document source raw_path and SHA-256/);
  assert.match(errorText(data=>data.sources.find(source=>source.id==='plan-body').raw_path='https://example.org/not-a-local-raw-file'),/Unsafe raw_path/);
  assert.match(errorText(data=>plan(data).content.evidence.checked_at='yesterday'),/checked_at must be/);
  assert.match(errorText(data=>plan(data).content.priorities=[false]),/nonempty strings/);
  assert.match(errorText(data=>budget(data).extraction_status='extracted'),/single acquisition axis/);
});

test('financial zero is observed while missing numeric findings require explicit null and status',()=>{
  const data=planningFixture(),zero=budget(data).findings.find(row=>row.kind==='budget_execution');
  assert.equal(zero.value,0);assert.equal(findingValue(zero),'0 %');
  assert.deepEqual(validateDataset(data).errors,[]);
  assert.match(errorText(data=>budget(data).findings[0].value=null),/observed value must be finite/);
  assert.match(errorText(data=>{budget(data).findings[0].value_status='missing';budget(data).findings[0].value=0;}),/non-observed value must be null/);
  assert.match(errorText(data=>budget(data).findings[0].value='1000'),/observed value must be finite/);
  assert.match(errorText(data=>delete budget(data).findings[0].unit),/unit must be/);
  assert.match(errorText(data=>delete budget(data).findings[0].value_status),/explicit value_status/);
  const missing=planningFixture();budget(missing).findings[0].value=null;budget(missing).findings[0].value_status='missing';
  assert.deepEqual(validateDataset(missing).errors,[]);assert.match(findingValue(budget(missing).findings[0]),/missing/);
});

test('budget execution, plan achievement and official evaluation preserve distinct definitions, types and scales',()=>{
  const data=planningFixture(),all=data.documents.flatMap(doc=>doc.findings||[]);
  assert.ok(all.some(row=>row.kind==='budget_execution'&&row.value===0));
  assert.ok(all.some(row=>row.kind==='plan_achievement'&&row.value===25));
  assert.ok(all.some(row=>row.kind==='official_evaluation'&&row.value===3&&row.scale.max===5));
  assert.ok(all.some(row=>row.kind==='official_evaluation'&&typeof row.statement==='string'&&!Object.hasOwn(row,'value')));
  assert.match(errorText(data=>budget(data).findings[0].kind='overall_success'),/must preserve the published/);
  assert.match(errorText(data=>delete budget(data).findings[0].definition),/definition must be/);
  assert.match(errorText(data=>delete budget(data).findings[0].scope),/scope must be/);
  assert.match(errorText(data=>data.documents.find(doc=>doc.id==='city-evaluation').findings[0].value=90),/outside the declared source scale/);
  const over=planningFixture();budget(over).findings.find(row=>row.kind==='budget_execution').value=115;
  assert.deepEqual(validateDataset(over).errors,[],'A published spending rate above 100 is not silently clamped or rewritten');
});

test('scoped gaps and documents remain exact-territory; parent selection does not inherit city evidence',()=>{
  const data=planningFixture();
  assert.deepEqual(planningDocuments(data,'north'),[]);
  assert.ok(planningDocuments(data,'city').every(doc=>doc.territory_id==='city'));
  assert.ok(!selectedGaps(data,'city').some(gap=>gap.territory_id==='district'||gap.territory_id==='north'));
  assert.ok(selectedGaps(data,'north').some(gap=>gap.category==='planning_documents'));
  data.sources.find(source=>source.id==='guidance').geographic_level='national';
  data.gaps.push({category:'national_series_gap',source_id:'guidance',status:'partial',detail:'National-only context has no local observation.',next_action:'Do not copy it locally.'});
  assert.ok(selectedGaps(data,'TST').some(gap=>gap.category==='national_series_gap'));
  assert.ok(!selectedGaps(data,'city').some(gap=>gap.category==='national_series_gap'));
  assert.ok(selectedGaps(data,'city').some(gap=>gap.category==='country_guidance'));
  assert.match(errorText(data=>data.gaps[1].territory_id='not-a-territory'),/gaps\[1\].territory_id/);
  assert.match(errorText(data=>data.gaps[1].source_id='not-a-source'),/gaps\[1\].source_id/);
});

test('related links stay HTTPS or inside the generated project; source update dates have their own state',()=>{
  for(const value of ['https://example.org/plan','./thematic/','./planning/?view=budget#resources'])assert.equal(isPlanningLink(value),true,value);
  for(const value of ['javascript:alert(1)','http://example.org','https://name:password@example.org/','//other.example/x','/other-project/','../secret','./../secret','./%2e%2e/secret','./%252e%252e/secret','./x\\y','./x\ny','investment/'])assert.equal(isPlanningLink(value),false,value);
  assert.match(errorText(data=>data.planning.related_links[0].url='./../secret'),/safe site-root-relative path/);
  assert.match(errorText(data=>data.planning.related_links[0].territory_id='unknown'),/registered territory/);
  assert.match(errorText(data=>data.planning.update.status='published'),/current or stopped/);
  assert.match(errorText(data=>data.planning.update.last_success_at='2026-10-01T00:00:00Z'),/cannot be after checked_at/);
  assert.deepEqual(validateDataset(planningFixture('scattered')).errors,[],'Stopped source updates can retain previously verified records');
});

test('malformed optional objects, nested arrays and primitive rows report errors without throwing',()=>{
  const mutations=[
    data=>data.planning=null,data=>data.planning=[],data=>data.planning.sections=[null],data=>data.planning.system=[],data=>data.planning.outputs={},
    data=>data.planning.map=null,data=>data.planning.map.statuses=[null],data=>data.planning.related_links=[null],data=>data.planning.update=9,
    data=>data.documents=[null],data=>plan(data).target_period=[],data=>plan(data).territory_match='city',data=>plan(data).official_evidence=false,
    data=>plan(data).content=[],data=>plan(data).content.evidence=null,data=>budget(data).findings=[null],data=>budget(data).findings[0].period=5,
    data=>budget(data).findings[0].evidence=[],data=>budget(data).findings[0].scale=[],data=>data.gaps=[null],data=>data.sources=[null],data=>data.territories=[null]
  ];
  for(const mutate of mutations) {
    const data=planningFixture();mutate(data);let result;
    assert.doesNotThrow(()=>{result=validateDataset(data);});assert.ok(result.errors.length,mutate.toString());
  }
  for(const value of [null,[],false,0,'bad'])assert.doesNotThrow(()=>validatePlanning(value));
  assert.deepEqual(validatePlanning({}).errors,[],'Optional validator leaves required base fields to validateDataset');
});

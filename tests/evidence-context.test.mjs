import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from './fixture.mjs';
import {analysisFixture} from './analysis-fixture.mjs';
import {evidenceCsv,planningMarkdown} from '../scaffold/site/model.mjs';

test('legacy evidence columns stay stable while declared context keeps original values and reasons',()=>{
 const legacy=evidenceCsv(fixture(),'TST-A','2024');
 assert.equal(legacy.split('\r\n')[0].split(',').length,18);
 const data=analysisFixture(),row=data.observations.find(r=>r.territory_id==='city'&&r.indicator_id==='people'&&r.period==='2024');
 Object.assign(row,{value:2,unit:'thousands',definition_id:'adults',population:'Adults',method:'historic-survey',boundary_version:'old-city'});
 const csv=evidenceCsv(data,'city','2024'),markdown=planningMarkdown(data,'city','2024');
 assert.match(csv,/"2","thousands","observed"/);assert.match(csv,/"Adults","historic-survey",false|"Adults","historic-survey","false"/);
 assert.match(csv,/Observation boundary edition does not match/);assert.match(csv,/"Definition ID"/);
 assert.match(markdown,/2 \| thousands/);assert.match(markdown,/population Adults; method historic-survey/);assert.match(markdown,/Observation boundary edition does not match/);
});

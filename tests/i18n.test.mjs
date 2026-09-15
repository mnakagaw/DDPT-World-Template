import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveLanguage,languageLocale,translateText,sourceSeriesLabel} from '../scaffold/site/i18n.mjs';

test('browser language chooses Japanese, Spanish or English when no preference exists',()=>{
  assert.equal(resolveLanguage({browserLanguages:['ja-JP','en-US']}),'ja');
  assert.equal(resolveLanguage({browserLanguages:['es-DO','en']}),'es');
  assert.equal(resolveLanguage({browserLanguages:['fr-FR']}),'en');
  assert.equal(languageLocale('ja'),'ja-JP');
});

test('explicit URL language and remembered choice take precedence over browser default',()=>{
  assert.equal(resolveLanguage({query:'es',stored:'ja',browserLanguages:['en-US']}),'es');
  assert.equal(resolveLanguage({stored:'ja',browserLanguages:['es']}),'ja');
  assert.equal(resolveLanguage({query:'xx',stored:'',browserLanguages:['es-MX']}),'es');
});

test('core interface and source-series labels have all three display languages',()=>{
  assert.equal(translateText('Territorial diagnostic','es'),'Diagnóstico territorial');
  assert.equal(translateText('Territorial diagnostic','ja'),'地域診断');
  assert.equal(sourceSeriesLabel({series_family:'census'},{period:'2022'},'2022','es'),'Censo 2022');
  assert.equal(sourceSeriesLabel({series_family:'international_reference'},{series_stage:'medium_projection'},'2026','ja'),'国連中位推計 2026年');
  assert.equal(sourceSeriesLabel({series_family:'international_reference',series_stage_by_period:{2026:'medium_projection'}},null,'2026','en'),'UN medium projection 2026');
});

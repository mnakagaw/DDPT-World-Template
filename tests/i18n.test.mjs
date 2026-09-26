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

test('regional hierarchy and diagnostic exports translate the selected area',()=>{
  assert.equal(translateText('Whole Central Asia · no lower area selected','ja'),'中央アジア全体・下位地域の選択なし');
  assert.equal(translateText('Belongs to Central Asia · a lower area is selected','es'),'Dentro de Asia Central · área inferior seleccionada');
  assert.equal(translateText('macroregion · within Asia','ja'),'広域・アジア内');
  assert.equal(translateText('country · within Central Asia','es'),'país · dentro de Asia Central');
  assert.equal(translateText('Diagnostic report — Central Asia','ja'),'地域診断レポート — 中央アジア');
  assert.equal(translateText('Editable Diagnostic report','es'),'Informe de diagnóstico editable');
  assert.equal(translateText('Full diagnostic data CSV','ja'),'地域診断の全データ CSV');
  assert.equal(translateText('ASIA · TERRITORIAL DIAGNOSTIC','ja'),'アジア・地域診断');
  assert.equal(translateText('COUNTRY REFERENCE BOUNDARIES','es'),'LÍMITES DE REFERENCIA DE PAÍSES');
  assert.equal(translateText('Time-series values and sources (10)','ja'),'時系列の値と出典（10件）');
  assert.equal(translateText('Within the selected area — Countries and areas in Central Asia','ja'),'選択地域内の比較 — 中央アジアの国・地域');
});

#!/usr/bin/env node
// Use the country UI's export builders for producer/source comparison.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv,comparisonRows} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/brunei-areadata-20260927');
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
const cases={
  Brunei:'BRN',
  BruneiMuara:'BRN:DEPS:BPP2021:DISTRICT:BRUNEI-MUARA',
  Belait:'BRN:DEPS:BPP2021:DISTRICT:BELAIT',
  Temburong:'BRN:DEPS:BPP2021:DISTRICT:TEMBURONG',
  Kianggeh:'BRN:DEPS:BPP2021:MUKIM:BRUNEI-MUARA:KIANGGEH',
  Melilas:'BRN:DEPS:BPP2021:MUKIM:BELAIT:MELILAS',
};
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
for(const [stem,id] of Object.entries(cases)){
  const exports={
    'diagnostic.csv':diagnosticCsv(data,id,'2021'),
    'diagnostic.html':diagnosticHtml(data,id,'2021'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2021'),
    'planning.html':planningHtml(data,id,'2021','en'),
    'evidence.csv':evidenceCsv(data,id,'2021'),
  };
  for(const [suffix,content] of Object.entries(exports))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
}
const districtRows=comparisonRows(data,{selected:'BRN',metric:'BRN_BPP2021_POP_TOTAL',period:'latest-available',level:'adm1'});
const mukimRows=comparisonRows(data,{selected:cases.BruneiMuara,metric:'BRN_BPP2021_POP_TOTAL',period:'latest-available',level:'adm2'});
console.log(JSON.stringify({cases,comparisons:{districts:districtRows.length,
  districtsObserved:districtRows.filter(row=>Number.isFinite(row.value)).length,
  bruneiMuaraMukims:mukimRows.length,
  mukimsObserved:mukimRows.filter(row=>Number.isFinite(row.value)).length}}));

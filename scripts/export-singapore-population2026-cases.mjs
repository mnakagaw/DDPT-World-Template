#!/usr/bin/env node
// Produce real diagnostics/planning exports for the pinned-source verifier.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv,comparisonRows} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/singapore-areadata-20260927');
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
const cases={
  SGP:'SGP',
  Tampines:'SGP:URA:MP2025:PA:TM',
  TampinesEast:'SGP:SINGSTAT2026:SZ:TM:TAMPINES-EAST',
  AngMoKio:'SGP:URA:MP2025:PA:AM',
  ChangiBay:'SGP:URA:MP2025:PA:CB',
};
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
for(const [stem,id] of Object.entries(cases)){
  const exports={
    'diagnostic.csv':diagnosticCsv(data,id,'2026-06'),
    'diagnostic.html':diagnosticHtml(data,id,'2026-06'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2026-06'),
    'planning.html':planningHtml(data,id,'2026-06','en'),
    'evidence.csv':evidenceCsv(data,id,'2026-06'),
  };
  for(const [suffix,content] of Object.entries(exports))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
}
const nationalComparison=comparisonRows(data,{selected:'SGP',metric:'SGP_SINGSTAT_RESIDENT_TOTAL',period:'latest-available',level:'adm1'});
const tampinesComparison=comparisonRows(data,{selected:cases.Tampines,metric:'SGP_SINGSTAT_RESIDENT_TOTAL',period:'latest-available',level:'adm2'});
console.log(JSON.stringify({cases,comparison:{national_total:nationalComparison.length,
  national_observed:nationalComparison.filter(row=>Number.isFinite(row.value)).length,
  tampines_total:tampinesComparison.length,
  tampines_observed:tampinesComparison.filter(row=>Number.isFinite(row.value)).length}}));

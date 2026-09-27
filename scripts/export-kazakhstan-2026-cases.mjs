#!/usr/bin/env node
// Exercise the same export builders used by the rendered country dashboard.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv,comparisonRows} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/kazakhstan-areadata-20260927');
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
const cases={
  Kazakhstan:'KAZ', AbayRegion:'KAZ:KATO:100000000', AbaiDistrict:'KAZ:KATO:103200000',
  Akmola:'KAZ:KATO:110000000', BurabayDistrict:'KAZ:KATO:117000000',
  Ulytau:'KAZ:KATO:620000000', AlmatyOblast:'KAZ:KATO:190000000',
  AlmatyCity:'KAZ:KATO:750000000', AstanaCity:'KAZ:KATO:710000000',
  AlmatyDistrictAstana:'KAZ:KATO:711110000', ShymkentCity:'KAZ:KATO:790000000',
};
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
for(const [stem,id] of Object.entries(cases)){
  const exports={
    'diagnostic.csv':diagnosticCsv(data,id,'2026'),
    'diagnostic.html':diagnosticHtml(data,id,'2026'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2026'),
    'planning.html':planningHtml(data,id,'2026','en'),
    'evidence.csv':evidenceCsv(data,id,'2026'),
  };
  for(const [suffix,content] of Object.entries(exports))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
}
await writeFile(path.join(out,'Kazakhstan2021-evidence.csv'),evidenceCsv(data,'KAZ','2021'));
await writeFile(path.join(out,'Kazakhstan2021-diagnostic.csv'),diagnosticCsv(data,'KAZ','2021'));
const parents=[cases.Kazakhstan,cases.AbayRegion,cases.Akmola,cases.AstanaCity];
const comparisons=Object.fromEntries(parents.map(id=>{
  const rows=comparisonRows(data,{selected:id,metric:'KAZ_2026_JUL_TOTAL',
    period:'latest-available',level:id==='KAZ'?'adm1':'adm2'});
  return [id,{members:rows.length,observed:rows.filter(row=>Number.isFinite(row.value)).length}];
}));
console.log(JSON.stringify({cases,comparisons}));

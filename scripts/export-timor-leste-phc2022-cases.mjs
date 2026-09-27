#!/usr/bin/env node
// Produce the same exports used by the country UI for source/output comparison.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv,comparisonRows} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/timor-leste-areadata-20260927');
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
const cases={
  TLS:'TLS',
  Dili:'TLS:INETL:PHC2022:ADM1:DILI',
  Atauro:'TLS:INETL:PHC2022:ADM1:ATAURO',
  Baucau:'TLS:INETL:PHC2022:ADM1:BAUCAU',
  Oecusse:'TLS:INETL:PHC2022:ADM1:OECUSSE',
};
const out=path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
for(const [stem,id] of Object.entries(cases)){
  const exports={
    'diagnostic.csv':diagnosticCsv(data,id,'2022'),
    'diagnostic.html':diagnosticHtml(data,id,'2022'),
    'diagnostic.md':diagnosticMarkdown(data,id,'2022'),
    'planning.html':planningHtml(data,id,'2022','en'),
    'evidence.csv':evidenceCsv(data,id,'2022'),
  };
  for(const [suffix,content] of Object.entries(exports))
    await writeFile(path.join(out,`${stem}-${suffix}`),content);
}
const rows=comparisonRows(data,{selected:'TLS',metric:'TLS_PHC2022_POP_TOTAL',period:'latest-available',level:'adm1'});
console.log(JSON.stringify({cases,comparison:{total:rows.length,
  observed:rows.filter(row=>Number.isFinite(row.value)).length}}));

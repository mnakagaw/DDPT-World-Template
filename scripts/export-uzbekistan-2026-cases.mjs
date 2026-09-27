#!/usr/bin/env node
// Export from the same builders used by the country UI for source comparison.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {diagnosticCsv,diagnosticHtml,diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml,evidenceCsv,comparisonRows} from '../scaffold/site/model.mjs';

const project=path.resolve(process.argv[2]||'generated/uzbekistan-areadata-20260927');
const data=JSON.parse(await readFile(path.join(project,'data/dashboard.json'),'utf8'));
const cases={
  Uzbekistan:'UZB',
  Karakalpakstan:'UZB:COATO:1735',
  NukusCity:'UZB:COATO:1735401',
  BozatauDistrict:'UZB:COATO:1735209',
  AndijanRegion:'UZB:COATO:1703',
  AndijanCity:'UZB:COATO:1703401',
  TashkentRegion:'UZB:COATO:1727',
  TashkentCity:'UZB:COATO:1726',
  YangikhayotDistrict:'UZB:COATO:1726292',
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
const national=comparisonRows(data,{selected:'UZB',metric:'UZB_2026_SIAT_TOTAL',period:'latest-available',level:'adm1'});
const kara=comparisonRows(data,{selected:cases.Karakalpakstan,metric:'UZB_2026_SIAT_TOTAL',period:'latest-available',level:'adm2'});
const tashkentCity=comparisonRows(data,{selected:cases.TashkentCity,metric:'UZB_2026_SIAT_TOTAL',period:'latest-available',level:'adm2'});
console.log(JSON.stringify({cases,comparisons:{national:national.length,
  nationalObserved:national.filter(row=>Number.isFinite(row.value)).length,
  karakalpakstan:kara.length,karakalpakstanObserved:kara.filter(row=>Number.isFinite(row.value)).length,
  tashkentCity:tashkentCity.length,tashkentCityObserved:tashkentCity.filter(row=>Number.isFinite(row.value)).length}}));

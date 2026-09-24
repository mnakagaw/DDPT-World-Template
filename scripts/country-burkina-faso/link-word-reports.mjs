// Apply the BFA-only Word download affordance after a common site rebuild.
import fs from 'node:fs';
import path from 'node:path';

const project=path.resolve(process.argv[2]||'');
if(!process.argv[2])throw Error('Usage: node link-word-reports.mjs <project>');
const dataset=JSON.parse(fs.readFileSync(path.join(project,'data/dashboard.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(project,'evidence/WORD_REPORT_MANIFEST.json'),'utf8'));
if(dataset.country.id!=='BFA'||manifest.files.length!==dataset.territories.length)throw Error('Incomplete BFA Word manifest');
for(let index=0;index<dataset.territories.length;index++){
  const entry=manifest.files[index];
  if(entry.index!==index||entry.territory_id!==dataset.territories[index].id||
     !fs.existsSync(path.join(project,'site',entry.path)))throw Error(`Word report mismatch at ${index}`);
}
const appPath=path.join(project,'site/assets/app.mjs');
let app=fs.readFileSync(appPath,'utf8');
const hook='function territorial() {';
const helper=`function bfaWordLink() {
  if(dataset.country.id!=='BFA')return '';
  const index=dataset.territories.findIndex(area=>area.id===state.selected);
  if(index<0)return '';
  const filename='area-'+String(index).padStart(4,'0')+'.docx';
  return '<a class="button" href="../exports/diagnostic/'+filename+'" download="Territorial Development Diagnostic - '+safeFilename(currentArea().name)+'.docx">Territorial Development Diagnostic Word</a>';
}
`;
if(!app.includes('function bfaWordLink()')){
  if(!app.includes(hook))throw Error('Territorial render hook not found');
  app=app.replace(hook,helper+hook);
}
const old="${button('diagnostic-csv','Full diagnostic data CSV')}</div>";
const next="${button('diagnostic-csv','Full diagnostic data CSV')}${bfaWordLink()}</div>";
if(!app.includes(next)){
  if(!app.includes(old))throw Error('Diagnostic output action hook not found');
  app=app.replace(old,next);
}
fs.writeFileSync(appPath,app);
console.log(`Linked ${manifest.files.length} BFA Word reports to the territorial page`);

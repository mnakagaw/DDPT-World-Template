#!/usr/bin/env node
// Check every adopted Qatar Census 2020 observation in all nine selected-area exports.
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {diagnosticCsv, diagnosticHtml, diagnosticMarkdown} from '../scaffold/site/diagnostic.mjs';
import {planningHtml, evidenceCsv, comparisonCsv, seriesCsv, observationsCsv} from '../scaffold/site/model.mjs';

const index = process.argv.indexOf('--project');
if (index < 0 || !process.argv[index + 1] || process.argv.length !== 4) throw new Error('Usage: node scripts/verify-qatar-census-2020-output.mjs --project <project>');
const project = path.resolve(process.argv[index + 1]);
const sha = value => createHash('sha256').update(value).digest('hex');
const dashboardBytes = await readFile(path.join(project,'data/dashboard.json'));
const data = JSON.parse(dashboardBytes);
const audit = JSON.parse(await readFile(path.join(project,'evidence/QAT_CENSUS2020_IMPORT_AUDIT.json')));
const manifest = JSON.parse(await readFile(path.join(project,audit.source_manifest)));
const receipt = manifest.receipts.find(row => row.file === 'Census_Final_Results.xlsx');
if (data.country.id !== 'QAT' || !receipt || receipt.sha256 !== audit.source_sha256 ||
    sha(await readFile(path.join(project,path.dirname(audit.source_manifest),receipt.file))) !== audit.source_sha256) {
  throw new Error('Official Qatar workbook receipt or candidate identity changed');
}
const areas = data.territories.filter(row => row.parent_id === 'QAT');
const indicators = data.indicators.filter(row => row.id.startsWith('QAT_CENSUS2020_'));
const observations = data.observations.filter(row => row.indicator_id.startsWith('QAT_CENSUS2020_'));
if (areas.length !== 8 || indicators.length !== 17 || observations.length !== 153 ||
    data.boundaries.features.length !== 0 || data.documents.length !== 0 || audit.adopted_direct_cells.length !== 153) {
  throw new Error('Qatar partial adoption scope changed');
}
const csvRows = csv => {
  const rows=[]; let row=[],cell='',quoted=false;
  for(let i=csv.charCodeAt(0)===0xfeff?1:0;i<csv.length;i++) {
    const c=csv[i];
    if(quoted) {if(c==='"'&&csv[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}
    else if(c==='"')quoted=true;else if(c===','){row.push(cell);cell='';}
    else if(c==='\n'){rows.push([...row,cell.replace(/\r$/,'')]);row=[];cell='';}else cell+=c;
  }
  if(row.length||cell)rows.push([...row,cell]);
  return rows.filter(row=>row.some(value=>value!==''));
};
const observationByKey = new Map(observations.map(row => [`${row.territory_id}/${row.indicator_id}`,row]));
for(const item of audit.adopted_direct_cells) {
  const sourceRow = observations.find(row => row.indicator_id === item.indicator_id && row.source_locator?.endsWith(`'${item.table}'!${item.cell}`));
  if(!sourceRow || sourceRow.value !== item.value || sourceRow.status !== 'observed' || sourceRow.provenance === 'calculated')
    throw new Error(`Dataset/source-coordinate mismatch: ${item.table}!${item.cell}`);
}
const out = path.join(project,'evidence/output-verification');
await mkdir(out,{recursive:true});
const checks=[];
for(const area of [data.territories.find(row=>row.id==='QAT'),...areas]) {
  const outputs={
    'diagnostic.csv': diagnosticCsv(data,area.id,'latest-available'),
    'diagnostic.html': diagnosticHtml(data,area.id,'latest-available'),
    'diagnostic.md': diagnosticMarkdown(data,area.id,'latest-available'),
    'planning.html': planningHtml(data,area.id,'latest-available','en'),
    'evidence.csv': evidenceCsv(data,area.id,'latest-available'),
  };
  const prefix=area.id.replaceAll(':','_');
  for(const [kind,content] of Object.entries(outputs))await writeFile(path.join(out,`${prefix}-${kind}`),content);
  const [head,...rows]=csvRows(outputs['diagnostic.csv']);
  const col=name=>{const at=head.indexOf(name);if(at<0)throw new Error(`Missing diagnostic field ${name}`);return at;};
  for(const indicator of indicators) {
    const expected=observationByKey.get(`${area.id}/${indicator.id}`);
    const overall=rows.filter(row=>row[col('Record scope')]==='overall'&&row[col('Indicator ID')]===indicator.id);
    const source=data.sources.find(row=>row.id===indicator.source_id);
    if(!expected||overall.length!==1||Number(overall[0][col('Value')])!==expected.value||
       overall[0][col('Period')]!=='2020'||overall[0][col('Status')]!=='observed'||
       overall[0][col('Value provenance')]!=='source_reported'||overall[0][col('Source URL')]!==source?.url)
      throw new Error(`Selected-area diagnostic mismatch: ${area.id}/${indicator.id}`);
    const within=rows.filter(row=>row[col('Record scope')]==='within_area'&&row[col('Indicator ID')]===indicator.id);
    if(within.length!==(area.id==='QAT'?8:0))throw new Error(`Comparison coverage mismatch: ${area.id}/${indicator.id}`);
    if(area.id==='QAT') {
      const [comparisonHead,...comparisonRows]=csvRows(comparisonCsv(data,{selected:'QAT',level:'adm1',metric:indicator.id,period:'2020'}));
      const ccol=name=>comparisonHead.indexOf(name);
      for(const child of areas) {
        const row=within.find(item=>item[col('Territory ID')]===child.id);
        const expectedChild=observationByKey.get(`${child.id}/${indicator.id}`);
        const comparison=comparisonRows.find(item=>item[ccol('Territory ID')]===child.id);
        if(!row||Number(row[col('Value')])!==expectedChild.value||row[col('Status')]!=='observed'||
           row[col('Value provenance')]!=='source_reported'||row[col('Comparable')]!=='true'||
           !comparison||Number(comparison[ccol('Value')])!==expectedChild.value||
           comparison[ccol('Value provenance')]!=='source_reported')
          throw new Error(`Internal comparison mismatch: ${child.id}/${indicator.id}`);
      }
    }
    const [seriesHead,...seriesRows]=csvRows(seriesCsv(data,area.id,indicator.id));
    const scol=name=>seriesHead.indexOf(name);
    if(seriesRows.length!==1||Number(seriesRows[0][scol('Value')])!==expected.value||
       seriesRows[0][scol('Status')]!=='observed'||seriesRows[0][scol('Value provenance')]!=='source_reported')
      throw new Error(`Series export mismatch: ${area.id}/${indicator.id}`);
  }
  if(!outputs['diagnostic.html'].includes(area.name)||!outputs['planning.html'].includes(area.name))
    throw new Error(`Selected-area heading absent: ${area.id}`);
  checks.push({area_id:area.id,diagnostic_csv_rows:rows.length,first_data_row:rows[0],last_data_row:rows.at(-1),
    output_sha256:Object.fromEntries(Object.entries(outputs).map(([kind,content])=>[kind,sha(content)]))});
}
const [allHead,...allRows]=csvRows(observationsCsv(data,['QAT',...areas.map(row=>row.id)]));
const acol=name=>allHead.indexOf(name);
const domestic=allRows.filter(row=>row[acol('Indicator ID')].startsWith('QAT_CENSUS2020_'));
if(domestic.length!==153||domestic.some(row=>row[acol('Status')]!=='observed'||row[acol('Value provenance')]!=='source_reported'))
  throw new Error('All-observations export changed');
const report={status:'partial_candidate_output_check',checked_at:new Date().toISOString(),
  dataset_sha256:sha(dashboardBytes),source_sha256:audit.source_sha256,checks,
  limitations:['Only 17 indicators from nine of 156 numbered source tables are adopted',
    'Official 2020 codes/polygons and current individual planning/fiscal documents unverified',
    'Browser download bytes, physical print, applicable acceptance scenarios and independent country audit pending']};
await writeFile(path.join(project,'evidence/QAT_OUTPUT_VERIFICATION.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(checks.map(row=>({area_id:row.area_id,rows:row.diagnostic_csv_rows})),null,2));

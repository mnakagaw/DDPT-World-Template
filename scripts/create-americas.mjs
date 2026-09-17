import {mkdir,lstat,writeFile,readFile,copyFile,cp,readdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {collectWorld} from '../lib/collect-world.mjs';
import {buildAmericas} from '../lib/americas-adapter.mjs';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {readTemplateReference} from './create-country.mjs';

const sha256=content=>createHash('sha256').update(content).digest('hex');
const posix=value=>value.split(path.sep).join('/');

async function walkFiles(directory){
  const files=[];
  async function walk(current){for(const entry of await readdir(current,{withFileTypes:true})){const target=path.join(current,entry.name);if(entry.isDirectory())await walk(target);else files.push(target);}}
  await walk(directory);return files;
}

async function attachRaw(source,projectRoot,relativePath,{receiptPath=null,rawFiles=null}={}){
  if(!source)return;
  const content=await readFile(path.join(projectRoot,...relativePath.split('/')));
  source.raw_path=relativePath;source.sha256=sha256(content);
  if(receiptPath)source.receipt_path=receiptPath;
  if(rawFiles)source.raw_files=rawFiles;
}

export async function importAmericasEvidence({dataset,outDir,centralAmericaProject,censusRawDir,unWppFile}){
  const summary={census_raw_files:0,wpp_raw_files:0,imported_evidence_files:0},byId=new Map(dataset.sources.map(source=>[source.id,source]));
  if(centralAmericaProject){
    const source=path.join(path.resolve(centralAmericaProject),'evidence'),target=path.join(outDir,'evidence','imported-central-america');
    await cp(source,target,{recursive:true,errorOnExist:true});summary.imported_evidence_files=(await walkFiles(target)).length;
  }
  if(censusRawDir){
    const sourceRoot=path.resolve(censusRawDir),targetRoot=path.join(outDir,'raw','central-america-census'),prefix='raw/central-america-census';
    await cp(sourceRoot,targetRoot,{recursive:true,errorOnExist:true});
    const receipt=JSON.parse(await readFile(path.join(sourceRoot,'receipt.json'),'utf8')),receiptPath=`${prefix}/receipt.json`;
    for(const entry of receipt.entries||[]){
      if(entry.status!=='acquired'||!entry.filename||!entry.source_id)continue;
      await attachRaw(byId.get(entry.source_id),outDir,`${prefix}/${posix(entry.filename)}`,{receiptPath});
    }
    for(const [id,file] of [['areadata-ca7-census-series','normalized-census.json'],['areadata-ca7-scope','manifest.snapshot.json']])await attachRaw(byId.get(id),outDir,`${prefix}/${file}`,{receiptPath});
    const municipalReceipt=JSON.parse(await readFile(path.join(sourceRoot,'HND','2013','municipal-receipt.json'),'utf8')),municipalReceiptPath=`${prefix}/HND/2013/municipal-receipt.json`;
    const rawFiles=(municipalReceipt.entries||[]).filter(entry=>entry.status==='acquired'&&entry.filename).map(entry=>({url:entry.final_url||entry.pdf_url,raw_path:`${prefix}/${posix(entry.filename)}`,sha256:entry.sha256,bytes:entry.bytes,retrieved_at:municipalReceipt.retrieved_at,status:'downloaded',receipt_path:municipalReceiptPath}));
    await attachRaw(byId.get('HND_C2013_MUNICIPAL_REPORT_COLLECTION'),outDir,`${prefix}/HND/2013/municipal-report-index.json`,{receiptPath:municipalReceiptPath,rawFiles});
    summary.census_raw_files=(await walkFiles(targetRoot)).length;
  }
  if(unWppFile){
    const input=path.resolve(unWppFile),filename=path.basename(input),targetDir=path.join(outDir,'raw','un-wpp2024'),target=path.join(targetDir,filename);
    await mkdir(targetDir,{recursive:true});await copyFile(input,target);
    const content=await readFile(target),info=await stat(target),rawPath=`raw/un-wpp2024/${filename}`,receiptPath='raw/un-wpp2024/receipt.json',source=byId.get('un-wpp2024-demographic-indicators-rev1');
    await writeFile(path.join(outDir,receiptPath),JSON.stringify({schema_version:'1.0',source_id:source?.id||null,url:source?.url||null,raw_path:rawPath,sha256:sha256(content),bytes:info.size,status:'copied_from_verified_evidence'},null,2)+'\n');
    await attachRaw(source,outDir,rawPath,{receiptPath});summary.wpp_raw_files=1;
  }
  await writeFile(path.join(outDir,'evidence','SOURCE_EVIDENCE_IMPORT.json'),JSON.stringify({...summary,created_at:new Date().toISOString()},null,2)+'\n');
  return summary;
}

export async function createAmericas({out,sourceDir,centralAmericaProject,centralAmericaRaw,unWppFile,unPopulationData='data/international/un-wpp2024-americas-population.json',startYear,endYear,collect=collectWorld,generate=generateSite}={}){
  const outDir=path.resolve(out||'generated/americas');
  try{await lstat(outDir);throw new Error(`Output already exists; choose a new directory: ${outDir}`);}catch(error){if(error.code!=='ENOENT')throw error;}
  await mkdir(path.join(outDir,'raw'),{recursive:true});
  try{
    const world=await collect({rawDir:path.join(outDir,'raw'),sourceDir:sourceDir?path.resolve(sourceDir):undefined,startYear,endYear,onProgress:message=>console.log(message)});
    const centralAmerica=centralAmericaProject?JSON.parse(await readFile(path.resolve(centralAmericaProject,'data/dashboard.json'),'utf8')):null;
    const unPopulation=unPopulationData?JSON.parse(await readFile(path.resolve(unPopulationData),'utf8')):null;
    const dataset=buildAmericas(world,{centralAmerica,unPopulation});
    await mkdir(path.join(outDir,'data'));await mkdir(path.join(outDir,'evidence'));
    await importAmericasEvidence({dataset,outDir,centralAmericaProject:centralAmericaProject?path.resolve(centralAmericaProject):null,censusRawDir:centralAmericaRaw?path.resolve(centralAmericaRaw):null,unWppFile:unWppFile?path.resolve(unWppFile):null});
    const validation=validateDataset(dataset),content=JSON.stringify(dataset,null,2)+'\n';
    await writeFile(path.join(outDir,'data/dashboard.json'),content);
    await writeFile(path.join(outDir,'evidence/validation.json'),JSON.stringify({...validation,dataset_sha256:sha256(content),checked_at:new Date().toISOString()},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/AMERICAS_SCOPE.json'),JSON.stringify({scope_id:'M49:019',country_area_count:dataset.analysis.coverage.country_area_count,un_wpp_country_area_count:dataset.analysis.coverage.un_wpp_country_area_count,un_wpp_missing_country_area_ids:dataset.analysis.coverage.un_wpp_missing_country_area_ids,census_integrated_country_ids:dataset.analysis.coverage.census_integrated_country_ids,census_integrated_territory_count:dataset.analysis.coverage.census_integrated_territory_count,generated_at:dataset.generated_at,world_source_dir:sourceDir?path.resolve(sourceDir):null,central_america_project:centralAmericaProject?path.resolve(centralAmericaProject):null,un_population_data:unPopulationData?path.resolve(unPopulationData):null},null,2)+'\n');
    await writeFile(path.join(outDir,'evidence/ACCEPTANCE.md'),await readFile(new URL('../templates/REGIONAL_ACCEPTANCE.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'evidence/INDEPENDENT_AUDIT.md'),await readFile(new URL('../templates/REGIONAL_INDEPENDENT_AUDIT.md',import.meta.url),'utf8'));
    await writeFile(path.join(outDir,'evidence/DELIVERY.json'),JSON.stringify({
      schema_version:'0.1',project:'AreaData Americas',build_status:'candidate',
      scope:{id:'M49:019',country_area_count:dataset.analysis.coverage.country_area_count,classification:'UN M49 Americas with a documented display-only Central America + Caribbean navigation group'},
      checks:Object.fromEntries(['scope_registry','aggregation_semantics','country_local_separation','browser_smoke','hierarchy_reset','download_exports','language_review','reproducible_build'].map(key=>[key,{status:'pending',evidence_file:'evidence/ACCEPTANCE.md'}])),
      independent_audit:{status:'pending',file:'evidence/INDEPENDENT_AUDIT.md'},
      release:{github_status:'pending',hosting_status:'blocked_by_audit',public_status:'not_published'}
    },null,2)+'\n');
    if(validation.errors.length)throw new Error(`Americas dataset failed validation: ${validation.errors.join('; ')}`);
    if(!dataset.observations.some(row=>row.status==='observed'))throw new Error('No numeric observations collected.');
    await generate({dataset,outDir});
    await writeFile(path.join(outDir,'TEMPLATE_REFERENCE.json'),JSON.stringify(await readTemplateReference(),null,2)+'\n');
    await copyFile(new URL('../docs/WORLD_ADAPTER.md',import.meta.url),path.join(outDir,'WORLD_ADAPTER.md'));
    await writeFile(path.join(outDir,'HANDOFF.md'),`# AreaData Americas\n\nThis candidate covers all ${dataset.analysis.coverage.country_area_count} countries and areas in UN M49 Americas (019). Navigation uses Northern America, South America and the documented Central America + Caribbean display group. UN WPP population is integrated for ${dataset.analysis.coverage.un_wpp_country_area_count} registry entries; ${dataset.analysis.coverage.un_wpp_missing_country_area_ids.join(', ') || 'none'} remain missing. Official census population and domestic hierarchy are integrated only for ${dataset.analysis.coverage.census_integrated_country_ids.join(', ') || 'no countries yet'}; missing integration does not mean no census exists.\n\nNo exact source-reported Americas total has been adopted. Regional calculations require complete same-period membership coverage. Planning laws and materials remain country-adapter work.\n\nComplete evidence/ACCEPTANCE.md, change only evidence-backed checks in evidence/DELIVERY.json to passed, and run:\n\n    node scripts/verify-regional-delivery.mjs --project ${outDir}\n\nIndependent audit status: PENDING. A separate task must inspect the actual sources, data, browser behavior and downloads without editing the candidate. Do not publish until it records ACCEPT and the publication gate passes:\n\n    node scripts/verify-regional-delivery.mjs --project ${outDir} --require-publishable\n`);
    console.log(`Created: ${outDir}`);return {outDir,dataset,validation};
  }catch(error){await writeFile(path.join(outDir,'COLLECTION_FAILED.txt'),`${new Date().toISOString()}\n${error.message}\n`);throw error;}
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['out','source-dir','central-america-project','central-america-raw','un-wpp-file','un-population-data','start-year','end-year']);if(args.help)console.log('node scripts/create-americas.mjs --source-dir previous-world/raw --central-america-project previous-central-america --central-america-raw acquired-census-directory --un-wpp-file WPP.xlsx --un-population-data data/international/un-wpp2024-americas-population.json --out generated/americas');else await createAmericas({out:args.out,sourceDir:args['source-dir'],centralAmericaProject:args['central-america-project'],centralAmericaRaw:args['central-america-raw'],unWppFile:args['un-wpp-file'],unPopulationData:args['un-population-data']||undefined,startYear:args['start-year']===undefined?undefined:Number(args['start-year']),endYear:args['end-year']===undefined?undefined:Number(args['end-year'])});}catch(error){reportError(error);}
}

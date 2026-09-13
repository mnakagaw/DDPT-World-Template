import {readFile, writeFile, mkdir, access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, relative, dirname, isAbsolute, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateDataset} from '../../lib/validate.mjs';

const exampleDir=dirname(fileURLToPath(import.meta.url));
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const json=bytes=>JSON.parse(bytes.toString('utf8'));

function inside(root,path) {
  if(typeof path!=='string'||!path||isAbsolute(path))throw new Error('Expected a relative evidence path');
  const target=resolve(root,path),rel=relative(root,target);
  if(rel==='..'||rel.startsWith('..\\')||rel.startsWith('../')||isAbsolute(rel))throw new Error(`Evidence path escapes source directory: ${path}`);
  return target;
}
async function verifiedFile(root,path,expectedHash) {
  if(!/^[a-f0-9]{64}$/.test(expectedHash||''))throw new Error(`Missing SHA-256 for ${path}`);
  const bytes=await readFile(inside(root,path));
  if(sha256(bytes)!==expectedHash)throw new Error(`Original SHA-256 mismatch: ${path}`);
  return bytes;
}
async function absent(path) {
  try {await access(path);}catch(error){if(error.code==='ENOENT')return;throw error;}
  throw new Error(`Output already exists; choose a new directory: ${path}`);
}

/** Offline adapter: original evidence and pinned population must pass their receipts. */
export async function buildExamples({sourceDir,outDir}) {
  if(!sourceDir||!outDir)throw new Error('sourceDir and outDir are required');
  const sourceRoot=resolve(sourceDir),outputRoot=resolve(outDir);
  const inputBytes=await readFile(join(exampleDir,'audited-input.json'));
  const input=json(inputBytes);
  if(input.input_version!=='1'||!Array.isArray(input.countries)||!Array.isArray(input.sources))throw new Error('Unsupported audited input');
  if(/https?:\/\/mail\.google\.com/i.test(inputBytes.toString('utf8')))throw new Error('Personal-mail links must not enter datasets');
  const populationRoot=join(exampleDir,'population');
  const receipts=json(await readFile(join(populationRoot,'receipts.json')));
  const populationFiles=new Map();
  for(const receipt of receipts)populationFiles.set(receipt.name,await verifiedFile(populationRoot,receipt.name,receipt.sha256));
  const metadataReceipt=receipts.find(row=>row.name==='population-metadata.json');
  const metadata=json(populationFiles.get('population-metadata.json'))?.[1]?.find(row=>row.id==='SP.POP.TOTL');
  if(!metadataReceipt||!metadata?.sourceNote||!metadata?.name)throw new Error('Population definition is absent');
  const originals=new Map();
  for(const source of input.sources)originals.set(source.raw_path,await verifiedFile(sourceRoot,source.raw_path,source.sha256));
  const prepared=[];
  for(const config of input.countries) {
    if(!['dom','uga'].includes(config.out_name))throw new Error('Unexpected example destination');
    const destination=inside(outputRoot,config.out_name);
    await absent(destination);
    const populationName=`${config.id}-population.json`;
    const populationReceipt=receipts.find(row=>row.name===populationName);
    const payload=json(populationFiles.get(populationName));
    if(!populationReceipt||payload?.[0]?.pages!==1||!Array.isArray(payload?.[1]))throw new Error(`Incomplete population response for ${config.id}`);
    const observations=payload[1].filter(row=>row.countryiso3code===config.id&&row.indicator?.id==='SP.POP.TOTL'&&/^\d{4}$/.test(row.date)&&typeof row.value==='number'&&Number.isFinite(row.value)).sort((a,b)=>Number(b.date)-Number(a.date));
    if(observations.length!==1||payload[1].length!==1)throw new Error(`Expected one latest non-null population observation for ${config.id}`);
    const observation=observations[0];
    if(observation.country?.id!==config.iso2)throw new Error(`Population country mismatch for ${config.id}`);
    const sourceIds=new Set(config.source_ids);
    const sources=input.sources.filter(source=>sourceIds.has(source.id));
    if(sources.length!==sourceIds.size)throw new Error(`Missing planning source for ${config.id}`);
    // The audited identity stays independent of the document assignment, including
    // authorities whose official code and historical boundary are both unknown.
    for(const doc of config.documents)if(doc.territory_match && doc.territory_match.territory_id!==doc.territory_id)throw new Error(`Audited territory assignment mismatch: ${doc.id}`);
    const populationSource={id:'wb-population',name:'World Bank WDI - Population, total',publisher:'World Bank',url:populationReceipt.url,retrieved_at:populationReceipt.retrieved_at,reference_period:observation.date,status:'ready',geographic_level:'national',raw_path:`raw/${populationName}`,sha256:populationReceipt.sha256,license:'World Bank dataset terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets',note:`Pinned mrnev=1 response; API lastupdated ${payload[0].lastupdated}. Population is a national midyear estimate; it is not allocated to local authorities.`};
    const metadataSource={id:'wb-population-metadata',name:'World Bank SP.POP.TOTL indicator metadata',publisher:'World Bank',url:metadataReceipt.url,retrieved_at:metadataReceipt.retrieved_at,reference_period:'Metadata retrieved '+metadataReceipt.retrieved_at.slice(0,10),status:'ready',geographic_level:'national',raw_path:'raw/population-metadata.json',sha256:metadataReceipt.sha256,license:populationSource.license,note:`${metadata.sourceOrganization} API unit is empty; the count unit is labelled people. The original definition is retained without changing its population scope.`};
    const national={id:config.id,name:config.name,level:'national',type:'country',parent_id:null,official_code:null,code_system:'World Bank economy code',boundary_version:null};
    const latestEvidence=[input.audit_checked_at,...receipts.map(row=>row.retrieved_at)].sort().at(-1);
    const dataset={
      schema_version:'0.2',generated_at:latestEvidence,
      country:{id:config.id,iso2:config.iso2,name:config.name,requested_name:config.name,locale:'en',national_territory_id:config.id,geography_note:'No boundaries were acquired for this planning evidence example. Local authorities are identified by the cited source documents; official geographic-code crosswalks and historical boundaries are unverified. National membership is recorded only; no current-boundary aggregation or synthetic map is supplied.'},
      territories:[national,...config.territories],
      indicators:[{id:'SP.POP.TOTL',name:metadata.name,theme:'Population',unit:'people',definition:metadata.sourceNote,source_id:'wb-population',aggregation:'none',measurement_method:'source_reported'}],
      observations:[{territory_id:config.id,indicator_id:'SP.POP.TOTL',period:observation.date,value:observation.value,status:'observed',source_id:'wb-population'}],
      sources:[populationSource,metadataSource,...sources],boundaries:{type:'FeatureCollection',features:[]},documents:config.documents,planning:config.planning,
      gaps:[{category:'boundaries',status:'not_collected',detail:'No boundary originals were acquired. The map remains empty; no placeholder polygons are used.',next_action:'Acquire and reconcile dated official boundaries if a map is needed.'},{category:'subnational_statistics',status:'not_collected',detail:'Only one national population observation is supplied. Local statistics are absent and national data must not be copied into them.',next_action:'Collect exact local observations and verify their territory and period.'},{category:'source_terms',status:'unverified',detail:'Re-use licences for local planning, evaluation and fiscal originals were not verified. Locally saved originals are not published or included in Git.',next_action:'Review each publisher’s reuse terms before redistributing original documents.'},...config.gaps],
      collection:{status:'partial',adapters:['audited-planning-evidence','pinned-world-bank-population'],notes:['Real, bounded planning evidence for local QA; not a completed country dashboard.','The offline adapter verifies original SHA-256 receipts before creating either example.','generated_at identifies the pinned evidence edition, so unchanged inputs reproduce identical datasets.','All local legal approval statuses remain unverified.']}
    };
    const validation=validateDataset(dataset);
    if(validation.errors.length)throw new Error(`${config.id} validation failed: ${validation.errors.join('; ')}`);
    prepared.push({destination,dataset,validation,rawFiles:new Map([...sources.map(source=>[source.raw_path,originals.get(source.raw_path)]),[populationSource.raw_path,populationFiles.get(populationName)],[metadataSource.raw_path,populationFiles.get('population-metadata.json')]])});
  }
  // All originals, destinations and datasets pass preflight before output mutation.
  await mkdir(outputRoot,{recursive:true});
  const results=[];
  for(const {destination,dataset,validation,rawFiles} of prepared) {
    await mkdir(destination); // EEXIST prevents concurrent overwrites.
    await mkdir(join(destination,'data'));
    for(const [path,bytes] of rawFiles) {
      const target=inside(destination,path);await mkdir(dirname(target),{recursive:true});
      await writeFile(target,bytes,{flag:'wx'});
    }
    const bytes=Buffer.from(JSON.stringify(dataset,null,2)+'\n');
    await writeFile(join(destination,'data','dashboard.json'),bytes,{flag:'wx'});
    const result={country:dataset.country.id,path:destination,dataset_sha256:sha256(bytes),audited_input_sha256:sha256(inputBytes),original_count:rawFiles.size,documents:dataset.documents.length,observations:dataset.observations.length,boundaries:0,validation};
    await writeFile(join(destination,'data','example-receipt.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
    results.push(result);
  }
  return results;
}

async function main() {
  const options={};const args=process.argv.slice(2);
  if(args.length===1&&args[0]==='--help'){console.log('node examples/planning-evidence/build-examples.mjs --source-dir <saved-originals> --out <new-output-root>');return;}
  for(let i=0;i<args.length;i+=2) {
    if(!['--source-dir','--out'].includes(args[i])||!args[i+1]||args[i+1].startsWith('--'))throw new Error('Use --source-dir <saved-originals> --out <new-output-root>');
    const key=args[i]==='--source-dir'?'sourceDir':'outDir';if(options[key])throw new Error(`Duplicate option ${args[i]}`);options[key]=args[i+1];
  }
  console.log(JSON.stringify(await buildExamples(options),null,2));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(error=>{console.error(error.message);process.exitCode=1;});

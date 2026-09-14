import {createHash} from 'node:crypto';
import {lstat,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

const REDIRECT_CODES=new Set([301,302,303,307,308]);
const SUPPORTED_FORMATS=new Set(['xlsx','pdf','csv','json']);

export async function loadCensusSourceManifest(file=new URL('../config/central-america-census-sources.json',import.meta.url)) {
  const manifest=JSON.parse(await readFile(file,'utf8'));
  validateCensusSourceManifest(manifest);
  return manifest;
}

export function validateCensusSourceManifest(manifest) {
  if(!manifest||!Array.isArray(manifest.sources)||!manifest.sources.length)throw new Error('Census source manifest needs at least one source.');
  const ids=new Set(),files=new Set();
  for(const source of manifest.sources){
    if(!source.id||ids.has(source.id))throw new Error(`Duplicate or missing census source id: ${source.id||'(missing)'}`);ids.add(source.id);
    if(!/^[A-Z]{3}$/.test(source.country_id||''))throw new Error(`Invalid country_id for ${source.id}`);
    if(!SUPPORTED_FORMATS.has(source.format))throw new Error(`Unsupported format for ${source.id}: ${source.format}`);
    const url=new URL(source.download_url);
    if(url.protocol!=='https:')throw new Error(`Census source must use HTTPS: ${source.id}`);
    if(!Array.isArray(source.allowed_hosts)||!source.allowed_hosts.includes(url.hostname))throw new Error(`Initial host is not allowlisted for ${source.id}`);
    const normalized=path.posix.normalize(String(source.filename||'').replaceAll('\\','/'));
    if(!normalized||normalized.startsWith('../')||normalized.includes('/../')||path.posix.isAbsolute(normalized))throw new Error(`Unsafe filename for ${source.id}`);
    if(files.has(normalized))throw new Error(`Duplicate census destination: ${normalized}`);files.add(normalized);
  }
  return manifest;
}

function approvedUrl(value,source){
  const url=new URL(value);
  if(url.protocol!=='https:'||!source.allowed_hosts.includes(url.hostname))throw new Error(`Unapproved download host for ${source.id}: ${url.hostname}`);
  return url;
}

async function fetchApproved(source,fetchImpl,maxRedirects=5,signal){
  let current=approvedUrl(source.download_url,source);
  for(let redirectCount=0;redirectCount<=maxRedirects;redirectCount++){
    const response=await fetchImpl(current,{redirect:'manual',signal,headers:{'user-agent':'AreaData census evidence collector/0.2','accept':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/pdf,text/csv,application/json;q=0.9,*/*;q=0.1'}});
    if(REDIRECT_CODES.has(response.status)){
      if(redirectCount===maxRedirects)throw new Error(`Too many redirects for ${source.id}`);
      const location=response.headers.get('location');
      if(!location)throw new Error(`Redirect without Location for ${source.id}`);
      current=approvedUrl(new URL(location,current),source);continue;
    }
    if(!response.ok)throw new Error(`HTTP ${response.status} for ${source.id}`);
    return {response,finalUrl:current.href,redirectCount};
  }
  throw new Error(`Unable to fetch ${source.id}`);
}

async function responseBytes(response,maxBytes){
  const length=Number(response.headers.get('content-length'));
  if(Number.isFinite(length)&&length>maxBytes)throw new Error(`Content-Length ${length} exceeds ${maxBytes} byte limit`);
  if(!response.body||typeof response.body.getReader!=='function'){
    const bytes=new Uint8Array(await response.arrayBuffer());
    if(bytes.byteLength>maxBytes)throw new Error(`Response exceeds ${maxBytes} byte limit`);
    return bytes;
  }
  const reader=response.body.getReader(),chunks=[];let total=0;
  while(true){
    const {done,value}=await reader.read();if(done)break;
    total+=value.byteLength;if(total>maxBytes){await reader.cancel();throw new Error(`Response exceeds ${maxBytes} byte limit`);}chunks.push(value);
  }
  const bytes=new Uint8Array(total);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}return bytes;
}

function startsWith(bytes,ascii){return ascii.split('').every((character,index)=>bytes[index]===character.charCodeAt(0));}
export function validateFileSignature(bytes,format){
  if(format==='xlsx'&&!startsWith(bytes,'PK'))throw new Error('XLSX response does not have a ZIP signature');
  if(format==='pdf'&&!startsWith(bytes,'%PDF-'))throw new Error('PDF response does not have a PDF signature');
  if(format==='json'){try{JSON.parse(new TextDecoder().decode(bytes));}catch{throw new Error('JSON response is invalid');}}
  if(format==='csv'){
    const prefix=new TextDecoder().decode(bytes.slice(0,512)).trimStart().toLowerCase();
    if(prefix.startsWith('<!doctype html')||prefix.startsWith('<html'))throw new Error('CSV response appears to be HTML');
  }
}

async function assertAbsent(target){try{await lstat(target);throw new Error(`Output already exists; choose a new directory: ${target}`);}catch(error){if(error.code!=='ENOENT')throw error;}}

async function loadReuseEvidence(reuseDir){
  if(!reuseDir)return null;
  const root=path.resolve(reuseDir),receipt=JSON.parse(await readFile(path.join(root,'receipt.json'),'utf8'));
  return {root,receipt,byId:new Map(receipt.entries.map(entry=>[entry.source_id,entry]))};
}

async function reuseSourceBytes(source,reuse,maxBytes){
  if(!reuse)return null;
  const prior=reuse.byId.get(source.id);
  if(!prior||prior.status!=='acquired')return null;
  if(prior.filename!==source.filename||prior.requested_url!==source.download_url)throw new Error(`Reuse evidence does not match the current manifest for ${source.id}`);
  const file=path.join(reuse.root,...source.filename.split('/')),bytes=new Uint8Array(await readFile(file));
  if(bytes.byteLength>maxBytes)throw new Error(`Reused file exceeds ${maxBytes} byte limit for ${source.id}`);
  validateFileSignature(bytes,source.format);
  const digest=createHash('sha256').update(bytes).digest('hex');
  if(digest!==prior.sha256)throw new Error(`Reuse receipt hash mismatch for ${source.id}`);
  return {bytes,prior};
}

export async function collectCensusSources({outDir,manifest,fetchImpl=fetch,now=()=>new Date(),reuseDir}={}){
  if(!outDir)throw new Error('outDir is required');
  manifest=validateCensusSourceManifest(manifest||await loadCensusSourceManifest());
  const target=path.resolve(outDir);await assertAbsent(target);const reuse=await loadReuseEvidence(reuseDir);await mkdir(target,{recursive:true});
  const receipt={schema_version:'1.0',scope_id:manifest.scope_id,retrieved_at:now().toISOString(),collector:'AreaData census evidence collector 0.2',entries:[]};
  for(const source of manifest.sources){
    const entry={source_id:source.id,country_id:source.country_id,census_year:source.census_year,title:source.title,publisher:source.publisher,catalog_url:source.catalog_url,requested_url:source.download_url,filename:source.filename,format:source.format,role:source.role,required:source.required===true,redistribution_status:source.redistribution_status,adoption_status:source.adoption_status,status:'failed'};
    try{
      const maxBytes=source.max_bytes||manifest.default_max_bytes;
      const reused=await reuseSourceBytes(source,reuse,maxBytes);
      let bytes,finalUrl,redirectCount,contentType,reusedFrom=null;
      if(reused){
        ({bytes}=reused);finalUrl=reused.prior.final_url;redirectCount=reused.prior.redirect_count;contentType=reused.prior.content_type;
        reusedFrom={source_receipt_retrieved_at:reuse.receipt.retrieved_at,source_sha256:reused.prior.sha256};
      }else{
        const timeoutMs=source.timeout_ms||manifest.default_timeout_ms||120000,signal=AbortSignal.timeout(timeoutMs);
        const fetched=await fetchApproved(source,fetchImpl,5,signal);finalUrl=fetched.finalUrl;redirectCount=fetched.redirectCount;
        contentType=fetched.response.headers.get('content-type')||null;bytes=await responseBytes(fetched.response,maxBytes);validateFileSignature(bytes,source.format);
      }
      const file=path.join(target,...source.filename.split('/'));await mkdir(path.dirname(file),{recursive:true});await writeFile(file,bytes,{flag:'wx'});
      Object.assign(entry,{status:'acquired',final_url:finalUrl,redirect_count:redirectCount,content_type:contentType,bytes:bytes.byteLength,sha256:createHash('sha256').update(bytes).digest('hex')});
      if(reusedFrom)entry.reused_from=reusedFrom;
    }catch(error){entry.error=error.message;}
    receipt.entries.push(entry);
  }
  receipt.summary={requested:receipt.entries.length,acquired:receipt.entries.filter(entry=>entry.status==='acquired').length,failed:receipt.entries.filter(entry=>entry.status==='failed').length,required_failed:receipt.entries.filter(entry=>entry.required&&entry.status==='failed').length};
  await writeFile(path.join(target,'manifest.snapshot.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  await writeFile(path.join(target,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  return {outDir:target,receipt};
}

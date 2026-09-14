import {createHash} from 'node:crypto';
import {lstat,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

const API_ROOT='https://ine.gob.hn/wp-json/wp/v2';
const MUNICIPAL_PARENT_CATEGORY=66;
const ALLOWED_HOST='ine.gob.hn';

const cleanText=value=>String(value||'').replace(/<[^>]*>/g,'').replaceAll('&#8211;','–').replaceAll('&#8217;',"'").replaceAll('&amp;','&').trim();

async function fetchJson(url,fetchImpl){
  const response=await fetchImpl(url,{signal:AbortSignal.timeout(60000),headers:{'user-agent':'AreaData Honduras census source discovery/0.1','accept':'application/json'}});
  if(!response.ok)throw new Error(`HTTP ${response.status}: ${url}`);
  return response.json();
}

export function normalizeHondurasPdfUrl(value){
  const url=new URL(String(value).replaceAll('&amp;','&'));
  if(url.hostname==='temp.ine.gob.hn')url.hostname=ALLOWED_HOST;
  if(url.protocol!=='https:'||url.hostname!==ALLOWED_HOST||!url.pathname.toLowerCase().endsWith('.pdf'))throw new Error(`Unapproved Honduras municipal PDF URL: ${url.href}`);
  return url.href;
}

export async function discoverHondurasMunicipalReports({fetchImpl=fetch,expectedCount=298}={}){
  const categoryUrl=`${API_ROOT}/categories?parent=${MUNICIPAL_PARENT_CATEGORY}&per_page=100&_fields=id,name,slug,count`;
  const categories=await fetchJson(categoryUrl,fetchImpl);
  const groups=await Promise.all(categories.map(async category=>{
    const postsUrl=`${API_ROOT}/posts?categories=${category.id}&per_page=100&_fields=id,link,title,content`;
    const posts=await fetchJson(postsUrl,fetchImpl);
    return posts.filter(post=>/año 2013/i.test(cleanText(post.title?.rendered))).map(post=>{
      const pdfs=[...new Set([...String(post.content?.rendered||'').matchAll(/href="([^"]+\.pdf)"/gi)].map(match=>normalizeHondurasPdfUrl(match[1])))];
      if(pdfs.length!==1)throw new Error(`Expected one municipal PDF for post ${post.id}; found ${pdfs.length}`);
      return {department:cleanText(category.name),department_category_id:category.id,post_id:post.id,title:cleanText(post.title?.rendered),post_url:post.link,pdf_url:pdfs[0]};
    });
  }));
  const byPdf=new Map();
  for(const report of groups.flat()){
    const existing=byPdf.get(report.pdf_url);
    if(!existing){byPdf.set(report.pdf_url,{...report,category_departments:[report.department],discovery_aliases:[]});continue;}
    if(existing.post_id!==report.post_id||existing.title!==report.title)existing.discovery_aliases.push({post_id:report.post_id,title:report.title,post_url:report.post_url,department:report.department,department_category_id:report.department_category_id});
    existing.category_departments=[...new Set([...existing.category_departments,report.department])];
  }
  const reports=[...byPdf.values()].sort((a,b)=>a.department.localeCompare(b.department,'es')||a.title.localeCompare(b.title,'es'));
  if(expectedCount!==null&&reports.length!==expectedCount)throw new Error(`Expected ${expectedCount} Honduras 2013 municipal reports; discovered ${reports.length}`);
  if(new Set(reports.map(report=>report.pdf_url)).size!==reports.length)throw new Error('Honduras municipal report discovery returned duplicate PDF URLs after normalization');
  return {schema_version:'1.0',country_id:'HND',census_year:'2013',catalog_url:'https://ine.gob.hn/censo-de-poblacion-y-vivienda-2013/',api_root:API_ROOT,category_count:categories.length,report_count:reports.length,reports};
}

async function assertAbsent(target){try{await lstat(target);throw new Error(`Output already exists: ${target}`);}catch(error){if(error.code!=='ENOENT')throw error;}}

async function fetchPdf(report,fetchImpl,maxBytes){
  const response=await fetchImpl(report.pdf_url,{signal:AbortSignal.timeout(90000),headers:{'user-agent':'AreaData Honduras census evidence collector/0.1','accept':'application/pdf'}});
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  const length=Number(response.headers.get('content-length'));if(Number.isFinite(length)&&length>maxBytes)throw new Error(`Content-Length ${length} exceeds ${maxBytes}`);
  const bytes=new Uint8Array(await response.arrayBuffer());if(bytes.byteLength>maxBytes)throw new Error(`Response exceeds ${maxBytes}`);
  if(new TextDecoder('ascii').decode(bytes.slice(0,5))!=='%PDF-')throw new Error('Response does not have a PDF signature');
  return {bytes,content_type:response.headers.get('content-type')||null,final_url:response.url||report.pdf_url};
}

export async function collectHondurasMunicipalReports({rootDir,index,fetchImpl=fetch,concurrency=6,maxBytes=10485760,now=()=>new Date(),reuseDir}={}){
  if(!rootDir)throw new Error('rootDir is required');
  index=index||await discoverHondurasMunicipalReports({fetchImpl});
  const base=path.join(path.resolve(rootDir),'HND','2013'),out=path.join(base,'municipal-reports'),indexFile=path.join(base,'municipal-report-index.json');await assertAbsent(out);await mkdir(out,{recursive:true});
  try{
    const existing=JSON.parse(await readFile(indexFile,'utf8'));
    if(existing.report_count!==index.report_count||existing.reports.map(row=>row.pdf_url).join('\n')!==index.reports.map(row=>row.pdf_url).join('\n'))throw new Error('Existing Honduras municipal report index differs from current discovery');
  }catch(error){if(error.code==='ENOENT')await writeFile(indexFile,JSON.stringify(index,null,2)+'\n',{flag:'wx'});else throw error;}
  let reuse=null;
  if(reuseDir){
    const reuseBase=path.join(path.resolve(reuseDir),'HND','2013'),receipt=JSON.parse(await readFile(path.join(reuseBase,'municipal-receipt.json'),'utf8'));
    reuse={byUrl:new Map(receipt.entries.filter(entry=>entry.status==='acquired').map(entry=>[entry.pdf_url,entry])),retrieved_at:receipt.retrieved_at};
  }
  const entries=new Array(index.reports.length);let cursor=0;
  async function worker(){
    while(true){
      const current=cursor++;if(current>=index.reports.length)return;const report=index.reports[current];
      const basename=path.basename(new URL(report.pdf_url).pathname),filename=`HND/2013/municipal-reports/${decodeURIComponent(basename)}`;
      const entry={...report,filename,status:'failed'};
      try{
        let downloaded,reusedFrom=null;const prior=reuse?.byUrl.get(report.pdf_url);
        if(prior){
          const priorFile=path.join(path.resolve(reuseDir),...prior.filename.split('/')),bytes=new Uint8Array(await readFile(priorFile)),digest=createHash('sha256').update(bytes).digest('hex');
          if(digest!==prior.sha256||new TextDecoder('ascii').decode(bytes.slice(0,5))!=='%PDF-')throw new Error(`Municipal reuse hash or signature mismatch for ${report.pdf_url}`);
          downloaded={bytes,content_type:prior.content_type,final_url:prior.final_url};reusedFrom={source_receipt_retrieved_at:reuse.retrieved_at,source_sha256:prior.sha256};
        }else downloaded=await fetchPdf(report,fetchImpl,maxBytes);
        const file=path.join(path.resolve(rootDir),...filename.split('/'));
        await writeFile(file,downloaded.bytes,{flag:'wx'});Object.assign(entry,{status:'acquired',final_url:downloaded.final_url,content_type:downloaded.content_type,bytes:downloaded.bytes.byteLength,sha256:createHash('sha256').update(downloaded.bytes).digest('hex')});
        if(reusedFrom)entry.reused_from=reusedFrom;
      }catch(error){entry.error=error.message;}
      entries[current]=entry;
    }
  }
  await Promise.all(Array.from({length:Math.max(1,Math.min(concurrency,index.reports.length))},worker));
  const receipt={schema_version:'1.0',country_id:'HND',census_year:'2013',retrieved_at:now().toISOString(),collector:'AreaData Honduras municipal census evidence collector 0.1',entries};
  receipt.summary={requested:entries.length,acquired:entries.filter(entry=>entry.status==='acquired').length,failed:entries.filter(entry=>entry.status==='failed').length};
  await writeFile(path.join(base,'municipal-receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  return receipt;
}

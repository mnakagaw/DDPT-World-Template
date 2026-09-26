import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {parseM49} from '../lib/collect-world.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

const URL='https://unstats.un.org/unsd/methodology/m49/overview/';
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');

export async function verifyAsiaM49(project,{fetchImpl=fetch}={}){
  const root=path.resolve(project),data=JSON.parse(await readFile(path.join(root,'data/dashboard.json'),'utf8'));
  if(data.country?.id!=='ASI')throw new Error('Expected Asia candidate');
  const response=await fetchImpl(URL);
  if(!response.ok)throw new Error(`UN M49 returned HTTP ${response.status}`);
  const bytes=Buffer.from(await response.arrayBuffer());
  const official=parseM49(bytes.toString('utf8')).filter(row=>row.region.code==='142');
  const candidate=data.territories.filter(area=>area.type==='country');
  const byId=new Map(candidate.map(area=>[area.id,area]));
  const missing=official.filter(row=>!byId.has(row.id)).map(row=>row.id);
  const extra=candidate.filter(area=>!official.some(row=>row.id===area.id)).map(area=>area.id);
  const mismatches=official.filter(row=>{const area=byId.get(row.id);return area&&(area.official_code!==row.m49||area.m49_membership?.subregion?.code!==row.subregion.code);})
    .map(row=>row.id);
  const receipt={source_url:URL,retrieved_at:new Date().toISOString(),http_status:response.status,
    content_type:response.headers.get('content-type'),raw_sha256:sha256(bytes),raw_bytes:bytes.length,
    official_asia_country_area_count:official.length,candidate_country_area_count:candidate.length,
    missing,extra,m49_or_subregion_mismatches:mismatches,
    official_rows:official.map(row=>({id:row.id,m49:row.m49,subregion:row.subregion.code}))};
  await mkdir(path.join(root,'raw'),{recursive:true});
  await writeFile(path.join(root,'raw/un-m49-live.html'),bytes);
  await writeFile(path.join(root,'evidence/ASIA_M49_LIVE_CHECK.json'),JSON.stringify(receipt,null,2)+'\n');
  if(missing.length||extra.length||mismatches.length)throw new Error('Asia candidate differs from current official UN M49; see ASIA_M49_LIVE_CHECK.json');
  return receipt;
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project']);if(!args.project)throw new Error('Use --project <Asia project>');
    const result=await verifyAsiaM49(args.project);console.log(`Official UN M49 Asia: ${result.official_asia_country_area_count} countries/areas; candidate matches`);
  }catch(error){reportError(error);}
}

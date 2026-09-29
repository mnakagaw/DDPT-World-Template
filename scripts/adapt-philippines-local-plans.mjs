#!/usr/bin/env node
// Adopt only the PDF passages inspected against official local government originals.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';

const project=resolve(process.argv[process.argv.indexOf('--project')+1]||'generated/philippines-areadata-20260929');
const dataPath=join(project,'data','dashboard.json');
const data=JSON.parse(await readFile(dataPath,'utf8'));
if(data.country?.id!=='PHL')throw Error('Expected Philippines dataset');
const checkedAt=new Date().toISOString();
const sha=b=>createHash('sha256').update(b).digest('hex');
const configs=[
  {
    file:'davao-city-cdp-2023-2028.pdf',sourceId:'davao-city-cdp-2023-2028',
    id:'phl-davao-cdp-verified',code:'1130700000',
    url:'https://cpdoapps.davaocity.gov.ph/requirements/download/RSD/Comprehensive%20Development%20Plan%20%282023-2028%29.pdf',
    title:'Davao City Comprehensive Development Plan 2023–2028',publisher:'Davao City Government / City Planning and Development Office',
    kind:'published-plan',category:'plan',period:'2023-2028',periodKind:'multi_year',
    status:'approved',statusLocator:'PDF pages 3–5: Ordinance No. 0356-23 and City Mayor approval dated 29 December 2023',
    summary:'The city plan includes local development indicators, sector plans and priority programs, an investment program and a medium-term financial plan. The finance sections are planned allocations, not an expenditure report or official evaluation.',
    contentLocator:'PDF pages 8–11 (contents); ordinance and mayor approval on pages 3–5',
    sourceNote:'Original 447-page official PDF retained locally with SHA-256; cover, adoption ordinance, mayor approval and table of contents were visually inspected. Planned financial sections are not treated as executed spending.'
  },
  {
    file:'olongapo-city-revised-aip-2025.pdf',sourceId:'olongapo-city-revised-aip-2025',
    id:'phl-olongapo-revised-aip-verified',code:'0331400000',
    url:'https://olongapocity.gov.ph/wp-content/themes/olongapo-ofc-theme-prod/assets/files/city-council/resolutions/RESOLUTIONS%202025/RES.%20NO.%2085%20-%202025%20-%20REVISED%20AIP%202025.pdf',
    title:'Olongapo City Revised Calendar Year 2025 Annual Investment Program, Resolution No. 85',
    publisher:'Olongapo City Government / Sangguniang Panlungsod',
    kind:'annual-plan',category:'budget',period:'2025',periodKind:'calendar_year',
    status:'council_approved',statusLocator:'PDF pages 1–2: Resolution No. 85 (Series of 2025), approved unanimously 28 July 2025',
    summary:'The city council resolution approves the revised 2025 Annual Investment Program. The attached tables list planned program amounts and funding sources. These are investment plans, not actual spending or completed project results.',
    contentLocator:'PDF pages 1–2 (resolution) and 10 (sample line-item investment table)',
    sourceNote:'Original 24-page official PDF retained locally with SHA-256; resolution pages and a line-item table were visually inspected. Mayor signature date is not adopted because the scan/OCR is unclear.'
  }
];
for(const config of configs){
  const bytes=await readFile(join(project,'raw',config.file));
  if(bytes.subarray(0,4).toString()!=='%PDF')throw Error('Invalid PDF '+config.file);
  const territory=data.territories.find(row=>row.id==='PHL:PSGC:'+config.code);
  if(!territory||territory.type!=='city'||territory.official_code!==config.code)
    throw Error('Local document PSGC match failed: '+config.code);
  data.sources=data.sources.filter(row=>row.id!==config.sourceId);
  data.sources.push({id:config.sourceId,name:config.title,publisher:config.publisher,url:config.url,
    reference_period:config.period,status:'ready',retrieved_at:checkedAt,
    raw_path:'raw/'+config.file,sha256:sha(bytes),bytes:bytes.length,
    note:config.sourceNote});
  const evidence=locator=>({source_id:config.sourceId,locator,checked_at:checkedAt,authority:config.publisher});
  data.documents=data.documents.filter(row=>row.id!==config.id);
  data.documents.push({id:config.id,territory_id:territory.id,category:config.category,
    title:config.title,kind:config.kind,url:config.url,period:config.period,
    target_period:{label:config.period,kind:config.periodKind},
    availability:'content_verified',official_status:config.status,
    official_evidence:evidence(config.statusLocator),source_id:config.sourceId,
    territory_match:{territory_id:territory.id,country_id:'PHL',type:'city',
      code_system:territory.code_system,official_code:territory.official_code,
      boundary_version:territory.boundary_version,
      method:'Exact city name and PSA PSGC code matched to the named official city-government PDF.',
      source_id:config.sourceId,locator:'PSA PSGC city row '+config.code+' and PDF cover/resolution',
      checked_at:checkedAt},
    content:{summary:config.summary,evidence:evidence(config.contentLocator)}
  });
}
const guideFile='dilg-cdp-toolkit-2022.pdf';
const guideBytes=await readFile(join(project,'raw',guideFile));
if(guideBytes.subarray(0,4).toString()!=='%PDF')throw Error('Invalid DILG guide PDF');
data.sources=data.sources.filter(row=>row.id!=='dilg-region1-cdp-toolkit-2022');
data.sources.push({id:'dilg-region1-cdp-toolkit-2022',
  name:'DILG Region 1 Comprehensive Development Plan Facilitator Toolkit (2022)',
  publisher:'Department of the Interior and Local Government, Region 1',
  url:'https://region1.dilg.gov.ph/images/Transparency/BOOKS/CDP-TOOLKIT-FINAL%20AS%20OF%20APRIL%208%202022.pdf',
  reference_period:'2022 edition; Region 1 facilitator guidance',status:'partial',retrieved_at:checkedAt,
  raw_path:'raw/'+guideFile,sha256:sha(guideBytes),bytes:guideBytes.length,
  license:'All rights reserved; no redistribution of original PDF in the candidate.',
  note:'Original 502-page PDF retained privately and hash-checked. Cover, copyright, contents and session-6 packaging passage inspected. Regional toolkit is not treated as a nationally mandated form; current 2024 harmonization circular and local applicability require review.'});
data.planning={...data.planning,purpose:'Find verified Philippine local planning materials for the selected area. Planned investments, actual expenditure and official evaluation are separate evidence.',
  update:{status:'stopped',checked_at:checkedAt,last_success_at:checkedAt,
    message:'Point-in-time 29 September 2026 source review; no continuous document monitor is configured.'}};
data.collection.status='partial';
data.collection.notes=[...new Set([...data.collection.notes.filter(note=>
  !note.includes('Initial national-data site inputs only') &&
  !note.includes('complete province/city/municipality planning authorities are not acquired') &&
  !note.includes('plans for all but the Iloilo City link are not acquired')),
  'Two city-government PDF originals (Davao CDP and Olongapo revised AIP) were acquired and visually checked; their planning and investment content does not prove spending or evaluation.'])];
data.generated_at=checkedAt;
for(const gap of data.gaps){if(gap.category==='planning_documents'){
  gap.status='partial';gap.detail='Davao CDP and Olongapo revised AIP bodies are verified for their named city authorities. Iloilo CDP remains link-only. National coverage of local plans, budgets, spending and evaluations is not established.';
  gap.next_action='Acquire and verify other authorities’ official documents; keep planned allocations, actual spending and formal evaluation separate.';
}}
await writeFile(dataPath,JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify({documents:data.documents.length,verified_pdf_documents:configs.length},null,2));

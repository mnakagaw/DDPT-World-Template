#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {cp,mkdir,readFile,readdir,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {generateSite} from '../lib/generate.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {CENSUS_THEMES} from '../lib/country-completion-matrix.mjs';

const SSB='https://www.ssb.no/offentlig-sektor/offentlig-forvaltning/artikler/regionale-inndelinger-2020/_/attachment/inline/33ea12e7-3c8e-4a1e-be0b-cfd6ca476b66%3A083a78030f49bbe43587436b9713748301e15506/NOT%202021-29_web.pdf';
const BVT_RULES='https://npolar.no/en/regulations-bouvetoya-nature-reserve/';
const SGS_FAQ='https://gov.gs/frequently-asked-questions/';
const SGS_ABOUT='https://gov.gs/about-sgssi/';
const SGS_STEWARDSHIP='https://gov.gs/stewardship-framework-for-sgssi/';
const SGS_MPA='https://gov.gs/marine-protected-area/';
const SGS_GAZETTES='https://laws.gov.gs/gazettes/';
const SGS_TPA='https://www.gov.gs/wp-content/uploads/2023/10/TPA-management-plan-FINAL-.pdf';
const SGS_MPA_PLAN='https://gov.gs/wp-content/uploads/2026/03/SGSSI-MPA-Management-Plan-2026_website.pdf';

function args(){const out={};for(let i=2;i<process.argv.length;i+=2)out[process.argv[i].replace(/^--/,'')]=process.argv[i+1];return out;}
async function copyFiles(source,target){await mkdir(target,{recursive:true});for(const name of await readdir(source)){const file=path.join(source,name);if((await stat(file)).isFile())await cp(file,path.join(target,name),{force:true});}}
const sha=async file=>createHash('sha256').update(await readFile(file)).digest('hex');
function structuralDomain(urls,note,basis,evidence){return {status:'structurally_not_applicable',identified:true,accessed:true,acquired:true,inspected:true,geography_matched:false,adopted:false,unavailable:false,restricted:false,failed_with_evidence:false,structurally_not_applicable:true,applicability_basis:basis,urls,note,completion_verified:true,evidence};}
function inspectedDomain(status,urls,note,evidence){return {status,identified:true,accessed:true,acquired:true,inspected:true,geography_matched:false,adopted:false,unavailable:false,restricted:false,failed_with_evidence:false,urls,note,completion_verified:true,evidence};}

async function main(){
  const a=args();if(!a.project||!a.source)throw new Error('Usage: node scripts/update-nonresident-americas-profiles.mjs --project <dir> --source <dir>');
  const root=path.resolve(a.project),source=path.resolve(a.source),evidenceDir=path.join(root,'evidence'),dataPath=path.join(root,'data','dashboard.json');
  const [dataset,preflight,inventory,receipt]=await Promise.all([readFile(dataPath,'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),readFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),'utf8').then(JSON.parse),readFile(path.join(source,'receipt.json'),'utf8').then(JSON.parse)]);
  const acquired=Object.fromEntries(receipt.files.filter(row=>row.status==='acquired').map(row=>[row.name,row]));
  for(const required of ['bvt-ssb-regional-classification.pdf','bvt-reserve-regulations.html','sgs-faq.html','sgs-about.html','sgs-stewardship.html','sgs-marine-protected-area.html','sgs-gazettes.html','sgs-terrestrial-plan.pdf','sgs-marine-plan-2026.pdf'])if(!acquired[required])throw new Error(`Required nonresident evidence is not acquired: ${required}`);
  const profiles={
    BVT:{name:'Bouvet Island',basis:'Statistics Norway states that Bouvet Island has no settlement and is therefore not a separate unit in its person statistics (Notes 2021/29, p. 14).',authority:'Statistics Norway and Norwegian Polar Institute',sourceId:'bvt-official-nonresident-profile',url:SSB,evidence:[{receipt:'raw/nonresident-americas-evidence/receipt.json'},{raw:'raw/nonresident-americas-evidence/bvt-ssb-regional-classification.pdf',locator:'Notes 2021/29, p. 14'},{raw:'raw/nonresident-americas-evidence/bvt-reserve-regulations.html'}]},
    SGS:{name:'South Georgia and the South Sandwich Islands',basis:'The Government of South Georgia and the South Sandwich Islands states that the Territory has no permanent residents; temporary Government and research-station personnel remain distinct.',authority:'Government of South Georgia and the South Sandwich Islands',sourceId:'sgs-official-nonresident-profile',url:SGS_FAQ,evidence:[{receipt:'raw/nonresident-americas-evidence/receipt.json'},{raw:'raw/nonresident-americas-evidence/sgs-faq.html',locator:'Who lives on the Island of South Georgia?'},{raw:'raw/nonresident-americas-evidence/sgs-about.html'}]}
  };
  const indicatorIds=new Set(Object.keys(profiles).map(id=>`${id}_PERMANENT_RESIDENT_POPULATION`));
  dataset.indicators=[...dataset.indicators.filter(row=>!indicatorIds.has(row.id)),...Object.entries(profiles).map(([id,p])=>({id:`${id}_PERMANENT_RESIDENT_POPULATION`,name:'Permanent resident population',theme:'Population',unit:'permanent residents',definition:`Permanent resident population. ${id==='SGS'?'Government and research-station personnel on temporary postings are excluded.':'Seasonal research teams are excluded.'}`,definition_id:`${id}-NONRESIDENT-PROFILE`,population:'Permanent resident population',measurement_method:'source_reported_status',aggregation:'none',period_policy:'current_source_status',series_family:'administrative',display_role:'primary',source_id:p.sourceId,source_locator:id==='BVT'?'Statistics Norway Notes 2021/29, p. 14':'Government FAQ and About SGSSI'}))];
  dataset.observations=[...dataset.observations.filter(row=>!indicatorIds.has(row.indicator_id)),...Object.keys(profiles).map(id=>({territory_id:id,indicator_id:`${id}_PERMANENT_RESIDENT_POPULATION`,period:'2026',value:0,status:'observed',source_id:profiles[id].sourceId,definition:`No permanent resident population; ${id==='SGS'?'temporary officials, scientists and seasonal staff may be present.':'seasonal researchers may be present.'}`,definition_id:`${id}-NONRESIDENT-PROFILE`,unit:'permanent residents',population:'Permanent resident population',measurement_method:'source_reported_status',source_locator:id==='BVT'?'Statistics Norway Notes 2021/29, p. 14':'Government FAQ and About SGSSI'}))];
  const sourceRows=[
    ['bvt-official-nonresident-profile','Bouvet Island settlement status in Norwegian official statistics','Statistics Norway',SSB,'bvt-ssb-regional-classification.pdf','Official statistics note states that there is no settlement and that Bouvet Island is not a separate unit in person statistics.'],
    ['bvt-nature-reserve-regulations','Regulations for Bouvetøya Nature Reserve','Norwegian Polar Institute',BVT_RULES,'bvt-reserve-regulations.html','Official management and access rules; environmental management exists even though resident Census and municipal planning are structurally inapplicable.'],
    ['sgs-official-nonresident-profile','Frequently Asked Questions and resident status','Government of South Georgia and the South Sandwich Islands',SGS_FAQ,'sgs-faq.html','Official page states that there is no permanent human population and distinguishes temporary staff.'],
    ['sgs-territory-overview','About SGSSI','Government of South Georgia and the South Sandwich Islands',SGS_ABOUT,'sgs-about.html','Official territory overview distinguishes no permanent residents from staffed research bases.'],
    ['sgs-stewardship-framework','Stewardship Framework for SGSSI','Government of South Georgia and the South Sandwich Islands',SGS_STEWARDSHIP,'sgs-stewardship.html','Official framework and annual-report entry point.'],
    ['sgs-marine-protected-area','Marine Protected Area programme','Government of South Georgia and the South Sandwich Islands',SGS_MPA,'sgs-marine-protected-area.html','Official management, research and monitoring material.'],
    ['sgs-gazettes','SGSSI Gazettes and legal record','Government of South Georgia and the South Sandwich Islands',SGS_GAZETTES,'sgs-gazettes.html','Official journal of record and appropriation notices.'],
    ['sgs-terrestrial-protected-area-plan','Terrestrial Protected Areas Management Plan','Government of South Georgia and the South Sandwich Islands',SGS_TPA,'sgs-terrestrial-plan.pdf','Official protected-area plan.'],
    ['sgs-marine-plan-2026','Marine Protected Area Management Plan 2026','Government of South Georgia and the South Sandwich Islands',SGS_MPA_PLAN,'sgs-marine-plan-2026.pdf','Official 2026 marine management plan.']
  ].map(([id,name,publisher,url,file,note])=>({id,name,publisher,url,status:'ready',retrieved_at:receipt.generated_at.slice(0,10),reference_period:file.includes('2026')?'2026':'current source at retrieval',geographic_level:id.startsWith('bvt')?'Bouvet Island':'South Georgia and the South Sandwich Islands',license:'Official public material; reuse terms not stated',note,raw_path:`raw/nonresident-americas-evidence/${file}`,receipt_path:'raw/nonresident-americas-evidence/receipt.json',sha256:acquired[file].sha256,bytes:acquired[file].bytes}));
  const sourceIds=new Set(sourceRows.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...sourceRows];
  const docRows=[
    ['bvt-reserve-regulations','BVT','reference','Bouvetøya Nature Reserve regulations','official-regulation',BVT_RULES,'bvt-nature-reserve-regulations'],
    ['sgs-stewardship','SGS','plan','Stewardship Framework for SGSSI','official-plan',SGS_STEWARDSHIP,'sgs-stewardship-framework'],
    ['sgs-terrestrial-plan','SGS','plan','Terrestrial Protected Areas Management Plan','official-plan',SGS_TPA,'sgs-terrestrial-protected-area-plan'],
    ['sgs-marine-plan','SGS','plan','Marine Protected Area Management Plan 2026','official-plan',SGS_MPA_PLAN,'sgs-marine-plan-2026'],
    ['sgs-gazettes','SGS','budget','Gazettes, laws and appropriation notices','official-reference',SGS_GAZETTES,'sgs-gazettes']
  ].map(([id,territory_id,category,title,kind,url,source_id])=>({id,territory_id,category,title,kind,url,availability:'body_acquired',official_status:'unverified',source_id}));
  const docIds=new Set(docRows.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!docIds.has(row.id)),...docRows];
  const structuralDomains=['latest_census','census_results','table_catalog','machine_readable_data','administrative_codes','adm1_adm2_boundaries'];
  for(const [id,p] of Object.entries(profiles)){
    const country=preflight.countries.find(row=>row.country_area_id===id);if(!country)throw new Error(`Missing preflight record ${id}`);
    country.scope_role='completed nonresident-area profile; environmental management remains available';country.edition_mode='nonresident_area_profile';country.country_adapter_status='complete_nonresident_area_profile';
    country.official_statistics_office=id==='BVT'?inspectedDomain('inspected',[SSB],`Statistics Norway explicitly records ${p.basis}`,p.evidence):structuralDomain([SGS_FAQ,SGS_ABOUT],'The administering Government, rather than a resident-population statistical office, supplies the official status for this nonresident territory.',p.basis,p.evidence);
    for(const domainId of structuralDomains)country[domainId]=structuralDomain([p.url],`${domainId.replaceAll('_',' ')} is structurally inapplicable to the permanent resident population because ${p.basis} A display-only country outline and temporary personnel are not converted into a resident Census or domestic administrative hierarchy.`,p.basis,p.evidence);
    if(id==='BVT'){
      country.planning_law=inspectedDomain('inspected',[BVT_RULES],'Official nature-reserve regulations are acquired. They govern access and environmental protection, not a resident municipality.',p.evidence);
      country.planning_guidance=inspectedDomain('acquired',[BVT_RULES],'Official reserve-management and access guidance is acquired and shown as environmental management material.',p.evidence);
      country.plans_budgets_implementation_evaluation=structuralDomain([BVT_RULES],'A resident municipal plan, municipal budget and resident-service evaluation are structurally inapplicable. Environmental management is shown separately and is not treated as absent.',p.basis,p.evidence);
    }else{
      country.planning_law=inspectedDomain('inspected',[SGS_GAZETTES],'The official Gazette and protected-area framework were inspected. The territory has government and environmental law but no resident municipal planning tier.',p.evidence);
      country.planning_guidance=inspectedDomain('acquired',[SGS_STEWARDSHIP,SGS_MPA,SGS_TPA],'Official stewardship, terrestrial and marine management guidance is acquired.',p.evidence);
      country.plans_budgets_implementation_evaluation=inspectedDomain('acquired',[SGS_STEWARDSHIP,SGS_GAZETTES,SGS_MPA_PLAN],'Official stewardship, appropriation records, management plans and monitoring material are linked without representing them as resident municipal plans.',p.evidence);
    }
  }
  const newSemantic=[];
  for(const [id,p] of Object.entries(profiles)){
    newSemantic.push({country_area_id:id,source_id:p.sourceId,source_path:'evidence/NONRESIDENT_AREAS_INTEGRATION_AUDIT.json',source_url:p.url,table_id:'nonresident-area-profile',table_title:'Permanent resident status',field_id:`${id}_PERMANENT_RESIDENT_POPULATION`,field_label:'Permanent resident population',numeric_cell_count:1,theme:'population_total',disposition:'integrated',reason:'The administering authority reports no permanent resident population. The observed zero applies only to permanent residents and excludes temporary personnel and visitors.',indicator_id:`${id}_PERMANENT_RESIDENT_POPULATION`,coverage_complete:true,country_edition_eligible:true});
    for(const theme of CENSUS_THEMES.filter(theme=>theme!=='population_total'))newSemantic.push({country_area_id:id,source_id:p.sourceId,source_path:'evidence/NONRESIDENT_AREAS_INTEGRATION_AUDIT.json',source_url:p.url,table_id:'nonresident-area-applicability',table_title:'Resident Census and municipal-planning applicability',field_id:`${id}_${theme}_NOT_APPLICABLE`,field_label:theme,numeric_cell_count:0,theme,disposition:'structurally_not_applicable',reason:'This resident-population theme has no applicable permanent resident population. It is not recorded as zero, and temporary personnel or visitors are not substituted.',coverage_complete:true,country_edition_eligible:false,applicability_basis:p.basis,evidence:p.evidence});
  }
  inventory.records=[...(inventory.records||[]).filter(row=>!Object.keys(profiles).includes(row.country_area_id)),...newSemantic];inventory.record_count=inventory.records.length;inventory.generated_at=new Date().toISOString();
  for(const [id,p] of Object.entries(profiles))inventory.adjudication={...(inventory.adjudication||{}),[id]:{reviewed_numeric_fields:CENSUS_THEMES.length,terminal_dispositions:CENSUS_THEMES.length,covered_themes:[...CENSUS_THEMES],method:'Permanent resident population is a source-supported zero; all other resident Census themes use the strictly evidenced nonresident-area structural exception.',applicability_basis:p.basis,audit:'evidence/NONRESIDENT_AREAS_INTEGRATION_AUDIT.json'}};
  dataset.collection.adapters=[...new Set([...(dataset.collection.adapters||[]),'nonresident-americas-area-profile-v1'])];dataset.collection.notes=[...(dataset.collection.notes||[]),'BVT and SGS: permanent resident population is source-reported as zero. Temporary researchers, government officers, seasonal staff and visitors are not counted as permanent residents and are not converted into resident Census characteristics.','Environmental and protected-area management documents remain available for nonresident areas; structural inapplicability applies only to resident Census and municipal-planning requirements.'];dataset.generated_at=new Date().toISOString();
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  await writeFile(dataPath,JSON.stringify(dataset,null,2)+'\n');await generateSite({dataset,outDir:root});await copyFiles(source,path.join(root,'raw','nonresident-americas-evidence'));
  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_ids:Object.keys(profiles),status:'complete_nonresident_area_profiles',edition_complete:true,source_receipt:'raw/nonresident-americas-evidence/receipt.json',semantic_records:newSemantic.length,integrated_population_records:2,structurally_not_applicable_records:newSemantic.filter(row=>row.disposition==='structurally_not_applicable').length,controls:{ordinary_countries_cannot_use_exception:true,applicability_basis_required:true,evidence_required:true,temporary_personnel_not_substituted:true,environmental_management_retained:true},dataset_sha256:await sha(dataPath)};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'COUNTRY_SEMANTIC_INVENTORY.json'),JSON.stringify(inventory,null,2)+'\n'),writeFile(path.join(evidenceDir,'NONRESIDENT_AREAS_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n')]);
  console.log(JSON.stringify({country_area_ids:Object.keys(profiles),validation,semantic_records:newSemantic.length,dataset_sha256:audit.dataset_sha256},null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

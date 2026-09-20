import {copyFile,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const LAW_PAGE='https://www.descentralizacion.gob.pa/page/ley-37-2009-descentralizacion';
const LAW_PDF='https://www.descentralizacion.gob.pa/uploads/ley-37-2009-descentralizacion.pdf';
const GUIDE_PAGE='https://www.mef.gob.pa/dire/';
const GUIDE_PDF='https://www.mef.gob.pa/wp-content/uploads/2024/05/5.-GUIA-PED-VF-Mayo-6.22.pdf';
const CURRENT_GUIDE_NOTICE='https://www.mef.gob.pa/2025/07/refuerzan-la-planificacion-municipal-con-la-guia-metodologica-para-la-formulacion-de-planes-estrategicos-de-desarrollo-territorial/';
const PLAN_PAGE='https://www.mef.gob.pa/plan-estrategico-de-gobierno/';
const PLAN_PDF='https://www.mef.gob.pa/wp-content/uploads/2024/12/GacetaNo_30186b_20241227.pdf';
const BUDGET_PAGE='https://diprena.mef.gob.pa/monitoreo-y-evaluacion-de-programas-presupuestarios-2/';
const BUDGET_PDF='https://diprena.mef.gob.pa/wp-content/uploads/2026/01/Informe-Borrador-Cierre-2024-Consolidado.-Para-Publicacion.pdf';
const EVALUATION_PDF='https://diprena.mef.gob.pa/wp-content/uploads/2024/06/Gu%C3%ADa-metodol%C3%B3gica-para-evaluar-la-calidad-del-gasto-p%C3%BAblico-en-Panam%C3%A1-junio2024.pdf';
const license='Reuse terms not verified; AreaData links to the official source and does not redistribute the original through the public site.';

const files=[
  {source:'law-37-2009.pdf',target:'planning_law-ley-37-2009.pdf',url:LAW_PDF,pages:40,inspected_pages:[5,6,28,29,32,33]},
  {source:'ped-guide-2022.pdf',target:'planning_guidance-ped-guide-2022.pdf',url:GUIDE_PDF,pages:94,inspected_pages:[6,16,18,22,24,71,72]},
  {source:'planning-3.html',target:'planning_guidance-ped-2025-2029-notice.html',url:CURRENT_GUIDE_NOTICE,pages:null,inspected_pages:[]},
  {source:'peg-2025-2029-gaceta.pdf',target:'plan-peg-2025-2029-gaceta.pdf',url:PLAN_PDF,pages:148,inspected_pages:[1,148]},
  {source:'budget-monitoring-2024.pdf',target:'implementation-budget-close-2024.pdf',url:BUDGET_PDF,pages:23,inspected_pages:[3,4,5,8,9,13,19]},
  {source:'evaluation-guide-2024.pdf',target:'evaluation-guidance-quality-of-spending-2024.pdf',url:EVALUATION_PDF,pages:33,inspected_pages:[6,9,10,29,30]}
];

async function sha256(file){return createHash('sha256').update(await readFile(file)).digest('hex');}
const sourceState=(note,urls,evidence,{geographyMatched=false}={})=>({status:'inspected',identified:true,accessed:true,acquired:true,inspected:true,geography_matched:geographyMatched,adopted:false,unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls,note,evidence});

export async function updatePanamaPlanningEvidence({project,raw}={}){
  if(!project||!raw)throw new Error('project and raw are required.');
  const root=path.resolve(project),rawRoot=path.resolve(raw),dataPath=path.join(root,'data','dashboard.json'),evidenceDir=path.join(root,'evidence');
  const [dataset,preflight,priorAudit]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'PAN_INTEGRATION_AUDIT.json'),'utf8').then(JSON.parse)
  ]);
  const pan=preflight.countries.find(row=>row.country_area_id==='PAN');
  if(!pan)throw new Error('PAN missing from source preflight.');
  const rawTarget=path.join(root,'raw','supplemental-country-sources','PAN');await mkdir(rawTarget,{recursive:true});
  const acquired=[];
  for(const item of files){
    const from=path.join(rawRoot,item.source),to=path.join(rawTarget,item.target);await copyFile(from,to);
    acquired.push({...item,path:path.relative(root,to).replaceAll('\\','/'),sha256:await sha256(to)});
  }
  const commonEvidence=[...acquired.map(({path,sha256,pages,inspected_pages,url})=>({path,sha256,pages,inspected_pages,url})),{audit:'evidence/PAN_PLANNING_INTEGRATION_AUDIT.json'}];
  pan.planning_law=sourceState('Official Ley 37 of 2009 was acquired and inspected. Article 13 makes territorial planning coordinated and obligatory and assigns the Plan Estratégico Distrital to the municipality and the Plan Estratégico de Corregimiento to each Junta Comunal. Article 115 links the annual municipal budget to the five-year district strategic plan. The law defines legal responsibilities; it is not evidence that every required plan is current or implemented.',[LAW_PAGE,LAW_PDF],commonEvidence);
  pan.planning_guidance=sourceState('The official 2022 district-plan methodology was acquired and inspected. It specifies a territorial diagnosis, strategy, indicative investment programme, and monitoring/evaluation steps. A 2025 MEF notice confirms guidance for PED 2025-2029 and five diagnostic dimensions; the notice is retained separately from the full 2022 guide because the 2025 guide body was not published at the inspected URL.',[GUIDE_PAGE,GUIDE_PDF,CURRENT_GUIDE_NOTICE],commonEvidence);
  pan.plans_budgets_implementation_evaluation=sourceState('The official gazette publication approving the five-year 2025-2029 government plan, the 2024 fiscal-close budget monitoring report, and the 2024 public-spending evaluation guide were acquired and inspected. They remain separate evidence types: the plan is an approved national framework; the fiscal-close report is budget implementation evidence; the evaluation guide is a method, not a completed plan outcome evaluation. MEF reported delivery of 68 district plans in 2025, but no district-plan body is represented as acquired by this adapter.',[PLAN_PAGE,PLAN_PDF,BUDGET_PAGE,BUDGET_PDF,EVALUATION_PDF,'https://www.mef.gob.pa/2025/09/entrega-de-68-planes-estrategicos-distritales-fortalece-la-gestion-y-transparencia-de-los-recursos-publicos/'],commonEvidence);
  pan.scope_role='regional_gateway_member; official Census 2023 depth and national/district planning evidence integrated; required theme gaps open';
  pan.country_adapter_status='official_census_2023_depth_and_planning_evidence_integrated; required_theme_gaps_open';

  const byTarget=new Map(acquired.map(row=>[row.target,row]));
  const sourceRows=[
    {id:'PAN_PLANNING_LAW_37_2009',name:'Ley 37 de 2009 sobre descentralización y planificación territorial',publisher:'Autoridad Nacional de Descentralización, Gobierno de Panamá',url:LAW_PDF,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2009 law text',geographic_level:'national, province, district and corregimiento',raw_path:byTarget.get('planning_law-ley-37-2009.pdf').path,sha256:byTarget.get('planning_law-ley-37-2009.pdf').sha256,license,note:'Official law text. Articles 13 and 115 were inspected for planning units, responsibilities, cycle and budget linkage. Current consolidated amendment status beyond this official publication was not independently certified.'},
    {id:'PAN_PLANNING_PED_GUIDE_2022',name:'Guía Metodológica para la Formulación de Planes Estratégicos Distritales',publisher:'Ministerio de Economía y Finanzas, Dirección de Desarrollo Territorial',url:GUIDE_PDF,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2022 methodology',geographic_level:'district',raw_path:byTarget.get('planning_guidance-ped-guide-2022.pdf').path,sha256:byTarget.get('planning_guidance-ped-guide-2022.pdf').sha256,license,note:'Official district planning guide with diagnosis, strategy, investment programme and monitoring/evaluation workflow. The separate 2025 official notice describes guidance for the 2025-2029 cycle.'},
    {id:'PAN_PLANNING_PED_NOTICE_2025',name:'MEF notice on territorial planning guidance for PED 2025-2029',publisher:'Ministerio de Economía y Finanzas',url:CURRENT_GUIDE_NOTICE,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2025-2029',geographic_level:'district',raw_path:byTarget.get('planning_guidance-ped-2025-2029-notice.html').path,sha256:byTarget.get('planning_guidance-ped-2025-2029-notice.html').sha256,license,note:'Official notice confirming the current cycle and five diagnostic dimensions. It is not represented as the full guide body.'},
    {id:'PAN_PLANNING_PEG_2025_2029',name:'Plan Estratégico de Gobierno 2025-2029, Gaceta Oficial 30186-B',publisher:'Consejo de Gabinete / Gaceta Oficial Digital',url:PLAN_PDF,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2025-2029',geographic_level:'national',raw_path:byTarget.get('plan-peg-2025-2029-gaceta.pdf').path,sha256:byTarget.get('plan-peg-2025-2029-gaceta.pdf').sha256,license,note:'Official gazette publication of Cabinet Resolution 124 approving the five-year government strategic plan. It is not a district plan.'},
    {id:'PAN_PLANNING_BUDGET_CLOSE_2024',name:'Monitoreo de la ejecución presupuestaria, cierre fiscal 2024',publisher:'Ministerio de Economía y Finanzas, DIPRENA',url:BUDGET_PDF,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2024 fiscal close',geographic_level:'national and public-sector entity',raw_path:byTarget.get('implementation-budget-close-2024.pdf').path,sha256:byTarget.get('implementation-budget-close-2024.pdf').sha256,license,note:'Official budget monitoring report. Budget-law, modified-budget and execution values are implementation evidence and are not converted into plan achievement.'},
    {id:'PAN_PLANNING_EVALUATION_GUIDE_2024',name:'Guía metodológica para evaluar la calidad del gasto público en Panamá',publisher:'Ministerio de Economía y Finanzas, DIPRENA',url:EVALUATION_PDF,status:'ready',retrieved_at:new Date().toISOString(),reference_period:'2024 methodology',geographic_level:'national and budget programme',raw_path:byTarget.get('evaluation-guidance-quality-of-spending-2024.pdf').path,sha256:byTarget.get('evaluation-guidance-quality-of-spending-2024.pdf').sha256,license,note:'Official evaluation methodology. It does not constitute a completed evaluation of the 2025-2029 government plan or a district plan.'}
  ];
  const sourceIds=new Set(sourceRows.map(row=>row.id));dataset.sources=[...dataset.sources.filter(row=>!sourceIds.has(row.id)),...sourceRows];
  const documents=[
    {id:'pan-law-37-2009',territory_id:'PAN',category:'reference',title:'Ley 37 de 2009: decentralization and territorial planning',kind:'official-law',url:LAW_PDF,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_LAW_37_2009',period:'2009 law text',target_period:{label:'2009 law text',kind:'other'}},
    {id:'pan-ped-guide-2022',territory_id:'PAN',category:'reference',title:'Methodological guide for district strategic plans',kind:'official-guidance',url:GUIDE_PDF,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_PED_GUIDE_2022',period:'2022 methodology',target_period:{label:'2022 methodology',kind:'other'}},
    {id:'pan-ped-guidance-notice-2025',territory_id:'PAN',category:'reference',title:'MEF guidance notice for district plans 2025-2029',kind:'official-guidance-notice',url:CURRENT_GUIDE_NOTICE,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_PED_NOTICE_2025',period:'2025-2029',target_period:{label:'2025-2029',kind:'multi_year'}},
    {id:'pan-peg-2025-2029',territory_id:'PAN',category:'plan',title:'Government Strategic Plan 2025-2029',kind:'official-national-plan',url:PLAN_PDF,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_PEG_2025_2029',period:'2025-2029',target_period:{label:'2025-2029',kind:'multi_year'}},
    {id:'pan-budget-close-2024',territory_id:'PAN',category:'implementation',title:'Budget execution monitoring, fiscal close 2024',kind:'official-financial-results',url:BUDGET_PDF,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_BUDGET_CLOSE_2024',period:'2024',target_period:{label:'2024',kind:'calendar_year'}},
    {id:'pan-evaluation-guide-2024',territory_id:'PAN',category:'evaluation',title:'Methodology for evaluating public spending quality',kind:'official-evaluation-guidance',url:EVALUATION_PDF,availability:'body_acquired',official_status:'unverified',source_id:'PAN_PLANNING_EVALUATION_GUIDE_2024',period:'2024',target_period:{label:'2024',kind:'calendar_year'}}
  ];
  const documentIds=new Set(documents.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!documentIds.has(row.id)),...documents];
  const checkedAt=new Date().toISOString();dataset.planning.update={status:'current',message:'Panama planning evidence now includes the official planning law, district methodology, approved 2025-2029 national plan, 2024 budget execution monitoring and evaluation guidance. District plan bodies and completed outcome evaluations remain explicit gaps.',checked_at:checkedAt,last_success_at:checkedAt};
  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'PAN',status:'inspected_official_law_guidance_plan_budget_implementation_and_evaluation_method',edition_domain_complete:true,documents:acquired.map(({source,target,url,pages,inspected_pages,path,sha256})=>({source,target,url,pages,inspected_pages,path,sha256})),findings:['Ley 37 assigns district strategic plans to municipalities and corregimiento plans to Juntas Comunales, and links the annual municipal budget to a five-year district plan.','The 2022 district guide specifies diagnosis, strategy, an indicative investment programme, and monitoring/evaluation steps; a 2025 notice confirms the 2025-2029 cycle and diagnostic dimensions.','The official gazette approves the national 2025-2029 plan. The 2024 fiscal-close report records budget implementation, while the 2024 evaluation guide records methodology.'],unresolved:['The inspected 2025 MEF guidance notice did not expose the complete 2025 guide body; the full 2022 official guide is retained as the acquired methodology.','No district-plan body was acquired by this adapter, even though MEF reported delivery of 68 district plans in September 2025.','No completed official outcome evaluation of the 2025-2029 national plan or district plans was acquired.'],evidence_policy:'Law, guidance, approved plans, authorized or modified budgets, financial implementation and completed official evaluation are separate evidence types. A guide is never shown as an evaluation result and a budget execution percentage is never shown as plan achievement.'};
  const panAudit={...priorAudit,generated_at:new Date().toISOString(),status:'partial_country_adapter_with_planning_evidence',edition_complete:false,unresolved_domains:[],planning_audit:'evidence/PAN_PLANNING_INTEGRATION_AUDIT.json'};
  await Promise.all([
    writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'PAN_PLANNING_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'PAN_INTEGRATION_AUDIT.json'),JSON.stringify(panAudit,null,2)+'\n'),
    writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')
  ]);
  return {country_area_id:'PAN',status:audit.status,documents:documents.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','raw']);if(args.help||!args.project||!args.raw)console.log('node scripts/update-panama-planning-evidence.mjs --project <directory> --raw <raw-dir>');else console.log(JSON.stringify(await updatePanamaPlanningEvidence(args),null,2));}catch(error){reportError(error);}
}

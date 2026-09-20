import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';
import {validateDataset} from '../lib/validate.mjs';
import {generateSite} from '../lib/generate.mjs';

const PLAN_URL='https://edc.gov.bz/wp-content/uploads/2023/04/Belize-Med-Term-Dev-Strat-and-Action-Plan-2022-2026.pdf';
const BUDGET_URL='https://mof.gov.bz/wp-content/uploads/2026/04/APPROVED-ESTIMATES-OF-REVENUE-AND-EXPENDITURE-FY-2026-2027-FINAL.pdf';
const PLAN_SOURCE='BLZ_PLANNING_MTDS_2022_2026';
const BUDGET_SOURCE='BLZ_PLANNING_APPROVED_BUDGET_2026_2027';
const license='Reuse terms not verified; AreaData links to the official source and does not redistribute the original through the public site.';

export async function updateBelizePlanningEvidence({project,receipts}={}){
  if(!project||!receipts)throw new Error('project and receipts are required.');
  const root=path.resolve(project),dataPath=path.join(root,'data','dashboard.json'),evidenceDir=path.join(root,'evidence');
  const [dataset,preflight,receiptDoc]=await Promise.all([
    readFile(dataPath,'utf8').then(JSON.parse),
    readFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),'utf8').then(JSON.parse),
    readFile(path.resolve(receipts),'utf8').then(JSON.parse)
  ]);
  const rows=receiptDoc.receipts||[],planReceipt=rows.find(row=>row.url===PLAN_URL),budgetReceipt=rows.find(row=>row.url===BUDGET_URL);
  if(!planReceipt||!budgetReceipt||planReceipt.status!=='acquired'||budgetReceipt.status!=='acquired')throw new Error('Both official Belize PDFs must be acquired.');
  const blz=preflight.countries.find(row=>row.country_area_id==='BLZ');if(!blz)throw new Error('BLZ missing from source preflight.');
  const evidence=[{path:'raw/supplemental-country-sources/BLZ/plans_budgets_implementation_evaluation-medium-term-development-strategy-2022-2026.pdf',sha256:planReceipt.sha256,pages:44,inspected_pages:[34,37,38]},{path:'raw/supplemental-country-sources/BLZ/plans_budgets_implementation_evaluation-approved-estimates-2026-2027.pdf',sha256:budgetReceipt.sha256,pages:376,inspected_pages:[7,9,11,12,13,15,17,18]},{audit:'evidence/BLZ_PLANNING_INTEGRATION_AUDIT.json'}];
  blz.plans_budgets_implementation_evaluation={status:'inspected',identified:true,accessed:true,acquired:true,inspected:true,geography_matched:false,adopted:false,unavailable:false,restricted:false,failed_with_evidence:false,completion_verified:true,urls:[PLAN_URL,BUDGET_URL,'https://mof.gov.bz/cat_doc/legal-approved-estimates-of-revenue-and-expenditure/'],note:'The official 2022-2026 Medium-Term Development Strategy and approved 2026-2027 estimates were acquired and inspected. The strategy states implementation, quarterly monitoring, evaluation and learning arrangements and budget/resource-mobilization requirements. The approved estimates expose 2023/24 and 2024/25 actuals, 2025/26 budget and projected out-turn, 2026/27 budget and forward estimates. These are kept distinct: financial actuals/out-turn are implementation evidence, not proof that development-plan outcomes were achieved. No separate completed official MTDS outcome evaluation was acquired.',evidence};
  blz.scope_role='regional_gateway_member; official Census 2022 district adapter and national planning evidence integrated';
  blz.country_adapter_status='official_census_district_and_planning_evidence_integrated';

  const sourceRows=[
    {id:PLAN_SOURCE,name:'#planBelize Medium-Term Development Strategy 2022-2026',publisher:'Economic Development Council, Government of Belize',url:PLAN_URL,status:'ready',retrieved_at:planReceipt.requested_at,reference_period:'2022-2026',geographic_level:'national',raw_path:'raw/supplemental-country-sources/BLZ/plans_budgets_implementation_evaluation-medium-term-development-strategy-2022-2026.pdf',sha256:planReceipt.sha256,license,note:'Official strategy. Chapter 7 specifies implementation, monitoring, evaluation and learning arrangements; Chapter 8 covers budget allocations, investment and resource mobilization. This is a framework and plan, not a completed outcome evaluation.'},
    {id:BUDGET_SOURCE,name:'Approved Estimates of Revenue and Expenditure FY 2026-2027',publisher:'Ministry of Finance, Government of Belize',url:BUDGET_URL,status:'ready',retrieved_at:budgetReceipt.requested_at,reference_period:'2023/24 actual through 2028/29 forward estimate',geographic_level:'national and ministry/programme',raw_path:'raw/supplemental-country-sources/BLZ/plans_budgets_implementation_evaluation-approved-estimates-2026-2027.pdf',sha256:budgetReceipt.sha256,license,note:'Official approved estimates. Tables keep actual, budget, projected out-turn and forward-estimate columns distinct; financial execution evidence is not converted into plan-achievement or evaluation claims.'}
  ];
  dataset.sources=[...dataset.sources.filter(row=>![PLAN_SOURCE,BUDGET_SOURCE].includes(row.id)),...sourceRows];
  const docs=[
    {id:'blz-mtds-2022-2026',territory_id:'BLZ',category:'plan',title:'#planBelize Medium-Term Development Strategy 2022-2026',kind:'official-plan',url:PLAN_URL,availability:'body_acquired',official_status:'unverified',source_id:PLAN_SOURCE,period:'2022-2026',target_period:{label:'2022-2026',kind:'multi_year'}},
    {id:'blz-mtds-mel-framework-2022-2026',territory_id:'BLZ',category:'reference',title:'MTDS implementation, monitoring, evaluation and learning framework',kind:'official-guidance',url:PLAN_URL,availability:'body_acquired',official_status:'unverified',source_id:PLAN_SOURCE,period:'2022-2026',target_period:{label:'2022-2026',kind:'multi_year'}},
    {id:'blz-approved-budget-2026-2027',territory_id:'BLZ',category:'budget',title:'Approved Estimates of Revenue and Expenditure FY 2026-2027',kind:'official-budget',url:BUDGET_URL,availability:'body_acquired',official_status:'unverified',source_id:BUDGET_SOURCE,period:'2026-2027',target_period:{label:'2026-2027',kind:'multi_year'}},
    {id:'blz-budget-actuals-outturn-2023-2026',territory_id:'BLZ',category:'implementation',title:'Financial actuals and projected out-turn in the FY 2026-2027 approved estimates',kind:'official-financial-results',url:BUDGET_URL,availability:'body_acquired',official_status:'unverified',source_id:BUDGET_SOURCE,period:'2023/24 actuals through 2025/26 projected out-turn',target_period:{label:'2023/24 actuals through 2025/26 projected out-turn',kind:'multi_year'}}
  ];
  const docIds=new Set(docs.map(row=>row.id));dataset.documents=[...dataset.documents.filter(row=>!docIds.has(row.id)),...docs];
  const checkedAt=new Date().toISOString();
  dataset.planning.update={status:'current',message:'Belize planning and budget evidence was refreshed from official 2022-2026 strategy and FY 2026-2027 approved estimates; the absence of a separate completed MTDS outcome evaluation remains explicit.',checked_at:checkedAt,last_success_at:checkedAt};

  const validation=validateDataset(dataset);if(validation.errors.length)throw new Error(validation.errors.join('; '));
  dataset.generated_at=new Date().toISOString();const content=JSON.stringify(dataset,null,2)+'\n';await writeFile(dataPath,content);await generateSite({dataset,outDir:root});
  const audit={schema_version:'1.0',generated_at:new Date().toISOString(),country_area_id:'BLZ',status:'inspected_official_plan_budget_and_financial_implementation_evidence',edition_domain_complete:true,documents:[{source_id:PLAN_SOURCE,sha256:planReceipt.sha256,pages:44,findings:['Chapter 7 defines implementation, monitoring, periodic evaluation and continuous learning arrangements.','Chapter 8 connects strategy delivery to budget allocations, investment and resource mobilization.']},{source_id:BUDGET_SOURCE,sha256:budgetReceipt.sha256,pages:376,findings:['Tables distinguish 2023/24 actual, 2024/25 actual, 2025/26 budget, 2025/26 projected out-turn, 2026/27 budget and forward estimates.','Financial results are implementation evidence and are not represented as official evaluation or plan achievement.']}],unresolved:['No separate completed official MTDS outcome-evaluation report was acquired.'],evidence_policy:'Plan, budget, financial implementation and official evaluation are separate evidence types. Missing evaluation results are not inferred from monitoring arrangements or budget execution.'};
  await Promise.all([writeFile(path.join(evidenceDir,'SOURCE_PREFLIGHT.json'),JSON.stringify(preflight,null,2)+'\n'),writeFile(path.join(evidenceDir,'BLZ_PLANNING_INTEGRATION_AUDIT.json'),JSON.stringify(audit,null,2)+'\n'),writeFile(path.join(evidenceDir,'validation.json'),JSON.stringify({...validation,dataset_sha256:createHash('sha256').update(content).digest('hex'),checked_at:new Date().toISOString()},null,2)+'\n')]);
  return {country_area_id:'BLZ',status:audit.status,documents:docs.length,validation_errors:validation.errors,validation_warnings:validation.warnings};
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['project','receipts']);if(args.help||!args.project||!args.receipts)console.log('node scripts/update-belize-planning-evidence.mjs --project <directory> --receipts <receipt.json>');else console.log(JSON.stringify(await updateBelizePlanningEvidence(args),null,2));}catch(error){reportError(error);}
}

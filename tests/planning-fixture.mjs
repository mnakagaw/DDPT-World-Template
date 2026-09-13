import {hierarchyFixture} from './hierarchy-fixture.mjs';

// Synthetic A/B/C evidence only. No values, approvals or documents describe a real country.
export function planningFixture(scenario='integrated') {
  const mode=({A:'integrated',B:'scattered',C:'partial'})[scenario] || scenario;
  if(!['integrated','scattered','partial'].includes(mode))throw new Error('Unknown fictional planning scenario');
  const data=hierarchyFixture();
  data.country.name=`Synthetic planning ${mode}`;
  data.collection.notes.push('All planning documents, official statuses and findings are fictional test evidence.');
  for(const id of ['city','district']) {
    const area=data.territories.find(row=>row.id===id);
    area.name='River Local Government';area.valid_from='2020-01-01';area.valid_to='2030-12-31';
  }
  const source=(id,name,status='ready')=>({id,name,publisher:'Synthetic test authority',url:`https://example.org/planning/${id}`,retrieved_at:'2026-09-13T00:00:00Z',reference_period:'2025/26',status,raw_path:`raw/${id}.pdf`,sha256:'3'.repeat(64),license:'Synthetic fixture only'});
  data.sources.push(source('identity-register','Synthetic historical identity register'),source('plan-body','Synthetic adopted plan'),source('budget-body','Synthetic budget report'),source('results-body','Synthetic implementation report'),source('evaluation-body','Synthetic official evaluation'),source('guidance','Synthetic country guidance'));
  const evidence=(source_id,locator='PDF page 4, table 2')=>({source_id,locator,checked_at:'2026-09-13T00:00:00Z'});
  const match=id=>{
    const area=data.territories.find(row=>row.id===id);
    return {territory_id:id,country_id:data.country.id,type:area.type,code_system:area.code_system,official_code:area.official_code,boundary_version:area.boundary_version,valid_from:area.valid_from,valid_to:area.valid_to,method:'Exact synthetic registry code and entity type',...evidence('identity-register',`Registry row ${id}`)};
  };
  const fiscal={label:'2025/26',kind:'fiscal_year',start:'2025-07-01',end:'2026-06-30'};
  const planPeriod={label:'2025/26–2029/30',kind:'multi_year',start:'2025-07-01',end:'2030-06-30'};
  const document=(id,territory_id,category,title,source_id,period=fiscal)=>({id,territory_id,category,title,kind:`synthetic-${category}`,url:`https://example.org/planning/${id}`,period:period.label,target_period:{...period},availability:'content_verified',official_status:'unverified',source_id,territory_match:match(territory_id)});
  const finding=(kind,label,value,unit,source_id,extra={})=>({kind,label,value,value_status:'observed',unit,definition:`Synthetic published definition for ${kind}; this is not another rate or an aggregate.`,scope:'River Local Government · city only',period:{...fiscal},evidence:evidence(source_id),...extra});
  const plan=document('city-plan','city','plan','Synthetic city development plan','plan-body',planPeriod);
  plan.official_status='council_adopted';
  plan.official_evidence={...evidence('plan-body','PDF page 2, synthetic council resolution'),'authority':'Synthetic City Council'};
  plan.content={summary:'Published synthetic priorities for the city, supported by the retained source.',priorities:['Water access','Local service reliability'],objectives:['Maintain verified baseline evidence','Review local priorities with participants'],evidence:evidence('plan-body','PDF pages 5–7')};
  const budget=document('city-budget','city','budget','Synthetic city budget and execution','budget-body');
  budget.findings=[finding('budget','Approved budget',1000,'test currency thousands','budget-body'),finding('revenue','Cumulative revenue',200,'test currency thousands','budget-body'),finding('expenditure','Cumulative expenditure',0,'test currency thousands','budget-body'),finding('budget_execution','Budget execution rate',0,'%','budget-body',{definition:'Synthetic cumulative expenditure / approved budget × 100; 0 is a published observed rate.'})];
  const results=document('city-results','city','implementation','Synthetic implementation results','results-body');
  results.findings=[finding('implementation_result','Reported completed actions',2,'actions','results-body'),finding('plan_achievement','Published plan achievement rate',25,'%','results-body',{definition:'Synthetic completed planned milestones / planned milestones × 100. This is not budget execution.'})];
  const evaluation=document('city-evaluation','city','evaluation','Synthetic official evaluation','evaluation-body');
  evaluation.findings=[finding('official_evaluation','Published evaluation score',3,'points','evaluation-body',{scale:{min:0,max:5,label:'Synthetic published 0–5 evaluation scale'},definition:'Published official evaluation score on its own source scale; not a budget or plan completion rate.'}),{kind:'official_evaluation',label:'Published qualitative finding',statement:'Synthetic source describes incomplete reporting for one activity.',definition:'Qualitative evaluation finding, not a numerical score.',scope:'River Local Government · city only',period:{...fiscal},evidence:evidence('evaluation-body','PDF page 9, conclusion 1')}];
  const district=document('district-plan','district','plan','Synthetic district plan — same name, different authority','plan-body',planPeriod);
  district.availability='body_acquired';district.official_status='unverified';
  const reference={id:'national-guidance',territory_id:'TST',category:'reference',title:'Synthetic national planning guidance',kind:'guidance',url:'https://example.org/planning/guidance',period:'2025',target_period:{label:'2025',kind:'calendar_year',start:'2025-01-01',end:'2025-12-31'},availability:'body_acquired',official_status:'unverified',source_id:'guidance'};
  data.planning={
    title:'Planning evidence and resources',purpose:'Use acquired local sources without inferring plan approval or filling missing parent evidence.',
    sections:[{id:'plan',label:'Development plans'},{id:'budget',label:'Budgets and expenditure'},{id:'implementation',label:'Implementation results'},{id:'evaluation',label:'Published evaluations'},{id:'reference',label:'Guidance and references'}],
    system:{label:'Synthetic planning system',scope:'Fictional city and district authorities',cycle:'Synthetic 2025/26–2029/30 cycle',source_ids:['guidance']},
    map:{mode:'official_status',category:'plan',period:planPeriod.label,statuses:[{id:'council_adopted',label:'Documented synthetic adoption',color:'#246f5e'},{id:'draft_published',label:'Published synthetic draft',color:'#9b6d20'}]},
    related_links:[{label:'Existing local finance view',url:'./thematic/',territory_id:'city'},{label:'Synthetic source catalogue',url:'https://example.org/planning/'}],
    update:{status:'current',checked_at:'2026-09-13T00:00:00Z',last_success_at:'2026-09-12T00:00:00Z',message:'Synthetic source check completed.'}
  };
  data.documents=[plan,budget,results,evaluation,district,reference];
  data.gaps=[{category:'country_guidance',status:'unverified',detail:'This entire fixture is synthetic.',next_action:'Use only for tests.'},{category:'planning_documents',status:'not_collected',territory_id:'north',detail:'No Northern Test Region documents are collected.',next_action:'Do not inherit city documents.'},{category:'district_content',status:'not_collected',territory_id:'district',source_id:'plan-body',detail:'District plan body has not been verified for narrative extraction.',next_action:'Read the exact district source.'}];
  if(mode==='scattered') {
    data.planning.sections=[{id:'plan',label:'Local plans'},{id:'budget',label:'Fiscal documents'}];
    data.planning.map={mode:'coverage',category:'plan'};
    delete data.planning.system;
    delete plan.content;delete plan.official_evidence;plan.availability='link_verified';plan.official_status='unverified';delete plan.territory_match;
    budget.availability='content_extracted';delete budget.findings;
    data.planning.update={status:'stopped',checked_at:'2026-09-13T00:00:00Z',last_success_at:'2026-08-20T00:00:00Z',message:'Synthetic collection stopped after source discovery; old evidence remains labelled.'};
  }
  if(mode==='partial') {
    data.planning.sections=[{id:'plan',label:'Plans',empty_message:'No acquired local plan in the selected period.'}];
    data.planning.outputs=[];
    data.planning.map={mode:'coverage'};
    delete data.planning.system;
    data.documents=[{...plan,availability:'unavailable',official_status:'unknown',content:undefined,official_evidence:undefined,territory_match:undefined},reference];
    // JSON roundtrip below removes absent optional fields, like a canonical on-disk dataset.
    data.gaps.push({category:'city_plan',status:'unavailable',territory_id:'city',source_id:'plan-body',detail:'Synthetic city plan source is not accessible; approval is unknown.',next_action:'Request the source from its authority.'});
  }
  return JSON.parse(JSON.stringify(data));
}
export function planningScenarios() {return {A:planningFixture('integrated'),B:planningFixture('scattered'),C:planningFixture('partial')};}

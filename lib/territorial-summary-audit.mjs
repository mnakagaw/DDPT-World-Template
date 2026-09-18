import {territorialIndicatorState,evidenceRows,observedValue} from '../scaffold/site/model.mjs';

const latest=rows=>[...rows].sort((a,b)=>String(b.period).localeCompare(String(a.period),'en',{numeric:true}))[0] || null;
const same=(a,b)=>Object.is(a,b);

export function auditTerritorialSummaries(dataset,{territoryIds=null}={}) {
  const selectedIds=new Set(territoryIds || dataset.territories.filter(area=>area.type==='country').map(area=>area.id));
  const errors=[],checks=[];
  for(const territory of dataset.territories.filter(area=>selectedIds.has(area.id))) {
    const exported=new Map(evidenceRows(dataset,territory.id,'latest-available').map(row=>[row.indicator.id,row]));
    for(const indicator of dataset.indicators) {
      const rows=dataset.observations.filter(row=>row.territory_id===territory.id&&row.indicator_id===indicator.id&&observedValue(row)!==null);
      if(!rows.length)continue;
      const expected=latest(rows),summary=territorialIndicatorState(dataset,territory.id,indicator.id,'latest-available'),output=exported.get(indicator.id);
      const expectedStatus=expected.provenance==='calculated'?'calculated':expected.status;
      const identity=`${territory.id}|${indicator.id}`;
      for(const [label,actual,wanted] of [
        ['summary value',summary.result.value,expected.value],
        ['summary period',String(summary.period),String(expected.period)],
        ['summary source',summary.result.row?.source_id,expected.source_id],
        ['summary status',summary.result.status,expectedStatus],
        ['export value',output?.value,expected.value],
        ['export period',String(output?.period),String(expected.period)],
        ['export source',output?.row?.source_id,expected.source_id],
        ['export status',output?.status,expectedStatus]
      ])if(!same(actual,wanted))errors.push(`${identity}: ${label} ${JSON.stringify(actual)} != ${JSON.stringify(wanted)}`);
      checks.push({territory_id:territory.id,indicator_id:indicator.id,period:String(expected.period),value:expected.value,source_id:expected.source_id,status:expectedStatus});
      for(const row of rows) {
        const explicit=territorialIndicatorState(dataset,territory.id,indicator.id,String(row.period));
        const explicitStatus=row.provenance==='calculated'?'calculated':row.status;
        if(!same(explicit.result.value,row.value)||String(explicit.period)!==String(row.period)||explicit.result.row?.source_id!==row.source_id||explicit.result.status!==explicitStatus)errors.push(`${identity}|${row.period}: explicit period does not reproduce value, period, source and status`);
      }
    }
  }
  return {
    ok:errors.length===0,
    territory_count:selectedIds.size,
    latest_indicator_checks:checks.length,
    explicit_observation_checks:dataset.observations.filter(row=>selectedIds.has(row.territory_id)&&observedValue(row)!==null).length,
    zero_value_checks:checks.filter(row=>row.value===0).length,
    checks,
    errors
  };
}

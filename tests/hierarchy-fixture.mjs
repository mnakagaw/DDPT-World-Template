// Entirely fictional data for hierarchy regression and browser QA. Not country statistics.
export function hierarchyFixture() {
  const area=(id,name,level,parent_id,type=level)=>({id,name,level,type,parent_id,official_code:id==='TST'?null:id,code_system:'Fictional test identifiers',boundary_version:id==='TST'?null:'test-edition-1'});
  const territories=[
    area('TST','Hierarchy test country','national',null,'country'),
    area('north','Northern Test Region','region','TST'),
    area('south','Southern Test Region','region','TST'),
    area('nile','River Test Subregion','subregion','north'),
    area('lake','Lake Test Subregion','subregion','north'),
    area('district','River Test District','district','nile'),
    area('city','River Test City','city','nile'),
    area('other-city','Lake Test City','city','lake'),
    ...Array.from({length:24},(_,index)=>area(`city-${String(index+1).padStart(2,'0')}`,`Test City ${String(index+1).padStart(2,'0')}`,'city','nile'))
  ];
  const observation=(territory_id,value,indicator_id='population',period='2024')=>({territory_id,indicator_id,period,value,status:'observed',source_id:'test-source'});
  const polygon=(id,x,y,size)=>({type:'Feature',properties:{territory_id:id,source_id:'test-boundaries'},geometry:{type:'Polygon',coordinates:[[[x,y],[x+size,y],[x+size,y+size],[x,y+size],[x,y]]]}});
  return {
    schema_version:'0.2',generated_at:'2026-09-13T00:00:00.000Z',
    country:{id:'TST',iso2:'TS',name:'Hierarchy test country',requested_name:'Fictional QA fixture',locale:'en',national_territory_id:'TST',geography_note:'Fictional hierarchy for browser regression only. No real country observations.'},
    territories,
    indicators:[{id:'population',name:'Test population',theme:'Population',unit:'people',definition:'Fictional values, not real country data.',source_id:'test-source',aggregation:'none',measurement_method:'source_reported'},{id:'water',name:'Test water',theme:'Services',unit:'%',definition:'Fictional service indicator.',source_id:'test-source',aggregation:'none',measurement_method:'source_reported'}],
    // Northern intentionally has NO observations. Its children must never be summed or reused.
    observations:[observation('TST',1000),observation('nile',400),observation('lake',250),observation('south',300),observation('city',100),observation('district',80),observation('other-city',40),observation('TST',70,'water'),observation('city',55,'water'),observation('nile',61,'water'),observation('city',90,'population','2023'),...Array.from({length:23},(_,index)=>observation(`city-${String(index+1).padStart(2,'0')}`,500+index))],
    sources:[{id:'test-source',name:'Fictional regression fixture',publisher:'Test suite',url:'https://example.org/test-data',retrieved_at:'2026-09-13T00:00:00Z',reference_period:'2023:2024',status:'ready',sha256:'1'.repeat(64),raw_path:'test-fixture',license:'Fictional data'},{id:'test-boundaries',name:'Fictional test boundaries',publisher:'Test suite',url:'https://example.org/test-boundaries',retrieved_at:'2026-09-13T00:00:00Z',reference_period:'test-edition-1',status:'ready',sha256:'2'.repeat(64),raw_path:'test-fixture',license:'Fictional data'}],
    boundaries:{type:'FeatureCollection',features:[polygon('north',0,0,8),polygon('south',0,-8,7),polygon('nile',0,0,4),polygon('lake',4,0,4),polygon('city',0,0,1),polygon('district',1,0,3),polygon('other-city',4,0,2),...Array.from({length:24},(_,index)=>polygon(`city-${String(index+1).padStart(2,'0')}`,0.4+(index%6)*0.5,1+Math.floor(index/6)*0.5,0.4))]},
    documents:[{id:'city-plan',territory_id:'city',title:'Fictional city-only planning reference',url:'https://example.org/city-only-plan',period:'2024',kind:'published-plan',availability:'link_verified',official_status:'unverified',source_id:'test-source'}],
    gaps:[{category:'test_fixture',status:'not_applicable',detail:'For local testing only. Northern parent data are deliberately absent.',next_action:'Verify no child data appear as parent totals.'}],
    collection:{status:'partial',adapters:['fictional-hierarchy-test'],notes:['Not real country data.']}
  };
}

// Completely synthetic world + country hierarchy for regression and browser QA.
// No names, numeric observations or polygons in this fixture represent real evidence.
export function analysisFixture() {
  const territory=(id,name,level,type,parent_id,country_id)=>({id,name,level,type,parent_id,official_code:id==='WLD'?null:id,code_system:'Fictional IDs',boundary_version:country_id?'test-local-1':null,...(country_id?{country_id}:{})});
  const territories=[
    territory('WLD','Synthetic world','national','exploration_scope',null),
    territory('americas','Synthetic Americas','continent','continent','WLD'),
    territory('central-caribbean','Synthetic Central America and Caribbean','macroregion','macroregion','americas'),
    territory('TST','Test country','country','country','central-caribbean','TST'),
    territory('north','Northern Test Region','region','region','TST','TST'),
    territory('south','Southern Test Region','region','region','TST','TST'),
    territory('river','River Test Province','province','province','north','TST'),
    territory('lake','Lake Test Province','province','province','north','TST'),
    territory('city','Same name','municipality','city','river','TST'),
    territory('municipality','Same name','municipality','municipality','river','TST'),
    territory('missing-city','Missing Test City','municipality','city','river','TST'),
    territory('city-ward','Fictional city ward','ward','ward','city','TST'),
    territory('other-continent','Other Synthetic Continent','continent','continent','WLD'),
    territory('OTH','Other test country','country','country','other-continent','OTH'),
    territory('other-region','Other Test Region','region','region','OTH','OTH'),
    ...Array.from({length:27},(_,i)=>territory(`extra-${i+1}`,`Extra Test Municipality ${i+1}`,'municipality','municipality','river','TST'))
  ];
  const source=(id,geographic_level,country_id)=>({id,name:`Fictional ${id}`,url:`https://example.org/${id}`,publisher:'Synthetic fixture',retrieved_at:'2026-09-13T00:00:00Z',status:'ready',license:'Fictional data',...(geographic_level?{geographic_level}:{}),...(country_id?{country_id}:{})});
  const observation=(territory_id,value,indicator_id='people',source_id='local',period='2024')=>({territory_id,indicator_id,period,value,status:value===null?'missing':'observed',source_id});
  const config=(parent_id,member_ids,label)=>({parent_id,member_ids,label,membership_note:'Fictional source-backed membership declaration for synthetic regression only.',source_ids:['membership']});
  return {
    schema_version:'0.2',generated_at:'2026-09-13T00:00:00Z',country:{id:'WLD',name:'Synthetic world QA',requested_name:'World fixture',locale:'en',national_territory_id:'WLD',geography_note:'Entirely fictional; parent statistics are intentionally absent.'},territories,
    analysis:{kind:'world',terminal_territory_ids:[],comparisons:[config('WLD',['TST','OTH'],'Test countries across the synthetic world'),config('americas',['TST'],'Test countries in the Americas'),config('river',['city','municipality','missing-city',...Array.from({length:27},(_,i)=>`extra-${i+1}`)],'Test municipalities')],country_sites:[{territory_id:'TST',country_id:'TST',url:'./countries/TST/territorial/',indicator_map:{people:'population'}}]},
    indicators:[{id:'people',name:'Test population',theme:'Population',unit:'people',definition:'Fictional resident population.',definition_id:'resident-count',population:'All usual residents',measurement_method:'source_reported',aggregation:'official_only',source_id:'local'},{id:'water',name:'Test water access',theme:'Services',unit:'%',definition:'Fictional households with service access.',population:'Households',measurement_method:'source_reported',aggregation:'weighted_rate',source_id:'local'}],
    observations:[observation('TST',1000,'people','national-tst'),observation('OTH',2000,'people','national-oth'),observation('south',300),observation('river',400),observation('lake',null),observation('city',0),observation('municipality',100),observation('city',90,'people','local','2023'),observation('TST',70,'water','national-tst'),observation('city',0,'water'),observation('municipality',90,'water'),...Array.from({length:27},(_,i)=>observation(`extra-${i+1}`,i+1))],
    sources:[source('local'),source('membership'),source('geometry'),source('national-tst','national','TST'),source('national-oth','national','OTH')],
    boundaries:{type:'FeatureCollection',features:territories.filter(area=>area.id!=='missing-city' && area.id!=='WLD').map((area,i)=>{const x=(i%8)*3-15,y=Math.floor(i/8)*3;return {type:'Feature',properties:{territory_id:area.id,official_code:area.official_code,code_system:area.code_system,boundary_version:area.boundary_version,source_id:'geometry'},geometry:{type:'Polygon',coordinates:[[[x,y],[x+2,y],[x+2,y+2],[x,y+2],[x,y]]]}};})},
    documents:[],gaps:[{category:'test_fixture',status:'not_applicable',detail:'Fictional data; Northern parent and Missing Test City have no statistics.',next_action:'Verify empty parents never reuse child values.'}],collection:{status:'partial',adapters:['synthetic-analysis-fixture'],notes:['Not country statistics.']}
  };
}

export function fixture() {
  return {
    schema_version:'0.2', generated_at:'2026-09-13T00:00:00Z',
    country:{id:'TST',iso2:'TS',name:'Test country — synthetic fixture',requested_name:'Test',locale:'en',national_territory_id:'TST',geography_note:'Synthetic test only'},
    territories:[
      {id:'TST',name:'Test country',level:'national',type:'country',parent_id:null,official_code:null,code_system:'test',boundary_version:null},
      {id:'TST-A',name:'Same name',level:'adm1',type:'province',parent_id:'TST',official_code:'01',code_system:'synthetic',boundary_version:'test-1'},
      {id:'TST-B',name:'Same name',level:'adm1',type:'city',parent_id:'TST',official_code:'02',code_system:'synthetic',boundary_version:'test-1'}
    ],
    indicators:[{id:'people',name:'Population',theme:'Population',unit:'people',definition:'Synthetic test count',source_id:'test',aggregation:'none',measurement_method:'source_reported'}],
    observations:[{territory_id:'TST',indicator_id:'people',period:'2024',value:100,status:'observed',source_id:'test'},{territory_id:'TST-A',indicator_id:'people',period:'2024',value:0,status:'observed',source_id:'test'},{territory_id:'TST-B',indicator_id:'people',period:'2024',value:null,status:'missing',source_id:'test'}],
    sources:[{id:'test',name:'Synthetic test source',url:'https://example.org/data',publisher:'Test',retrieved_at:'2026-09-13T00:00:00Z',reference_period:'2024',status:'ready',sha256:'a'.repeat(64),raw_path:'raw/test.json',license:'Synthetic fixture'}],
    boundaries:{type:'FeatureCollection',features:[{type:'Feature',properties:{territory_id:'TST-A'},geometry:{type:'Polygon',coordinates:[[[30,0],[31,0],[31,1],[30,1],[30,0]]]}}]},
    documents:[],gaps:[{category:'planning',status:'not_collected',detail:'Synthetic fixture',next_action:'Test only'}],collection:{status:'partial',adapters:['synthetic'],notes:[]}
  };
}

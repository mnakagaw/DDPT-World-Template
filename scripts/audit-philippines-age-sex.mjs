import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const index=process.argv.indexOf('--project');
if(index<0||!process.argv[index+1])throw new Error('Provide --project <country directory>');
const project=path.resolve(process.argv[index+1]);
const raw=path.join(project,'raw','popcen-catalogue-2024');
const sourceFile=path.join(raw,'0201A6DPAG0-all-data.json');
const metadataFile=path.join(raw,'0201A6DPAG0-metadata.json');
const readJson=file=>JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));
const sourceBytes=fs.readFileSync(sourceFile);
const source=readJson(sourceFile),metadata=readJson(metadataFile);
const dimensions=new Map(metadata.variables.map(variable=>[variable.code,variable]));
const age=dimensions.get('Age Group'),geography=dimensions.get('Geographic Location'),sex=dimensions.get('Sex');
if(!age||!geography||!sex||source.data.length!==age.values.length*geography.values.length*sex.values.length)
  throw new Error('Unexpected 2024 POPCEN age/sex table dimensions');
const names=new Map(geography.values.map((code,i)=>[code,geography.valueTexts[i].replace(/^\.+/,'').trim()]));
const cells=new Map();
for(const row of source.data){
  const key=row.key.join('|'),value=Number(row.values[0]);
  if(cells.has(key)||!Number.isSafeInteger(value)||value<0)throw new Error(`Invalid or repeated cell: ${key}`);
  cells.set(key,value);
}
const get=(a,g,s)=>{
  const key=`${a}|${g}|${s}`;
  if(!cells.has(key))throw new Error(`Missing cell: ${key}`);
  return cells.get(key);
};
const sexMismatches=[],ageMismatches=[];
for(const g of geography.values){
  for(const a of age.values){
    const both=get(a,g,'0'),male=get(a,g,'1'),female=get(a,g,'2');
    if(both!==male+female)sexMismatches.push({geography_code:g,geography_name:names.get(g),age_code:a,age_group:age.valueTexts[age.values.indexOf(a)],both,male,female,sex_sum:male+female,difference:both-male-female});
  }
  for(const s of sex.values){
    const all=get('0',g,s),ageSum=age.values.slice(1).reduce((sum,a)=>sum+get(a,g,s),0);
    if(all!==ageSum)ageMismatches.push({geography_code:g,geography_name:names.get(g),sex_code:s,sex:sex.valueTexts[sex.values.indexOf(s)],all_ages:all,age_sum:ageSum,difference:all-ageSum});
  }
}
const affectedGeographies=[...new Set(sexMismatches.map(row=>row.geography_code))];
const pattern=affectedGeographies.every(g=>
  get('17',g,'0')-get('17',g,'1')-get('17',g,'2')===get('18',g,'1')+get('18',g,'2')&&
  age.values.slice(1).reduce((sum,a)=>sum+get(a,g,'0'),0)-get('0',g,'0')===get('18',g,'0')
);
const report={
  source_table_id:'0201A6DPAG0.px',
  source_url:'https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/1A/PO_2024/0201A6DPAG0.px',
  source_file:path.relative(project,sourceFile).replaceAll('\\','/'),
  source_sha256:crypto.createHash('sha256').update(sourceBytes).digest('hex'),
  source_rows:source.data.length,
  geography_count:geography.values.length,
  age_groups:age.values.length,
  sex_categories:sex.values.length,
  sex_mismatch_count:sexMismatches.length,
  age_sum_mismatch_count:ageMismatches.length,
  affected_geography_count:affectedGeographies.length,
  shared_high_age_mismatch_pattern:pattern,
  disposition:'Do not adopt age-by-sex profiles or infer corrected values until the PSA table definition or corrigendum resolves the inconsistent published cells.',
  sex_mismatches:sexMismatches,
  age_sum_mismatches:ageMismatches
};
const output=path.join(project,'evidence','PHL_POPCEN_2024_AGE_SEX_ARITHMETIC.json');
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({output,source_sha256:report.source_sha256,source_rows:report.source_rows,sex_mismatch_count:report.sex_mismatch_count,age_sum_mismatch_count:report.age_sum_mismatch_count,affected_geography_count:report.affected_geography_count,shared_high_age_mismatch_pattern:pattern}));

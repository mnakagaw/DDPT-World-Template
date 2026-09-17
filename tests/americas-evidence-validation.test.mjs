import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {validateAmericasEvidence} from '../scripts/validate-americas-evidence.mjs';

test('Americas evidence validator rejects blank WPP identity and future usable wording',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'americas-evidence-'));
  try{
    await mkdir(path.join(root,'data'),{recursive:true});await mkdir(path.join(root,'evidence'),{recursive:true});
    await writeFile(path.join(root,'data/dashboard.json'),JSON.stringify({territories:[{id:'BVT',type:'country'},{id:'USA',type:'country'}]}));
    await writeFile(path.join(root,'evidence/SOURCE_PREFLIGHT.json'),JSON.stringify({countries:[{country_area_id:'BVT',latest_census:{note:'Latest identified/usable year: 2030.'},recent_census_rounds:[{year:2030}]},{country_area_id:'USA',latest_census:{note:'Latest scheduled/identified round: 2030. Results are not acquired or usable.'},recent_census_rounds:[{year:2030}]}]}));
    await writeFile(path.join(root,'evidence/SOURCE_DISPOSITION.csv'),'record_type,country_area_id,source_id,source_table_or_field,indicator_id,disposition\nwpp_country_area_adoption,,wrong,Total Population as of 1 January,UN_WPP_POP_TOTL,adopted\n');
    const result=await validateAmericasEvidence(root);
    assert.equal(result.ok,false);assert.ok(result.errors.some(error=>/blank/.test(error)));assert.ok(result.errors.some(error=>/identified\/usable/.test(error)));assert.ok(result.errors.some(error=>/1 July/.test(error)));
  }finally{await rm(root,{recursive:true,force:true});}
});

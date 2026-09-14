import {collectCensusSources} from '../lib/collect-census.mjs';
import {parseArgs,isMain,reportError} from '../lib/cli.mjs';

export async function collectCentralAmericaCensus({out,reuse}={}){
  const result=await collectCensusSources({outDir:out||'.work/central-america-census',reuseDir:reuse});
  const {summary}=result.receipt;
  console.log(`Census acquisition: ${summary.acquired}/${summary.requested} acquired; ${summary.required_failed} required failed.`);
  console.log(`Receipt: ${result.outDir}\\receipt.json`);
  if(summary.required_failed)throw new Error('Required census originals were not all acquired. Review receipt.json; successful files remain immutable evidence.');
  return result;
}

if(isMain(import.meta.url)){
  try{const args=parseArgs(process.argv.slice(2),['out','reuse']);if(args.help)console.log('node scripts/collect-central-america-census.mjs --out .work/central-america-census-YYYY-MM-DD [--reuse .work/prior-census-acquisition]');else await collectCentralAmericaCensus({out:args.out,reuse:args.reuse});}catch(error){reportError(error);}
}

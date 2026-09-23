import {mkdir, writeFile, copyFile, readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {escapeHtml, nationalOnly, regionalCoverageSummary} from '../scaffold/site/model.mjs';
import {planningSettings} from '../scaffold/site/planning.mjs';

const scaffold = fileURLToPath(new URL('../scaffold/site/', import.meta.url));
const templateVersion=createRequire(import.meta.url)('../package.json').version;
const pages = {home:'Explore', territorial:'Territorial diagnostic', thematic:'Thematic diagnostic', database:'Database', planning:'Planning and resources'};

export function pageShell({country, page='home'}) {
  if (!(page in pages)) throw new Error(`Unknown generated page: ${page}`);
  const prefix=page==='home'?'./':'../';
  const links=Object.entries(pages).map(([key,label])=>`<a href="${prefix}${key==='home'?'':key+'/'}" data-page-link="${key}" data-i18n="${escapeHtml(label)}"${key===page?' aria-current="page"':''}>${escapeHtml(label)}</a>`).join('');
  const locale=/^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(country.locale || '')?country.locale:'en';
  const assetQuery=`?v=${encodeURIComponent(templateVersion)}`;
  return `<!doctype html>
<html lang="${escapeHtml(locale)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="description" content="Explore population and everyday life through census and regional statistics. Compare places and find data for research and regional planning.">
<title>${escapeHtml(pages[page])} — ${escapeHtml(country.name)}</title>
<link rel="stylesheet" href="${prefix}assets/styles.css${assetQuery}">
<script type="module" src="${prefix}assets/app.mjs${assetQuery}"></script>
</head>
<body data-page="${page}" id="top">
<a class="skip-link" href="#app" data-i18n="Skip to content">Skip to content</a>
<header class="site-header"><div class="header-inner"><div class="header-bar"><a class="brand" data-brand-link href="${prefix}" title="Return to the AreaData start"><span class="brand-mark" aria-hidden="true">A</span><span class="brand-title"><span>AreaData</span><small id="dataset-name" data-i18n="Explore the world through census data">Explore the world through census data</small></span></a><nav class="primary-nav" aria-label="Main pages">${links}</nav><div class="header-tools"><span class="language-caption" aria-hidden="true">LANG</span><div class="language-switcher" role="group" aria-label="Language" data-i18n-skip><button type="button" data-language="en" aria-label="English" aria-pressed="false">EN</button><button type="button" data-language="es" aria-label="Spanish" aria-pressed="false">ES</button><button type="button" data-language="ja" aria-label="Japanese" aria-pressed="false">日本語</button></div></div></div></div></header>
<main id="app" class="page-container" tabindex="-1"><p role="status">Loading acquired evidence…</p><noscript><h1>JavaScript is needed for this dashboard</h1><p>Use the local server to open the interactive pages. The acquired dataset is available as <a href="${prefix}data/dashboard.json">dashboard.json</a>.</p></noscript></main>
<footer class="site-footer" data-i18n="AreaData · Census and regional statistics for research and planning">AreaData · Census and regional statistics for research and planning</footer>
</body></html>
`;
}

/** Create a portable static site. The caller validates and saves the canonical dataset. */
const sha256=value=>createHash('sha256').update(value).digest('hex');

export async function generateSite({dataset, outDir, canonicalSha256=null}) {
  if(!dataset?.country?.id || !Array.isArray(dataset.territories) || !Array.isArray(dataset.indicators) || !Array.isArray(dataset.observations)) throw new Error('generateSite requires a validated dashboard dataset');
  if(!outDir || typeof outDir!=='string')throw new Error('generateSite requires outDir');
  const projectDir=path.resolve(outDir), siteDir=path.join(projectDir,'site');
  await mkdir(path.join(siteDir,'assets'),{recursive:true});
  await mkdir(path.join(siteDir,'data'),{recursive:true});
  await mkdir(path.join(siteDir,'data','countries'),{recursive:true});
  const files=[];
  for(const page of Object.keys(pages)) {
    const directory=page==='home'?siteDir:path.join(siteDir,page);
    await mkdir(directory,{recursive:true});
    const filename=path.join(directory,'index.html');
    await writeFile(filename,pageShell({country:dataset.country,page}),'utf8');files.push(filename);
  }
  for(const file of ['app.mjs','model.mjs','analysis.mjs','aggregation.mjs','census-history.mjs','diagnostic.mjs','i18n.mjs','planning.mjs','planning-view.mjs','styles.css']) {
    const destination=path.join(siteDir,'assets',file);
    if(file.endsWith('.mjs')) {
      const source=await readFile(path.join(scaffold,file),'utf8');
      // Version nested modules too: a fresh entry point can otherwise import a cached dictionary.
      const versioned=source.replace(/(\bfrom\s*['"])(\.\/[\w-]+\.mjs)(['"])/g,`$1$2?v=${encodeURIComponent(templateVersion)}$3`);
      await writeFile(destination,versioned,'utf8');
    } else await copyFile(path.join(scaffold,file),destination);
    files.push(destination);
  }
  const hostingConfig=path.join(siteDir,'.htaccess');
  await copyFile(path.join(scaffold,'.htaccess'),hostingConfig);files.push(hostingConfig);
  const dataFile=path.join(siteDir,'data','dashboard.json');
  // The canonical project copy remains review-friendly. The browser copy is
  // compact because country-depth boundaries and explicit missing cells make
  // pretty-printed JSON several times larger without changing its meaning.
  const countryRoots=new Map(dataset.territories.filter(area=>area.type==='country'&&area.id===area.country_id).map(area=>[area.id,area]));
  const descendantCountryIds=new Set(dataset.territories.filter(area=>area.id!==area.country_id&&countryRoots.has(area.country_id)).map(area=>area.country_id));
  let publicDataset=dataset;
  if(['world','regional'].includes(dataset.analysis?.kind)&&descendantCountryIds.size){
    const descendantIds=new Set(dataset.territories.filter(area=>descendantCountryIds.has(area.country_id)&&area.id!==area.country_id).map(area=>area.id));
    const shardManifest={},countryIntegrity={};
    for(const countryId of [...descendantCountryIds].sort()){
      const branchIds=new Set(dataset.territories.filter(area=>area.country_id===countryId).map(area=>area.id));
      const lowerIds=new Set([...branchIds].filter(id=>id!==countryId));
      const territoryById=new Map(dataset.territories.filter(area=>lowerIds.has(area.id)).map(area=>[area.id,area]));
      const branchBoundaries=(dataset.boundaries?.features||[]).filter(feature=>lowerIds.has(feature.properties?.territory_id));
      const boundariesByLevel=new Map();
      for(const feature of branchBoundaries){
        const level=territoryById.get(feature.properties?.territory_id)?.level||'unclassified';
        if(!boundariesByLevel.has(level))boundariesByLevel.set(level,[]);
        boundariesByLevel.get(level).push(feature);
      }
      const boundaryShards={},boundaryIntegrity={};let boundaryIndex=0;
      for(const [level,features] of [...boundariesByLevel.entries()].sort(([a],[b])=>a.localeCompare(b))){
        const relative=`countries/${countryId}.boundaries.${boundaryIndex++}.json`;
        const payload={schema_version:'0.1-boundary-shard',country_area_id:countryId,level,generated_at:dataset.generated_at,type:'FeatureCollection',features};
        const content=JSON.stringify(payload)+'\n',filename=path.join(siteDir,'data',relative);
        await writeFile(filename,content,'utf8');files.push(filename);
        boundaryShards[level]=relative;boundaryIntegrity[level]={sha256:sha256(content),feature_count:features.length};
      }
      const shard={schema_version:'0.2-country-shard',country_area_id:countryId,generated_at:dataset.generated_at,
        territories:dataset.territories.filter(area=>lowerIds.has(area.id)),
        observations:dataset.observations.filter(row=>lowerIds.has(row.territory_id)),
        boundaries:{type:'FeatureCollection',features:[]},boundary_shards:boundaryShards,
        documents:(dataset.documents||[]).filter(row=>branchIds.has(row.territory_id)),
        comparisons:(dataset.analysis?.comparisons||[]).filter(row=>branchIds.has(row.parent_id)&&row.parent_id!==dataset.country.national_territory_id),
        terminal_territory_ids:(dataset.analysis?.terminal_territory_ids||[]).filter(id=>lowerIds.has(id))};
      const relative=`countries/${countryId}.json`,filename=path.join(siteDir,'data',relative);
      const shardContent=JSON.stringify(shard)+'\n';
      await writeFile(filename,shardContent,'utf8');files.push(filename);shardManifest[countryId]=relative;
      countryIntegrity[countryId]={sha256:sha256(shardContent),territory_count:shard.territories.length,observation_count:shard.observations.length,boundary_count:branchBoundaries.length,boundary_shards:boundaryIntegrity,document_count:shard.documents.length,comparison_count:shard.comparisons.length};
    }
    publicDataset=structuredClone(dataset);
    publicDataset.territories=dataset.territories.filter(area=>!descendantIds.has(area.id));
    publicDataset.observations=dataset.observations.filter(row=>!descendantIds.has(row.territory_id));
    publicDataset.boundaries={...(dataset.boundaries||{}),features:(dataset.boundaries?.features||[]).filter(feature=>!descendantIds.has(feature.properties?.territory_id))};
    publicDataset.documents=(dataset.documents||[]).filter(row=>!descendantCountryIds.has(row.territory_id)&&!descendantIds.has(row.territory_id));
    publicDataset.analysis={...dataset.analysis,
      comparisons:(dataset.analysis?.comparisons||[]).filter(row=>!descendantCountryIds.has(row.parent_id)&&!descendantIds.has(row.parent_id)),
      terminal_territory_ids:(dataset.analysis?.terminal_territory_ids||[]).filter(id=>!descendantIds.has(id))};
    const fullFile=path.join(siteDir,'data','dashboard-full.json');
    const fullContent=JSON.stringify(dataset)+'\n';
    await writeFile(fullFile,fullContent,'utf8');files.push(fullFile);
    if(!canonicalSha256){
      try{canonicalSha256=sha256(await readFile(path.join(projectDir,'data','dashboard.json')));}catch{}
    }
    publicDataset.data_shards={schema_version:'1.1',base:'data/',countries:shardManifest,full:'dashboard-full.json',integrity:{canonical_sha256:canonicalSha256,full_sha256:sha256(fullContent),territory_count:dataset.territories.length,observation_count:dataset.observations.length,boundary_count:dataset.boundaries?.features?.length||0,document_count:dataset.documents?.length||0,comparison_count:dataset.analysis?.comparisons?.length||0,countries:countryIntegrity},note:'Country-depth data load when a country or one of its lower areas is selected.'};
  }
  await writeFile(dataFile,JSON.stringify(publicDataset)+'\n','utf8');files.push(dataFile);
  const statusFile=path.join(siteDir,'data','update-status.json');
  await writeFile(statusFile,JSON.stringify({status:'current',checked_at:new Date().toISOString(),last_success_at:new Date().toISOString(),data_edition:dataset.generated_at,message:'Last build validated successfully.'},null,2)+'\n');files.push(statusFile);
  const handoffPath=path.join(projectDir,'SITE_README.md');
  const lines=[
    `# ${dataset.country.name} — generated dashboard`, '',
    `Data schema: ${dataset.schema_version}. Data edition: ${dataset.generated_at}.`, '',
    '## Scope', '',
    nationalOnly(dataset)?'This initial dashboard contains national observations only. Local areas, where acquired, are selectable reference geography. Local observations and official country planning forms must be collected and verified before this can support substantive local planning. National values are never copied into local records.':'This dashboard contains some local observations. Local coverage still varies by indicator and source period; missing values and acquisition gaps remain explicit.', '',
    `- ${dataset.territories.length} territory records; ${dataset.indicators.length} indicators; ${dataset.observations.length} observation records.`,
    `- ${dataset.documents.length} acquired document records. Acquisition state does not establish official approval.`, '',
    '## Run and extend', '',
    'Serve the site directory over HTTP using the template’s scripts/serve.mjs. Double-clicking index.html uses file:// and browsers may block the JSON and module requests.',
    'The home, territorial/, thematic/, database/ and planning/ entry pages share the same local assets and dataset. Links and fetch URLs work at the domain root or below a hosting subdirectory.',
    'Add verified local observations, source records, document references and official-code joins to the canonical data/dashboard.json, validate it, then run scripts/build-country.mjs from the template. Do not patch generated site/data/dashboard.json as the canonical source.', '',
    '## Available outputs', '',
    `Adopted planning outputs: ${planningSettings(dataset).outputs.join(', ') || 'None; use original references and the country workflow'}. Markdown and print-ready HTML include official material references, verified findings and statistical evidence with their own periods. Materials CSV is available when adopted; statistical Evidence CSV retains its existing contract. The generated outline is generic and unapproved. No .doc or .docx is generated.`,
    'Diagnostic exports: editable Markdown, print-ready HTML with maps, legends and all member rows, and full diagnostic CSV. Internal comparisons do not change the analysis area; municipalities stop subdivision. Existing selected-period and time-series CSV remain available. CSV cells guard spreadsheet formulas in downloaded source strings.', '',
    '## Required acceptance work', '',
    '- Verify national → local A → local B → national selection, metric/period retention, direct links, reload and browser back/forward.',
    '- Verify zero vs missing and lack of local ranks when only national data exist.',
    '- Check map selection and fitting, boundary gaps, official/provider code distinctions and keyboard alternatives.',
    '- Inspect 320, 375, 768 and 1366px widths, actual 200% text zoom, keyboard focus and downloads.',
    '- Compare downloaded Markdown, HTML and CSV against selected area, period, units and sources.',
    '- Record the exact code revision, dataset edition, environment, evidence and checks not performed. Generation is not public-site or accessibility acceptance.', '',
    '## Recorded acquisition gaps', '',
    ...dataset.gaps.map(gap=>{
      if(dataset.analysis?.kind==='regional'&&gap.category==='census_country_coverage'){
        const summary=regionalCoverageSummary(dataset),completion=summary.country_edition_complete_count===null?'not reported':`${summary.country_edition_complete_count} of ${summary.total}`,wpp=summary.un_wpp_country_area_count===null?'not reported':`${summary.un_wpp_country_area_count} of ${summary.total}`;
        return `- ${gap.category} (partial): Coverage measures are separate: ${summary.census_history_count} of ${summary.total} Census-history profiles; ${summary.domestic_branch_count} of ${summary.total} country data branches with domestic records; country editions meeting the current completion gate ${completion}; UN WPP country/area rows ${wpp}. None substitutes for another. Missing and structurally inapplicable evidence remain distinct from zero. Next: Continue country-specific source updates without filling evidence gaps with estimates.`;
      }
      return `- ${gap.category} (${gap.status}): ${gap.detail} Next: ${gap.next_action || 'Verify the source.'}`;
    }), '',
    'This generator does not publish a site or modify a hosting account. Hosting remains a separate, explicitly scoped operation.', ''
  ];
  await writeFile(handoffPath,lines.join('\n'),'utf8');
  return {siteDir, files, handoffPath};
}

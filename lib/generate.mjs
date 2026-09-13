import {mkdir, writeFile, copyFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {escapeHtml, nationalOnly} from '../scaffold/site/model.mjs';

const scaffold = fileURLToPath(new URL('../scaffold/site/', import.meta.url));
const pages = {home:'Explore', territorial:'Territorial diagnostic', thematic:'Thematic diagnostic', planning:'Planning and resources'};

export function pageShell({country, page='home'}) {
  if (!(page in pages)) throw new Error(`Unknown generated page: ${page}`);
  const prefix=page==='home'?'./':'../';
  const links=Object.entries(pages).map(([key,label])=>`<a href="${prefix}${key==='home'?'':key+'/'}" data-page-link="${key}"${key===page?' aria-current="page"':''}>${escapeHtml(label)}</a>`).join('');
  const locale=/^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(country.locale || '')?country.locale:'en';
  return `<!doctype html>
<html lang="${escapeHtml(locale)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="description" content="${escapeHtml(country.name)} territorial evidence, thematic comparison and source-grounded planning aids. Coverage and missing data remain explicit.">
<title>${escapeHtml(pages[page])} — ${escapeHtml(country.name)}</title>
<link rel="stylesheet" href="${prefix}assets/styles.css">
<script type="module" src="${prefix}assets/app.mjs"></script>
</head>
<body data-page="${page}" id="top">
<a class="skip-link" href="#app">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="brand" data-brand-link href="${prefix}" title="Return to national start with default conditions"><span class="brand-mark" aria-hidden="true">◫</span><span class="brand-title"><span id="country-name">${escapeHtml(country.name)}</span><small>Territorial information &amp; planning</small></span></a><nav class="primary-nav" aria-label="Main pages">${links}</nav></div></header>
<main id="app" class="page-container" tabindex="-1"><p role="status">Loading acquired evidence…</p><noscript><h1>JavaScript is needed for this dashboard</h1><p>Use the local server to open the interactive pages. The acquired dataset is available as <a href="${prefix}data/dashboard.json">dashboard.json</a>.</p></noscript></main>
<footer class="site-footer">Source-grounded evidence · Explicit data gaps · Generic planning aids, pending official country guidance</footer>
</body></html>
`;
}

/** Create a portable static site. The caller validates and saves the canonical dataset. */
export async function generateSite({dataset, outDir}) {
  if(!dataset?.country?.id || !Array.isArray(dataset.territories) || !Array.isArray(dataset.indicators) || !Array.isArray(dataset.observations)) throw new Error('generateSite requires a validated dashboard dataset');
  if(!outDir || typeof outDir!=='string')throw new Error('generateSite requires outDir');
  const projectDir=path.resolve(outDir), siteDir=path.join(projectDir,'site');
  await mkdir(path.join(siteDir,'assets'),{recursive:true});
  await mkdir(path.join(siteDir,'data'),{recursive:true});
  const files=[];
  for(const page of Object.keys(pages)) {
    const directory=page==='home'?siteDir:path.join(siteDir,page);
    await mkdir(directory,{recursive:true});
    const filename=path.join(directory,'index.html');
    await writeFile(filename,pageShell({country:dataset.country,page}),'utf8');files.push(filename);
  }
  for(const file of ['app.mjs','model.mjs','styles.css']) {
    const destination=path.join(siteDir,'assets',file);
    await copyFile(path.join(scaffold,file),destination);files.push(destination);
  }
  const dataFile=path.join(siteDir,'data','dashboard.json');
  await writeFile(dataFile,JSON.stringify(dataset,null,2)+'\n','utf8');files.push(dataFile);
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
    'The home, territorial/, thematic/ and planning/ entry pages share the same local assets and dataset. Links and fetch URLs work at the domain root or below a hosting subdirectory.',
    'Add verified local observations, source records, document references and official-code joins to the canonical data/dashboard.json, validate it, then run scripts/build-country.mjs from the template. Do not patch generated site/data/dashboard.json as the canonical source.', '',
    '## Available outputs', '',
    'Planning: editable .md, evidence .csv, and a print-ready .html file with the same planning text. The outline is generic and unapproved, pending verified country forms. No .doc or .docx is generated. Use the print-ready HTML in a browser to print or save a PDF.',
    'Diagnostic exports: source-labelled CSV for exact selected periods and acquired time series. CSV cells guard spreadsheet formulas in downloaded source strings.', '',
    '## Required acceptance work', '',
    '- Verify national → local A → local B → national selection, metric/period retention, direct links, reload and browser back/forward.',
    '- Verify zero vs missing and lack of local ranks when only national data exist.',
    '- Check map selection and fitting, boundary gaps, official/provider code distinctions and keyboard alternatives.',
    '- Inspect 320, 375, 768 and 1366px widths, actual 200% text zoom, keyboard focus and downloads.',
    '- Compare downloaded Markdown, HTML and CSV against selected area, period, units and sources.',
    '- Record the exact code revision, dataset edition, environment, evidence and checks not performed. Generation is not public-site or accessibility acceptance.', '',
    '## Recorded acquisition gaps', '',
    ...dataset.gaps.map(gap=>`- ${gap.category} (${gap.status}): ${gap.detail} Next: ${gap.next_action || 'Verify the source.'}`), '',
    'This generator does not publish a site or modify a hosting account. Hosting remains a separate, explicitly scoped operation.', ''
  ];
  await writeFile(handoffPath,lines.join('\n'),'utf8');
  return {siteDir, files, handoffPath};
}

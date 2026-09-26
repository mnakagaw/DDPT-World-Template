# UAE AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; candidate `generated/united-arab-emirates-areadata-20260926` (ignored local directory). Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/uae-fcsc-scad-population-source-audit-2026-09-26.md) and [12-point producer check](../../evidence/uae-country-lesson-audit-2026-09-26.md) set the evidence limit. Candidate `dashboard.json` SHA-256 is `78057659138d671a551babde3bd397b972f95e6a25d9fe602ca6f36b2486f18a`. Ignored raw originals, hash receipts, table audit, site and output hashes stay in the country project. Environment: Windows/PowerShell, Node 24, Python 3, Poppler and Codex in-app browser; date 2026-09-26.

## Replay

After `node scripts/create-country.mjs --country "United Arab Emirates" --out generated/united-arab-emirates-areadata-20260926`, read `evidence/SOURCE_PREFLIGHT.md`/JSON and run:

```powershell
python scripts/fetch-uae-population-sources.py --project generated/united-arab-emirates-areadata-20260926
python scripts/import-uae-historical-and-scad-population.py --project generated/united-arab-emirates-areadata-20260926
node scripts/validate-country.mjs --project generated/united-arab-emirates-areadata-20260926
node scripts/build-country.mjs --project generated/united-arab-emirates-areadata-20260926
node scripts/verify-uae-domestic-output.mjs
npm run check
npm test
```

Pinned raw content changes stop replay pending review. The importer is idempotent for its own territory/indicator/source IDs. Source terms still need review; the originals and candidate data are not committed.

## What works and what does not

- FCSC's official 2009 PDF has a December **2005** census table with national **4,106,427** and all seven emirates. A separate SCAD official page has **2024** Abu Dhabi administrative-register population **4,135,985** and three regions; revised **2023 R1** region counts are also adopted. These are **two non-comparable local series**, not a 2024 population table for the seven emirates. National WDI 2005 midyear population **4,664,790** is kept separate.
- The candidate has **2 domestic indicators, 15 observations** and 10 local areas (7 emirates plus 3 Abu Dhabi SCAD regions). 2005 federal observations sum nationally; 2024 SCAD regions sum to the reported emirate total. 2023 SCAD emirate aggregate is left missing because only rounded region values were confirmed. No SCAD figures are assigned to Dubai or the national row.
- 2017 geoBoundaries emirate shapes are display references matched by name. Official code/boundary equivalence is unresolved; SCAD regions have no joined shapes. The FCSC report's other tables and years, SCAD's other fields and current series for the other six emirates remain unassessed.
- Local browser: national 2005 FCSC table showed 7/7 emirates; Abu Dhabi SCAD 2024 showed 3/3 source regions with no national SCAD value. Selecting Abu Dhabi Region and directly reselecting Whole Abu Dhabi restored parent title, URL, **4,135,985** and the selected 2024 indicator/period. `validate-country` has 0 errors and one material warning: no verified country-specific planning documents.
- Five output cases generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Internal rows were **7, 3, 0, 0, 0** for national 2005, Abu Dhabi 2024, Abu Dhabi Region 2024, Al Dhafra 2023 and Dubai 2005; data-row counts were **112, 56, 14, 14, 14**. Private `evidence/OUTPUT_VERIFICATION.json` records values, first/last rows and hashes. No Word/PDF/whole-table print or full 42-scenario acceptance was completed.

## Next evidence needed

1. Inspect FCSC UAE.Stat and emirate statistical centres for **current compatible all-emirate** estimates with definitions, periods and geography. SCAD's register series covers only Abu Dhabi. Audit all acquired numeric tables/fields and official boundary/code editions before a broader comparison.
2. Confirm each emirate's planning institution, law, applicable plan and local outputs. The UAE government local-government and Dubai 2040 overview pages are only leads; no actual selected-area plan, budget execution, implementation or official evaluation was collected.
3. Review raw reuse terms, whole output/print/Word/PDF, 42 acceptance scenarios, independent audit and hosting. Keep this edition local until `ACCEPT`; no country public URL is configured.
4. Continue the requested Middle East order with the next unstarted country while closing earlier partials. At this checkpoint: Asia 50 = **0 ACCEPT, 9 partial, 1 research-only, 40 unstarted**; Middle East 19 = **0 ACCEPT, 7 partial, 1 research-only, 11 unstarted**.

`npm run check` passed (137 JavaScript modules and JSON templates); `npm test` passed **218/218**. Country validation passed with the one planning-document warning. Independent audit and all 42 scenarios remain incomplete. Source-feedback commit IDs are recorded here and in `KIT_FEEDBACK_HANDOFF.md` after transfer. This candidate data edition is not Git-published; only scripts/evidence/status are.

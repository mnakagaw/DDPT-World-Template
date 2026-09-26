# Cyprus AreaData continuation — 2026-09-27 JST

Branch `codex/asia-domestic-20260926`; ignored candidate `generated/cyprus-areadata-20260927`. Status: **partial, unpublished, no independent `ACCEPT`**. [Source audit](../../evidence/cyprus-cystat2021-source-audit-2026-09-27.md) and [producer check](../../evidence/cyprus-country-lesson-audit-2026-09-27.md) delimit the claims. The candidate dataset SHA-256 at this checkpoint is `eac31982eada7f6698759d86c8606edb0ae19d739572a961c3ee97f458ab5a10`. Date is Japan time; originals were acquired on 2026-09-26 UTC. No Cyprus hosting destination has been specified.

## Replay and actual content

`SOURCE_PREFLIGHT.md`/`.json` were read first and contained no Cyprus-specific prior lead. `scripts/inventory-cyprus-cystat-census2021.py` archives the official 46-table/12-directory API catalogue and seven selected full matrices in the ignored candidate. `raw/cystat/Census2021-Final_Results-EN-090824.pdf` is the official nine-page final release; `raw/cystat/GEOCODES-2015.csv` is the official historical code classification. The inventory records requests, URLs, hashes and all table locations. The importer pins selected source hashes, verifies numeric and geographic controls, and rewrites only `CYP`-specific source/indicator/document content of this generated project. The latest candidate contains **516 territories, 27 domestic indicators, 11,804 domestic observations and 24 comparison sets**. The 2021 census government-controlled-area population 923,381 is held in a separate scope node from the whole-island country/WDI series. The source's seven household-size `N.A.` values remain not applicable; omitted fields remain missing. Historical 2015 code existence is verified for all 410 localities and 99 quarters, with no 2021/2024 boundary implication.

```powershell
node scripts/create-country.mjs --country Cyprus --out generated/cyprus-areadata-NEW
python scripts/inventory-cyprus-cystat-census2021.py --project generated/cyprus-areadata-NEW
# Obtain the official final-results PDF and GEOCODES 2015 CSV into raw/cystat/ as recorded in the source audit.
python scripts/import-cyprus-cystat-census2021.py --project generated/cyprus-areadata-NEW
node scripts/validate-country.mjs --project generated/cyprus-areadata-NEW
node scripts/build-country.mjs --project generated/cyprus-areadata-NEW
node scripts/verify-cyprus-cystat-output.mjs generated/cyprus-areadata-NEW
npm run check
npm test
```

`create-country.mjs` refuses an existing output; an existing candidate can instead be reimported from its pinned local raw files. The historical GEOCODES source URL is `https://www.data.gov.cy/sites/default/files/GEOCODES%202015.csv`; the final-results PDF URL is in the source audit. Reacquired bytes that change hashes need review before importing, not a silent hash update. The full census API download takes multiple requests; its inventory script retries throttling, and 39 unselected table bodies are still pending.

The candidate passed `validate-country` with zero errors/warnings, `build-country`, the eight-case actual output verifier, `npm run check` (148 modules/templates), and `npm test` (218/218) on 2026-09-27 JST. Outputs include all five controlled-area districts, 113 Lefkosia district localities, 19 Lefkosia quarter rows, housing, labour, explicit zero and institution-only cases across CSV/HTML/Markdown and planning HTML/evidence CSV. The local browser showed scope→district→locality→quarter changes, quarter→district re-selection, source labels and planning-location/absence distinction. The 113-locality territorial page is very large and needs a separate timed accessibility/visual/print test; mobile and actual printed/PDF/Word output remain unverified.

## Unresolved gates and next priority

1. Acquire and semantically audit the remaining **39 official census matrix bodies** and **65 unassessed field combinations** of the seven selected matrices. Keep source year, universe, official field definition and `N.A.`/missing distinctions. The 46-table catalogue is an expectation register, not 46 adopted tables.
2. Obtain a date-specific official DLS polygon layer and 2024 local-government crosswalk. The 2015 code classification and older INSPIRE/geoBoundaries layers do not prove matched boundaries. Reconcile 2021 statistical areas to current legal units without name-only joins.
3. Acquire exact DTPH local/area plan bodies, maps, current revisions, operative legal/guidance texts and area-specific budgets, execution and evaluations. The 2024 Paralimni/Agia Napa/Deryneia plan location and 2026 four-city preparation process are not complete or current plan contents for every district/locality.
4. Review CYSTAT PxWeb copyright/reuse terms and layer-specific spatial terms. Complete representative and missing-value paths, all applicable 42 scenarios, print/device/accessibility checks and independent `ACCEPT` before hosting.
5. Record the Cyprus public official source locations in the Kit feedback loop at `official_location_identified` only. After this checkpoint, Asia 50 = **0 ACCEPT, 20 partial, 1 research-only, 29 unstarted**; Middle East 19 = **0 ACCEPT, 18 partial, 1 research-only, 0 unstarted**. Next unstarted country in the requested order is India; Middle East remains incomplete until independent gates close.

The generated project and raw originals are ignored locally. Only repeatable scripts, public source locations, bounded audit, status and source-feedback bundle belong in Git. AreaData and Kit commits, remote parity and any actual hosting/public verification must be appended here after those steps occur.

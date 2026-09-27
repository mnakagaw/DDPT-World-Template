# Thailand AreaData handoff — 2026-09-27 JST

**Status: 2024p GPP provincial partial candidate, independent `ACCEPT` pending, unpublished.** After this candidate the Asia ledger is 0 complete, 32 partial, 1 research-only and 17 not started. Next unstarted priority: Myanmar. The ignored project is `generated/thailand-areadata-20260927`. Tracked code, source manifest, audit and producer validation allow rebuilding a new candidate. No THA Hosting/Public destination is assigned.

## Evidence and decisions

- The [official NESDC 2024p GPP workbook](https://www.nesdc.go.th/wp-content/uploads/2026/03/GPP-2024-On-Web-1995-2024.xlsx) and catalogue were acquired. Its 12 sheets, numeric columns and reporting blocks are inventoried. `PER CAPITA` supplies GPP, its population denominator and published GPP per capita; current-price 2024p `AE` supplies 21 distinct adopted sector fields. Country and 77 provinces have **24 indicators, 1,872 direct observations**. The 7 economic regions and 2 duplicate/overlapping sector rows remain audit-only. All 2,210 selected country/region/province core cells reconcile; 1995–2023, CVM, `Regions to GDP` and `CLUSTERS` remain `priority_unassessed`.
- The source prints a contradictory detailed-table Kam Phaeng Phet population at `NO!AE691`, **1.531952980056 thousand** above the population at `PER CAPITA!D47`; only the latter reconciles with printed per capita and complete province coverage. The former is withheld and recorded in the audit.
- NESDC's four-character economic-region/province labels are **not confirmed DOPA legal codes**. The initial 2017 geoBoundaries shapes were removed; no exact 2024p official polygon is joined. The country and 77 province selector/full tables work with an explicit missing-boundary message. NSO 2025 resident census and BORA registration remain separate from NESDC's GPP population denominator and WDI.
- The [NSO 2025 census portal](https://www.nso.go.th/nsoweb/main/summano/aE?set_lang=en), [BORA registration catalogue](https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php), [DOPA code register](https://stat.bora.dopa.go.th/stat/statnew/statMenu/newStat/ccaa.php) and [district registration dataset](https://data.go.th/en/dataset/0405_01_0005) were located. The indexed NSO final PDF returned HTTP 418, BORA/DOPA failed DNS and data.go.th returned 403; no local values or codes were invented.
- The [NESDC provincial planning catalogue](https://www.nesdc.go.th/downloadable-documents/province-provincial-cluster/) and six-page guide were acquired; the guide text begins with a draft marker. Chiang Mai's official plan/progress catalogue and FY2025 review PDF location were indexed but requests timed out. National references remain separate from selected province materials; local plan/budget/implementation/evaluation categories show uncollected.

[Source audit](../../evidence/thailand-nesdc-gpp2024-source-audit-2026-09-27.md), [start sheet](../../evidence/thailand-country-start-2026-09-27.md), [Task Contract](../../evidence/thailand-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/thailand-country-lesson-audit-2026-09-27.md) define the evidence boundary. The ignored candidate holds pinned originals, whole-workbook row/column inventory, detailed audit, import result, output hashes and final dataset.

## Reproduce and inspect

Start from a **new** directory; never overwrite a working candidate after acquisition/build failure. Obtain the four NESDC official originals at paths in `config/thailand-gpp2024-source-manifest.json` and verify bytes/SHA-256. If an official original changes, review the new snapshot before changing the manifest or adopter. Preserve the previous candidate until replacement passes validation.

```powershell
node scripts/create-country.mjs --country Thailand --out generated/thailand-replay-new
# Obtain official NESDC workbook, two catalogue HTML pages and the six-page guide in the manifest raw paths.
python scripts/audit-thailand-gpp2024.py --project generated/thailand-replay-new
python scripts/import-thailand-gpp2024.py --project generated/thailand-replay-new
node scripts/validate-country.mjs --project generated/thailand-replay-new
node scripts/build-country.mjs --project generated/thailand-replay-new
node scripts/verify-thailand-gpp2024-output.mjs generated/thailand-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `c2cb0894b0070f68636dc8d502e6ad6e0de3669db8487b7508cbe253b4b9615c`, validator **0 errors/warnings**, site built, **5 direct-original/output cases** passed, `npm run check` **160 JavaScript/JSON** and `npm test` **218/218**. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, all 77 national comparison rows for each of 24 indicators and source locators. Local browser at `127.0.0.1:4272` confirmed Thailand→Chiang Mai→Thailand with heading/URL/value change, 24 observed provincial indicators, no unsupported polygons, and distinct national references. The nationwide page renders 24 indicators and 1,848 comparison rows; lower-powered-device and narrow-screen behavior remain to test. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Thailand edition

1. Obtain NSO 2025 final census province tables, BORA registration files and dated DOPA province/district/subdistrict code and polygon editions from accessible official endpoints. Keep resident, registered, NESDC denominator and WDI populations separate.
2. Semantically audit NESDC 1995–2023 historical and CVM series, `Regions to GDP` and cluster tables, preserving any non-additivity, definition/coverage shifts and the Kam Phaeng Phet conflict. Adopt only source-supported compatible comparisons.
3. Review current provincial, cluster and local-administration planning competence by article, issuer and period. Obtain representative current plans, adopted budgets, actual spending, implementation and official evaluations; reconcile legal territory identity before assigning a document to a statistical row.
4. Review reuse terms; complete applicable 42 scenarios, all-indicator print/mobile/performance and Thai-language inspection, plus independent `ACCEPT`. Assign THA-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits each lead. It transfers no XLSX/PDF, 1,872 observations or country acceptance. [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) records import and repository commits. **Local:** partial candidate. **GitHub:** scoped code, audit and source leads. **Hosting:** none. **Public:** none.

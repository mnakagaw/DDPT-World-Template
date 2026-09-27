# Myanmar AreaData handoff — 2026-09-27 JST

**Status: DOP 2024 census state/region partial candidate; independent `ACCEPT` pending; unpublished.** The Asia ledger is 0 complete, 33 partial, 1 research-only and 16 not started. Next unstarted priority: Malaysia. The ignored candidate is `generated/myanmar-areadata-20260927`. Tracked manifest, audit/import scripts and actual-output verifier allow a new candidate to be rebuilt. No Myanmar-specific Hosting/Public destination is assigned.

## Evidence and decisions

- The [DOP 2024 demographic Excel appendix](https://dop.gov.mm/sites/dop.gov.mm/files/datamap-documents/2024_census_appendix_table_demographic_characteristics_eng.xlsx), [later Union Report](https://www.dop.gov.mm/sites/dop.gov.mm/files/publication_docs/2024mphc_unionreport_en_26nov.pdf), [earlier provisional report](https://dop.gov.mm/sites/dop.gov.mm/files/publication_docs/2024_provisional_result_eng.pdf), and [MOI FY2026-27 plan-coordination article](https://www.moi.gov.mm/moi:eng/news/18967) were acquired and hash-pinned. The provisional nationwide 51,316,756 and later 51,375,327 are different editions, not a time-series change.
- The later report says 152/330 townships fully enumerated, 120 partial, 58 not canvassed; 32,183,599 people enumerated and 19,191,728 statistically estimated (37.4%). National and 15 state/region-equivalent Table A-1 rows plus report coverage fields provide **15 indicators and 240 observations**, including printed coverage percentages. Chin is 92.2% estimated; Yangon, Ayeyawady and Nay Pyi Taw are 0.0% estimated. The latter's Excel dashes become nine explicitly calculated zeros after report/total reconciliation.
- All 19 workbook sheets and numeric columns were inventoried (17,081 numeric cells including table/list labels). Only Table A-1's 12 fields and Union Report Tables 2.2/3.1 coverage fields are adopted. A-2–A-18, including district/township rows, remain `priority_unassessed`; a source location or a numeric-cell inventory is not semantic acceptance.
- DOP's 15 source reporting rows have no verified legal code in A-1. The initial 2019 geoBoundaries set has only 14 shapes; all shapes were removed. No state/region, district or township polygon is joined. WDI national estimates remain separate from 2024 DOP census numbers.
- The MOI planning article is a national reference to coordination, not evidence of local plan approval or law. Local plan, budget, actual spending, implementation and evaluation remain uncollected. The CSO 2023 GAD administrative-count table and DOP 2024/2014 workbook catalogues are location leads, not adopted code/values.

[Detailed source audit](../../evidence/myanmar-dop-census2024-source-audit-2026-09-27.md), [start sheet](../../evidence/myanmar-country-start-2026-09-27.md), [Task Contract](../../evidence/myanmar-task-contract-2026-09-27.md) and [producer lesson audit](../../evidence/myanmar-country-lesson-audit-2026-09-27.md) define the evidence boundary. The ignored candidate holds original files, source hashes, the 19-sheet inventory, audit JSON, output verification and built site.

## Reproduce and inspect

Start in a **new** directory. Never overwrite a working candidate after acquisition/build failure. Obtain the four official originals at the exact paths in `config/myanmar-census2024-source-manifest.json`, preserving bytes/SHA-256. Python needs `openpyxl` and `pypdf`. If a source changes, inspect the new edition before updating the manifest or importer.

```powershell
node scripts/create-country.mjs --country Myanmar --out generated/myanmar-replay-new
# Download the manifest's four official source URLs to their raw_path locations, then verify byte count and SHA-256.
python scripts/audit-myanmar-census2024.py --project generated/myanmar-replay-new
python scripts/import-myanmar-census2024.py --project generated/myanmar-replay-new
node scripts/validate-country.mjs --project generated/myanmar-replay-new
node scripts/build-country.mjs --project generated/myanmar-replay-new
node scripts/verify-myanmar-census2024-output.mjs generated/myanmar-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `2af0ee9339b8dbc79c40e49a5272cc3d0c8b79a3f5a4ddcf93517622adc8cbe8`; validator **0 errors/warnings**, site built; **5 selected source/output cases** and **225 national comparison CSV/print rows** checked; `npm run check` **161 JavaScript/JSON** and `npm test` **219/219**. Local browser at `127.0.0.1:4273` checked Chin→Yangon→Myanmar, total/estimate/coverage values, URL and heading changes, no-polygon fallback, separate national planning references, 15/15 estimated-share ranking and comparison-row focus leaving the national analysis area unchanged. The shared runtime was corrected to respect a sourced explicit comparison of the DOP mixed State/Region/Union Territory reporting roster; an undeclared mixed cohort remains blocked by a new regression test. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Myanmar edition

1. Semantically audit the other 17 demographic tables, 2024 State/Region subject workbooks and more recent or historical DOP materials. Preserve provisional/final, direct/imputed and temporal/geographic definitions. Investigate district/township code and repeated-name resolution before taking A-2 local numbers.
2. Acquire dated DOP/GAD official administrative codes and polygons for all 15 reporting areas and finer relevant hierarchy. Match exact codes and editions; do not reuse the 2019 14-shape set by name.
3. Verify current planning law, guidance, formal Region/State and township competence and representative issuer-approved plans, budgets, expenditure, implementation and official evaluation. Keep national coordination news separate from local materials.
4. Review source reuse terms, complete applicable 42 scenarios and Burmese/English, print/mobile/performance/local-user checks, then obtain independent `ACCEPT`. Set Myanmar-specific Hosting/Public scope and verify deployed JSON and rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits the leads. It transfers no PDFs/XLSX, 240 observations, geometry match or country acceptance. [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) records repository commits. **Local:** partial candidate. **GitHub:** code, audit and source leads. **Hosting:** none. **Public:** none.

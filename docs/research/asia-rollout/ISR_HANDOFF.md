# Israel AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; candidate `generated/israel-areadata-20260926` (ignored local directory). Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/israel-cbs2022-source-audit-2026-09-26.md) and [producer check](../../evidence/israel-country-lesson-audit-2026-09-26.md) define the evidence limit. Private `dashboard.json` SHA-256 is `05c9db52b1cefa505fbc4d89cc850bcf69d8613f4a6ae63d3ab98f7b12a2a00b`; private raw originals, receipts, field inventory and output hashes remain in the candidate. Environment: Windows/PowerShell, Node 24, Python 3, Codex in-app browser; date 2026-09-26.

## Replay

After `node scripts/create-country.mjs --country Israel --out generated/israel-areadata-20260926`, read `evidence/SOURCE_PREFLIGHT.md` and JSON, then run:

```powershell
python scripts/fetch-israel-cbs-census.py --project generated/israel-areadata-20260926
python scripts/import-israel-cbs2022-districts.py --project generated/israel-areadata-20260926
node scripts/validate-country.mjs --project generated/israel-areadata-20260926
node scripts/build-country.mjs --project generated/israel-areadata-20260926
node scripts/verify-israel-cbs2022-output.mjs
npm run check
npm test
```

The fetcher refuses altered originals, and the importer replaces only its own source/indicator IDs. Six CBS XLSX originals and their receipts are excluded from Git; source terms require review. Its code replaces generated provider local geometries with no local polygons because the 2006 six-shape reference cannot be reconciled to the CBS 2022 seven-row reporting cohort.

## Verified portion and limits

- From CBS 2022 Census broad-geography Excel, eight indicators supply **64 direct observations**: nationwide and seven first-level source rows, including six districts and a separately scoped Israeli-localities-only row for Judea and Samaria Area. The seven rounded populations sum to the CBS nationwide **9,601,720**. The seventh row's **481,940** is not an all-resident population for that area. Source row/column IDs remain in every observation.
- Six official workbooks contain 14 sheets. One selected 454-column sheet is field-inventoried; only eight fields in eight rows are adopted. Locality/statistical-area books and 16 subdistrict/52 natural-area rows remain held, including incomplete source coverage. More local themes cannot be claimed from a partial workbook audit.
- The 2006 six-piece reference boundary is not joined to the 2022 CBS seven-row cohort. There are **no verified local polygons** in the candidate. No first-level reporting row is asserted to be a legal plan-making unit. WDI national midyear population is not subtracted from CBS Census counts or assigned locally.
- Browser checked national population **9,601,720** and 7/7 comparable 2022 ranking; area 7 **481,940** with code, restricted scope, row 78 and no boundary; reselected national and recovered the parent value; area-7 planning page displayed **0** verified local materials, with working outputs still available. This is a narrow producer-side UI check, not all 42 scenarios.
- Seven output cases generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Values, periods, source cell locators, selected-area names, national first/last internal rows, counts and hashes matched. National diagnostic had seven internal comparison rows; local rows had zero. No full-table print, Word/PDF or final visual output rendering was completed.

`validate-country` passed with zero errors and one material warning: no verified country-specific planning documents. The output verifier passed. `npm run check` passed (139 modules and JSON templates); `npm test` passed **218/218**. Kit import, its 173/173 tests and Git IDs are recorded in the [feedback handoff](KIT_FEEDBACK_HANDOFF.md). Independent audit and hosting remain undone.

## Next work

1. Audit all 14 CBS sheets field by field; reconcile locality/statistical-area code universes, missing places, denominators and reference periods. Add compatible local themes only after complete source coverage checks.
2. Obtain official 2022 or current boundaries and code histories for districts, local authorities and statistical areas; resolve the CBS area-7 scope explicitly before any map join.
3. Inspect current planning law and responsible authorities, then acquire actual plan/approval/budget/implementation/evaluation evidence for contrasting localities and this reporting area's appropriate institutions.
4. Complete 42 scenarios, full-table print and output layout, producer sign-off, independent `ACCEPT`, and only then consider hosting. No Israel hosting destination is configured.
5. Continue Middle East in the requested order. At this checkpoint Asia 50 = **0 ACCEPT, 11 partial, 1 research-only, 38 unstarted**; Middle East 19 = **0 ACCEPT, 9 partial, 1 research-only, 9 unstarted**. The next unstarted country is Lebanon.

Only code/evidence/status, not this candidate dataset or raw originals, is Git-published.

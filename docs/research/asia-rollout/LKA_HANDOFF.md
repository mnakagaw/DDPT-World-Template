# Sri Lanka AreaData handoff — 2026-09-27 JST

**Status: local census partial candidate, independent `ACCEPT` pending, unpublished.** Asia ledger after this candidate: 0 complete, 25 partial, 1 research-only, 24 not started. The next unstarted priority is Bhutan. The separate ignored project is `generated/sri-lanka-areadata-20260927`; this handoff, scripts, source manifest and audit are tracked. No Sri Lanka hosting/public destination has been assigned.

## Acquired and adopted

- DCS CPH 2024 official catalogue and 34 original files: seven Population A, 16 Housing A, nine GN, one code register and the English final report. The 23 numbered A workbooks are all acquired, but only Population A5, Housing A14 and A16 have all selected numeric fields and 366 reporting rows semantically audited. Other acquired numeric fields remain `priority_unassessed`.
- The selected 30 source count indicators yield 10,989 direct observations across country, 25 districts and 340 DS divisions; the report's Table 3.2 adds nine direct province population observations. The dataset contains 375 statistical territories. National census population is 21,781,800; nine province population values sum to that figure. The 6,111,315 national households and original water/toilet categories use a household denominator. WDI national midyear estimates remain a separate series. Province household/age observations are missing.
- DCS code register and provisional GN population file match on 14,008 code-component keys. The 340 final DS rows reconcile by district, sex/population counts and name where possible; 16 have name variants. Provisional GN age counts differ from final DS age counts in eight divisions; GN observations are not adopted. Official compatible polygon count is zero; the first provider shapes were removed. DS census divisions are not local-government councils.
- Planning source is a Gazette location lead only. Colombo Municipal Council documents have not been assigned to statistical Colombo District or Colombo DS. No area-specific approved plan, budget body, expenditure or evaluation is adopted.

[Source audit](../../evidence/sri-lanka-cph2024-source-audit-2026-09-27.md), [start sheet](../../evidence/sri-lanka-country-start-2026-09-27.md), [Task Contract](../../evidence/sri-lanka-task-contract-2026-09-27.md) and [producer lesson audit](../../evidence/sri-lanka-country-lesson-audit-2026-09-27.md) record source URLs, selections and limits. `config/sri-lanka-cph2024-source-manifest.json` pins URL, bytes and hash; ignored candidate `evidence/` holds receipts and complete selected-table values. Raw originals, generated site and other large artifacts remain ignored.

## Reproduce and inspect

In repository root, using Python with `openpyxl` and `pypdf` plus Node dependencies:

```powershell
python scripts/fetch-sri-lanka-cph2024.py --project generated/sri-lanka-areadata-20260927
python scripts/inventory-sri-lanka-cph2024.py --project generated/sri-lanka-areadata-20260927
python scripts/import-sri-lanka-cph2024.py --project generated/sri-lanka-areadata-20260927
node scripts/validate-country.mjs --project generated/sri-lanka-areadata-20260927
node scripts/build-country.mjs --project generated/sri-lanka-areadata-20260927
node scripts/verify-sri-lanka-cph2024-output.mjs generated/sri-lanka-areadata-20260927
npm run check
npm test
```

The producer run returned zero validator errors and **one warning for absent verified planning documents**; the site built, eight source-cell/output examples passed, `npm run check` checked 153 modules/templates, and `npm test` passed 218/218. The output verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV and full printable 9/3/13 comparison rows. The browser hierarchy and same-parent re-selection were checked at `127.0.0.1:4184`. This is producer evidence, not independent acceptance or a claim that all 42 scenarios passed. `evidence/LKA_IMPORT_RESULT.json` in the ignored candidate holds the dataset SHA-256; it changes if a new import timestamp is written.

## Remaining before a complete Sri Lanka edition

1. Inventory every acquired numeric column and report table, definitions and geography; choose adoption/nonadoption per field. Reconcile GN provisional/final versions before any GN indicator use. Review further official themes and 2024 census revisions.
2. Obtain dated official code and polygon editions for province, district, DS, GN and local authorities; prove crosswalk/overlap. Verify the 16 DS name variants and one GN spelling difference. Treat council, statistical division and planning area separately.
3. Audit current local-government and planning laws, guidelines, applicable forms, each selected authority's actual plan and budget body, expenditure, implementation and official evaluation. Check issuer, legal adoption, period and jurisdiction. Review original redistribution terms.
4. Complete applicable 42 acceptance scenarios, non-Colombo and missing cases, local language, narrow/mobile/print and Word/PDF outputs, then independent `ACCEPT`. Assign country-specific hosting/public scope and verify its deployed JSON and rendered URL only after acceptance. No DDPT deployment scope transfers to Sri Lanka.

Kit feedback is **source-location-only** (`official_location_identified`) until Kit independently audits each lead. It does not transfer original files, observations or country acceptance. AreaData and Kit commit references and verification are recorded in [Kit handoff](KIT_FEEDBACK_HANDOFF.md). Local: partial candidate. GitHub: scoped code, audit and source leads. Hosting: none. Public: none.

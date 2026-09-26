# Bhutan AreaData handoff — 2026-09-27 JST

**Status: local census partial candidate, independent `ACCEPT` pending, unpublished.** Asia ledger after this candidate: 0 complete, 26 partial, 1 research-only, 23 not started. The next unstarted priority is Maldives. The separate ignored project is `generated/bhutan-areadata-20260927`; this handoff, scripts, source manifest and audit are tracked. No Bhutan hosting/public destination has been assigned.

## Acquired and adopted

- NSB PHCB 2017 national report and all 20 Dzongkhag reports, the December 2020 BSSGC PDF and 2012 Local Government Rules PDF: 23 originals with immutable bytes/hashes. The PMO 13th FYP PDF could not be acquired because TLS peer verification failed; no certificate bypass or body adoption.
- Only district Annex Table A2.1 population/sex numeric rows and national Table 2.1 are adopted. Twenty districts, 64 town/Thromde rows and 205 rural Gewog **parts** plus country yield 290 statistical territories, four indicators and 871 direct observations. The 329 A2.1 source rows include 40 overlapping Urban/Rural subtotals retained in audit only. The other 641 district report table headings have no numeric-semantic audit.
- The comparable detailed-analysis count is 727,145; the distinct all-found count is 735,553 and includes 8,408 hotel visitors without local detailed rows. District and town/rural-part parent sums reconcile in all three adopted count fields. WDI national midyear series is separate. No official-compatible 2017 polygons or historical code match are claimed; legal Gewog and statistical rural part are distinct.
- The 2012 rules provide only bounded historical institutional context. Current legal force, 13th FYP content and actual area-specific plan/budget/expenditure/evaluation are unverified. No local document is attached.

[Source audit](../../evidence/bhutan-phcb2017-source-audit-2026-09-27.md), [start sheet](../../evidence/bhutan-country-start-2026-09-27.md), [Task Contract](../../evidence/bhutan-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/bhutan-country-lesson-audit-2026-09-27.md) record selections and limits. The manifest pins all acquired PDFs; ignored candidate `evidence/` holds receipts, selected-table values, source page images and actual output checks. Large originals, generated site and other artifacts remain outside Git.

## Reproduce and inspect

In repository root, using Python with `requests` plus Node dependencies and Poppler `pdftotext`:

```powershell
python scripts/fetch-bhutan-phcb2017.py --project generated/bhutan-areadata-20260927
python scripts/inventory-bhutan-phcb2017.py --project generated/bhutan-areadata-20260927
python scripts/import-bhutan-phcb2017.py --project generated/bhutan-areadata-20260927
node scripts/validate-country.mjs --project generated/bhutan-areadata-20260927
node scripts/build-country.mjs --project generated/bhutan-areadata-20260927
node scripts/verify-bhutan-phcb2017-output.mjs generated/bhutan-areadata-20260927
npm run check
npm test
```

The producer run returned zero validator errors and **one warning for absent verified planning documents**; the site built, six source-row/output cases passed, `npm run check` checked 154 modules/templates, and `npm test` passed 218/218. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV and full printable 20/8/10 comparison rows. The browser hierarchy and same-parent re-selection were checked at `127.0.0.1:4185`. These are producer checks, not independent acceptance or a claim that all 42 scenarios passed. The ignored `evidence/BTN_IMPORT_RESULT.json` records the dataset SHA-256, which changes on timestamped reimports.

## Remaining before a complete Bhutan edition

1. Audit all acquired report tables' numeric fields, definitions, denominators and source geography; choose adoption/nonadoption per field. Search for current official local statistics without assuming missing A2.1 themes do not exist.
2. Obtain 2017-compatible official code and polygon editions, town/Thromde boundaries and a legal-Gewog-to-rural-part crosswalk. Preserve internal IDs until every match is proven.
3. Verify current Local Government Rules and applicable 13th FYP requirements through a verifiable official PDF channel. Obtain the competent body's actual local plans, budgets, expenditures, implementation and official evaluations, with issuer, jurisdiction, period, adoption and content checks. Review reuse terms.
4. Complete applicable 42 scenarios, edge and missing cases, local language, narrow/mobile/print and Word/PDF outputs, then independent `ACCEPT`. Assign Bhutan-specific Hosting/Public scope and verify deployed JSON and rendered URL only after acceptance. Do not transfer DDPT deployment scope.

Kit feedback is **source-location-only** (`official_location_identified`) until Kit independently audits each lead. It does not transfer original files, observations or country acceptance. AreaData adapter/selection commit `5b3ca07c824cfa48d42a577aebb38cf1c471e1f0` and Kit import commit `97356cefa61fa4468de891a463f804b15f882e27` were pushed and remote heads verified. The 276-source bundle carries that AreaData commit as `origin_commit`; [Kit handoff](KIT_FEEDBACK_HANDOFF.md) records validation. Local: partial candidate. GitHub: scoped code, audit and source leads pushed. Hosting: none. Public: none.

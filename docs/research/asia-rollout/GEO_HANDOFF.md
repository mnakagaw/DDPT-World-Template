# Georgia AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/georgia-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/georgia-geostat2024-source-audit-2026-09-26.md) and [producer check](../../evidence/georgia-country-lesson-audit-2026-09-26.md) delimit verification. Private `dashboard.json` SHA-256: `bf90082d191dabcfea1bab75bbde0e79a86e7a4f01570426e79ced16cb18b454`. Originals, catalog HTML, receipts, field/adoption inventories and output hashes remain in the ignored candidate. Environment: Windows/PowerShell, Node 24, Python 3 and local in-app browser; date 2026-09-26. No Georgia hosting destination is configured.

## Replay

Read `evidence/SOURCE_PREFLIGHT.md` and `.json` first. The generator refuses an existing directory: regenerate into a fresh sibling or preserve the current candidate. `fetch` acquires eight catalog pages, 48 XLSX originals and the final overview; the private inventory pins their URLs and hashes. Import rejects changed selected originals and source arithmetic mismatches.

```powershell
node scripts/create-country.mjs --country Georgia --out generated/georgia-areadata-20260926
python scripts/fetch-georgia-geostat-census2024.py --project generated/georgia-areadata-20260926 --download
python scripts/inventory-georgia-geostat-fields.py --project generated/georgia-areadata-20260926
python scripts/import-georgia-geostat-census2024.py --project generated/georgia-areadata-20260926
node scripts/validate-country.mjs --project generated/georgia-areadata-20260926
node scripts/build-country.mjs --project generated/georgia-areadata-20260926
node scripts/verify-georgia-geostat2024-output.mjs generated/georgia-areadata-20260926
npm run check
npm test
node scripts/serve.mjs --dir generated/georgia-areadata-20260926/site --port 4197
```

The importer replaces its own IDs on replay; `generated_at` and dataset hash change while original numeric values remain pinned. Candidate and originals stay outside Git. Use the Node server on this Windows host for correct `.mjs` MIME type.

## Verified scope and limits

- Five adopted Geostat 2024 census tables create **85 territories, 22 local indicators and 1,740 observations**, of which 1,440 are source reported and 300 calculated. Eight catalog categories list 48 XLSX originals; all originals and 85,449 numeric cells were mechanically inventoried, but **43 tables are semantically unassessed**.
- National census usual-resident population **3,929,581**, 11 top-level rows, 63 municipalities and ten Tbilisi internal districts are source-table identities. Population/sex/urban-rural totals reconcile across complete child sets. Tbilisi is a self-governed municipality; its districts are diagnostic, not separate municipalities. `-` magnitude nil in the source becomes zero; missing unprovided district age/labour/etc. stays missing. WDI estimates and private-household residents are separate series.
- Browser checked Georgia → Adjara → Batumi → Adjara whole, and Tbilisi → Gldani; the parent re-selection returned to **402,929** and six municipal members. The thematic page focused Samgori while retaining Gldani as analysis target. Gldani planning showed zero collected documents, nine available indicators and unapproved outputs. No verified local polygon was substituted.
- Thirteen actual output cases checked diagnostic CSV/HTML/Markdown and planning HTML/evidence CSV, with source/year/value, all printable comparison rows, first/last row and hashes. The 42-scenario suite, rendered print PDF, narrow-width and human-user checks are incomplete.

Country validation passed with zero errors and one missing-plan warning; build and 13-case verifier passed. AreaData `npm run check` checked 144 JavaScript modules and JSON templates; `npm test` passed 218/218. No independent audit, Hosting or Public was done.

## Next work

1. Semantically classify the other 43 acquired Geostat tables by universe, definition, geography, year and reuse, then prioritize local sector indicators. A mechanical cell inventory alone does not support adoption.
2. Obtain an official administrative code edition and 2024-compatible region, municipality and Tbilisi-district polygons; resolve occupied-area treatment and settlement hierarchy. Do not join 2015 reference polygons by name alone.
3. Audit operative planning law/ordinance, official local manual, approved plan bodies, decisions, budgets, implementation and evaluation for contrasting Tbilisi, Batumi and rural municipalities. Separate municipality plan authority from internal-district diagnosis.
4. Complete applicable 42 scenarios, long-table print rendering, document layout, source terms and independent `ACCEPT` before any hosting.
5. Continue the user-requested Middle East priority order. With Georgia counted as partial, Asia 50 has **0 ACCEPT, 16 partial, 1 research-only, 33 unstarted**; Middle East 19 has **0 ACCEPT, 14 partial, 1 research-only, 4 unstarted**. Next unstarted priority: Qatar.

Only code, source leads, evidence and status are saved to GitHub. AreaData adapter/source audit `8bf8d222f0b4b664486fc1ad3aed27bac1d56f47` and 112-lead bundle `d2a5c42b817c6552787d2ef68b014039625b5029` were pushed; Kit imported the 13 Georgia leads at `b390195c9b030f96ca651a4cb1c7c77dc8e1dac5`. [The Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) records the validation. All Georgia leads remain `official_location_identified` and `not_acquired_by_kit_preflight` until Kit independently audits them.

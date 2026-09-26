# Maldives AreaData handoff — 2026-09-27 JST

**Status: local census partial candidate, independent `ACCEPT` pending, unpublished.** Asia ledger after this candidate: 0 complete, 27 partial, 1 research-only, 22 not started. The next unstarted priority is Indonesia. The separate ignored project is `generated/maldives-areadata-20260927`; code, manifests and audit documents are tracked. No Maldives hosting/public destination is assigned.

## Evidence and decisions

- The Maldives Bureau of Statistics 2022 census catalogues yielded 58 XLSX originals: 52 numbered tables and six supplemental sheets. URLs, bytes and SHA-256 are pinned. All numeric columns were mechanically inventoried, but only selected original count fields from P4/P5/H2/H7/EC3/ED16 were semantically audited and adopted. Other 52 books and unselected fields remain `priority_unassessed`.
- The candidate has 218 statistical territories, 23 indicators and 3,626 direct observations. Country census population **515,132** and households **94,424** reconcile to Maale, 20 atoll/city reporting groups and the non-administrative-island aggregate. All 186 administrative islands reconcile to their P4 parents for nine P4/P5 population fields. No cross-year WDI estimate is used as a local count.
- P5 G17 Maldivian female is source-blank and stays missing. EC3 and ED16 each have two unmatched island spellings (`Mundhoo/Mundoo`, `Madeveli/Madaveli`) and those local values are withheld. H7's source “safe/unsafe” categories are not WHO/JMP service tiers. EC3 age 15+ and ED16 Maldivian age 10+ are different populations.
- The 2022 atoll rows are **statistical areas**, while the President's Office says atoll councils ceased in May 2026. A current council jurisdiction or official 2022-compatible polygon is not assigned. The initial geoBoundaries ADM1 shapes were removed. One 114-page revised 2022–2026 Fonadhoo Council plan PDF is attached only to L Fonadhoo, with approval, full contents and legal boundary match unverified. Budgets, actual spending and evaluation remain unacquired.

[Source audit](../../evidence/maldives-cph2022-source-audit-2026-09-27.md), [start sheet](../../evidence/maldives-country-start-2026-09-27.md), [Task Contract](../../evidence/maldives-task-contract-2026-09-27.md) and [producer lesson audit](../../evidence/maldives-country-lesson-audit-2026-09-27.md) give the evidence boundaries. The ignored project's `evidence/` holds acquisition receipt, all-workbook inventory, selected numeric audit, actual-output files/hashes and import hash. Originals and site are outside Git.

## Reproduce and inspect

In the repository root with Python `requests`/`openpyxl` and Node dependencies:

```powershell
node scripts/create-country.mjs --country Maldives --out generated/maldives-replay-new
python scripts/fetch-maldives-cph2022.py --project generated/maldives-replay-new
python scripts/fetch-maldives-planning.py --project generated/maldives-replay-new
python scripts/inventory-maldives-cph2022.py --project generated/maldives-replay-new
python scripts/audit-maldives-cph2022.py --project generated/maldives-replay-new
```

The planning fetcher saves a receipt, uses TLS validation and reports whether the four bodies match `config/maldives-planning-source-manifest.json`. The importer rejects changed originals until the manifest and contents are reviewed. Then:

```powershell
python scripts/import-maldives-cph2022.py --project generated/maldives-replay-new
node scripts/validate-country.mjs --project generated/maldives-replay-new
node scripts/build-country.mjs --project generated/maldives-replay-new
node scripts/verify-maldives-cph2022-output.mjs generated/maldives-replay-new
npm run check
npm test
```

Producer run: validator **zero errors/warnings**, site built, six source/output cases passed, `npm run check` 155 and `npm test` 218/218. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, printable 22/9/14/11 comparison rows, source gaps and Fonadhoo-only document scope. Browser checks at `127.0.0.1:4186` confirmed nationwide→L→Fonadhoo→same L re-selection, and the plan link disappearing on L. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Maldives edition

1. Audit all 52 other acquired workbook bodies and every unselected numeric field/definition/denominator; seek newer official local statistics. Resolve two spelling conflicts through an official island code rather than an inferred name join.
2. Acquire a dated official island code register and compatible 2022 polygons, then audit the 2026 legal council boundaries and current consolidated law/amendments. Keep census partitions and current planning authorities separate.
3. Read Fonadhoo's full Dhivehi plan, approval evidence and implementation; obtain actual matching local budgets, expenditure, performance and official evaluation. Expand document coverage across representative city/island jurisdictions. Review reuse terms.
4. Complete applicable 42 scenarios, missing and edge cases, English/Dhivehi, mobile/print and Word/PDF output, then independent `ACCEPT`. Assign a Maldives-specific Hosting/Public scope and verify deployed JSON and rendered URL only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits the leads. It transfers no raw originals, observations or country acceptance. AreaData adapter/selection commit `7f800c05c281823328f5102426a6a408c4663e7e` and Kit import commit `8b256693d7a1ad4c5824be699e1326d42e18058e` were pushed and remote heads verified. The 338-source bundle carries the AreaData commit as `origin_commit`; [Kit handoff](KIT_FEEDBACK_HANDOFF.md) records validation. Local: partial candidate. GitHub: scoped code, audit and source leads pushed. Hosting: none. Public: none.

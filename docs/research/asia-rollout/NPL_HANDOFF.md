# Nepal AreaData handoff — 2026-09-27 JST

**Status: local census partial candidate, independent `ACCEPT` pending, unpublished.** Asia ledger: 0 complete, 24 partial, 1 research-only, 25 not started. The next not-started priority is Sri Lanka. The project at `generated/nepal-areadata-20260927` is ignored by Git; this handoff, importer, manifests and source audit are tracked. No Nepal hosting/public destination has been assigned.

## Acquired and adopted

- Official NSO 2021 provincial catalogue: 91 entries/province (89 XLSX, two reports). Archived four XLSX table families across seven provinces: 28 originals, of which the 21 population, water and toilet originals were adopted and seven literacy originals remain `priority_unassessed`. Three adopted families expose 19 direct count indicators and 16,230 direct observations.
- The dataset has 915 NSO statistical records: country, seven provinces, 77 districts, 753 local levels and 77 separate institutional rows. No provider or official polygon was adopted. A further 1,155 institutional private-household-amenity observations are explicitly `not_applicable`.
- Direct census population is 29,164,578. Institutional rows account for 239,098 people and 6,096 households. Private households total 6,660,841, while all households total 6,666,937. National WDI series remain separate. The inventory reconciles adopted fields from country to province to district to local/institutional rows, with the proper household universe.
- Official NSO 2023 code sheet: 77 districts matched, 749 local names normalized exactly and two with minor transliteration. Two unresolved 2021/2023 local-name conflicts have `official_code: null`; candidate codes 30304 and 70905 remain in audit evidence, never adopted as an exact join.
- Acquired the 244-page NPC 2078 local-planning guide and three Kathmandu Metropolitan City PDFs: 2083/84 action plan, 2083/84 budget/program, 2082/83 progress. Reviewed only specific opening pages, not whole bodies or approval. The city documents attach solely to local-level `NPL:NSO2021:P3:D06:L08` (2023 code 30608), not Kathmandu District or Bagmati. The Local Government Operation Act 2074 is location-only.

[The source audit](../../evidence/nepal-nso2021-source-audit-2026-09-27.md), [country start sheet](../../evidence/nepal-country-start-2026-09-27.md), [Task Contract](../../evidence/nepal-task-contract-2026-09-27.md) and [producer lesson audit](../../evidence/nepal-country-lesson-audit-2026-09-27.md) contain source URLs, exact selection rules, unresolved meanings and review scope. Raw URLs, byte lengths and hashes are pinned by `config/nepal-nso2021-source-manifest.json` and `config/nepal-planning-source-manifest.json`; acquisition and field-audit receipts live in the ignored candidate's `evidence/` directory.

## Reproduce and inspect

Run in repository root with Python supporting `openpyxl` and the existing Node dependencies:

```powershell
python scripts/inventory-nepal-nso2021.py --project generated/nepal-areadata-20260927
python scripts/import-nepal-nso2021.py --project generated/nepal-areadata-20260927
node scripts/validate-country.mjs --project generated/nepal-areadata-20260927
node scripts/build-country.mjs --project generated/nepal-areadata-20260927
node scripts/verify-nepal-nso2021-output.mjs generated/nepal-areadata-20260927
npm run check
npm test
```

The final producer rerun returned zero country-validation errors/warnings, built the site, passed eight source-cell/output cases, `npm run check` (152 modules/templates), and 218/218 tests. The output verifier checks CSV, HTML, Markdown, planning and evidence exports; full printable comparison rows were checked for country (seven provinces), Koshi (14 districts) and Kathmandu District (12 local/institutional children). In the local browser, Bagmati→Kathmandu District→Kathmandu Metropolitan City→the same district re-selection changed the analysis target and cleared city-only documents. These checks are bounded producer evidence, not independent acceptance or 42 scenario passes. Dataset hash after the last import is in ignored `evidence/NPL_IMPORT_RESULT.json` and will change on a new import timestamp.

## Remaining before a complete Nepal edition

1. Review current law and NPC guidance by page and reconcile the 2021/2023 code-name conflicts. Acquire source-compatible official province/district/local/ward polygons and their editions; keep statistical and legal planning units distinct.
2. Audit the seven literacy workbooks' row semantics, the remaining 85 XLSX families and two reports per province as needed for national theme coverage. Record acquisition, field meaning, adoption and nonadoption separately; confirm source terms before any raw redistribution.
3. Acquire representative actual palika plans, budgets, execution and official evaluations with approval and period evidence. Review every page and applicable output form of the Kathmandu example before treating its numbers or status as accepted. Budget allocations, expenditure, plan delivery and evaluation remain distinct.
4. Check the 42 applicable acceptance scenarios, other territory types, narrow/mobile/print and Word/PDF outputs, local language and user workflow. Obtain independent `ACCEPT`, then assign Nepal hosting/public scope and verify its deployed JSON and rendered URL. There is no publication authorization or destination carried over from DDPT.

Kit feedback is **source-location-only** (`official_location_identified`) until Kit independently audits each lead; it does not transfer raw originals, observations or country acceptance. The AreaData adapter and 34 official-source selections were committed/pushed at `9b0ef7ee59a81490ce7b66e0b380bced7d6a3daa`. The 217-source bundle carries that exact origin commit. Kit dry-run/import accepted all 217 leads, inserted 34 Nepal records and updated 183 earlier origin histories; Kit committed/pushed at `8294c493d1439267953759e8b927178f8ecab667`. Kit check, 173/173 tests and readiness (`ready: true`, 217 feedback sources) passed. [Kit handoff](KIT_FEEDBACK_HANDOFF.md) records the transfer. Local: partial candidate. GitHub: scoped code, audit and source leads pushed; this bundle/handoff update is committed in the following AreaData commit. Hosting: none. Public: none.

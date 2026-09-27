# Malaysia AreaData handoff — 2026-09-27 JST

**Status: DOSM 2020/2024 population and state HIES/amenities partial candidate; independent `ACCEPT` pending; unpublished.** The Asia ledger is 0 complete, 34 partial, 1 research-only and 15 not started. Next unstarted priority by CSV order: Singapore. The ignored candidate is `generated/malaysia-areadata-20260927`. No Malaysia-specific Hosting/Public destination is assigned.

## Evidence and decisions

- Six [OpenDOSM data catalogues](https://open.dosm.gov.my/data-catalogue/population_district) yielded population national/state/district, HIES state/district and amenities CSVs. The 6 originals contain 674,676 numeric cells. Selected 2020 census-adjusted and 2024 intercensal population sex totals, 2022/2024 five state HIES and three state amenities fields produce 14 indicators, 1,258 values plus 24 explicit missing amenities slots. In all, country +16 state/FT +156 subdivided districts have 173 territories. The four self-district duplicates are not extra local units.
- The 2024 HIES district table has 162 reporting rows but only 149 exact names among the 156 population district units; it is wholly held. Four older population district labels differ; their 2020 rows are held. Other ages, ethnicities and periods, all 19 MyCensus district report tables and annual report contents remain unassessed. The catalogue's apparent year wording and the CSV's 2024 rows should be reconciled.
- The [MyGeoportal UPI land-code workbook](https://www.mygeoportal.gov.my/en/unique-parcel-identifier-upi) has 16 state-code and 139 land-district-code rows. It is not yet a dated DOSM/PBT crosswalk. All 2017 reference polygons were removed. The candidate uses source-row IDs, no certified official code or plan-area identity.
- [Federal Gazette P.U. (B) 206/2025](https://www.dbkl.gov.my/files/senarai-perundangan/subsidiari/(10)-pemberitahuan-penerimaan-draf-pelan-tempatan-bagi-wpkl.pdf) confirms KL Local Plan 2040 adoption on 5 May and effect on 11 June 2025. The 576-page [DBKL plan Volume 2](https://ppkl.dbkl.gov.my/wp-content/uploads/2025/06/1.-VOLUME-2-PROMOTING-CITY-DEVELOPMENT.pdf) is acquired but unassessed beyond identity. [DBKL Budget 2025 speech](https://www.dbkl.gov.my/files/arkib-ucapan-belanjawan-dbkl/ucapan-belanjawan-2025.pdf) page 16 supplies only estimated revenue/expenditure and reported deficit, not actuals. Historical estimate workbook and 2023 annual report were acquired; actual expenditure/evaluation was not extracted. KL documents apply only to KL; PLANMalaysia's Act 172 framework cannot be imposed on Sabah/Sarawak/FTs or on DOSM districts as PBTs.

[Detailed source audit](../../evidence/malaysia-dosm-source-audit-2026-09-27.md), [start sheet](../../evidence/malaysia-country-start-2026-09-27.md), [Task Contract](../../evidence/malaysia-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/malaysia-country-lesson-audit-2026-09-27.md) and tracked `config/malaysia-dosm-source-manifest.json` define the boundary. The ignored candidate holds originals, audit JSON, output verification and built site.

## Reproduce and inspect

Create a **new** candidate directory, then download the manifest's 13 URLs to its exact `raw_path` locations. Verify byte length/SHA-256. If a source changes, audit its edition before modifying the manifest or import contract. Python needs `openpyxl` and `pypdf`. Do not overwrite the previous working candidate on download, import or build failure.

```powershell
node scripts/create-country.mjs --country Malaysia --out generated/malaysia-replay-new
# Download each manifest source URL to generated/malaysia-replay-new/<raw_path>.
python scripts/import-malaysia-dosm.py --project generated/malaysia-replay-new
node scripts/validate-country.mjs --project generated/malaysia-replay-new
node scripts/build-country.mjs --project generated/malaysia-replay-new
node scripts/verify-malaysia-dosm-output.mjs generated/malaysia-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `fabb14d24a4cbdd8265005c166bf2b78f2d3b4e153ba8e4390e0c6e18a8039d0`; validator **0 errors/warnings**, build succeeded, five source/output cases checked, 16 national state/FT population comparison rows checked, `npm run check` **162 JavaScript/JSON**, `npm test` **219/219**. Local browser at `127.0.0.1:4274` checked Selangor→Petaling→Selangor whole-area selection, KL Gazette and budget display then Selangor with no residual KL documents, and 16/16 2024 state ranking with Johor row focus leaving Selangor selected. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Malaysia edition

1. Semantically inspect all MyCensus district PDF tables and the many unselected DOSM age, ethnicity, years, HIES district and amenities district fields. Track definition, unit, universe, true zero, missing and survey uncertainty individually.
2. Obtain official date-specific DOSM statistical codes, UPI/PBT crosswalk and compatible boundaries. Resolve the four changed 2020 district labels, HIES 2024's 162 rows, Sabah/Sarawak changes and whole-area duplicate rows before district survey comparisons.
3. Verify each jurisdiction's current law/authority and actual plan, budget, expenditure, implementation and evaluation documents. For KL, inspect Volume 2's full contents and the scanned annual financial statements; keep 2025 speech estimates distinct from actuals.
4. Confirm source reuse terms, complete applicable 42 scenarios and full CSV/print/mobile/performance/language/local-user checks, then obtain independent `ACCEPT`. Set Malaysia-specific Hosting/Public scope and inspect deployed JSON and rendered URLs only after acceptance.

Kit feedback transfers **official locations and reuse cautions only** at `official_location_identified`. It transfers no raw CSV/PDF/XLSX, numeric observations, code/geometry match or country acceptance. **Local:** partial candidate. **GitHub:** code, audit, source leads. **Hosting:** none. **Public:** none. Commit IDs are recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) after the two-repository exchange.

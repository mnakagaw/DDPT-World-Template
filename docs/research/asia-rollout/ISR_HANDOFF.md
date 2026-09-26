# Israel country candidate — handoff, 2026-09-26

**Status: official CBS 2022 nation/six-district partial candidate; not independently accepted or published.** The ignored output is `generated/israel-areadata-20260926`. Six original Excel workbooks and their receipts, 14-sheet/3,410-column discovery inventory, district crosswalk, import audit, selected output checks and site are local only. The [tracked source audit](../../evidence/israel-cbs-2022-official-sources-2026-09-26.md) gives exact source URLs, hashes, field decisions and geographic caveats. Do not commit the original workbooks without redistribution review.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country Israel --out <new-directory>
python -X utf8 scripts/collect-israel-cbs-census-2022.py --project <new-directory>
python -X utf8 scripts/inspect-israel-cbs-census-2022.py --project <new-directory>
python -X utf8 scripts/import-israel-cbs-district-partial.py --project <new-directory>
python -X utf8 scripts/register-israel-official-source-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-israel-cbs-output.mjs --project <new-directory>
```

The importer pins the broad-workbook SHA-256 and exact 12 column codes. It adopts 84 observations for Nationwide and six CBS districts. The CBS separately reported Judea and Samaria Area (code 7, population 481,940) remains in source evidence only. Six mapped district populations sum to 9,119,780; that separate row reconciles to the CBS national 9,601,720. Do not infer political status from this source layout, invent a seventh district polygon or distribute the national residual across the six districts. The six 2017 `geoBoundaries` polygons are reference shapes matched by name; current official legal boundary equivalence is unverified. The 12 national WDI series are separate from the CBS 2022 census series.

The other five acquired census files and all nonadopted columns remain structurally inventoried but semantically unassessed. The CBS geographic-code API, Planning and Building Law record, XPLAN plan search and local-authority audited-finance dataset are only source locations. No actual local plan, approved budget, expenditure, implementation or official evaluation has been attached. The planning institutional unit and current code/boundary join remain unresolved.

The first local candidate dataset SHA-256 is `A0F345B24A91C37E94A3173D995EF429F6658E03CF67C842E6C7DAC9B981A118`. It passed the country validator with zero errors and one expected planning-document warning, build and selected HTML/CSV/value/source checks. The browser showed national CBS 9,601,720 and distinct WDI population, six district comparison rows, Tel Aviv selection, then country reset without stale district values. A fresh ignored directory (`generated/israel-replay-20260926`) reacquired the six originals and reproduced the **same 84 adopted CBS observation tuples, full structural column inventory and original hashes**; its validator, build and output verifier also passed. Dataset file hashes differ because generated timestamps and the live national bootstrap are separate. The `evidence/COUNTRY_LESSON_AUDIT.md` in the ignored project marks the sampled scenarios and remaining gates. Independent 42-scenario and source/UX `ACCEPT` are not complete. Hosting and public verification have not been run.

Next: inspect census localities and statistical areas by official codes and source definitions, obtain a dated official boundary/code edition, acquire representative actual plan and audited finance records by planning unit, then test a populated local unit, an unpopulated unit and a source-scope exception across screen and outputs. Keep this candidate unpublished until independent `ACCEPT`.

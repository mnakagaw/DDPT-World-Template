# Palestine country candidate — handoff, 2026-09-26

**Status: PCBS 2017 final census Table 2 nation/two reporting regions/16 governorates, four direct count fields, plus two national Ministry of Local Government references. Partial, not independently accepted or published.** The ignored local candidate is `generated/palestine-areadata-20260926-v2`; the independent bootstrap replay is `generated/palestine-replay-20260926`. The [tracked source audit](../../evidence/palestine-pcbs-2017-molg-sources-2026-09-26.md) records official URLs, raw hashes, source table/column decisions, plan-document scope, numerical controls and sampled verification. Large original PDFs/HTML and receipts remain local pending redistribution review.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country PSE --out <new-directory>
python -X utf8 scripts/collect-palestine-pcbs-2017-sources.py --project <new-directory>
python -X utf8 scripts/collect-palestine-molg-planning.py --project <new-directory>
python -X utf8 scripts/inspect-palestine-pcbs-2017.py --project <new-directory>
python -X utf8 scripts/import-palestine-pcbs-2017-partial.py --project <new-directory>
python -X utf8 scripts/import-palestine-molg-planning.py --project <new-directory>
python -X utf8 scripts/register-palestine-official-source-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-palestine-pcbs-output.mjs --project <new-directory>
```

`python -X utf8 scripts/compare-palestine-pcbs-replay.py --project <first-project> --replay <second-project>` compares two independently bootstrapped candidates using the same pinned five originals. The actual replay matched 19 territories, 76 PCBS observations, two national documents and seven PCBS/MoLG source records; adopted tuple SHA-256 `c8338c5caa3b50d53f00edd1b63c1f6d9584cab53687f07d59e05d2bdd688440`. Fresh WDI fetch times are excluded from semantic equality.

The current dataset SHA-256 is `0f66351ca0b4701e3aa637b45d5ee1926bbd50e9d57cddc79c66bd97b6da5908`. It has **19 territories, 16 indicators, 388 observations, 76 domestic PCBS observations, two national documents and zero accepted polygons**. The 2017 PCBS national final count is 4,781,248, including the post-enumeration estimate noted by the source. WDI's “West Bank and Gaza” annual economy values stay separate. PCBS 2017 Table 29 now has a coordinate-based extraction aid for all 585 locality code/count cells, including 56 physically wrapped source rows, but the 4,500,085 locality sum differs from the 4,781,248 printed national final total by 281,163. The cause and allocation remain unverified, so no locality count is adopted; see PSE_TABLE29_REPAIR.md. The 270-page detailed census volume and 2019-hosted area table are acquired but unassessed for numeric adoption.

`validate-country` returned zero errors and warnings; build and seven-area CSV/HTML output checks passed. `npm run check` and 218/218 tests passed. Browser checks covered Palestine, West Bank, Jenin, explicit parent reselection, Gaza Strip, same-name Gaza Governorate, planning and thematic navigation. The Gaza Governorate planning page correctly shows zero local documents while keeping the 2018 city/town SDIP guide and 2025–2027 national MoLG sector strategy in a separate national reference section. The ignored `evidence/COUNTRY_LESSON_AUDIT.md` records the limited producer check; **42 applicable acceptance scenarios and independent `ACCEPT` remain open**. Hosting and Public verification have not run.

Official-source feedback exports only public URLs and records all seven PSE leads at `official_location_identified` until Kit independently acquires/audits them. This producer candidate does not authorize `source_acquired`, a current local-plan status or a country-edition completion in Kit. The AreaData and Kit commit/roundtrip record is in [KIT_FEEDBACK_HANDOFF.md](KIT_FEEDBACK_HANDOFF.md).

Next: inventory every relevant physical table and numeric column in the 186-page Summary and 270-page detailed PCBS volumes; resolve the Table 29 locality-versus-national difference 281,163, Jerusalem J1/J2 and the dated locality code hierarchy; obtain dated official governorate/legal polygons; determine current governorate versus municipal/village-council planning obligations; acquire individual plans, approval, budget, expenditure and evaluation originals. Expand representative and exception area UI/export/print checks and complete independent acceptance before any public deployment.

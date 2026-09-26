# Asia source feedback to Census Dashboard Kit — 2026-09-26

This handoff records the source-location loop for the current Asia work. It transfers public source leads and reuse cautions, not observations, raw files, candidate acceptance, or permission to publish a country edition.

| Step | Repository / artifact | Commit / result |
|---|---|---|
| AreaData source selection and evidence | `DDPT-World-Template`, `config/kit-source-feedback-selections.json` | `6c348e5f1452f6b523cd4a09b2144a3295c7ac75` |
| AreaData exported bundle | `evidence/KIT_SOURCE_FEEDBACK.json` | `d7a35e6266d1dbaec56d0e6b955d93c37e6c5dae` |
| Kit import | `Census-Dashboard-Kit`, `config/areadata-source-feedback.json` | `bd9f45f558619ad99f78e3b1ac5db30313be68c3`, branch `codex/asia-source-feedback-20260926` |

The bundle has 30 source leads in eight countries: BFA 14, BGD 2, IRQ 4, LAO 2, SAU 1, TUR 1, UGA 3, YEM 3. The Iraq COSIT table catalogue and Yemen CSO/law leads are part of the current Middle East continuation. Other leads were already recorded in AreaData and are carried forward without claiming a new discovery. All 30 exported stages are capped at `official_location_identified` pending independent source audit; the Kit import starts every lead at `not_acquired_by_kit_preflight`.

Kit's importer dry-run and actual import each accepted 30 source leads. The merge inserted 6, updated 24 and left 31 total records. The additional origin events on older sources record this export without changing their current-project acquisition status. `npm run check`, `npm test` (173/173) and `npm run verify:kit` passed in the isolated Kit worktree. The Kit branch was pushed to GitHub and `git ls-remote` matched `bd9f45f558619ad99f78e3b1ac5db30313be68c3`.

The next country adapter must recheck its URL, acquire and inspect the source, match official territorial codes and boundary versions, and adopt only verified tables and indicators. This import does not change the Asia country status counts or the independent `ACCEPT` gate.

## Jordan continuation — 2026-09-26

AreaData added six new Jordan official-source leads: three 2025 DoS workbooks, the DoS 2015 census table catalogue, the Ministry-hosted 2018 governorate planning guide and the 2021 Local Administration Law PDF. The tracked [source audit](../../evidence/jordan-dos-2025-source-audit-2026-09-26.md) records which originals were acquired and which tables were actually adopted. The feedback bundle retains only source leads, public URLs and reuse cautions; all six Jordan stages remain `official_location_identified`.

| Step | Commit / verification |
|---|---|
| AreaData selection, importer and evidence | `af9b28f7f6175a6b8259139195b24678f99e28fc` on `codex/asia-domestic-20260926` |
| AreaData 36-source / nine-country bundle | `84fdbca1fa690cbfaac3cc28f3ed55187840eb5b`; `evidence/KIT_SOURCE_FEEDBACK.json` has this edition's `origin_commit` = `af9b28f7f6175a6b8259139195b24678f99e28fc` |
| Kit import | `0f0d195e87226909e20100b6753f361793e27d94` on `codex/asia-source-feedback-20260926`; six inserted, 30 origin histories updated, 37 records total |
| Kit validation | Import dry-run and actual import both accepted 36 leads; `npm run check`, `npm test` (173/173), `npm run verify:kit` (`ready: true`, 36 feedback sources) passed in an isolated clone. |

Both branches were pushed to GitHub. Kit keeps all imported leads at `not_acquired_by_kit_preflight`; the import does not reclassify Jordan as accepted or authorize publication.

## Jordan Table 2.17 continuation — 2026-09-26

AreaData added the [official DoS 2015 drinking-water-source Table 2.17 PDF](../../evidence/jordan-census-water-2015-source-audit-2026-09-26.md) as Jordan's seventh lead. The AreaData candidate independently uses selected 2015 fields, but the Kit transfer remains only a public source location and reuse caution. Its feedback stage is capped at `official_location_identified`; Kit's project state remains `not_acquired_by_kit_preflight`.

| Step | Commit / verification |
|---|---|
| AreaData source selection, importer and evidence | `38adfac5d3ec98d5203bc3efcca98377d0b36b63` on `codex/asia-domestic-20260926` |
| AreaData 37-source / nine-country bundle | `988ad784110cea29dd1e0be46db32816306e00f6`; `evidence/KIT_SOURCE_FEEDBACK.json` has `origin_commit` = `38adfac5d3ec98d5203bc3efcca98377d0b36b63` |
| Kit import | `f7e655080ee13f03f086231ba46a1877c44e0087` on `codex/asia-source-feedback-20260926`; one source inserted, 36 origin histories updated, 38 records total |
| Kit validation | Import dry-run and actual import both accepted 37 leads; `npm run check`, `npm test` (173/173), `npm run verify:kit` (`ready: true`, 37 feedback sources) passed in the isolated Kit clone. Both remote branch heads matched `git ls-remote`. |

The imported lead does not carry the raw PDF, the 910 numeric cells or AreaData's calculated indicators, and it does not advance any country's independent acceptance status.

## Syria historical census and current planning leads — 2026-09-26

Five new Syria leads were selected: two archived copies of **original CBS 2004 census PDFs**, one OCHA-distributed XLS mirror, an official SANA report about a **proposed** 2025 local-development planning method, and the Ministry of Finance's **national** 2026 citizen-budget PDF location. The [source audit](../../evidence/syria-cbs2004-source-audit-2026-09-26.md) records 213 PDF/XLS numeric differences and why AreaData used PDF values. The feedback transfers no observations or raw material, and no local plan or local budget is asserted.

| Step | Commit / verification |
|---|---|
| AreaData selection, importer and evidence | `fdcedd992c03099c5b87bd47db5995b34179bae2` on `codex/asia-domestic-20260926` |
| AreaData 42-source / ten-country feedback bundle | `f9bb915361da5f847ecdf040276e56ebd46a52b6`, with `origin_commit` = `fdcedd992c03099c5b87bd47db5995b34179bae2` |
| Kit import | `2d5f93d5439ec4e5e9ab889ebc320df5426e34ce` on `codex/asia-source-feedback-20260926`; five inserted, 37 existing origin histories updated, 43 records total |
| Kit validation | Dry-run and import both accepted 42 leads. `npm run check`, `npm test` (173/173), `npm run verify:kit` (`ready: true`, 42 feedback sources) passed. Both remote branch heads matched `git ls-remote`. |

All five Syria feedback stages remain `official_location_identified`, and Kit's own state remains `not_acquired_by_kit_preflight`. The archive URLs preserve old official content but are not live current CBS endpoints. The SANA report is not an adopted guide and the national citizen budget is not a governorate budget. This transfer does not change Syria's partial/unpublished or the Asia independent-acceptance count.

## UAE FCSC and Abu Dhabi leads — 2026-09-26

Four public leads were selected: the FCSC 2009 report's 2005 census table, SCAD's Abu Dhabi 2023 R1/2024 population page, the FCSC UAE.Stat population explorer and the UAE government's Dubai 2040 plan overview. The [source audit](../../evidence/uae-fcsc-scad-population-source-audit-2026-09-26.md) records that FCSC 2005 and SCAD 2024 differ in period, geographic scope and method. The UAE government's local-government overview remains in the AreaData research record but was **not** exported under `planning_law`: it is not an enacted law.

| Step | Commit / verification |
|---|---|
| AreaData selection, importer and evidence | `ce802a37d89ef6c3aef1a18a32b5f3e52f6dedb9` on `codex/asia-domestic-20260926` |
| AreaData 46-source / eleven-country bundle | `b04a0736df95ffc3d36187cf59b4b8a07b35ae2b`; `origin_commit` = AreaData `ce802a37d89ef6c3aef1a18a32b5f3e52f6dedb9` |
| Kit import | `7d4eef354a2e7241a0b758bbb77ac072ed53471b` on `codex/asia-source-feedback-20260926`; four inserted, 42 existing origin histories updated, 47 records total |
| Kit validation | Dry-run/import accepted 46 leads; `npm run check`, `npm test` (173/173) and `npm run verify:kit` (`ready: true`, 46 feedback sources) passed. Both remote heads matched `git ls-remote`. |

The four UAE stages remain `official_location_identified`; Kit marks them `not_acquired_by_kit_preflight`. No observation, raw file, current all-emirate comparability or country `ACCEPT` passes through feedback. The UAE candidate stays partial/unpublished.

## Azerbaijan SSC and planning leads — 2026-09-26

Nine new public official leads were selected: SSC population tables 1.15, 1.17 and 1.19; the 2024 administrative classification; 2019 census Volumes A/B; the regional statistics yearbook catalogue; the President's Urban Planning and Construction Code page; and ARXKOM's master-plan catalogue. [The Azerbaijan source audit](../../evidence/azerbaijan-ssc-population-source-audit-2026-09-26.md) distinguishes the two adopted population/sex tables from the unadopted historical fields, front-matter-only census volumes and location-only planning/yearbook leads. No raw files, observations or country acceptance state are transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `32a916ad84aedb3aae8a5721fa60271d81707bae`, then source-register extension `8a03b814df077f7f9bf25a57c46a69e50eafeba8` on `codex/asia-domestic-20260926` |
| AreaData 55-source / twelve-country bundle | `98258093dd11c9b0de204e880c54a7735a8556fb`; `origin_commit` = `8a03b814df077f7f9bf25a57c46a69e50eafeba8` |
| Kit import | `80482539a4081bd4ac82fefd21e210301fb33d13` on `codex/asia-source-feedback-20260926`; nine inserted, 46 existing origin histories updated, 56 records total |
| Kit validation | Dry-run and import accepted 55 leads. `npm run check`, `npm test` (173/173) and `npm run verify:kit` (`ready: true`, 55 feedback sources) passed. Kit branch pushed. |

All nine Azerbaijan feedback stages are `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. The 2024 code PDF has three held city/rayon joins and no local polygons; the two census volumes were acquired in AreaData but not table-by-table assessed. Kit must independently inspect them before reuse. Azerbaijan remains partial and unpublished.

## Israel CBS 2022 and planning-service leads — 2026-09-26

Nine new public official leads were selected: six CBS 2022 Census workbooks, Planning Administration XPLAN search, the planning/building laws index and Mavat procedural guidance. [The Israel source audit](../../evidence/israel-cbs2022-source-audit-2026-09-26.md) distinguishes the eight adopted columns and first-level rows from the unassessed fields and locality sheets. It records the Israeli-localities-only scope of CBS area 7, the unmatched 2006 reference boundary and absence of actual plan/budget records. No raw files, observations or country acceptance state were transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `732648d4dc766dd237e811a4ece0449b53310b44` on `codex/asia-domestic-20260926` |
| AreaData 64-source / thirteen-country bundle | `61739706af75589d14fbdd07b2516cee533091a1`; `origin_commit` = `732648d4dc766dd237e811a4ece0449b53310b44` |
| Kit import | `7e51a594a6f2d04b045a67e5075e742d6deda67f` on `codex/asia-source-feedback-20260926`; nine inserted, 55 existing origin histories updated, 65 records total |
| Validation | AreaData `npm run check`, `npm test` (218/218), country validation (zero errors, one missing-plan warning) and seven-case output verifier passed. Kit dry-run/import accepted 64 leads; Kit `npm run check`, `npm test` (173/173) and `npm run verify:kit` (`ready: true`, 64 feedback sources) passed. Both branches were pushed. |

All nine Israel feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently inspect the workbooks, scope, code and source terms before any adoption. Israel remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Lebanon CAS survey and planning leads — 2026-09-26

Seven public official leads were selected: the CAS LFHLCS main survey PDF and demography workbook, CAS subnational MICS 2023 Chapter 11 workbook, CAS district-profile catalogue, DGU zoning procedure, ministry DGU office description and DGU national master-plan overview. [The Lebanon source audit](../../evidence/lebanon-cas-lfhlcs-source-audit-2026-09-26.md) separates the four selectively adopted survey indicators from the unassessed source tables, incomplete MICS geography, incompatible 2017 geometry and location-only planning leads. This is a household survey, not a census. No raw files, observations or country acceptance state were transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `dd6b31fce9fff097aca98a01c7b1008ba3a3fccc` on `codex/asia-domestic-20260926` |
| AreaData 71-source / fourteen-country bundle | `87a822247784243b0409c3f4fee57930f97b07d7` on the same branch; bundle `origin_commit` = `dd6b31fce9fff097aca98a01c7b1008ba3a3fccc` |
| Kit import | `07ccade0e9141b46b82061ab6a1a12397cb734b0` on `codex/asia-source-feedback-20260926`; seven inserted, 64 existing origin histories updated, 72 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, one missing-plan warning), build and eight-case output verifier passed. Kit dry-run/import accepted 71 leads; Kit check, 173/173 tests and readiness (`ready: true`, 71 feedback sources) passed. Both branches were pushed. |

All seven Lebanon feedback stages are `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently acquire and inspect them before reuse. Lebanon remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Palestine PCBS census and MoLG leads — 2026-09-26

Ten public official leads were selected: four PCBS 2017 original PDFs (updated summary, separate counted-population detail, earlier summary and locality code guide), the PCBS projection table location, MoLG law/guidance/project/budget locations and the PCBS/MoLG boundary-revision note. [The Palestine source audit](../../evidence/palestine-pcbs2017-source-audit-2026-09-26.md) separates the selected updated-summary Table 2/29 fields from the 71 unadopted or unassessed report tables, projection, code-edition differences, absent polygons and location-only planning leads. No raw file, observation, formal planning state or country acceptance is transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `bdbc4c2e7f84e22b5a2220c43aa5c7d258b9051d` on `codex/asia-domestic-20260926`; Kit role mapping corrected at `365d0faae2ab52da4af6b07d6e0bf5966c563cce` |
| AreaData final 81-source / fifteen-country bundle | `9b25bff7363880f733d66fcc7eabc0afb13475fb` on the same branch; bundle `origin_commit` = `365d0faae2ab52da4af6b07d6e0bf5966c563cce` |
| Kit import | `e4233578211dc6c1fd7d8d9dc4bd909c8a348504` on `codex/asia-source-feedback-20260926`; ten inserted, 71 existing origin histories updated, 82 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, one missing-plan warning), build and twelve-case output verifier passed. Kit dry-run/import accepted 81 leads; Kit check, 173/173 tests and readiness (`ready: true`, 81 feedback sources) passed. |

All ten Palestine feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. The 2026 pre-conflict projection is not an observed present population series. Kit must independently review PDFs, 2017 code/boundary edition, current law and actual plan/fiscal bodies before use. Palestine remains partial and unpublished.

## Oman NCSI registration and planning leads — 2026-09-26

Six public official leads were selected: the NCSI 2026 Statistical Year Book Table 7-2, the 2020 eCensus portal, the 2026 Urban Planning Law, the 2022 Governorates System, the national spatial strategy overview and MoHUP projects catalogue. [The Oman source audit](../../evidence/oman-ncsi-yearbook-source-audit-2026-09-26.md) records the six adopted nationality/year columns, calculated totals and independent published-total checks. The feedback carries no raw PDF, 450 source cells, 225 calculated values, plan body or acceptance state.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `a85495247cadcd677ab1a4a6b450bf511bd32737` on `codex/asia-domestic-20260926` |
| AreaData 87-source / sixteen-country bundle | `dce7935204d79ec01bfedb6b4ac95e7c6905ff17` on the same branch; bundle `origin_commit` = `a85495247cadcd677ab1a4a6b450bf511bd32737` |
| Kit import | `6fcf0afd61f46523b8f26d1c0cdfca34935d8b12` on `codex/asia-source-feedback-20260926`; six inserted, 81 origin histories updated, 88 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, one missing-plan warning), build and twelve-case output verifier passed. Kit dry-run/import accepted 87 leads; Kit check, 173/173 tests and readiness (`ready: true`, 87 feedback sources) passed. |

All six Oman stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently inspect the yearbook, eCensus, legal terms and plan bodies before reuse. Oman remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Kuwait CSB registration census and planning leads — 2026-09-26

Twelve public official leads were selected: the CSB 2021 census catalog and eight table locations, a historical CSB geography report, the municipality-law catalog and an archived national plan. [The Kuwait source audit](../../evidence/kuwait-csb2021-source-audit-2026-09-26.md) identifies the eight adopted tables and their 3,246 checked numeric cells, the 110 cataloged tables whose numeric bodies remain unaudited, and the boundary and planning gaps. The feedback contains source locations only; it transfers no original workbook, PDF, observation, code/boundary join or acceptance state.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `94a9adeb9f14f6f3653570ad87c68eeede46eb83` on `codex/asia-domestic-20260926` |
| AreaData 99-source / seventeen-country bundle | `2717366ebb7d413f137bad6a2fc70e631b40538a` on the same branch; the Kuwait entries have `origin_commit` = `94a9adeb9f14f6f3653570ad87c68eeede46eb83` |
| Kit import | `c1868b039440c137b8d52425df9711378af3a422` on `codex/asia-source-feedback-20260926`; twelve inserted, 87 existing origin histories updated, 100 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, one missing-plan warning), build and 15-case actual output verifier passed. Kit dry-run/import accepted 99 leads; Kit check, 173/173 tests and readiness (`ready: true`, 99 feedback sources) passed. |

All twelve Kuwait feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently acquire and assess source files, scope, codes, terms and planning authority before reuse. Kuwait remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Georgia Geostat 2024 census and planning leads — 2026-09-26

Thirteen public official leads were selected: the Geostat final-2024 census catalogue and five selectively adopted workbooks, Geostat GIS portal, the Matsne spatial and local-government codes, Ordinance 260, the Tbilisi plan and initial 2026 budget records, and Batumi municipality's budget portal. [The Georgia source audit](../../evidence/georgia-geostat2024-source-audit-2026-09-26.md) distinguishes five audited/adopted tables from 43 other acquired but semantically unassessed originals, no official code/polygon join and location-only planning materials. Feedback transfers no raw XLSX/PDF, observation, plan body, budget amount, official status or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit and status | `8bf8d222f0b4b664486fc1ad3aed27bac1d56f47` on `codex/asia-domestic-20260926` |
| AreaData 112-source / eighteen-country bundle | `d2a5c42b817c6552787d2ef68b014039625b5029` on the same branch; bundle `origin_commit` = `8bf8d222f0b4b664486fc1ad3aed27bac1d56f47` |
| Kit import | `b390195c9b030f96ca651a4cb1c7c77dc8e1dac5` on `codex/asia-source-feedback-20260926`; 13 inserted, 99 existing origin histories updated, 113 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, one missing-plan warning), build and 13-case actual output verifier passed. Kit dry-run/import accepted 112 leads; Kit check, 173/173 tests and readiness (`ready: true`, 112 feedback sources) passed. Both branches were pushed. |

All thirteen Georgia stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently acquire and classify the workbooks, official geography, terms, planning authority and actual fiscal documents. Georgia remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Qatar NPC Census 2020 and QNMP leads — 2026-09-26

Ten official public leads were selected: NPC's 2020 results catalogue, main and alternate workbook URLs, the original PDF's Zone No. crosswalk, the NPC GIS atlas location, the QNMP MSDP directory, zoning page, QNDF, historical Al Shamal strategy and historical combined Al Rayyan/Al Shahhaniya strategy. [The Qatar source audit](../../evidence/qatar-npc2020-source-audit-2026-09-26.md) distinguishes the 12 partly adopted tables from 144 unassessed numbered tables, the alternate workbook's misleading `2022` filename, five population-missing Zones and the historical planning reference. No workbook/PDF bytes, observations, current planning approval, code/polygon join or country acceptance were transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit, status and ten selections | `69551828f7c3173d6a44b196e1b8a9e522897e81` on `codex/asia-domestic-20260926` |
| AreaData 122-source / nineteen-country bundle | `049fec26faa627a48a09a27017eec657c415c074` on the same branch; Qatar entries have `origin_commit` = `69551828f7c3173d6a44b196e1b8a9e522897e81` |
| Kit import | `d685a681ae1b356b73d985de4b2a77610c8c2d03` on `codex/asia-source-feedback-20260926`; ten inserted, 112 older origin histories updated, 123 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors/warnings), build and 14-case actual output verifier passed. Kit dry-run/import each accepted 122 leads; Kit check, 173/173 tests and readiness (`ready: true`, 122 feedback sources) passed. Remote parity is recorded in the final handoff commit. |

All ten Qatar feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. The 2017 Al Shamal volume is a historical reference, not proof of its present legal effect. Kit must independently inspect original sheets, exact geographic definitions, source terms, current plan versions and boundary data before use. Qatar remains partial and unpublished.

## Armenia ArmStat 2022 census and planning leads — 2026-09-26

Seven official public leads were selected: the ArmStat 2022 results directory and Chapter 1 archive, the ARLIS administrative classifier and Local Self-Government Law, the Ashtarak plan decision, municipality catalogue entry and plan PDF location. [The Armenia source audit](../../evidence/armenia-armstat2022-source-audit-2026-09-26.md) distinguishes two partly adopted population workbooks from 55 other unassessed workbooks, 2025 codes from unverified 2022 polygon geography, council approval from the unacquired PDF body and WDI estimates from census populations. No original, observation, plan content, code/polygon join or country acceptance was transferred.

| Step | Commit / verification |
|---|---|
| AreaData importer, source/producer audit, status and seven selections | `0c157b289154e3bc115698b07bf90198d730a11b` on `codex/asia-domestic-20260926` |
| AreaData 129-source / twenty-country bundle | `195cfaa67872566b48351bd262a2fc2ea2be648d` on the same branch; Armenia entries have `origin_commit` = `0c157b289154e3bc115698b07bf90198d730a11b` |
| Kit import | `60d02046ee0fdc54b1112d31e1b6a387d1f45f4b` on `codex/asia-source-feedback-20260926`; seven inserted, 122 existing origin histories updated, 130 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors, eight source-terms warnings), build and nine-case actual output verifier passed. Kit dry-run/import each accepted 129 leads; Kit check, 173/173 tests and readiness (`ready: true`, 129 feedback sources) passed. |

All seven Armenia stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight` for each. Kit must independently acquire and inspect originals, source terms, classifier edition, actual planning material and dated polygons before reuse. Armenia remains partial and unpublished; no independent `ACCEPT` or hosting is implied.

## Bahrain iGA Census 2020 and UPDA leads — 2026-09-27 JST

Nine official public leads were selected: the iGA 45-dataset Census-theme catalogue, the selectively adopted 2020 population table, separate annual population and area series, the 1994 planning law, its 2022 amendment, the 2023 zoning decision, the UPDA procedure manual and the historical Capital 2017 zoning-map decision. [The Bahrain source audit](../../evidence/bahrain-iga2020-source-audit-2026-09-27.md) records the 45 numeric-field inventory, selected cell checks, 27 unassessed fields and the excluded three-building-table governorate conflict. Feedback transfers public locations and reuse cautions only, not raw API pages/PDFs, 184 observations, a code/polygon join, current planning status or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData importer, evidence, status and nine selections | `6fbe93a6e7c2b240d0f69c63f3e4eb8dbc472836` on `codex/asia-domestic-20260926` |
| AreaData 138-source / 21-country bundle | `b241538e904ac5399bab8815198368ce13cb9233` on the same branch; the nine Bahrain entries carry the full `6fbe93a6e7c2b240d0f69c63f3e4eb8dbc472836` origin commit |
| Kit import | `abee464955a966b2cb6645ea70188a9ffb4880bf` on `codex/asia-source-feedback-20260926`; nine inserted, 129 older origin histories updated, 139 records total |
| Validation | AreaData check, 218/218 tests, country validation (zero errors/six source-terms warnings), build and eight-case actual output verifier passed. Kit dry-run/import each accepted 138 leads; Kit check, 173/173 tests and readiness (`ready: true`, 138 feedback sources) passed. |

All nine Bahrain stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`. Kit must independently reacquire and classify sources, check annual method and planning editions, resolve local building values, source terms and official polygons before reuse. The feedback `checked_at` is 2026-09-26 UTC; this handoff is dated 2026-09-27 in Japan. Bahrain remains partial and unpublished, with no independent `ACCEPT` or hosting implied.

## Cyprus CYSTAT 2021 census, GEOCODES and planning leads — 2026-09-27 JST

Fourteen official public leads were selected: CYSTAT's 46-table census catalogue, seven selectively adopted matrix URLs, its final release, the 2015 GEOCODES classification, the DLS INSPIRE administrative-boundary catalogue, the DTPH development-plan catalogue and 2026 process notice, and the Ministry's district-local-government-organisation page. [The Cyprus source audit](../../evidence/cyprus-cystat2021-source-audit-2026-09-27.md) separates seven archived matrices from 39 location-only tables, 120 inventoried source-field combinations from the 65 still unassessed, historical code existence from matched boundaries, and a plan location/process from plan content or legal effect. Feedback transfers no raw API body/PDF/CSV, observation, polygon join, plan status or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, evidence, status and fourteen selections | `21b524f4199802c154417a5ee734de4300a8585b` on `codex/asia-domestic-20260926` |
| AreaData 152-source / 22-country bundle | `74ec4af5560dafa9878a385a62e1498693b30005` on the same branch; Cyprus entries carry the full AreaData adapter commit as origin |
| Kit import | `92e87ad9e46462eec13f1b0f8969bd1bb085359a` on `codex/asia-source-feedback-20260926`; dry-run and import accepted 152 leads, fourteen inserted, 138 existing updated, 153 records total |
| Validation | AreaData check 148 modules/templates, 218/218 tests, Cyprus country validation zero errors/warnings, build and eight-case actual output verification. Kit check, 173/173 tests and readiness (`ready: true`, 152 feedback sources) passed. Kit branch was pushed. |

All fourteen Cyprus feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`. The 2015 GEOCODES and DLS boundary listing require current geographic reconciliation, and PxWeb source terms need independent review. Cyprus remains a partial local candidate without independent `ACCEPT` or hosting. Feedback `checked_at` is 2026-09-26 UTC, the day the official sources were checked.

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

## India ORGI 2011 PCA, geography and Panchayat planning leads — 2026-09-27 JST

Eight public official locations were selected: the acquired ORGI 2011 state/district PCA workbook, lower-unit Population Finder catalogue, 2011 administrative atlas, current LGD catalogue, acquired Constitution Articles 243G/243W, two acquired MoPR FY 2026–27 planning guidance PDFs, and eGramSwaraj's portal information page. [The India source audit](../../evidence/india-orgi-pca2011-source-audit-2026-09-27.md) distinguishes 24 adopted field/reporting-row combinations from 231 unassessed, 2011 census units from current LGD/Panchayats, and national planning guidance from local plan/financial bodies. The feedback contains source addresses and cautions only: no raw workbook/PDF, numerical observation, legal plan status, polygon join or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData India adapter, evidence, status and eight selections | `f2f76938e324c77e44141bb0d9566c7058df5025` on `codex/asia-domestic-20260926` |
| AreaData 160-source / 23-country bundle | `385c7e56308cd817238a55475a0f78b0655aef0b` on the same branch; India origin events carry the full adapter commit |
| Kit feedback import | `7709e71860ea8f4a1c6c70651077cdb16e00181b` on `codex/asia-source-feedback-20260926`; dry-run and import accepted 160 leads, eight India records inserted, 152 prior records updated, 161 total |
| Validation | AreaData check 149 modules/templates, 218/218 tests, India country validation zero errors/warnings, build and seven-case actual output verification. Kit check 52 JS/templates + 67 Markdown, 173/173 tests and readiness (`ready: true`, 160 AreaData feedback sources) passed. Remote parity is recorded after branch push. |

All eight India feedback stages are `official_location_identified` and Kit stores `not_acquired_by_kit_preflight`; the source bodies acquired by AreaData were not copied to Kit. Both states are intentionally conservative until Kit independently checks each source. This feedback does not close the India candidate's current geography, state law, local plan/fiscal, source-terms or independent-audit gaps. Feedback `checked_at` is 2026-09-26 UTC; the handoff is dated 2026-09-27 JST.

## Pakistan PBS 2023 census, geography and local-government leads — 2026-09-27 JST

Seventeen public official locations were selected: the PBS numbered-table catalogue and six Table 1 workbooks, PBS GIS/administrative-district and Census District code references, five provincial/ICT local-government law locations plus KP tehsil rules, and the federal PSDP page. [The Pakistan source audit](../../evidence/pakistan-pbs2023-source-audit-2026-09-27.md) distinguishes the six partly adopted Table 1 count fields from unassessed lower-unit fields and the 32 other numbered tables. It also records the Topi Tehsil source-cell conflict, the four-province-plus-ICT scope, and the absence of an official administrative-district code/polygon join. The feedback carries no raw workbook, observations, legal body, plan or budget record, district code, or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData importer, evidence, status and seventeen selections | `c7d2678c0907a2be5c6605f4146376c4a87bd93b` on `codex/asia-domestic-20260926` |
| AreaData 177-source / 24-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries `origin_commit` = `c7d2678c0907a2be5c6605f4146376c4a87bd93b` |
| Kit import | `3af46382fda7941fc88722727f9a82ba321d7fa2` on `codex/asia-source-feedback-20260926`; dry-run and import accepted 177 leads, seventeen Pakistan records inserted, 160 existing origin histories updated, 178 records total |
| Validation | AreaData check 150 modules/templates, 218/218 tests, Pakistan country validation zero errors/warnings, build and nine-case actual output verifier passed. Kit check 52 JS/templates + 67 Markdown, 173/173 tests and readiness (`ready: true`, 177 feedback sources) passed. Kit remote branch head matched `git ls-remote`. |

All seventeen Pakistan feedback stages are `official_location_identified`; Kit stores `not_acquired_by_kit_preflight`. Kit must independently acquire and inspect the source bodies, Table 1 scope, census versus administrative district codes, provincial law editions, local plan/fiscal records and source terms before reuse. Pakistan remains a partial local candidate without independent `ACCEPT` or hosting.

## Afghanistan NSIA 1404 estimate and city-planning leads — 2026-09-27 JST

Six public official locations were selected: NSIA's 1404/2025–26 estimated-population PDF, Kabul Municipality's urban-law, historical annual-plan and city-plan catalogues, MUDH's Herat **city** master-plan handover article, and the Ministry of Finance's national budget catalogue. [The Afghanistan source audit](../../evidence/afghanistan-nsia1404-source-audit-2026-09-27.md) records the 76-table heading/column-family inventory, the three selected Table 4 latest-year population fields, the Table 76 household discrepancies and the NSIA TLS certificate-name mismatch. Feedback transfers no raw PDF, 108 observations, legal effect, polygon/code join, province plan, budget actual or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData importer, evidence, status and six selections | `58759b4c06d97ba2a2bc2ac741195dfe7ca66c01` on `codex/asia-domestic-20260926` |
| AreaData 183-source / 25-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries the full `58759b4c06d97ba2a2bc2ac741195dfe7ca66c01` as `origin_commit` |
| Kit feedback import | `9648a4ea8e3839f25d37956d106b2850b89fe12d` on `codex/asia-source-feedback-20260926`; dry-run and import accepted 183 leads, six Afghanistan records inserted, 177 existing origin histories updated, 184 records total. GitHub branch head matches remote. |
| Validation | AreaData check 151 modules/templates, 218/218 tests, Afghanistan validator zero errors/warnings, build and seven actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 183 feedback sources). |

All six Afghanistan feedback stages remain `official_location_identified`; Kit stores `not_acquired_by_kit_preflight`. Kit must independently reacquire the NSIA PDF through validated identity, review the unassessed tables and source terms, and resolve current planning authority, actual plan bodies and geography. Afghanistan is still a partial unpublished candidate without independent `ACCEPT`.

## Nepal NSO 2021 census and Kathmandu planning leads — 2026-09-27 JST

Thirty-four public official locations were selected: four NSO 2021 workbook families across seven provinces (28 original XLSX addresses), the official NSO 2023 geographical-code workbook, the Local Government Operation Act location, NPC local-planning guidance and three Kathmandu Metropolitan City PDFs. [The Nepal source audit](../../evidence/nepal-nso2021-source-audit-2026-09-27.md) separates 21 adopted count workbooks from seven acquired but semantically unassessed literacy workbooks, 2021 census records from a partly reconciled 2023 code register, and bounded city document inspection from plan approval, actual expenditure or evaluation. Feedback carries no original, observation, current boundary, code-conflict resolution, plan figure or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData importer, audit, status and 34 selected source locations | `9b0ef7ee59a81490ce7b66e0b380bced7d6a3daa` on `codex/asia-domestic-20260926`; pushed and remote head matched. |
| AreaData 217-source / 26-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that full AreaData adapter commit as `origin_commit`; bundle and this handoff are committed in the following AreaData commit. |
| Kit feedback import | `8294c493d1439267953759e8b927178f8ecab667` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 217 leads, 34 Nepal records inserted, 183 earlier origin histories updated, 218 total. Pushed and remote head matched. |
| Validation | AreaData check 152 modules/templates, 218/218 tests, Nepal validator zero errors/warnings, build and eight actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 217 feedback sources). |

All 34 Nepal feedback stages remain `official_location_identified`; Kit stores `not_acquired_by_kit_preflight`. Kit must independently reacquire and audit source bodies, code geography, legal applicability, city document contents and source terms before use. Nepal remains a partial unpublished candidate without independent `ACCEPT`.

## Sri Lanka DCS CPH 2024 source leads — 2026-09-27 JST

Thirty-five public official locations were selected: the 23 numbered DCS Population/Housing A workbooks, nine GN workbooks, administrative-code workbook, English final census report, and a municipal budget-rule Gazette location. [The Sri Lanka source audit](../../evidence/sri-lanka-cph2024-source-audit-2026-09-27.md) identifies the three adopted final DS tables and one province report table; it separately marks other acquired tables, provisional GN counts and uninspected Gazette body. No raw original, observation, code/boundary acceptance, plan/budget fact or country approval is transferred.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit and status | `b8cfe0c` on `codex/asia-domestic-20260926`; scoped source files, scripts and country evidence pushed. |
| AreaData 35 source selections and 252-source / 27-country bundle | Selections commit `0741eb439bd713d298765c74e00fb734f0b09a9d`; `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact `origin_commit`. Both adapter and selections were pushed. |
| Kit feedback import | `46f245d881a572f1c7bfc696f96b28bdea5aac5f` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 252 leads, inserted 35 Sri Lanka records and updated 217 prior origin histories, 253 Kit records total. Pushed; remote branch head matched. |
| Validation | AreaData check 153 modules/templates, 218/218 tests, Sri Lanka validator zero errors and one planning warning, build and eight actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 252 feedback sources). |

All 35 Sri Lanka feedback stages are `official_location_identified`; Kit records `not_acquired_by_kit_preflight`. Kit must independently acquire and audit originals, final/provisional census editions, statistical versus council geography, source terms and planning rules. Sri Lanka remains a partial unpublished candidate without independent `ACCEPT`.

## Bhutan NSB PHCB 2017 and planning source leads — 2026-09-27 JST

Twenty-four public official locations were selected: the NSB national PHCB 2017 report, 20 Dzongkhag reports, December 2020 geographic-code PDF, 2012 Local Government Rules PDF and PMO 13th FYP PDF location. [The Bhutan source audit](../../evidence/bhutan-phcb2017-source-audit-2026-09-27.md) identifies the adopted national Table 2.1 and district Table A2.1 population/sex cells, and keeps 641 other numbered table headings unassessed. It distinguishes the detailed-analysis 727,145 from the hotel-inclusive all-found 735,553, the 2020 code edition from unverified 2017 geography, and acquired rules from current legal force. The PMO PDF was **not** acquired because TLS peer verification failed. Feedback transfers no raw PDF, 871 observations, code/polygon join, local plan or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, evidence, status and 24 selected source locations | `5b3ca07c824cfa48d42a577aebb38cf1c471e1f0` on `codex/asia-domestic-20260926`; pushed and remote head matched. |
| AreaData 276-source / 28-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that full AreaData adapter commit as `origin_commit`; bundle and this handoff are committed in the following AreaData commit. |
| Kit feedback import | `97356cefa61fa4468de891a463f804b15f882e27` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 276 leads, 24 Bhutan records inserted, 252 earlier origin histories updated, 277 total. Pushed and remote head matched. |
| Validation | AreaData check 154 modules/templates, 218/218 tests, Bhutan validator zero errors and one planning warning, build and six actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 276 feedback sources). |

All 24 Bhutan feedback stages remain `official_location_identified`; Kit stores `not_acquired_by_kit_preflight`, including for originals acquired by AreaData. Kit must independently obtain and inspect originals, resolve the hotel-inclusive count, historical geographic codes, current rule/plan contents and terms before reuse. Bhutan remains a partial unpublished candidate without independent `ACCEPT`.

## Maldives MBS CPH 2022 and current local-council source leads — 2026-09-27 JST

Sixty-two public official locations were selected: 52 numbered MBS 2022 census XLSX, six supplementary population/employment indicator/definition XLSX, Fonadhoo Council's published plan PDF and page, and two President's Office 2026 local-governance amendment announcements. [The Maldives source audit](../../evidence/maldives-cph2022-source-audit-2026-09-27.md) limits numerical adoption to selected fields in P4/P5/H2/H7/EC3/ED16 and holds 52 other workbooks, P5 G17's blank and two spelling conflicts in EC3/ED16. The 2022 atoll rows are statistical reporting groups, not 2026 atoll councils. Fonadhoo's plan is issuer-specific; approval and full text are unverified. Feedback transfers no raw XLSX/PDF, 3,626 observations, council/polygon join, local budget/evaluation or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, evidence, status and 62 source selections | `7f800c05c281823328f5102426a6a408c4663e7e` on `codex/asia-domestic-20260926`; pushed and remote head matched before bundle export. |
| AreaData 338-source / 29-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact AreaData adapter commit as `origin_commit`; bundle and this handoff are committed in the following AreaData commit. |
| Kit feedback import | `8b256693d7a1ad4c5824be699e1326d42e18058e` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 338 leads, inserted 62 Maldives records, updated 276 prior origin histories, 339 total records. Pushed and remote head matched. |
| Validation | AreaData check 155 modules/templates, 218/218 tests, Maldives validator zero errors/warnings, build and six actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 338 feedback sources). |

All 62 Maldives feedback stages are `official_location_identified`; Kit records `not_acquired_by_kit_preflight` even when AreaData already acquired an original. Kit must independently obtain and inspect bodies, definitions, council law/jurisdiction, source geography and terms. Maldives remains a partial unpublished candidate without independent `ACCEPT`.

## Indonesia BPS SP2020 and regional-planning source leads — 2026-09-27 JST

Forty-one public official locations were selected: BPS SP2020 Table 1 country page and 34 province drill-down pages, the five-table population catalogue, Surabaya JDIH's record/PDF copy of Permendagri 86/2017, Jawa Barat's official plan catalogue/JDIH RPJMD location, and a Kemendagri code-register PDF location. [The Indonesia source audit](../../evidence/indonesia-sp2020-source-audit-2026-09-27.md) limits adoption to three Table 1 direct count columns in 549 historical BPS reporting units, preserving duplicate TOTAL rows, same-name Bogor codes and the later Papua split boundary. The code-register and RPJMD bodies were **not** acquired; neither is treated as matched current geography or verified local plan. Feedback transfers no raw HTML/PDF, 1,647 observations, code/polygon join or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, evidence, status and 41 selected source locations | `dd97f2b64bb27511cdd9c50be4c7b6c3ba9748a2` on `codex/asia-domestic-20260926`; pushed and remote head matched. |
| AreaData 379-source / 30-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that full AreaData adapter commit as `origin_commit`; bundle and this handoff are committed in the following AreaData commit. |
| Kit feedback import | `4573180f88b14280f78c9f76019955d0c9e6f959` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 379 leads, inserted 41 Indonesia records, updated 338 earlier origin histories, 380 total. Pushed and remote head matched. |
| Validation | AreaData check 156 modules/templates, 218/218 tests, Indonesia validator zero errors/warnings, build and seven actual-output cases. Kit check 52 JS/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 379 feedback sources). |

All 41 Indonesia feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, including for originals already acquired by AreaData. Kit must independently acquire and inspect source bodies, definitions, legal jurisdiction, geography and terms. Indonesia remains a partial unpublished candidate without independent `ACCEPT`.

## Philippines PSA POPCEN 2024 and local planning source leads — 2026-09-27 JST

Forty-four public official locations were selected: 22 PSA POPCEN attachments, eight PSGC original files and two PSA PSGC page leads, one PSA census release page, six DILG/Quezon City planning PDFs, four Quezon City council adoption/ordinance pages, and the Official Gazette RA7160 page. [The Philippines source audit](../../evidence/philippines-popcen-source-audit-2026-09-27.md) limits numerical adoption to direct 2024 Table A/B population, keeps Table C and historical/PGR fields unassessed, and separates 2024 Q2 codes from the later Q4 edition. Quezon City plans and fiscal records are scoped to that city; budget authorization is neither expenditure nor plan evaluation. Feedback transfers no original, 1,744 observations, boundary/code acceptance, plan figure or country approval.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit, status and 44 selected source locations | `fcf87211cad097c3501f980e28dd043d126f57ba` on `codex/asia-domestic-20260926`; pushed and remote head matched before bundle export. |
| AreaData 423-source / 31-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact AreaData adapter commit as `origin_commit`; bundle SHA-256 `5583849b07669375cea82a2fdbdd091a2859ed474a7bc6291e7067ae88a957a0`, committed as `c75953e5ed94455298838bdc97835de5bc56f0a0` and pushed. |
| Kit feedback import | `ec756368f3a558dffc4371bc1d1ff071b79c2591` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 423 leads, inserted 44 Philippines records, updated 379 earlier origin histories, 424 total Kit records. Pushed and remote head matched. |
| Validation | AreaData check 157, 218/218 tests, Philippines validator zero errors/warnings, build and ten actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 423 feedback sources). |

All 44 Philippines feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, even for originals already acquired by AreaData. Kit must independently obtain and inspect source bodies, Table C/other census topics, current codes and polygons, planning law/plan scope, fiscal facts and terms before reuse. Philippines remains a partial unpublished candidate without independent `ACCEPT`.

## Cambodia NIS 2019 census and NCDD source leads — 2026-09-27 JST

Eight public official locations were selected: the NIS final census PDF and census catalogue, NCDD district Gazetteer page and index, the Commune/Village Databook selector, and three NCDD law/plan-guide catalogue pages. [The Cambodia source audit](../../evidence/cambodia-census2019-source-audit-2026-09-27.md) separates all-person from normal-household counts, notes P-table printing and parent/child conflicts, and limits the NCDD code confirmation to Srei Santhor. Law/guide PDF bodies returned 403 and were not acquired. Feedback transfers no raw PDF/HTML, 11,301 observations, current code/polygon join, local plan, budget or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit, status and 8 selected source locations | `49aa58160f8227b7706cad39c9b7c658bd11329c` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 431-source / 32-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact adapter commit as `origin_commit`; bundle SHA-256 `be65dc34ddd8aa2bc591f20a6f84be631fa773a621db24f20583c4a77a75f738`, committed as `3059248e7db3bb068a6bc66c7a1398b76634638c` and pushed. |
| Kit feedback import | `7e46552c5092468fb4095184c7c7368bee2450a9` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 431 leads, inserted 8 Cambodia records and updated 423 prior origin histories, 432 Kit records total. Pushed. |
| Validation | AreaData check 158 modules/templates, 218/218 tests, Cambodia validator zero errors/warnings, build and 14 actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 431 feedback sources). |

All eight Cambodia feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, including for originals already acquired by AreaData. Kit must independently obtain and inspect report tables, P-table exceptions, 2019 code/boundary edition, present planning rules, local documents and terms before reuse. Cambodia remains a partial unpublished candidate without independent `ACCEPT`.

## Viet Nam GSO/UNFPA 2019 census and planning source leads — 2026-09-27 JST

Eleven public official locations were selected: the joint GSO/UNFPA census report and catalogue, the separate NSO Completed Results catalogue and original-PDF location, NSO census warehouse and press release, the planning and local-government laws, the 2025 province reform and code list, and current Hà Nội city/Kiến Hưng ward plan catalogue locations. [The Viet Nam source audit](../../evidence/vietnam-census2019-source-audit-2026-09-27.md) limits numerical adoption to Table 1's nine direct person-count columns for 2019 country and 63 historical provinces/cities. The separate district report was not acquired from NSO, other joint-report tables remain unassessed, and current 2025 codes and planning bodies are not joined to historical census row IDs. Feedback transfers no PDF, observations, code/polygon join, local plan or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit, status and 11 source selections | `618ce6e8c127be582e466e1442a7272f8e7c3e14` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 442-source / 33-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact adapter commit as `origin_commit`; SHA-256 `43b06b0b87017c01bbe3a6086cb0aa8ccb07a56e5e55f79fcabc7757c0d9200d`, committed as `05b09d265079b960ec5a25061393bbca21b73b5f` and pushed. |
| Kit feedback import | `065a07d1bf3c51dc2e2d296506801e7b0231fc28` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 442 leads, inserted 11 Viet Nam records and updated 431 prior origin histories, 443 Kit records total. Pushed. |
| Validation | AreaData check 159 JavaScript/JSON, 218/218 tests, Viet Nam validator zero errors/warnings, build and five actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 442 feedback sources). |

All 11 Viet Nam stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, including for the original acquired by AreaData. Kit must independently obtain and inspect source bodies, full numerical columns, historical/current geography, legal application, local documents and terms. Viet Nam remains a partial unpublished candidate without independent `ACCEPT`.

## Thailand NESDC 2024p GPP and planning source leads — 2026-09-27 JST

Eleven public official locations were selected: the NESDC 2024p GPP workbook and release catalogue, NESDC province/cluster guide and catalogue, NSO 2025 census portal and indexed final PDF, BORA registration catalogue, DOPA administrative-code register, Chiang Mai plan/progress catalogue and FY2025 plan PDF location, and Thai Open Government district-registration catalogue. [The Thailand source audit](../../evidence/thailand-nesdc-gpp2024-source-audit-2026-09-27.md) records 1,872 direct AreaData observations, but Kit receives only locations and warnings. It also records one withheld conflicting Kam Phaeng Phet population cell, current-price sector overlaps, incomplete historical/CVM audit, blocked NSO/BORA/open-data acquisition and unverified planning effect. Feedback transfers no raw XLSX/PDF, numeric cells, DOPA code/polygon join, local plan, budget or country acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit, status and 11 selected source locations | `a25450f3ba01197c6ba21c8c5f6381f6ca8dbd3e` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 453-source / 34-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact adapter commit as `origin_commit`; SHA-256 `2e813de7f8fbee9b7749bf22baeda9609186f016776c4aa202b574ff8cb91256`, committed as `2311a40` and pushed. |
| Kit feedback import | `74de9dc` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 453 leads, inserted 11 Thailand records and updated 442 prior origin histories, 454 Kit records total. Pushed. |
| Validation | AreaData check 160 JavaScript/JSON, 218/218 tests, Thailand validator zero errors/warnings, build and five 24-indicator actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 453 feedback sources). |

All 11 Thailand stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, even for the originals acquired by AreaData. Kit must independently acquire and inspect body, tables, definitions, local availability, administrative and plan jurisdiction, rights and reuse terms. Thailand remains a partial unpublished candidate without independent `ACCEPT`.

## Myanmar DOP 2024 census source leads — 2026-09-27 JST

Seven public official locations were selected: the DOP demographic appendix and later Union Report, the separate earlier provisional report, the 2024 main/state Excel catalogues, the 2014 census data catalogue and the CSO yearbook location for GAD administrative-unit counts. [The Myanmar source audit](../../evidence/myanmar-dop-census2024-source-audit-2026-09-27.md) distinguishes the provisional 51,316,756 from the later 51,375,327, and records the later report's 62.6% direct enumeration / 37.4% statistical estimation. AreaData adopted 15 local census indicators and 240 observations, but Kit receives **locations and reuse cautions only**. CSO 2023 administrative counts are neither 2024 official codes nor matched polygons; A-2 district/township and other 2024 subject tables remain unassessed.

| Step | Commit / verification |
|---|---|
| AreaData adapter, source audit, status and seven selections | `1d515570187eb568addc5b7e0dd868472298136c` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 460-source / 35-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that adapter commit as `origin_commit`; bundle SHA-256 `34696d77f2cf619afbfaabe1f21385cf6fcd3f4c1edfde7fbe37651550c4ff00`, committed as `6edd26e2206a363742240f544f538f7a738b869f` and pushed. |
| Kit feedback import | `946fbca36612cd8bea9b087dc8dde59c51018f71` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 460 leads, inserted seven Myanmar records, updated 453 previous origin histories, 461 Kit records total. Pushed. |
| Validation | AreaData check 161 JavaScript/JSON, 219/219 tests, Myanmar validator zero errors/warnings, build and five 15-indicator actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 460 feedback sources). |

All seven Myanmar stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, including for the originals acquired by AreaData. Kit must independently obtain source bodies, audit all relevant tables and mixed-enumeration definitions, verify official geographic codes/edition, local planning evidence and reuse terms. Myanmar remains a partial unpublished candidate without independent `ACCEPT`.

## Malaysia DOSM and Kuala Lumpur source leads — 2026-09-27 JST

Fifteen official public locations were selected: six OpenDOSM population/HIES/amenities CSVs, the MyCensus 2020 district report, MyGeoportal UPI codes, PLANMalaysia Act 172 overview/manual catalogue, and five Kuala Lumpur Gazette/plan/budget/annual-report originals. [The Malaysia source audit](../../evidence/malaysia-dosm-source-audit-2026-09-27.md) separates 2020 adjusted census population, 2024 intercensal estimates, HIES household surveys, 2025 DBKL **budget estimates** and the KL-only 2040 plan Gazette. The district HIES roster and UPI code/boundary match are unresolved. Kit receives **locations and reuse cautions only**, not AreaData's observations, acquired bodies or acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, source audit, status and 15 selections | `b11619c3679c5069d51dad0594a1d57237f5fe91` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 475-source / 36-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that adapter commit as `origin_commit`; bundle SHA-256 `380b3924f84720939f3c34df9fb40ed6fd66e162f2f98b1b402a9a0d42873867`, committed as `0cff02b60f76a8cd41ec70ca940af8a03c60cc99` and pushed. |
| Kit feedback import | `a06afbf1925ce13aa4af3d5f1a5ff406beb77cdf` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 475 leads, inserted 15 Malaysia records, updated 460 prior origin histories, 476 Kit records total. Pushed. |
| Validation | AreaData check 162 JavaScript/JSON, 219/219 tests, Malaysia validator zero errors/warnings, build and five actual-output cases. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 475 feedback sources). |

All 15 Malaysia stages remain `official_location_identified`, and the Kit records `not_acquired_by_kit_preflight`, including originals acquired by AreaData. Kit must independently obtain source bodies, audit full fields/tables, reconcile official geographic codes and dated boundaries, verify law/plan applicability and reuse terms. Malaysia remains a partial unpublished candidate without independent `ACCEPT`.

## Singapore SingStat 2026 and URA planning source leads — 2026-09-27 JST

Ten official public locations were selected: SingStat Population Trends 2026 geospatial ZIP/report, the 2020 Census planning-area age-sex CSV, URA MP2025 planning-area/region GeoJSON and Written Statement, MP2019 historical subzone GeoJSON, URA's gazette and system-overview pages, and the Planning Act. [The Singapore source audit](../../evidence/singapore-population2026-source-audit-2026-09-27.md) separates the 2026 residents on MP2025 geography from the 2020 Census on MP2019 geography, WDI total population, indicative shapes, and the national statutory plan. AreaData has 1,489 selected direct resident-count cells and 839 nil/negligible missing slots, but Kit receives **locations and reuse cautions only**. No original bytes, values, geography matching or AreaData acceptance are transferred.

| Step | Commit / verification |
|---|---|
| AreaData adapter, source audit, status and ten selections | `f52589362ddad66c16a9e3b37b6842dfeeef480b` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 485-source / 37-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact adapter commit as `origin_commit`; bundle SHA-256 `10d0ccf95d431cd81d268118442f067e88114c5d7f320d553ccd447cadb1bed0`, committed as `cc5ab47b8f64de7e5ee38e5ea71874c704a95ccc` and pushed. |
| Kit feedback import | `e14548498d1f8d9f4bd37f22a22ac39f71b18c80` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 485 leads, inserted ten Singapore records and updated 475 previous origin histories, 486 Kit records total. Pushed. |
| Validation | AreaData check 163 JavaScript/JSON, 219/219 tests, Singapore validator zero errors/warnings, build and five actual-output cases × six source cells; 48/55 national area comparison values. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 485 feedback sources). |

All ten Singapore feedback stages remain `official_location_identified`, and Kit records `not_acquired_by_kit_preflight` even for originals AreaData acquired. Kit must independently obtain and inspect full bodies/tables, the 2019-to-2025 geographic relation, 2026 subzone code/shape, operative planning guidance and reuse terms. Singapore remains a partial unpublished candidate without independent `ACCEPT`.

## Timor-Leste INETL 2022 and local planning source leads — 2026-09-27 JST

Eight public official locations were selected: the INETL 2022 Census Main Report, Law 19/2023 on territorial administration, the 2023 suco recognition Gazette, municipal and Ataúro plan procedures, Díli's 2026–2030 plan and 2026 annual action plan, and Ataúro's 2026–2030 published draft. [The Timor-Leste source audit](../../evidence/timor-leste-phc2022-source-audit-2026-09-27.md) separates the 2022 census's 14 first-level reporting rows from 2023 legal types and the 2017 13-shape reference layer. AreaData adopted selected columns from 3 of 33 numbered census tables, 135 direct cells and 30 derived ratios, while image-only lower tables, conflicting sex counts and suppressed age cells remain unresolved. Kit receives **locations and reuse cautions only**, no PDF originals, values, boundary matching or AreaData acceptance.

| Step | Commit / verification |
|---|---|
| AreaData adapter, audit, status and eight selections | `3e0ab610903a40ded10a47802ab1a38497660649` on `codex/asia-domestic-20260926`; pushed. |
| AreaData 493-source / 38-country bundle | `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact adapter commit as `origin_commit`; SHA-256 `91f71334446381a9843d2d0bb5ef541c61979d9e4bb3afb9d7068842a8f4f314`, committed as `8140f8a6dc8209602c17974d2978f538cfd78581` and pushed. |
| Kit feedback import | `5059d90206e2d2eea17ca37265b8b248416c283b` on `codex/asia-source-feedback-20260926`; dry-run/import accepted 493 leads, inserted eight Timor-Leste records and updated 485 prior origin histories, 494 Kit records total. Pushed. |
| Validation | AreaData check 164 JavaScript/JSON, 219/219 tests, Timor-Leste validator 0 errors/warnings, build, and five 11-indicator actual-output cases with 154 national comparison indicator cells. Kit check 52 JavaScript/templates plus 67 Markdown, 173/173 tests and readiness (`ready: true`, 493 feedback sources). |

All eight Timor-Leste feedback stages remain `official_location_identified`; Kit records `not_acquired_by_kit_preflight`, even for originals acquired by AreaData. Kit must independently acquire the report and laws, review all numbered and image-only tables, reconcile 2022/current administrative names/codes/shapes, verify plan approval/financial status and reuse terms. Timor-Leste remains a partial unpublished candidate without independent `ACCEPT`.

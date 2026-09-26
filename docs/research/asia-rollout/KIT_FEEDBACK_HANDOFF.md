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

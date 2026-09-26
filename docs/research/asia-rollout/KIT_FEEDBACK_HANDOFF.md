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

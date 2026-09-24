# Burkina Faso branch in AreaData world site — 2026-09-25

This release adds Burkina Faso's historical 2019 Census geography to the existing AreaData world site. It is an integrated country branch, not a separate website. The original world root and all 48 existing country shards are preserved; the BFA graft changes the root index and common app, and adds only BFA country/boundary shards and area-specific Word reports. The publication script refuses removed files and verifies existing remote bytes before replacement.

## Data and screen checks

- 410 territory identities: national, 13 historical regions, 45 provinces and 351 communes. The administrative membership is from INSD RGPH 2019; 2017 provider geometry is a reference map, not a legal boundary certification or a 2025 administrative-unit crosswalk.
- 61 added indicators and 15,882 added observations in the integrated canonical dataset. The published BFA shard includes 15,902 observations including 20 pre-existing world observations for BFA. No old root observation is removed.
- Four national planning/legal reference records, displayed on the planning page for a selected BFA lower area as national references. They are not attributed as Centre's own plans.
- 410 selected-area Word reports. All source files are SHA-256 checked against the existing manifest before staging. The national, Centre and final commune report also matched their local HTTP downloads.
- Local browser checks: BFA national shows 2019 Census population and 13-region comparison; Centre shows 3,030,384 people and the Kadiogo internal comparison; the thematic page retains Centre and shows the 2019 population; the planning page retains Centre, lists four national references separately, and links Centre's Word file. The common `npm run check` and `npm test` pass, 213 tests.
- The public root edition used as the base has SHA-256 `48eaebcb2c3544e19c894a154a4213cf5e675724ef39f71e186d1a5f2a774b57`. The staged root has SHA-256 `d9f3f0118fb0a81552b8b242b567966ef3785f59b047aa94351312ecc996a76f`.

## Limits kept visible

This is a source-limited integrated branch, not a declaration that the country edition passed all 42 acceptance scenarios. The separate BFA ledger still records 0 full passes, 39 uncompleted and 3 outside scope, and no independent audit. The 2019 statistical volume contains 581 table IDs; only part of it has undergone printed-page and semantic review. The source-conflicting INSD fertility table is withheld. Current administrative/legal correspondence, local plans and budgets remain unresolved. These omissions must not be converted to zero, inferred from lower areas, or described as a completed planning system.

## Reproduction

1. Build the BFA country project from the archived receipts and scripts under `scripts/country-burkina-faso/`.
2. Run `integrate-world.mjs` against the canonical AreaData world dataset and the BFA country dataset to create a new integrated candidate.
3. Run `prepare-areadata-release.py` with the deployed site's exact base, the integrated candidate, the BFA country project and a new output directory. The script checks Word hashes, preserves old root observations and emits a scoped release site and evidence JSON.
4. Inspect the exact file diff, perform browser checks, and deploy only changed/added files with remote preflight backups, FTPS read-back and public HTTPS hash checks. Keep the accepted baseline and the generated candidate; do not replace the former with the latter.

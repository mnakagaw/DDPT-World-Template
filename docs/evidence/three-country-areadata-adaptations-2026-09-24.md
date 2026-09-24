# AreaData country adaptations — local verification, 2026-09-24

## Kit source-location feedback

The seven selected URLs below are location leads, not an independent AreaData source audit. Bangladesh and Laos were copied from their Kit country projects, so their presence here is a return of reusable metadata, not a claim of new discovery. Uganda's leads came through the Uganda-LGDP adaptation. `config/kit-source-feedback-selections.json` selects these exact dataset source IDs; `evidence/KIT_SOURCE_FEEDBACK.json` is the export. All seven have the conservative stage `official_location_identified`. Source terms and current content must be rechecked before any Kit country adoption.

The same selection now also includes eight **Burkina Faso** source leads found and acquired in a separate local country adaptation. Its exact source list, adopted coverage, gaps, and verification boundary are in [Burkina Faso adaptation evidence](burkina-faso-areadata-adaptation-2026-09-24.md). The conservative feedback stage also applies to all eight Burkina Faso leads; this does not upgrade the earlier three countries' audit status.

| Country | Dataset source ID | Source location |
| --- | --- | --- |
| Bangladesh | `bgd-bbs-preliminary-2022` | https://bbs.gov.bd/pages/static-pages/6922e073933eb65569e27220 |
| Bangladesh | `bgd-bbs-community-series-2022` | https://bbs.gov.bd/pages/static-pages/6922e073933eb65569e27220 |
| Lao PDR | `lao-phc-2015` | https://lao.unfpa.org/en/publications/results-population-and-housing-census-2015-english-version |
| Lao PDR | `lao-cod-ps` | https://data.humdata.org/dataset/cod-ps-lao |
| Uganda | `uga-lgdp-census-normalized` | https://statistics.ubos.org/nphc/report?cat=resources |
| Uganda | `uga-plan-lgdp_guidelines_2020` | https://npa.go.ug/wp-content/uploads/2026/07/LOCAL-GOVERNMENT-DEVELOPMENT-PLANNING-GUIDELINES-2020.pdf?x56883 |
| Uganda | `uga-plan-npa_plan_catalog` | https://npa.go.ug/local-government-development-plans/ |

The earlier Lao 2015 feedback URL was an SDG indicator page, not the census report. The corrected UNFPA/LSB report listing supersedes that feedback entry; the old record is retained only as correction history and must not be offered as a source lead.

These are separate country projects under `generated/`, based on already acquired country evidence. The source projects were read but not modified. This is an AreaData integration and local functional check, not an independent country-source audit or a public release.

| Country | Project | Principal adopted series | Areas | Indicators | Observations | Documents | Site JSON |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Bangladesh | `generated/bangladesh-areadata-20260924-v2` | BBS Population and Housing Census 2022, plus separately labelled international series | 580 | 253 | 108,076 | 70 | 28 MB |
| Lao PDR | `generated/laos-areadata-20260924` | 2015 detailed census and separately labelled 2024 population estimates | 167 | 42 | 1,896 | 10 | 8 MB |
| Uganda | `generated/uganda-areadata-20260924` | UBOS NPHC 2024 national, region, subregion, district/city and lower-area records | 2,375 | 68 | 161,500 | 27 | 82 MB |

Each project contains canonical `data/dashboard.json`, copied raw source evidence, `evidence/IMPORT_ORIGIN.json`, `evidence/validation.json`, generated `site/` and a `HANDOFF.md`. The Bangladesh and Laos adapters came from the separate Census Dashboard Kit projects. The Uganda adapter used Uganda-LGDP's normalized NPHC publication and verified geometry joins. The source hashes and data lineage are recorded in each project's import manifest. These project directories are excluded from the template Git repository; do not treat a code push as publication of the datasets.

The three country validators reported zero errors. At initial adaptation, warnings were 11 Bangladesh source terms, 14 Lao aggregation-rule availability, and 18 Uganda source terms. After the source-evidence warning was added, current counts are 11, 20 and 29 respectively: six Lao and eleven Uganda `ready` sources have no local raw evidence. The initial `npm run check` passed 118 syntax/JSON checks and `npm test` passed 207 tests; later source-audit changes have their own test record. Local headless Chrome loaded all three territorial pages without JavaScript errors. Explicitly selecting an ancestor after a lower area reset the analysis scope for Barishal, Vientiane Capital and Abim. Both thematic and planning links retained the selected ancestor. District/province diagnostic exports contained 440, 400 and 1,156 data rows respectively; planning evidence exports contained 40, 40 and 68 rows. Each export included its selected area. Exact browser observations are in each project's `evidence/qa-browser.json`, `qa-interaction.json` and `qa-downloads.json`.

The three generated sites are local review builds. They have **not** passed an independent AreaData source/acceptance audit, were **not** uploaded to FTP, and have **not** been checked on a public URL. Before publishing, review source redistribution terms, Uganda's unmatched lower-area shapes and national-versus-district population scope, Lao 2015/2024/2025 vintage labels, and large browser payloads. The 2025 Lao census listing must not be presented as published local values until actual results and geography can be verified. No unsupported district or province total was derived from incomplete lower-area data.

To rebuild after a dataset change, run `node scripts/validate-country.mjs --project <project>` then `node scripts/build-country.mjs --project <project>` from the repository root. If validation fails, the last successful generated site stays in place. For public release, first obtain an independent AreaData audit of these exact data editions and specify each country's hosting path; then verify deployed assets and live interaction/output, recording the code commit and dataset hashes.

# Philippines AreaData partial candidate — 29 September 2026

## Result and identity

- Local project: `generated/philippines-areadata-20260929` (ignored/private).
- Producer: `scripts/adapt-philippines-psa-regions.mjs`. Rebuild with `node scripts/build-country.mjs --project generated/philippines-areadata-20260929`.
- Scope: one country, all 18 PSA PSGC regions dated 31 July 2025, and **one** City of Iloilo planning case. The 2024 POPCEN counts are official published figures; WDI national series remain separate.
- This is **not a completed Philippine local-planning edition**. Province, HUC, city, municipality and barangay coverage, dated current polygons, source-table audit, plan/finance/evaluation content, browser acceptance and independent audit remain open. No Hosting/Public release is authorized by this candidate.

## Directly checked official sources

| Source | Direct observation in this candidate | Acquisition limit |
| --- | --- | --- |
| [PSA PSGC regions](https://psa.gov.ph/classification/psgc/regions) | 18 ten-digit region codes and 18 2024 POPCEN population values; captured as a rendered-text excerpt, normalized rows, and hashes in the local project's `raw/` | Origin HTML and official XLSX were blocked by the PSA site challenge; 31 July 2025 is the displayed PSGC edition, not a verified 30 June 2026 full register |
| [PSA official 2024 POPCEN release](https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president) | 112,729,484 national total as of 1 July 2024; includes persons in Philippine missions abroad | Table A/B XLSX linked but direct local retrieval blocked; no full row/field inventory |
| [PSA domestic-population explanation](https://psa.gov.ph/statistics/population-and-housing/node/1684081344) | 112,727,776 in Philippine territory plus 1,708 in missions abroad. The 18 recorded regions sum exactly to 112,727,776. | Indexed official excerpt captured; direct origin body not retained |
| [PSA City of Iloilo PSGC record](https://psa.gov.ph/classification/psgc/barangays/0631000000) | PSGC `0631000000`, correspondence `063022000`, 2024 POPCEN population 473,728 | One city case only; Region VI lower-area coverage is explicitly incomplete |
| [Official Gazette RA 7160](https://officialgazette.gov.ph/1991/10/10/republic-act-no-7160/) | Sections 106 and 109 locate comprehensive local plans and development councils at provincial, city, municipal and barangay levels | Current amendment and full legal-effect audit pending; regions are exploratory statistical areas, not automatically local planning authorities |
| [DILG CDP guide](https://region12.dilg.gov.ph/sites/default/files/reportsresources/knowledge-materials/961-illustrative-guide-v4b.pdf) | Official guidance location for city/municipal CDP work | Local direct fetch returned 404; original edition/body not acquired |
| [Iloilo City CDP 2023–2028](https://iloilocity.gov.ph/main/wp-content/uploads/2023/05/CDP2023-2028_4-13_Final-Document.pdf) | Official city PDF location/title; a link-only document is attached to the one matched city | Direct fetch returned 403; no cost, approval, implementation or evaluation content is adopted |
| [Lipa City transparency page](https://lipa.gov.ph/transparency/) | Location for a city CDP, local investment plan, annual budgets and spending reports | Direct fetch returned 406; not matched to the selected Iloilo city case or adopted as city data |
| [PSA 2025 Statistical Yearbook](https://psa.gov.ph/philippine-statistical-yearbook) | Official chapter table index includes 2024 population by region/province/city and thematic regional tables | Direct CSV retrieval returned 403; each table's geography and field meanings remain unreviewed |
| [PSA 2023 poverty release](https://psa.gov.ph/sites/default/files/phdsd/Press%20Release_2023%20Full%20Year%20Official%20Poverty%20Statistics.pdf) | Official three-page release includes 18-region family poverty incidence and NIR adjustment notes | Direct PDF retrieval returned 403. Table footnotes show the 2023 Region IX/BARMM arrangement differs from the 2025 PSGC population register; values were not attached to the current region comparison |

PSA web pages state CC BY 4.0 unless otherwise stated. The captured rendered excerpts are kept in the private local project; the original files and any exception-specific terms have not been fully checked. The prior Census Dashboard Kit Philippines prototype was read as a **warning source only**: its 17-region geography, five relabelled NDHS fields and planning evidence were rejected in its 17 September 2026 independent review. No observations or polygons were copied from it.

## Meaning and geography

- The domestic POPCEN series uses one definition across national, region and Iloilo city: people enumerated within Philippine territory. Its national value is 112,727,776. A separate national-only indicator holds 112,729,484 including missions abroad. Neither series is merged with WDI midyear estimates.
- The generated 2020 geoBoundaries ADM1 shapes do not describe the displayed 18-region register after the 2024 Negros Island Region creation or later changes. They remain in private raw references; the adopted dataset has zero polygon joins. See [PSA NIR update](https://psa.gov.ph/content/second-quarter-2024-psgc-updates-creation-negros-island-region-and-correction-names-two).
- Country internal comparison registers all 18 regions. Region VI has only one registered city case; `analysis.incomplete_child_cover_ids` suppresses a false one-city comparison for the whole region. Iloilo city is a local planning case, not evidence of national municipal coverage.
- Both official population counts and 2024 WDI national population may appear in the data, with separate indicator IDs, source URLs, definitions and missing local WDI cells. No national value is copied into a local observation.

## Evidence and acceptance

The adapter validates the 18 rows against the saved PSA rendered excerpt and requires the domestic + abroad reconciliation. `node scripts/validate-country.mjs` and `node scripts/build-country.mjs` succeeded; the validator leaves two explicit source-terms warnings for the linked Gazette/CDP sources. `scripts/verify-philippines-outputs.mjs` saves and reads generator-produced diagnostic CSV/HTML, planning HTML and evidence CSV for the national area, Region VI and Iloilo city. It verifies the selected population, 18 national members, zero Region VI members and Iloilo plan link. This does not verify browser downloads or printing.

The 42-scenario country acceptance is **0 complete**. The app browser connection failed before a page could be inspected, so screen selection, URL restore, downloads, responsive layout and print remain untested. Independent country audit is pending. The candidate must remain local/private; do not infer an `ACCEPT` verdict from schema validation or previous Kit deployment.

The local HTTP preview returned 200 for the five page entry points, dataset JSON and app module; the served JSON had 20 territories, 333 observations and zero polygons. This verifies file delivery only, not interaction or rendering. The preview server was stopped.

## Source-feedback custody

- AreaData producer selection and exporter commit: `817825fdcc155c9b313120a7b0ed1b8f52ff58e9`; the Kit-supported poverty-table role was corrected in `0a5bb07377593d76836f9dc2f934e6e1f4e6b539`.
- AreaData feedback bundle after that correction: `evidence/KIT_SOURCE_FEEDBACK.json`, committed at `c8abee6` on `codex/philippines-areadata-20260929`. It contains 11 PHL official-location leads, all at `official_location_identified`, alongside 211 unchanged earlier leads. The PHL-only import bundle is retained in the ignored local project's `evidence/`.
- Census Dashboard Kit import: 11 inserted into `config/areadata-source-feedback.json`, commit `f429629` on `codex/philippines-source-feedback-20260929`. Repeated dry-run found 11 unchanged; Kit `npm run check`, `npm test` (173/173), and `npm run verify:kit` passed. The import transfers discovery locations only, never observations, assets, or a country acceptance verdict.

## Next concrete steps

1. Obtain PSA 2024 POPCEN Table B and the 30 June 2026 PSGC release through normal authorized access, preserve original hashes, inventory every sheet/table/field, and reconcile all province, HUC, city and municipality codes plus changes.
2. Acquire a dated current boundary edition and compare NIR, BARMM/Sulu and other changes before polygon joins.
3. Acquire actual city/municipal plan, annual investment program, adopted budget, expenditure and evaluation originals for a matched representative authority. Keep amounts and official approval separate.
4. Complete six-theme source review, full catalogue disposition, 42 applicable scenarios and separate independent audit. Publish only after `ACCEPT` and a scoped release instruction.

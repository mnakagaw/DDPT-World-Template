# Singapore AreaData handoff — 2026-09-27 JST

**Status: SingStat June 2026/URA MP2025 partial candidate; independent `ACCEPT` pending; unpublished.** The Asia ledger is 0 complete, 35 partial, 1 research-only and 14 not started. Next unstarted priority by CSV order: Timor-Leste. Candidate: `generated/singapore-areadata-20260927` (ignored). No SGP-specific Hosting/Public destination is assigned.

## Evidence and decisions

- [SingStat Population Trends 2026](https://www.singstat.gov.sg/publication-resources/population-trends-2026) provided three XLSX workbooks and 7 sheets under a geospatial ZIP, plus a 54-page report. All 456,288 data rows/value cells were mechanically classified as 244,240 numeric and 212,048 nil/negligible `-`; footnotes were recorded. Six selected direct resident-count indicators produce **388 reporting territories, 1,489 observed cells and 839 explicit missing**. The population measure is citizens/permanent residents with local addresses, excluding those continuously away 12+ months; it differs from WDI national total population. National direct resident population is 4,231,520; Tampines is 296,060. Independent rounding to tens explains small parent/sex-sum differences; no child sum replaces a parent.
- 55 SingStat 2026 Planning Area names match all 55 [URA Master Plan 2025 Planning Area](https://data.gov.sg/datasets/d_2cc750190544007400b2cfd5d7f53209/view) names/codes/polygons. Those indicative polygons are for display. The 332 Subzones retain their exact source area/name pairs but have no verified MP2025 subzone codes/polygons. The 5 MP2025 Region polygons are raw evidence only, with no invented 2026 regional population. Initial 2016 provider polygons were removed.
- Acquired [2020 Census age-sex CSV](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view) (388 rows, 60 value columns) and [MP2019 subzone polygons](https://data.gov.sg/datasets/d_8594ae9ff96d0c708bc2af633048edfb/view) belong to a different edition. No value is carried into MP2025 geography or labelled as a 2020–2026 change. The other ZIP dimensions and Census detailed releases remain priority unassessed; old indexed report PDF URLs returned 404.
- [URA MP2025 Written Statement](https://www.ura.gov.sg/land-planning/master-plan/) is acquired, and [URA's gazette notice](https://www.ura.gov.sg/guidelines/circulars/ppg25-12/) confirms national statutory effect from 1 December 2025. It is displayed only for Singapore nationwide. Planning Areas/Subzones are not independent municipalities; location-specific plans, budgets, actual expenditure, implementation and official evaluation are not acquired.

[Detailed source audit](../../evidence/singapore-population2026-source-audit-2026-09-27.md), [start sheet](../../evidence/singapore-country-start-2026-09-27.md), [Task Contract](../../evidence/singapore-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/singapore-country-lesson-audit-2026-09-27.md), and tracked [source manifest](../../config/singapore-population2026-source-manifest.json) define the boundary. The ignored candidate holds raw originals, full-sheet audit JSON, real output verification and built site.

## Reproduce and inspect

Create a **new** candidate directory, then download the manifest's 7 official originals to its `raw_path` locations. data.gov.sg GeoJSON/CSV downloads use its dataset API; the manifest records stable public catalogue URLs, not short-lived signed blob URLs. Verify byte length/SHA-256. On source change, inspect the edition before updating the manifest/import contract. Python needs `openpyxl` and `pypdf`. Do not replace a prior working candidate on acquisition/import/build failure.

```powershell
node scripts/create-country.mjs --country Singapore --out generated/singapore-replay-new
# Download each manifest source to generated/singapore-replay-new/<raw_path>.
python scripts/import-singapore-population2026.py --project generated/singapore-replay-new
node scripts/validate-country.mjs --project generated/singapore-replay-new
node scripts/build-country.mjs --project generated/singapore-replay-new
python scripts/verify-singapore-population2026-output.py --project generated/singapore-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `286785d5f0b0368093beefebbdb35f4e148fbd3df1c7ed29efb1587e403aee26`; validator **0 errors/warnings**, build succeeded, five source/output cases × six source cells plus five output types checked, 55 national planning-area comparison rows, `npm run check` **163 JavaScript/JSON**, `npm test` **219/219**. In the local browser, national comparison showed 48/55 resident values and 7 missing; Tampines→Tampines East→Tampines whole-area selection reset main value to 296,060 and URL; Changi Bay stayed missing; the national plan did not appear as a Changi Bay-specific document; focusing Tampines in the theme map did not change the Singapore analysis target. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Singapore edition

1. Semantically inspect all unselected single-age, age-group, dwelling/floor-area, male/female and 2020 Census detailed tables. Verify denominator, nil/negligible and rounding treatment individually.
2. Obtain MP2025 official Subzone codes/polygons and a time-aware MP2019→MP2025 crosswalk before mapping all 332 subzones or calculating local historical change.
3. Verify the operative Planning Act/URA guidance and obtain location-linked plan, budget estimate, actual expenditure, implementation and evaluation bodies. Keep the national MP2025 from becoming 55 artificial local plans.
4. Confirm reuse terms, complete applicable 42 scenarios and visual/print/mobile/performance/language/local-user checks, then obtain independent `ACCEPT`. Set SGP-specific Hosting/Public scope and verify deployed JSON plus rendered URLs only after acceptance.

Kit feedback transfers **official public locations and reuse cautions only** at `official_location_identified`, no ZIP/CSV/PDF/GeoJSON, observations, code join or country acceptance. **Local:** partial candidate. **GitHub:** code, audit and source leads committed and pushed. **Hosting:** none. **Public:** none. The two-repository exchange is also recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md).

GitHub handoff: AreaData adapter/audit `f52589362ddad66c16a9e3b37b6842dfeeef480b`, 485-source feedback bundle `cc5ab47b8f64de7e5ee38e5ea71874c704a95ccc` (SHA-256 `10d0ccf95d431cd81d268118442f067e88114c5d7f320d553ccd447cadb1bed0`), Kit import `e14548498d1f8d9f4bd37f22a22ac39f71b18c80`. All are pushed on their respective `codex/asia-*` branches. This final AreaData handoff record follows the adapter-bound bundle and does not change its `origin_commit`.

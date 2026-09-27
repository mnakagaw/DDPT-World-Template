# Uzbekistan AreaData handoff — 2026-09-27 JST

**Status: SIAT 2026 domestic permanent-population estimate plus preliminary census partial candidate; independent `ACCEPT` pending; unpublished.** Asia ledger: 0 complete, 38 partial, 1 research-only, 11 not started. Next unstarted priority by CSV order: Kazakhstan. Candidate: `generated/uzbekistan-areadata-20260927` (ignored). UZB-specific Hosting/Public destination is not assigned.

## Evidence and decisions

- Five [NSC SIAT annual permanent-population series](https://siat.stat.uz/data/246/?lang=en) give 2026-01-01 direct values for the nation, 14 first-level units and 206 districts/cities: five indicators, 1,105 cells. SIAT supplies COATO codes. The [NSC 2026-01-27 release](https://stat.uz/img/news/demografiya-press-reliz-en_p24116.pdf) independently matches nation and 14 first-level total rows. Prior SIAT years are inventoried but not adopted for time comparison.
- The [2026 preliminary census report](https://aholi.stat.uz/en/64-news-eng/6232-preliminary-results-of-population-and-agriculture-census-conducted-in-the-republic-of-uzbekistan-in-2026) printed pp.4–5 supplies five distinct 2026-01-15 population measures for nation and 14 first-level units: 75 direct cells. Its 25 other tabulated sections and an [11-sheet agriculture workbook](https://aholi.stat.uz/en/64-news-eng/6260-preliminary-results-of-the-2026-population-census) remain `priority_unassessed`. Census 39,047,321 people and SIAT 38,236.7 thousand people are not labelled growth or joined with WDI midyear estimates.
- The [ASDR regional strategy task](https://asdr.gov.uz/en/tasks-set-for-the-development-of-regional-strategies/) locates 2030 preparation for all 14 first-level units, not their approved plans. [PF-21](https://test.lex.uz/docs/8050769) is national; the [MOF local-budget table](https://gov.uz/en/imv/sections/view/190028) has ambiguous triplet periods, so its 90 numeric cells are not adopted or called actual expenditure.
- The 2017 geoBoundaries initial layer was removed; the 2026 official code/polygon correspondence is unverified. Top selectors and full member tables remain usable without polygons. Tashkent region `1727` and Tashkent city `1726` remain distinct.

[Detailed source audit](../../evidence/uzbekistan-siat-census2026-source-audit-2026-09-27.md), [start sheet](../../evidence/uzbekistan-country-start-2026-09-27.md), [Task Contract](../../evidence/uzbekistan-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/uzbekistan-country-lesson-audit-2026-09-27.md), [table/sheet inventory](../../evidence/uzbekistan-siat-census2026-table-audit-2026-09-27.json), and [source manifest](../../../config/uzbekistan-2026-source-manifest.json) define the boundary. The ignored candidate retains raw originals, generated audit, exports and built site.

## Reproduce and inspect

Create a **new** candidate directory and download the manifest's nine official originals into each `raw_path`; verify byte length/SHA-256. Any source edition/hash change requires review before import. Python requires openpyxl and Poppler `pdftotext`. A failed update must leave the last working candidate intact.

```powershell
node scripts/create-country.mjs --country Uzbekistan --out generated/uzbekistan-replay-new
# Download each manifest source to generated/uzbekistan-replay-new/<raw_path>.
python scripts/import-uzbekistan-2026.py --project generated/uzbekistan-replay-new
node scripts/validate-country.mjs --project generated/uzbekistan-replay-new
node scripts/build-country.mjs --project generated/uzbekistan-replay-new
node scripts/export-uzbekistan-2026-cases.mjs generated/uzbekistan-replay-new
python scripts/verify-uzbekistan-2026-output.py --project generated/uzbekistan-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `f2a65f3fc267661a8634ca5079a5e70eb8c2220875e2116fe4cd2442b28eff2f`; validator **0 errors/warnings**, build succeeded. Nine independently transcribed source cases check 180 diagnostic/evidence value or missing cells and nine original hashes. National comparison 14/14, Karakalpakstan 17/17, Tashkent city 12/12. Browser checked national→Karakalpakstan→Nukus→same parent, Tashkent region/city separation, Yangikhayot→same city, distinct SIAT/census cards and plan/budget location states. `npm run check` checked **166** JavaScript/JSON files and `npm test` passed **219/219**. These producer checks do not equal all 42 scenarios or independent acceptance.

## Remaining before a complete Uzbekistan edition

1. Audit all numeric columns and definitions in 25 other preliminary report tables, the 11 agriculture sheets, SIAT prior-year administrative changes and the eventual final census release; look for genuinely local census tables.
2. Acquire a dated official COATO code registry and compatible first/second-level polygons, verify name/type/code match for census rows, 2026 geography, legal units, and reuse terms.
3. Acquire each regional plan body, operative legal procedure, approval, district/city authority and applicable forms; resolve MOF table periods and separate budget estimates, actual spending, implementation and official evaluation.
4. Confirm source redistribution rights, local-user and full 42-scenario visual/print/mobile/output checks, then independent `ACCEPT`. Assign UZB-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback transfers **official public locations and reuse cautions only** at `official_location_identified`; no originals, observations, code/polygon join or country acceptance. **Local:** partial candidate. **GitHub:** adapter, audit and source leads committed and pushed. **Hosting:** none. **Public:** none. The two-repository commit exchange is recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md).

GitHub handoff: AreaData adapter/audit `fec3b12132eac791a2b68822dd95a0e6cc7a40d5`, 513-source feedback bundle `15a4f61b61cf9761339873c3cf1a6dc3dd01c086` (SHA-256 `fa07cb5a6fcd5932fd0c8de57ae1134e6e7d62e969541ab4de60c1bfc5fb1130`), Kit import `0f32eaf8f0f67b41d6bc82060ec4c089d2f12ba2`. All were pushed on their respective `codex/asia-*` branches. The final AreaData handoff record follows the adapter-bound bundle and does not change its `origin_commit`.

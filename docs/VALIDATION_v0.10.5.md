# AreaData v0.10.5 validation record

Date: 2026-09-23
Scope: Americas regional map scale, incomplete Census presentation, and full-cover UN population context at country and higher levels.
Code commit: `0c3f98a` (`fix: show complete UN population across Americas regions`).
Data edition: `2026-09-23T12:55:27.858Z`; `data/dashboard.json` SHA-256 `3d493cd7fb691954a39d99d26174125527eebaa78e83c864195e93921d0f0488`.
Environment: Windows, Node.js, local static server, CORESERVER FTPS, public `https://areadata.net/`.

## Adopted population evidence and behavior

- The UN WPP 2024 Rev.1 workbook was checked at SHA-256 `98e34d9b65b53858cd08a57a566e45050b08093ad85ba5714fe6fbd78055ae6d`. The national series has exact source rows for 55 of 57 Americas country/area IDs for 2023–2026. BVT and SGS have no national WPP rows and remain missing, not zero.
- The same workbook contains South America subregion rows (WPP location code 931; SDMX 005). These are separate direct source observations; the 2026 value is 440,484,432 people. The country subtotal is not silently substituted for this published regional value.
- Northern America and Central America + Caribbean are sums of their own completely covered, non-overlapping WPP country/area rows for the same year. The 2026 values are 389,628,823 and 231,651,130 people respectively. The Americas 2026 value, 1,061,764,385, is an **AreaData calculation** across these three fully covered regions, not a direct UN publication for this custom navigation partition.
- The national UN series is an estimate in 2023 and a medium-variant projection in 2024–2026. It remains distinct from mixed-year national Census observations and from subnational Census data. No national figure is propagated to a province or municipality.
- The Central America + Caribbean Census series has observations for 7 of 36 country/area entries. Its 43,883,591-person covered subtotal is labeled as partial; 29 uncollected entries are disclosed. This is not presented as the region's total.
- The map longitude wrap fix removes the nearly 360-degree extent that made the Central America + Caribbean shape tiny. It changes display geometry only, not boundaries or statistical membership.

## Checks

- `npm run check`: PASS, 113 JavaScript modules and JSON templates.
- `npm test`: PASS, 200/200 tests, including full-cover aggregation independent of incomplete Census, direct South America WPP evidence, distinct comparison and aggregation membership, and the map extent regression.
- `node scripts/validate-country.mjs --project .work/areadata-americas-v0.10.5-map-coverage`: PASS, no errors or warnings.
- `node scripts/validate-territorial-summaries.mjs --project .work/areadata-americas-v0.10.5-map-coverage`: PASS, 57 territories, 756 latest-indicator checks, 1,484 explicit-observation checks, 3 zero-value checks, no errors. Receipt: `.work/areadata-americas-v0.10.5-map-coverage/evidence/TERRITORIAL_SUMMARY_AUDIT.json`.
- Local browser: Central America + Caribbean and Americas maps fill their intended location panels; regional UN totals, source/period and partial Census label appear. Jamaica shows its country UN WPP observation. Domestic regions do not receive national UN values.
- Public browser, Japanese UI: Central America + Caribbean map, 231,651,130 UN total and 43,883,591 Census partial subtotal with 29 uncovered entries confirmed; Americas map and 1,061,764,385 UN total confirmed.

## Publication

- GitHub `main`: commit `0c3f98a` pushed.
- FTPS: 122 changed files from the 126-file generated site were deployed. All predecessors were hash-checked and backed up. The first connection ended after 15 verified files; those 15 were rechecked and the remaining files were uploaded with per-file reconnect/retry and final remote hash verification. Receipt: `.work/ftp-deployment-areadata-v0.10.5-map-coverage-2026-09-23.json`.
- Public HTTPS: all 125 web-accessible generated files matched the local candidate byte-for-byte; `.htaccess` is excluded from HTTP verification. Receipt: `.work/public-verification-areadata-v0.10.5-map-coverage-2026-09-23.json`.

This release verifies the scoped population and UI changes. It does not certify the separate, still-pending independent content audit for every Americas country edition or claim complete Census coverage of the continent.

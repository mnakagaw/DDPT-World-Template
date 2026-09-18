# AreaData Americas v0.10.1 remediation record

Date: 2026-09-18.

## Why v0.10.0 ACCEPT was withdrawn

The USA territorial page used the literal `latest-available` value in its basic-fact lookup. The top population, electricity and internet facts were missing while the detailed cards contained 2025/2024 observations. The former audit did not catch this cross-section mismatch.

A second completion review found that the seven Census adapters currently adopt Census population and domestic hierarchy, but do not yet contain a semantic disposition for every acquired table and numeric field. The other 50 Americas registry entries remain source preflight records. Therefore v0.10.0 is a regional exploration gateway, not 57 completed country editions.

## Remediation implemented

- Territorial `latest-available` now resolves per territory and indicator.
- Basic facts, detail cards and evidence exports use the same `territorialIndicatorState` resolver.
- Explicit-year selection preserves an exact missing row instead of falling back silently.
- Numeric zero remains observed.
- `validate-territorial-summaries.mjs` checks the newest observed value, actual period, source ID and status plus every explicit observed period.
- `COUNTRY_COMPLETION_MATRIX.json` has 57 records and reports **57 complete** after every required source domain and theme received a terminal, evidence-backed disposition. This does not mean that every country has local Census tables; unavailable, restricted, failed-with-evidence and not-adopted material remains explicit.
- The Americas publication gate requires 57/57 complete matrix records and a new independent ACCEPT.
- Shared-source numeric fields, including the 120 UN WPP `MULTI` fields, now need a terminal disposition before the publication gate can pass.
- Guatemala's 22 department and 340 municipality reference polygons are joined by exact SEGEPLAN codes, and the comparison notes describe the same joined state.
- Belize's three derived household-service ratios retain the Appendix B table, printed page, component counts, numerator and denominator. The screen shows the exact source-table locator beside the official source.

## Current checks

- `npm run check`: 78 JavaScript modules and JSON templates.
- `npm test`: 171/171 passed.
- Dataset summary audit: 57 territories, 265 latest indicator checks, 993 explicit observation checks, zero errors.
- Completion matrix: 57/57 complete; 627/627 required domains and 855/855 required themes are terminal.
- Evidence validator: registry 57; UN WPP rows 57, with 55 adopted and 2 unavailable; 797 inventory files.
- Output verification: 34 generated files; all non-empty, all hashes unique, and representative CSV row counts and first/last rows matched their receipts.
- Browser verification: eight smoke checks passed, including Guatemala and Belize parent reset, three languages, 320/375-pixel widths, Guatemala boundary wording and the Belize source-table locator.
- Independent re-audit: **ACCEPT**, with zero blocking, major or minor findings after rechecking source files, generated data and the live local screen.
- `verify-regional-delivery.mjs --require-publishable`: `publishable=true`.

## Release status

The v0.10.1 build passed the independent audit and publication gate on 2026-09-18. GitHub, FTP and public-URL deployment evidence are recorded separately from the independent audit so the auditor's result is not used as proof of hosting.

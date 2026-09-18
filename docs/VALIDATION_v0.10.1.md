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
- `COUNTRY_COMPLETION_MATRIX.json` has 57 records and currently reports **0 complete**.
- The Americas publication gate requires 57/57 complete matrix records and a new independent ACCEPT.

## Current checks

- `npm run check`: 72 JavaScript modules and JSON templates.
- `npm test`: 168/168 passed.
- Current dataset summary audit: 57 territories, 236 latest indicator checks, 964 explicit observation checks, zero errors.
- Browser verification: USA basic facts show population 341,784,857 (2025), electricity 100 (2024) and internet 94.69 (2024), matching the detailed cards.

## Release status

The remediation candidate is not publishable. Country completion is 0/57 and the independent audit status is `incomplete_audit`. The prior public release remains available as a disclosed exploration pilot; no claim of full Americas country completion is made.

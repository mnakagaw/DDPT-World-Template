# AreaData v0.10.4 validation record

Date: 2026-09-23
Scope: country-only territorial summary and browser-load performance.

## User-visible behavior

- The compact population summary above the diagnostic sections is rendered only when the selected territory has `type: country`.
- A province, planning region, municipality or other domestic area has no summary block in that position. Missing values therefore do not create a large repeated `No data` display above the detailed Census section.
- The country summary contains at most two values. When present, the Census population total and UN population estimate are selected before other indicators whose labels or definitions merely contain the word population.
- Detailed indicator sections, missing-value semantics, country/parent reselection, URL state and exports are unchanged.

## Load reductions

- Domestic boundaries are emitted as level-specific shards and fetched only for the selected level and the immediate comparison context.
- The 615-entry source register and UNSD preflight table are created when their disclosure is opened.
- Full Census history is rendered on the database page; other pages link to it.
- Area-search typing updates the result container instead of rerendering the full page.

Representative initial country transfers, calculated with gzip level 6 from the v0.10.3 and v0.10.4 generated files:

| Country | v0.10.3 country payload | v0.10.4 initial data + first boundary level | Change |
| --- | ---: | ---: | ---: |
| El Salvador | 16,940,691 bytes | 2,631,437 bytes | -84.5% |
| Canada | 6,653,516 bytes | 1,257,767 bytes | -81.1% |
| United States | 3,740,529 bytes | 2,929,987 bytes | -21.7% |
| Brazil | 1,247,325 bytes | 1,246,710 bytes | approximately unchanged |
| Mexico | 2,650,931 bytes | 2,007,118 bytes | -24.3% |

The Japanese Americas home page had 156 DOM elements, zero table rows, zero materialized source entries and zero Census-history rows after load. The earlier eager-render baseline recorded 7,391 elements and 102 rows.

## Checks

- `npm run check`: PASS, 112 JavaScript modules and JSON templates.
- `npm test`: PASS, 196/196 tests.
- `node scripts/validate-country.mjs --project .work/areadata-americas-v0.10.4-performance`: PASS with no errors or warnings.
- `node scripts/verify-regional-delivery.mjs --project .work/areadata-americas-v0.10.4-performance`: data and shard integrity PASS. The pre-existing independent Americas-completion audit remains pending, so this UX/performance patch does not claim that every Americas country edition is complete.
- Local browser, domestic selection (`Cibao Norte`): PASS. No country-summary block and no large missing summary; location and internal-comparison maps rendered.
- Local browser, country selection (`Dominican Republic`): PASS. One compact summary block showed Census population and UN population estimate; the source register remained unmaterialized while collapsed.
- Local browser console: no warnings or errors on the checked country page.

## Publication

- FTPS publication: PASS. Of 126 generated site files, 62 existing files changed, 59 boundary-shard files were added and 5 files were unchanged. All 62 predecessors were hash-checked and backed up before mutation. The first connection ended after 28 verified deployments; the recorded resume boundary was checked and the remaining 93 files were uploaded with per-file reconnect/retry and final remote hash verification.
- FTPS receipt: `.work/ftp-deployment-areadata-v0.10.4-performance-2026-09-23.json`.
- Public HTTPS verification: PASS. All 125 web-accessible generated files matched the local candidate byte-for-byte. The retained `.htaccess` was excluded from HTTP verification.
- Public verification receipt: `.work/public-verification-areadata-v0.10.4-performance-2026-09-23.json`.
- Public browser, domestic selection (`Cibao Norte`): PASS. No country summary, map present, detailed Census content present and collapsed source register not materialized.
- Public browser, country selection (`Dominican Republic`): PASS. Compact Census/UN population summary and map present; browser console warnings/errors: 0.

This is a scoped update to the already-public Americas progress snapshot, not an acceptance of the pending full-Americas completion audit.

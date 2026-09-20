# AreaData Americas v0.10.2 validation record

Date: 2026-09-21 JST.

## Status

The Americas candidate is `.work/areadata-americas-v0.10.2-rebuild`. It covers all 57 UN M49 Americas country/area entries. The producer completion matrix reports source review 57/57 and country edition completion 57/57. This means each edition satisfies the evidence contract: official Census or equivalent population evidence, required source-domain review, and either an adopted value or an evidence-backed terminal gap for every required theme. It does not mean that every territory has a value for every theme or the same domestic geographic depth.

The public site remains on the previous release until the current candidate receives a fresh independent `ACCEPT`, passes the publishable gate, and completes the transactional FTPS release.

## Candidate identity

- Template base before release commit: `1fdcd819670ee0dbd21b4b80934bf53194543abf`
- Data edition: `2026-09-20T14:24:44.769Z`
- Dataset SHA-256: `040c125715c0ce27da6c94d495c65196c7933ef47189df56beead2d87ed30eaa`
- 14,988 territories
- 506 indicators
- 183,718 observations
- 564 sources
- 14,914 boundary features
- 239 planning documents

## Evidence and semantic checks

- `npm test`: 184/184 passed.
- `npm run check`: 103 JavaScript modules and JSON templates passed syntax validation.
- `validate-country.mjs`: no errors and no warnings.
- Americas evidence registry: 57 entries; WPP rows 57; adopted 55; evidence-backed unavailable 2; source preflight 57. The final raw-file inventory accounts for all 1,491 files exactly once. Its XLSX semantic inventory accounts for all 185 workbooks as 177 structurally unique workbooks and 8 byte-identical duplicates, with 7,881 field-level disposition records.
- Territorial summary validation: 57 territories, 728 latest-indicator checks, 1,456 explicit-observation checks, and 3 observed zero-value checks; no errors.
- Country isolation: 57 country routes and 342 representative outputs; no cross-country leaks.
- Output verification: 34 non-empty outputs with unique hashes. Data-row checks were Americas 348, Central America + Caribbean 222, Belize 154, Belize district 22, Guatemala 506, and El Progreso 198. Six planning output records were checked.

## Browser and output checks

`evidence/FINAL_BROWSER_QA.json` records 11/11 successful assertions in Google Chrome through the Chrome DevTools Protocol over local HTTP.

- 1366×900, 768×1024, 375×844 and 320×720 had no horizontal document overflow and exposed all five primary navigation items.
- A 200% equivalent run used a 683×450 CSS viewport with device scale factor 2. Navigation and indicator values remained visible without horizontal overflow.
- English, Spanish and Japanese Peru views retained the territorial identity, localized heading, Census population value, 2017 source year, localized unit, Census label and source link.
- `South Georgia and the South Sandwich Islands` rendered at 320px without horizontal overflow, while its observed zero remained visible.
- Keyboard navigation moved from the diagnostic HTML control to the diagnostic CSV control with one Tab and activated it with Enter. Chrome reported a completed 193,235-byte, 199-line download.
- A representative El Progreso diagnostic HTML contained all 176 expected internal rows and 311 source links. Chrome printed the document to a 77-page PDF with SHA-256 `2d9e46f60d6c4cf86833251e080630cb936860f5c1b531f40ff64a2e6c390016`.

## Aggregation and geography safeguards

The candidate keeps source-published observations distinct from AreaData calculations. A parent observation takes priority. A derived value is permitted only for an approved additive indicator with complete, non-overlapping, evidence-backed component coverage; component identities and periods remain attached. Incomplete subtotals are never presented as totals, rates are not simply averaged, missing is distinct from zero, and national values are not copied into municipalities.

The 57-country UN M49 Americas register is retained even where reference geometry is absent. The display-only Central America + Caribbean group is explicitly UN 013 + 029, includes Mexico, and is not presented as an official UN aggregate. Domestic hierarchies remain country-specific.

## Completion and audit boundary

The producer acceptance record has all 42 scenarios classified as passed, not applicable, or not yet performed. A20, direct observation with municipal officials or researchers, remains `未実施`; it is a post-publication user study rather than a claim of technical execution. Responsive, multilingual, keyboard-download, complete-output and print checks are supported by fresh browser evidence.

The candidate is technically complete from the producer side. Publication remains blocked until the separate independent audit is `ACCEPT` and `verify-regional-delivery.mjs --require-publishable` succeeds against the same frozen candidate.

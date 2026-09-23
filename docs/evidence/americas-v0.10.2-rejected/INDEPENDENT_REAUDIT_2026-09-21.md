# AreaData Americas v0.10.2 — independent re-audit

## Decision

**REJECT — BLOCKING**

- Audited commit: `0b136a070e476003b3f78db62f27d91f7be21be8`
- Candidate: `.work/areadata-americas-v0.10.2-rebuild`
- Data edition: `2026-09-20T14:24:44.769Z`
- Canonical dataset SHA-256: `040c125715c0ce27da6c94d495c65196c7933ef47189df56beead2d87ed30eaa`
- Audit date: 2026-09-21 JST

The release transport is internally consistent, but the claim that all 57 country/area editions are complete is not supported by the integrated data or source evidence. The previous `ACCEPT` decision is therefore not accepted by this re-audit.

## Checks that passed

- `HEAD`, `origin/main`, `DELIVERY.json`, and GitHub Actions point to the audited commit.
- GitHub Actions run `35523216260` completed successfully for the four configured Windows/Ubuntu and Node 22/24 jobs.
- `npm run check` passed for 103 JavaScript/JSON inputs.
- `npm test` passed 184/184 tests.
- `validate-country.mjs`, `validate-americas-evidence.mjs`, `validate-territorial-summaries.mjs`, and `verify-regional-delivery.mjs --require-publishable` passed under their current rules.
- The current public full dataset and all 48 declared country shards were reachable and matched the manifest hashes during this re-audit.

These checks show that the same candidate was built, tested, and deployed. They do not establish that the country editions contain sufficiently broad official evidence.

## Blocking findings

### B1. The country-edition gate counts evidence-backed gaps as completed themes

`lib/country-completion-matrix.mjs` treats `not_adopted`, `unavailable`, `restricted`, and `failed_with_evidence` as edition-closing gaps. Lines 47, 50, and 64–66 allow one such record to make a required theme `country_edition_complete=true`; line 73 then makes the country edition complete.

This conflicts with `docs/AMERICAS_COMPLETION_CONTRACT.md`, which states that only integrated and eligible items count toward a completed country edition. A gap may close source review, but it cannot prove that the country dashboard is complete.

### B2. The 57/57 number does not represent broad integrated data

The 15 required themes in `COUNTRY_COMPLETION_MATRIX.json` have the following actual `data_available=true` distribution:

- 1 theme: 5 country/area entries
- 2 themes: 10
- 3 themes: 2
- 4 themes: 2
- 5 themes: 7
- 6 themes: 2
- 7 themes: 2
- fewer than 10 themes: 30
- all 15 themes: 19

The 7,881 semantic inventory records comprise 548 `integrated`, 7,050 `not_adopted`, 210 `unavailable`, and 45 `failed_with_evidence` records. All 57 editions are nevertheless marked complete.

A stricter direct aggregation of observed domestic/local indicators, excluding the common international series, found:

- 14/57 with at least 10 local domestic indicators
- 34/57 with fewer than 6 local domestic indicators
- 9/57 with no local observed value at all: `ABW`, `AIA`, `BHS`, `BRB`, `BVT`, `CUW`, `SGS`, `SXM`, `VGB`

The Central American seven-country adapters and the United States are substantially improved. The result as a whole is a regional gateway with highly uneven country depth, not 57 completed country dashboards.

### B3. A narrow source product is used to close unrelated national themes

Brazil integrates population and age/sex from IBGE SIDRA table 9514. The same age/sex table is then cited to close 13 unrelated themes—housing, water, sanitation, electricity, education, employment, disability, migration, urban/rural, ethnicity, health, nutrition, and poverty—as unavailable. The records themselves say this is only a product-level finding and does not show that the themes are absent from other official sources.

This violates the project rule that the absence of a field in one workbook or table must not be generalized to the whole Census or national statistical system.

### B4. Required source-domain completion lacks auditable evidence

For `BOL`, `BRA`, `COL`, `ECU`, `FLK`, `GUY`, `PRY`, `PER`, `SUR`, `URY`, and `VEN`, all ten required source domains carry `completion_verified=true` while their `evidence` arrays are empty. The gate trusts the boolean flag and does not require an acquired object, hash, page/table locator, or signed audit receipt.

Final-dataset binding is also incomplete: among the 57 `*_INTEGRATION_AUDIT.json` files, 9 match the final dataset SHA, 13 contain no dataset SHA, and 35 point to an older/intermediate SHA. `SOURCE_PREFLIGHT.json` still reports only seven integrated country adapters.

### B5. Planning evidence is not complete across 57 editions

Thirteen entries have no site document in any of plan, budget, implementation, or evaluation categories. Seventeen have no plan document, 39 no budget document, 45 no implementation document, and 47 no evaluation document. An inspected URL or locator is not equivalent to a source-integrated planning record.

### B6. Public cross-country navigation leaves stale country-specific state

On the public United States territorial page, changing the hierarchy country selection to Canada changed the body to Canada Census content, but left the URL/share state with `metric=USA_ACS_POP_TOTAL` and `level=country`. The upper explanatory text remained tied to the United States indicator, and Canada’s available domestic comparison was shown as unconfigured even though the Canada shard contains thousands of lower territories and observations.

This is a cross-country state-isolation failure. Country, territory, metric, level, headings, comparisons, URL, and share state must change atomically.

### B7. Public coverage statements use incompatible definitions

The published bootstrap declares `collection.status=partial`, 55 `census_integrated_country_ids`, and only 48 country shards/domestic branches. Other public UI text reports a different Census-integration count. `SITE_README.md` and the previous audit state that 55/57 combine Census/equivalent evidence with an available domestic hierarchy, although only 48 entries actually contain a domestic branch in the canonical dataset.

The completion, Census-history, and domestic-hierarchy counts must be split and labelled separately.

### B8. The thematic indicator selector exposes foreign country-only indicators

The United States thematic page exposes all 506 indicators, including country-specific fields such as `GTM_CENSUS_DISABILITY_PCT`. A malformed direct link is corrected on first load, but the normal country-switch interaction does not run the same normalization. Country-specific indicators must be filtered to the active country/area before they are selectable.

Reloading the broken Canada URL restores a Canada metric and comparison, but the URL can still retain `level=country` while the page renders the `province_territory` comparison. The canonical URL and rendered level therefore remain inconsistent.

## Major traceability findings

- The previous `INDEPENDENT_AUDIT.md` has no auditor/task identity, separate-thread receipt, command ledger, or signed result. It accepts the same permissive completion rule it was meant to audit.
- `.work/` is ignored by Git, so the claimed independent audit and supporting candidate evidence are not preserved in the published repository.
- `evidence/PUBLIC_VERIFICATION.json` and `evidence/FTP_DEPLOYMENT.json` inside the candidate are stale v0.10.0 records. `DELIVERY.json` instead points to current receipts under repository `tmp/`. Those receipts exist, but they are outside the candidate evidence package and are not the files named by the older evidence records.
- 184 passing tests mainly prove internal consistency with the permissive gate. They do not test whether all relevant official tables were sought before a theme was closed, or whether every country has adequate integrated depth.

## A20

Keeping A20 as unperformed is accurate. A20 is not the reason for this rejection. The release already fails the data-coverage, source-evidence, and public-state requirements above.

## Required remediation before a new ACCEPT

1. Make evidence-backed gaps close only `source_review_complete`; never count them as `country_edition_complete` or `data_available`.
2. Require each completed source domain to point to acquired evidence with hash and exact page/table/API locator, bound to the final dataset SHA.
3. Re-open every country with fewer than the agreed minimum integrated theme/local-indicator depth. Search the broader official Census/statistical catalog, not one selected table.
4. Keep honest country-level classifications such as `source review complete`, `national-only`, `population/local hierarchy only`, `broad local edition`, and `structural nonresident exception` instead of one 57/57 completed label.
5. Reconcile the 43/48/55 Census, shard, and hierarchy counts and expose them as separate measures.
6. Fix country switching so metric, level, URL, share state, explanatory text, map, ranking, documents, and outputs all switch together.
7. Put the final deployment and public-verification receipts inside the audited evidence package, remove or supersede stale receipts, and run a genuinely separate audit against the final commit and dataset hash.

Until these are complete, the public release may be described as a technical preview or regional gateway with uneven country coverage. It must not be described as 57 completed country/area editions or as independently accepted.

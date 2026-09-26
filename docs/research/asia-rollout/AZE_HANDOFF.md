# Azerbaijan country candidate — handoff, 2026-09-26

**Partial domestic candidate; no independent country-edition ACCEPT; unpublished.** Local ignored candidate: `generated/azerbaijan-areadata-20260926`; fresh bootstrap/replay: `generated/azerbaijan-replay-20260926`. The [source and output audit](../../evidence/azerbaijan-ssc-2026-age-astara-planning-2026-09-26.md) and [727-column register](../../evidence/azerbaijan-ssc-xls-numeric-columns-2026-09-26.csv) explain adopted and pending evidence. Original 11 files, acquisition receipts, source row checks and actual ten-area outputs remain in each ignored project; large or redistribution-unreviewed originals are not in Git.

Recreate in a **new** directory; `import-azerbaijan-age2026-partial.py` refuses to overwrite a modified bootstrap:

```powershell
node scripts/create-country.mjs --country AZE --out <new-directory>
# Read <new-directory>/evidence/SOURCE_PREFLIGHT.md and .json first.
python -X utf8 scripts/collect-azerbaijan-official.py --project <new-directory>
python -X utf8 scripts/inspect-azerbaijan-official.py --project <new-directory>
python -X utf8 scripts/import-azerbaijan-age2026-partial.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-azerbaijan-age2026-output.mjs --project <new-directory>
```

The collector pins all 11 original SHA-256 hashes and will stop on upstream change. For an offline replay, copy each raw original and its receipt into a fresh bootstrap, then run the collector; the recorded acquisition time remains the original fetch time. The replay verified all 11 files and matched the 2,023 adopted domestic observation tuples at SHA-256 `2b0e0fc3de2952d66581a7113864cac540400159f623e5789c669c85fa3f1c7f`.

Candidate dataset SHA-256 `009c2a6e13a06a39f9d997818ea989f7582aaaa7b1b9a81c99381d9ac9ed324d`: 102 territories, 23 domestic indicators, 2,023 domestic observations, one Astara-city-only approved plan record, **zero polygons**. SSC 2026 table 1.23.6 contributes 101 rows × 20 exact-person columns, and SSC table 1.19 contributes three rounded-thousand Astara city values. The 14 first-level source rows sum to the national 10,262,351 residents. These are 2026 annual estimates derived from the 2019 census, not the census itself. Their economic-region comparison is statistical, not a planning-authority definition. Astara city is not Astara district, and its plan does not become a district plan.

Producer validator 0 errors/warnings, build and source-pinned ten-area CSV/HTML output verifier passed for candidate and replay. Browser QA reached the city through the hierarchy, returned to the district, checked city/district values and missing child-specific values, and showed the Cabinet approval only on the city planning page; national thematic comparison had 14/14 values. The optional `analysis.incomplete_child_cover_ids` holds Astara district navigable without comparing its only registered city as a full district cover. These checks are not the 42-scenario suite or independent acceptance. Local HTTP was only for QA; no Hosting/Public Azerbaijan site exists.

Next: audit the 2019 census A/B volumes and all 704 unadopted XLS numeric columns; reconcile every official code and current dated polygon including territorial changes; establish legal planning roles and plan annex/current revisions; acquire other local plans, budgets, execution and evaluations; finish representative/narrow/print/download and applicable acceptance scenarios; submit fixed producer commit and dataset hash to an independent checker. Source locations can return to Kit at `official_location_identified` only, without data values. No country publication before independent `ACCEPT`.

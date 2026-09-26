# Georgia country candidate — handoff, 2026-09-26

**Status: partial domestic candidate, producer-validated, independent audit pending, unpublished.** Local ignored candidate: `generated/georgia-areadata-20260926`; separately bootstrapped/re-fetched replay: `generated/georgia-replay-20260926`. The [tracked official-source audit](../../evidence/georgia-geostat-2024-kutaisi-planning-2026-09-26.md) and [63-column register](../../evidence/georgia-geostat-2024-numeric-columns-2026-09-26.csv) record originals, field decisions, hashes, Kutaisi evidence and limitations. The candidates retain raw files, receipts, source rows, seven-area output checks and producer notes outside Git.

Recreate in a **new** directory; do not rerun the importer over an already imported candidate:

```powershell
node scripts/create-country.mjs --country GEO --out <new-directory>
# Read <new-directory>/evidence/SOURCE_PREFLIGHT.md and .json before proceeding.
python -X utf8 scripts/collect-georgia-geostat-2024.py --project <new-directory>
python -X utf8 scripts/collect-georgia-kutaisi-planning.py --project <new-directory>
python -X utf8 scripts/inspect-georgia-geostat-2024.py --project <new-directory>
python -X utf8 scripts/import-georgia-geostat-2024-partial.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-georgia-geostat-output.mjs --project <new-directory>
```

For an independent fresh bootstrap, repeat in a second **new** directory, then run `python -X utf8 scripts/compare-georgia-geostat-replay.py --project <first> --replay <second>`. In this pass all nine originals re-fetched with identical hashes. The replay matched 85 territories, 1,440 domestic records, two documents and 19 Georgia source records; adopted tuple SHA-256 `6706b151efab4aa65d9b63ffb5dabd664a5bc0f32c1ba0c468a19d2aae1551e5`, snapshot SHA-256 `183f90edfe4525ebd56d391bd25ceae661829cf23e639add8d26581e837a3131`. Fresh WDI retrieval timestamps are outside this domestic comparison.

Current candidate dataset SHA-256 `2f93be22179041b3f07cd86ba372ab92399b3774bf0a1ac725d1ba3437a33a75`: 85 territories (nation, 11 broad reporting rows, 63 other municipalities/cities, 10 Tbilisi districts), 18 domestic indicators, 1,440 domestic observations (1,413 numeric, 27 source-dash missing), two Kutaisi documents and **zero polygons**. Table 02 nationwide population is 3,929,581. Table 06 nationwide IDPs are 210,628, a population subset. No Tbilisi-district IDP is inferred. The 12 bootstrap 2015 provider polygons are withheld pending official coded, dated reconciliation.

Both candidates validated with zero errors/warnings, built and passed seven-area source-pinned CSV/HTML checks. Local browser checks covered Georgia → Imereti → Kutaisi → Imereti, Kutaisi's two documents, Tbilisi → Didube, and the district IDP comparison (0/10 observed). The local browser needed a JavaScript MIME type for `.mjs`; the generated site itself was unchanged by that server setting. The original Kutaisi budget is documented as approved in December 2025, while later amendments and actual expenditure are unverified. These are producer checks, **not** 42-scenario or independent acceptance. GitHub storage does not imply Hosting/Public publication.

Next: independently audit the fixed producer commit, dataset SHA, receipts, original cells/pages and actual screen/output files, yielding `ACCEPT`, `REJECT` or `INCOMPLETE AUDIT`. If findings require code/data changes, fix in a separate isolated worktree and resubmit the regenerated candidate to the same checker. Substantive unfinished work remains: all other 2024 census topical/agricultural tables, official 2024 codes/geometry, current Kutaisi budget revisions, other local plans/budgets/implementation/evaluation, narrow screen/print checks and applicable acceptance scenarios. No country hosting/publication before independent `ACCEPT`.

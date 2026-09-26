# UAE country candidate — handoff, 2026-09-26

**Status: historical seven-emirate census and Abu Dhabi 2024 local partial candidate; not independently accepted or published.** The ignored local output is `generated/uae-areadata-20260926`. Its four official originals and hash receipts are in `raw/uae-official/`; the dataset, `evidence/ARE_OFFICIAL_IMPORT_AUDIT.json`, `evidence/ARE_SOURCE_NAME_CROSSWALK.csv`, `evidence/ARE_OUTPUT_VERIFICATION.json`, `evidence/COUNTRY_LESSON_AUDIT.md` and site are local only. The [tracked source audit](../../evidence/uae-official-census-scad-dubai-sources-2026-09-26.md) records the adopted fields, page-level nonadoption inventory and limitations. Do not put the 7.7 MB plan PDF, census PDF, HTML snapshot or unreviewed redistribution bodies in Git.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country 'United Arab Emirates' --out <new-directory>
python -X utf8 scripts/collect-uae-official-sources.py --project <new-directory>
python -X utf8 scripts/import-uae-official-partial.py --project <new-directory>
python -X utf8 scripts/register-uae-official-source-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-uae-official-output.mjs --project <new-directory>
```

The importer pins exact PDF hashes. SCAD's HTML changes between requests, so each local receipt pins its downloaded body and the importer checks exact displayed counts and labels; a content change fails until audited. The verified first local candidate dataset SHA-256 after the 2026-09-26 pass is `E3477F4D59891BCA677EA8FD5187A16A176C5D40A54A288881BFCAFBBED5F622`. It has 8 territories, 19 indicators, 475 observations and two Dubai-only documents. Four federal census count series cover 1975/1980/1985/1995/2005, national and all seven emirates (160 observations). SCAD 2024 total/male/female cover **Abu Dhabi only** (3 observations). The source table sums and urban+rural decompositions pass for every census year. National WDI midyear population, SCAD register counts and 2005 federal census counts remain distinct indicators.

Seven 2017 `geoBoundaries` shapes support navigation only. Two source/provider spelling pairs are explicit, but official emirate codes and dated legal boundaries, the three SCAD internal regions, and lower geography have not been reconciled. Dubai's 2040 plan executive summary and Law 16/2023 are Dubai-only references with selected pages checked. They do not establish any other emirate's law or plan. No actual budget, execution report, evaluation or plan-compliance decision was adopted. The SCAD page linked from the Kit/UNSD preflight is reused rather than newly discovered; its Abu Dhabi content does not prove a seven-emirate 2023 national census.

Local validation returned zero errors/warnings; site build and selected HTML/CSV output checks passed. A second fresh directory (`generated/uae-replay-20260926`, ignored) reacquired the originals and reproduced all 163 adopted domestic observations and the two document IDs; its validator, build and output checks passed. Browser selection checked Abu Dhabi's old and current values, Dubai's two documents, and Dubai → national reset with no Dubai document carryover. This is **not** a 42-scenario pass or an independent source/UX `ACCEPT`. Hosting and public verification were not run.

Next: obtain comparable recent official observations for the other six emirates and current sector indicators; audit the remaining FCSC publication tables/columns; acquire UAE.Stat and Dubai 2024 population bulletin originals if access permits (direct requests returned HTTP 403); verify current official code/boundary editions and internal regions; check the entire Dubai plan/law amendments and find each other emirate's plans, budgets, execution and official evaluations; run representative selection, full-table print/export, 42-scenario and independent acceptance checks before publication. Keep the last validated local candidate until those gates pass.

# Oman country candidate — handoff, 2026-09-26

**Status: 2020 eCensus population and housing-unit subsets plus one national 2026–2030 plan document; independent country-edition verdict REJECT, unpublished.** The original ignored candidate is `generated/oman-areadata-20260926`; the current independently re-acquired housing extension is `generated/oman-housing-remediation-r2-20260926`. The [population/plan source audit](../../evidence/oman-ecensus-2020-moi-national-plan-2026-09-26.md), [housing remediation audit](../../evidence/oman-ecensus-housing-remediation-2026-09-26.md) and [independent checker verdict](../../evidence/oman-housing-independent-audit-2026-09-26.md) give official URLs, source decisions, hashes and sampled validation. Original XLSX/JSON/PDF/HTML files and receipts are local only pending redistribution review.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country Oman --out <new-directory>
python -X utf8 scripts/collect-oman-ecensus-moi-sources.py --project <new-directory>
python -X utf8 scripts/collect-oman-national-plan.py --project <new-directory>
python -X utf8 scripts/collect-oman-ncsi-wilayat-register.py --project <new-directory>
python -X utf8 scripts/inspect-oman-ecensus-moi.py --project <new-directory>
python -X utf8 scripts/import-oman-ecensus-2020-partial.py --project <new-directory>
python -X utf8 scripts/import-oman-national-plan.py --project <new-directory>
python -X utf8 scripts/register-oman-official-source-leads.py --project <new-directory>
python -X utf8 scripts/collect-oman-ecensus-product-catalogue.py --project <new-directory>
python -X utf8 scripts/import-oman-ecensus-housing-2020.py --project <new-directory>
python -X utf8 scripts/register-oman-governorate-finance-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-oman-ecensus-output.mjs --project <new-directory>
```

Compare a second independently created directory with `python -X utf8 scripts/compare-oman-ecensus-replay.py --first <first-project> --second <second-project>`. The actual `generated/oman-replay-20260926` comparison passed: pinned MOI `63225e0a09ad41a41d5bd3b98b506e9117defdd67b8a7bbc0770ed686c63419b`, national plan `66362a395113a6db83acdf1c1a6887635a69df6bca66fad077bffca5dea6a58b`, adopted 219-tuple hash `a3ef02dfd0b86ecd753cefe10da2c50b84f9fc3bfb809ebcf81b9ffeb4ca0686`, bilingual crosswalk and 63 NCSI/MOI name matches. Dynamic API processing times and fresh WDI national fetches are excluded from semantic equality.

The first registered candidate dataset SHA-256 is `7bacf1fe42e7e9746188b1b556c83595626232d4cbaae9f000e23d7b9d573799`. It has 73 territories, 15 indicators and 531 observations, including **219 eCensus domestic observations**, and one national plan document. The 2020-12-12 census total is **4,471,148**. It is not WDI's later midyear estimate, and the source's English “Residential Status” is the Arabic nationality Omani/expatriate. Other eCensus dates and fields are not adopted. The 2025 Ministry of Interior directory has 63 wilayats; the source's `ALJABAL ALAKDAR` and `SINAW` 2020 cells are null, not zero. NCSI/MOI spatial names match 63/63, but code systems and valid boundary dates differ or remain unknown. No polygon has been accepted as the 2020 source boundary.

The current housing-extension dataset SHA-256 is `5d9b5af1d2f208f2c007c2bf96afb774a251d035272e8b043add5d0dbf688326`: the same 73 territories, 16 indicators and **604 observations**, including 219 domestic population and 73 domestic housing-unit values. The source's 2020-12-12 national housing-unit count is **1,312,327**. The other 11 public eCensus products have metadata inventory only; no values from them are adopted. The 2024 Ministry of Finance final-account PDF and governorate duties are location leads, not local plan approval or adopted financial values. Three additional public locations were selected for Kit feedback, capped at `official_location_identified`.

`validate-country` returned zero errors and warnings for the current extension; build and seven-area CSV/HTML output checks passed, including seven housing controls and the three pivot receipts. The two housing acquisitions have identical substantive pivot data after excluding variable `query_time_ms`. Browser checks covered Oman, Muscat governorate, same-name Muscat wilayat, explicit parent reselection, planning and thematic navigation; the current Muscat governorate screen showed 412,033 housing units and 6/6 internal comparison. Muscat's planning page correctly shows no local plan while displaying the national plan separately. The ignored `evidence/COUNTRY_LESSON_AUDIT.md` gives sampled UA results; **42 applicable acceptance scenarios and independent `ACCEPT` remain open**. Hosting and public verification were not run.

Source-feedback roundtrip: AreaData selection/script/evidence commit `e38724e882d186e2e69e5c848333d5536e768885` and 82-source export commit `366ada58f9aef1b6c20fe77356b0192294107668` were pushed. Bundle `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 is `f94a0e6ff780fa67e5fa874377399d45f99430d2b24cf264a1eb82056ffea191`; it contains ten Oman leads, all capped at `official_location_identified`. Kit dry-run accepted 82, inserted 10 and updated 72; import produced 83 total records. Kit `check`, 173 tests and `verify:kit` passed; repeat dry-run found 82 unchanged. Kit import commit `b7b3e7b343b03dec1c876d3c26677933d316bd22` was pushed, and all Oman records retain `not_acquired_by_kit_preflight`. The AreaData and Kit remote branch heads were read back and matched local commits.

The housing extension's three newly identified governorate/finance locations were returned through a second source-feedback roundtrip: AreaData producer `32cbaba6e396bdb84fd3458db1e9f06d4449fe4c`, bundle `5cd8d2d7c29654209a34e943ccc516c27bffd09c` (SHA-256 `3ceb8acc4ca3c3bea8f87bdd7e5a0f7f923ee6fe1d3c37638a1e5c4afcc3a8c2`), Kit import `92837ab7b1ba5d2549ea009a3660829670721f50`. The bundle now has 13 Oman leads among 133 total; Kit has 134 records overall. All new Oman records remain `official_location_identified` in feedback and `not_acquired_by_kit_preflight` in Kit. Both branches were pushed and remote hashes matched.

The independent checker returned **ACCEPT for the narrow housing remediation and REJECT for Oman country completion** on the fixed producer commit and dataset hash above. It verified all 73 housing pivot cells/row positions, 13 product receipts, seven diagnostic CSVs (576 rows), and same-named Muscat wilayat→governorate browser reselection. No checked P0/P1 regression was found. This does not authorize Hosting/Public release.

Next: audit the 11 metadata-only eCensus products and housing subgroups; reconcile 2020/2025 wilayat codes and dated legal polygons; assess the remaining 120 main-plan PDF pages, strategic-programme and spatial-plan volumes; verify the operative local planning law; acquire actual governorate plans, budgets, expenditure and evaluation originals and distinguish government-unit from territorial spending. Run representative and exception area exports/print and full independent acceptance before any public deployment.

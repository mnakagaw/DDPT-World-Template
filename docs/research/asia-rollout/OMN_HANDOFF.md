# Oman country candidate — handoff, 2026-09-26

**Status: 2020 eCensus nation/11-governorate/61-wilayat population subset plus one national 2026–2030 plan document; partial, not independently accepted or published.** The ignored candidate is `generated/oman-areadata-20260926`. The [tracked source audit](../../evidence/oman-ecensus-2020-moi-national-plan-2026-09-26.md) gives official URLs, source hashes, numerical choices, code/boundary caveats and sampled validation. Original XLSX/JSON/PDF/HTML files and receipts are local only pending redistribution review.

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
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-oman-ecensus-output.mjs --project <new-directory>
```

Compare a second independently created directory with `python -X utf8 scripts/compare-oman-ecensus-replay.py --first <first-project> --second <second-project>`. The actual `generated/oman-replay-20260926` comparison passed: pinned MOI `63225e0a09ad41a41d5bd3b98b506e9117defdd67b8a7bbc0770ed686c63419b`, national plan `66362a395113a6db83acdf1c1a6887635a69df6bca66fad077bffca5dea6a58b`, adopted 219-tuple hash `a3ef02dfd0b86ecd753cefe10da2c50b84f9fc3bfb809ebcf81b9ffeb4ca0686`, bilingual crosswalk and 63 NCSI/MOI name matches. Dynamic API processing times and fresh WDI national fetches are excluded from semantic equality.

The first registered candidate dataset SHA-256 is `7bacf1fe42e7e9746188b1b556c83595626232d4cbaae9f000e23d7b9d573799`. It has 73 territories, 15 indicators and 531 observations, including **219 eCensus domestic observations**, and one national plan document. The 2020-12-12 census total is **4,471,148**. It is not WDI's later midyear estimate, and the source's English “Residential Status” is the Arabic nationality Omani/expatriate. Other eCensus dates and fields are not adopted. The 2025 Ministry of Interior directory has 63 wilayats; the source's `ALJABAL ALAKDAR` and `SINAW` 2020 cells are null, not zero. NCSI/MOI spatial names match 63/63, but code systems and valid boundary dates differ or remain unknown. No polygon has been accepted as the 2020 source boundary.

`validate-country` returned zero errors and warnings; build and selected CSV/HTML output checks passed. Browser checks covered Oman, Muscat governorate, same-name Muscat wilayat, explicit parent reselection, planning and thematic navigation. Muscat's planning page correctly shows no local plan while displaying the national plan separately. The ignored `evidence/COUNTRY_LESSON_AUDIT.md` gives sampled UA results; **42 applicable acceptance scenarios and independent `ACCEPT` remain open**. Hosting and public verification were not run.

Next: audit all official eCensus population, housing and establishment fields and product catalogue; reconcile 2020/2025 wilayat codes and dated legal polygons; assess the remaining 120 main-plan PDF pages, strategic-programme and spatial-plan volumes; determine the legal local planning unit; acquire actual governorate/wilayat plans, budget, expenditure and evaluation originals. Run representative and exception area exports/print and full independent acceptance before any public deployment.

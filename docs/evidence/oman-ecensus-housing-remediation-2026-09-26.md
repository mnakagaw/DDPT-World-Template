# Oman remediation: eCensus product inventory and housing-unit counts

Checked 2026-09-26. This is an **unpublished partial candidate**, not an independent `ACCEPT`. The current isolated candidate is `generated/oman-housing-remediation-r2-20260926`, dataset SHA-256 `5d9b5af1d2f208f2c007c2bf96afb774a251d035272e8b043add5d0dbf688326`. It has 73 territories, 16 indicators, 604 observations (219 domestic population, 73 domestic housing units and 312 separate WDI national records), one national plan reference and zero adopted polygons.

## Original product inventory and new adoption

The [official eCensus dataset builder](https://www.ecensus.gov.om/web/#/en/datasets) uses the public API at `https://www.ecensus.gov.om/dregndrop-api/v1/datasets/`. Its `/categories` response lists **13 products in three categories**: population (population, job seekers, workforce, births, deaths, disability), housing/buildings (land, housing units, buildings), and enterprises (enterprise, establishment, vehicles, investors). `collect-oman-ecensus-product-catalogue.py` now receipts the catalogue, all 13 product metadata responses, and the national, governorate and wilayat pivots for the housing-unit product. The generated `OMN_ECENSUS_PRODUCT_INVENTORY.json` records every product's fields, source hash and current disposition: the prior 219 population observations, the new 73 housing-unit observations after import, and metadata-only status for the remaining 11 products. Catalogue and metadata enumeration is **not** a numerical audit of those 11 products.

The official `v_public_ds_housing_unit_en` metadata identifies `AMOUNT` as the measure, `RUN_DATE`, `LOCATION_GOVERNORATE`, `LOCATION_WILAYAT`, and housing-unit use/type/occupancy as dimensions. With no category filters, the 2020-12-12 pivot returns **1,312,327 housing units** nationally, 11 governorates and 61 wilayats with numeric 2020 cells. The source's two other wilayat rows, `Ad Dakhliyah / ALJABAL ALAKDAR` and `Ash Sharqiyah North / SINAW`, are null at this date, not zero. The 11 source governorate cells and 61 observed wilayat cells each sum to the national source cell; every governorate equals the sum of its observed wilayats. The three independently receipted pivot levels are joined by exact source labels to the already adopted 2020 population reporting IDs. No 2025 code or polygon is promoted to 2020 validity.

`import-oman-ecensus-housing-2020.py` adds one narrowly named **housing-unit count** indicator with 73 observed rows, each carrying a source pivot row. It does **not** infer households, occupied units, housing quality, water or sanitation. Occupancy subgroup values and their definitions remain unassessed and unadopted. Later dates are not mixed into the 2020 series. Product and pivot originals plus receipts are stored only in the ignored generated candidate, pending redistribution-terms review.

The first and second separate API acquisitions returned different byte hashes because the response metadata includes a variable `query_time_ms`. After excluding metadata and canonicalizing structure, headers, data and totals, both acquisitions had the same substantive SHA-256 per pivot: national `749075acbfa2249b239d890933e19344f55c61024254dd95cf8b81331180667d`, governorate `23c4d0c1ff4904586b41cc078f1d15789f825c7cc4fe90f8e3a35a608847b9ba`, wilayat `f631e095b328ac800917cb06effe9dd949695e337a39dec26782b3e23adff0b3`. Each complete raw response still matches its own receipt byte hash. The source controls in the output verifier include 1,312,327 national, 412,033 Muscat governorate, 6,868 Muscat wilayat, 136,188 Ad Dakhliyah governorate, 39,307 Nizwa, 70,438 Sohar and 12,343 Al Wusta governorate housing units.

## Planning and finance: evidence located, not yet adopted

An [official South Al Sharqiyah Governorate page quoting Article 11 of Royal Decree 36/2022](https://ssg.gov.om/the-governor) assigns the governor preparation/monitoring of governorate development-plan projects and preparation of the annual governorate budget and final account for submission to the Ministry of Finance. This establishes a **governorate-level responsibility**, but neither a specific approved local plan nor a wilayat planning obligation. The [government-hosted English Gazette translation](https://alwusta.gov.om/wp-content/uploads/2025/10/Promulgating-the-System-of-Governorates.pdf) is an additional legal-original lead; its edition, legal language and applicability require separate verification before the country adapter treats it as complete legal authority.

The [Ministry of Finance e-library](https://www.mof.gov.om/e-library) lists the 2026 State Budget and final-account products. Its [2024 final-account schedules PDF](https://www.mof.gov.om/download.aspx?id=L1VwbG9hZHNBbGwvRmluYWxBY2NvdW50LzE3NDg3Nzg3MDU0NDJTY2hlZHVsZXMgb2YgdGhlIHN0YXRlcyBmaW5hbCBhY2NvdW50IGZvciBmaXNjYWwgeWVhciAyMDI0LnBkZg%3D%3D) contains governorate-labeled development-expenditure rows (PDF pages 47–49). These are promising **government-unit expenditure** records; they are not yet copied into a local-finance indicator or interpreted as all spending within a governorate. The [Oman National Spatial Strategy overview](https://oman.housing.gov.om/onss) describes national coordination across 11 governorates, not an adopted local plan body for each area.

`register-oman-governorate-finance-leads.py` records the three new public locations in the candidate with status `official_location_identified` in its preflight and no adopted values. The government-hosted Gazette translation remains an unverified lead and was not added to the feedback selection.

## Reproduction and remaining acceptance conditions

Run on an Oman candidate already holding the 2020 population import:

```powershell
python -X utf8 scripts/collect-oman-ecensus-product-catalogue.py --project <candidate>
python -X utf8 scripts/import-oman-ecensus-housing-2020.py --project <candidate>
python -X utf8 scripts/register-oman-governorate-finance-leads.py --project <candidate>
node scripts/validate-country.mjs --project <candidate>
node scripts/build-country.mjs --project <candidate>
node scripts/verify-oman-ecensus-output.mjs --project <candidate>
```

On two isolated copies of the existing Oman candidate, acquisition found the same 13 products and substantive housing pivots; import added 73 observations. The second candidate also registered the three planning/finance locations. Its `validate-country` returned zero errors/warnings; build and seven-area CSV/HTML source-output checks passed. The generated gap text now reports housing adoption and the other 11 metadata-only products. Local browser checks showed Muscat governorate's 412,033 housing units, the 6/6 internal comparison and the explicit unit/source wording. These checks do **not** replace narrow-screen, print, all 42 applicable scenarios or independent source audit.

Still blocking independent acceptance: dated 2020 official codes and legal boundary polygons/equivalence; value-level disposition of the remaining eCensus products and housing subdivisions; original approved governorate plans, budget/final-account and implementation/evaluation bodies linked to the correct unit and period; full applicable 42-scenario screen/output/print checks; a separate independent `ACCEPT`. No publication is authorized.

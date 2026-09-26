# Oman remediation: eCensus product inventory and housing-unit counts

Checked 2026-09-26. This is an **unpublished partial candidate**, not an independent `ACCEPT`.

## Original product inventory and new adoption

The [official eCensus dataset builder](https://www.ecensus.gov.om/web/#/en/datasets) uses the public API at `https://www.ecensus.gov.om/dregndrop-api/v1/datasets/`. Its `/categories` response lists **13 products in three categories**: population (population, job seekers, workforce, births, deaths, disability), housing/buildings (land, housing units, buildings), and enterprises (enterprise, establishment, vehicles, investors). `collect-oman-ecensus-product-catalogue.py` now receipts the catalogue, all 13 product metadata responses, and the national, governorate and wilayat pivots for the housing-unit product. The generated `OMN_ECENSUS_PRODUCT_INVENTORY.json` records every product's fields, source hash and non-adoption decision. Catalogue and metadata enumeration is **not** a numerical audit of the other 12 products.

The official `v_public_ds_housing_unit_en` metadata identifies `AMOUNT` as the measure, `RUN_DATE`, `LOCATION_GOVERNORATE`, `LOCATION_WILAYAT`, and housing-unit use/type/occupancy as dimensions. With no category filters, the 2020-12-12 pivot returns **1,312,327 housing units** nationally, 11 governorates and 61 wilayats with numeric 2020 cells. The source's two other wilayat rows, `Ad Dakhliyah / ALJABAL ALAKDAR` and `Ash Sharqiyah North / SINAW`, are null at this date, not zero. The 11 source governorate cells and 61 observed wilayat cells each sum to the national source cell; every governorate equals the sum of its observed wilayats. The three independently receipted pivot levels are joined by exact source labels to the already adopted 2020 population reporting IDs. No 2025 code or polygon is promoted to 2020 validity.

`import-oman-ecensus-housing-2020.py` adds one narrowly named **housing-unit count** indicator with 73 observed rows, each carrying a source pivot row. It does **not** infer households, occupied units, housing quality, water or sanitation. For comparison, an official occupancy pivot of the same table showed 2020 `Used` 962,369, `Semi-used` 112,506 and `Not used` 237,452, summing to 1,312,327; that breakdown remains unadopted pending definition review. Later dates are not mixed into the 2020 series. Product and pivot originals plus receipts are stored only in the ignored generated candidate, pending redistribution-terms review.

## Planning and finance: evidence located, not yet adopted

An [official South Al Sharqiyah Governorate page quoting Article 11 of Royal Decree 36/2022](https://ssg.gov.om/the-governor) assigns the governor preparation/monitoring of governorate development-plan projects and preparation of the annual governorate budget and final account for submission to the Ministry of Finance. This establishes a **governorate-level responsibility**, but neither a specific approved local plan nor a wilayat planning obligation. The [government-hosted English Gazette translation](https://alwusta.gov.om/wp-content/uploads/2025/10/Promulgating-the-System-of-Governorates.pdf) is an additional legal-original lead; its edition, legal language and applicability require separate verification before the country adapter treats it as complete legal authority.

The [Ministry of Finance e-library](https://www.mof.gov.om/e-library) lists the 2026 State Budget and final-account products. Its [2024 final-account schedules PDF](https://www.mof.gov.om/download.aspx?id=L1VwbG9hZHNBbGwvRmluYWxBY2NvdW50LzE3NDg3Nzg3MDU0NDJTY2hlZHVsZXMgb2YgdGhlIHN0YXRlcyBmaW5hbCBhY2NvdW50IGZvciBmaXNjYWwgeWVhciAyMDI0LnBkZg%3D%3D) contains governorate-labeled development-expenditure rows (PDF pages 47–49). These are promising **government-unit expenditure** records; they are not yet copied into a local-finance indicator or interpreted as all spending within a governorate. The [Oman National Spatial Strategy overview](https://oman.housing.gov.om/onss) describes national coordination across 11 governorates, not an adopted local plan body for each area.

## Reproduction and remaining acceptance conditions

Run on an Oman candidate already holding the 2020 population import:

```powershell
python -X utf8 scripts/collect-oman-ecensus-product-catalogue.py --project <candidate>
python -X utf8 scripts/import-oman-ecensus-housing-2020.py --project <candidate>
node scripts/validate-country.mjs --project <candidate>
node scripts/build-country.mjs --project <candidate>
node scripts/verify-oman-ecensus-output.mjs --project <candidate>
```

On an isolated copy of the current Oman candidate, acquisition found 13 products; import added 73 observations; `validate-country` returned zero errors/warnings; build and representative CSV/HTML source-output checks passed. These checks do **not** replace browser/print scenarios or independent source audit.

Still blocking independent acceptance: dated 2020 official codes and legal boundary polygons/equivalence; value-level disposition of the remaining eCensus products and housing subdivisions; original approved governorate plans, budget/final-account and implementation/evaluation bodies linked to the correct unit and period; full applicable 42-scenario screen/output/print checks; a separate independent `ACCEPT`. No publication is authorized.

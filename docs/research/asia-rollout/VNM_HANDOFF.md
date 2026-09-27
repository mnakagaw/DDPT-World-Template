# Viet Nam AreaData handoff — 2026-09-27 JST

**Status: historical 2019 census partial candidate, independent `ACCEPT` pending, unpublished.** After this candidate the Asia ledger is 0 complete, 31 partial, 1 research-only and 18 not started. Next unstarted priority: Thailand. The ignored project is `generated/vietnam-areadata-20260927`. Tracked code, source manifest, audit and producer validation allow rebuilding a new candidate. No VNM Hosting/Public destination is assigned.

## Evidence and decisions

- The [official joint GSO/UNFPA 2019 results report](https://vietnam.unfpa.org/en/publications/results-2019-census-population-and-housing-viet-nam) was acquired as a 380-page PDF. Table 1 has nine person-count columns across country, six socioeconomic regions and 63 historical provinces/cities. All 630 cells were parsed, with row-internal and both national subtotal checks. Country population is **96,208,984**; 64 country/province rows ×9 columns yield **576 direct observations**. The six broad regions remain audit-only to avoid overlap in the administrative comparison. WDI annual midyear population is a separate series.
- The separate [NSO Completed Results catalogue](https://www.nso.gov.vn/en/data-and-statistics/2020/11/completed-results-of-the-2019-viet-nam-population-and-housing-census/) describes 26 detailed district-level tables. The [official original PDF location](https://www.nso.gov.vn/wp-content/uploads/2019/12/Ket-qua-toan-bo-Tong-dieu-tra-dan-so-va-nha-o-2019.pdf) was indexed but NSO requests reset. Its body, district data and fields were not acquired. The joint report's other 59 detailed table headings are `priority_unassessed`; some subjects use a 9% household sample.
- The partial site has **64 statistical reporting areas**, not a present-day province roster. Table 1 lacks printed administrative codes, so `P01`–`P63` are source-row ordinals only. The old provider's 64 ADM1 shapes were removed; no official compatible polygon is joined. The [2025 reform](https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-quyet-so-202-2025-qh15-ve-sap-xep-don-vi-hanh-chinh-cap-tinh-119250612174148722.htm) created 34 province-level units; the [2025 code notice](https://xaydungchinhsach.chinhphu.vn/bang-danh-muc-va-ma-so-cua-34-tinh-thanh-moi-cac-don-vi-hanh-chinh-cap-xa-moi-11925070418263625.htm) lists 3,321 communes. No name-only 2019↔2025 join or legal planning authority is asserted.
- Planning law, 2025 local-government law and a pair of current Hà Nội city/Kiến Hưng ward plan catalogue locations were identified. The local catalogue requests timed out and no content or approval was adopted. Selected historical Ha Noi has empty local plan, budget, implementation and evaluation categories; current references appear separately as national examples.

[Source audit](../../evidence/vietnam-census2019-source-audit-2026-09-27.md), [start sheet](../../evidence/vietnam-country-start-2026-09-27.md), [Task Contract](../../evidence/vietnam-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/vietnam-country-lesson-audit-2026-09-27.md) define the evidence boundary. The ignored project holds pinned originals, row audit, import result, output hashes and final dataset.

## Reproduce and inspect

Start from a **new** directory; never overwrite a working candidate after acquisition/build failure. Obtain the two official UNFPA originals at the paths in `config/vietnam-census2019-source-manifest.json` and verify bytes/SHA-256. If an official original changes, review the new snapshot before changing the manifest or adopter. Preserve the old candidate until the new one passes validation.

```powershell
node scripts/create-country.mjs --country "Viet Nam" --out generated/vietnam-replay-new
# Obtain the official UNFPA catalogue HTML and joint GSO/UNFPA PDF in the manifest's raw paths.
# Use pdftotext -layout to create evidence/GSO_UNFPA_2019_LAYOUT.txt from the pinned PDF.
python scripts/audit-vietnam-census2019.py --project generated/vietnam-replay-new
python scripts/import-vietnam-census2019.py --project generated/vietnam-replay-new
node scripts/validate-country.mjs --project generated/vietnam-replay-new
node scripts/build-country.mjs --project generated/vietnam-replay-new
node scripts/verify-vietnam-census2019-output.mjs generated/vietnam-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `8a6709c517ac891d7f707bb5038a8b87a810a54b0fa0e4f84fa79b843020810c`, validator **0 errors/warnings**, site built, **5 direct-original/output cases** passed, `npm run check` **159 JavaScript/JSON** and `npm test` **218/218**. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, all 63 national comparison rows and source locators. Local browser at `127.0.0.1:4271` confirmed Viet Nam→Ha Noi→Viet Nam, including heading, URL and country count; Ha Noi local materials remained empty with national references in a separate section. These are producer checks, **not** 42-scenario or independent acceptance.

## Remaining before a complete Viet Nam edition

1. Acquire the NSO 26-table Completed Results original from an official endpoint; inventory every numeric field and district geography. Assess the joint report's other 59 numbered detailed tables by universe, sample basis, denominator, date and locality. Do not infer district values from province rows.
2. Acquire a dated official 2019 administrative code list and compatible polygons. Independently build current 2025 34-province/3,321-commune geography and a source-supported historical crosswalk. Assign current planning bodies only to current legal units.
3. Review the current Planning Law and Local Government Law by article, competent province/commune, plan period and official form. Obtain representative current plans, budgets, actual spending, implementation and evaluations, with issuers, content and approval separately checked.
4. Check other sector sources by VNM theme/year/grain, review source terms, complete applicable 42 scenarios, print/mobile/local-language and Word/PDF inspection, and independent `ACCEPT`. Assign VNM-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits each lead. It transfers no raw PDF, 576 observations or country acceptance. [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) records import and repository commits. **Local:** partial candidate. **GitHub:** scoped code, audit and source leads. **Hosting:** none. **Public:** none.

GitHub handoff: AreaData adapter `618ce6e8c127be582e466e1442a7272f8e7c3e14`, 442-source bundle `05b09d265079b960ec5a25061393bbca21b73b5f`, Kit import `065a07d1bf3c51dc2e2d296506801e7b0231fc28`. All were pushed to their respective `codex/asia-*` branches. The bundle SHA-256 is `43b06b0b87017c01bbe3a6086cb0aa8ccb07a56e5e55f79fcabc7757c0d9200d`.

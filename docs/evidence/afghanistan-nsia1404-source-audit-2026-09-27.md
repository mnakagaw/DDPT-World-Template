# Afghanistan NSIA 1404 source and adoption audit — 2026-09-27 JST

**Status: local partial candidate, not an accepted country edition.** The adopted release is an *estimate* for solar year 1404 / 2025–26, not a new census. It is kept separate from the World Bank WDI midyear population series. Original PDF and machine inventory remain in the ignored `generated/afghanistan-areadata-20260927/raw/` and `evidence/` directories; the reproducible inventory and importer are tracked under `scripts/`.

## Original and acquisition

| Item | Evidence and limit |
|---|---|
| Publisher, document | National Statistics and Information Authority (NSIA), [Estimated Population of Afghanistan 2025–26](https://nsia.gov.af:8443/wp-content/uploads/2025/09/%D8%A8%D8%B1%D8%A7%D9%88%D8%B1%D8%AF-%D9%86%D9%81%D9%88%D8%B3-%DA%A9%D8%B4%D9%88%D8%B1-%D8%B3%D8%A7%D9%84-1404.pdf), September 2025, 168 PDF pages. [EUAA's source list](https://www.euaa.europa.eu/coi-report-afghanistan-country-focus/public-sources) independently points to this exact NSIA URL. |
| Original | 18,549,385 bytes; SHA-256 `1ab39fdecc6d5eb3caba4e0ab89fa9199c581efc798c800f7a23f23160929d58`. PDF cover, preface, Table 4 pp31–32 and Table 76 p167 were inspected; selected pages were rendered. |
| Acquisition caution | Certificate-validating curl failed with `SEC_E_WRONG_PRINCIPAL`; an HTTP 200 PDF was saved with `curl --insecure`. Thus TLS peer identity was **not** verified. The EUAA link and internal PDF content support provenance but do not remove this transport gap. Reacquire through valid TLS or authenticated official mirror before independent acceptance. |
| Method | The PDF preface describes a population estimate based on the 2002–05 household listing and a 2004 base with exponential growth. It says no second full census followed 1979. A fixed 1.5 million nomadic estimate is included in the national figure. |
| Redistribution | Public official PDF located; explicit reuse and redistribution terms remain unverified. The raw PDF is ignored and is not committed. |

Initial `create-country.mjs` preflight was read before domestic adoption. Its 292 WDI national observations remain national-only and the 34 geoBoundaries 2007 ADM1 provider polygons were **removed** from this candidate: no official NSIA 1404 province-code or same-edition polygon correspondence is established.

## Complete numbered-table register and adoption boundary

`scripts/inventory-afghanistan-nsia1404.py` inventories the PDF's **76 numbered tables**, each first page, title, numeric-column *family* and adoption state in ignored `evidence/AFG_NSIA1404_TABLE_INVENTORY.csv`. It groups Table 1's age × residence × sex, Table 2's three-year age × sex, Table 3's zone/residence/sex, Table 4's nine year/sex counts, 34 province age/sex count-and-percent tables, 34 province administrative-unit × rural/urban/total × sex tables, Kabul city district/household/sex Table 7, ratios Tables 74–75 and household/population Table 76. This is **not** a complete cell-level semantic audit of the other 75 tables. Their adoption state is `priority_unassessed`, never zero or unavailable.

| Source fields and locator | Decision | Reason |
|---|---|---|
| Table 4 pp31–32, 1404/2025–26 female, male, both-sex counts; country, settled subtotal, 34 named province rows | **Adopt direct counts only**: three full-national values at Afghanistan root and three settled-only indicators at statistical-coverage scope plus 34 provinces, 108 direct observations | All 34 province female+male counts and all nine province→settled and settled+nomadic→national columns reconcile. Table 76 p167 independently matches the 34 adopted population rows. Each observation retains PDF page/row/column locator. |
| Table 4 pp31–32, 1402/2023–24 and 1403/2024–25 six count columns | `priority_unassessed` | Arithmetic was checked for parse safety, but definitions, historical comparability and independent table conflicts have not been semantically accepted. |
| Tables 1–3 and 5–75, other numeric groups | `priority_unassessed` | Age, residence, administrative-unit, city-district and demographic-ratio content can materially deepen the edition after source meaning, unit, geography and consistency checks. Do not infer nonexistence from Table 4 alone. |
| Table 76 p167, households and average household size | **Withheld** | The national household count 4,693,804 exceeds settled 4,494,826 plus nomadic 198,856 by **122**; 34 province household rows sum 4,796,874, **302,048 more** than its settled total. Population cells alone corroborate Table 4. |

Table 4 continuation p32 prints year headings 1401/1402/1403, unlike p31's 1402/1403/1404 and the 2025–26 province tables. The last population column was adopted only after its province figures matched Table 76. Table 2's 2024–25 national female/male values also differ by ±1 from Table 4; no historical field is adopted. Kandahar's wrapped Table 4 last cell is handled explicitly by the hash-pinned parser rather than silently accepting the PDF text layout's trailing row serial.

For 1404, Table 4 reports **36,435,197 full-national**, **34,935,197 settled in the 34 named provinces**, and **1,500,000 nomadic unallocated to provinces**. The national male/female counts are 18,582,499/17,852,698; settled male/female 17,790,216/17,144,981. Afghanistan's WDI 2025 midyear population is separately 43,844,111. No comparison, source, or parent value substitutes one series for the other.

The 34 province names and Table 4 serials are source row locators, **not official province codes**. A statistical settled-coverage scope sits below the country root; its 34 children cover the settled subtotal only. The single root child is explicitly labelled partial coverage, not a full-national aggregation. No area-compatible polygon or municipal geography has been adopted.

## Official planning and fiscal locations checked

| Official location | Disposition |
|---|---|
| [Kabul Municipality urban laws](https://km.gov.af/19134/urban-laws-and-regulations) | Catalogue of past law/gazette references; current legal effect and amendments unverified. Kabul city is not Kabul Province. |
| [Kabul annual development plans](https://km.gov.af/19100/annual-development-plans) and [city-plan portal](https://kmplan.km.gov.af/) | Catalogue and interactive location only. Visible annual plan years 1395–1400 are historical. Exact current plan body, boundary and approval unacquired. |
| [MUDH Herat city master-plan handover](https://www.mudh.gov.af/dr/%D9%85%D8%A7%D8%B3%D8%AA%D8%B1%D9%BE%D9%84%D8%A7%D9%86-%D9%88%D9%84%D8%A7%DB%8C%D8%AA-%D9%87%D8%B1%D8%A7%D8%AA-%D8%AC%D9%87%D8%AA-%D8%AA%D8%B7%D8%A8%DB%8C%D9%82-%D8%B1%D8%B3%D9%85%D8%A7-%D8%A8%D9%87-%D9%88%D8%A7%D9%84%DB%8C-%D9%87%D8%B1%D8%A7%D8%AA-%D8%AA%D8%B3%D9%84%DB%8C%D9%85-%D8%AF%D8%A7%D8%AF%D9%87-%D8%B4%D8%AF) | Announcement refers in its body to **Herat city** and handover to the governor. It is not evidence of a province-wide adopted plan. Plan document, legal effect, matching city boundary and finance are unacquired. |
| [Ministry of Finance budget-document catalogue](https://www.mof.gov.af/en/budget-document) | National document index; visible older years do not establish a current province/city budget or expenditure. |

The candidate's planning page holds these as references and presents plan, budget, implementation and evaluation as uncollected. Its generic planning HTML and evidence CSV are research outputs, not an Afghanistan official plan form.

## Reproducibility and unresolved acceptance

`python scripts/inventory-afghanistan-nsia1404.py --project generated/afghanistan-areadata-20260927` pins the PDF hash and verifies the selected cells; `python scripts/import-afghanistan-nsia1404.py --project ...` creates the dataset. The resulting dataset SHA-256 is in ignored `evidence/AFG_IMPORT_RESULT.json`. Validator, build, seven actual CSV/HTML/Markdown/planning-output cases and browser selection were checked on 2026-09-27 JST. The full 34-row comparison print table was checked for first/last row, count and sum. These are producer checks only.

Priority next: valid-identity reacquisition; Table 3/6–73 and ratios semantic audit, official current code/boundary correspondence and lower-level data; current competent planning bodies, plans and budget/implementation/evaluation by city/province; source terms, language/mobile/print and independent 42-scenario acceptance. **No hosting or public deployment has been authorized or completed for this country candidate.**

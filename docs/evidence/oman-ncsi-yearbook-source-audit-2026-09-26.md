# Oman NCSI yearbook source audit — 2026-09-26

Scope: **partial, unpublished** country candidate in ignored `generated/oman-areadata-20260926`. The generated `SOURCE_PREFLIGHT.md` had no Oman-specific pre-researched source. The original [NCSI Statistical Year Book 2026, issue 54](https://api.ncsi.gov.om/uploads/pdfs/statistical_year_book_2026___issue_54_1777963604.pdf) was acquired privately (17,012,041 bytes; SHA-256 `93a4fc2ba4b508ab5b01a7ec5de041529ff284d8ba1b3eab6fe1b0463196f9df`). The private receipt, full PDF, extracted text and `OMN_NCSI_YEARBOOK_FIELD_AUDIT.json` retain the replay evidence. Redistribution terms remain under review; the original is not committed.

## Original fields, adoption and reconciliation

| Original location | Numeric fields and decision |
|---|---|
| Table 7-2, PDF pp. 36–37 | All six numeric columns of this table were parsed: registered expatriate and Omani population at year end for **2025, 2024 and 2023**. It has **75 reporting rows**: Sultanate total, 11 governorates and 63 Wilayats. Thus **450 source cells** are directly adopted as two nationality indicators. Wrapped bilingual names were reconciled with page and row anchors. These are annual registration values, **not** 2020 eCensus counts or World Bank midyear estimates. |
| Table 6-2, PDF p. 34 | Published total population for the Sultanate and each of 11 governorates, for each of the three years, was used as an **independent 36-cell total cross-check**. No extra Table 6-2 observation was created. |
| Table 8-2, PDF p. 38 | Published 2025 national total **5,359,557** was checked as a second national anchor; its other columns and years were not adopted. |
| Other yearbook tables and fields | **Unassessed, unadopted.** The 346-page original is not marked `all_tables_checked`. A separate complete table/field inventory and semantic audit is required. |

Within each Table 7-2 row and year, AreaData adds the mutually exclusive Omani and expatriate counts into a **calculated** total. This creates **225 calculated observations**, labelled as such with both components in the output. The 2025 national row is **3,039,349 Omani + 2,320,208 expatriate = 5,359,557**. Its 2024 and 2023 totals are **5,268,072** and **5,165,602**. For **every** year and nationality column, Wilayat rows exactly sum to their published governorate row, and the 11 governorates sum to the published national row. The 36 calculated parent totals independently match Table 6-2. No rate or incomplete constituent subtotal is synthesized.

The candidate now contains **75 territories**, **three NCSI indicators**, **450 direct category observations** and **225 calculated totals**. Source locator includes PDF page, exact English row label, year and column. IDs use the governorate path plus Wilayat name to keep the two **Muscat** and two **Al Buraymi** rows distinct. These are AreaData source-qualified IDs, **not official administrative codes**. The 63 Wilayats are comparison members of 11 governorates; their presence does not identify a statutory plan maker.

The generator's seven 2023 geoBoundaries ADM1 reference shapes cannot cover the yearbook's 11 governorates. They were deliberately removed from this candidate's geometry rather than joined by name. No official polygon, code edition or boundary history was acquired. The yearbook's map cautions that its statistical limits are not official legal boundaries. The browser therefore shows a boundary gap while retaining selection, values and full member tables.

## Other official source locations

- [NCSI eCensus 2020 portal](https://www.ecensus.gov.om/): location only. Detailed local tables, code and boundary editions, definitions and terms were not acquired. Registration values are not relabelled as census values.
- [Ministry of Justice and Legal Affairs 2026 Urban Planning Law](https://mjla.gov.om/decrees/ar/1/show/1453) and [2022 Governorates System](https://mjla.gov.om/laws/ar/1/show/186): official locations only. Current consolidated provisions, commencement, lawful plan-making unit, obligation and local applicability have not been audited.
- [Ministry of Housing and Urban Planning national spatial strategy overview](https://oman.housing.gov.om/onss) and [projects catalogue](https://mohup.gov.om/en/projects): official locations only. No selected-area plan body, formal decision, budget, implementation or evaluation was adopted.

The cross-country candidates listed in `SOURCE_PREFLIGHT.md` remain `availability_not_checked_for_country`: location, acquisition, geographic reconciliation and indicator adoption are distinct statuses. The current three local indicators cover registered population only. Health, living conditions, education, employment and planning evidence remain country-specific collection tasks; the national World Bank series is displayed separately and never allocated to a Wilayat.

Next: inventory the remaining yearbook tables and eCensus datasets at field level, inspect definitions and temporal breaks, obtain official code/boundary versions, audit the current law and actual plans/fiscal/performance records for contrasting governorates and Wilayats, then complete the 42 scenarios and independent `ACCEPT`. Missing documents do not establish that plans are absent or unapproved.

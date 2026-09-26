# Jordan official-source audit — 2026-09-26

Status: **partial domestic candidate, not independent `ACCEPT`**. Original files and receipts are kept in the ignored country project at `generated/jordan-areadata-20260926/raw/official-jordan/`. The small [sheet and numeric-column ledger](jordan-dos-2025-sheet-inventory.json) records every sheet and numeric column in the three acquired Excel workbooks, including unadopted sheets. Counts and cell positions in that mechanical inventory are not a semantic audit.

## Acquired originals and source identity

| Original | Official location | Bytes | SHA-256 | Disposition |
|---|---|---:|---|---|
| `PopulationEstimatesbyLocality.xlsx` | [DoS 2025 locality/sex/household estimates](https://dosweb.dos.gov.jo/databank/Population/Population_Estimares/PopulationEstimatesbyLocality.xlsx) | 203,558 | `ebf49f985570c25de141a26c75fc70790a0f7225fb351b3ecd04b68402bd0ef8` | Summary sheet partially adopted. Twelve detailed governorate sheets unassessed. |
| `PopulationEstimates.xlsx` | [DoS 2025 population estimates](https://dosweb.dos.gov.jo/databank/Population/Population_Estimares/PopulationEstimates.xlsx) | 88,000 | `0917681306aa728e501464a8a42c0ec31ed81e66cf16245862ede53f007f7002` | Selected 2025 urban/rural, area and density fields adopted; other tables unassessed. |
| `Municipalities.xlsx` | [DoS 2025 municipality estimates](https://dosweb.dos.gov.jo/databank/Population/Population_Estimares/Municipalities.xlsx) | 157,842 | `3f880201fd685830e5c77f6505797a2bc91086412f72a758399dd4f92dda4b97` | Acquired and inventoried; no municipal value adopted or silently treated as an administrative district. |
| `YearBook_2024_Population.pdf` | [DoS Statistical Yearbook 2024 population chapter](https://dosweb.dos.gov.jo/databank/yearbook/YearBook_2024/Population.pdf) | 975,911 | `4ebf27354c51d95776b4b51cbd27a9b34a7cdb021ab31de55c8e56f981b90dea` | Acquired for historical comparison; tables unassessed and not adopted. |
| `GovernoratePlanningGuide.pdf` | [Ministry-hosted 2018 governorate planning guide](https://www.mola.gov.jo/ebv4.0/root_storage/ar/eb_list_page/guide_for_the_preparation_of_governorate_strategic_development_and_implementation_plans.pdf) | 6,862,512 | `ebb981db5b5afd468e3662461a0f84445732ab916b512d57f65ddd526efab85a` | 62-page Ministry of Interior guide; cover, contents and data-analysis sections inspected. It refers to the 2015 decentralization law and is not proof of current 2026 legal procedure. |
| `LocalAdministrationLaw2021.pdf` | [Ministry of Local Administration law PDF](https://mola.gov.jo/EBV4.0/Root_Storage/AR/EB_Info_Page/%D9%82%D8%A7%D9%86%D9%88%D9%86_%D8%A7%D9%84%D8%A7%D8%AF%D8%A7%D8%B1%D8%A9_%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%D8%A92021.pdf) | 22,257,005 | `715f73dc331e62764ee2ec7433ba06e402953ec706ac683df8f4e1f46d8569ac` | 53-page image PDF; title of Law No. 22 of 2021 visually checked. Article-by-article and amendment audit remains open. |

The [DoS 2015 census table catalogue](https://dosweb.dos.gov.jo/censuses/population_housing/census2015/census2015_tables/) and [Ministry of Interior governorate listing](https://moi.gov.jo/En/List/Governorates_and_Sectors) were located. A catalogue is not an acquired table or an adopted 2015 observation. The [Ministry planning archive](https://mop.gov.jo/EN/List/Governorates_Developmental_Map) lists governorate development map files; file dates, content, status and territorial coverage remain unassessed.

## Adopted cells and checks

| Source location | Meaning and result | Adoption |
|---|---|---|
| `PopulationEstimatesbyLocality.xlsx` / `الملخص ` / `B5:E117`, `B122:E122` | Male, female, source-reported total population, households. Twelve governorate, 49 ordinary district, 52 sub-district and one national row. Every B+C=D and every complete parent-child source sum checked. Nationwide D122 = **11,937,000**, E122 = **2,475,767**. | Four indicators for 114 territories. Rows 118–121 (Aqaba's two district centres and two qadaa) are held: the source does not present complete same-rank district parent rows. |
| `PopulationEstimates.xlsx` / `2.3` / `B27:C39` | Urban and rural source categories for 12 governorates and nation. B39 = **10,784,700**, C39 = **1,152,300**; B+C matches source population. Urban follows the source's locality threshold of at least 5,000, based on the 2015 census definition. | Two indicators for 13 territories. Table 2.2 B6:D18 is used to cross-check the locality summary, not a second adopted population series. |
| `PopulationEstimates.xlsx` / `2.7` / `E29:E41`, `G29:G41` | DoS-reported governorate/national area and population density. Source D population and D/E=G identities checked within workbook precision. National E41 = **88,793.512 km²**. | Two indicators for 13 territories. DoS area is not calculated from the geoBoundaries display polygons. |

These give eight distinct domestic indicators and **508 observations**. The annual 2025 DoS population estimate is based on the 2015 census; it is **not** a new 2025 enumeration. The national World Bank `SP.POP.TOTL` midyear series remains distinct (2025: 11,520,684). The Jordan screen labels DoS as the default population indicator and places both series in basic information with their own definitions.

## Territory and planning limits

The DoS summary establishes the parent ordering for the adopted rows. The 49 district and 52 sub-district IDs are provisional source-scoped IDs because their official codes and compatible boundary shapes have not been verified. The 12 governorate names were joined to **2006 geoBoundaries reference shapes by name** for navigation only. Neither this join nor the DoS table proves 2025 legal boundary equivalence. Aqaba's four held lower rows are retained in the private audit and never turned into a fabricated same-level comparison.

The 2018 guide describes governorate strategic plans, an annual implementation stage, data analysis, implementation and review. Its cited legal basis predates the acquired 2021 law. The current legal division of planning responsibilities, a verified current plan for Amman or another selected governorate, budgets, implementation and official evaluations are **unconfirmed**. No plan document or approval status is inferred from the guidance or the development-map archive.

## Verification and continuation

The importer pins source hashes, source sheet/row/column locators and source identities; it checks the source hierarchy, sex sums, urban/rural sums and area/density identity before writing the candidate. `validate-country` reports zero errors and one warning for missing verified country-specific planning documents. Local browser checks covered national → Amman → Jizah District → Jizah Sub-District → Amman, including selected value, heading and URL reset. CSV/HTML/Markdown diagnostics and planning/evidence outputs were generated and checked for representative national, governorate, district, sub-district and Aqaba cases; counts, first/last rows and hashes are in the ignored `evidence/OUTPUT_VERIFICATION.json`. This is an output check, **not independent acceptance**.

Next: audit every numeric field of the unadopted detailed locality, municipality and 2015 census tables; acquire official codes and a compatible boundary edition; review the 2021 law (the PDF is image-only) and actual selected-area plan/budget/implementation/evaluation documents; verify terms; complete `templates/COUNTRY_LESSON_AUDIT.md` and the 42 applicable acceptance scenarios with an independent `ACCEPT` decision before publication.

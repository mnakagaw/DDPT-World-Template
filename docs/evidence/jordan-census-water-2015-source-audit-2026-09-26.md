# Jordan 2015 census water-source Table 2.17 audit — 2026-09-26

Source: [Jordan Department of Statistics, Population and Housing Census 2015, Table 2.17](https://dosweb.dos.gov.jo/DataBank/Census2015/HousingUnits/Housing_2.17.pdf), eight-page PDF, 208,451 bytes, SHA-256 `266ed17dc71faabaedc308793556d0fdb56f62789bf21cfb20eb862924a8e88d`. The raw PDF, receipt and normalized 13-area × 10-category × 7-field table are in the ignored Jordan project. English source headings and numeric rows were extracted with Poppler; PDF pages 1 and 8 were visually checked. Each adopted observation records the physical PDF page, area, category and field.

## Full field and category disposition

The source has 13 areas (national plus 12 governorates). Each area has **nine mutually listed main-source categories** plus its Total row: Public Network, Filter at Home, Tank, Rain Water/ Well, Mineral Water (Filtered), Artesian Well, Spring, Others, Unspecified, Total. Each of the 130 rows has these seven numeric fields, **910 source numeric cells**. All cells are retained in the private normalized inventory and used for reconciliation, with these display decisions:

| Original numeric field | Source meaning | Decision |
|---|---|---|
| Persons / Collective Households | Persons residing in collective households, for each main-source category | Retained and checked as component; no separate indicator. |
| Persons / Private Households | Persons residing in private households, for each main-source category | Retained and checked as component; no separate indicator. |
| Persons / Total | Sum of preceding two person columns | Public Network and Total rows adopted as source-reported counts. Other eight category rows retained, not displayed. |
| Households / Collective | Collective household counts by main-source category | Retained and checked as component; no separate indicator. |
| Households / Private | Private household counts by main-source category | Retained and checked as component; no separate indicator. |
| Households / Total | Sum of preceding two household columns | Public Network and Total rows adopted as source-reported counts. Other eight category rows retained, not displayed. |
| Houseunits / Total | Occupied housing-unit counts by main-source category | Retained and checked; no indicator because a housing unit is not a household or person denominator. |

The importer checked, for **all 130 rows**, collective+private persons=person total and collective+private households=household total. For **every area and all seven fields**, the nine source categories sum to its Total row. For **every category and field**, the 12 governorates sum to the national row. Any failed identity stops the import. This is a complete numeric-field audit of **Table 2.17 only**, not of the other 2015 census catalogue tables.

## Adopted indicators and interpretation

For each national/governorate record, four source-reported counts are retained: public-network persons, all table persons, public-network households and all table households. Two **AreaData-calculated** percentages divide the public-network count by the corresponding source Total within the same area, year and unit. That gives six indicators and **78 observations**. No district or sub-district 2015 value is imputed.

| Area | Public-network persons / table persons | AreaData person share | Public-network households / table households | AreaData household share |
|---|---:|---:|---:|---:|
| Jordan | 5,435,650 / 9,453,124 | 57.501097% | 1,106,564 / 1,953,194 | 56.654075% |
| Amman | 2,079,505 / 3,952,251 | 52.615712% | 431,734 / 843,558 | 51.180120% |
| Aqaba | 174,074 / 184,889 | 94.150544% | 35,799 / 38,027 | 94.141005% |

The source counts **main source of drinking water** for persons and households in the table's occupied housing-unit universe. The PDF footnotes exclude hotels and collective housing units, 15,576 incomplete private households and 219 incomplete collective households. “Public Network” is a source category, **not** a tested safe-water, quality, continuity or access measure. Source person totals must not be presented as a new 2025 population estimate or silently compared with WDI's different population concept. The DoS 2025 annual population-estimate series and this 2015 census table have separate source IDs, periods, definitions and UI labels.

The source names were matched to the existing 12 governorate records; no official 2015 codes or legal boundary edition were supplied by this PDF. The polygon layer remains a **2006 geoBoundaries navigation reference by name** with an explicit warning, not a certified 2015 extent. Ministry of Health GIS service discovery was attempted but timed out; it supplied no adopted code or shape.

Representative browser checks: Amman territorial diagnosis shows **52.62%**, explicitly labelled “AreaData calculated”, with PDF page 1 numerator and page 2 denominator in the source note. Jordan thematic comparison shows **12/12** governorate observations for 2015 and a 57.50% national reference; no district value is invented. Full candidate source table and output hashes remain in ignored project evidence. The country edition is **partial, not independently accepted or published**.

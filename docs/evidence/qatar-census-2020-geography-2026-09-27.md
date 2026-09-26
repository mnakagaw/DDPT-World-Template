# Qatar Census 2020 historical geography: separate R2 candidate

Checked 2026-09-26 UTC. This update applies to the ignored local `generated/qatar-census-r2-20260927` candidate. The prior R1 candidate and its fixed independent audit are unchanged. This is a historical geography and planning-location update, **not** a full Qatar country acceptance or a public release.

## Official originals and crosscheck

The [Qatar GIS `Census_Zone_2020` layer](https://services.gisqatar.org.qa/server/rest/services/Vector/Census_Zone/MapServer/layers) exposes `ZONE_NO`, `MUNICIPAL_CODE`, municipality names and 91 zone polygons. The related 2020 zone population table reports male and female values for 90 zones. Zone 99 in Al Shamal has **null** male and female fields; neither is converted to zero or adopted as a zone observation. All eight sums of reported zone sex counts exactly match the eight municipality controls in [NPC Census 2020 Table 1](https://www.npc.qa/en/statistics/census2020/Pages/results/default.aspx); the national total remains the directly published 2,846,118. The [NPC detailed results PDF](https://www.npc.qa/en/statistics/census2020/results/Documents/Census_Final_Results.pdf) also locates the 2020 zone map.

The successful raw geography run is `raw/qatar-census-2020-geography/20260926T154810Z/manifest.json` in each local candidate. It has four independently hashed receipts: layer metadata `1214a7fdbe647251354282dfee9983bd9a91afd5283491b8096b47d5243460e8`, polygon GeoJSON `0dffd1905ddc0665b0bd492d0df7b872df241217f951d35a3738eb5fe3c54125`, zone population JSON `451bfb4c0f0a3173859c8e7824ed6a0485dc4e72294db5082085def20aef4e26` and QNMP page `252bc2538c7d00ff645a75f1524b1c402463b5af4c7f2ebb445fae2dfb355554`. The national workbook hash remains `bcca276482bab67b49d261f35903aa132df2888dfa1cc90c7cd3c753694cbe5a`.

`inspect-qatar-census-2020-geography.py` checks every polygon ID, coordinate ring, named municipality and 2020 sex-count control against the workbook. `derive-qatar-census-2020-boundaries.py` checks all 91 polygon topologies with Shapely 2.1.2 and dissolves zones within the same GIS layer into eight display polygons, without repair or simplification. No source area is lost to an overlap; no different municipalities overlap. The derived GeoJSON hash is `d19a7ec3893ca24e97d08581fa3fd932a47e36fa14390ca2a604be1a4c77b8a6`. This coordinate-space topology check does not determine legal area. The original, receipts, geographic audit, topology audit and derived file stay in the ignored candidate; large GIS originals are not committed.

R2 attaches the historical codes 1–8, `Census_Zone_2020` boundary edition and eight dissolved shapes to the same 2020 census municipality areas used by the 17 directly published indicators. It does **not** use current MunicipalityAT shapes, adopt zone-level population, infer a 2026 legal boundary or attach a spatial plan to the census geography. The 2020-to-current legal boundary/change register and GIS reuse terms remain open.

## Planning location and adoption limit

The [QNMP municipality-plan page](https://www.mm.gov.qa/QatarMasterPlan/English/MSDP-Municipalities.aspx?panel=about) says an MSDP was completed for each of eight municipalities. The [separate older zoning page](https://www.mm.gov.qa/QatarMasterPlan/English/msdp-zoning.aspx) names six municipalities and describes future extension for Al Khor and Al Wakra. These are different statements on different pages; neither establishes today's approved and operative edition, individual fiscal allocation, implementation or evaluation. R2 retains **zero adopted plan documents** and records the eight-plan page as a location lead.

## Candidate gates and replay

R2 has Qatar plus eight 2020 census municipalities, 8 display polygons, 17 direct domestic indicators and 153 direct national/municipality observations. The 12 WDI national series remain separate. Of 1,588 numeric workbook columns, 1,557 have not received semantic assessment. The dataset SHA, code commit and R2 checks are recorded in the local `evidence/DELIVERY.json` and `HANDOFF.md`.

Replay into a **new** project directory: create Qatar, copy the three successful source run directories with receipts, inspect the national workbook and import the exact selected cells, register official leads, inspect the historical geography, derive the polygons with Shapely, then adopt the geography. Validate, build and run the nine-area output verifier. The importer and geography adopter are single-use transformations. A new candidate must not overwrite R1 or R2.

R2 has not passed full-country independent acceptance. Current plans/finance, remaining census semantics, reuse terms, applicable 42 scenarios, downloaded-file bytes and physical print remain open. **Hosting/Public: not attempted.**

# Bahrain: official Census 2020 acquisition and partial country candidate

Checked 2026-09-26. Candidate: `generated/bahrain-census-r2-20260926`. **Partial, not independently accepted or published.** The generated country directory and raw originals are local/ignored. Reproducible collectors, source decisions and this record are tracked.

## Source and meaning

The [Information & eGovernment Authority open-data API](https://www.data.gov.bh/api/explore/v2.1/catalog/datasets?search=Census%202020&limit=100&offset=0) returned 514 search hits; 45 dataset titles expressly contain `Census 2020`. The collector acquired all 45 table bodies: 2,602 source rows in 56 paged JSON responses, 45 numeric fields, 2,598 numeric cells and four null cells. Of the 45 tables, 20 have a governorate dimension. The 45-table inventory and one-row-per-numeric-field register are in the candidate's `evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json` and `evidence/BHR_CENSUS_2020_FIELD_REGISTER.csv`; each raw response has a status, URL, timestamp and SHA-256 receipt under `raw/bahrain-census-2020/`. Current inventory SHA-256 is `5bc1d1fc5c794887da74b2df4a19d53705db4fbdb7da0f172e7c7bf9f85ad9bc`.

The 2020 census is described by [iGA as register-based](https://www.iga.gov.bh/article/al-qaed-highlights-igas-experience-in-producing-statistics-through-administrative-records-meeting-held-with-saudi-arabias-general-authority-for-statistics). This edition adopts **ten count indicators** from five official governorate tables: population total, male, female, Bahraini and non-Bahraini; housing units; all households and private households; school-enrolled persons aged 3+; and economically active persons aged 15+. Each of the 40 governorate indicator values is explicitly an **AreaData sum of mutually exclusive source cells**, with all source page and row locators. The full four-governorate cover permits a second, marked AreaData calculation of each national count. No direct source-observed national census row is stored in the dataset. Six other acquired tables provide source-cell crosschecks; their detailed categories are not adopted. The other 34 fields remain `priority_unassessed`, rather than silently accepted or rejected.

| Census measure | Four-governorate complete-cover control |
|---|---:|
| Population | 1,501,635 |
| Male / female | 942,895 / 558,740 |
| Bahraini / non-Bahraini | 712,362 / 789,273 |
| Housing units | 387,126 |
| All / private households | 245,983 / 228,972 |
| School-enrolled people aged 3+ | 309,557 |
| Economically active people aged 15+ | 875,558 |

Population by nationality groups independently reconciles the 16-cell base table; two private-household tables, school-stage detail, labor-status detail and national housing-type/occupancy table independently reconcile the selected counts. The imported 40 cells preserve their source table, dimensions, unit, reference year and calculated provenance. Four original null building/ownership cells are **missing**, not zero. The separately published [Ministry of Health 2020 demographic table](https://www.moh.gov.bh/Content/Files/Publications/statistics/HS2020/PDF/CH-02-census_2020-2.pdf) and the WDI midyear population series show 1,472,204 for 2020; this differs by 29,431 from the iGA Census 2020 portal count. The source frame/series and timing have not been reconciled, so the values remain separate and only the portal count enters the census indicator.

## Geography, plans and finance

The [2014 governorate amendment](https://www.lloc.gov.bh/Legislation/HTM/L5614) names Capital, Muharraq, Northern and Southern. Those names match the four Census 2020 reporting categories. The dated legal map annex, official area code register, 2020/2026 boundary editions and exact municipality crosswalk were not acquired. Four initial 2017 geoBoundaries provider shapes were removed from the candidate. Thus the geographic selector and tables work, while the map states that verified polygons are unavailable. The census reporting governorates are not automatically the legal plan authorities.

The [2002 Municipalities Law implementing regulation, Articles 36–39](https://www.lloc.gov.bh/Legislation/HTM/RCAB1602) locates municipal local-plan and budget provisions, including council and ministerial steps. The [1994 urban-planning law](https://www.lloc.gov.bh/Legislation/HTM/L0294) is a separate planning framework. Their operative consolidated September 2026 wording and amendments were not audited. The ministry identifies [four municipalities](https://mun.gov.bh/newportal/index.php/en/municipal-affairs/faqs?field_description_value=&field_sector_target_id=1&page=0); an [approved 2025–26 budget page](https://www.mun.gov.bh/newportal/en/municipal-affairs/approved-budget-fiscal-years-2025-and-2026) is a four-municipality aggregate location, not a verified allocation, execution record or official evaluation for any one municipality. The candidate contains zero adopted local plans and zero finance amounts. Its planning page labels missing references without inferring plan nonexistence or approval status.

## Reuse, output and acceptance boundary

The [iGA portal Terms of Use](https://www.data.gov.bh/pages/terms-and-conditions/) allow reuse subject to source and download-date attribution, identifying transformations as the user's work, their prescribed disclaimer and pass-through conditions. The source ledger contains links and retrieval dates and the screen labels calculated values. The full prescribed terms/disclaimer and any sublicensing flow are **not implemented or checked for external release**. Data stay in the ignored local candidate until that gate and country acceptance are closed.

Candidate R2 dataset SHA-256: `ec7f076ac69effcd5feae72a834561a877abcad3f02f2aebf76dd4f427eca776` at this checkpoint. It has five territories, zero polygons, 22 indicators, 352 observation records (40 domestic calculated-from-source-cell records and 312 distinct WDI national records), and zero planning documents. `validate-country` returned zero errors and one explicit no-local-planning-document warning; build and source-pinned five-area export verifier passed. `npm run check` and `npm test` (220/220) passed. Diagnostic CSV output has 110 rows for Bahrain and 22 rows per governorate, 198 rows total across five selected areas; source, period, ID and calculation provenance were checked for all ten domestic indicators. In the local browser, Bahrain displayed 1,501,635 and four of four comparable governorates, Capital displayed 548,345 as calculated and its national reference separately, and the planning page showed zero local materials. Selecting Capital and then Bahrain changed URL, title and selected-area values. Full printed pages, downloaded file bytes, all 42 applicable scenarios and independent country acceptance remain open.

Reproduce in a new empty directory:

```powershell
node scripts/create-country.mjs --country Bahrain --out <new-directory>
python scripts/collect-bahrain-census-2020.py --project <new-directory>
python scripts/inspect-bahrain-census-2020.py --project <new-directory>
python scripts/import-bahrain-census-2020-partial.py --project <new-directory>
python scripts/register-bahrain-official-source-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-bahrain-census-2020-output.mjs --project <new-directory>
```

The independent first/R2 acquisitions were compared with `python scripts/compare-bahrain-census-replay.py --first generated/bahrain-areadata-20260926 --second generated/bahrain-census-r2-20260926`: all 45 substantive source table bodies and all 40 `(area, indicator, period, value)` tuples matched. The first run predates the provenance correction, so its calculated classification is not a reference. Exact response metadata, WDI refreshes and retrieval times are excluded from semantic equality. An independent checker must review the fixed producer commit and dataset SHA before any `ACCEPT`. Next work: audit all remaining source fields and finer geography; reconcile legal code/boundary and municipality planning units; acquire individual approved plans, budgets, final accounts, implementation and evaluations; complete representative and exception area print/download scenarios and portal-term implementation. **Hosting/Public: not attempted.**

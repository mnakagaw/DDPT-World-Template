# Jordan country lesson audit — producer-side partial check

Based on `templates/COUNTRY_LESSON_AUDIT.md` and its 12 checks. Date: 2026-09-26. Candidate: `generated/jordan-areadata-20260926`; template branch `codex/asia-domestic-20260926`; final commit and dataset hash are recorded in the handoff and ignored `evidence/OUTPUT_VERIFICATION.json`. Windows local preview at 127.0.0.1:4179 was used. This producer check is **not** a separate independent audit or `ACCEPT`.

Representative areas: Jordan (national), Amman (governorate with nine districts), Jizah District (two sub-districts), Jizah Sub-District (leaf), Aqaba (held mixed-rank lower rows). The DoS 2025 annual estimate is distinct from a census and from the World Bank midyear series. Source originals, receipts and output files are in the ignored country project; public source hashes and cell disposition are in [the Jordan source audit](jordan-dos-2025-source-audit-2026-09-26.md).

| ID | Result | Evidence and next action |
|---|---|---|
| UA01 | 制約付き | Three Excel workbooks: every sheet and numeric column mechanically inventoried. Summary and selected 2025 fields semantically adopted. The seven numeric fields and ten categories of 2015 census Table 2.17 were fully reconciled; other detailed localities, municipalities and census catalogue tables remain unassessed. |
| UA02 | 制約付き | Seven official originals hash-pinned. DoS 2025 representative cells/hierarchy and 2015 Table 2.17 full category/field identities checked; 2024 yearbook and other 2015 thematic bodies not reviewed. |
| UA03 | 制約付き | Source row hierarchy checked: 12 governorates, 49 districts, 52 sub-districts. Official lower codes and matching current legal boundaries absent. Four Aqaba rows held. |
| UA04 | 制約付き | Fourteen domestic indicators, 586 observations: eight 2025 estimate indicators / 508 observations plus six 2015 water-source indicators / 78 observations. Sex, parent-child, urban/rural, density, all 2015 source category/field sums and selected ratio denominators checked. Other sectors remain unassessed. |
| UA05 | 制約付き | Browser: national → Amman → Jizah District → Jizah Sub-District → Amman; heading, selected population, URL and source labels followed. Jordan thematic 2015 water-source share showed 12/12 governorates; Amman planning page showed no selected-area documents. Full planning workflow and narrow viewport remain untested. |
| UA06 | 制約付き | Upper Amman reselection cleared Jizah Sub-District and restored 5,004,600, nine district rows and Amman URL. All indicator, memo and download paths still need full regression. |
| UA07 | 未実施 | No complete missing-area/indicator focus regression. |
| UA08 | 制約付き | DoS end-2025 estimates, WDI midyear 2025 and 2015 census water-source counts/shares separately labelled. Other 2015/2024 historical tables and complete thematic export audit remain open. |
| UA09 | 制約付き | 2018 guide and 2021 law acquired; 2021 articles/current applicability, selected-area plan, budget, implementation and evaluation unverified. |
| UA10 | 未実施 | No official current selected-area form or plan output mapping. |
| UA11 | 制約付き | Representative CSV/HTML/Markdown, planning HTML and evidence CSV generated; selected population and 2015 water-source share, year, source URL, locator, first/last rows, full internal population rows and 2015 missing lower-area rows checked. No adopted Word/PDF output or complete print inspection. |
| UA12 | 制約付き | Local raw replay and candidate validation completed; standard check/test and independent audit results belong in the handoff. No hosting or public edition. |

All 42 standard acceptance scenarios are **not completed**. The independent audit is **unperformed**. The candidate is **partial and unpublished**. The 2018 guide is not treated as proof of current local planning duty, and missing plans are not treated as non-existent.

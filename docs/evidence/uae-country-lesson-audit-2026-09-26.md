# UAE country lesson audit — producer-side partial check

Date 2026-09-26; branch `codex/asia-domestic-20260926`; ignored project `generated/united-arab-emirates-areadata-20260926`. This follows `templates/COUNTRY_LESSON_AUDIT.md` and is **not** an independent audit or `ACCEPT`. Source details are in [the FCSC/SCAD audit](uae-fcsc-scad-population-source-audit-2026-09-26.md); dataset and export hashes in private `evidence/OUTPUT_VERIFICATION.json`. Preview environment: Windows, Node 24, local in-app browser `127.0.0.1:4190` (viewport and network conditions not measured). No local official/user confirmed the workflow.

| ID | Result | Evidence, limitation and next action |
|---|---|---|
| UA01 | 制約付き | FCSC 48-page PDF p.9 population table: all four numeric year columns and seven emirates/total inventoried; only 2005 adopted. SCAD 2023 R1/2024 region table audited; 2024 emirate headline adopted. Other PDF pages, SCAD fields, UAE.Stat and other emirate sources remain unassessed. |
| UA02 | 制約付き | Two originals hash-pinned; FCSC p.9 visually checked. SCAD acquired HTML and its disclosure-rounding note verified. Full national census catalogue and other emirate statistical releases unresolved. |
| UA03 | 制約付き | Seven emirates matched by name to 2017 reference shapes; no official historic/current code-boundary equivalence. Three SCAD region IDs are provisional without polygons or legal-unit verification. |
| UA04 | 制約付き | Two distinct indicators / **15** observations: federal 2005 census eight; SCAD 2023 R1/2024 seven. Seven 2005 emirates sum to FCSC national; three 2024 regions sum to SCAD emirate headline. Other emirates have no SCAD values; 2023 emirate total not imputed. |
| UA05 | 制約付き | Browser checked national 2005 FCSC source and seven-emirate comparison; Abu Dhabi 2024 selection; three-region 2024 thematic comparison; planning/data page matrix incomplete. |
| UA06 | 制約付き | Dropdown selected Abu Dhabi Region, then reselected Whole Abu Dhabi; title, URL, 2024 SCAD indicator/period and parent population restored. Memo and every output route not browser-tested. |
| UA07 | 制約付き | Output verifier confirmed missing SCAD observation in national/Dubai and missing FCSC 2005 value in SCAD regions. Full focus/zero/missing UI regression unperformed. |
| UA08 | 制約付き | FCSC December 2005 census, SCAD 2024 registers, revised 2023 R1 and national WDI estimate are separately labelled. A same-method current seven-emirate comparison is unavailable. |
| UA09 | 未実施 | UAE government local-government/Dubai 2040 overview leads found; no selected-area plan, budget, implementation or evaluation document content-verified. |
| UA10 | 未実施 | Emirate-specific legal planning responsibility and current official output form not verified. |
| UA11 | 制約付き | Diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV verified for five representative area/period pairs with first/last rows, source locator and missing cross-series values. Word/PDF/whole-table print untested. |
| UA12 | 制約付き | Pinned raw replay, importer, country validation, build and representative export verifier passed. Standard check/test and Kit transfer belong in the handoff; no independent ACCEPT or public edition. |

The 42 standard acceptance scenarios remain incomplete. The local UAE candidate is **partial and unpublished**.

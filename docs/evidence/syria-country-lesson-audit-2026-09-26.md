# Syria country lesson audit — producer-side partial check

Date 2026-09-26; candidate `generated/syria-areadata-20260926` on `codex/asia-domestic-20260926`. This follows `templates/COUNTRY_LESSON_AUDIT.md` and is **not** the separate independent audit or `ACCEPT`. The ignored candidate `evidence/OUTPUT_VERIFICATION.json` records its exact dataset hash, representative export hashes, first/last CSV rows and environment date. Local preview was checked in the Codex in-app browser on Windows at `127.0.0.1:4181` (screen width and network conditions not measured). No Syrian local user confirmed the workflow.

Selection coverage: national, Homs governorate with six districts, Homs district with 12 sub-districts, Kherbet Tin Noor (PDF/XLS value conflict and leaf) and Damascus governorate (one district with a repeated name). [Source audit](syria-cbs2004-source-audit-2026-09-26.md) and [field ledger](syria-cbs2004-sheet-inventory.json) are the tracked numeric evidence.

| ID | Result | Evidence, limit and next action |
|---|---|---|
| UA01 | 制約付き | Three originals hash-pinned; all six XLS sheets and every column mechanically inventoried. Six census indicators semantically adopted. Other XLS columns, 6,135 locality rows, other census tables and current releases lack complete disposition. |
| UA02 | 制約付き | Archived CBS original PDF rows control adopted values; all population/sex arithmetic and 213 PDF/XLS mismatches retained. Source catalogue, current agency releases and lower housing meanings remain open. |
| UA03 | 制約付き | Source hierarchy 14 governorates, 61 districts, 270 sub-districts; P-codes only provider identifiers. 2017 ADM1 shapes are display references, without certified 2004/current legal code/boundary match or lower polygons. |
| UA04 | 制約付き | Six historical domestic indicators / 1,083 observations. Complete parent/child population and sex sums pass. National/governorate housing only; no lower housing carry-over or WDI/census rate blending. Other themes unreviewed. |
| UA05 | 制約付き | Browser checked national territorial/thematic, Homs governorate → Homs sub-district → Homs governorate, and Homs planning. The thematic page shows 14/14 observed 2004 governorates. Full page/viewport/locale matrix untested. |
| UA06 | 制約付き | Re-selecting Homs governorate after a sub-district restored its 1,529,402 population, six-district comparison, title and URL. Indicator/memo persistence and all outputs were not exhaustively browser-regressed. |
| UA07 | 未実施 | A full missing-area and missing-indicator focus regression is still needed. Housing at a lower area is mechanically checked as absent in output. |
| UA08 | 制約付き | 2004 CBS census and later WDI national series remain separately labelled, with no derived trend across them. Other source periods, themes and comparable definitions need review. |
| UA09 | 制約付き | Current official news provides a proposed local-planning method lead. Actual method, current legal planning duty, selected-area plan, budget, implementation and evaluation documents are unverified. The screen states 0/345 collected local material references rather than asserting plan absence. |
| UA10 | 未実施 | No verified area-specific official plan form, guide, planning report structure or human approval mapping. |
| UA11 | 制約付き | Diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV for five representative areas matched 2004 value, period, PDF URL/row, complete internal row counts and missing lower housing. Word/PDF and whole-table print quality were not checked. |
| UA12 | 制約付き | Pinned fetch replay, audit, import, country validation, build, export verifier and standard check/test are recorded in the handoff. No independent review, hosting or public edition. |

The 42 standard acceptance scenarios are **not all complete**. Current candidate status is **partial, unpublished**. Historical population availability does not close the current-statistics, official-geography or planning-document requirements.

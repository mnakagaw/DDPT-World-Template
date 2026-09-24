# Burkina Faso — 42-scenario acceptance ledger

2026-09-24 local review of AreaData template 0.12.1, dataset SHA-256 `53e2de7488ea6fd3657270006a858a609f80e3b3d969dcda2d129048c4681aa7`. Browser target: `http://127.0.0.1:4175/` (local only). Representative areas: Burkina Faso, historical Centre, Kadiogo, Komki-Ipala. This ledger uses the four statuses in `templates/ACCEPTANCE.md`; partial checks are recorded as evidence but do not make a scenario pass. The independent audit and public release are **not complete**.

| ID | Status | Evidence and remaining check |
| --- | --- | --- |
| A01 | 未実施 | National/Centre rendering inspected; full A→B→same-name/type→national sequence across all panels remains. |
| A02 | 未実施 | Planning route rendered; all adopted page transitions and target preservation remain. |
| A03 | 未実施 | URL contains target; share, legacy URL and browser history sequence remain. |
| A04 | 未実施 | Search of lower-ranked name/code and effect on comparison collection remain. |
| A05 | 未実施 | National and child maps inspected; filter/KPI/legend scope sequence remains. |
| A06 | 未実施 | Source years recorded in inventory; cross-page count and definition audit remains. |
| A07 | 未実施 | Schema distinguishes missing and zero; BFA UI cases for every state remain. |
| A08 | 未実施 | ADM3 geometry withheld; all missing-boundary/numerator cases remain. |
| A09 | 未実施 | Public national references exist; unauthenticated retrieval affordance and reason for unavailable local documents remain. No login workflow was adopted. |
| A10 | 未実施 | Generated Markdown/HTML/CSV content checked at four levels in `OUTPUT_QA.json`; browser download and print checks remain. DOCX/PDF/PNG are not adopted outputs, under `docs/PLANNING_DATA_CONTRACT.md`. |
| A11 | 未実施 | Reverse-response and failed-load simulation remains. |
| A12 | 未実施 | Saved notes/backup flow, if exposed by this build, remains to be exercised. |
| A13 | 未実施 | Long page navigation and complete print remain. |
| A14 | 未実施 | One national desktop screenshot inspected; matched baseline and duplicate-content review remain. |
| A15 | 未実施 | 1366/768/375/320 widths, actual 200% zoom and keyboard-to-download remain. |
| A16 | 未実施 | Full BFA localization review across pages and exports remains. |
| A17 | 対象外 | AI narrative generation is not adopted in the BFA project; no authenticated generation flow or generated text is offered. |
| A18 | 未実施 | Slow/offline background and source refresh failure remain. |
| A19 | 未実施 | Direct country values are separate from local totals; source-level reconciliation and overlap cases remain. |
| A20 | 未実施 | No Burkina Faso staff usability session has occurred. |
| A21 | 未実施 | Earlier actual Komki-Ipala→same Centre dropdown changed title/URL/map; all metrics, materials, exports and new dataset replay remain. |
| A22 | 未実施 | Same-region, another-region, parent-whole and national reset sequences remain. |
| A23 | 未実施 | History, reload, delayed child response and memo persistence after parent reselection remain. |
| A24 | 未実施 | Map-to-hidden-row, bottom-row and missing-row focus sequence remains. |
| A25 | 未実施 | Fourteen 2019 national/region pyramids checked numerically; missing-region switch and source/order visual check remain. |
| A26 | 対象外 | No optional water-background layer is adopted in this BFA build. |
| A27 | 未実施 | Common tests pass; BFA-specific old dataset and output regeneration remain. |
| A28 | 未実施 | Four national references and configured outputs render; section reorder/remove and `outputs: []` remain. |
| A29 | 未実施 | Historical geography is kept separate; adversarial mismatched-document rejection and parent clearing remain. |
| A30 | 未実施 | Four acquired national references have stage/hash records; all acquisition-state UI/output and invalid evidence rejection remain. |
| A31 | 未実施 | Source years are explicit; mixed document period/invalid interval cases remain. |
| A32 | 未実施 | No area-specific official status is asserted; adopted map meaning and unsupported-state cases remain. |
| A33 | 未実施 | No verified local plan, budget, result or evaluation body; real-content comparison cannot pass yet. |
| A34 | 未実施 | Raw replay matched observed values and planning config; failure/rollback/last-good preservation remains. |
| A35 | 未実施 | National screenshot shows top selector and map; reference comparison and narrow layout remain. |
| A36 | 未実施 | Regional values for seven new indicators checked; all themes, grain and map/table membership remain. |
| A37 | 対象外 | This local project provides the BFA country dataset only; world/continent group membership and cross-dataset handoff are outside this edition. |
| A38 | 未実施 | 351 census communes registered; legal/current municipality identity and stopping behavior remain. |
| A39 | 未実施 | Comparison map/table focus isolation and parent-change refresh remain. |
| A40 | 未実施 | No parent value is inferred from incomplete children; full comparability, boundary and legend edge cases remain. |
| A41 | 未実施 | Four-level generated output content checked; browser download, first/last/all rows and actual print remain. National HTML is about 9.7 MB. |
| A42 | 未実施 | Common tests pass; old URL/dataset, quick switch and parent reselect integration replay remain. |

Count: **0 合格 / 0 不合格 / 39 未実施 / 3 対象外**. A scenario with incomplete evidence is 未実施, not 合格. Required A01–A10, A13–A16 and A21–A23 are not accepted. Overall decision: **NOT ACCEPTED**. No independent auditor has reviewed this edition.

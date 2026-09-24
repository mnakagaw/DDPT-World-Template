# Burkina Faso diagnostic Word review 2026-09-24

Four **country-specific review artifacts** are in `generated/burkina-faso-20260924/exports/`: `Territorial Development Diagnostic.docx` for Burkina Faso and `Territorial Development Diagnostic - Centre.docx`, `- Kadiogo.docx`, `- Komki-Ipala.docx` for the three lower levels. They are local and ignored by Git because they embed acquired-source-derived data. Rebuild them with `scripts/country-burkina-faso/build-diagnostic-word.py`; inspect with `scripts/country-burkina-faso/check-diagnostic-word.py`. The AreaData website does **not** yet provide a live selected-area Word download, so A10 and A41 are not accepted.

| Check | Result |
| --- | --- |
| Selected areas | Burkina Faso, Centre, Kadiogo and Komki-Ipala in the historical 2019 census geography |
| DOCX SHA-256 | National `f1d1233bcb2cb003a3b26532cc1953ee6fa9bdb7e956207f3c927da09714c68e`; Centre `5ab5e4b355db9bd89f0387736f03f270b2f17fb7cc647c154115b1cdea5d1593`; Kadiogo `f6310076c7d4ad2ac03223eae46aa60f8c7ebbf07cb85b619421e331bca867fb`; Komki-Ipala `d8010119c3de3cc0fb413f4bc03d136e344565e0c977eaa68373ba4d423ea4d5` |
| Dataset SHA-256 | `53d17c6d10f60cdea5fcb8c317e43e37123c680a37d9af386875f9eb0715baa2` |
| Values | Seven Word table rows **per area** checked against `data/dashboard.json` for selected area, value, unit, year and source table; 2019 population and available age-band/sex sums checked |
| Visuals | National and Centre pyramids, lower-area broad age charts, and comparable-area population charts rendered. Four national and three pages per lower area were visually inspected. Centre's split table and orphan final line were corrected before final render. |
| Narrative | Deterministic text uses checked observations and labelled age-share calculations; distinguishes 2018 poverty model from 2019 census and keeps regional enrolment separate from the communal attendance measure. Causes, priorities, present legal territory and approvals remain unresolved. |
| Evidence files | Ignored `evidence/WORD_QA.json` plus three area-hash `WORD_QA-*.json` files and final `evidence/word-render-v2-{National,Centre,Kadiogo,Komki-Ipala}/page-*.png`. Original source PDF hashes remain in the ignored project. |

The document is **not** an approved development plan. It does not establish live browser download behavior, Word compatibility in every installation, municipal staff acceptance, or an independent audit. For final acceptance, compare the same selected territory and period in the live screen, diagnostic CSV, downloaded Word, and actual print output, including missing and edge-area cases.

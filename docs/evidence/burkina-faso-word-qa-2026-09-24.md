# Burkina Faso diagnostic Word review 2026-09-24

The adopted **country-specific review artifact** is `generated/burkina-faso-20260924/exports/Territorial Development Diagnostic.docx`. It is local and ignored by Git because it embeds acquired-source-derived data. Rebuild it with `scripts/country-burkina-faso/build-diagnostic-word.py`; inspect with `scripts/country-burkina-faso/check-diagnostic-word.py`. The AreaData website does **not** yet provide this file as a live selected-area download, so A10 and A41 are not accepted.

| Check | Result |
| --- | --- |
| Selected area | Burkina Faso (`BFA`), 2019 historical census geography |
| DOCX SHA-256 | `e63d04d2efe31a9f9f40d18c6882d90e8b96a89dedc0e973218d950a22b1e9f1` |
| Dataset SHA-256 | `53d17c6d10f60cdea5fcb8c317e43e37123c680a37d9af386875f9eb0715baa2` |
| Values | Seven Word table rows checked against `data/dashboard.json` for exact selected area, value, unit, year and source table; 2019 population and age-sex sum checked |
| Visuals | Population pyramid and historical regional comparison chart rendered; all four page PNGs visually inspected for clipping, missing glyphs, table splits and misleading labels. The comparison chart has room for the full value labels. |
| Narrative | Deterministic text uses checked observations and one labelled age-share calculation; distinguishes 2018 poverty model from 2019 census and leaves causes, priorities, current legal territory and approvals unresolved |
| Evidence files | Ignored `evidence/WORD_QA.json` and `evidence/word-render-final/page-1.png` through `page-4.png`. Original source PDF hashes remain in the ignored project |

The document is **not** an approved development plan. It does not establish live browser download behavior, Word compatibility in every installation, municipal staff acceptance, or an independent audit. For final acceptance, compare the same selected territory and period in the live screen, diagnostic CSV, downloaded Word, and actual print output, including missing and edge-area cases.

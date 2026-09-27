# Timor-Leste AreaData handoff — 2026-09-27 JST

**Status: INETL 2022 census / Díli and Ataúro partial candidate; independent `ACCEPT` pending; unpublished.** The Asia ledger is 0 complete, 36 partial, 1 research-only and 13 not started. Next unstarted priority by CSV order: Brunei Darussalam. Candidate: `generated/timor-leste-areadata-20260927` (ignored). No TLS-specific Hosting/Public destination is assigned.

## Evidence and decisions

- [INETL 2022 Census Main Report](https://inetl-ip.gov.tl/wp-content/uploads/2023/05/Final-Main-Report_TLPHC-Census_18052023-1.pdf) is acquired and hash-pinned. All 33 numbered tables are registered, but numeric-column and semantic review is complete only for selected columns in Tables 4.3, 4.11 and 4.12. These yield **15 reporting territories, 11 indicators, 135 directly reported cells and 30 same-row derived ratios**. Published total population is 1,341,737. The 4.11 age detail has 9 suppressed cells; none is reconstructed. Other 30 tables remain `priority_unassessed`.
- The census has 14 first-level reporting rows; [Law 19/2023](https://www.mj.gov.tl/jornal/public/docs/2023/serie_1/SERIE_I_NO_45_D.pdf) later distinguishes Ataúro, 12 municipalities and Oe-Cusse Ambeno. Official geography codes and matching 2022/2026 polygons are not acquired. Initial 2017 geoBoundaries 13 polygons were removed. The [2023 suco recognition Gazette](https://www.mj.gov.tl/jornal/public/docs/2023/serie_1/SERIE_I_NO_16_A.pdf) says 461 sucos, while the census reports 452 in 2022; the lower-level crosswalk is pending. Image-only Tables 4.1/4.2 are not imported. The Table 4.3 national sex ratio and national/Baucau gender totals conflict with Table 4.1, so sex indicators are withheld.
- [Municipal plan procedure 72/2024](https://www.mj.gov.tl/jornal/public/docs/2024/serie_1/SERIE_I_NO_49.pdf) and [Ataúro procedure 33/2025](https://www.mj.gov.tl/jornal/public/docs/2025/serie_1/SERIE_I_NO_38.pdf) are separate. Acquired [Díli PEDM 2026–2030](https://dili.gov.tl/wp-content/uploads/2026/02/Planu-Estratejiku-dezenvolvimentu-Munisipal-PEDM-DILI-2026-2030.pdf), [Díli 2026 Annual Action Plan](https://dili.gov.tl/wp-content/uploads/2026/02/PAA-2026-AM-Dili.pdf), and [Ataúro draft 2026–2030](https://atauro.gov.tl/wp-content/uploads/2026/02/Ezbosu_Planu-Dezenvolvimentu-Atauro-2026-2030_Final-Version-21-JANEIRU-26.pdf). Díli's PDF p.8 lists a **planned** US$19,502,642; this is not spending. Council of Ministers approval resolutions and full plan content have not been independently verified. Each local document appears only for its named jurisdiction.

[Detailed source audit](../../evidence/timor-leste-phc2022-source-audit-2026-09-27.md), [start sheet](../../evidence/timor-leste-country-start-2026-09-27.md), [Task Contract](../../evidence/timor-leste-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/timor-leste-country-lesson-audit-2026-09-27.md), and [tracked source manifest](../../../config/timor-leste-phc2022-source-manifest.json) define the boundary. The ignored candidate holds raw originals, table audit JSON, real output verification, and built site.

## Reproduce and inspect

Create a **new** candidate directory, download the manifest's eight official PDFs to each `raw_path`, and verify byte length/SHA-256. On source change, inspect the edition before updating the manifest/import contract. Python needs `pypdf`; Poppler `pdftotext` is used for tables. Do not replace a prior working candidate on acquisition/import/build failure.

```powershell
node scripts/create-country.mjs --country Timor-Leste --out generated/timor-leste-replay-new
# Download each manifest source to generated/timor-leste-replay-new/<raw_path>.
python scripts/import-timor-leste-phc2022.py --project generated/timor-leste-replay-new
node scripts/validate-country.mjs --project generated/timor-leste-replay-new
node scripts/build-country.mjs --project generated/timor-leste-replay-new
python scripts/verify-timor-leste-phc2022-output.py --project generated/timor-leste-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `9b5a0fb1f401e9cbfd53f77d0ff2e29efef170cf87efe6f75f7dc151714a36f9`; validator **0 errors/warnings**, build succeeded. Five cases ×11 indicators and five export types, plus national comparison 14 regions ×11 indicators=154 cells, are checked against source PDFs. Browser confirmed national→Díli→Ataúro→national selection, values, URL, geography-gap display, and jurisdiction-specific planning documents. `npm run check` passed **164 JavaScript/JSON** modules/templates and `npm test` passed **219/219**. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Timor-Leste edition

1. Inspect all 30 unselected report tables and full numeric columns, visually transcribe/check Tables 4.1/4.2 post/suco cells, and independently resolve the sex-count conflict without reconstructing suppressed age cells.
2. Acquire dated official codes, compatible polygons and a 2022→current crosswalk for first-level and lower-level geographies; verify post/suco coverage needed for municipal-plan internal diagnosis.
3. Verify each competent body's current procedure, Council of Ministers approval decision, own plan, budget, actual expenditure, implementation and evaluation. Inspect Díli/Ataúro full plans and any formal status separately.
4. Confirm reuse terms, applicable 42 scenarios, visual/print/mobile/performance/language/local-user checks, then obtain independent `ACCEPT`. Set TLS-specific Hosting/Public scope and verify deployed JSON plus rendered URLs only after acceptance.

Kit feedback transfers **official public locations and reuse cautions only** at `official_location_identified`, no PDF originals, observations, geographic join or country acceptance. **Local:** partial candidate. **GitHub:** code, audit and source leads committed and pushed. **Hosting:** none. **Public:** none. The two-repository exchange is recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md).

GitHub handoff: AreaData adapter/audit `3e0ab610903a40ded10a47802ab1a38497660649`, 493-source feedback bundle `8140f8a6dc8209602c17974d2978f538cfd78581` (SHA-256 `91f71334446381a9843d2d0bb5ef541c61979d9e4bb3afb9d7068842a8f4f314`), Kit import `5059d90206e2d2eea17ca37265b8b248416c283b`. All are pushed on their respective `codex/asia-*` branches. This final AreaData handoff record follows the adapter-bound bundle and does not change its `origin_commit`.

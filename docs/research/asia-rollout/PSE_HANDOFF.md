# Palestine AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; candidate `generated/palestine-areadata-20260926-pse` (ignored local directory). Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/palestine-pcbs2017-source-audit-2026-09-26.md) and [producer check](../../evidence/palestine-country-lesson-audit-2026-09-26.md) define the evidence limit. Private `dashboard.json` SHA-256 is `4e2803b1eb42161032629ccf53acfe6c21ad6e051fa95465890d9f9ac1276af8`; private originals, receipts, field inventory and output hashes remain in the candidate. Environment: Windows/PowerShell, Node 24, Python 3, Poppler, Codex in-app browser; date 2026-09-26. No Palestine hosting destination is configured.

## Replay

Read the new project's `evidence/SOURCE_PREFLIGHT.md` and JSON first. ISO3 `PSE` is the generator's resolved key; the display name is set from the PCBS original by the importer. A failed `--country "State of Palestine"` attempt in another ignored directory was preserved and must not be counted as a built edition.

```powershell
node scripts/create-country.mjs --country PSE --out generated/palestine-areadata-20260926-pse
python scripts/fetch-palestine-pcbs2017-sources.py --project generated/palestine-areadata-20260926-pse
python scripts/import-palestine-pcbs2017-census.py --project generated/palestine-areadata-20260926-pse
node scripts/validate-country.mjs --project generated/palestine-areadata-20260926-pse
node scripts/build-country.mjs --project generated/palestine-areadata-20260926-pse
node scripts/verify-palestine-pcbs2017-output.mjs generated/palestine-areadata-20260926-pse
npm run check
npm test
```

The generator rejects an existing destination. Fixed hashes prevent silently using a changed PCBS PDF. The importer replaces only its own source/indicator IDs and removes unverified 2021 reference local geometry. Original PDFs and private candidate are excluded from Git; reuse terms require review.

## Verified portion and limits

- PCBS updated 2017 census summary Table 2/29 contributes **606 territories**, **four indicators** and **1,837 direct observations**, including **585 coded localities**. National census population **4,781,248** includes a **75,393** post-enumeration estimate. The detailed-report counted population **4,705,855**, older-summary **4,780,978**, WDI midyear series and 2021-published projection series remain separate and unadopted for local comparisons.
- The 16 governorates directly cover two reporting regions. Fifteen governorates' locality rows fully cover their parent. Jerusalem J1 has only an aggregate; J2's 29 coded rows sum to J2. J1 + J2 equals Jerusalem governorate. No J1 locality observations are fabricated. Household observations stop at national/region/governorate level.
- Names from wrapped bilingual PDF rows were corrected. All 585 source codes are unique, sex components equal row total, and code/parent anchors are asserted on replay. Eight updated source codes are absent in the earlier May 2017 classification; legal geography and compatible polygons remain unverified. The 2021 geoBoundaries shapes are unjoined, so map absence is explicit.
- Browser checked national → West Bank → Jenin → corrected coded locality `010110` → Jenin whole. Heading, URL and source value followed the active selection, returning from **427** to **314,866** for the parent. Jenin thematic and planning pages kept its target; planning states **zero** collected selected-area documents. These are narrow producer checks, not all 42 scenarios.
- Twelve output cases generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Selected value, source locator, period, comparison first/last rows, counts and hashes matched. No full-table print, Word/PDF, responsive-width or final visual-layout audit was completed.

`validate-country` passed with zero errors and one material warning for missing verified country-specific planning documents. Build and output verifier passed. Standard AreaData check/test, Kit feedback and Git IDs are recorded in [KIT_FEEDBACK_HANDOFF.md](KIT_FEEDBACK_HANDOFF.md). Independent audit, Hosting and Public remain undone.

## Next work

1. Complete semantic audit of the other 27 updated-summary and 44 detailed-report tables and their numeric columns. Find newer official observation sources and treat pre-2023 projections separately from actual outcomes.
2. Obtain official PCBS/GeoMOLG code, boundary and version correspondence, including the eight code-guide gaps and Jerusalem J1/J2, and distinguish census localities from local-government and lawful planning units.
3. Acquire current applicable law/manual, selected-area actual plans and decisions, public budgets, implementation and official evaluation for contrasting West Bank, Jerusalem and Gaza cases. Keep document acquisition separate from formal plan status.
4. Close 42 acceptance scenarios, whole-table print, output layout, source terms and independent `ACCEPT` before hosting.
5. Continue the requested Middle East sequence. At this checkpoint Asia 50 = **0 ACCEPT, 13 partial, 1 research-only, 36 unstarted**; Middle East 19 = **0 ACCEPT, 11 partial, 1 research-only, 7 unstarted**. Next unstarted country: Oman.

Only code, evidence and status, not this private dataset or raw originals, are saved to GitHub.

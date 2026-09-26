# Syria AreaData continuation — 2026-09-26

Branch: `codex/asia-domestic-20260926`. Country project: `generated/syria-areadata-20260926` (ignored local output, separate from template). Producer result: **partial historical-census candidate**, not independent `ACCEPT`, not hosted/published. The tracked [source audit](../../evidence/syria-cbs2004-source-audit-2026-09-26.md), [all-column XLS ledger](../../evidence/syria-cbs2004-sheet-inventory.json) and [12-point producer check](../../evidence/syria-country-lesson-audit-2026-09-26.md) state the adoption boundary. Raw copies, receipts, row discrepancies and representative output hashes remain in this local country project.

Candidate `dashboard.json` SHA-256: `f7fcff2bbdff670337ae7e2a8af39abd4c363d0cde3eb3f530b8230a4113470b`. The ignored `evidence/OUTPUT_VERIFICATION.json` records this exact edition, export files and limitations. Environment: Windows/PowerShell, Node 24, Python 3 with `xlrd` and Poppler `pdftotext`, Codex in-app browser; date 2026-09-26. This candidate data edition is **not Git-published**. The audited importer/evidence commit is `fdcedd992c03099c5b87bd47db5995b34179bae2`; feedback bundle commit `f9bb915361da5f847ecdf040276e56ebd46a52b6`; Kit source-location import commit `2d5f93d5439ec4e5e9ab889ebc320df5426e34ce`. Both branches were pushed and their remote heads verified at those commits. See `KIT_FEEDBACK_HANDOFF.md` for transfer counts and cautions.

## Reproduce and verify

For a fresh directory, run `node scripts/create-country.mjs --country Syria --out generated/syria-areadata-20260926` and read its `evidence/SOURCE_PREFLIGHT.md`/JSON first. Then:

```powershell
python scripts/fetch-syria-census-2004.py --project generated/syria-areadata-20260926
python scripts/audit-syria-census-2004.py --project generated/syria-areadata-20260926 --public-output docs/evidence/syria-cbs2004-sheet-inventory.json
python scripts/import-syria-census-2004.py --project generated/syria-areadata-20260926
node scripts/validate-country.mjs --project generated/syria-areadata-20260926
node scripts/build-country.mjs --project generated/syria-areadata-20260926
node scripts/verify-syria-domestic-output.mjs
npm run check
npm test
```

The fetcher reuses only exact SHA-256 matches and stops on changed content. The raw files are ignored because source reuse/redistribution terms need review. The three imports are archived **original CBS PDFs** for values and a separate archived OCHA XLS for English names/P-codes. The latter is not a numeric source for adopted rows.

## Established evidence

- CBS 2004 census: national **17,920,844** people. Source counts cover 14 governorates, 61 districts and 270 sub-districts. Six indicators / **1,083** observations: population, male, female at all four levels; households, occupied and vacant dwellings at national/governorate only. This is **2004 historical** distribution, not current residents or a 2025/2026 census.
- The OCHA workbook's six sheets and every numeric column are inventoried. **213 numeric fields** conflict with CBS PDFs in 73 rows. The PDFs control: Homs district **1,035,055** versus XLS **1,035,438**, Kherbet Tin Noor **52,496** versus XLS **52,879**. Every adopted population/sex row and parent sum was reconciled to source PDF totals. No other XLS numeric columns were adopted.
- Source P-codes are treated as provider IDs. The 2017 geoBoundaries ADM1 polygons are name-matched navigation references, not certified 2004/current legal boundaries. No lower boundary polygons are joined. Old `cbssyr.sy` access returned 403; today's `cbssyr.org` homepage is not the historic CBS site.
- The browser showed 14/14 observed 2004 governorates in the thematic comparison, separate 2004 CBS and World Bank national series, PDF page/row citations, and the historical geography warning. Selecting Kherbet Tin Noor showed the PDF value **52,496**. Reselecting Homs governorate immediately restored its **1,529,402**, six district comparison rows and governorate URL. The Homs planning page correctly stated no *collected* selected-area planning references, without inferring no plan exists.
- The output verifier generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV for national, Homs governorate/district, Kherbet Tin Noor and Damascus governorate. Complete population internal rows: **14, 6, 12, 0, 1**; CSV total data rows: **270, 126, 234, 18, 36**. It checked the source PDF URL, 2004 period, page/row, relevant household counts and missing lower household counts. First/last rows and hashes are in the ignored evidence.
- `validate-country` passes with **one material warning**: no verified country-specific planning document collected. The 42 scenarios and independent `ACCEPT` have not been completed.

## Unclosed work

1. Locate current Syrian statistical releases, official territorial hierarchy/codes and boundary editions; obtain current local populations/sector statistics as available. A historical census cannot describe post-2011 displacement or today's local service demand.
2. Inspect unadopted CBS/OCHA fields and other original census tables semantically, resolve the 213 differing values and lower housing-row anomalies. Do not generalize the present three-PDF/XLS audit to the whole census catalogue.
3. Obtain the actual local-development planning method, current governing instruments, selected-area plans, budgets, implementation and official evaluations. The official 2025 news report describes a **proposal**; the 2026 Ministry of Finance citizen budget is only a **national** lead. Verify planning units and status before adaptation.
4. Verify raw reuse terms, all applicable 42 acceptance scenarios, complete print/Word/PDF output and an independent audit before any country hosting/public release. Kit feedback is source-location only and does not transfer candidate acceptance.
5. Continue the remaining Middle East countries in requested order while closing the above gates. At this checkpoint the Asia 50-country target is **0 ACCEPT, 8 partial, 1 research-only, 41 unstarted**. Middle East 19: **0 ACCEPT, 6 partial, 1 research-only, 12 unstarted**.

## Standard validation record

`npm run check`: pass, 136 JavaScript modules and JSON templates syntax-checked. `npm test`: **218/218 passed**. `validate-country`: 0 errors, one planning-document warning. Browser: local in-app preview at `127.0.0.1:4181`; no hosting or public URL. An independent audit has **not** accepted this country edition.

# Qatar AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/qatar-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/qatar-npc2020-source-audit-2026-09-26.md) and [producer check](../../evidence/qatar-country-lesson-audit-2026-09-26.md) delimit verification. Private `dashboard.json` SHA-256 at this check: `b0a7d3edb60067cfa2555d5ed6758bd8e324a6b04fef29ba6bae3fa9fd7695b6`. Originals, inventories, candidate and actual output files remain ignored. Environment: Windows/PowerShell, Node 24, Python 3 and local in-app browser; date 2026-09-26. No Qatar hosting destination is configured.

## Replay

Read generated `evidence/SOURCE_PREFLIGHT.md` and `.json` first. The generator refuses an existing directory; keep this candidate or use a fresh sibling. Acquire these exact official originals under `raw/npc-census2020/` before inventory/import; trusted TLS via `curl.exe` worked on this Windows host. Source updates that change pinned hashes require a new audit, not silent replay.

| Filename | Official source |
|---|---|
| `Census_Final_Results.xlsx` | [NPC main 2020 XLSX](https://www.npc.qa/en/statistics/census2020/results/Documents/Census_Final_Results.xlsx) |
| `Qatar_Census_2022_Final_Results.xlsx` | [NPC alternate 2020-content XLSX](https://www.npc.qa/Style%20Library/NPC/CensusDetailedResults/documents/Qatar_Census_2022_Final_Results.xlsx) |
| `Census_Final_Results.pdf` | [NPC 2020 PDF](https://www.npc.qa/en/statistics/census2020/results/Documents/Census_Final_Results.pdf) |
| `Al_Shamal_Dec_2017.pdf` | [Ministry historical strategy](https://www.mm.gov.qa/QatarMasterPlan/Downloads-qnmp/MunicipalityStrategy/English/Al%20Shamal%20Dec%20%202017.pdf) |

```powershell
node scripts/create-country.mjs --country Qatar --out generated/qatar-areadata-20260926
python scripts/inventory-qatar-npc-census2020.py --project generated/qatar-areadata-20260926
python scripts/import-qatar-npc-census2020.py --project generated/qatar-areadata-20260926
python scripts/audit-qatar-npc-census2020-fields.py --project generated/qatar-areadata-20260926
node scripts/validate-country.mjs --project generated/qatar-areadata-20260926
node scripts/build-country.mjs --project generated/qatar-areadata-20260926
node scripts/verify-qatar-npc2020-output.mjs generated/qatar-areadata-20260926
npm run check
npm test
node scripts/serve.mjs --dir generated/qatar-areadata-20260926/site --port 4198
```

The importer replaces its own ID prefix on replay; `generated_at` and dataset hash change but source values remain pinned. `pdftotext` is needed for the official Zone No. crosswalk. The Node server supplies correct `.mjs` MIME on this Windows host.

## Verified scope and limits

- The NPC/PSA 2020 main workbook has 209 sheets and an alternate URL has 206 common, cell-identical sheets. The alternate's filename `2022` is not a new census year. All **1,580 numeric columns / 36,209 numeric cells** of the fuller workbook are mechanically inventoried, 44 columns have selected adopted cells, and **144 of 156 numbered tables remain semantically unassessed**. Twelve selected tables supply **101 territories, 29 indicators and 522 observations** (495 source reported, 27 calculated).
- The PDF lists eight municipalities and **92 Zone Nos**; XLSX Table 2 reports population for 87. Five Doha zones (10, 11, 19, 60, 62) lack a row and stay missing. Census national **2,846,118** and all municipality/Zone population-sex sums reconcile. Municipality code edition and 2020-compatible polygons are unacquired; 2015 reference shapes are unjoined. WDI midyear population remains a separate series.
- Browser checked Qatar → Doha → Zone 10 → Doha whole, Al Shamal thematic focus on Doha while Al Shamal stayed selected, and Al Shamal planning. A generic territorial page fix keeps the active metric card visible when a valid selected area lacks an observation. The 2017 Al Shamal strategy is shown as a historical reference with `body_acquired` and institutional state `unverified`; present full MSDP and fiscal/evaluation content are not claimed.
- Fourteen actual output cases checked diagnostic CSV/HTML/Markdown and planning HTML/evidence CSV, including values, provenance, source locators, periods, missing versus true zero, full comparison membership and first/last printable rows. The Al Shamal output exposes the 2017 historical reference and unverified state. The 42-scenario suite, rendered print PDF, narrow-width and human-user checks remain incomplete.

Country validation passed with zero errors/warnings; build and 14-case verifier passed. AreaData `npm run check` checked 145 JavaScript modules and JSON templates; `npm test` passed **218/218**. No independent audit, Hosting or Public was done.

## Next work

1. Semantically classify the other 144 numbered NPC tables and all unselected cells by concept, population, year, geography and reuse. Prioritize useful local health, education, labour and service fields; keep raw and adopted universes separate.
2. Obtain the official municipality code edition, a matching 2020 municipality/Zone polygon layer and its reuse terms; verify code and boundary version before joining. Five unreported Zone populations stay missing.
3. Audit current QNDF/MSDP legal status, all eight current municipality strategies, zoning regulations/maps, revisions, plan decisions, budgets, execution and official evaluations. Verify whether the 2017 Al Shamal strategy is still operative; do not apply it as a current full plan. Retain Zones as internal diagnosis, not independent municipality planning authorities.
4. Complete applicable 42 scenarios, long-table rendered print and document layout, source terms and independent `ACCEPT` before any hosting.
5. Continue the user-requested Middle East priority order. With Qatar counted as partial, Asia 50 has **0 ACCEPT, 17 partial, 1 research-only, 32 unstarted**; Middle East 19 has **0 ACCEPT, 15 partial, 1 research-only, 3 unstarted**. Next unstarted priority: Armenia.

Only code, source leads, evidence and status are saved to GitHub. The AreaData→Kit source feedback is recorded separately in [the Kit handoff](KIT_FEEDBACK_HANDOFF.md) after transfer; Kit must independently assess originals before adoption.

# Armenia AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/armenia-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/armenia-armstat2022-source-audit-2026-09-26.md) and [producer check](../../evidence/armenia-country-lesson-audit-2026-09-26.md) delimit verification. Dataset SHA-256 at this checkpoint: `8c6ec513e6a1b74a8cfcb2ab66ba9f3c767540aa496be6826d9d76205d663f1c`. Environment: Windows/PowerShell, Python 3.14, Node 24 and local in-app browser; date 2026-09-26. No Armenia hosting destination is configured.

## Replay

The initial country generator's `evidence/SOURCE_PREFLIGHT.md` and `.json` were read. `create-country` refuses an existing directory; reuse this ignored candidate or generate a fresh sibling. Acquire the nine official `https://armstat.am/file/article/section_1.7z` through `section_9.7z` archives under `raw/armstat/`, and extract each archive to `raw/armstat/section_N/` with 7-Zip. The originals' hashes and each numeric-column disposition are in ignored `evidence/ARM_ARMSTAT2022_SOURCE_INVENTORY.json`. Obtain the official HTML sources at the exact URLs below under the exact filenames; the importer pins the three ARLIS hashes and the inventory pins the adopted XLSX hashes. Changed originals require a new audit rather than silent replay.

| Local file under `raw/armstat/` | Official URL |
|---|---|
| `arlis-territorial-classifier-2025.html` | [2025 HD 002-2021 incorporation](https://www.arlis.am/hy/acts/208945) |
| `arlis-local-self-government-2026.html` | [Local Self-Government Law](https://www.arlis.am/hy/acts/231070) |
| `arlis-ashtarak-decision-194-N.html` | [Ashtarak Council Decision N 194-N](https://www.arlis.am/hy/acts/173115) |

```powershell
node scripts/create-country.mjs --country Armenia --out generated/armenia-areadata-20260926
python scripts/inventory-armenia-armstat-census2022.py --project generated/armenia-areadata-20260926
python scripts/import-armenia-armstat-census2022.py --project generated/armenia-areadata-20260926
node scripts/validate-country.mjs --project generated/armenia-areadata-20260926
node scripts/build-country.mjs --project generated/armenia-areadata-20260926
node scripts/verify-armenia-armstat2022-output.mjs generated/armenia-areadata-20260926
npm run check
npm test
node scripts/serve.mjs --dir generated/armenia-areadata-20260926/site --port 4199
```

The census importer replaces its own IDs on replay and avoids duplicate sources/collection notes. `retrieved_at`, `generated_at` and candidate hash change when replayed; adopted source cells and pinned original hashes must not. The direct Ashtarak plan PDF timed out and is intentionally absent from this replay.

## Verified scope and limits

- ArmStat's nine English chapter archives contain nine narrative DOCX and **57 Excel workbooks / 58 worksheets** after excluding a 165-byte Office lock file. The inventory records **837 numeric columns / 42,403 numeric cells including headers**. Only selected 2022 D/G/J cells in Chapter 1 Tables 1.1.1/1.1.2 were semantically adopted: **94 territories, six indicators, 564 direct observations**. The other 55 workbooks and unselected fields remain unassessed. National usual residents **2,932,731** and present population **2,689,438** are separate from WDI midyear estimates.
- The official 2025 classifier supplies ten marzes, Yerevan, 12 Yerevan districts and 70 marz communities. Complete selected source rows and 70 official code matches are in the ignored crosswalk. The narrative says 72 communities while table/classifier imply 71 including Yerevan; 2022-to-2025 boundary equivalence is unverified. Shirak Table 1.1.1 male/female marz values differ by **+2/-2** from their six child sums; source values are retained. No official matching polygons were joined; 2005 reference shapes remain unjoined.
- The current law distinguishes community five-year plan, annual plan and budget. Ashtarak's 2022–2026 plan approval has an acquired council decision, but the municipality PDF body is only a verified link. Its chapters, revisions, budget and execution are not adopted. Other community planning material is uncollected.
- Browser checked national → Aragatsotn → Ashtarak and Ashtarak → Aragatsotn whole through the native parent selector, the Ashtarak planning page, and Shirak thematic focus while Aragatsotn stayed selected. Nine real output cases checked diagnostic CSV/HTML/Markdown and planning HTML/evidence CSV, source values/cell locators, selected IDs, full internal row counts and printable first/last rows. Rendered print, narrow widths, Armenian user review and full 42 scenarios remain undone.

Country validation passed with **zero errors and eight source-terms warnings**; build and nine-case verifier passed. `npm run check` checked 146 modules/templates and `npm test` passed **218/218**. No independent audit, Hosting or Public was done. The public-source Kit feedback selection is capped at `official_location_identified` until independent audit; Kit must begin each lead as `not_acquired_by_kit_preflight`.

## Next work

1. Semantically classify remaining census fields by year, universe, unit, geography and source corrections; assess local services, education, housing, migration and health without promoting every numeric column.
2. Obtain the dated official marz, community and Yerevan district polygons, reuse terms and 2022/2025 crosswalk; resolve the 72/71 narrative/table difference and Shirak ±2 source issue.
3. Acquire and inspect Ashtarak's full plan PDF and later amendments, then representative community annual plans, budgets, execution and evaluations. Distinguish Yerevan's legal provisions and lower diagnostic districts.
4. Complete applicable 42 scenarios, rendered print, accessible/mobile widths, source terms and independent `ACCEPT` before any hosting.
5. Continue the requested Middle East priority order. With Armenia counted as partial, Asia 50 = **0 ACCEPT, 18 partial, 1 research-only, 31 unstarted**; Middle East 19 = **0 ACCEPT, 16 partial, 1 research-only, 2 unstarted**. Next unstarted priority: Bahrain.

Only code, source leads, evidence and status are saved to GitHub. The originals, inventory, candidate, crosswalk and output files stay ignored. Commit IDs and Kit import verification are recorded in [the Kit handoff](KIT_FEEDBACK_HANDOFF.md) after the feedback loop.

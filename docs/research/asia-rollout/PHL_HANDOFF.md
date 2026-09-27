# Philippines AreaData handoff — 2026-09-27 JST

**Status: local POPCEN partial candidate, independent `ACCEPT` pending, unpublished.** After this candidate the Asia ledger is 0 complete, 29 partial, 1 research-only and 20 not started. Next unstarted priority: Cambodia. The separate ignored project is `generated/philippines-areadata-20260927`; code, source manifests, source audit and producer validation are tracked. No Philippines Hosting/Public destination is assigned.

## Evidence and decisions

- The official PSA 2024 POPCEN Table A national I7 and Table B all 18 regional sheets yield **1,744 reporting territories and 1,744 direct 2024 population observations**, including country population **112,729,484**. The 18 region values total **112,727,776**; Table A says the **1,708** difference is Filipinos at diplomatic missions abroad. All 101 2024 reporting parent/child sums match.
- 2024 Q2 PSGC identifies 18 regions, 82 provinces, 149 cities, 1,493 municipalities and 42,004 barangays. Table B has one additional non-LGU SGA subtotal with no PSGC code; eight municipalities under it have Q2 codes. Ten named exceptions record recast historical 2020 values or labels. Sulu is retained under 2024 BARMM. No 2024-compatible official polygon is acquired, and stale geoBoundaries ADM1 shapes were removed.
- The 30 PSA originals and six DILG/Quezon City PDFs have tracked URL/byte/hash manifests. All 26 XLSX original workbooks and 161 sheets were inspected for numeric columns, generating 329 sheet-column inventory entries. Only Table A/B 2024 population is adopted. Table C primary 119 sheets contain 43,750 numeric D-column cells, but barangay code/total reconciliation is still `priority_unassessed`; historical population/PGR and further census topics also remain unassessed.
- RA7160 §106/109/114 defines LGU local planning context, with a 502-page DILG guide acquired but not fully audited. Quezon City PSGC `1381300000` is the only locality with attached documents: CDP 2026–2031, LDIP 2027–2029, FY2026 AIP resolution and CY2026 budget ordinance. Official council records identify CDP adoption SP-10311 S-2025, LDIP adoption SP-10515 S-2026, AIP adoption SP-10255 S-2025 and budget ordinance SP-3465 S-2025. The AIP **PHP 56,902,941,000** and budget **PHP 43,300,000,000** are different measures; neither is expenditure or official evaluation. LDIP resolution body and full plan/fiscal contents remain unassessed.

[Source audit](../../evidence/philippines-popcen-source-audit-2026-09-27.md), [start sheet](../../evidence/philippines-country-start-2026-09-27.md), [Task Contract](../../evidence/philippines-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/philippines-country-lesson-audit-2026-09-27.md) set the evidence boundary. The ignored project holds originals, full workbook/row/column audit, import result and actual-output hashes.

## Reproduce and inspect

Start from a **new** country directory. PSA attachments must first be downloaded through their official release pages in a browser; CLI access to those attachments returned Cloudflare 403 during this run. Download files are named in `scripts/archive-philippines-popcen.py`. Existing raw originals can be copied from the current ignored candidate only when their pinned hashes match. Do not write over a working candidate on failure.

```powershell
node scripts/create-country.mjs --country Philippines --out generated/philippines-replay-new
python scripts/archive-philippines-popcen.py --downloads-dir <browser-download-dir> --project generated/philippines-replay-new
python scripts/fetch-philippines-planning.py --project generated/philippines-replay-new
python scripts/audit-philippines-popcen.py --project generated/philippines-replay-new
python scripts/import-philippines-popcen.py --project generated/philippines-replay-new
node scripts/validate-country.mjs --project generated/philippines-replay-new
node scripts/build-country.mjs --project generated/philippines-replay-new
node scripts/verify-philippines-popcen-output.mjs generated/philippines-replay-new
npm run check
npm test
```

Producer run: validator **0 errors/warnings**, site built, ten direct-original/output cases passed, `npm run check` **157**, `npm test` **218/218**. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, all comparison rows, and document scope. Browser at `127.0.0.1:49800` confirmed national→NCR→Quezon City→the same NCR whole-area reselection and removal of QC documents after selecting NCR. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Philippines edition

1. Reconcile the Table C barangay lines, hierarchy, duplicates and 2024 PSGC codes; audit remaining census/sector tables by original definition, denominator and location. Resolve Imelda/Payao 2020 differences and other historical recasts before any time series.
2. Acquire dated official 2024 statistical/legal polygons and verify their exact codes, NIR/SGA, Cotabato/Maguindanao and Makati/Taguig boundary editions. Keep region and SGA statistical reporting separate from LGU planning authority.
3. Audit current planning law and guide revisions, the full QC CDP/LDIP/AIP/budget content and LDIP resolution body, plus representative province, component city, municipality and barangay plans, annual budgets, actual expenditure and official evaluation.
4. Complete applicable 42 scenarios, missing/edge cases, local language, mobile/print, Word/PDF outputs and independent `ACCEPT`. Assign Philippines-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits the leads. It transfers no raw originals, observations or country acceptance. The AreaData adapter/selection commit `fcf87211cad097c3501f980e28dd043d126f57ba`, 423-source export commit `c75953e5ed94455298838bdc97835de5bc56f0a0`, and Kit import commit `ec756368f3a558dffc4371bc1d1ff071b79c2591` were pushed and their remote branch heads verified. The export carries the adapter commit as `origin_commit`; [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) records the 44 new Philippines leads and Kit validation. **Local:** partial candidate. **GitHub:** scoped code, audit and source leads pushed. **Hosting:** none. **Public:** none.

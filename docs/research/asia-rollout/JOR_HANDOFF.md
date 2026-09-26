# Jordan AreaData continuation — 2026-09-26

Branch: `codex/asia-domestic-20260926`. Country project: `generated/jordan-areadata-20260926` (ignored local output, separate from the template). Producer result: **partial domestic candidate**, not independent `ACCEPT`, not published. [Source audit](../../evidence/jordan-dos-2025-source-audit-2026-09-26.md), [numeric-column ledger](../../evidence/jordan-dos-2025-sheet-inventory.json) and [12-point producer check](../../evidence/jordan-country-lesson-audit-2026-09-26.md) are tracked. The original files, receipts, crosswalk, full source inventory and output checks are retained inside this local country project.

## Reproduce and validate

Start from an already generated Jordan project or run `node scripts/create-country.mjs --country Jordan --out generated/jordan-areadata-20260926` in a fresh checkout. The initial `evidence/SOURCE_PREFLIGHT.md` and JSON must be read before adoption. Then:

```powershell
python scripts/fetch-jordan-official-sources.py --project generated/jordan-areadata-20260926
python scripts/audit-jordan-population-workbooks.py --project generated/jordan-areadata-20260926 --public-output docs/evidence/jordan-dos-2025-sheet-inventory.json
python scripts/import-jordan-population-2025.py --project generated/jordan-areadata-20260926
node scripts/validate-country.mjs --project generated/jordan-areadata-20260926
node scripts/build-country.mjs --project generated/jordan-areadata-20260926
node scripts/verify-jordan-domestic-output.mjs
npm run check
npm test
```

The fetch script skips files whose pinned SHA-256 already matches. A changed upstream body is a **stop** requiring re-audit, not an automatic update. Raw files and receipts are not committed because redistribution terms remain under review. The importer writes source-scoped provisional district/sub-district IDs and a source row/cell crosswalk. It retains 2006 geoBoundaries governorate shapes as display references only.

## Current evidence and checks

- Eight DoS domestic indicators, **508** source observations; national plus 12 governorates, 49 districts and 52 sub-districts have four summary indicators. Urban/rural, DoS area and density are national/governorate only.
- National DoS end-2025 population: **11,937,000**; Amman: **5,004,600**; Jizah District: **147,365**; Jizah Sub-District: **130,085**; Aqaba: **250,900**. These are annual estimates based on the 2015 census. The separate World Bank 2025 midyear national series is **11,520,684**.
- Every adopted row passed male+female=total; complete adopted parent sums, Table 2.2/Table 2.3 reconciliation and density identity passed. Four mixed-rank Aqaba lower rows remain in the private audit but are not mapped as comparable children.
- Browser navigation was checked for national → Amman → Jizah District → Jizah Sub-District → Amman. Direct Amman reselection cleared the lower selection and restored the governorate heading, URL and **5,004,600** population with nine district comparison rows.
- Output verifier checks diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV for national, Amman, Jizah District, Jizah Sub-District and Aqaba. Population internal-row counts: **12, 9, 2, 0, 0** respectively; diagnostic CSV total data rows: **260, 200, 60, 20, 20**. It writes `evidence/OUTPUT_VERIFICATION.json` with hashes, first/last data rows and limitations.
- `validate-country` passes with one warning: no verified country-specific planning documents collected. This warning is material, not a publication waiver.

## Unclosed work

1. Inspect all unadopted numeric fields in the detailed locality and municipality workbooks, 2024 yearbook and 2015 census thematic tables. Municipality and administrative district identities must stay separate.
2. Obtain official administrative codes, hierarchy and boundary edition; do not treat 2006 geoBoundaries shape/name matching as 2025 legal geography. Resolve the Aqaba mixed-rank parent rows without guessing.
3. Review the image-only 2021 Local Administration Law No. 22 and later amendments. The acquired 2018 governorate planning guide cites the older 2015 decentralization law. Verify current planning units, applicable guide/forms, and actual governorate/municipal plans, budgets, implementation and official evaluations.
4. Check source reuse/redistribution terms, all 42 applicable acceptance scenarios, every planned output format and independent `ACCEPT` before any hosting/public release.
5. Continue Middle East work with Syria and the remaining 13 unstarted countries, while closing existing partials. The Asia 50-country goal is **0 ACCEPT, 7 partial, 1 research-only, 42 unstarted** at this checkpoint.

## Source feedback and repositories

Six Jordan public official-source leads were added to `config/kit-source-feedback-selections.json`: three DoS 2025 workbooks, the 2015 census table catalogue, the 2018 governorate guide and the 2021 law. The export stage is capped at `official_location_identified` until Kit independently audits each source. Record the AreaData and Kit commits and any import result in `KIT_FEEDBACK_HANDOFF.md`; a feedback import never changes the Jordan country acceptance status.

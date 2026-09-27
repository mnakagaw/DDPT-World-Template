# Cambodia AreaData handoff — 2026-09-27 JST

**Status: local NIS 2019 census partial candidate, independent `ACCEPT` pending, unpublished.** After this candidate the Asia ledger is 0 complete, 30 partial, 1 research-only and 19 not started. Next unstarted priority: Vietnam. The separate ignored project is `generated/cambodia-areadata-20260927`; tracked code, source manifest, audit and producer validation allow a new candidate to be rebuilt. No KHM Hosting/Public destination is assigned.

## Evidence and decisions

- The [NIS 2019 final report](https://nis.gov.kh/nis/Census2019/Final%20General%20Population%20Census%202019-English.pdf) directly reports all-person population **15,552,211** in Table 2.1.1 and normal/regular-household population **15,184,511** in Appendix PT 01. They are separate denominators. The latter P-table scope supports province/district/commune reporting; WDI is a separate national series.
- A 304-page PDF and NCDD Gazetteer HTML are hash-pinned. The 25 P tables contain 202 district and 1,646 commune rows plus 74 province Total/Urban/Rural subtotal rows, six numeric columns each. Selected-table inventory has 467 entries, including 11,532 P-table numeric cells. Other report headings remain unassessed.
- The partial site has **1,874 statistical reporting areas, nine NIS indicators and 11,301 direct NIS observations**. The report overview's 204 intermediate units versus 202 P-table rows is unresolved. Eight parent IDs show 28 count-field differences. Suspect district fields at `0302`, `0801`, `2202` are held, without substituting child sums. NCDD confirms `0314` for P-03 Srei Santhor despite printed `211`. No 2019-compatible official polygons or current legal-subtype crosswalk were adopted; 2017 reference shapes were removed.
- NCDD Library law/guide catalogues and the NIS/CDB directories were located. Law and plan-guide PDF fetches returned 403, so body/current force is unverified. There is no acquired local plan, investment programme, budget actual or official evaluation. National source references are shown separately from selected-area materials.

[Source audit](../../evidence/cambodia-census2019-source-audit-2026-09-27.md), [start sheet](../../evidence/cambodia-country-start-2026-09-27.md), [Task Contract](../../evidence/cambodia-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/cambodia-country-lesson-audit-2026-09-27.md) define the evidence boundary. The ignored project holds pinned originals, raw parsed rows, field inventory, output hashes and the final dataset.

## Reproduce and inspect

Start from a **new** directory, never overwrite a working candidate after acquisition/build failure. Download the two `config/cambodia-census2019-source-manifest.json` URLs into the listed raw paths and require exact bytes/SHA-256. A changed NCDD HTML body requires a new reviewed snapshot and code assertion, not a bypass of the hash check.

```powershell
node scripts/create-country.mjs --country Cambodia --out generated/cambodia-replay-new
# Obtain the two official originals in the manifest's raw paths; verify byte counts and SHA-256.
python scripts/audit-cambodia-census2019.py --project generated/cambodia-replay-new
python scripts/import-cambodia-census2019.py --project generated/cambodia-replay-new
node scripts/validate-country.mjs --project generated/cambodia-replay-new
node scripts/build-country.mjs --project generated/cambodia-replay-new
node scripts/verify-cambodia-census2019-output.mjs generated/cambodia-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `38537521a1e4bc749042d0d52bb7e967d44ff618555d14e4de5a99a82506447f`, validator **0 errors/warnings**, site built, **14 direct-original/output cases** passed, `npm run check` **158** and `npm test` **218/218**. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, all comparison rows and source locators. Local browser at `127.0.0.1:49801` confirmed Cambodia→Banteay Meanchey→Mongkol Borei→the same Banteay Meanchey whole-area reselection; Mongkol Borei all-person count remained missing. The planning page showed no area-specific material and separate national reference links. These are producer checks, **not** 42-scenario or independent acceptance.

## Remaining before a complete Cambodia edition

1. Resolve two overview/P-table intermediate-unit differences and 28 field discrepancies from official corrections or independent NIS tables; audit the report's other population, education, housing, health and economic columns with definition, universe and original location.
2. Acquire a dated official 2019 code/gazetteer and compatible polygons; reconcile all 25/202/1,646 rows and legal subtype. Keep reporting hierarchy distinct from current planning jurisdictions.
3. Acquire current subnational law and plan guidance bodies, then representative capital/province, district/municipality/khan and commune/sangkat actual plans, investment programmes, adopted budgets, disbursement/implementation and official evaluations. Confirm periods, issuers and approval separately.
4. Check CDB and international source availability for KHM theme/year/grain, acquire permissioned originals, review terms; finish applicable 42 scenarios, print/mobile/local-language and Word/PDF inspection, and independent `ACCEPT`. Assign KHM-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits each lead. It transfers no raw original, 11,301 observations or country acceptance. AreaData and Kit commit/hashes are recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md) when published. **Local:** partial candidate. **GitHub:** tracked adapter/evidence pending commit in this handoff draft. **Hosting:** none. **Public:** none.

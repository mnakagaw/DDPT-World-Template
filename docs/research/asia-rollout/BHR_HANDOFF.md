# Bahrain AreaData continuation — 2026-09-27

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/bahrain-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The [source audit](../../evidence/bahrain-iga2020-source-audit-2026-09-27.md) and [producer check](../../evidence/bahrain-country-lesson-audit-2026-09-27.md) delimit the claims. Candidate dataset SHA-256 at this checkpoint: `f9a2dd8d6ef323025df989ad41fdd1145d1be6c2bc7463b6c61d00f7beac34f1`. Environment: Windows/PowerShell, Python 3.14, Node 24 and local browser; date 2026-09-27. No Bahrain hosting destination is configured.

## Replay and current evidence

`SOURCE_PREFLIGHT.md`/`.json` were read first; they had no Bahrain country-specific lead. The country generator rejects an existing directory. Reuse this ignored candidate or create a new sibling and reacquire originals. `scripts/inventory-bahrain-census2020.py` fetches the 45-dataset [official Census-theme API catalogue](https://www.data.gov.bh/api/explore/v2.1/catalog/datasets?limit=100&refine=theme%3ACensus) and every paginated record body without overwriting existing raw pages. The private inventory pins each URL/hash. Additional official originals are in `raw/bahrain-open-data/`: four `annual-governorate-{0,100,200,300}.json` pages and metadata; `area-2023-records.json` and metadata; 1994/2022 laws, 2023 zoning decision, UPDA catalogue/manual and six-page Capital map decision. `scripts/import-bahrain-iga-census2020.py` checks all consumed hashes and exact source counts/independent identities before replacing only its own indicator/source/document IDs. Source changes require review, not silent replay.

```powershell
node scripts/create-country.mjs --country Bahrain --out generated/bahrain-areadata-20260926
python scripts/inventory-bahrain-census2020.py --project generated/bahrain-areadata-20260926
python scripts/import-bahrain-iga-census2020.py --project generated/bahrain-areadata-20260926
node scripts/validate-country.mjs --project generated/bahrain-areadata-20260926
node scripts/build-country.mjs --project generated/bahrain-areadata-20260926
node scripts/verify-bahrain-iga-output.mjs generated/bahrain-areadata-20260926
npm run check
npm test
node scripts/serve.mjs --dir generated/bahrain-areadata-20260926/site --port 4201
```

The importer is intentionally bounded to the original 45 Census-theme datasets, the 320-row annual population table and the 79-row area table. Census-theme numeric columns: 45 / 2,598 numeric cells, with field disposition in the ignored inventory. **27 numeric fields remain `priority_unassessed`**. The selected 2020 census, separate June annual and 2024 area yield **five territories, 22 domestic indicators and 184 observations**. National census population **1,501,635** and June 2025 portal population **1,603,260** are not WDI estimates. Annual method is not stated by dataset metadata. Three building datasets conflict on Muharraq/Southern labels and were excluded; their matching national sum does not cure the local conflict. There are no verified official codes/polygons, and the 2017 geoBoundaries reference edition is unjoined.

Planning evidence is national law/guidance plus one historical Capital zoning-map decision. UPDA's 83-page June 2023 procedure manual and six-page Capital 2017 Gazette maps are locally acquired, but current Capital zoning applicability, other governorates' actual plan bodies, budgets, execution and evaluations are unverified. The dashboard treats statistical governorates and competent municipalities separately and does not promote a 2017 decision to a complete current governorate development plan.

Browser checked national → Capital, Capital → national, the Capital planning page, and all four national governorate rankings; thematic focus Northern retained Bahrain as the analysis target. Eight real output cases checked five output formats, source row locators, values/periods and full printable comparison rows. Country validation has zero errors/six source-terms warnings. The later commit/export/Kit replay hashes and shared test results are recorded below when complete. No independent `ACCEPT`, Hosting or Public was done.

## Next work

1. Semantically audit the 27 untouched Census-theme numeric columns and unselected cells of the eight partly adopted tables; investigate disability, literacy, services, housing and labour definitions, denominators and lower-area coverage.
2. Obtain 2020/2025 official governorate and smaller-area codes/polygons, source edition and reuse terms; reconcile the 2014 redivision and the 2017 reference shapes. Resolve the three conflicting building tables with iGA before using local building values.
3. Obtain a method note for the annual population series, current UPDA zoning map editions and actual competent-municipality plan/financial bodies; distinguish historical approval, current legal effect and collected content.
4. Complete applicable 42 scenarios, printed/report/device checks, source terms and independent `ACCEPT` before any hosting.
5. Continue the Middle East priority order with Cyprus. After Bahrain as partial, Asia 50 = **0 ACCEPT, 19 partial, 1 research-only, 30 unstarted**; Middle East 19 = **0 ACCEPT, 17 partial, 1 research-only, 1 unstarted**.

Only code, public source leads, evidence and status belong in Git. Raw originals, inventory, candidate and generated output files remain ignored. The Kit feedback transfer stops at `official_location_identified` and does not carry observations or acceptance. Commit IDs and remote parity are appended after the two-repository handoff.

# India AreaData continuation — 2026-09-27 JST

Branch `codex/asia-domestic-20260926`; ignored candidate `generated/india-areadata-20260927`; **partial, local, unpublished; no independent `ACCEPT`**. The source audit is `docs/evidence/india-orgi-pca2011-source-audit-2026-09-27.md`, producer check is `docs/evidence/india-country-lesson-audit-2026-09-27.md`. Candidate dataset SHA-256 at this checkpoint: `f811a882ff2371dbe9c2b599078ea93d96d8472db7a66157c6b18930e6b30dfc`. No India hosting destination or publication scope has been specified.

## Replay and obtained result

`evidence/SOURCE_PREFLIGHT.md` and `.json` were read before source collection; they had no India-specific pre-researched location. ORGI's official 2011 state/district PCA workbook is saved under `raw/`, with official catalogue HTML, four PDFs (2027 Gazette notice, Constitution, two MoPR planning guides), source receipts and private full-column inventory. `scripts/inventory-india-census2011.py` audits the pinned XLSX hash and all 172,380 numeric cells; `scripts/import-india-orgi-pca2011.py` pins all acquired hashes, imports 24 selected direct-count combinations, and leaves 231 field/row-class combinations unassessed. The candidate has **676 territories (India, 35 states/UT, 640 districts), 24 domestic indicators, 16,224 direct domestic observations, 36 comparison sets**. The 2011 national census count 1,210,854,977 is separate from WDI estimates. No 2027 results, subdistrict/village rows, current LGD mapping or region polygon is inferred.

```powershell
node scripts/create-country.mjs --country India --out generated/india-areadata-NEW
# Acquire the five pinned official originals and catalogue listed in the source audit into raw/.
python scripts/inventory-india-census2011.py --project generated/india-areadata-NEW
python scripts/import-india-orgi-pca2011.py --project generated/india-areadata-NEW
node scripts/validate-country.mjs --project generated/india-areadata-NEW
node scripts/build-country.mjs --project generated/india-areadata-NEW
node scripts/verify-india-orgi-pca-output.mjs generated/india-areadata-NEW
node scripts/serve.mjs --dir generated/india-areadata-NEW/site --port 4203
```

`create-country.mjs` refuses an existing directory. The existing candidate can be reimported from its pinned local originals. Changed source bytes require review, not silent hash replacement. The current candidate passed validator (zero errors/warnings), build, seven-case actual export verifier, shared check (149 modules/templates), and 218/218 tests on 2026-09-27 JST. In-app browser checked India/Delhi/New Delhi selection, New Delhi rural **zero** with Sheet1 row/column source, district→state re-selection to Delhi rural 419,042, and national references displayed apart from absent local plans. The local Node preview serves `.mjs` as JavaScript; a Python `http.server` attempt with `text/plain` MIME was discarded.

## Open gates and next priority

1. Acquire/inventory ORGI's other PCA and finer-unit bodies, and assess the 231 unadopted field/reporting-row combinations with full definitions and source terms. The ORGI Population Finder and village catalogue are locations, not acquired local values.
2. Acquire source-compatible official 2011 polygons and a dated current LGD/Panchayat crosswalk, including split/merged state and district cases. Do not name-join current boundaries to 2011 statistics.
3. Check applicable state rural and urban laws, competent local planning units and actual approved plans, budgets, execution/evaluation. The 2011 census District is not automatically a current District Panchayat; national Ministry guidance is not an area plan.
4. Complete visual/mobile/print and all relevant 42 scenarios, source reuse/hosting terms and independent `ACCEPT`. No source body or candidate is published.
5. Feed eight newly confirmed public official locations to Kit at `official_location_identified` only. Next unstarted country in the requested priority is Pakistan. All Middle East editions still lack independent completion; progress into South Asia is not a declaration that phase 1 is complete.

The generated candidate, source originals, receipts, complete inventory and output artifacts are ignored locally. Git stores repeatable code, bounded audit, status, handoff and public source-location metadata. Kit receives no raw records or country acceptance. Local, GitHub, Hosting and Public state must be reported separately.

# Lebanon AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; candidate `generated/lebanon-areadata-20260926` (ignored local directory). Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/lebanon-cas-lfhlcs-source-audit-2026-09-26.md) and [producer check](../../evidence/lebanon-country-lesson-audit-2026-09-26.md) define the evidence limit. Private `dashboard.json` SHA-256 is `2d2b7516f5e9cf3dc157ae8eda835bda81151292e246d1662669085aa148e6c1`; private originals, receipts, field inventory and output hashes remain in the candidate. Environment: Windows/PowerShell, Node 24, Python 3, Codex in-app browser; date 2026-09-26. No Lebanon hosting destination is configured.

## Replay

Create a **new** project directory, read its `evidence/SOURCE_PREFLIGHT.md` and JSON, then run the source replay:

```powershell
node scripts/create-country.mjs --country Lebanon --out generated/lebanon-areadata-20260926
python scripts/fetch-lebanon-cas-sources.py --project generated/lebanon-areadata-20260926
python scripts/import-lebanon-cas-lfhlcs2018.py --project generated/lebanon-areadata-20260926
node scripts/validate-country.mjs --project generated/lebanon-areadata-20260926
node scripts/build-country.mjs --project generated/lebanon-areadata-20260926
node scripts/verify-lebanon-cas-output.mjs
npm run check
npm test
```

The generator refuses an existing output directory; choose another name for a fresh run. Fetch refuses changed originals. The importer replaces only its own source and indicator IDs and removes unverified generated local reference geometry. Original files and private candidate are excluded from Git; reuse terms still require review.

## Verified portion and limits

- CAS LFHLCS 2018–19 is a **household survey** with mid-2018 estimates for residents of residential dwellings. It is not a census or an all-resident series. Main report Table 1.1 and Demography.xls HL.5 yield **four local indicators and 140 direct observations** for national, eight governorates and 26 caza source rows. Population and household values are rounded to 100. The published national population is **4,842,500**, household count **1,266,700**. Rounded governorate totals differ by +100/−100, and no parent is filled by child addition.
- The survey's two coextensive Beirut/Akkar governorate–caza pairs retain distinct type-specific records. Their caza rows are hidden in ordinary area controls when their governorates are marked terminal; this selection issue remains before acceptance. The 2017 nine-shape ADM1 reference is not joined to the eight 2018 governorate reporting rows, and there are **no verified local polygons or adopted official codes**. WDI national population remains a separately defined international series.
- The acquired demography workbook has 26 sheets; only HL.5 selected fields were adopted. Acquired MICS Chapter 11 has 14 sheets, all unassessed and unadopted; its five-governorate sample and separate displaced/refugee domains do not furnish a nationwide estimate. CAS district profiles were located but not acquired. DGU procedure/office/master-plan overview are location leads only; no selected-area legal plan, approval, budget, execution or evaluation record was verified.
- Browser checked Lebanon territorial page **4,842,500** with 8/8 first-level comparison; Mount Lebanon **2,032,600** with 6/6 caza comparison; Baabda **553,800**; reselecting Mount Lebanon reset heading, URL and values; thematic comparison held the 8/8 2018 governorate cohort; Mount Lebanon planning showed **zero** selected-area materials and explicit gaps. These are narrow producer checks, not all 42 scenarios.
- Eight output cases generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Selected-area value, period, source locator/URL, within-area row count, first/last comparison rows and hashes were checked. No full-table print, Word/PDF or final visual layout audit was completed.

`validate-country` passed with zero errors and one material warning: no verified country-specific planning documents. Build and output verifier passed. Standard AreaData check/test, Kit feedback and Git IDs are recorded in [KIT_FEEDBACK_HANDOFF.md](KIT_FEEDBACK_HANDOFF.md). Independent audit, Hosting and Public remain undone.

## Next work

1. Complete field-by-field review of the whole LFHLCS report and all 26 demography sheets, plus the MICS workbook and district profiles. Identify additional compatible, non-overlapping themes only after method, denominator, full area universe and period checks.
2. Obtain current official administrative code/boundary editions and historical correspondence for the eight-governorate/26-caza survey geography; resolve coextensive caza selection without implying a new legal hierarchy.
3. Verify current planning law, responsible authorities and actual plan/decision/budget/implementation/evaluation records for contrasting units. Keep location, acquisition and institutional status separate.
4. Complete 42 acceptance scenarios, full-table print, output layout, source terms, producer sign-off and independent `ACCEPT` before hosting.
5. Continue the requested Middle East sequence. At this checkpoint Asia 50 = **0 ACCEPT, 12 partial, 1 research-only, 37 unstarted**; Middle East 19 = **0 ACCEPT, 10 partial, 1 research-only, 8 unstarted**. Next unstarted country: State of Palestine.

Only code, evidence and status, not this private dataset or raw originals, are saved to GitHub.

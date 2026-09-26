# Azerbaijan AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; candidate `generated/azerbaijan-areadata-20260926` (ignored local directory). Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/azerbaijan-ssc-population-source-audit-2026-09-26.md) and [producer check](../../evidence/azerbaijan-country-lesson-audit-2026-09-26.md) define the evidence limit. The private `dashboard.json` SHA-256 is `09e682745df307ce5a1ab9983298b94a5b676740bb24ed343fcf509281847844`; private raw originals, receipts, field/crosswalk inventory and output hashes remain in the candidate. Environment: Windows/PowerShell, Node 24, Python 3, Poppler and Codex in-app browser; date 2026-09-26.

## Replay

After `node scripts/create-country.mjs --country Azerbaijan --out generated/azerbaijan-areadata-20260926`, read `evidence/SOURCE_PREFLIGHT.md` and JSON, then run:

```powershell
python scripts/fetch-azerbaijan-ssc-sources.py --project generated/azerbaijan-areadata-20260926
python scripts/import-azerbaijan-ssc-population.py --project generated/azerbaijan-areadata-20260926
node scripts/validate-country.mjs --project generated/azerbaijan-areadata-20260926
node scripts/build-country.mjs --project generated/azerbaijan-areadata-20260926
node scripts/verify-azerbaijan-domestic-output.mjs
npm run check
npm test
```

The fetcher refuses altered original hashes, and the importer can be rerun on its own IDs. The three `.xls` files, code PDF and two large census ZIPs are not committed. Source terms need review.

## Verified portion and limits

- SSC table 1.15 supplies national + 14 parent + 86 child source rows, with rounded 2019 census-basis and 1 January 2026 resident values; table 1.19 supplies the corresponding 2026 male/female values. The candidate has **four local indicators and 403 direct observations**. Aghdara's 2019 `...` is missing. 2026 children add to published parents at source precision. The 2019 parent rows remain direct observations, not sums over missing children.
- The 2024 SSC code PDF yields **87** first-level code candidates. **84** are adopted including Baku; Lankaran, Shaki and Yevlakh city/rayon type conflicts are held without official code adoption. The two 2021 geoBoundaries components provide only a **national** reference outline; no local polygon is joined. The statistical economic regions are not declared legal plan makers.
- The 2019 census Volumes A/B were acquired, but their 1,054 combined pages have only catalogue/front-matter inspection. Historical table 1.17, table 1.15 area/density, table 1.19 settlement/urban/rural, the 2025 regional yearbook and other local themes are unadopted. The 2025 yearbook is only a located lead. Do not call this a full census inventory.
- SSC publishes rounded **thousand people** at 1 January 2026; WDI's national population is in **people** at a different date. Browser verification caught the generic population-difference card subtracting these raw numbers; the importer now leaves `analysis.population_context` unset, and the false comparison disappeared on reload.
- Browser checked national 2026 **10,262.4** thousand and 14/14 direct parent comparison; Baku **2,356.2** and 12/12 district thematic comparison; Binagadi **309.2**; direct reselection of Baku from Binagadi reset the target and parent value. Baku planning page says **0** verified local materials, and local map panels explicitly say no verified boundary. The default thematic level for Baku is its own city level (1/1); choosing local administrative unit shows its 12 districts. This behavior needs wider UX acceptance review, not an ad hoc shared control change.
- Eight output cases produced diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV with checked value, period, source row, selected area, first/last internal rows and hashes. Internal-row counts were **14, 12, 0, 10, 0, 8, 0, 14** (national 2026, Baku, Binagadi, Garabagh, Aghdara, Nakhchivan, Lankaran, national 2019). No full print/Word/PDF or all 42 scenarios were completed.

`validate-country` passed with 0 errors and one material warning: no verified country-specific planning documents. `npm run check` passed (138 JavaScript modules and JSON templates); `npm test` passed **218/218**. The eight-case output verifier passed. Independent audit and hosting remain undone.

## Next work

1. Audit every table and numeric field in both 2019 census volumes and the other acquired SSC sheets; obtain and audit the regional yearbook and locality statistics. Maintain missing, period and measurement distinctions.
2. Resolve the three held code/type matches and obtain current official local boundary polygons and a historical geographic crosswalk. Avoid substituting the two-part 2021 country outline for local boundaries.
3. Verify current amended planning law, legal plan maker and actual plan/approval for Baku, a rayon and Nakhchivan; acquire their budget, implementation and evaluation sources and map them to the right area and period.
4. Complete the 42 scenario and 12-point producer audits, output rendering, independent `ACCEPT` and only then consider hosting. The country hosting destination is not configured.
5. Continue the requested Middle East order while closing existing partial editions. At this checkpoint Asia 50 = **0 ACCEPT, 10 partial, 1 research-only, 39 unstarted**; Middle East 19 = **0 ACCEPT, 8 partial, 1 research-only, 10 unstarted**. The next unstarted country is Israel.

AreaData and Kit commit IDs and GitHub verification are recorded in [the feedback handoff](KIT_FEEDBACK_HANDOFF.md) when completed. Only code/evidence/status, not this candidate dataset, are Git-published.

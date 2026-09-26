# Kuwait AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/kuwait-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/kuwait-csb2021-source-audit-2026-09-26.md) and [producer check](../../evidence/kuwait-country-lesson-audit-2026-09-26.md) delimit what was verified. Private `dashboard.json` SHA-256: `df69c3b86e9758add45ed0269fb2a53107447ecc45540cb830b62618ff454ab6`. Private catalog HTML, 16 Excel/PDF originals, receipts, field audit, generated reports and output hashes remain in the ignored candidate. Environment: Windows/PowerShell, Node 24, Python 3 and Codex in-app browser; date 2026-09-26. No Kuwait hosting destination is configured.

## Replay

Read `evidence/SOURCE_PREFLIGHT.md` and `.json` first. The generator refuses an existing directory; use a fresh sibling candidate or preserve the original privately. The six catalog HTML pages must be copied/acquired separately before the catalog inventory command; their private hashes are in `KWT_CSB2021_CATALOG_INVENTORY.json`. The eight selected Excel/PDF pairs are pinned in the fetch script.

```powershell
node scripts/create-country.mjs --country Kuwait --out generated/kuwait-areadata-20260926
python scripts/fetch-kuwait-csb-census2021.py --project generated/kuwait-areadata-20260926
python scripts/inventory-kuwait-csb-catalog.py --project generated/kuwait-areadata-20260926
python scripts/import-kuwait-csb-census2021.py --project generated/kuwait-areadata-20260926
node scripts/validate-country.mjs --project generated/kuwait-areadata-20260926
node scripts/build-country.mjs --project generated/kuwait-areadata-20260926
node scripts/verify-kuwait-csb-census-output.mjs generated/kuwait-areadata-20260926
npm run check
npm test
node scripts/serve.mjs --dir generated/kuwait-areadata-20260926/site --port 4196
```

Importer replacement of its own IDs is idempotent. Replaying changes `generated_at` and therefore the dataset hash while keeping source numeric values fixed. The candidate and originals are excluded from Git; redistribution terms require review. Use the Node preview server because its `.mjs` MIME type is correct on this Windows host.

## Verified portion and limits

- The official 2021 registration census contributes **165 territories** (national, 6 governorates, 157 Areas and one geography-not-stated reporting row), **17 local indicators**, **889 direct observations** and **32 calculated observations**. Eight source tables' 3,246 numeric cells were audited. The other 110 listed tables are not numeric-audited.
- Table 1 national **4,385,717** includes a **4,578** geography-not-stated residual. Six governorates sum to **4,381,139**, so the national exact value is never treated as their calculated complete aggregate. The 157 Area rows group 33/17/41/33/20/13 by contiguous source order, with all nine columns matching each governorate. This is source-table reconciliation, not official code/boundary certification.
- National census labour force **2,570,091** and unemployed **23,992** yield a clearly labelled **0.93% AreaData-calculated share**. WDI midyear population is a distinct method. The source excludes stated non-Kuwaiti categories; the 2021 registration census is not a current resident count.
- Browser checked Kuwait → Capital → DASMAN → Capital whole; **4,385,717 → 574,839 → 1,942 → 574,839**. Capital's 33 Area values and no-polygon message appeared; the unassigned 4,578 appears separately. On the thematic page, focusing Hawalli left Capital selected. Capital planning had zero collected documents and labelled outputs unapproved. A viewport screenshot was visually inspected.
- Fifteen output cases checked actual diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Value, year, source locator, calculated provenance, all printable HTML member rows and hashes matched. For Capital, the report included all 33 Area rows. The print CSS removes scroll clipping, but no rendered print/PDF, Word, narrow-screen audit or complete 42-scenario pass was performed.

Country validation passed with zero errors and one material missing-plan warning; build, 15-case output verifier, AreaData `npm run check` and **218/218** tests passed. The shared internal-comparison view/export was corrected to label AreaData-calculated source observations rather than “Source reported.” Independent audit, Hosting and Public are undone.

## Next work

1. Prioritize the remaining 110 official CSB census tables by useful local geography/themes. Audit original numeric fields and definitions rather than equating catalog titles with acquired observations. Check later administrative estimates separately.
2. Obtain official 2021/current Area and governorate codes, polygons and history; independently confirm all 157 Area parent assignments. The 2011 CSB GIS report and six reference shapes are not a compatible boundary join.
3. Audit operative Municipal Law 33/2016, plan-making authority, current national/master/local plans, selected-area approval, budget, implementation and evaluation for contrasting urban and peripheral Areas. Do not infer a plan or legal plan maker from census geography.
4. Complete all applicable 42 scenarios, long-table print rendering, document layout, source terms and independent `ACCEPT` before hosting.
5. Continue the user-requested Middle East order. At this checkpoint Asia 50 = **0 ACCEPT, 15 partial, 1 research-only, 34 unstarted**; Middle East 19 = **0 ACCEPT, 13 partial, 1 research-only, 5 unstarted**. Next unstarted country: Georgia.

Only code, public-source leads, evidence and status, not the private dataset or original files, are saved to GitHub. Kit feedback and both repositories' commit IDs are recorded in `KIT_FEEDBACK_HANDOFF.md` after transfer.

# Kazakhstan AreaData handoff — 2026-09-27 JST

**Status: BNS 2026 local-population and 2021 national-census partial candidate; independent `ACCEPT` pending; unpublished.** Asia ledger after this candidate: 0 complete, 39 partial, 1 research-only, 10 not started. Next unstarted priority by CSV order: Tajikistan. Candidate `generated/kazakhstan-areadata-20260927` is ignored; KAZ-specific Hosting/Public destination is not assigned.

## Evidence and decisions

- [BNS July population](https://stat.gov.kz/en/industries/social-tatistics/demography/spreadsheets/) sheet 2 supplies nine direct July 2026 values for nation, 20 first-level units and 228 children: 2,241 observations. [BNS August workbook](https://stat.gov.kz/en/industries/social-tatistics/demography/spreadsheets/) supplies four distinct August/Jan–Jul values for nation plus 20 first-level units: 84 observations. [BNS 2021 census Volume I](https://stat.gov.kz/en/national/2021/) supplies five adopted national cells. In total: 249 territories, 18 domestic indicators, 2,330 direct observations. July national 20,590,589, August national 20,604,819 and 2021 census 19,186,015 have different dates/methods; WDI remains separate.
- [KATO edition 18 September 2026](https://stat.gov.kz/ru/classifiers/statistical/21/) provides codes matched by complete 2026 July population parent/child order and names. This later classifier is not proven identical on 1 July. The [NSDI WFS district-layer attributes](https://map.gov.kz/) have 211 unique codes in 254 features and omit 37 candidate local IDs. Polygon date and coverage remain unverified. The initial 2017 geoBoundaries shapes were removed; map geometry is missing, selectors and full comparison tables work.
- [Planning system decree 790](https://old.adilet.zan.kz/rus/docs/P1700000790) distinguishes oblast/republican-city and district/regional-city plan units. [Ulytau plan body](https://www.gov.kz/memleket/entities/ulytau/documents/details/1017009?lang=ru) is acquired, approval instrument not checked. [Burabay district plan body](https://www.gov.kz/memleket/entities/aqmola-burabay/press/news/details/1135605) states maslikhat approval `8C-39/3`, 19 December 2025. Akmola/Almaty oblast plan listings and Akmola budget-execution report are link-only. Targets, allocations, execution and evaluation are not converted to population or actuals.
- The 2021 census local tables refer to geography before the 2022 oblast split; their values are withheld from the 2026 territory IDs. Acquired workbook/plan columns are mechanically inventoried; many remain `priority_unassessed`, and other census volumes are not acquired.

[Detailed source audit](../../evidence/kazakhstan-bns2026-source-audit-2026-09-27.md), [start sheet](../../evidence/kazakhstan-country-start-2026-09-27.md), [Task Contract](../../evidence/kazakhstan-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/kazakhstan-country-lesson-audit-2026-09-27.md), [table/column inventory](../../evidence/kazakhstan-bns2026-table-audit-2026-09-27.json), [source manifest](../../../config/kazakhstan-2026-source-manifest.json). The ignored candidate retains raw originals, rendered census pages, output cases and built site.

## Reproduce and inspect

Create a **new** candidate directory and download all nine manifest originals to each `raw_path`; verify byte length/SHA-256. Python needs openpyxl; census inspection needs Poppler `pdfinfo`/`pdftotext`. A hash or source-edition change requires review before import. A failed update must leave the previous working candidate intact.

```powershell
node scripts/create-country.mjs --country Kazakhstan --out generated/kazakhstan-replay-new
# Download each manifest source to generated/kazakhstan-replay-new/<raw_path>.
python scripts/import-kazakhstan-2026.py --project generated/kazakhstan-replay-new
node scripts/validate-country.mjs --project generated/kazakhstan-replay-new
node scripts/build-country.mjs --project generated/kazakhstan-replay-new
node scripts/export-kazakhstan-2026-cases.mjs generated/kazakhstan-replay-new
python scripts/verify-kazakhstan-2026-output.py --project generated/kazakhstan-replay-new
npm run check
npm test
```

Producer dataset SHA-256 `343084b4737934eeb3bc1e2fb3329ca5c4f6c871cbd2265d53b77be3307dff85`, unchanged after a second import. Validator **0 errors/warnings**, build succeeded. Eleven source-transcribed output cases checked 401 value/missing cells and nine original hashes. National comparison 20/20, Abay 12/12, Akmola 20/20, Astana 6/6. Browser checked national→Akmola→Burabay→same parent, Ulytau and Almaty oblast/city plan separation, selected URL, headings and main values. `npm run check` checked **167** JavaScript/JSON files and `npm test` passed **219/219**. These producer checks are not all 42 scenarios or independent acceptance.

## Remaining before a complete Kazakhstan edition

1. Semantically assess all acquired workbook/plan numeric columns and census tables, other census volumes, municipality level availability, dates, population definitions and rights. Build a separate historical 2021 geography edition before local census adoption.
2. Obtain a July 2026-valid official KATO crosswalk and complete dated polygons. Resolve NSDI feature duplicates, missing codes, layer date and redistribution terms; do not use display geometry for legal/statistical aggregation.
3. Acquire each relevant local plan, approval decision, investment annex, current forms, budget allocations, actual execution and official evaluation; keep plan targets and actuals distinct.
4. Complete the 42-scenario UI/print/mobile/output review, local-user checks and independent `ACCEPT`. Assign KAZ-specific Hosting/Public scope and inspect deployed JSON/rendered URL only after acceptance.

Kit feedback transfers **public official locations and reuse cautions only** at `official_location_identified`; no originals, observations, code/polygon join or acceptance. **Local:** partial candidate. **GitHub:** adapter/audit and source leads committed and pushed. **Hosting:** none. **Public:** none. Two-repository commit exchange is recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md).

GitHub handoff: AreaData adapter/audit `0c8c0bc0499869d76d9f676f36b13a8a746636ac`, 525-source feedback bundle `5e78eb34e72a68e11d3ab24c91b9929c87fdff04` (SHA-256 `a219966c7207d4f03c9749457239f74cfb870d82feddf9238b7660f163c90a0d`), Kit import `f6470a84f85903928ae801b285d1b1b8685191ed`. All were pushed on their respective `codex/asia-*` branches. The final AreaData handoff record follows the adapter-bound bundle and does not change its `origin_commit`.

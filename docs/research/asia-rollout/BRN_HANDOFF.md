# Brunei Darussalam AreaData handoff — 2026-09-27 JST

**Status: DEPS BPP 2021 domestic statistics partial candidate; independent `ACCEPT` pending; unpublished.** Asia ledger: 0 complete, 37 partial, 1 research-only, 12 not started. Next unstarted priority by CSV order: Uzbekistan. Candidate: `generated/brunei-areadata-20260927` (ignored). No BRN-specific Hosting/Public destination is assigned.

## Evidence and decisions

- [DEPS BPP 2021 final report and Annexes A–C](https://www.deps.gov.bn/statistical-publications/) comprise four acquired PDFs. These plus AGC and MOF PDFs are byte/hash pinned in the six-item [manifest](../../../config/brunei-bpp2021-source-manifest.json). Annex A1/A2/B1/B2/C1 selected columns have 1,311 audited numeric cells. National + four districts + 39 mukims receive **11 indicators, 352 direct cells and 15 age-band sums**. Annex A3–A12/B3–B6/C2–C10 and all Main Report tables remain `priority_unassessed`. Census national population is 440,715; WDI annual estimates are separate.
- The [Attorney General's Chambers Cap.248 revised 2022](https://www.agc.gov.bn/documents/town-and-country-planning-act/) assigns draft District Plans to the Planning Authority and approval/rejection to the Minister. The [MOF RKN12](https://www.mof.gov.bn/ndpo_general-information/) p.114 lists four 2026–2045 District Plan **projects**, not proof of completion. The [JPBD catalogue](https://www.jpbd.gov.bn/buku-garispanduan-dan-master-plan/) lists four named District Plans, but plan bodies, map editions, periods, approval notices and local budgets are unacquired. Each mukim shows only its parent district catalogue context, without an independent mukim plan.
- DEPS reporting names establish the 4+39 hierarchy, not official geographic codes. The 2011 geoBoundaries layer is removed because its compatibility with BPP 2021 is unverified. No district/mukim polygon is joined. The [Survey Department Geoportal](https://geoportal.survey.gov.bn/start) is an official source location, not an acquired compatible release.

[Detailed source audit](../../evidence/brunei-bpp2021-source-audit-2026-09-27.md), [start sheet](../../evidence/brunei-country-start-2026-09-27.md), [Task Contract](../../evidence/brunei-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/brunei-country-lesson-audit-2026-09-27.md), [all-28-annex table inventory](../../evidence/brunei-bpp2021-table-audit-2026-09-27.json), and [source manifest](../../../config/brunei-bpp2021-source-manifest.json) define the boundary. The ignored candidate retains raw PDFs, generated audit JSON, exports and built site.

## Reproduce and inspect

Create a **new** candidate directory, download the manifest's six official PDFs to each `raw_path`, then verify byte length/SHA-256. A source edition/hash change requires source review before import. Python requires Poppler `pdftotext`. Do not replace a prior working candidate on acquisition/import/build failure.

```powershell
node scripts/create-country.mjs --country Brunei --out generated/brunei-replay-new
# Download each manifest source to generated/brunei-replay-new/<raw_path>.
python scripts/import-brunei-bpp2021.py --project generated/brunei-replay-new
node scripts/validate-country.mjs --project generated/brunei-replay-new
node scripts/build-country.mjs --project generated/brunei-replay-new
node scripts/export-brunei-bpp2021-cases.mjs generated/brunei-replay-new
python scripts/verify-brunei-bpp2021-output.py --project generated/brunei-replay-new
npm run check
npm test
```

Producer run: dataset SHA-256 `868a15b5a57e7ca9248c76f6d618a6caace21167b1567a6b4cc11018b0ac5cfc`; validator **0 errors/warnings**, build succeeded. Six independent source-transcribed cases ×11 indicators in diagnostic/evidence exports check 132 value/status cells, including Melilas temporary-resident zero and absent mukim age groups. National comparison 4/4 districts, Brunei Muara 18/18 mukims. Browser confirmed national and district/mukim selection, same-parent reselection, calculated provenance, URL and planning-document separation. `npm run check` passed **165 JavaScript/JSON** modules/templates; `npm test` passed **219/219**. These producer checks do not equal all 42 scenarios or independent acceptance.

## Remaining before a complete Brunei edition

1. Inspect numeric columns, populations, definitions and lower-area coverage in 23 unassessed Annex tables and all Main Report tables. Assess Kampung detail and the 2011–2021 census-geography relationship without inferring a stable time series.
2. Acquire official dated district/mukim/kampung codes and compatible polygons, map geographic changes and licensed reuse terms; keep unmatched values visible in selector/table form.
3. Acquire each District Plan body, maps, edition, applicable Minister/Gazette approval, and district-specific budget allocation, actual spending, implementation and official evaluation. Do not turn the RKN12 project list or JPBD cover image into an approved plan.
4. Confirm statistical/plan/geospatial reuse terms, applicable 42 scenarios, visual/print/mobile/performance/language/local-user checks, then obtain independent `ACCEPT`. Set BRN-specific Hosting/Public scope and verify deployed JSON and rendered URLs only after acceptance.

Kit feedback carries **official public locations and reuse cautions only** at `official_location_identified`; no PDF originals, observations, code/shape join or country acceptance. **Local:** partial candidate. **GitHub:** adapter, audit and source leads committed and pushed. **Hosting:** none. **Public:** none. Two-repository commit exchange is recorded in [Kit feedback handoff](KIT_FEEDBACK_HANDOFF.md).

GitHub handoff: AreaData adapter/audit `8ff8f6b73aa01bdd0d352c5150f8c40529a16c29`, 501-source feedback bundle `d24dd2ba7e1f2e60180858146db4d05f8ac1aad3` (SHA-256 `d0988c9689445697c68f4120d8d929e696c75ed5a2087e1887aca5f10f6dea1e`), Kit import `7acfdcd80d4aceb2b76459fbe53480ee1bbf74ea`. All are pushed on their respective `codex/asia-*` branches. The final AreaData handoff record follows the adapter-bound bundle and does not change its `origin_commit`.

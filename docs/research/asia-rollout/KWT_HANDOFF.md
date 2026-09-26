# Kuwait country candidate — handoff, 2026-09-26

**Status: partial, producer-validated, independently unaccepted, unpublished.** Local ignored candidate: `generated/kuwait-areadata-20260926`; independent bootstrap replay: `generated/kuwait-replay-20260926`. The [tracked official-source audit](../../evidence/kuwait-csb-2021-official-sources-2026-09-26.md) lists URLs, four pinned original hashes, all audited source fields, exclusions and unadopted area rows. The candidate's raw PDFs/XLSX, receipts and source-row CSVs stay outside Git pending reuse/redistribution review.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country KWT --out <new-directory>
python -X utf8 scripts/collect-kuwait-csb-2021.py --project <new-directory>
python -X utf8 scripts/inspect-kuwait-csb-2021.py --project <new-directory>
python -X utf8 scripts/import-kuwait-csb-2021-partial.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-kuwait-csb-output.mjs --project <new-directory>
```

Use `python -X utf8 scripts/compare-kuwait-csb-replay.py --project <first-project> --replay <second-project>` after two separate bootstraps. The actual replay matched 7 territories, 63 domestic count observations and 9 official source records; adopted snapshot SHA-256 `cd21163bf98570bf9a586b92789d4b812114e7a0d001d0ab1d67a2e489043888`. Fresh WDI retrieval times are outside that comparison.

Current candidate dataset SHA-256 `9f85d45fbc301ed105511581d7cfe8c351214148ce98b71d313c5c1b48b48bcc`: 7 territories (nation plus six governorates), 21 indicators (nine domestic), 375 observations (63 domestic), 23 sources, **zero planning documents and zero polygons**. Official 2021 registration-census Table 1 national population is 4,385,717. Six governorates sum to 4,381,139; `Not Stated` 4,578 is a nonterritorial source row, not a seventh governorate and not a zero. The website homepage displayed a different headline 4,385,291; the pinned final Table 1 governs this candidate. The exact Table 1 register-extraction date is not established. CSB 2021 values and WDI annual estimates remain separate.

Table 51's 157 named area counts were obtained and checked against both official formats, but **none was adopted** without an official area code and explicit parent-governorate key. Source row order happens to produce the six governorate subtotals; arithmetic alone is insufficient to certify the crosswalk. Six 2017 provider polygons are withheld, and the 2021 governorate source labels do not certify current legal boundaries. Official law 33/2016 and historical planning locations are logged; direct body acquisition failed, and no local approval, plan, budget, expenditure or evaluation is asserted.

Both candidates validated with errors 0 and a truthful warning for missing planning originals; both built. `verify-kuwait-csb-output.mjs` checked five areas' diagnosis CSV/HTML, planning HTML and evidence CSV against original counts, source URL, child rows, first and last rows. Browser checks covered Kuwait → Hawalli → Kuwait, theme comparison and Al-Farwaniya planning with zero documents. `evidence/COUNTRY_LESSON_AUDIT.md` records limited producer checks. **The 42 scenarios and independent `ACCEPT` remain open; Hosting/Public are not deployed.**

Next: inventory all other population, building and establishment census tables and newer population bulletins; acquire dated official PACI/CSB code and boundary directory; resolve Table 51's 157 area-to-governorate and legal-status crosswalk; acquire and inspect the current municipality law/amendments, fourth master plan and individual planning/budget/implementation/evaluation originals; run representative and exception-area UI, exported-file, narrow-screen and print checks; complete independent acceptance. Kit feedback must carry public URLs only and remain `official_location_identified` until Kit independently acquires and audits the originals.

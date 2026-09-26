# Lebanon country candidate — handoff, 2026-09-26

**Status: CAS LFHLCS 2018–19 nation/eight-governorate/26-caza partial survey candidate; not a census edition, not independently accepted or published.** The ignored output is `generated/lebanon-areadata-20260926`. The [tracked source audit](../../evidence/lebanon-cas-lfhlcs-moph-2026-09-26.md) records exact URLs, hashes, field decisions, 8-versus-9 governorate geography and validation. Original XLS/PDF/GeoJSON files and individual receipts are local only pending redistribution review.

Recreate in a **new** directory:

```powershell
node scripts/create-country.mjs --country Lebanon --out <new-directory>
python -X utf8 scripts/collect-lebanon-cas-moph-sources.py --project <new-directory>
python -X utf8 scripts/inspect-lebanon-lfhlcs-demography.py --project <new-directory>
python -X utf8 scripts/import-lebanon-lfhlcs-2018-partial.py --project <new-directory>
python -X utf8 scripts/register-lebanon-official-source-leads.py --project <new-directory>
node scripts/validate-country.mjs --project <new-directory>
node scripts/build-country.mjs --project <new-directory>
node scripts/verify-lebanon-lfhlcs-output.mjs --project <new-directory>
```

For a second independently generated directory, use `python -X utf8 scripts/compare-lebanon-lfhlcs-replay.py --first <first-project> --second <second-project>`. It compares four pinned original hashes, the 105 adopted survey tuples, workbook sheet structures and every inventoried column. It intentionally does not require identical full JSON hashes because generated times and fresh international fetches can differ.

The importer adopts only HL5 Women, Men and Women & Men columns: 3 × 35 = **105** domestic survey observations. The source uses 2018 estimates for residents of residential dwellings, scaled from thousands and rounded to 100 people. Country total is **4,842,500**, not a current census count or the WDI 2025 national value. The workbook's other 23 HL sheets and 26 acquired district profiles are still semantically unassessed. The 2023 MICS release covers only five of eight governorates and specified settlements/camps, so unreported areas cannot be called zero.

CAS survey reporting has eight governorates; the undated MOPH ADM1 and bootstrap reference have nine. The eight survey governorates have no asserted shape. Twenty-six MOPH ADM2 polygons are name-matched reference drawings only, with a distinct boundary edition on the survey observations so that district source values remain visible but comparable polygon shading/ranking is withheld. MOPH PCODE is not treated as a verified legal or survey code. The current legal code/boundary edition and Keserwan-Jbeil split need source-level reconciliation.

The first candidate dataset SHA-256 after source registration is `7482da5de7df2d133d707078e2e9bdba3878880b5f69975b13fd14b009c8de28`. It and `generated/lebanon-replay-20260926` passed validation (zero errors, one expected no-planning warning), build and selected output verification. Browser checks covered national 8-governorate comparison, Mount Lebanon, Keserwan, parent reselection, and selected-area planning/thematic navigation. The ignored `evidence/COUNTRY_LESSON_AUDIT.md` records sampled work and unrun gates. All 42 applicable acceptance scenarios and independent `ACCEPT` remain open. Hosting and public verification were not run.

Next: close the official census/product inventory, audit remaining survey fields and profiles, obtain dated government codes/boundaries and municipal planning law/guidance, then attach actual plan/budget/spending/evaluation records to verified local units. Check representative and exception areas across screen, saved content and exports. Keep this candidate unpublished until independent `ACCEPT`.

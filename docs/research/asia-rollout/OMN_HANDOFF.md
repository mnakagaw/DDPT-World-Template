# Oman AreaData continuation — 2026-09-26

Branch `codex/asia-domestic-20260926`; ignored local candidate `generated/oman-areadata-20260926`. Status: **partial, unpublished, no independent `ACCEPT`**. The tracked [source audit](../../evidence/oman-ncsi-yearbook-source-audit-2026-09-26.md) and [producer check](../../evidence/oman-country-lesson-audit-2026-09-26.md) delimit the evidence. Private `dashboard.json` SHA-256: `017a7ff4e09f430f362d0624b3545be607e8ae787105dff5f5120d4535beec23`. Private original, receipt, field audit and output hashes remain in the candidate. Environment: Windows/PowerShell, Node 24, Python 3, Poppler and Codex in-app browser; date 2026-09-26. No Oman hosting destination is configured.

## Replay

Read `evidence/SOURCE_PREFLIGHT.md` and `.json` first. The initial preflight has no Oman-specific leads. The generator refuses an existing output directory; for replay use a fresh sibling candidate or preserve the original privately before changing it.

```powershell
node scripts/create-country.mjs --country Oman --out generated/oman-areadata-20260926
python scripts/fetch-oman-ncsi-yearbook2026.py --project generated/oman-areadata-20260926
python scripts/import-oman-ncsi-yearbook2026.py --project generated/oman-areadata-20260926
node scripts/validate-country.mjs --project generated/oman-areadata-20260926
node scripts/build-country.mjs --project generated/oman-areadata-20260926
node scripts/verify-oman-ncsi-yearbook-output.mjs generated/oman-areadata-20260926
npm run check
npm test
```

The fixed hash rejects changed NCSI PDF bytes. The importer replaces its own source/indicator IDs and removes the seven unverified reference ADM1 features. The PDF and candidate are excluded from Git; redistribution terms need review. Replaying changes `generated_at` and therefore the dataset hash, while keeping verified source numbers fixed.

## Verified portion and limits

- NCSI Year Book 2026 Table 7-2, PDF pp. 36–37 contributes **75 territories**, **three registered-population indicators**, **450 direct nationality observations** and **225 AreaData-calculated totals** for **2023–2025**. All six numeric source columns were parsed. Table 6-2's 36 parent totals and Table 8-2's national 2025 total match. Other yearbook tables and 2020 eCensus remain unassessed or unacquired.
- Wilayats completely cover their parent governorate for every year and nationality; governorates completely cover national. 2025 national **5,359,557** = **3,039,349 Omani + 2,320,208 expatriate**. The WDI 2025 **5,494,691** is a separate midyear international estimate, not silently reconciled. No legal code or polygon was joined; statistical reporting units are not certified planning authorities.
- Browser checked national → Muscat governorate → Muscat Wilayat → Muscat governorate whole, then Dhofar → Salalah. The same-name parent reselection changed the value from **45,167** back to **1,532,486** without a separate zoom action. Salalah thematic comparison showed 10/10 Dhofar Wilayat values; focusing Taqah kept Salalah selected. Salalah planning had zero acquired documents and labelled the draft outputs unapproved. One viewport screenshot was visually inspected.
- Twelve output cases generated diagnostic CSV/HTML/Markdown, planning HTML and evidence CSV. Source value, year, source locator, calculated provenance, first/last internal rows, counts and hashes matched. Full-table print, Word/PDF, all 42 scenarios and final visual-layout audit are not complete.

`validate-country` passed with zero errors and one material warning for missing verified country-specific planning documents. Build, output verifier, AreaData `npm run check` and **218/218** tests passed. Kit feedback/Git IDs are in [KIT_FEEDBACK_HANDOFF.md](KIT_FEEDBACK_HANDOFF.md). Independent audit, Hosting and Public remain undone.

## Next work

1. Inventory the remaining NCSI yearbook numeric tables and 2020 eCensus local datasets; inspect population definitions/temporal method changes and add compatible nonpopulation local indicators with denominators.
2. Obtain official 11-governorate/63-Wilayat code and current boundary editions; examine changes including Sinaw and Al Jabal Alakhdar. Keep the incomplete geoBoundaries shapes unjoined.
3. Audit the effective Urban Planning Law, Governorates System, full spatial strategy and actual plan/decision/fiscal/performance documents for contrasting Muscat, Dhofar/Salalah, Al Wusta/Ad Duqm and Sharqiyah North/Sinaw. Separate lawful plan makers from statistical Wilayats.
4. Close the 42 scenarios, whole-table print, output layout, source terms and independent `ACCEPT` before any hosting.
5. Continue the requested Middle East sequence. At this checkpoint Asia 50 = **0 ACCEPT, 14 partial, 1 research-only, 35 unstarted**; Middle East 19 = **0 ACCEPT, 12 partial, 1 research-only, 6 unstarted**. Next unstarted country: Kuwait.

Only code, public-source leads, evidence and status, not the private dataset or original PDF, are saved to GitHub.

# Indonesia AreaData handoff — 2026-09-27 JST

**Status: local census partial candidate, independent `ACCEPT` pending, unpublished.** Asia ledger after this candidate: 0 complete, 28 partial, 1 research-only, 21 not started. Next unstarted priority: Philippines. The separate ignored project is `generated/indonesia-areadata-20260927`; code, source manifests and audit documents are tracked. No Indonesia Hosting/Public destination is assigned.

## Evidence and decisions

- BPS SP2020 Table 1 country page plus 34 province drill-down HTML originals are pinned by URL, bytes, SHA-256 and retrieval date. The 35 original tables carry three selected numeric columns and 1,749 cells including duplicated province-page TOTAL rows. National, 34 province and 514 kabupaten/kota 2020 reporting rows yield **549 territories, three indicators and 1,647 direct observations**. National population **270,203,917**. All sex and parent/child totals reconcile. Four other tables in the official population catalogue and other census themes remain `priority_unassessed`.
- BPS 2020 source codes are not automatically current Kemendagri codes or legal planning units. Bogor `3201` and Bogor `3271` have the same source name but distinct IDs and counts. Later Papua splits make the 34-province partition historical. No official compatible polygon is joined; initial geoBoundaries reference shapes were removed.
- A Surabaya JDIH hosted copy of Permendagri 86/2017, 644 pages, is archived. Selected definitions and provisions were read. It is a national legal reference only. Jawa Barat RPJMD 2025–2029 has official JDIH and province catalogue locations, but its PDF body was not acquired; no local plan, budget, actual expenditure or evaluation is attached.

[Source audit](../../evidence/indonesia-sp2020-source-audit-2026-09-27.md), [start sheet](../../evidence/indonesia-country-start-2026-09-27.md), [Task Contract](../../evidence/indonesia-task-contract-2026-09-27.md), and [producer lesson audit](../../evidence/indonesia-country-lesson-audit-2026-09-27.md) set the evidence boundary. The ignored candidate holds originals, full Table 1 numeric audit, column inventory, import and actual-output hashes.

## Reproduce and inspect

In the repository root with Python `requests`/`pypdf` and Node dependencies:

```powershell
node scripts/create-country.mjs --country Indonesia --out generated/indonesia-replay-new
python scripts/fetch-indonesia-sp2020.py --project generated/indonesia-replay-new
python scripts/fetch-indonesia-planning.py --project generated/indonesia-replay-new
python scripts/import-indonesia-sp2020.py --project generated/indonesia-replay-new
node scripts/validate-country.mjs --project generated/indonesia-replay-new
node scripts/build-country.mjs --project generated/indonesia-replay-new
node scripts/verify-indonesia-sp2020-output.mjs generated/indonesia-replay-new
npm run check
npm test
```

Producer run: validator **zero errors/warnings**, site built, seven source/output cases passed, `npm run check` 155 and `npm test` 218/218. The verifier checks diagnostic CSV/HTML/Markdown, planning HTML, evidence CSV, source totals/locators, printable 34/23/6/27/29 comparisons and national-only law document scope. Browser at `127.0.0.1:4187` confirmed Indonesia→Jawa Barat→Bogor `3201`→same Jawa Barat whole-area reselection. The planning page reports no acquired Jawa Barat local plan. These are producer checks, **not** all 42 scenarios or independent acceptance.

## Remaining before a complete Indonesia edition

1. Acquire and audit all other SP2020 population tables and relevant sector/fiscal publications by original numeric column, definition, denominator and local grain; check availability of newer subnational statistics and source terms.
2. Acquire dated official historical/current code registers and 2020-compatible province/kabupaten/kota polygons. Resolve type and Papua split crosswalks before a map or legal-plan join.
3. Audit present planning law/amendments and guidance, acquire the actual Jawa Barat RPJMD body plus representative province/kabupaten/kota RPJMD, RKPD/APBD, expenditure and official evaluation originals. Confirm legal jurisdiction and text before attaching.
4. Complete applicable 42 scenarios, missing/edge cases, Indonesian language, mobile/print, Word/PDF outputs and independent `ACCEPT`. Assign an Indonesia-specific Hosting/Public scope and verify deployed JSON/rendered URLs only after acceptance.

Kit feedback is source-location-only (`official_location_identified`) until Kit independently acquires and audits the leads. It transfers no raw originals, observations or country acceptance. Record AreaData adapter commit, Kit import commit, validation and remote parity in [Kit handoff](KIT_FEEDBACK_HANDOFF.md) after source feedback import. Local: partial candidate. GitHub: scoped code/audit/source leads pending commit. Hosting: none. Public: none.

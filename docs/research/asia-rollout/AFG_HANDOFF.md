# Afghanistan AreaData continuation — 2026-09-27 JST

Branch `codex/asia-domestic-20260926`; ignored candidate `generated/afghanistan-areadata-20260927`. **Partial, local, unpublished; no independent `ACCEPT`.** Consult [source audit](../../evidence/afghanistan-nsia1404-source-audit-2026-09-27.md), [start sheet](../../evidence/afghanistan-country-start-2026-09-27.md), [Task Contract](../../evidence/afghanistan-task-contract-2026-09-27.md), [producer lesson audit](../../evidence/afghanistan-country-lesson-audit-2026-09-27.md). Dataset SHA-256, receipt and actual-output hashes are in the ignored candidate's `evidence/` directory.

## Rebuild and verified scope

The initial country preflight was inspected. NSIA's September 2025 168-page estimated-population PDF was acquired and hash-pinned, with a **TLS certificate-name mismatch** caveat. The 76 numbered tables were inventoried by first page, title, numeric-column family and status. Only Table 4's three 1404/2025–26 population/sex fields were adopted, with independent province-population cross-check against Table 76. Full national 36,435,197 includes an unallocated 1.5 million nomadic estimate. The 34 provinces cover a different settled subtotal 34,935,197. The national WDI 2025 midyear figure 43,844,111 is another series. Six NSIA indicators yield 108 direct observations, 36 statistical nodes (country + settled scope + 34 provinces), zero matched official polygons and zero acquired area-plan bodies. Province source serials are internal locators, not official codes.

```powershell
node scripts/create-country.mjs --country Afghanistan --out generated/afghanistan-areadata-NEW
# Place the hash-pinned NSIA PDF from the source-audit URL in raw/nsia-population-1404.pdf.
# Acquisition currently requires a valid-TLS official mirror or explicit source-identity review.
python scripts/inventory-afghanistan-nsia1404.py --project generated/afghanistan-areadata-NEW
python scripts/import-afghanistan-nsia1404.py --project generated/afghanistan-areadata-NEW
node scripts/validate-country.mjs --project generated/afghanistan-areadata-NEW
node scripts/build-country.mjs --project generated/afghanistan-areadata-NEW
node scripts/verify-afghanistan-nsia1404-output.mjs generated/afghanistan-areadata-NEW
node scripts/serve.mjs --dir generated/afghanistan-areadata-NEW/site --port 4205
```

2026-09-27 Windows local: validator zero errors/warnings, build, seven actual-output cases including full 34-row printable comparison, check 151 JS/modules/templates, tests 218/218. In-app browser: WDI root and separate NSIA national count, settled-only partial-coverage label, Herat province 2,383,202, Herat→settled parent re-selection updating title/URL and clearing child, explicit no-boundary substitute. Selection-driven output checks are producer-side, not independent 42-scenario acceptance. The planning page gives Kabul and Herat **city** source locations as references only; no province plan, local budget, actual or official evaluation was acquired.

## Remaining before country completion

1. Reacquire NSIA original with verified TLS identity or authenticated official mirror. Establish reuse terms.
2. Semantically audit Table 3 and 34 administrative-unit tables, 34 age tables, Kabul city districts, Tables 74–75 and Table 4 old years; resolve Table 76 household discrepancies and historical sex-count conflict. Do not turn the unfinished inventory into a zero or completed thematic coverage.
3. Obtain current official province/district/municipal codes and same-edition boundaries. Locate the legally competent planning units separately from NSIA statistical units.
4. Acquire applicable current laws/guidance, actual approved local plans, budgets, implementation and evaluations by unit, with period and official status. Herat city announcement is not a Herat province plan.
5. Check all 42 applicable scenarios, source-to-screen/export equality, narrow and print layouts, current local-language needs, local practitioners, then independent `ACCEPT` and a separately assigned hosting/public destination.

AreaData's new official source locations are eligible for Kit feedback as `official_location_identified` only. Kit has not independently retrieved or adopted them. Local, GitHub, Hosting and Public status must be recorded separately. The next not-started priority is Nepal; earlier Middle East partial editions remain unfinished.

## GitHub and Kit handoff

AreaData's importer, producer audit and six official-source selections were committed at `58759b4c06d97ba2a2bc2ac741195dfe7ca66c01`. The exported `evidence/KIT_SOURCE_FEEDBACK.json` carries that exact origin commit, 183 leads across 25 countries. Kit accepted the bundle in dry-run and import, then committed/pushed its registry at `9648a4ea8e3839f25d37956d106b2850b89fe12d`; six AFG records remain `official_location_identified` / `not_acquired_by_kit_preflight`. [The Kit handoff register](KIT_FEEDBACK_HANDOFF.md) records both check/test gates. AreaData bundle and this handoff are committed in the following AreaData commit.

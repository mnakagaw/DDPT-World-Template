# Americas country completion contract

The Americas gateway registry contains 57 UN M49 countries and areas. A regional map, WDI/WPP country series, a source location, or a successful site build does not complete a country adapter.

## Required country evidence

Each country or area needs explicit evidence for:

1. official statistics office and current Census round;
2. Census results, table catalog and machine-readable or PDF products;
3. official codes, statistical geography, ADM1/ADM2 and usable municipality correspondence;
4. a semantic inventory of every acquired sheet, table and numeric field;
5. a terminal disposition for every numeric field: `integrated`, `not_adopted`, `unavailable`, `restricted`, or `failed_with_evidence`, always with a reason;
6. population, age/sex, households/housing, drinking water, sanitation, electricity, education/literacy, employment, disability, migration, urban/rural and ethnicity; and a documented search/disposition for health, nutrition and poverty;
7. planning law, planning guidance, current plans, budgets, implementation reports and evaluations, while distinguishing the legal planning authority from lower diagnostic geography.

The process states remain separate: `identified`, `accessed`, `acquired`, `inspected`, `geography_matched`, and `adopted`. A start URL or `identified` state is incomplete. Missing, unavailable, restricted and acquisition failure are different outcomes.

## Required evidence files

- `evidence/SOURCE_PREFLIGHT.json`: source discovery and process states;
- `evidence/COUNTRY_SEMANTIC_INVENTORY.json`: table-and-field dispositions and theme coverage;
- `evidence/COUNTRY_COMPLETION_MATRIX.json`: all 57 country/area completion states;
- `evidence/TERRITORIAL_SUMMARY_AUDIT.json`: latest and explicit-period value, year, source and status parity;
- country source payloads, receipts, hashes and geography crosswalks outside the public site when redistribution is not established.

`node scripts/build-country-completion-matrix.mjs --project <project>` creates the matrix without promoting incomplete evidence. `node scripts/verify-regional-delivery.mjs --project <project> --require-publishable` refuses an Americas release until all 57 records are complete and a separate audit records ACCEPT.

## Post-build display rule

On territorial pages, `latest-available` resolves independently for every selected-area indicator. The basic facts, full indicator card, CSV and diagnostic output must show the same value, actual source year, source ID and status. A numeric zero is observed data. Thematic comparisons keep a common explicit period so rankings do not mix years silently.

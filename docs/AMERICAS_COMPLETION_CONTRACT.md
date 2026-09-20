# Americas country completion contract

The Americas gateway registry contains 57 UN M49 countries and areas. A regional map, WDI/WPP country series, a source location, a terminal research disposition, or a successful site build does not complete a country adapter.

The matrix exposes two different results:

- `source_review_complete`: every required domain and theme has an evidence-backed terminal review result. `not_adopted`, `unavailable`, `restricted`, and `failed_with_evidence` may close this review status.
- `country_edition_complete`: every required source domain has reached the required acquired, geography-matched, and adopted stage. A resident edition must have a complete eligible population-total field. Every other theme must have either a complete integrated field with `country_edition_eligible=true`, or an explicit terminal gap carrying `edition_gap_closed=true`, a controlled `gap_kind`, a reason, complete review coverage, and source evidence. A closed gap remains `data_available=false` and never creates a value. A formally evidenced area with no permanent resident population may use `edition_mode=nonresident_area_profile`; only that mode may close resident Census and municipal-planning requirements as `structurally_not_applicable`, and every exception must carry an applicability basis and source evidence.

## Required country evidence

Each country or area needs explicit evidence for:

1. official statistics office and current Census round;
2. Census results, table catalog and machine-readable or PDF products;
3. official codes, statistical geography, ADM1/ADM2 and usable municipality correspondence;
4. a semantic inventory of every acquired sheet, table and numeric field;
5. a terminal source-review disposition for every numeric field: `integrated`, `not_adopted`, `unavailable`, `restricted`, or `failed_with_evidence`, always with a reason; only `integrated` and country-edition-eligible fields count toward the country edition;
6. population, age/sex, households/housing, drinking water, sanitation, electricity, education/literacy, employment, disability, migration, urban/rural and ethnicity; and a documented search/disposition for health, nutrition and poverty;
7. planning law, planning guidance, current plans, budgets, implementation reports and evaluations, while distinguishing the legal planning authority from lower diagnostic geography.

The process states remain separate: `identified`, `accessed`, `acquired`, `inspected`, `geography_matched`, and `adopted`. A start URL or `identified` state is incomplete. Missing, unavailable, restricted and acquisition failure are different outcomes.

## Required evidence files

- `evidence/SOURCE_PREFLIGHT.json`: source discovery and process states;
- `evidence/COUNTRY_SEMANTIC_INVENTORY.json`: table-and-field dispositions and theme coverage;
- `evidence/COUNTRY_COMPLETION_MATRIX.json`: all 57 country/area completion states;
- `evidence/TERRITORIAL_SUMMARY_AUDIT.json`: latest and explicit-period value, year, source and status parity;
- country source payloads, receipts, hashes and geography crosswalks outside the public site when redistribution is not established.

`node scripts/build-country-completion-matrix.mjs --project <project>` creates both statuses without promoting incomplete evidence. `node scripts/verify-regional-delivery.mjs --project <project> --require-publishable` refuses an Americas release until all 57 `country_edition_complete` records are true and a new independent audit records `ACCEPT`. A previous audit does not transfer to a rebuilt candidate.

Run `python scripts/refresh-americas-source-inventories.py --project <project>` after the final country acquisition pass and before the completion matrix. It reconciles every file under `raw`, accounts for every XLSX as a unique workbook or byte-identical duplicate, preserves existing adjudications, and records every remaining numeric field as explicitly reviewed but not adopted. `validate-americas-evidence.mjs` rejects any missing or extra raw/XLSX inventory path.

For multi-country releases, use `node scripts/apply-country-edition-batch.mjs --project <project> --spec <batch.json>`. The spec is a non-empty JSON array of `{ "bundle": "relative/path.json", "manifest": "relative/path.json" }` pairs, resolved relative to the spec file. The batch rejects duplicate or mismatched country IDs, applies every country in memory, validates the combined dataset, writes the shared evidence ledgers, and generates the site once. It does not relax any country contract or publication gate.

## Post-build display rule

On territorial pages, `latest-available` resolves independently for every selected-area indicator. The basic facts, full indicator card, CSV and diagnostic output must show the same value, actual source year, source ID and status. A numeric zero is observed data. Thematic comparisons keep a common explicit period so rankings do not mix years silently.

# Americas country completion contract

The Americas gateway registry contains 57 UN M49 countries and areas. A regional map, WDI/WPP country series, a source location, a terminal research disposition, or a successful site build does not complete a country adapter.

The matrix exposes two different results:

- `source_review_complete`: every required statistical source domain and all 15 themes have an evidence-backed terminal review result. `not_adopted`, `unavailable`, `restricted`, and `failed_with_evidence` may close this review status.
- `country_edition_complete`: the statistical diagnostic edition is ready. An ordinary resident edition needs reviewed statistical domains and all 15 theme reviews, locally integrated population and age/sex, a domestic hierarchy, at least 10 distinct `observed` indicators on domestic territories, and local integrated evidence in at least six of the eight diagnostic groups below. Country-level observations, common international series, and terminal gaps do not count toward the local indicator or group thresholds. A formally evidenced area with no permanent resident population may use `edition_mode=nonresident_area_profile`; only that mode may close resident Census requirements as `structurally_not_applicable`, and every exception must carry an applicability basis and source evidence.
- `planning_readiness`: planning law, guidance, plan/budget/implementation/evaluation evidence is reported separately as `ready` or `incomplete`. It does not raise or lower statistical `country_edition_complete`.

The eight diagnostic groups are: housing/services (housing, drinking water, sanitation or electricity), education, employment, disability/health, migration/urban, ethnicity, nutrition, and poverty. A group counts only when at least one eligible integrated indicator in that group has an `observed` value on a domestic territory.

Each row also carries one mutually exclusive depth classification: `source_review_incomplete`, `source_review_complete`, `national_only`, `population_local_hierarchy_only`, `broad_local_edition`, or `structural_nonresident_exception`. Only `broad_local_edition` and the strictly evidenced nonresident exception set `country_edition_complete=true`. The matrix records the domestic territory count, distinct local observed indicator IDs, integrated local themes, diagnostic groups, the fixed 10-indicator and six-group thresholds, and the resulting classification so that the count is reproducible from the canonical dataset.

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

A completed statistical source domain must point to at least one retained project object through `object_path` or `path`, the SHA-256 of its actual bytes, and an exact table, sheet/cell range, API field, or page-section locator. A legacy `audit`, `receipt`, `raw`, `inspection`, or `inventory` path by itself does not complete the domain. Administrative-code and boundary domains also require an explicit geography-match statement. `validate-americas-evidence.mjs` recomputes every raw inventory byte count and SHA-256 and independently verifies the retained objects used by every source-review-complete country/area.

## Required evidence files

- `evidence/SOURCE_PREFLIGHT.json`: source discovery and process states;
- `evidence/COUNTRY_SEMANTIC_INVENTORY.json`: table-and-field dispositions and theme coverage;
- `evidence/COUNTRY_COMPLETION_MATRIX.json`: all 57 country/area completion states;
- `evidence/TERRITORIAL_SUMMARY_AUDIT.json`: latest and explicit-period value, year, source and status parity;
- country source payloads, receipts, hashes and geography crosswalks outside the public site when redistribution is not established.

Every active `*_INTEGRATION_AUDIT.json` keeps its integration-time hash where available and must also carry `final_dataset_sha256` matching the canonical dataset after the matrix and coverage summary are finalized. Superseded deployment or public-verification receipts stay under an explicitly labelled superseded directory. A publishable package must contain the final deployment and HTTPS-verification receipts under `evidence/`, and its independent-audit record must identify the auditor, task/thread, audited commit, audited dataset SHA and command ledger.

`node scripts/build-country-completion-matrix.mjs --project <project>` creates both statuses without promoting incomplete evidence, synchronizes the matrix counts into `SOURCE_PREFLIGHT.json` and `data/dashboard.json` `analysis.coverage`, binds every integration audit to the resulting final dataset SHA, and regenerates the site plus `validation.json`. `node scripts/verify-regional-delivery.mjs --project <project> --require-publishable` is the pre-publication gate: it requires all 57 `country_edition_complete` records and a new independent `ACCEPT` bound to the final commit and dataset, but does not require receipts for a deployment that has not happened yet. After publication, rerun with `--require-published`; that post-publication gate additionally requires final FTPS and HTTPS-verification receipts inside the candidate `evidence/` package and `release.public_status=verified`. A previous audit does not transfer to a rebuilt candidate.

Run `python scripts/refresh-americas-source-inventories.py --project <project>` after the final country acquisition pass and before the completion matrix. It reconciles every file under `raw`, accounts for every XLSX as a unique workbook or byte-identical duplicate, preserves existing adjudications, and records every remaining numeric field as explicitly reviewed but not adopted. `validate-americas-evidence.mjs` rejects any missing or extra raw/XLSX inventory path, byte-count mismatch, SHA-256 mismatch, or completed source domain whose retained object, hash, or exact locator cannot be verified.

For multi-country releases, use `node scripts/apply-country-edition-batch.mjs --project <project> --spec <batch.json>`. The spec is a non-empty JSON array of `{ "bundle": "relative/path.json", "manifest": "relative/path.json" }` pairs, resolved relative to the spec file. The batch rejects duplicate or mismatched country IDs, applies every country in memory, validates the combined dataset, writes the shared evidence ledgers, and generates the site once. It does not relax any country contract or publication gate.

## Post-build display rule

On territorial pages, `latest-available` resolves independently for every selected-area indicator. The basic facts, full indicator card, CSV and diagnostic output must show the same value, actual source year, source ID and status. A numeric zero is observed data. Thematic comparisons keep a common explicit period so rankings do not mix years silently.

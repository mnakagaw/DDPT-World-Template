# Burkina Faso source adapter (review build)

This adapter reconstructs the local **2019 census geography** project; it does not certify a current legal-area crosswalk or a completed country release. Keep raw INSD downloads inside the ignored country project. The INSD catalogue's terms do not establish permission to redistribute them.

From the AreaData repository root, create a **new** country project (the generator refuses an existing output), then copy the Python adapters into its `scripts/` directory. The scripts locate the project relative to their own file path. The optional Word builder and QA require `python-docx` and Pillow; the local Codex bundled Python supplies both. Render with the isolated document renderer and LibreOffice, not Microsoft Word COM.

```powershell
$project = 'generated/burkina-faso-rebuild'
node scripts/create-country.mjs --country 'Burkina Faso' --out $project
New-Item -ItemType Directory -Force "$project/scripts" | Out-Null
Copy-Item scripts/country-burkina-faso/*.py "$project/scripts/"
python "$project/scripts/fetch-primary.py"
python "$project/scripts/fetch-supplementary.py"
$raw = "$project/raw/insd-rgph-2019"
pdftotext -layout "$raw/localities.pdf" "$raw/localities.txt"
pdftotext -layout "$raw/statistical_tables.pdf" "$raw/statistical_tables.txt"
pdftotext -layout "$raw/communal_disparities.pdf" "$raw/communal_disparities.txt"
pdftotext -layout "$raw/poverty_map.pdf" "$raw/poverty_map.txt"
python "$project/scripts/parse-localities.py"
python "$project/scripts/check-boundaries.py"
python "$project/scripts/build-dashboard.py"
python "$project/scripts/add-age-groups.py"
python "$project/scripts/add-census-themes.py"
python "$project/scripts/add-census-expanded.py"
python "$project/scripts/add-communal-model.py"
python "$project/scripts/add-poverty-atlas.py"
python "$project/scripts/add-planning.py"
python "$project/scripts/add-age-sex-pyramids.py"
python "$project/scripts/finalize-dataset.py"
python "$project/scripts/write-evidence.py"
node scripts/validate-country.mjs --project $project
node scripts/build-country.mjs --project $project
node scripts/country-burkina-faso/check-outputs.mjs $project
Copy-Item scripts/country-burkina-faso/screen-statistical-tables.py "$project/scripts/"
python "$project/scripts/screen-statistical-tables.py"
python scripts/country-burkina-faso/build-diagnostic-word.py --project $project --territory BFA --out "$project/exports/Territorial Development Diagnostic.docx"
# Render the DOCX with the isolated document renderer and inspect every page.
python scripts/country-burkina-faso/check-diagnostic-word.py --project $project --territory BFA --docx "$project/exports/Territorial Development Diagnostic.docx" --render-dir "$project/evidence/word-render-final"
```

The source PDFs and 2017 reference boundaries are acquired with byte hashes and receipts. `check-boundaries.py` writes candidate commune matches **for audit only**; unresolved ADM3 geometry is not joined to the dashboard. `write-evidence.py` inventories 12 acquired INSD PDFs and 581 statistical-table headings. Fifteen selected tables have adopted values; 566 need full numeric-column review. `screen-statistical-tables.py` identifies 3,900 numeric **positions** across modal text rows, not 3,900 verified semantic columns. `TABLE_COLUMN_SCREEN.csv` and `TABLE_NUMERIC_COLUMN_CANDIDATES.csv` let a reviewer locate the source body and candidate position, then confirm the printed header, denominator, period and geography before any new adoption. `SOURCE_RESOURCE_INVENTORY.json`, `SOURCE_TABLE_INVENTORY.csv`, `INDICATOR_INVENTORY.csv`, `THEME_COVERAGE.json`, the source receipts, and the validation report are evidence of the exact scope.

The four-level output check exercises Markdown, HTML and CSV, including 2019 population and 2018 modeled poverty. `screen-statistical-tables.py` creates an automated locator and numeric-row triage for all 581 tables; its 566 pending rows are **not** semantically reviewed or adopted. `build-diagnostic-word.py` creates the BFA-specific Word review artifact with source-grounded narrative and charts. Its source/value checks and four-page visual render are documented in [Word QA](../../docs/evidence/burkina-faso-word-qa-2026-09-24.md). The DOCX is not yet linked to a live selected-area download and does **not** replace 42-scenario acceptance, actual browser/print inspection, current consolidated-law review, local plan/budget collection, independent audit, hosting, or public verification. The source-specific review record is [the Burkina Faso adaptation note](../../docs/evidence/burkina-faso-areadata-adaptation-2026-09-24.md).

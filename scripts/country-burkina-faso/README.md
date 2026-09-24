# Burkina Faso source adapter (review build)

This adapter reconstructs the local **2019 census geography** project; it does not certify a current legal-area crosswalk or a completed country release. Keep raw INSD downloads inside the ignored country project. The INSD catalogue's terms do not establish permission to redistribute them.

From the AreaData repository root, create a **new** country project (the generator refuses an existing output), then copy the Python adapters into its `scripts/` directory. The scripts locate the project relative to their own file path.

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
python "$project/scripts/add-communal-model.py"
python "$project/scripts/add-poverty-atlas.py"
python "$project/scripts/add-planning.py"
python "$project/scripts/add-age-sex-pyramids.py"
python "$project/scripts/finalize-dataset.py"
python "$project/scripts/write-evidence.py"
node scripts/validate-country.mjs --project $project
node scripts/build-country.mjs --project $project
node scripts/country-burkina-faso/check-outputs.mjs $project
```

The source PDFs and 2017 reference boundaries are acquired with byte hashes and receipts. `check-boundaries.py` writes candidate commune matches **for audit only**; unresolved ADM3 geometry is not joined to the dashboard. `write-evidence.py` inventories 12 acquired INSD PDFs and 581 statistical-table headings. Eight selected tables have adopted values; 573 need full numeric-column review. `SOURCE_RESOURCE_INVENTORY.json`, `SOURCE_TABLE_INVENTORY.csv`, `INDICATOR_INVENTORY.csv`, `THEME_COVERAGE.json`, the source receipts, and the validation report are evidence of the exact scope.

The four-level output check exercises Markdown, HTML and CSV, including 2019 population and 2018 modeled poverty. It does **not** replace the 42-scenario acceptance, full visual/print inspection, article-level law review, plan/budget collection, Word review, independent audit, hosting, or public verification. The source-specific review record is [the Burkina Faso adaptation note](../../docs/evidence/burkina-faso-areadata-adaptation-2026-09-24.md).

# Reusable normalized census data

`central-america-population-v0.7.json` is the generated, source-linked population layer for the seven-country Central America pilot. It contains national and adopted subnational observations, geography identities, comparison memberships, source hashes, source URLs, periods, methods and reconciliation findings. It does not contain the acquired XLSX/PDF originals.

The file can be passed directly to the regional generator:

```sh
node scripts/create-central-america.mjs --source-dir generated/world/raw --census-data data/census/central-america-population-v0.7.json --out generated/central-america-with-census
```

The values use different official reference years: Belize 2022, Guatemala 2018, El Salvador 2024, Honduras 2013, Nicaragua 2005, Costa Rica 2022 and Panama 2023. Costa Rica is an official corrected estimate associated with partial 2022 census coverage. The Honduras Esparta municipality value is withheld because its official PDF conflicts with its identity and parent reconciliation; the national and department observations remain available.

Source-specific terms remain attached to every source. Before making this repository or a derivative data download public, review every source whose license is null or whose manifest `redistribution_status` is `terms_review_required`. The normalized file's presence in the current private repository is not a declaration that the official originals may be redistributed.

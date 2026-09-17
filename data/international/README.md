# Reusable international reference data

`un-wpp2024-central-america-population.json` and `un-wpp2024-americas-population.json` are compact extractions from the official UN World Population Prospects 2024 Rev.1 demographic-indicators workbook. The first contains the seven Central America pilot countries. The Americas file follows the 57-entry UN M49 Americas registry and contains the 55 country/area rows present in the workbook; BVT and SGS remain explicit missing entries. Both cover 2023–2026: 2023 is an estimate and 2024–2026 are medium-variant projections. Values are total population as of 1 July.

The original XLSX is not stored in Git. The normalized file records its official URL, retrieval time, byte size, SHA-256, license, scenario and source precision. Recreate it with:

```sh
python scripts/extract-un-wpp-central-america.py --input path/to/WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx --out data/international/un-wpp2024-central-america-population.json
python scripts/extract-un-wpp-americas.py --input path/to/WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx --registry path/to/world/data/dashboard.json --out data/international/un-wpp2024-americas-population.json
```

Pass it to the regional generator with `--un-population-data`. The UN series is same-period national context and never replaces official census observations used for subnational diagnosis.

# Reusable international reference data

`un-wpp2024-central-america-population.json` is a compact extraction from the official UN World Population Prospects 2024 Rev.1 demographic-indicators workbook. It contains the seven Central America pilot countries for 2023–2026: 2023 is an estimate and 2024–2026 are medium-variant projections. Values are total population as of 1 July.

The original XLSX is not stored in Git. The normalized file records its official URL, retrieval time, byte size, SHA-256, license, scenario and source precision. Recreate it with:

```sh
python scripts/extract-un-wpp-central-america.py --input path/to/WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx --out data/international/un-wpp2024-central-america-population.json
```

Pass it to the regional generator with `--un-population-data`. The UN series is same-period national context and never replaces official census observations used for subnational diagnosis.

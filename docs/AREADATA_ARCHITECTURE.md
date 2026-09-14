# AreaData architecture

Version 0.5 decision, 2026-09-14. AreaData is the first public service and repository output. WorldCensus and AreaPlan names or separate domains remain later decisions.

## One public service, three functions

| Initial URL | Function | Purpose in this version |
|---|---|---|
| `areadata.net/` | AreaData entry and dashboard | Map-first exploration from a broad area to a country and, as country adapters mature, provinces and municipalities. |
| `areadata.net/database/` | Data database | Indicator dictionary, territories, sources and downloadable observations. The future table builder, extracts and API are identified as later work. |
| `areadata.net/planning/` | Planning materials | Keeps the selected area while presenting verified laws, plans, budgets, evaluations and working outputs. An analysis group is not automatically a legal planning authority. |

The three pages use one dataset identity, one selected-area state, one indicator dictionary and one evidence register. A future `worldcensus.net` or `areaplan.net` must route into the same data and identity system rather than create a second copy.

## Central America pilot

The first operational scope is seven sovereign Central American countries: Belize, Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica and Panama. The public name must say **7-country pilot**. This project scope differs from UN M49 Central America (013), which also includes Mexico.

The entry hierarchy is:

1. Central America — 7-country pilot;
2. the seven source-identified countries;
3. verified country administrative hierarchies added by separate country adapters.

This pilot tests common behavior before scaling to Latin America and the world. Six countries reuse the existing Latin America source-location research; Belize has a separately verified official 2022 census portal. Source locations for all seven countries are written to the generated census preflight. None is treated as acquired municipal statistics until its original tables, codes and geography have been archived and checked.

Official national censuses are the primary series for country and subnational diagnosis. Same-year World Bank or other international values remain a separate reference series for cross-country context. Different census years are permitted and must be shown for every component; a mixed-year census sum is never labelled as a same-year total. See [CENSUS_SERIES_CONTRACT.md](CENSUS_SERIES_CONTRACT.md).

## Missing data and aggregation contract

Every indicator declares whether it can be aggregated. The runtime uses this order:

1. Use an exact, compatible observation for the selected area when one exists.
2. Otherwise, only an indicator with an approved method may be calculated.
3. Build a complete, non-overlapping cover using the highest available exact observations. A country total is preferred to its provinces; a province total is preferred to its municipalities.
4. Descend one level only when the parent has no exact value, the child membership is source-backed and complete, and every child is covered by compatible evidence.
5. Reject ancestor/descendant overlap and duplicate components.
6. If the cover is incomplete, show no total. Show a labelled covered subtotal, component count and missing-area list as diagnostic information.

This means missing municipalities have no effect on a Latin America calculation when their country’s exact nationwide value is available. If a nationwide value is missing, the system may use provinces only when every province is covered. It never fills a missing country with a selection of available cities.

Population is the only calculated indicator in the first pilot. The current international reference series uses a single selected year. A later census total may use the latest usable year in each country only under the explicit mixed-period rule and with every component year visible. Percentages are never averaged. A regional rate requires compatible numerator and denominator totals. Life expectancy and other non-additive measures require a separately approved weighted method and compatible weights; otherwise they remain unavailable. Source-reported and AreaData-calculated values receive different status labels in the screen and downloads.

## Scale checkpoints

Before adding all municipalities in the 20 countries, verify:

- selection and map performance with a representative large register;
- exact country totals remain the selected components when municipal records are added;
- full and incomplete country coverage cases;
- zero, missing, not collected and acquisition failure stay distinct;
- every calculated value can be reproduced from its exported component IDs;
- changing from a municipality back to the same parent clears the municipality and updates all evidence;
- database CSV and diagnostic CSV agree with the screen;
- planning materials follow only a single verified planning territory.

Country adapters can be added incrementally. A country with no municipal adapter still participates in a regional population total through its compatible nationwide source observation. Its municipal pages remain unavailable rather than receiving copied national values.

## Storage and scale test

The public pilot may continue to serve generated static JSON and CSV, but MariaDB 10.6 is the canonical structured store for the scaling experiment. It stores dataset versions, geographic identity and membership, indicator meaning, observations, source evidence, aggregation rules and calculation lineage. Raw Excel, CSV, PDF, GeoJSON and Parquet files remain immutable external assets with their paths and SHA-256 recorded in the database.

Real seven-country data test acquisition and definition differences. Separate synthetic benchmarks test 10,000 and 50,000 territories without presenting generated values as real evidence. The benchmark records import time, indexed query time, regional aggregation time, export time, database size and peak memory. Browser payloads remain selected extracts rather than full SQL dumps.

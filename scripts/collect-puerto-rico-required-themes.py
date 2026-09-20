#!/usr/bin/env python3
"""Build the Puerto Rico country-depth bundle from retained official sources.

Puerto Rico is kept as its own AreaData country/area branch.  The collector
reuses the exact Census Bureau ACS/PRCS 2019-2023 table prefixes and official
2023 cartographic boundary file already acquired for the USA adapter, but it
selects only FIPS state 72 and the 78 municipio (county-equivalent) rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


TABLES = [
    "B01003", "B01001", "B11001", "B25001", "B25047", "B15003",
    "B23025", "C18108", "B05002", "B03003", "B27010", "B17001",
    "B22003", "B28002",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def num(row, key):
    try:
        value = float(row[key])
        return value if value >= 0 else None
    except (KeyError, TypeError, ValueError):
        return None


def total(row, keys):
    values = [num(row, key) for key in keys]
    return None if any(value is None for value in values) else sum(values)


def ratio(numerator, denominator):
    return None if numerator is None or denominator is None or denominator <= 0 else round(numerator / denominator * 100, 4)


def field(table, n):
    return f"{table}_E{n:03d}"


SPECS = [
    ("PRI_PRCS_POP_TOTAL", "Population, PRCS 5-year estimate", "Population", "people", "B01003", lambda r: num(r, field("B01003", 1)), [1], None, "Resident population estimate."),
    ("PRI_PRCS_FEMALE_PCT", "Female population", "Population", "%", "B01001", lambda r: ratio(num(r, field("B01001", 26)), num(r, field("B01001", 1))), [26], [1], "Female population as a share of the total population."),
    ("PRI_PRCS_AGE_0_14_PCT", "Population aged 0–14", "Population", "%", "B01001", lambda r: ratio(total(r, [field("B01001", i) for i in [3, 4, 5, 27, 28, 29]]), num(r, field("B01001", 1))), [3, 4, 5, 27, 28, 29], [1], "Population aged 0–14 as a share of the total population."),
    ("PRI_PRCS_HOUSEHOLDS_TOTAL", "Households", "Households and housing", "households", "B11001", lambda r: num(r, field("B11001", 1)), [1], None, "Total households."),
    ("PRI_PRCS_HOUSING_UNITS_TOTAL", "Housing units", "Households and housing", "housing units", "B25001", lambda r: num(r, field("B25001", 1)), [1], None, "Total housing units."),
    ("PRI_PRCS_LACKING_PLUMBING_PCT", "Occupied housing units lacking complete plumbing facilities", "Water and sanitation", "% of occupied housing units", "B25047", lambda r: ratio(num(r, field("B25047", 3)), num(r, field("B25047", 1))), [3], [1], "Occupied housing units lacking complete plumbing facilities; this combined plumbing measure is not a separate drinking-water or sewer-access measure."),
    ("PRI_PRCS_HIGH_SCHOOL_OR_HIGHER_PCT", "Population age 25+ with high school credential or higher", "Education", "% of population age 25+", "B15003", lambda r: ratio(total(r, [field("B15003", i) for i in range(17, 26)]), num(r, field("B15003", 1))), list(range(17, 26)), [1], "Population age 25+ with a regular high school diploma, GED or higher attainment."),
    ("PRI_PRCS_LABOR_FORCE_PCT", "Population age 16+ in the labor force", "Employment", "% of population age 16+", "B23025", lambda r: ratio(num(r, field("B23025", 2)), num(r, field("B23025", 1))), [2], [1], "Population age 16+ in the labor force."),
    ("PRI_PRCS_DISABILITY_PCT", "Civilian noninstitutionalized population with a disability", "Disability", "%", "C18108", lambda r: ratio(total(r, [field("C18108", i) for i in [3, 4, 7, 8, 11, 12]]), num(r, field("C18108", 1))), [3, 4, 7, 8, 11, 12], [1], "Civilian noninstitutionalized population reporting one or more disability types."),
    ("PRI_PRCS_BORN_OUTSIDE_PR_PCT", "Population born outside Puerto Rico", "Migration", "%", "B05002", lambda r: ratio(total(r, [field("B05002", i) for i in [4, 9, 13]]), num(r, field("B05002", 1))), [4, 9, 13], [1], "Population born in another U.S. state, native-born outside the United States, or foreign-born, as a share of total population; these source categories are mutually exclusive and this measure is not identical to foreign-born population."),
    ("PRI_PRCS_HISPANIC_LATINO_PCT", "Hispanic or Latino population", "Race and ethnicity", "%", "B03003", lambda r: ratio(num(r, field("B03003", 3)), num(r, field("B03003", 1))), [3], [1], "Hispanic or Latino population of any race as a share of total population."),
    ("PRI_PRCS_UNINSURED_PCT", "Civilian noninstitutionalized population without health insurance", "Health", "%", "B27010", lambda r: ratio(total(r, [field("B27010", i) for i in [17, 33, 50, 66]]), num(r, field("B27010", 1))), [17, 33, 50, 66], [1], "Civilian noninstitutionalized population without health insurance coverage."),
    ("PRI_PRCS_POVERTY_PCT", "Population below the poverty level", "Poverty", "%", "B17001", lambda r: ratio(num(r, field("B17001", 2)), num(r, field("B17001", 1))), [2], [1], "Population for whom poverty status is determined with income below the poverty level."),
    ("PRI_PRCS_SNAP_HOUSEHOLDS_PCT", "Households receiving Nutrition Assistance", "Food assistance", "% of households", "B22003", lambda r: ratio(num(r, field("B22003", 2)), num(r, field("B22003", 1))), [2], [1], "Households receiving Food Stamps/SNAP or Puerto Rico Nutrition Assistance in the past 12 months; a program-participation measure, not a nutrition outcome."),
    ("PRI_PRCS_BROADBAND_PCT", "Households with broadband Internet subscription", "Connectivity", "% of households", "B28002", lambda r: ratio(num(r, field("B28002", 4)), num(r, field("B28002", 1))), [4], [1], "Households with broadband Internet subscription of any type."),
]


def load_geographies(path: Path):
    selected = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="|"):
            gid = row["GEO_ID"]
            if gid == "0400000US72":
                selected[gid] = {"id": "PRI", "level": "country", "code": "72", "name": "Puerto Rico"}
            elif gid.startswith("0500000US72"):
                code = gid[-5:]
                name = row["NAME"].removesuffix(", Puerto Rico").removesuffix(" Municipio")
                selected[gid] = {"id": f"PRI:PRCS2023:MUN:{code}", "level": "municipio", "code": code, "name": name}
    if len(selected) != 79:
        raise RuntimeError(f"Expected Puerto Rico plus 78 municipios, got {len(selected)}")
    return selected


def load_table(path: Path, areas):
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="|"):
            if row["GEO_ID"] in areas:
                rows[row["GEO_ID"]] = row
    if set(rows) != set(areas):
        raise RuntimeError(f"{path.name}: expected {len(areas)} Puerto Rico rows, got {len(rows)}")
    return rows


def urban_observations(path: Path, areas):
    ids = {area["code"]: area["id"] for area in areas.values() if area["level"] == "municipio"}
    rows, total_population, urban_population = {}, 0, 0
    ws = load_workbook(path, read_only=True, data_only=True)["2020_UA_COUNTY"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if str(row[0]).zfill(2) != "72":
            continue
        code = f"72{str(row[1]).zfill(3)}"
        if code not in ids:
            continue
        total_value, urban_value = int(row[4]), int(row[11])
        pct = round(float(row[12]) * 100, 4)
        if abs(pct - urban_value / total_value * 100) > 0.011:
            raise RuntimeError(f"Urban percentage does not reconcile for {code}")
        rows[ids[code]] = (pct, urban_value, total_value)
        total_population += total_value
        urban_population += urban_value
    if len(rows) != 78:
        raise RuntimeError(f"Expected 78 municipio urban rows, got {len(rows)}")
    rows["PRI"] = (round(urban_population / total_population * 100, 4), urban_population, total_population)
    return [
        {
            "territory_id": area,
            "indicator_id": "PRI_C2020_URBAN_POP_PCT",
            "period": "2020",
            "value": value,
            "status": "observed",
            "source_id": "pri-census-2020-urban-rural",
            "definition": "2020 Census population classified as urban as a share of total population.",
            "definition_id": "PRI-C2020-URBAN",
            "unit": "%",
            "population": "2020 Census total population",
            "measurement_method": "derived_from_source_counts",
            "source_locator": "2020_UA_COUNTY: POP_URB / POP_COU",
            "numerator": numerator,
            "denominator": denominator,
        }
        for area, (value, numerator, denominator) in sorted(rows.items())
    ]


def boundary_features(zip_path: Path, areas):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".work" / "python-packages"))
    import shapefile

    extracted = zip_path.parent / (zip_path.stem + "-extracted")
    extracted.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extracted)
    reader = shapefile.Reader(str(next(extracted.glob("*.shp"))))
    by_code = {area["code"]: area for area in areas.values() if area["level"] == "municipio"}
    features = []
    for record, shape in zip(reader.records(), reader.shapes()):
        data = record.as_dict()
        code = str(data["GEOID"])
        if code not in by_code:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "territory_id": by_code[code]["id"],
                "source_id": "pri-census-cartographic-boundaries-2023",
                "official_code": code,
                "code_system": "Census ANSI/FIPS",
                "geometry_edition": "2023 Census cartographic boundary 1:5,000,000",
                "join_method": "Exact Census municipio GEOID/FIPS join",
                "reference_only": True,
            },
            "geometry": shape.__geo_interface__,
        })
    if len(features) != 78:
        raise RuntimeError(f"Expected 78 municipio boundary features, got {len(features)}")
    return features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acs-raw", required=True)
    parser.add_argument("--urban-xlsx", required=True)
    parser.add_argument("--source-raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    acs = Path(args.acs_raw).resolve()
    urban = Path(args.urban_xlsx).resolve()
    source_raw = Path(args.source_raw).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).date().isoformat()
    areas = load_geographies(acs / "Geos20235YR-through-county.txt")
    tables = {table: load_table(acs / f"acsdt5y2023-{table.lower()}-through-county.dat", areas) for table in TABLES}
    metadata = {table: json.loads((acs / f"{table}-variables.json").read_text(encoding="utf-8")) for table in TABLES}

    territories = [
        {
            "id": area["id"], "country_id": "PRI", "name": area["name"],
            "level": "municipio", "type": "municipio", "parent_id": "PRI",
            "official_code": area["code"], "code_system": "Census ANSI/FIPS",
            "boundary_version": "2023 Census cartographic boundary 1:5,000,000",
            "valid_from": "2023-01-01",
        }
        for area in areas.values() if area["level"] == "municipio"
    ]
    indicators, observations, sources = [], [], []
    for iid, name, theme, unit, table, calc, numerator, denominator, definition in SPECS:
        source_id = f"pri-prcs-2023-{table.lower()}"
        formula = "+".join(field(table, i) for i in numerator) + (f" / {field(table, denominator[0])} * 100" if denominator else "")
        concept = metadata[table].get("variables", {}).get(f"{table}_{numerator[0]:03d}E", {}).get("concept", definition)
        indicators.append({"id": iid, "name": name, "theme": theme, "unit": unit, "definition": definition, "definition_id": f"PRCS5-2023-{table}", "population": concept, "measurement_method": "source_reported" if denominator is None else "derived_from_source_counts", "aggregation": "sum" if denominator is None else "none", "period_policy": "fixed_source_period", "series_family": "survey", "display_role": "primary", "source_id": source_id, "source_locator": f"{table}: {formula}"})
        if not any(source["id"] == source_id for source in sources):
            sources.append({"id": source_id, "name": f"2019–2023 Puerto Rico Community Survey 5-year Detailed Table {table}", "publisher": "United States Census Bureau", "url": f"https://data.census.gov/table/ACSST5Y2023.{table}?g=040XX00US72$0500000", "status": "ready", "retrieved_at": retrieved, "reference_period": "2019–2023 PRCS 5-year estimate", "geographic_level": "Puerto Rico and 78 municipios", "license": "United States Government public data; verify Census terms", "license_url": "https://www.census.gov/about/policies/open-gov/open-data.html", "source_locator": f"{table}: retained fields and formula listed on indicator", "note": "PRCS is collected separately for Puerto Rico and released within the ACS products. Margins of error remain in the archived source rows; AreaData displays estimates."})
        for gid, area in areas.items():
            row = tables[table][gid]
            value = calc(row)
            observations.append({"territory_id": area["id"], "indicator_id": iid, "period": "2023", "value": value, "status": "observed" if value is not None else "missing", "source_id": source_id, "definition": definition, "definition_id": f"PRCS5-2023-{table}", "unit": unit, "population": concept, "measurement_method": "source_reported" if denominator is None else "derived_from_source_counts", "source_locator": f"{table}: {formula}", "formula": formula, "numerator": None if denominator is None else total(row, [field(table, i) for i in numerator]), "denominator": None if denominator is None else num(row, field(table, denominator[0]))})

    urban_obs = urban_observations(urban, areas)
    urban_source = {"id": "pri-census-2020-urban-rural", "name": "2020 Census Puerto Rico municipio urban-rural population table", "publisher": "United States Census Bureau", "url": "https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural.html", "status": "ready", "retrieved_at": retrieved, "reference_period": "2020", "geographic_level": "Puerto Rico and 78 municipios", "license": "United States Government public data", "license_url": "https://www.census.gov/about/policies/open-gov/open-data.html", "source_locator": "2020_UA_COUNTY sheet; state 72; POP_URB / POP_COU", "note": "All 78 municipio rows are joined by exact five-digit FIPS and reconcile to the published component counts."}
    urban_indicator = {"id": "PRI_C2020_URBAN_POP_PCT", "name": "Urban population, 2020 Census", "theme": "Settlement", "unit": "%", "definition": "2020 Census population classified as urban as a share of total population.", "definition_id": "PRI-C2020-URBAN", "population": "2020 Census total population", "measurement_method": "derived_from_source_counts", "aggregation": "none", "period_policy": "fixed_source_period", "series_family": "census", "display_role": "primary", "source_id": urban_source["id"], "source_locator": "2020_UA_COUNTY: POP_URB / POP_COU"}
    sources.append(urban_source)
    indicators.append(urban_indicator)
    observations.extend(urban_obs)

    context_sources = [
        {"id": "pri-eia-electric-customers-2024", "name": "Electric Power Annual Table 12.1 — Puerto Rico ultimate customers served", "publisher": "U.S. Energy Information Administration", "url": "https://www.eia.gov/electricity/annual/table.php?t=epa_12_01.html", "status": "ready", "retrieved_at": retrieved, "reference_period": "2024", "geographic_level": "Puerto Rico", "raw_path": "raw/puerto-rico-required-themes/eia_customers_2024.html", "license": "United States Government public data", "note": "Customer accounts served by the electric system. This is not a household electricity-access rate and is not allocated to municipios."},
        {"id": "pri-health-brfss-obesity-2024", "name": "Plan de Acción para la Prevención de la Obesidad en Puerto Rico 2026–2028", "publisher": "Departamento de Salud de Puerto Rico / Comisión de Alimentación y Nutrición", "url": "https://www.salud.pr.gov/CMS/DOWNLOAD/10416", "status": "ready", "retrieved_at": retrieved, "reference_period": "2024", "geographic_level": "Puerto Rico", "license": "Official government publication; verify reuse terms", "note": "The plan reports PR-BRFSS adult obesity prevalence of 36.2% for 2024. It is a survey estimate and is not allocated to municipios."},
    ]
    context_indicators = [
        {"id": "PRI_EIA_ELECTRIC_CUSTOMERS_TOTAL_2024", "name": "Electricity ultimate customers served", "theme": "Electricity", "unit": "customer accounts", "definition": "Number of ultimate electricity customer accounts served across all end-use sectors in Puerto Rico.", "definition_id": "EIA-EPA-12.1-PRI-2024", "population": "Residential, commercial, industrial and transportation customer accounts", "measurement_method": "source_reported", "aggregation": "none", "period_policy": "fixed_source_period", "series_family": "administrative", "display_role": "context", "source_id": context_sources[0]["id"], "source_locator": "Table 12.1, Annual totals, 2024, All Sectors"},
        {"id": "PRI_BRFSS_ADULT_OBESITY_PCT_2024", "name": "Adult obesity prevalence", "theme": "Nutrition", "unit": "%", "definition": "Share of adults classified with obesity in the Puerto Rico Behavioral Risk Factor Surveillance System.", "definition_id": "PR-BRFSS-OBESITY-2024", "population": "Adults in Puerto Rico represented by PR-BRFSS", "measurement_method": "survey_estimate", "aggregation": "none", "period_policy": "fixed_source_period", "series_family": "survey", "display_role": "context", "source_id": context_sources[1]["id"], "source_locator": "Plan page 11, Figure 2, obesity series, 2024"},
    ]
    context_observations = [
        {"territory_id": "PRI", "indicator_id": context_indicators[0]["id"], "period": "2024", "value": 1511848, "status": "observed", "source_id": context_sources[0]["id"], "definition": context_indicators[0]["definition"], "definition_id": context_indicators[0]["definition_id"], "unit": context_indicators[0]["unit"], "population": context_indicators[0]["population"], "measurement_method": "source_reported", "source_locator": context_indicators[0]["source_locator"]},
        {"territory_id": "PRI", "indicator_id": context_indicators[1]["id"], "period": "2024", "value": 36.2, "status": "observed", "source_id": context_sources[1]["id"], "definition": context_indicators[1]["definition"], "definition_id": context_indicators[1]["definition_id"], "unit": context_indicators[1]["unit"], "population": context_indicators[1]["population"], "measurement_method": "survey_estimate", "source_locator": context_indicators[1]["source_locator"]},
    ]
    sources.extend(context_sources)
    indicators.extend(context_indicators)
    observations.extend(context_observations)

    boundary_source = {"id": "pri-census-cartographic-boundaries-2023", "name": "2023 Census municipio cartographic boundary file, 1:5,000,000", "publisher": "United States Census Bureau", "url": "https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html", "status": "ready", "retrieved_at": retrieved, "reference_period": "2023", "geographic_level": "Puerto Rico municipios", "license": "United States Government public data; cartographic boundaries are reference geometry", "license_url": "https://www.census.gov/about/policies/open-gov/open-data.html", "note": "Official Census cartographic boundaries joined by exact municipio FIPS/GEOID; reference geometry is not a legal boundary certification."}
    sources.append(boundary_source)
    features = boundary_features(acs / "cb_2023_us_county_5m.zip", areas)
    member_ids = sorted(area["id"] for area in areas.values() if area["level"] == "municipio")
    receipts = []
    for file in [acs / "Geos20235YR-through-county.txt", *(acs / f"acsdt5y2023-{table.lower()}-through-county.dat" for table in TABLES), acs / "cb_2023_us_county_5m.zip", urban, source_raw / "eia_customers_2024.html", source_raw / "receipt.json"]:
        receipts.append({"path": str(file), "bytes": file.stat().st_size, "sha256": sha(file)})
    audit = {
        "schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "PRI",
        "status": "complete_country_depth_bundle", "selected_geography_count": 79, "municipio_count": 78,
        "indicator_count": len(indicators), "observation_count": len(observations), "boundary_feature_count": len(features),
        "prcs_rows_per_table": 79, "urban_rows": len(urban_obs), "national_context_observations": 2,
        "evidence_policy": "PRCS/ACS estimates, 2020 Census urban-rural counts, EIA customer accounts and PR-BRFSS obesity remain distinct by period, unit, method and geography. National context values are not copied to municipios.",
        "receipts": receipts,
    }
    bundle = {
        "schema_version": "1.0", "country_area_id": "PRI", "period": "2023", "replace_country_branch": True,
        "territories": territories, "terminal_territory_ids": member_ids,
        "comparisons": [{"parent_id": "PRI", "member_ids": member_ids, "label": "78 municipios", "membership_note": "Puerto Rico municipio geography; municipios are Census county equivalents. Exact FIPS joins are used.", "source_ids": ["pri-prcs-2023-b01003", boundary_source["id"]]}],
        "indicators": indicators, "observations": observations, "sources": sources,
        "boundaries": {"type": "FeatureCollection", "features": features}, "audit": audit,
    }
    (out / "puerto-rico-country-depth-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "PUERTO_RICO_COLLECTION_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: audit[key] for key in ["selected_geography_count", "municipio_count", "indicator_count", "observation_count", "boundary_feature_count"]}, indent=2))


if __name__ == "__main__":
    main()

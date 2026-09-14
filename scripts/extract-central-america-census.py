"""Extract the first audited census population layer without editing source XLSX files."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook


INDICATOR_ID = "CENSUS_POP_TOTAL"
BELIZE_DISTRICTS = ["Corozal", "Orange Walk", "Belize", "Cayo", "Stann Creek", "Toledo"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_entry(receipt: dict, source_id: str) -> dict:
    entry = next(item for item in receipt["entries"] if item["source_id"] == source_id)
    if entry["status"] != "acquired":
        raise ValueError(f"Required source is not acquired: {source_id}")
    return entry


def source_path(root: Path, entry: dict) -> Path:
    path = root.joinpath(*entry["filename"].split("/"))
    if sha256(path) != entry["sha256"]:
        raise ValueError(f"Receipt hash mismatch: {entry['source_id']}")
    return path


def finite_number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Expected a finite number at {label}")
    return value


def difference(left, right):
    return float(left) - float(right)


def source_record(entry: dict, note: str, license_value=None, license_url=None) -> dict:
    return {
        "id": entry["source_id"],
        "name": entry["title"],
        "publisher": entry["publisher"],
        "url": entry["final_url"],
        "catalog_url": entry["catalog_url"],
        "status": "ready",
        "retrieved_at": entry["retrieved_at"] if "retrieved_at" in entry else None,
        "reference_period": entry["census_year"],
        "sha256": entry["sha256"],
        "bytes": entry["bytes"],
        "license": license_value,
        "license_url": license_url,
        "geographic_level": "subnational",
        "note": note,
    }


def observation(territory_id, value, source_id, period, footnote, precision="source_decimal"):
    return {
        "territory_id": territory_id,
        "indicator_id": INDICATOR_ID,
        "period": str(period),
        "value": finite_number(value, f"{territory_id} population"),
        "status": "observed",
        "source_id": source_id,
        "footnote": footnote,
        "source_precision": precision,
    }


def extract_belize(root: Path, receipt: dict):
    general_entry = source_entry(receipt, "BLZ_C2022_GENERAL_CHARACTERISTICS")
    locality_entry = source_entry(receipt, "BLZ_C2022_POP_SETTLEMENT_SEX")
    general_path, locality_path = source_path(root, general_entry), source_path(root, locality_entry)

    general_book = load_workbook(general_path, read_only=True, data_only=True)
    locality_book = load_workbook(locality_path, read_only=True, data_only=True)
    try:
        admin = general_book["Admin_Area"]
        national = finite_number(admin["D4"].value, "BLZ Admin_Area!D4")
        published_admin = {
            str(admin.cell(row, 2).value).strip(): finite_number(admin.cell(row, 4).value, f"BLZ Admin_Area!D{row}")
            for row in range(4, admin.max_row + 1)
            if admin.cell(row, 2).value is not None and isinstance(admin.cell(row, 4).value, (int, float))
        }
        district_values = {name: published_admin[name] for name in BELIZE_DISTRICTS}
        territories, observations, comparisons, terminal_ids = [], [], [], []
        district_ids = []
        general_note = "SIB 2022 calibrated-weight census population estimate. The workbook retains fractional weighted values; SIB's report presents rounded persons."
        observations.append(observation("BLZ", national, general_entry["source_id"], 2022, general_note))
        for index, name in enumerate(BELIZE_DISTRICTS, start=1):
            territory_id = f"BLZ:C2022:DIST:{index}"
            district_ids.append(territory_id)
            territories.append({
                "id": territory_id,
                "country_id": "BLZ",
                "name": name,
                "level": "district",
                "type": "district",
                "parent_id": "BLZ",
                "official_code": None,
                "code_system": "No district code column in adopted SIB 2022 workbook",
                "boundary_version": None,
                "source_id": general_entry["source_id"],
                "geography_note": "District name as published by SIB; official code and polygon edition remain unverified.",
            })
            observations.append(observation(territory_id, district_values[name], general_entry["source_id"], 2022, general_note))
        comparisons.append({
            "parent_id": "BLZ",
            "member_ids": district_ids,
            "label": "Six Belize districts",
            "membership_note": "All six district totals published in SIB's 2022 general characteristics workbook. Codes and polygon boundaries remain unverified.",
            "source_ids": [general_entry["source_id"]],
        })

        sheet = locality_book["2022"]
        current_district = None
        locality_row_counts = {name: 0 for name in BELIZE_DISTRICTS}
        rejected = []
        published_totals = {}
        for row in range(5, sheet.max_row + 1):
            district_cell, name_cell = sheet.cell(row, 1).value, sheet.cell(row, 2).value
            if district_cell is not None:
                current_district = " ".join(str(district_cell).split())
            if current_district not in locality_row_counts or name_cell is None:
                continue
            name = str(name_cell).strip()
            value = sheet.cell(row, 5).value
            if name == "Total":
                published_totals[current_district] = finite_number(value, f"BLZ locality total row {row}")
                continue
            if name.lower().startswith("other "):
                rejected.append({"row": row, "district": current_district, "name": name, "reason": "Residual group is not one discrete locality."})
                continue
            finite_number(value, f"BLZ locality row {row}")
            locality_row_counts[current_district] += 1

        district_reconciliation = []
        for district in BELIZE_DISTRICTS:
            listed = published_totals[district]
            official = district_values[district]
            district_reconciliation.append({"district": district, "general_characteristics_total": official, "locality_table_total": listed, "difference": difference(listed, official)})
        audit = {
            "national_population": national,
            "district_count": len(district_ids),
            "district_sum": sum(district_values.values()),
            "district_sum_difference": difference(sum(district_values.values()), national),
            "published_discrete_localities_audited": sum(locality_row_counts.values()),
            "published_discrete_localities_by_district": locality_row_counts,
            "locality_adoption_status": "audited_not_loaded; no official code or statutory-type column, no verified polygons, and two district totals conflict with the adopted district table",
            "residual_rows_not_adopted_as_territories": rejected,
            "district_reconciliation": district_reconciliation,
            "precision_note": general_note,
        }
    finally:
        general_book.close()
        locality_book.close()
    return {
        "country_id": "BLZ",
        "period": "2022",
        "territories": territories,
        "observations": observations,
        "comparisons": comparisons,
        "terminal_territory_ids": terminal_ids,
        "sources": [
            source_record(general_entry, "National and district population source. Values are calibrated-weight estimates and retain source decimals."),
            source_record(locality_entry, "City/town/village/community population and sex table. Audited but not loaded as territories: residual rows, missing geographic codes and two district-total conflicts require reconciliation."),
        ],
        "audit": audit,
    }


def extract_guatemala(root: Path, receipt: dict):
    population_entry = source_entry(receipt, "GTM_C2018_POP_SEX_AGE_AREA")
    centroid_entry = source_entry(receipt, "GTM_C2018_POPULATED_PLACE_CENTROIDS")
    population_path, centroid_path = source_path(root, population_entry), source_path(root, centroid_entry)
    population_book = load_workbook(population_path, read_only=True, data_only=True)
    centroid_book = load_workbook(centroid_path, read_only=True, data_only=True)
    try:
        national_sheet = population_book["A1_1"]
        municipality_sheet = population_book["A1_2"]
        place_sheet = population_book["A1_3"]
        centroid_sheet = centroid_book["A_3"]
        national = finite_number(national_sheet["C8"].value, "GTM A1_1!C8")
        territories, observations, comparisons, terminal_ids = [], [], [], []
        department_ids, departments = [], {}
        note = "INE XII Censo 2018 enumerated population (poblacion total censada) in the published A1 table."
        observations.append(observation("GTM", national, population_entry["source_id"], 2018, note, "integer"))
        for row, values in enumerate(national_sheet.iter_rows(min_row=10, max_row=31, min_col=1, max_col=3, values_only=True), start=10):
            code = str(values[0])
            name = str(values[1]).strip()
            value = finite_number(values[2], f"GTM A1_1!C{row}")
            territory_id = f"GTM:C2018:DEP:{code}"
            department_ids.append(territory_id)
            departments[code] = {"id": territory_id, "name": name, "value": value, "municipality_ids": [], "municipality_sum": 0}
            territories.append({
                "id": territory_id,
                "country_id": "GTM",
                "name": name,
                "level": "department",
                "type": "department",
                "parent_id": "GTM",
                "official_code": code,
                "code_system": "INE Guatemala Censo 2018 published department code",
                "boundary_version": None,
                "source_id": population_entry["source_id"],
                "geography_note": "Code and name copied from the 2018 census table; polygon edition remains unverified.",
            })
            observations.append(observation(territory_id, value, population_entry["source_id"], 2018, note, "integer"))
        comparisons.append({
            "parent_id": "GTM",
            "member_ids": department_ids,
            "label": "22 Guatemala departments",
            "membership_note": "Complete department register and totals as published in INE Censo 2018 table A1.1; polygon boundaries are not yet joined.",
            "source_ids": [population_entry["source_id"]],
        })
        for row, values in enumerate(municipality_sheet.iter_rows(min_row=7, max_row=346, min_col=1, max_col=5, values_only=True), start=7):
            department_code = str(values[0])
            municipality_code = str(values[2])
            name = str(values[3]).strip()
            value = finite_number(values[4], f"GTM A1_2!E{row}")
            if department_code not in departments:
                raise ValueError(f"Unknown department code for municipality row {row}: {department_code}")
            territory_id = f"GTM:C2018:MUN:{municipality_code}"
            terminal_ids.append(territory_id)
            departments[department_code]["municipality_ids"].append(territory_id)
            departments[department_code]["municipality_sum"] += value
            territories.append({
                "id": territory_id,
                "country_id": "GTM",
                "name": name,
                "level": "municipality",
                "type": "municipality",
                "parent_id": departments[department_code]["id"],
                "official_code": municipality_code,
                "code_system": "INE Guatemala Censo 2018 published municipality code",
                "boundary_version": None,
                "source_id": population_entry["source_id"],
                "geography_note": "Municipality code and name copied from table A1.2; polygon edition remains unverified.",
            })
            observations.append(observation(territory_id, value, population_entry["source_id"], 2018, note, "integer"))
        for department in departments.values():
            comparisons.append({
                "parent_id": department["id"],
                "member_ids": department["municipality_ids"],
                "label": f"Municipalities within {department['name']}",
                "membership_note": "Complete municipality membership as published in INE Censo 2018 table A1.2; polygon boundaries are not yet joined.",
                "source_ids": [population_entry["source_id"]],
            })

        population_place_keys = []
        for values in place_sheet.iter_rows(min_row=7, max_row=20042, min_col=5, max_col=6, values_only=True):
            population_place_keys.append((str(values[0]), str(values[1]).strip()))
        centroid_place_keys, missing_coordinates = [], 0
        for values in centroid_sheet.iter_rows(min_row=7, max_row=20042, min_col=5, max_col=8, values_only=True):
            centroid_place_keys.append((str(values[0]), str(values[1]).strip()))
            if values[2] is None or values[3] is None:
                missing_coordinates += 1
        if population_place_keys != centroid_place_keys:
            raise ValueError("Guatemala population-place and centroid workbook identities do not match row-for-row")
        department_reconciliation = [
            {
                "department_code": code,
                "department": item["name"],
                "department_total": item["value"],
                "municipality_count": len(item["municipality_ids"]),
                "municipality_sum": item["municipality_sum"],
                "difference": difference(item["municipality_sum"], item["value"]),
            }
            for code, item in departments.items()
        ]
        audit = {
            "national_population": national,
            "department_count": len(department_ids),
            "department_sum": sum(item["value"] for item in departments.values()),
            "department_sum_difference": difference(sum(item["value"] for item in departments.values()), national),
            "municipality_count": len(terminal_ids),
            "municipality_sum": sum(item["municipality_sum"] for item in departments.values()),
            "municipality_sum_difference": difference(sum(item["municipality_sum"] for item in departments.values()), national),
            "department_reconciliation": department_reconciliation,
            "published_place_rows": len(population_place_keys),
            "place_rows_matching_centroid_register": len(population_place_keys),
            "place_rows_without_complete_coordinates": missing_coordinates,
            "place_adoption_status": "audited_not_loaded; municipalities are the first terminal analysis level",
        }
    finally:
        population_book.close()
        centroid_book.close()
    return {
        "country_id": "GTM",
        "period": "2018",
        "territories": territories,
        "observations": observations,
        "comparisons": comparisons,
        "terminal_territory_ids": terminal_ids,
        "sources": [
            source_record(population_entry, "Adopted national, department and municipality population source; table also contains sex, five-year age and urban/rural columns.", "Creative Commons Attribution (official catalog record)", population_entry["catalog_url"]),
            source_record(centroid_entry, "Acquired and row-identity checked against 20,036 published populated-place rows. Not yet used as municipality polygons or as a terminal dashboard layer.", "Creative Commons Attribution (official catalog record)", centroid_entry["catalog_url"]),
        ],
        "audit": audit,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Acquisition directory containing receipt.json and XLSX files")
    parser.add_argument("--out", help="Normalized JSON; defaults to ROOT/normalized-census.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
    for entry in receipt["entries"]:
        entry["retrieved_at"] = receipt["retrieved_at"]
    countries = [extract_belize(root, receipt), extract_guatemala(root, receipt)]
    output = {
        "schema_version": "1.0",
        "scope_id": receipt["scope_id"],
        "generated_at": receipt["retrieved_at"],
        "status": "partial_country_coverage",
        "indicator": {
            "id": INDICATOR_ID,
            "name": "Official census population",
            "theme": "Population",
            "unit": "people",
            "definition": "Population published in each country's adopted official census product. Country year and country-specific weighting or enumeration method remain attached to every observation.",
            "definition_id": "official-census-population-country-product-v1",
            "population": "Population under each national statistical office's adopted census definition; see country observation footnote",
            "measurement_method": "country-specific official census product",
            "aggregation": "sum",
            "series_family": "census",
            "display_role": "primary",
            "period_policy": "latest_available_by_component",
            "display_decimals": 0
        },
        "series_source": {
            "id": "areadata-ca7-census-series",
            "name": "AreaData Central America census series contract",
            "publisher": "AreaData project",
            "url": "https://areadata.net/",
            "status": "partial",
            "retrieved_at": receipt["retrieved_at"],
            "reference_period": "Belize 2022 and Guatemala 2018 acquired; five pilot countries pending",
            "license": "Project metadata; official observations retain source-specific terms",
            "geographic_level": "multi-country and subnational",
            "note": "This source defines only the cross-country indicator contract. Each observation cites its official national source. No seven-country total is available until all members pass compatibility and coverage review."
        },
        "countries": countries,
        "summary": {
            "pilot_country_count": 7,
            "countries_acquired": [country["country_id"] for country in countries],
            "countries_pending": ["SLV", "HND", "NIC", "CRI", "PAN"],
            "territories_added": sum(len(country["territories"]) for country in countries),
            "observations_added": sum(len(country["observations"]) for country in countries),
            "regional_total_status": "not_available_incomplete_country_coverage"
        }
    }
    output["indicator"]["source_id"] = output["series_source"]["id"]
    target = Path(args.out).resolve() if args.out else root / "normalized-census.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {output['summary']['observations_added']} census observations across {output['summary']['territories_added']} added territories.")
    print(f"Regional total: {output['summary']['regional_total_status']}. Output: {target}")


if __name__ == "__main__":
    main()

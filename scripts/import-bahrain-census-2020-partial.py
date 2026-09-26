"""Adopt a checked subset of Bahrain Census 2020 governorate counts.

National values are runtime sums of the complete four-governorate cover, never
stored as source-observed national rows. The remaining census fields stay open.
"""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


TABLES = {
    "population": "population-by-governorate-nationality-and-sex-census-2020",
    "nationality_groups": "population-by-governorate-nationality-groups-and-sex-census-2020",
    "housing": "housing-units-by-housing-type-and-governorate-census-2020",
    "housing_occupancy": "housing-units-by-housing-type-and-occupancy-census-2020",
    "households": "total-households-by-governorate-and-type-of-household-census-2020",
    "private_households": "private-households-by-governorate-and-household-nationality-census-2020",
    "household_distribution": "distribution-households-by-governorate-and-nationality-of-households-census-2020",
    "school": "school-enrolled-population-3-years-and-above-by-governorate-nationality-and-sex-",
    "school_stages": "school-enrolled-population-3-years-and-above-by-sex-governorate-and-schooling-st",
    "active": "economically-active-population-15-years-and-above-by-governorate-nationality-and",
    "labor_detail": "population-15-years-and-above-by-governorate-and-labour-force-participation-cens",
}
GOVERNORATES = ("Capital", "Muharraq", "Northern", "Southern")
ARABIC = {"Capital": "العاصمة", "Muharraq": "المحرق", "Northern": "الشمالية", "Southern": "الجنوبية"}
SOURCE_IDS = {"population": "bhr-iga-census2020-pop-governorate",
              "housing": "bhr-iga-census2020-housing-governorate",
              "households": "bhr-iga-census2020-households-governorate",
              "school": "bhr-iga-census2020-school-enrolled-governorate",
              "active": "bhr-iga-census2020-economically-active-governorate"}


def read_table(project, inventory, prefix):
    matches = [item for item in inventory["tables"] if item["dataset_id"].startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one source table: {prefix}")
    table = matches[0]
    rows = []
    for page in table["pages"]:
        path = project / page["raw_path"]
        body = path.read_bytes()
        receipt = json.loads((project / (page["raw_path"] + ".receipt.json")).read_text(encoding="utf-8"))
        digest = hashlib.sha256(body).hexdigest()
        if digest != page["sha256"] or digest != receipt["sha256"] or receipt["status"] != "acquired":
            raise ValueError(f"Original/receipt mismatch: {page['raw_path']}")
        payload = json.loads(body)
        if payload["total_count"] != table["record_count"]:
            raise ValueError(f"Source row count changed: {table['dataset_id']}")
        for index, row in enumerate(payload["results"], 1):
            rows.append((row, f"{page['raw_path']} row {index}"))
    if len(rows) != table["record_count"] or len(table["numeric_fields"]) != 1:
        raise ValueError(f"Source incomplete or value field ambiguous: {table['dataset_id']}")
    return table, rows


def checked_counts(rows, field, expected_govs=True):
    seen = set()
    by_gov = defaultdict(list)
    for row, locator in rows:
        gov = row.get("governorate")
        if expected_govs and gov not in GOVERNORATES:
            raise ValueError(f"Unmatched Census 2020 governorate: {gov}")
        if expected_govs and row.get("lmhfz") != ARABIC[gov]:
            raise ValueError(f"Arabic/English governorate mismatch: {gov}")
        value = row[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Invalid Census 2020 integer: {locator}={value}")
        key = tuple((name, str(value)) for name, value in sorted(row.items()) if name != field)
        if key in seen:
            raise ValueError(f"Duplicate Census 2020 source categories: {locator}")
        seen.add(key)
        if gov is not None:
            by_gov[gov].append((value, locator, row))
    if expected_govs and set(by_gov) != set(GOVERNORATES):
        raise ValueError("Four-governorate census coverage incomplete")
    return by_gov


def grouped(by_gov, predicate=lambda row: True):
    out = {}
    for gov in GOVERNORATES:
        cells = [(value, locator) for value, locator, row in by_gov[gov] if predicate(row)]
        if not cells:
            raise ValueError(f"No source cells for {gov}")
        out[gov] = {"value": sum(value for value, _ in cells),
                    "locators": [locator for _, locator in cells]}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    inventory = json.loads((project / "evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "BHR" or len(inventory["tables"]) != 45 or \
            any(item["id"].startswith("BHR:CENSUS2020:") for item in dataset["territories"]):
        raise ValueError("Expected unmodified Bahrain bootstrap and 45-table inventory")
    tables = {}
    cells = {}
    source_rows = {}
    for key, prefix in TABLES.items():
        table, rows = read_table(project, inventory, prefix)
        tables[key] = table
        source_rows[key] = rows
        cells[key] = checked_counts(rows, table["numeric_fields"][0],
                                    expected_govs=key != "housing_occupancy")
    pop = cells["population"]
    groups = {
        "POP_TOTAL": grouped(pop),
        "POP_MALE": grouped(pop, lambda row: row["sex"] == "Male"),
        "POP_FEMALE": grouped(pop, lambda row: row["sex"] == "Female"),
        "POP_BAHRAINI": grouped(pop, lambda row: row["nationality"] == "Bahraini"),
        "POP_NON_BAHRAINI": grouped(pop, lambda row: row["nationality"] == "Non-Bahraini"),
        "HOUSING_UNITS": grouped(cells["housing"]),
        "HOUSEHOLDS_TOTAL": grouped(cells["households"]),
        "HOUSEHOLDS_PRIVATE": grouped(cells["households"], lambda row: row["type_of_household"] == "Private Households"),
        "SCHOOL_ENROLLED_3PLUS": grouped(cells["school"]),
        "ECONOMICALLY_ACTIVE_15PLUS": grouped(cells["active"]),
    }
    controls = {"POP_TOTAL": 1501635, "POP_MALE": 942895, "POP_FEMALE": 558740,
                "POP_BAHRAINI": 712362, "POP_NON_BAHRAINI": 789273,
                "HOUSING_UNITS": 387126, "HOUSEHOLDS_TOTAL": 245983,
                "HOUSEHOLDS_PRIVATE": 228972, "SCHOOL_ENROLLED_3PLUS": 309557,
                "ECONOMICALLY_ACTIVE_15PLUS": 875558}
    for key, total in controls.items():
        if sum(item["value"] for item in groups[key].values()) != total:
            raise ValueError(f"Census 2020 national control changed: {key}")
    for gov in GOVERNORATES:
        if groups["POP_MALE"][gov]["value"] + groups["POP_FEMALE"][gov]["value"] != groups["POP_TOTAL"][gov]["value"] or \
                groups["POP_BAHRAINI"][gov]["value"] + groups["POP_NON_BAHRAINI"][gov]["value"] != groups["POP_TOTAL"][gov]["value"]:
            raise ValueError(f"Population partition fails: {gov}")
        if sum(value for value, _, _ in cells["nationality_groups"][gov]) != groups["POP_TOTAL"][gov]["value"] or \
                sum(value for value, _, row in cells["nationality_groups"][gov] if row["nationality_groups"] == "Bahraini") != groups["POP_BAHRAINI"][gov]["value"]:
            raise ValueError(f"Detailed nationality crosscheck fails: {gov}")
        if sum(value for value, _, _ in cells["private_households"][gov]) != groups["HOUSEHOLDS_PRIVATE"][gov]["value"] or \
                sum(value for value, _, _ in cells["household_distribution"][gov]) != groups["HOUSEHOLDS_PRIVATE"][gov]["value"]:
            raise ValueError(f"Private-household crosscheck fails: {gov}")
        if sum(value for value, _, _ in cells["school_stages"][gov]) != groups["SCHOOL_ENROLLED_3PLUS"][gov]["value"]:
            raise ValueError(f"School-stage crosscheck fails: {gov}")
        if sum(value for value, _, row in cells["labor_detail"][gov]
               if row["labour_force_participation"] in ("Employed", "Unemployed")) != groups["ECONOMICALLY_ACTIVE_15PLUS"][gov]["value"]:
            raise ValueError(f"Labor-status crosscheck fails: {gov}")
    housing_scope = [row["housing"] for row, _ in source_rows["housing_occupancy"]]
    if len(housing_scope) != 10 or sum(housing_scope) != controls["HOUSING_UNITS"]:
        raise ValueError("Housing type/occupancy national crosscheck fails")
    now = datetime.now(timezone.utc).isoformat()
    dataset["territories"] = [item for item in dataset["territories"] if item["id"] == "BHR"]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    ids = {}
    for gov in GOVERNORATES:
        area_id = f"BHR:CENSUS2020:GOV:{gov.upper().replace(' ', '-')}"
        ids[gov] = area_id
        dataset["territories"].append({"id": area_id, "name": gov,
            "local_name": ARABIC[gov], "level": "adm1", "type": "2020 census governorate reporting area",
            "parent_id": "BHR", "official_code": None,
            "code_system": "iGA Census 2020 English/Arabic labels; official code unverified",
            "boundary_version": None, "source_id": SOURCE_IDS["population"]})
    dataset["sources"].append({"id": "bhr-governorates-2014-amendment", "name": "Decree-Law 56/2014: four governorates",
        "url": "https://www.lloc.gov.bh/Legislation/HTM/L5614", "publisher": "Legislation and Legal Opinion Commission (Bahrain)",
        "reference_period": "2014 amendment; applicability and map annex to verify", "geographic_level": "four governorates",
        "status": "partial", "retrieved_at": now, "license": "official_legal_source_terms_review_required",
        "note": "The official legal search result names Capital, Muharraq, Northern and Southern after the 2014 change. Exact dated legal polygon and area codes have not been acquired; 2017 provider shapes are withheld."})
    source_table = {"POP_TOTAL": "population", "POP_MALE": "population", "POP_FEMALE": "population",
        "POP_BAHRAINI": "population", "POP_NON_BAHRAINI": "population", "HOUSING_UNITS": "housing",
        "HOUSEHOLDS_TOTAL": "households", "HOUSEHOLDS_PRIVATE": "households",
        "SCHOOL_ENROLLED_3PLUS": "school", "ECONOMICALLY_ACTIVE_15PLUS": "active"}
    for key in SOURCE_IDS:
        table = tables[key]
        page = table["pages"][0]
        receipt = json.loads((project / (page["raw_path"] + ".receipt.json")).read_text(encoding="utf-8"))
        dataset["sources"].append({"id": SOURCE_IDS[key], "name": table["title"],
            "url": f"https://www.data.gov.bh/explore/dataset/{table['dataset_id']}/",
            "publisher": "Information & eGovernment Authority (Bahrain)",
            "reference_period": "2020 Census (UNSD listing: 17 March 2020); not the annual 2020 estimate",
            "geographic_level": "four 2020 census governorate reporting areas", "status": "ready",
            "retrieved_at": receipt["retrieved_at"], "raw_path": page["raw_path"], "sha256": page["sha256"],
            "license": "https://www.data.gov.bh/pages/terms-and-conditions/",
            "note": "Official portal table acquired with exact JSON receipt. Selected governorate values are sums of mutually exclusive cells within this table. Portal terms require source/download-date attribution and prescribed terms/disclaimer text before external republication. No official area code or dated polygon is asserted."})
    definitions = {
        "POP_TOTAL": ("2020 census population", "Population", "people", "All persons in the official 2020 Census governorate nationality×sex table"),
        "POP_MALE": ("2020 census male population", "Population", "people", "Male persons in the same census table"),
        "POP_FEMALE": ("2020 census female population", "Population", "people", "Female persons in the same census table"),
        "POP_BAHRAINI": ("2020 census Bahraini population", "Population", "people", "Bahraini persons in the same census table"),
        "POP_NON_BAHRAINI": ("2020 census non-Bahraini population", "Population", "people", "Non-Bahraini persons in the same census table"),
        "HOUSING_UNITS": ("2020 census housing units", "Housing", "housing units", "All housing types in the official Census 2020 governorate housing-type table; occupancy is not inferred"),
        "HOUSEHOLDS_TOTAL": ("2020 census households, all types", "Households", "households", "Private plus collective households in the official Census 2020 governorate household-type table"),
        "HOUSEHOLDS_PRIVATE": ("2020 census private households", "Households", "households", "Private households only, excluding collective households"),
        "SCHOOL_ENROLLED_3PLUS": ("2020 census school-enrolled people aged 3+", "Education", "people", "School-enrolled persons aged 3 years and above in the governorate census table; not an enrollment rate"),
        "ECONOMICALLY_ACTIVE_15PLUS": ("2020 census economically active people aged 15+", "Work", "people", "Economically active persons aged 15 years and above in the governorate census table; employed plus unemployed, not an activity rate"),
    }
    for key, (name, theme, unit, population) in definitions.items():
        indicator_id = f"BHR_CENSUS2020_{key}"
        dataset["indicators"].append({"id": indicator_id, "name": name, "theme": theme,
            "unit": unit, "source_id": SOURCE_IDS[source_table[key]],
            "definition": f"{population}. Governorate values are exact sums of mutually exclusive source cells; national value is an AreaData calculation from the complete four-governorate cover. Census 2020 and annual 2020 demographic estimates are distinct series.",
            "population": population, "aggregation": "sum",
            "measurement_method": "same_table_exclusive_cell_sum_2020_census",
            "series_family": "census", "display_role": "primary",
            "period_policy": "latest_available_per_indicator", "display_decimals": 0})
        for gov in GOVERNORATES:
            item = groups[key][gov]
            dataset["observations"].append({"territory_id": ids[gov], "indicator_id": indicator_id,
                "period": "2020", "value": item["value"], "status": "observed",
                "source_id": SOURCE_IDS[source_table[key]],
                "measurement_method": "same_table_exclusive_cell_sum_2020_census",
                "source_locator": "; ".join(item["locators"]),
                "provenance": "calculated",
                "footnote": f"AreaData sum of {len(item['locators'])} mutually exclusive governorate source cells; source rows and coordinates are in source_locator."})
    dataset["analysis"]["comparisons"] = [{"parent_id": "BHR", "member_ids": list(ids.values()),
        "label": "Four 2020 census governorate reporting areas",
        "membership_note": "The official 2020 census tables report exactly these four governorates, matching the four names in the 2014 legal amendment; official geographic codes and dated polygon equality remain unverified.",
        "source_ids": [SOURCE_IDS["population"], "bhr-governorates-2014-amendment"]}]
    dataset["analysis"]["aggregation"] = {"policy": "exact_then_complete_cover",
        "rules": [{"indicator_id": f"BHR_CENSUS2020_{key}", "method": "sum", "completeness": "full_cover",
                   "period_policy": "same_period", "label": "AreaData sum of four census governorates",
                   "note": "Only all four non-overlapping published 2020 governorate cells are used; no 2017 reference polygon or current 2026 territory is implied."}
                  for key in definitions]}
    dataset["country"]["geography_note"] = ("The official 2020 census portal reports four governorate categories: Capital, Muharraq, Northern and Southern. The 2014 legal amendment names the same four; official codes, the exact dated legal polygons and municipal planning-unit equivalence are not yet established. Four 2017 geoBoundaries provider shapes are withheld. National WDI annual data and the separately published annual 2020 demographic estimate are not census observations.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap["status"] = "partial"
            gap["detail"] = ("Four Census 2020 governorate labels match the names in the official 2014 legal amendment. No official code table or dated legal boundary was acquired; four 2017 provider polygons were withheld.")
            gap["next_action"] = "Acquire the legal map annex, official code register and 2020/2026 boundary editions; reconcile municipalities and census reporting units before adopting polygons."
        elif gap["category"] == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = ("All 45 titled Census 2020 portal tables and 2,602 source rows were acquired. Ten narrowly defined indicators use 40 governorate observations from five tables; another six source tables provided independent crosschecks. The other value fields and finer local geography remain unassessed; national census values are calculated only from a complete four-governorate cover.")
            gap["next_action"] = "Semantically audit all remaining table fields and any block/municipal statistics; assess the 2020 population discrepancy against the separate annual demographic series."
        elif gap["category"] == "planning_documents":
            gap["status"] = "not_collected"
            gap["detail"] = ("The municipal regulation's local-plan and budget duties, urban-planning law, four-municipality 2025–26 aggregate budget page and ministry project catalogue have official locations only. No approved municipality plan, individual budget, expenditure, implementation or evaluation original has been adopted.")
            gap["next_action"] = "Verify the operative 2026 legal amendments and municipality/governorate mapping, then acquire individual approved local plans, budgets, final accounts, project execution and evaluation originals."
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["bahrain-iga-census2020-partial"]))
    dataset["collection"]["notes"].append("The five adopted Census 2020 tables are source-receipted; national values are calculated at use time from all four governorates.")
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    register_path = project / "evidence/BHR_CENSUS_2020_FIELD_REGISTER.csv"
    with register_path.open(encoding="utf-8-sig", newline="") as handle:
        field_rows = list(csv.DictReader(handle))
    adopted_ids = {tables[key]["dataset_id"] for key in SOURCE_IDS}
    checked_ids = {tables[key]["dataset_id"] for key in TABLES if key not in SOURCE_IDS}
    for row in field_rows:
        if row["dataset_id"] in adopted_ids:
            row["decision"] = "partially_adopted_governorate_sums"
            row["reason"] = "Exact 2020 source cells grouped only within one governorate; national values calculated by complete-cover rule"
        elif row["dataset_id"] in checked_ids:
            row["decision"] = "crosscheck_only_not_adopted"
            row["reason"] = "Independent crosscheck of adopted measure; detailed categories remain unassessed"
    with register_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(field_rows[0]))
        writer.writeheader()
        writer.writerows(field_rows)
    audit = {"status": "partial_candidate_not_accepted", "source_tables_acquired": 45,
        "source_rows_acquired": 2602, "source_numeric_cells": 2598, "source_null_cells": 4,
        "adopted_table_ids": sorted(adopted_ids), "crosscheck_table_ids": sorted(checked_ids),
        "observations_added": 40, "national_complete_cover_controls": controls,
        "governorate_ids": ids, "source_geometry_adopted": 0,
        "unresolved": ["Official codes and dated legal polygons", "Municipality-to-governorate planning correspondence",
                       "All remaining source field semantics and finer geography", "Approved local plans and fiscal originals",
                       "Full 42-scenario/independent acceptance and portal terms for release"]}
    (project / "evidence/BHR_CENSUS_2020_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"indicators": len(definitions), "observations": 40, "governorates": 4,
                      "national_census_population_calculated": controls["POP_TOTAL"]}))


if __name__ == "__main__":
    main()

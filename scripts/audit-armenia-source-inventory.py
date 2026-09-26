#!/usr/bin/env python3
"""Build a structural source/field audit for the partial Armenia candidate.

Catalogued fields are not semantically accepted indicators. The outputs keep
unreviewed source columns visible and make partial adoption explicit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
EVIDENCE = PROJECT / "evidence"


def read(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def save(name: str, value: dict) -> None:
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    dataset = json.loads((PROJECT / "data" / "dashboard.json").read_text(encoding="utf-8"))
    catalogue = read("ARM_CENSUS_2022_CATALOGUE.json")
    bulletin = read("ARM_POPULATION_2026_TABLE_INVENTORY.json")
    budget = read("ARM_ASHTARAK_BUDGET_INVENTORY.json")
    geoportal = read("ARM_GEOPORTAL_LAYER_INVENTORY.json")
    census_extract = read("ARM_CENSUS_2022_MARZ_POPULATION_EXTRACT.json")
    if len(catalogue["tables"]) != 14 or len(census_extract["rows"]) != 12:
        raise ValueError("Census catalogue or adopted extract changed")
    if budget["sheet_count"] != 13 or budget["numeric_cell_count"] != 6434:
        raise ValueError("Budget workbook inventory changed")
    if Counter(row["disposition"] for row in bulletin["rows"])["adopted_direct"] != 81:
        raise ValueError("Annual population row disposition changed")

    resources = []
    for source in dataset["sources"]:
        sid = source["id"]
        if sid.startswith("armstat-census-2022"):
            stage = "partially_adopted_2022_total_by_national_and_first_level_area"
        elif sid == "armstat-permanent-population-2026-01-01":
            stage = "partially_adopted_81_direct_reporting_rows"
        elif sid == "arm-ashtarak-budget-xls-2026":
            stage = "three_approved_document_controls_only"
        elif sid.startswith("arm-yerevan-budget") or sid == "arm-yerevan-budget-execution-2025-decision":
            stage = "acquired_not_semantically_adopted"
        elif sid == "arm-geoportal-admin-boundary-map":
            stage = "official_location_inspected_no_geometry_adopted"
        elif sid.startswith("arm-") or sid.startswith("armstat-"):
            stage = "location_and_selected_document_content_checked"
        else:
            stage = "bootstrap_international_reference"
        resources.append({"source_id": sid, "name": source["name"], "url": source["url"],
                          "raw_path": source.get("raw_path"), "sha256": source.get("sha256"),
                          "retrieved_at": source.get("retrieved_at"), "reference_period": source.get("reference_period"),
                          "geographic_level": source.get("geographic_level"), "reuse_terms": source.get("license"),
                          "audit_stage": stage})
    save("SOURCE_RESOURCE_INVENTORY.json", {
        "edition": dataset["generated_at"], "resource_count": len(resources), "resources": resources,
        "official_boundary_observation": {"map_url": geoportal["source_page"],
                                          "marz_feature_count": geoportal["marz_feature_count"],
                                          "marz_property_keys": geoportal["marz_property_keys"],
                                          "community_endpoint_status": geoportal["community_endpoint_status"],
                                          "disposition": geoportal["disposition"]},
        "interpretation": "Acquisition and structural indexing do not imply semantic acceptance or permission to redistribute originals."
    })

    tables = []
    rows = []
    inventory_header = ["source_id", "source_hash", "table_or_sheet", "column_or_variable", "original_label",
                        "unit", "universe", "period", "geography_type", "role", "indicator_id", "decision", "reason", "locator"]
    for table in catalogue["tables"]:
        adopted = "PS-pp-1-1-2.px" in table["url"]
        axes = [{"name": axis["name"], "option_count": len(axis["options"]),
                 "options": axis["options"]} for axis in table["variables"]]
        tables.append({"source_id": "armstat-census-2022-pxweb-marzes", "kind": "PxWeb_table",
                       "title": table["title"], "url": table["url"], "sha256": table["sha256"],
                       "raw_path": table["raw_path"], "axes": axes,
                       "numeric_measure": "PxWeb population/household count, cross-tab values; unit and universe require table-specific verification",
                       "decision": "one_2022_total_slice_adopted_other_cells_unassessed" if adopted else "priority_unassessed",
                       "reviewed_slice": census_extract["query"] if adopted else None})
        rows.append({"source_id": "armstat-census-2022-pxweb-marzes", "source_hash": table["sha256"],
                     "table_or_sheet": table["title"], "column_or_variable": "PxWeb numeric result measure",
                     "original_label": table["title"], "unit": "table_specific_review_required",
                     "universe": "table_specific_review_required", "period": "2001/2011/2022 where offered; check table",
                     "geography_type": "see axes; do not infer community detail",
                     "role": "raw_result_measure", "indicator_id": "ARM_CENSUS_2022_PERMANENT_POP" if adopted else "",
                     "decision": "partial_adoption_12_total_2022_cells" if adopted else "priority_unassessed",
                     "reason": "Other axis combinations and underlying definitions remain unassessed" if adopted else "Axis metadata only; numeric values not semantically inspected",
                     "locator": table["url"]})
    for sheet in budget["sheet_inventory"]:
        columns = [field for field in budget["column_inventory"] if field["sheet"] == sheet["sheet"]]
        tables.append({"source_id": "arm-ashtarak-budget-xls-2026", "kind": "XLS_sheet",
                       **sheet, "numeric_column_count": len(columns),
                       "decision": "three_document_controls_across_workbook_other_cells_unassessed"})
    for field in budget["column_inventory"]:
        rows.append({"source_id": "arm-ashtarak-budget-xls-2026", "source_hash": budget["source_sha256"],
                     "table_or_sheet": field["sheet"], "column_or_variable": field["column"],
                     "original_label": "Numeric column; row labels in ARM_ASHTARAK_BUDGET_NUMERIC_CELLS.csv",
                     "unit": "mixed_codes_amd_or_chart_values_unverified", "universe": "Ashtarak approved 2026 budget",
                     "period": "2026 planned", "geography_type": "Ashtarak community",
                     "role": "structural_numeric_column", "indicator_id": "",
                     "decision": field["decision"], "reason": field["note"],
                     "locator": f"XLS {field['sheet']}!{field['first_cell']}:{field['last_cell']}"})
    for field in ("total_thousand", "urban_thousand", "rural_thousand"):
        rows.append({"source_id": "armstat-permanent-population-2026-01-01", "source_hash": next(
                         source["sha256"] for source in dataset["sources"] if source["id"] == "armstat-permanent-population-2026-01-01"),
                     "table_or_sheet": "2026 bulletin pages 4-9", "column_or_variable": field,
                     "original_label": field.replace("_thousand", ""), "unit": "thousand persons, one decimal",
                     "universe": "permanent registered population with statistical adjustment", "period": "2026-01-01",
                     "geography_type": "national; marz; community", "role": "direct_published_value",
                     "indicator_id": "ARM_2026_PERMANENT_POP_" + field.split("_")[0].upper(),
                     "decision": "adopted_for_81_primary_rows_only", "reason": "Internal settlements and duplicate rows are withheld; source dash stays not_applicable",
                     "locator": "PDF pages 4-9; see ARM_POPULATION_2026_TABLE_INVENTORY.json"})
    tables.append({"source_id": "armstat-permanent-population-2026-01-01", "kind": "PDF_table_rows",
                   "page_range": "4-9", "row_count": len(bulletin["rows"]),
                   "dispositions": dict(Counter(row["disposition"] for row in bulletin["rows"])),
                   "decision": "81_primary_rows_adopted_other_rows_withheld_or_duplicate"})
    tables.append({"source_id": "armstat-permanent-population-2025-01-01", "kind": "PDF_acquired_not_adopted",
                   "reason": "2025 Khoy-to-Vagharshapat merger prevents direct 2026-code join; source table and crosswalk remain unaudited"})
    save("SOURCE_TABLE_INVENTORY.json", {"table_count": len(tables), "tables": tables,
                                          "status": "structural_inventory_partial_semantic_audit"})
    with (EVIDENCE / "INDICATOR_INVENTORY.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=inventory_header)
        writer.writeheader()
        writer.writerows(rows)

    themes = [
        ("population", "2022 census first-level permanent totals and 2026 census-based current total/urban/rural across communities adopted", "partial", "Audit census age/sex, historical years and comparable 2025 crosswalk"),
        ("education", "2022 census education table metadata found, numeric cells and local detail unassessed", "candidate_identified", "Request and audit exact numeric slices and universe"),
        ("health_nutrition", "No Armenia-specific official health/nutrition original acquired in this run", "not_yet_searched", "Search health ministry and Armstat official local tables"),
        ("water_sanitation_housing_energy", "2022 census housing, water, toilet, sewage and heating table metadata found; values unassessed", "candidate_identified", "Audit source universes, geographic axes and numeric slices"),
        ("livelihood_poverty_economy", "Ashtarak 2026 approved budget acquired, but it is not household livelihood or poverty data", "not_yet_searched", "Search Armstat economic and poverty local releases"),
        ("access_infrastructure_environment", "No comparable local official infrastructure/environment original adopted", "not_yet_searched", "Search sector ministries and Armstat local tables"),
    ]
    save("THEME_COVERAGE.json", {"country": "ARM", "as_of": dataset["generated_at"],
                                 "themes": [{"theme": theme, "evidence": evidence, "stage": stage, "next_action": action}
                                            for theme, evidence, stage, action in themes],
                                 "interpretation": "Located is not acquired; acquired is not code-matched; code-matched is not adopted."})
    print(json.dumps({"resources": len(resources), "source_tables": len(tables), "field_rows": len(rows),
                      "themes": len(themes), "budget_unassessed_cells": budget["dispositions"]["priority_unassessed"]}))


if __name__ == "__main__":
    main()

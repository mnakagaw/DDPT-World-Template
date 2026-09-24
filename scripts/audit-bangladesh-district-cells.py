"""Read-only district-row audit of all adopted BBS Community Series fields.

This checks district rows in every worksheet of all 64 retained workbooks.
Upazila/city rows and geography crosswalks still require independent review.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import column_index_from_string


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "bangladesh-areadata-20260924-v2"


def normalized(value):
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def main():
    data = json.loads((PROJECT / "data/dashboard.json").read_text(encoding="utf-8"))
    fields = json.loads((PROJECT / "evidence/COMMUNITY_SERIES_FIELD_INVENTORY.json").read_text(encoding="utf-8"))
    resources = json.loads((PROJECT / "evidence/SOURCE_RESOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    workbook_resources = {Path(resource["raw_path"]).name: resource for catalog in resources["catalogs"]
                          for resource in catalog["resources"] if resource.get("raw_path", "").endswith(".xlsx")}
    observations = {(item["territory_id"], item["indicator_id"]): item
                    for item in data["observations"] if item["source_id"] == "bgd-bbs-community-series-2022"
                    and item["period"] == "2022"}
    checked = 0
    issues = []
    skipped_missing = 0
    sheets_without_district_observation = 0
    sheets_checked = 0
    for inventory in fields["workbooks"]:
        name = inventory["workbook"]
        resource = workbook_resources[name]
        district_id = resource["territory_id"]
        district_name = normalized(inventory["district"])
        by_sheet = defaultdict(list)
        for field in inventory["fields"]:
            if field["decision"] == "adopted" and field.get("indicator_id"):
                by_sheet[field["sheet"]].append(field)
        workbook = load_workbook(PROJECT / "raw/bbs-community-series-2022" / name,
                                 read_only=True, data_only=True)
        for sheet_name, adopted in by_sheet.items():
            if sheet_name not in workbook:
                issues.append(f"{name}/{sheet_name}: worksheet absent")
                continue
            district_row = None
            for row in workbook[sheet_name].iter_rows(min_row=1, max_row=40, values_only=True):
                if any(isinstance(cell, str) and normalized(cell) == district_name for cell in row) and sum(
                    isinstance(row[column_index_from_string(field["column"]) - 1], (int, float))
                    for field in adopted if column_index_from_string(field["column"]) <= len(row)
                ) >= 1:
                    district_row = row
                    break
            if district_row is None:
                if any((district_id, field["indicator_id"]) in observations and
                       observations[(district_id, field["indicator_id"])]["status"] == "observed"
                       for field in adopted):
                    issues.append(f"{name}/{sheet_name}: district row absent but AreaData has observed values")
                else:
                    sheets_without_district_observation += 1
                continue
            sheets_checked += 1
            for field in adopted:
                item = observations.get((district_id, field["indicator_id"]))
                if item is None or item["status"] != "observed":
                    skipped_missing += 1
                    continue
                col = column_index_from_string(field["column"]) - 1
                source = district_row[col] if col < len(district_row) else None
                actual = item["value"]
                if not isinstance(source, (int, float)) or not isinstance(actual, (int, float)):
                    issues.append(f"{name}/{sheet_name}/{field['column']} {field['indicator_id']}: nonnumeric source or observation")
                    continue
                if abs(source - actual) > 0.00002:
                    issues.append(f"{name}/{sheet_name}/{field['column']} {field['indicator_id']}: source {source}, AreaData {actual}")
                else:
                    checked += 1
        workbook.close()
    report = {"workbooks": len(fields["workbooks"]), "sheets_checked": sheets_checked,
              "sheets_without_district_observation": sheets_without_district_observation,
              "matching_observed_district_cells": checked, "unobserved_or_missing_fields": skipped_missing,
              "issue_count": len(issues), "issue_examples": issues[:30],
              "verdict": "PASS_DISTRICT_CELLS_ONLY" if not issues else "FAIL"}
    print(json.dumps(report, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())

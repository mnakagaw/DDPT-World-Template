"""Record a disposition for every numeric column in the NPC census workbook.

This is a mechanical manifest. A partly adopted column has selected cells with
source locators in the country dataset; its other cells are not thereby approved.
The manifest and raw workbook stay in the ignored country project.
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl.utils import get_column_letter


LOCATOR = re.compile(r"sheet '([^']+)', row ([0-9-]+), column ([A-Z]+)$")


def main(project):
    inventory = json.loads((project / "evidence/QAT_NPC2020_WORKBOOK_INVENTORY.json").read_text(encoding="utf-8"))
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    original = inventory["originals"]["Census_Final_Results.xlsx"]
    selected = defaultdict(lambda: {"indicators": set(), "locators": set()})
    for observation in dataset["observations"]:
        if not observation["indicator_id"].startswith("QAT_NPC2020_"):
            continue
        locator = observation.get("source_locator", "")
        match = LOCATOR.search(locator)
        if not match:
            raise ValueError(f"Missing or unparsable original-cell locator: {locator}")
        sheet, rows, column = match.groups()
        key = (sheet, column)
        selected[key]["indicators"].add(observation["indicator_id"])
        selected[key]["locators"].add(rows)

    fields = []
    for sheet_name in original["sheet_order"]:
        sheet = original["sheets"][sheet_name]
        for index, count in sheet.get("numeric_columns", {}).items():
            column = get_column_letter(int(index))
            entry = selected.get((sheet_name, column))
            fields.append({
                "sheet": sheet_name,
                "sheet_title": sheet.get("title"),
                "column": column,
                "numeric_cells_including_headers": count,
                "disposition": "selected_cells_partially_adopted" if entry else "mechanically_inventoried_semantics_pending",
                "adopted_indicator_ids": sorted(entry["indicators"]) if entry else [],
                "selected_source_rows": sorted(entry["locators"]) if entry else [],
            })
    field_keys = {(field["sheet"], field["column"]) for field in fields}
    if not set(selected).issubset(field_keys):
        raise ValueError(f"Adopted source columns missing from workbook inventory: {set(selected) - field_keys}")
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "original_sha256": original["sha256"],
        "meaning": "Every numeric column is listed. Selected-cell adoption does not approve unselected cells or the full column; source semantics for other columns and tables remain pending.",
        "numeric_cells_including_headers": sum(field["numeric_cells_including_headers"] for field in fields),
        "numeric_columns": len(fields),
        "partly_adopted_columns": len(selected),
        "fields": fields,
    }
    output = project / "evidence/QAT_NPC2020_FIELD_DISPOSITION.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"numeric_columns": result["numeric_columns"],
                      "numeric_cells_including_headers": result["numeric_cells_including_headers"],
                      "partly_adopted_columns": result["partly_adopted_columns"],
                      "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

"""Mechanically inventory every acquired 2022 Maldives census workbook column.

This does not certify definitions or adopt the numeric cells. Selected tables
receive a separate row-and-field semantic audit before import.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/maldives-cph2022-source-manifest.json"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def main(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = manifest["source_files"]
    if len(sources) != 58:
        raise ValueError(f"Expected 58 acquired XLSX sources, found {len(sources)}")
    books = []
    total_numeric = 0
    for source in sources:
        path = project / source["raw_path"]
        body = path.read_bytes()
        if len(body) != source["bytes"] or digest(body) != source["sha256"]:
            raise ValueError(f"Original differs: {source['id']}")
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheets = []
        for sheet in workbook.worksheets:
            numeric = defaultdict(lambda: {"count": 0, "first_row": None, "last_row": None,
                                           "integer_count": 0, "decimal_count": 0})
            top_text = defaultdict(list)
            actual_nonblank_rows = 0
            for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
                if any(value is not None and str(value).strip() for value in row):
                    actual_nonblank_rows += 1
                for index, value in enumerate(row, 1):
                    if isinstance(value, bool):
                        continue
                    if isinstance(value, (int, float)):
                        item = numeric[index]
                        item["count"] += 1
                        item["first_row"] = item["first_row"] or row_number
                        item["last_row"] = row_number
                        item["integer_count" if isinstance(value, int) or float(value).is_integer()
                             else "decimal_count"] += 1
                    elif row_number <= 6 and value is not None and str(value).strip():
                        top_text[index].append(str(value).strip()[:180])
            columns = [{"column": get_column_letter(index), "numeric_cells": item["count"],
                        "integer_cells": item["integer_count"], "decimal_cells": item["decimal_count"],
                        "first_numeric_row": item["first_row"], "last_numeric_row": item["last_row"],
                        "header_text_first_six_rows": top_text.get(index, [])}
                       for index, item in sorted(numeric.items())]
            total_numeric += sum(item["numeric_cells"] for item in columns)
            sheets.append({"name": sheet.title, "declared_rows": sheet.max_row,
                           "declared_columns": sheet.max_column,
                           "actual_nonblank_rows": actual_nonblank_rows,
                           "numeric_columns": columns,
                           "field_decision": "priority_unassessed_until_selected_table_audit"})
        books.append({"source_id": source["id"], "code": source["code"],
                      "sha256": source["sha256"], "url": source["url"],
                      "sheets": sheets})
    result = {"status": "mechanical_inventory_not_semantic_acceptance",
              "manifest_sha256": digest(MANIFEST.read_bytes()),
              "workbooks": len(books), "numbered_tables": sum(x["catalogue"] == "summary" for x in sources),
              "indicator_and_definition_workbooks": sum(x["catalogue"] == "indicator_sheets" for x in sources),
              "all_numeric_cells_including_headers_totals_and_unassessed": total_numeric,
              "books": books}
    (project / "evidence/MDV_CPH2022_WORKBOOK_INVENTORY.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("workbooks", "numbered_tables",
        "indicator_and_definition_workbooks", "all_numeric_cells_including_headers_totals_and_unassessed")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

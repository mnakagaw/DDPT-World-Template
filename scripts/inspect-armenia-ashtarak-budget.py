#!/usr/bin/env python3
"""Inventory every numeric cell of the acquired Ashtarak 2026 budget XLS.

The inventory is structural. Only the three independently checked decision
totals have a semantic disposition; numeric headings, codes, duplicated
charts, and detail amounts remain unassessed for indicator adoption.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import xlrd


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
SOURCE = PROJECT / "raw" / "official-planning" / "ashtarak-budget-2026-annexes.xls"
EVIDENCE = PROJECT / "evidence"
CONTROLS = {
    ("Sheet1", 10, 3): ("approved_total_revenue_thousand_amd", 7693615.1),
    ("Sheet2+", 10, 5): ("approved_total_expenditure_thousand_amd", 8622091.5),
    ("Sheet4+", 12, 2): ("approved_budget_balance_thousand_amd", -928476.4),
}


def neighbor_label(sheet: xlrd.sheet.Sheet, row: int, col: int) -> str:
    for index in range(col - 1, -1, -1):
        cell = sheet.cell(row, index)
        if cell.ctype == xlrd.XL_CELL_TEXT and str(cell.value).strip():
            return str(cell.value).strip()[:240]
    return ""


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    workbook = xlrd.open_workbook(str(SOURCE))
    cells = []
    sheet_inventory = []
    field_inventory = []
    seen_controls = set()
    for sheet in workbook.sheets():
        count = 0
        for col in range(sheet.ncols):
            col_rows = []
            for row in range(sheet.nrows):
                cell = sheet.cell(row, col)
                if cell.ctype != xlrd.XL_CELL_NUMBER:
                    continue
                value = float(cell.value)
                key = (sheet.name, row, col)
                disposition = "priority_unassessed"
                meaning = ""
                if key in CONTROLS:
                    meaning, expected = CONTROLS[key]
                    if abs(value - expected) > 0.000001:
                        raise ValueError(f"Official budget control changed: {key}: {value} != {expected}")
                    disposition = "adopted_document_control_only"
                    seen_controls.add(key)
                coord = f"{xlrd.colname(col)}{row + 1}"
                cells.append({"sheet": sheet.name, "cell": coord, "row": row + 1,
                              "column": xlrd.colname(col), "value": repr(value),
                              "left_label": neighbor_label(sheet, row, col),
                              "disposition": disposition, "meaning": meaning})
                col_rows.append(row)
                count += 1
            if col_rows:
                field_inventory.append({"sheet": sheet.name, "column": xlrd.colname(col),
                                        "numeric_cells": len(col_rows),
                                        "first_cell": f"{xlrd.colname(col)}{col_rows[0]+1}",
                                        "last_cell": f"{xlrd.colname(col)}{col_rows[-1]+1}",
                                        "decision": "partial_document_controls" if any((sheet.name, r, col) in CONTROLS for r in col_rows) else "priority_unassessed",
                                        "note": "Structural numeric column; headings/codes/charts and financial values require row-level interpretation."})
        sheet_inventory.append({"sheet": sheet.name, "rows": sheet.nrows,
                                "columns": sheet.ncols, "numeric_cells": count})
    if seen_controls != set(CONTROLS):
        raise ValueError(f"Missing approved budget controls: {set(CONTROLS) - seen_controls}")
    with (EVIDENCE / "ARM_ASHTARAK_BUDGET_NUMERIC_CELLS.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cells[0]))
        writer.writeheader()
        writer.writerows(cells)
    result = {"source_path": str(SOURCE.relative_to(PROJECT)).replace("\\", "/"),
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "format": "legacy XLS", "sheet_count": len(sheet_inventory),
              "sheet_inventory": sheet_inventory,
              "numeric_cell_count": len(cells), "numeric_column_count": len(field_inventory),
              "dispositions": dict(Counter(row["disposition"] for row in cells)),
              "column_inventory": field_inventory,
              "interpretation": "Only three high-level approved-budget amounts agree with Decision 170-N clause 1. All other numeric cells are structurally inventoried but semantically unassessed; the original annexes include identifiers, formula results and duplicate chart series. No execution amount is adopted."}
    (EVIDENCE / "ARM_ASHTARAK_BUDGET_INVENTORY.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("sheet_count", "numeric_cell_count", "numeric_column_count", "dispositions")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

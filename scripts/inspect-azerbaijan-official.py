"""Inventory every numeric column in acquired Azerbaijan population XLS originals."""

import argparse
import csv
import json
from pathlib import Path

import xlrd


FILES = (
    "2025-area-population-density.xls",
    "2025-administrative-division.xls",
    "2026-resident-population-by-area.xls",
    "2026-population-sex-settlement.xls",
    "2020-2026-population-age-by-area.xls",
)


def cell_text(sheet, row, column):
    value = sheet.cell_value(row, column)
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "AZE":
        raise ValueError("Expected an Azerbaijan candidate")
    base = project / "raw/azerbaijan-official"
    output = project / "evidence"
    rows = []
    samples = []
    for filename in FILES:
        workbook = xlrd.open_workbook(base / filename)
        print(filename, len(workbook.sheets()), "sheets")
        for sheet in workbook.sheets():
            sample = {
                "file": filename,
                "sheet": sheet.name,
                "dimensions": [sheet.nrows, sheet.ncols],
                "first_rows": [
                    {"excel_row": row + 1, "cells": {xlrd.colname(column): cell_text(sheet, row, column)
                        for column in range(sheet.ncols) if sheet.cell_type(row, column) != xlrd.XL_CELL_EMPTY}}
                    for row in range(min(18, sheet.nrows))
                ],
            }
            if (filename != "2020-2026-population-age-by-area.xls" or
                    sheet.name in ("01.01.2020 (Total population)", "01.01.2026 (Total population)",
                                   "01.01.2026 (men)", "01.01.2026 (rural areas)")):
                samples.append(sample)
            for column in range(sheet.ncols):
                numeric = [row for row in range(sheet.nrows) if sheet.cell_type(row, column) == xlrd.XL_CELL_NUMBER]
                if not numeric:
                    continue
                rows.append({
                    "file": filename,
                    "sheet": sheet.name,
                    "column": xlrd.colname(column),
                    "header_rows_1_to_8": " | ".join(
                        f"r{row + 1}:{cell_text(sheet, row, column)}" for row in range(min(8, sheet.nrows))
                        if sheet.cell_type(row, column) != xlrd.XL_CELL_EMPTY
                    ),
                    "numeric_cells": len(numeric),
                    "first_numeric_row": numeric[0] + 1,
                    "first_numeric_value": cell_text(sheet, numeric[0], column),
                    "last_numeric_row": numeric[-1] + 1,
                    "last_numeric_value": cell_text(sheet, numeric[-1], column),
                    "disposition": "not_adopted_pending_row_and_geography_audit",
                })
    with (output / "AZE_XLS_NUMERIC_COLUMNS.csv").open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "AZE_XLS_SAMPLE.json").write_text(json.dumps(samples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Numeric columns:", len(rows))


if __name__ == "__main__":
    main()

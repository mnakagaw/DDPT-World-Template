"""Read-only inventory of every sheet and column in CAS LFHLCS demography XLS."""

import argparse
import csv
import json
from pathlib import Path

import xlrd


ADOPTED = {2: "Women", 3: "Men", 4: "Women & Men"}


def cell_text(value):
    return str(value).strip()[:180] if value != "" else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    data = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if data["country"]["id"] != "LBN":
        raise ValueError("Expected Lebanon candidate")
    source = project / "raw/lebanon-cas-moph/lfhlcs-2018-19-demography.xls"
    workbook = xlrd.open_workbook(source, on_demand=True)
    structure, columns = [], []
    for sheet in workbook.sheets():
        sample = [{"row": row + 1, "cells": {str(index + 1): cell_text(value)
                   for index, value in enumerate(sheet.row_values(row)) if value != ""}}
                  for row in range(min(sheet.nrows, 8))]
        structure.append({"sheet": sheet.name, "rows": sheet.nrows, "columns": sheet.ncols,
                          "first_eight_rows": sample})
        for index in range(sheet.ncols):
            values = [sheet.cell_value(row, index) for row in range(sheet.nrows)]
            nonempty = [value for value in values if value != ""]
            numeric = [value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
            adopted = sheet.name == "HL5" and index in ADOPTED
            columns.append((sheet.name, index + 1, cell_text(values[0]), len(nonempty), len(numeric),
                            cell_text(nonempty[0]) if nonempty else "",
                            "adopted_2018_survey_native_geography" if adopted else "unassessed",
                            "HL5 weighted resident estimate in thousands; scaled to people and rounded to 100 for display."
                            if adopted else "Definition, geography, table overlap or denominator not yet assessed."))
    workbook.release_resources()
    evidence = project / "evidence"
    (evidence / "LBN_LFHLCS_DEMOGRAPHY_STRUCTURE.json").write_text(
        json.dumps(structure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (evidence / "LBN_LFHLCS_DEMOGRAPHY_COLUMNS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("sheet", "column_index", "first_row_label", "nonempty_cells", "numeric_cells",
                         "first_nonempty", "decision", "reason"))
        writer.writerows(columns)
    print(json.dumps({"sheets": len(structure), "physical_columns": len(columns),
                      "columns_with_numeric_cells": sum(int(row[4]) > 0 for row in columns),
                      "adopted_columns": sum(row[6].startswith("adopted") for row in columns)}))


if __name__ == "__main__":
    main()

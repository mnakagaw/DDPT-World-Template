"""Audit two explicitly located Taiz yearbook district tables without adoption."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PDF_SHA256 = "9781f9ea9c4a186bba726b42e994fbb72021c72290bbac09db91bd20c6f34504"
POPULATION_NAMES = [
    "Mawiyah", "Sharab As Salam", "Sharab Ar Rawnah", "Maqbanah", "Al Mukha",
    "Dhubab", "Mawza", "Jabal Habashy", "musharieuh and hudnan", "Sabir Al Mawadim",
    "Al Misrakh", "Dimnat Khadir", "As Silw", "Ash Shamayatayn", "Al Wazi'yah",
    "Hayfan", "Al Mudhaffar", "Al Qahirah", "Salh", "At Ta'ziyah",
    "Al Ma'afer", "Al Mawasit", "Sama",
]
HOUSEHOLD_NAMES = [
    "Mawiyah", "Sharab As Salam", "Sharab Ar Rawnah", "Maqbanah", "Al Mukha",
    "Dhubab", "Mawza", "Jabal Habashy", "Mashraah Wa Hadnan", "Sabir Al Mawadim",
    "Al Misrakh", "Dimnat Khadir", "As Silw", "Ash Shamayatayn", "Al Wazi'yah",
    "Hayfan", "Al Mudhaffar", "Al Qahirah", "Salh", "At Ta'ziyah",
    "Al Ma'afer", "Al Mawasit", "Sama",
]


def page_text(pdf, number):
    result = subprocess.run(["pdftotext", "-f", str(number), "-l", str(number),
                             "-layout", "-enc", "UTF-8", str(pdf), "-"],
                            capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def rows(text, names, columns):
    result = []
    for line_no, line in enumerate(text.splitlines(), 1):
        ascii_line = line.encode("ascii", "ignore").decode("ascii").strip()
        match = next((name for name in names if ascii_line.startswith(name + "  ")), None)
        if match is None:
            continue
        remainder = ascii_line[len(match):]
        cells = re.findall(r"[0-9][0-9,]*|-", remainder)
        if len(cells) != len(columns):
            raise ValueError(f"{match}: expected {len(columns)} cells, found {cells}")
        result.append({"name": match, "line": line_no,
                       **{field: None if value == "-" else int(value.replace(",", ""))
                          for field, value in zip(columns, cells)}})
    if [row["name"] for row in result] != names:
        raise ValueError("District names/order differ from visually inspected table")
    return result


def total_row(text, columns):
    lines = [line.encode("ascii", "ignore").decode("ascii").strip()
             for line in text.splitlines()]
    candidates = [[int(value.replace(",", "")) for value in re.findall(r"[0-9][0-9,]*", line[5:])]
                  for line in lines if line.startswith("Total  ")]
    matching = [values for values in candidates if len(values) == len(columns)]
    if len(matching) != 1:
        raise ValueError(f"Total row column count differs: {candidates}")
    numbers = matching[0]
    return dict(zip(columns, numbers))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    pdf = project / "raw/taiz-cso-2024/taiz-cso-statistical-yearbook-2024.pdf"
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != PDF_SHA256:
        raise ValueError("Taiz yearbook PDF differs from pinned source")
    population_columns = ["population_2024", "males_2024_printed", "females_2024_printed",
                          "population_2023", "males_2023_printed", "females_2023_printed"]
    household_columns = ["households_2024", "rural_2024", "urban_2024"]
    population_text = page_text(pdf, 42)
    household_text = page_text(pdf, 43)
    if "Table No. (3)Resident Population" not in population_text or "Table No. (4)Number of households" not in household_text:
        raise ValueError("Pinned table locators changed")
    population = rows(population_text, POPULATION_NAMES, population_columns)
    households = rows(household_text, HOUSEHOLD_NAMES, household_columns)
    printed_population_total = total_row(population_text, population_columns)
    printed_household_total = total_row(household_text, household_columns)
    sums = {field: sum(row[field] for row in population) for field in population_columns}
    sums.update({field: sum(row[field] or 0 for row in households)
                 for field in household_columns})
    differences = {field: sums[field] - printed for field, printed in
                   {**printed_population_total, **printed_household_total}.items()}
    sex_row_discrepancies = [
        {"name": row["name"], "year": year,
         "total_minus_male_female": row[f"population_{year}"] -
         row[f"males_{year}_printed"] - row[f"females_{year}_printed"]}
        for row in population for year in [2023, 2024]
        if row[f"population_{year}"] != row[f"males_{year}_printed"] + row[f"females_{year}_printed"]
    ]
    audit = {"source_yearbook": 2024, "source_pdf_sha256": PDF_SHA256,
             "checked_at": datetime.now(timezone.utc).isoformat(), "source_pdf_pages": 314,
             "table_3_pdf_page": 42, "table_4_pdf_page": 43,
             "district_rows": 23, "printed_totals": {**printed_population_total, **printed_household_total},
             "district_row_sums": sums, "row_sum_minus_printed": differences,
             "sex_row_discrepancies": sex_row_discrepancies,
             "sex_conflict": "PDF page 39 summary labels male 2,158,100 and female 2,073,500 for 2024, the reverse of table 3 page 42 total sex labels. Do not adopt sex-specific values before publisher clarification.",
             "household_missing_note": "A dash in the rural/urban columns denotes unavailable source data per table footnote; never silently convert it to observed zero.",
             "adoption": "none; source and geography audit only",
             "geography_gap": "Taiz 2024 yearbook district roster lacks a verified official-code and versioned boundary crosswalk to the 2017 provider polygons"}
    evidence = project / "evidence"
    (evidence / "TAIZ_2024_YEARBOOK_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (evidence / "TAIZ_2024_YEARBOOK_DISTRICT_FIELDS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["table", "pdf_page", "row", "field", "value", "source_sha256"])
        for table, page, items, fields in [(3, 42, population, population_columns),
                                           (4, 43, households, household_columns)]:
            for row in items:
                for field in fields:
                    writer.writerow([table, page, row["name"], field, row[field], PDF_SHA256])
    print(json.dumps({"district_rows": 23, "row_sum_minus_printed": differences,
                      "sex_row_discrepancies": len(sex_row_discrepancies),
                      "household_rows_with_missing_category": sum(
                          row["rural_2024"] is None or row["urban_2024"] is None for row in households)},
                     indent=2))


if __name__ == "__main__":
    main()

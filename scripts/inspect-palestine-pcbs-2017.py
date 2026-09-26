"""Inventory PCBS 2017 census originals and extract only Summary Table 2."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = "raw/palestine-pcbs-2017/"
HASHES = {
    "pcbs-2017-final-summary.pdf": "25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f",
    "pcbs-2017-detailed-population.pdf": "0ab9b57187f3924a128069a685a83295a23d80ab7d706dc8e690b8df2e9d0520",
    "pcbs-2017-governorate-area.html": "33eebd91cecdeffecc42076406e22fe5b232f852037ce1ff5f8ab0a04c2fc233",
}
NAMES = ["Palestine", "West Bank", "Jenin", "Tubas & Northern Valleys", "Tulkarm", "Nablus",
         "Qalqiliya", "Salfit", "Ramallah & Al-Bireh", "Jericho & Al Aghwar", "Jerusalem",
         "Bethlehem", "Hebron", "Gaza Strip", "North Gaza", "Gaza", "Dier al Balah",
         "Khan Yunis", "Rafah"]
COLUMNS = [
    ("Sex Ratio", "ratio", "unassessed_not_adopted", "Requires source definition and interval/rounding check"),
    ("Average Household Size", "people per household", "unassessed_not_adopted", "Population includes post-enumeration estimates; do not infer from displayed counts"),
    ("Households Percentage", "%", "unassessed_not_adopted", "Printed rounded share, not a distinct count"),
    ("Households Number", "households", "adopted", "Reported count; not a population estimate"),
    ("Female Population Percentage", "%", "unassessed_not_adopted", "Printed rounded share"),
    ("Female Population Number", "people", "adopted", "Final census count includes post-enumeration population estimates"),
    ("Male Population Percentage", "%", "unassessed_not_adopted", "Printed rounded share"),
    ("Male Population Number", "people", "adopted", "Final census count includes post-enumeration population estimates"),
    ("Total Population Percentage", "%", "unassessed_not_adopted", "Printed rounded share"),
    ("Total Population Number", "people", "adopted", "Final census count includes post-enumeration population estimates"),
]


def verify(project, name):
    path = project / (ROOT + name)
    body = path.read_bytes()
    receipt = json.loads((project / (ROOT + name + ".receipt.json")).read_text(encoding="utf-8"))
    digest = hashlib.sha256(body).hexdigest()
    if digest != HASHES[name] or receipt["sha256"] != digest or receipt["status"] != "acquired":
        raise ValueError(f"PCBS original/receipt changed: {name}")
    return path


def pdf_text(path):
    return subprocess.check_output(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"]
    ).decode("utf-8")


def parse_int(token):
    if not re.fullmatch(r"\d[\d,]*", token):
        raise ValueError(f"Expected integer source count: {token}")
    return int(token.replace(",", ""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    summary = pdf_text(verify(project, "pcbs-2017-final-summary.pdf"))
    detailed = pdf_text(verify(project, "pcbs-2017-detailed-population.pdf"))
    verify(project, "pcbs-2017-governorate-area.html")
    start = summary.find("Table 2: Population in Palestine by Governorate and Sex, 2017")
    end = summary.find("Table 3: Population in Palestine by Age Group, Sex and Governorate, 2017")
    if start < 0 or end < start or summary[:start].count("\f") + 1 != 71:
        raise ValueError("PCBS final Summary Table 2 page/locator changed")
    table = summary[start:end]
    rows = []
    for line in table.splitlines():
        if not line.startswith("  ") or not line[2:3].isalpha():
            continue
        cells = re.split(r"\s{2,}", line.strip())
        if cells[0] not in NAMES:
            continue
        if len(cells) < 12 or not all(re.fullmatch(r"[\d.,]+", cell) for cell in cells[1:11]):
            raise ValueError(f"Table 2 split/ambiguous row: {cells[:12]}")
        rows.append({"name": cells[0], "sex_ratio": cells[1], "average_household_size": cells[2],
                     "household_percent": cells[3], "households": parse_int(cells[4]),
                     "female_percent": cells[5], "females": parse_int(cells[6]),
                     "male_percent": cells[7], "males": parse_int(cells[8]),
                     "total_percent": cells[9], "total": parse_int(cells[10]),
                     "source_pdf_page": 71, "source_printed_page": 71})
    if [row["name"] for row in rows] != NAMES:
        raise ValueError("Expected 19 source reporting rows in exact Table 2 order")
    for row in rows:
        if row["females"] + row["males"] != row["total"]:
            raise ValueError(f"Sex counts do not sum: {row['name']}")
    for region, children in ((rows[1], rows[2:13]), (rows[13], rows[14:])):
        for field in ("households", "females", "males", "total"):
            if sum(child[field] for child in children) != region[field]:
                raise ValueError(f"Table 2 governorates do not cover {region['name']}/{field}")
    for field in ("households", "females", "males", "total"):
        if rows[1][field] + rows[13][field] != rows[0][field]:
            raise ValueError(f"Table 2 regions do not cover national/{field}")
    if (rows[0]["total"], rows[0]["females"], rows[0]["males"], rows[0]["households"]) != \
            (4_781_248, 2_348_052, 2_433_196, 929_221):
        raise ValueError("PCBS final 2017 country controls changed")
    t29_start = summary.find("Table 29: Population* in Palestine by Locality and Sex, 2017")
    t29_end = summary.find("Table 29:      Population in Palestine by Locality and Sex, 2017")
    if t29_start < 0 or t29_end < t29_start:
        raise ValueError("Table 29 locality inventory range changed")
    t29 = summary[t29_start:t29_end]
    locality_codes = re.findall(r"(?<!\d)(\d{5,6})(?!\d)", t29)
    inline = re.findall(r"^\s{1,3}(.+?)\s{2,}([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+(\d{5,6})\b", t29, re.M)
    if len(locality_codes) != 585 or len(set(locality_codes)) != 585 or len(inline) != 529:
        raise ValueError("Table 29 locality rows/line-split structure changed")
    notice = summary.find("Notice For Users")
    if notice < 0 or "post enumeration survey" not in summary[notice:notice + 1800]:
        raise ValueError("PCBS population universe notice not located")
    evidence = project / "evidence"
    with (evidence / "PSE_PCBS_2017_TABLE2_ROWS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    with (evidence / "PSE_PCBS_2017_TABLE2_COLUMNS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["column", "label", "unit", "decision", "reason"])
        writer.writeheader()
        for index, (label, unit, decision, reason) in enumerate(COLUMNS, 1):
            writer.writerow({"column": index, "label": label, "unit": unit,
                             "decision": decision, "reason": reason})
    report = {"status": "table2_four_count_fields_checked_other_tables_open",
              "summary_pdf_sha256": HASHES["pcbs-2017-final-summary.pdf"],
              "detailed_pdf_sha256": HASHES["pcbs-2017-detailed-population.pdf"],
              "summary_pages": summary.count("\f"), "detailed_pages": detailed.count("\f"),
              "table2_pdf_page": 71, "table2_rows": len(rows),
              "table2_physical_numeric_columns": len(COLUMNS), "table2_adopted_count_columns": 4,
              "table29_pdf_first_page": 116, "table29_locality_codes": len(locality_codes),
              "table29_single_line_rows": len(inline),
              "table29_split_or_wrapped_rows": len(locality_codes) - len(inline),
              "table29_adoption": "none; all 585 locality source rows require full visual and semantic extraction, especially wrapped Gaza/Jerusalem records",
              "detailed_report_adoption": "none; 270-page population volume acquired, tables/fields not yet semantically inventoried",
              "population_universe": "Final 2017 population counts include actually enumerated persons and post-enumeration estimates; historical, not current 2026 population",
              "national_controls": {key: rows[0][key] for key in ("total", "females", "males", "households")}}
    (evidence / "PSE_PCBS_2017_STRUCTURE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"table2_rows": len(rows), "adopted_columns": 4,
                      "table29_locality_codes_unadopted": len(locality_codes),
                      "national_total": rows[0]["total"]}))


if __name__ == "__main__":
    main()

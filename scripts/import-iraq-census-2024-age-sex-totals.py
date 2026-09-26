"""Import explicitly printed COSIT 2024 governorate sex/urban-rural totals.

The 268-page age table also contains age bands and sub-governorate units. This
adapter uses only its 18 labelled governorate total rows and grand total. It
does not claim an inventory or adoption of the remaining rows.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PDF_INDEX = 21
PDF_SHA256 = "e0800bbfd58a41d879ed4b9edc269eefe37a632eb2d32ecbade2b3f171ea0b3f"
SOURCE_ID = "irq-cosit-census-2024-age-sex-urban-rural-pdf"
POPULATION_INDICATOR = "IRQ_CENSUS_2024_POP_TABULATED"
EXPECTED_CODES = {
    "11": "Dohuk", "12": "Ninawa", "13": "Al-Sulaimaniyah", "14": "Kirkuk",
    "15": "Erbil", "21": "Diyala", "22": "Al-Anbar", "23": "Baghdad",
    "24": "Babil", "25": "Karbala", "26": "Wasit", "27": "Salah al-Din",
    "28": "An-Najaf", "31": "Al-Qadisiyah", "32": "Al-Muthanna",
    "33": "Dhi Qar", "34": "Maysan", "35": "Al-Basrah",
}
COLUMNS = ["total", "female", "male", "rural_total", "rural_female",
           "rural_male", "urban_total", "urban_female", "urban_male"]
NATIONAL = [46118793, 22957189, 23161604, 13755144, 6833089,
            6922055, 32363649, 16124100, 16239549]
INDICATORS = [
    ("IRQ_CENSUS_2024_MALE", "Male population in 2024 census", "male",
     "Persons classified male in COSIT's age/sex and urban/rural table."),
    ("IRQ_CENSUS_2024_FEMALE", "Female population in 2024 census", "female",
     "Persons classified female in COSIT's age/sex and urban/rural table."),
    ("IRQ_CENSUS_2024_URBAN", "Urban population in 2024 census", "urban_total",
     "Persons in the source table's urban category; this is not the WDI urban series."),
    ("IRQ_CENSUS_2024_RURAL", "Rural population in 2024 census", "rural_total",
     "Persons in the source table's rural category; classification details beyond the source table have not been verified."),
]


def numbers(value):
    return [int(item) for item in re.findall(r"[0-9]+", value)]


def check_arithmetic(row):
    v = row["values"]
    if len(v) != 9 or v[1] + v[2] != v[0] or v[3] + v[6] != v[0]:
        raise ValueError(f"Population split fails for {row['code']}")
    if v[4] + v[5] != v[3] or v[7] + v[8] != v[6]:
        raise ValueError(f"Urban/rural sex split fails for {row['code']}")
    if v[4] + v[7] != v[1] or v[5] + v[8] != v[2]:
        raise ValueError(f"Sex/environment split fails for {row['code']}")


def extract_totals(pdf):
    result = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
                            check=True, capture_output=True)
    pages = result.stdout.decode("utf-8").split("\f")
    if len(pages) - 1 != 268:
        raise ValueError(f"Expected 268 source pages; got {len(pages) - 1}")
    rows = []
    grand = None
    for page_number, page in enumerate(pages[:-1], 1):
        for line_number, line in enumerate(page.splitlines(), 1):
            if "Grand Total" in line:
                if grand is not None:
                    raise ValueError("Duplicate grand total")
                grand = {"code": "IRQ", "page": page_number,
                         "line": line_number, "values": numbers(line.split("Grand Total")[0])}
            elif "Total" in line:
                before, after = line.split("Total", 1)
                codes = numbers(after)
                if len(codes) == 1 and len(str(codes[0])) == 2:
                    rows.append({"code": str(codes[0]), "page": page_number,
                                 "line": line_number, "values": numbers(before)})
    if len(rows) != 18 or set(row["code"] for row in rows) != set(EXPECTED_CODES):
        raise ValueError("Governorate code roster differs from visually checked source")
    if grand is None or grand["values"] != NATIONAL or grand["page"] != 268:
        raise ValueError("Published national totals or page changed")
    for row in rows + [grand]:
        check_arithmetic(row)
    for index, national_value in enumerate(NATIONAL):
        if sum(row["values"][index] for row in rows) != national_value:
            raise ValueError(f"Governorates do not add to national {COLUMNS[index]}")
    return rows, grand


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    pdf = project / "raw/cosit-2024-table-21.pdf"
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != PDF_SHA256:
        raise ValueError("COSIT age/sex source PDF hash changed")
    manifest = json.loads((project / "raw/cosit-census-2024-catalogue.json").read_text(encoding="utf-8"))
    source = next((item for item in manifest["entries"] if item["index"] == PDF_INDEX), None)
    if not source or source["acquisition"] != "success" or source["sha256"] != PDF_SHA256:
        raise ValueError("Source acquisition receipt does not match PDF")
    rows, grand = extract_totals(pdf)

    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "IRQ" or any(
            item["id"] in {spec[0] for spec in INDICATORS} for item in dataset["indicators"]):
        raise ValueError("Expected Iraq candidate before this import")
    areas = {item["name"]: item for item in dataset["territories"] if item["parent_id"] == "IRQ"}
    if set(areas) != set(EXPECTED_CODES.values()):
        raise ValueError("Existing governorate roster changed")
    census_population = {item["territory_id"]: item["value"] for item in dataset["observations"]
                         if item["indicator_id"] == POPULATION_INDICATOR and item["period"] == "2024"}
    if len(census_population) != 19 or census_population.get("IRQ") != NATIONAL[0]:
        raise ValueError("The prior 2024 source population is incomplete")
    for row in rows:
        territory = areas[EXPECTED_CODES[row["code"]]]
        if census_population[territory["id"]] != row["values"][0]:
            raise ValueError(f"Age/sex total differs from earlier census workbook: {territory['name']}")
        if territory.get("census_source_code") not in (None, row["code"]):
            raise ValueError("Existing census source code conflicts with COSIT table")
        # The territory's registered geometry remains a 2022 provider shape.
        # Keep its boundary code_system and official_code unpromoted until the
        # 2024 census codes are reconciled to a versioned official boundary.
        territory["census_source_code"] = row["code"]
        territory["census_source_code_system"] = "COSIT 2024 census governorate table"
        territory["census_code_reconciliation_status"] = "name_and_exact_population_matched_to_2024_summary"
        row["territory_id"] = territory["id"]
    grand["territory_id"] = "IRQ"
    stamp = datetime.now(timezone.utc).isoformat()
    dataset["sources"].append({"id": SOURCE_ID,
        "name": "COSIT Iraq 2024 census age/sex and urban/rural table, governorate totals",
        "url": source["url"], "publisher": "Iraq COSIT", "reference_period": "2024",
        "geographic_level": "country, governorate totals",
        "status": "ready", "retrieved_at": manifest["checked_at"], "sha256": PDF_SHA256,
        "raw_path": "raw/cosit-2024-table-21.pdf", "license": "terms_review_required",
        "note": "Only 18 printed governorate total rows and the grand total are adopted; the 268-page age bands and sub-governorate rows remain unreviewed."})
    for indicator_id, name, field, definition in INDICATORS:
        dataset["indicators"].append({"id": indicator_id, "name": name,
            "theme": "Census 2024", "unit": "people", "definition": definition,
            "population": "Persons counted in Iraq 2024 census age/sex source table",
            "source_id": SOURCE_ID, "aggregation": "sum", "measurement_method": "source_reported",
            "series_family": "census", "period_policy": "latest_available_per_indicator",
            "display_decimals": 0})
        field_index = COLUMNS.index(field)
        for row in rows + [grand]:
            dataset["observations"].append({"territory_id": row["territory_id"],
                "indicator_id": indicator_id, "period": "2024",
                "value": row["values"][field_index], "status": "observed",
                "measurement_method": "source_reported", "source_id": SOURCE_ID,
                "source_locator": f"PDF p.{row['page']} governorate total {row['code']}, {field}"})
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                   ["iraq-cosit-2024-age-sex-governorate-totals"]))
    dataset["country"]["geography_note"] = (
        "COSIT 2024 census provides 18 governorate rows. The age/sex source prints governorate codes; "
        "all 18 code, name and exact population combinations match the 2024 summary workbook. "
        "The original and Cabinet-decision-adjusted population columns remain distinct. "
        "geoBoundaries 2022 reference polygons are paired by name for navigation, without verified equivalence "
        "to the 2024 legal/census boundary version. World Bank national series remain separate.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap["detail"] = ("The 18 COSIT 2024 census governorate codes and exact population totals are matched to the "
                             "2024 summary workbook. The 2022 geoBoundaries reference polygons are not verified as equivalent to 2024 legal boundaries.")
            gap["next_action"] = "Acquire official versioned 2024 governorate/district boundaries and reconcile every code and changed unit."
        elif gap["category"] == "subnational_statistics":
            gap["detail"] = ("Five 2024 census summary fields, six household-service indicators, and four age/sex/urban-rural "
                             "governorate-total indicators are integrated for 18 governorates. Age bands and sub-governorate rows in the "
                             "268-page PDF are not yet audited or adopted.")
            gap["next_action"] = ("Audit the 268-page age-band and sub-governorate rows with codes, remaining COSIT tables, "
                                  "official boundary versions and planning sources.")

    evidence = project / "evidence"
    with (evidence / "COSIT_2024_AGE_SEX_GOVERNORATE_FIELDS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["pdf_page", "source_line", "census_governorate_code", "territory_id", "field", "value", "source_sha256"])
        for row in rows + [grand]:
            for field, value in zip(COLUMNS, row["values"]):
                writer.writerow([row["page"], row["line"], row["code"], row["territory_id"], field, value, PDF_SHA256])
    audit = {"country": "IRQ", "source_year": 2024, "checked_at": stamp,
             "pdf_sha256": PDF_SHA256, "pdf_pages": 268,
             "scope": "18 printed governorate totals and one grand total; age bands and sub-governorate rows not yet inventoried",
             "source_columns_left_to_right": COLUMNS,
             "governorate_codes": {row["code"]: {"name": EXPECTED_CODES[row["code"]],
                                                  "page": row["page"], "population": row["values"][0]}
                                   for row in rows},
             "crosscheck": "All 18 population totals uniquely equal the 2024 governorate summary workbook; all nine columns sum to the printed national total; every sex and urban/rural partition balances",
             "new_indicator_ids": [spec[0] for spec in INDICATORS],
             "new_observations": 19 * len(INDICATORS),
             "boundary_status": "2022 provider polygon equivalence to 2024 census geography unverified",
             "limitations": ["268-page source not fully semantically inventoried", "No age-band or district values adopted",
                             "Governorate planning records and source redistribution terms not verified", "Independent audit pending"]}
    (evidence / "COSIT_2024_AGE_SEX_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    crosswalk_path = evidence / "CODE_CROSSWALK.csv"
    with crosswalk_path.open(newline="", encoding="utf-8") as stream:
        old_rows = list(csv.DictReader(stream))
    if len(old_rows) != 18 or {row["areadata_territory_id"] for row in old_rows} != {row["territory_id"] for row in rows}:
        raise ValueError("Existing code crosswalk differs from 18 matched areas")
    code_by_id = {row["territory_id"]: row["code"] for row in rows}
    for row in old_rows:
        row["cosit_2024_governorate_code"] = code_by_id[row["areadata_territory_id"]]
        row["census_code_match"] = "source_name_and_exact_2024_population"
        row["boundary_equivalence"] = "unverified_2022_reference_to_2024_census"
    with crosswalk_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(old_rows[0]))
        writer.writeheader()
        writer.writerows(old_rows)
    inventory_path = evidence / "SOURCE_TABLE_INVENTORY.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory.setdefault("pdf_tables", []).append({
        "source_id": SOURCE_ID, "source_sha256": PDF_SHA256,
        "source_pages": 268, "review_scope": "18 governorate total rows and grand total only",
        "fields": [{"column": field, "adoption": ("crosscheck" if field == "total" else
                                                   "adopted" if field in {spec[2] for spec in INDICATORS} else "audited_not_adopted")}
                   for field in COLUMNS],
        "unreviewed": "All age-band and sub-governorate rows; not counted as source-review complete"})
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"governorates": len(rows), "new_indicators": len(INDICATORS),
                      "new_observations": 19 * len(INDICATORS), "matched_census_source_codes": 18}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Adopt two COSIT 2024 census household-service tables into an Iraq candidate.

Requires the prior Iraq census summary import and the private PDFs collected by
collect-iraq-census-2024-catalogue.py. The electricity and water denominators are
different source populations; neither is substituted for the other.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PDFS = {
    "electricity": (6, "cd385b3544553810424bcf2a9d9e22d32995a22172f57b04aed7a6d4e76e8dd7"),
    "water": (7, "4c2766f98a629535a0349b4db6b91b8a4c4edec0d8bc7be388bce9881be80ab5"),
}
SOURCE_IDS = {"electricity": "irq-cosit-census-2024-electricity-pdf",
              "water": "irq-cosit-census-2024-home-water-pdf"}
CATALOGUE_ID = "irq-cosit-census-2024-table-catalogue"
PREFIX = "IRQ_CENSUS_2024_HH_"

# Manually read from the visible first pages. PDF text loses Arabic characters,
# so a name-only programmatic join would be unsafe. Pinned PDF hashes and every
# category/national sum protect this row-position crosswalk from source drift.
ELECTRICITY_ORDER = [
    "Erbil", "Al-Anbar", "Al-Basrah", "Al-Sulaimaniyah", "Al-Qadisiyah",
    "Al-Muthanna", "An-Najaf", "Babil", "Baghdad", "Dohuk", "Diyala",
    "Dhi Qar", "Salah al-Din", "Karbala", "Kirkuk", "Maysan", "Ninawa", "Wasit",
]
WATER_ORDER = [
    "Dohuk", "Ninawa", "Al-Sulaimaniyah", "Kirkuk", "Erbil", "Diyala",
    "Al-Anbar", "Baghdad", "Babil", "Karbala", "Wasit", "Salah al-Din",
    "An-Najaf", "Al-Qadisiyah", "Al-Muthanna", "Dhi Qar", "Maysan", "Al-Basrah",
]
ELECTRICITY_FIELDS = [
    "responding_regular_households", "wind", "solar", "grid_bypass",
    "private_generator", "shared_generator", "public_grid",
]
WATER_FIELDS = [
    "households_total", "not_applicable", "unspecified", "surface_water",
    "tanker_truck", "fixed_tank", "public_tap_outside_dwelling",
    "unprotected_well_or_spring", "protected_well_or_spring",
    "piped_inside_dwelling",
]
ADOPTED = [
    ("ELEC_RESPONDING_HH", "Households responding on electricity sources", "households",
     "Count of regular responding households in the COSIT electricity-source table; a separate denominator from the domestic-water table.", "electricity", 0, 1),
    ("ELEC_PUBLIC_GRID_HH", "Households reporting public-grid electricity (count)", "households",
     "Households reporting the public grid among electricity sources. Sources can overlap, so source-category counts must not be summed as a partition.", "electricity", 6, 7),
    ("ELEC_PUBLIC_GRID_PCT", "Households reporting public-grid electricity (share)", "%",
     "Reported share of regular responding households citing public-grid electricity; multiple electricity sources may be reported.", "electricity_pct", 5, 6),
    ("WATER_HH_TOTAL", "Households in primary domestic-water table", "households",
     "All households in the primary water source used at home table, including not applicable and unspecified; distinct from the electricity response count.", "water", 0, 1),
    ("WATER_PIPED_IN_HOME_HH", "Households with piped water inside dwelling as primary home-water source (count)", "households",
     "Count whose primary water source used at home is piped water inside the dwelling. This is not a drinking-water source or safe-water indicator.", "water", 9, 10),
    ("WATER_PIPED_IN_HOME_PCT", "Households with piped water inside dwelling as primary home-water source (share)", "%",
     "Published percentage of all households whose primary water source used at home is piped water inside the dwelling; not a drinking-water or safe-water rate.", "water_pct", 9, 10),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_pages(path):
    result = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
                            capture_output=True, check=True)
    return result.stdout.decode("utf-8").split("\f")


def number_rows(page, width):
    lines = page.splitlines()
    found = []
    for line_no, line in enumerate(lines, 1):
        numbers = re.findall(r"[0-9][0-9,]*", line)
        if len(numbers) == width:
            found.append((line_no, [int(item.replace(",", "")) for item in numbers]))
    if len(found) != 19:
        raise ValueError(f"Expected 18 governorates and total in count table, got {len(found)}")
    return found


def percent_rows(page, width):
    found = []
    for line_no, line in enumerate(page.splitlines(), 1):
        values = re.findall(r"[0-9]+\.[0-9]+%", line)
        if len(values) == width:
            found.append((line_no, [float(item[:-1]) for item in values]))
    if len(found) != 19:
        raise ValueError(f"Expected 18 governorates and total in percentage table, got {len(found)}")
    return found


def verify_table(name, counts, percentages, national_counts, fraction_digits):
    if counts[-1][1] != national_counts:
        raise ValueError(f"{name}: published national totals changed")
    for column in range(len(national_counts)):
        if sum(row[1][column] for row in counts[:-1]) != national_counts[column]:
            raise ValueError(f"{name}: governorates do not add to national field {column}")
    if name == "water":
        for _, row in counts:
            if sum(row[1:]) != row[0]:
                raise ValueError("Water primary-source categories do not partition households")
    offset = 1 if name == "electricity" else 0
    for index, ((_, count_row), (_, pct_row)) in enumerate(zip(counts, percentages)):
        denominator = count_row[0]
        if name == "water" and pct_row[0] != 100:
            raise ValueError(f"Water percentage total is not 100 at row {index}")
        for column, reported in enumerate(pct_row):
            count_column = column + offset
            computed = 100 * count_row[count_column] / denominator
            tolerance = 0.5 * 10 ** (-fraction_digits) + 1e-7
            if abs(computed - reported) > tolerance:
                raise ValueError(f"{name}: page 2 percentage mismatch at row {index}, field {column}: {computed} vs {reported}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    raw = project / "raw"
    manifest = json.loads((raw / "cosit-census-2024-catalogue.json").read_text(encoding="utf-8"))
    if manifest["catalogue_url"] != "https://cosit.gov.iq/ar/1234-2019-09-05-07-53-20":
        raise ValueError("Catalogue identity changed")
    if digest(raw / "cosit-census-2024-catalogue.html") != manifest["catalogue_sha256"]:
        raise ValueError("Catalogue HTML hash mismatch")
    tables = {}
    for name, (index, pinned_hash) in PDFS.items():
        path = raw / f"cosit-2024-table-{index:02d}.pdf"
        receipt = next(entry for entry in manifest["entries"] if entry["index"] == index)
        if receipt["acquisition"] != "success" or receipt["sha256"] != pinned_hash or digest(path) != pinned_hash:
            raise ValueError(f"{name}: source PDF or acquisition receipt does not match pinned hash")
        pages = extract_pages(path)
        counts = number_rows(pages[0], 7 if name == "electricity" else 10)
        percentages = percent_rows(pages[1], 6 if name == "electricity" else 10)
        tables[name] = {"counts": counts, "percentages": percentages,
                        "url": receipt["url"], "sha256": pinned_hash}
    verify_table("electricity", tables["electricity"]["counts"],
                 tables["electricity"]["percentages"],
                 [7757742, 3001, 25522, 62900, 323700, 4440525, 7634417], 2)
    verify_table("water", tables["water"]["counts"],
                 tables["water"]["percentages"],
                 [8054385, 10310, 286716, 159422, 103578, 61792, 430080, 39447, 228198, 6734842], 1)
    dataset_path = project / "data" / "dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "IRQ" or not any(
            item["id"] == "IRQ_CENSUS_2024_POP_TABULATED" for item in dataset["indicators"]):
        raise ValueError("Expected previously imported Iraq 2024 census summary")
    governors = {item["name"]: item["id"] for item in dataset["territories"]
                 if item["parent_id"] == "IRQ"}
    if len(governors) != 18 or set(governors) != set(ELECTRICITY_ORDER) or set(governors) != set(WATER_ORDER):
        raise ValueError("Existing Iraq governorate roster differs from the checked crosswalk")
    observations = []
    extracted_rows = []
    for name, order in (("electricity", ELECTRICITY_ORDER), ("water", WATER_ORDER)):
        counts = tables[name]["counts"]
        percentages = tables[name]["percentages"]
        fields = ELECTRICITY_FIELDS if name == "electricity" else WATER_FIELDS
        for index, territory_name in enumerate(order + ["Iraq"]):
            territory_id = "IRQ" if index == 18 else governors[territory_name]
            values = counts[index][1]
            reported_pct = percentages[index][1]
            for field, value in zip(fields, values):
                extracted_rows.append({"table": name, "page": 1, "row_index": index + 1,
                                       "territory_id": territory_id, "field": field, "value": value,
                                       "source_hash": tables[name]["sha256"]})
            for column, value in enumerate(reported_pct):
                extracted_rows.append({"table": name, "page": 2, "row_index": index + 1,
                                       "territory_id": territory_id,
                                       "field": (fields[column + 1] if name == "electricity" else fields[column]) + "_percent",
                                       "value": value, "source_hash": tables[name]["sha256"]})
            for suffix, _, _, definition, table_key, field_index, source_column in ADOPTED:
                if not table_key.startswith(name):
                    continue
                page = 2 if table_key.endswith("_pct") else 1
                value = reported_pct[field_index] if page == 2 else values[field_index]
                observations.append({"territory_id": territory_id,
                                     "indicator_id": PREFIX + suffix, "period": "2024",
                                     "value": value, "status": "observed",
                                     "measurement_method": "source_reported", "source_id": SOURCE_IDS[name],
                                     "source_locator": f"{name} PDF p.{page}, table row {index + 1}, numeric column {source_column}"})
    indicators = [{"id": PREFIX + suffix, "name": label,
                   "theme": "Housing and services", "unit": unit,
                   "definition": definition,
                   "population": "Households in Iraq's 2024 population and housing census; table-specific denominators",
                   "source_id": SOURCE_IDS["electricity" if table_key.startswith("electricity") else "water"],
                   "aggregation": "sum" if unit == "households" else "none",
                   "measurement_method": "source_reported", "series_family": "census",
                   "period_policy": "latest_available_per_indicator",
                   "display_decimals": 0 if unit == "households" else 1 if suffix.startswith("WATER") else 2}
                  for suffix, label, unit, definition, table_key, _, _ in ADOPTED]
    dataset["indicators"] = [item for item in dataset["indicators"]
                             if not item["id"].startswith(PREFIX)] + indicators
    dataset["observations"] = [item for item in dataset["observations"]
                               if not item["indicator_id"].startswith(PREFIX)] + observations
    stamp = datetime.now(timezone.utc).isoformat()
    dataset["generated_at"] = stamp
    dataset["sources"] = [item for item in dataset["sources"]
                          if item["id"] not in set(SOURCE_IDS.values()) | {CATALOGUE_ID,
                                                                            "irq-cosit-census-2024-household-services"}]
    dataset["sources"].append({"id": CATALOGUE_ID,
                               "name": "COSIT Iraq 2024 census table catalogue",
                               "url": manifest["catalogue_url"], "publisher": "Iraq COSIT",
                               "reference_period": "2024", "geographic_level": "country, governorate, district or subdistrict where individual table supports it",
                               "status": "partial", "retrieved_at": manifest["checked_at"],
                               "sha256": manifest["catalogue_sha256"],
                               "raw_path": "raw/cosit-census-2024-catalogue.html",
                               "license": "terms_review_required",
                               "note": "Thirty linked PDFs identified. Only two household-service tables have adopted indicators here; other contents need separate inspection."})
    for name, (index, pinned_hash) in PDFS.items():
        dataset["sources"].append({"id": SOURCE_IDS[name],
                                   "name": f"COSIT Iraq 2024 census {name} household table",
                                   "url": tables[name]["url"], "publisher": "Iraq COSIT",
                                   "reference_period": "2024", "geographic_level": "country, governorate",
                                   "status": "ready", "retrieved_at": manifest["checked_at"],
                                   "sha256": pinned_hash,
                                   "raw_path": f"raw/cosit-2024-table-{index:02d}.pdf",
                                   "license": "terms_review_required",
                                   "note": ("Nonexclusive electricity sources; 7,757,742 responding regular households."
                                            if name == "electricity" else
                                            "Mutually exclusive primary source used at home; 8,054,385 households. Not the drinking-water source table.")})
    for gap in dataset["gaps"]:
        if gap.get("category") == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = ("Five numeric fields from the 2024 census governorate summary and six household-service indicators "
                             "from two official COSIT PDFs are integrated for all 18 governorates. The electricity and home-water "
                             "tables have different household denominators. Other catalogue tables, age/sex, district statistics "
                             "and official codes remain unreviewed or unadopted.")
            gap["next_action"] = ("Inventory remaining COSIT census PDFs and the 562-page report; reconcile official administrative "
                                  "codes and 2024 boundaries; research planning institutions, documents and source terms.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["iraq-cosit-2024-household-services"]))
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    with (evidence / "COSIT_2024_HOUSEHOLD_FIELDS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["table", "page", "row_index", "territory_id", "field", "value", "source_hash"])
        writer.writeheader()
        writer.writerows(extracted_rows)
    audit = {"country": "IRQ", "source_year": 2024, "checked_at": stamp,
             "catalogue_sha256": manifest["catalogue_sha256"],
             "table_pdf_sha256": {name: item["sha256"] for name, item in tables.items()},
             "electricity_governorates": 18, "water_governorates": 18,
             "electricity_numeric_fields_p1": ELECTRICITY_FIELDS,
             "water_numeric_fields_p1": WATER_FIELDS,
             "electricity_p2_percentages": "Six source-specific shares of responding regular households; nonexclusive, not summed to 100%",
             "water_p2_percentages": "Ten shares of all households, including total, not applicable and unspecified",
             "adopted_indicator_ids": [PREFIX + item[0] for item in ADOPTED],
             "new_observations": len(observations), "all_extracted_numeric_cells": len(extracted_rows),
             "geography_match": "18 source governorate labels visually checked against pinned PDFs and the pre-existing 18-name census workbook crosswalk; no official 2024 boundary equivalence established",
             "not_adopted": ["Electricity wind/solar/generator/grid-bypass counts and percentages: preserved in extracted CSV; no additive electricity mix claim",
                              "Water remaining primary-source categories: preserved in extracted CSV; categories mutually exclusive, but no safe drinking-water interpretation",
                              "Other 2024 COSIT census catalogue PDFs: identified or acquired, semantic review pending"],
             "limitations": ["Source terms not yet established for redistributing original PDFs or derived observations",
                             "This does not close age/sex, codes/boundaries, planning, broad-domain or independent-audit requirements"]}
    (evidence / "COSIT_2024_HOUSEHOLD_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"new_indicators": len(indicators), "new_observations": len(observations),
                      "extracted_numeric_cells": len(extracted_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Import five 2025 end-year Jordan DoS population estimates by governorate.

Only Tables 2.2 and 2.3 are adopted. The 2015 census, districts and
subdistricts, age groups, area and density require separate review. The
geoBoundaries polygons remain 2006 navigation references, not official codes.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "jor-dos-population-estimates-end-2025"
SOURCE_URL = "https://dosweb.dos.gov.jo/DataBank/population/population_Estimares/PopulationEstimates.pdf"
SOURCE_HASH = "659587a2f4a243c912835720073c76974dd64bdb44dbab0411238cf425deacce"
RAW_RELATIVE = "raw/jordan-dos-2025/jordan-population-estimates-2025.pdf"
NAMES = {
    "Amman": "Amman", "Balqa": "Balqa", "Zarqa": "Zarqa", "Madaba": "Madaba",
    "Irbid": "Irbid", "Mafraq": "Mafraq", "Jarash": "Jerash",
    "Ajlun": "Ajloun", "Karak": "Karak", "Tafiela": "Tafilah",
    "Ma'an": "Ma'an", "Aqaba": "Aqaba",
}
TOTALS = {"population": 11937000, "female": 5617100, "male": 6319900,
          "rural": 1152300, "urban": 10784700}
INDICATORS = {
    "population": ("JOR_DOS_EST_2025_POP", "Estimated population, end of 2025", "Table 2.2", "Total No."),
    "female": ("JOR_DOS_EST_2025_FEMALE", "Estimated female population, end of 2025", "Table 2.2", "Female"),
    "male": ("JOR_DOS_EST_2025_MALE", "Estimated male population, end of 2025", "Table 2.2", "Male"),
    "rural": ("JOR_DOS_EST_2025_RURAL", "Estimated rural population, end of 2025", "Table 2.3", "Rural"),
    "urban": ("JOR_DOS_EST_2025_URBAN", "Estimated urban population, end of 2025", "Table 2.3", "Urban"),
}


def parse_rows(section, field_count):
    numbers = r"([\d,]+)"
    if field_count == 4:
        pattern = re.compile(r"^\s*([A-Za-z][A-Za-z'. ]+?)\s+(\d{1,2}\.\d)\s+" +
                             r"\s+".join([numbers] * 3) + r"\s+", re.MULTILINE)
    else:
        pattern = re.compile(r"^\s*([A-Za-z][A-Za-z'. ]+?)\s+" +
                             r"\s+".join([numbers] * 3) + r"\s+", re.MULTILINE)
    result = {}
    for match in pattern.finditer(section):
        name = match.group(1).strip()
        if name in NAMES:
            if name in result:
                raise ValueError(f"Duplicate DoS governorate: {name}")
            fields = match.groups()[2:] if field_count == 4 else match.groups()[1:]
            result[name] = tuple(int(value.replace(",", "")) for value in fields)
    if set(result) != set(NAMES):
        raise ValueError(f"DoS table coverage changed: {set(NAMES) ^ set(result)}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    original = project / RAW_RELATIVE
    receipt = json.loads((project / (RAW_RELATIVE + ".receipt.json")).read_text(encoding="utf-8"))
    if receipt["source_url"] != SOURCE_URL or receipt["sha256"] != SOURCE_HASH:
        raise ValueError("Wrong DoS PDF receipt")
    if hashlib.sha256(original.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("Wrong DoS PDF bytes")
    page = subprocess.run(["pdftotext", "-f", "3", "-l", "3", "-layout", "-enc", "UTF-8",
                           str(original), "-"], check=True, capture_output=True).stdout.decode("utf-8")
    if ("Table 2.2 Estimated Population" not in page or
            "Table 2.3 Estimated Population" not in page or
            "at The End of year 2025" not in page or
            '"Urban" includes localities of (5000) or more Population' not in page):
        raise ValueError("Unexpected DoS table or edition")
    first, second = page.split("Table 2.3 Estimated Population", 1)
    sex = parse_rows(first, 4)  # printed total, female, male; the % is not adopted
    settlement = parse_rows(second, 3)  # printed total, rural, urban
    rows = {}
    for name in NAMES:
        population, female, male = sex[name]
        other_population, rural, urban = settlement[name]
        if population != female + male or population != rural + urban or population != other_population:
            raise ValueError(f"Sex/settlement row inconsistency: {name}")
        rows[name] = {"population": population, "female": female, "male": male,
                      "rural": rural, "urban": urban}
    for field, expected in TOTALS.items():
        if sum(row[field] for row in rows.values()) != expected:
            raise ValueError(f"DoS printed national total mismatch: {field}")
    if TOTALS["female"] + TOTALS["male"] != TOTALS["population"] or \
            TOTALS["rural"] + TOTALS["urban"] != TOTALS["population"]:
        raise ValueError("DoS totals do not decompose")

    path = project / "data/dashboard.json"
    dataset = json.loads(path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "JOR":
        raise ValueError("Expected Jordan project")
    regions = {area["name"]: area for area in dataset["territories"] if area["parent_id"] == "JOR"}
    if len(regions) != 12 or set(regions) != set(NAMES.values()) or len(dataset["boundaries"]["features"]) != 12:
        raise ValueError("Reference governorate coverage changed")
    ids = {item[0] for item in INDICATORS.values()}
    if any(item["id"] in ids for item in dataset["indicators"]) or any(item["id"] == SOURCE_ID for item in dataset["sources"]):
        raise ValueError("DoS source has already been imported")
    timestamp = datetime.now(timezone.utc).isoformat()
    dataset["sources"].append({
        "id": SOURCE_ID, "name": "Jordan DoS estimated population at end of 2025, Tables 2.2 and 2.3",
        "url": SOURCE_URL, "publisher": "Jordan Department of Statistics",
        "reference_period": "end of 2025", "geographic_level": "country and 12 governorates",
        "status": "ready", "retrieved_at": receipt["retrieved_at"],
        "sha256": SOURCE_HASH, "raw_path": RAW_RELATIVE, "license": "terms_review_required",
        "note": "January 2026 PDF prepared for the 2025 Statistical Yearbook. Five end-year estimated counts are adopted. The 2015 census is a different source and reference date. Urban means localities of 5,000 or more under the 2015 census definition. The 2006 geoBoundaries polygons are navigation references only; no official code or current boundary equivalence was established.",
    })
    for field, (indicator_id, label, table, column) in INDICATORS.items():
        dataset["indicators"].append({
            "id": indicator_id, "name": label, "theme": "Population estimates 2025", "unit": "people",
            "definition": f"DoS end-2025 estimated {field} count, {table}, {column} column. " +
                          ("Urban is localities of 5,000 or more under the 2015 census definition. " if field == "urban" else "") +
                          "This is not a 2015 census count or a WDI midyear estimate.",
            "population": "Estimated residents of Jordan at the end of 2025 as defined by Jordan DoS",
            "source_id": SOURCE_ID, "aggregation": "sum", "measurement_method": "source_reported",
            "series_family": "administrative", "display_role": "primary",
            "period_policy": "latest_available_per_indicator",
            "display_decimals": 0,
        })
        dataset["observations"].append({
            "territory_id": "JOR", "indicator_id": indicator_id, "period": "2025",
            "value": TOTALS[field], "status": "observed", "measurement_method": "source_reported",
            "source_id": SOURCE_ID, "source_locator": f"PDF page 3, {table}, Total row, {column} column",
        })
    crosswalk = []
    for source_name, reference_name in NAMES.items():
        area = regions[reference_name]
        area["source_name_en"] = source_name
        area["reconciliation_status"] = "name_correspondence_only_2006_reference_boundary_unverified"
        crosswalk.append([source_name, reference_name, area["id"], area["provider_code"],
                          "name_correspondence_only; official_code_and_2025_boundary_unverified"])
        for field, (indicator_id, _, table, column) in INDICATORS.items():
            dataset["observations"].append({
                "territory_id": area["id"], "indicator_id": indicator_id, "period": "2025",
                "value": rows[source_name][field], "status": "observed", "measurement_method": "source_reported",
                "source_id": SOURCE_ID,
                "source_locator": f"PDF page 3, {table}, {source_name} row, {column} column",
            })
    dataset["country"]["geography_note"] = (
        "Jordan DoS reports end-2025 estimated population for all 12 governorates. DoS table names were matched one-to-one to 2006 geoBoundaries reference shapes for navigation; official codes and 2025 boundary equivalence remain unverified. National WDI midyear series and the 2015 census are separate.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap["status"] = "partial"
            gap["detail"] = "All 12 DoS governorate names were matched to 2006 geoBoundaries reference names, including three spelling variants. Official codes and 2025 legal boundary equivalence are not established."
            gap["next_action"] = "Acquire the dated official administrative code and boundary register, then verify every shape and any change since 2006."
        if gap["category"] == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = "Five end-2025 DoS estimated population counts were adopted for all 12 governorates and country. Other PDF tables, the separate 2015 census, district/subdistrict statistics and sector indicators remain unadopted."
            gap["next_action"] = "Audit 2015 census tables and the remaining 2025 PDF fields, obtain official lower-unit codes/boundaries and inspect comparable sector statistics."
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                   ["jordan-dos-2025-population-estimates-governorates"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["generated_at"] = timestamp
    path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    with (evidence / "JOR_NAME_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["dos_2025_name", "geoboundaries_2006_name", "territory_id", "provider_shape_id", "status"])
        writer.writerows(crosswalk)
    (evidence / "JOR_DOS_2025_IMPORT_AUDIT.json").write_text(json.dumps({
        "status": "partial_import_not_accepted", "source_url": SOURCE_URL, "sha256": SOURCE_HASH,
        "page": 3, "adopted_tables": ["2.2", "2.3"], "indicators_added": len(INDICATORS),
        "governorates": len(rows), "observations_added": len(INDICATORS) * (len(rows) + 1),
        "printed_national_totals": TOTALS, "arithmetic": "Each row and each national column reconciled to both printed tables.",
        "unresolved": ["2015 census tables", "district and subdistrict values", "official codes and current boundaries",
                       "planning documents, budgets and evaluation", "source redistribution terms", "independent acceptance"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"governorates": len(rows), "indicators": len(INDICATORS),
                      "observations": len(INDICATORS) * (len(rows) + 1), "national": TOTALS["population"]}))


if __name__ == "__main__":
    main()

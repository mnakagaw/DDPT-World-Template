"""Import the 2022 Saudi census regional population cited in MOH yearbook Table 1-12.

The 2010–2021 columns are recalculated estimates, not census counts, and are
deliberately not adopted by this importer. Shapes remain navigation references.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SOURCE_ID = "sau-moh-yearbook-2022-census-regions"
SOURCE_URL = "https://www.moh.gov.sa/en/Ministry/Statistics/book/Documents/Statistical-Yearbook-2022.pdf"
SOURCE_FILE = "moh-statistical-yearbook-2022.pdf"
SOURCE_HASH = "ad90d515309ac5b87a3864e863d0c41989b1412a1e923b86377c64f7c5a4f4c8"
INDICATOR_ID = "SAU_CENSUS_2022_POP_REGION"
NAMES = {
    "Riyadh": "Riyadh Region", "Makkah": "Makkah Region",
    "Medinah": "Al Madinah Region", "Qaseem": "Al-Qassim Region",
    "Eastern": "Eastern Region", "Aseer": "'Asir Region",
    "Tabouk": "Tabuk Region", "Ha`il": "Hayel Region",
    "Northern": "Northern Borders Region", "Jazan": "Jazan Region",
    "Najran": "Najran Region", "Al-Bahah": "Al Bahah Region",
    "Al-Jouf": "Al Jawf Region",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    project = Path(args.project)
    raw = project / "raw" / SOURCE_FILE
    if hashlib.sha256(raw.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("MOH original PDF SHA-256 mismatch")
    completed = subprocess.run(
        ["pdftotext", "-f", "51", "-l", "51", "-layout", "-enc", "UTF-8", str(raw), "-"],
        capture_output=True, check=True,
    )
    page = completed.stdout.decode("utf-8")
    if "Table 1-12" not in page or "Based on (2022G) Census" not in page:
        raise ValueError("Wrong PDF table or edition")
    if "Source: General Authority for Statistics" not in page:
        raise ValueError("Printed GASTAT source attribution missing")
    records = []
    for line in page.splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z\-` ]+?)\s{2,}(\d[\d,]+)\s+", line)
        if match and match.group(1).strip() in NAMES:
            name = match.group(1).strip()
            number = int(match.group(2).replace(",", ""))
            records.append((name, number))
    if len(records) != 13 or {name for name, _ in records} != set(NAMES):
        raise ValueError("Source administrative-region coverage changed")
    if sum(number for _, number in records) != 32175224:
        raise ValueError("2022 source regional counts do not match published national total")
    dataset_path = project / "data" / "dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    regions = {item["name"]: item for item in dataset["territories"]
               if item["parent_id"] == "SAU"}
    if len(regions) != 13 or set(regions) != set(NAMES.values()):
        raise ValueError("Reference-region name correspondence changed")
    if len(dataset["boundaries"]["features"]) != 13:
        raise ValueError("Reference-region polygon count changed")

    observations = [{"territory_id": "SAU", "indicator_id": INDICATOR_ID,
                     "period": "2022", "value": 32175224, "status": "observed",
                     "measurement_method": "source_reported", "source_id": SOURCE_ID,
                     "source_locator": "PDF page 51, Table 1-12, Total row, 2022 column"}]
    crosswalk = []
    for name, number in records:
        territory = regions[NAMES[name]]
        territory["source_name_en"] = name
        territory["reconciliation_status"] = "name_correspondence_only_reference_boundary_unverified"
        observations.append({"territory_id": territory["id"], "indicator_id": INDICATOR_ID,
                             "period": "2022", "value": number, "status": "observed",
                             "measurement_method": "source_reported", "source_id": SOURCE_ID,
                             "source_locator": f"PDF page 51, Table 1-12, {name} row, 2022 column"})
        crosswalk.append((name, territory["name"], territory["id"],
                          territory["provider_code"], "name_correspondence_only"))

    dataset["indicators"] = [item for item in dataset["indicators"] if item["id"] != INDICATOR_ID]
    dataset["indicators"].append({
        "id": INDICATOR_ID, "name": "2022 census population by administrative region",
        "theme": "Census 2022", "unit": "people",
        "definition": "2022 population in Ministry of Health Statistical Yearbook 2022 Table 1-12, sourced there to the General Authority for Statistics. The table calls 2010–2021 regional figures recalculated estimates; only its 2022 column is adopted here.",
        "population": "Population counted in the Saudi 2022 census, as reported in the official yearbook",
        "source_id": SOURCE_ID, "aggregation": "sum", "measurement_method": "source_reported",
        "series_family": "census", "period_policy": "latest_available_per_indicator",
        "display_decimals": 0,
    })
    dataset["observations"] = [item for item in dataset["observations"]
                               if item["indicator_id"] != INDICATOR_ID] + observations
    stamp = datetime.now(timezone.utc).isoformat()
    dataset["generated_at"] = stamp
    dataset["sources"] = [item for item in dataset["sources"] if item["id"] != SOURCE_ID]
    dataset["sources"].append({
        "id": SOURCE_ID,
        "name": "Ministry of Health Statistical Yearbook 2022, Table 1-12",
        "url": SOURCE_URL, "publisher": "Saudi Ministry of Health",
        "original_data_publisher": "General Authority for Statistics (GASTAT), credited in the table",
        "reference_period": "2022", "geographic_level": "country, administrative region",
        "status": "ready", "retrieved_at": stamp, "sha256": SOURCE_HASH,
        "raw_path": f"raw/{SOURCE_FILE}", "license": "terms_review_required",
        "note": "2022 census count sourced to GASTAT. 2010–2021 columns are recalculated estimates and not imported. geoBoundaries 2017 shapes are name-matched reference geometry, not a certified 2022 legal boundary match.",
    })
    dataset["country"]["geography_note"] = (
        "The Saudi Ministry of Health Yearbook 2022 reports GASTAT census population for all 13 administrative regions. Reference polygons are matched by region-name correspondence only; official codes and census-date boundary equivalence remain unverified. National WDI estimates are separate.")
    dataset["gaps"] = [item for item in dataset["gaps"] if item["category"] != "subnational_statistics"]
    dataset["gaps"].append({
        "category": "subnational_statistics", "status": "partial",
        "detail": "2022 census population adopted for 13 administrative regions from official MOH yearbook citing GASTAT. Governorate/local census tables, other subjects and official code/boundary matching remain open.",
        "next_action": "Acquire the direct GASTAT 2022 tabulation and detailed governorate data; verify legal planning units and actual materials.",
    })
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["saudi-moh-yearbook-2022-census-regions"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"url": SOURCE_URL, "retrieved_at_utc": stamp,
               "size_bytes": raw.stat().st_size, "sha256": SOURCE_HASH,
               "redistribution_terms": "review_required"}
    (project / "raw" / (SOURCE_FILE + ".receipt.json")).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    with (evidence / "NAME_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("yearbook_region", "reference_region", "territory_id",
                         "reference_shape_id", "status"))
        writer.writerows(crosswalk)
    audit = {"country": "SAU", "status": "partial_import_not_accepted",
             "source_url": SOURCE_URL, "sha256": SOURCE_HASH,
             "table": "PDF page 51, Table 1-12", "adopted_columns": ["2022"],
             "unadopted_columns": [str(year) for year in range(2010, 2022)],
             "reason_unadopted": "Recalculated estimates, not the 2022 census enumeration",
             "regions": 13, "national": 32175224, "observations": len(observations),
             "reconciliation": "All 13 printed 2022 administrative-region values sum to the printed national total.",
             "unresolved": ["Direct GASTAT tabulation", "Governorate tables and themes", "Official codes and 2022 boundaries", "Planning law and documents", "Redistribution terms"]}
    (evidence / "SAU_CENSUS_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"regions": 13, "observations": len(observations),
                      "national": 32175224}))


if __name__ == "__main__":
    main()

"""Partially adopt Jordan DoS 2015 census Table 2.17 with source-wide checks.

The public-network category is a *main drinking-water source*, not a measure
of safe water, reliability, quality or access. The table's occupied-housing
unit/household universe excludes the incomplete records noted in the PDF.
"""

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


FILENAME = "Census2015_Housing_2.17.pdf"
SHA256 = "266ed17dc71faabaedc308793556d0fdb56f62789bf21cfb20eb862924a8e88d"
URL = "https://dosweb.dos.gov.jo/DataBank/Census2015/HousingUnits/Housing_2.17.pdf"
SOURCE_ID = "jor-dos-census2015-housing-table-2-17"
PREFIX = "JOR_CENSUS2015_WATER_"
AREA_NAMES = ("Jordan", "Amman", "Balqa", "Zarqa", "Madaba", "Irbid", "Mafraq",
              "Jerash", "Ajloun", "Karak", "Tafielah", "Ma'an", "Aqaba")
GOV_ALIASES = {"Tafielah": "Tafilah"}
CATEGORIES = ("Public Network", "Filter at Home", "Tank", "Rain Water/ Well",
              "Mineral Water (Filtered)", "Artesian Well", "Spring", "Others",
              "Unspecified", "Total")
FIELDS = ("persons_collective", "persons_private", "persons_total",
          "households_collective", "households_private", "households_total", "houseunits_total")
WATER_NOTE = " 2015 census Table 2.17 is a separate historic occupied-housing-unit/household universe; its drinking-water source categories are not safe-water quality measures."


def parse_source(path):
    completed = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                               capture_output=True, text=True, encoding="utf-8")
    pages = completed.stdout.split("\f")
    if len(pages) - (pages[-1] == "") != 8:
        raise ValueError(f"Expected eight PDF pages, found {len(pages)}")
    heading = re.compile(r"^\s*(" + "|".join(re.escape(name) for name in AREA_NAMES) + r")\s+[^\d\s].*$")
    category = re.compile(r"^\s*(" + "|".join(re.escape(name) for name in sorted(CATEGORIES, key=len, reverse=True))
                          + r")\s+" + r"\s+".join([r"(\d+)"] * 7) + r"\s+.*$")
    table = {}
    current = None
    for page_number, page in enumerate(pages[:8], 1):
        for line_number, line in enumerate(page.splitlines(), 1):
            area = heading.match(line)
            if area:
                current = area.group(1)
                if current in table:
                    raise ValueError(f"Duplicate governorate heading: {current}")
                table[current] = {}
                continue
            row = category.match(line)
            if not row:
                continue
            if current is None:
                raise ValueError(f"Category before governorate at PDF page {page_number}")
            label = row.group(1)
            if label in table[current]:
                raise ValueError(f"Duplicate {current}/{label}")
            values = [int(value) for value in row.groups()[1:]]
            if values[0] + values[1] != values[2] or values[3] + values[4] != values[5]:
                raise ValueError(f"Source component identity failed: {current}/{label}")
            table[current][label] = {"values": dict(zip(FIELDS, values)),
                                     "locator": f"Table 2.17 PDF p{page_number}, {current}, {label}",
                                     "physical_page": page_number, "line_on_page": line_number}
    if set(table) != set(AREA_NAMES):
        raise ValueError(f"Source governorates changed: {sorted(table)}")
    for area, rows in table.items():
        if set(rows) != set(CATEGORIES):
            raise ValueError(f"Incomplete categories for {area}: {sorted(rows)}")
        for field in FIELDS:
            total = rows["Total"]["values"][field]
            parts = sum(rows[label]["values"][field] for label in CATEGORIES if label != "Total")
            if parts != total:
                raise ValueError(f"Category sum differs for {area}/{field}: {parts} != {total}")
    for label in CATEGORIES:
        for field in FIELDS:
            national = table["Jordan"][label]["values"][field]
            local_sum = sum(table[area][label]["values"][field] for area in AREA_NAMES if area != "Jordan")
            if local_sum != national:
                raise ValueError(f"National/governorate sum differs for {label}/{field}: {local_sum} != {national}")
    if table["Jordan"]["Public Network"]["values"]["persons_total"] != 5435650 or table["Jordan"]["Total"]["values"]["persons_total"] != 9453124:
        raise ValueError("National Table 2.17 source anchors changed")
    return table


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    project = Path(args.project)
    raw = project / "raw" / "official-jordan" / FILENAME
    if hashlib.sha256(raw.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Census Table 2.17 source hash changed")
    table = parse_source(raw)
    dashboard = project / "data" / "dashboard.json"
    data = json.loads(dashboard.read_text(encoding="utf-8"))
    if data["country"]["id"] != "JOR":
        raise ValueError("Expected Jordan candidate")
    gov = {area["name"]: area["id"] for area in data["territories"] if area["parent_id"] == "JOR"}
    if len(gov) != 12 or set(gov) != {GOV_ALIASES.get(name, name) for name in AREA_NAMES if name != "Jordan"}:
        raise ValueError("Governorate crosswalk is incomplete")
    data["sources"] = [item for item in data["sources"] if item["id"] != SOURCE_ID]
    data["indicators"] = [item for item in data["indicators"] if not item["id"].startswith(PREFIX)]
    data["observations"] = [item for item in data["observations"] if not item["indicator_id"].startswith(PREFIX)]
    base_note = ("2015 DoS census Table 2.17. Universe: persons or households in occupied housing units covered by this table. "
                 "Hotels and collective housing units, 15,576 incomplete private households and 219 incomplete collective households are excluded per source footnotes. "
                 "A main drinking-water source does not establish water safety, quality, treatment, reliability or continuity.")
    definitions = (
        ("PUBLIC_NETWORK_PERSONS", "Persons whose main drinking-water source is the public network, 2015", "people", "persons_total", "Public Network", "sum", 0),
        ("TOTAL_PERSONS", "Persons in occupied housing units in water-source table, 2015", "people", "persons_total", "Total", "sum", 0),
        ("PUBLIC_NETWORK_PERSON_SHARE", "Share of persons with public network as main drinking-water source, 2015", "%", "persons_total", "ratio", "none", 2),
        ("PUBLIC_NETWORK_HOUSEHOLDS", "Households whose main drinking-water source is the public network, 2015", "households", "households_total", "Public Network", "sum", 0),
        ("TOTAL_HOUSEHOLDS", "Households in occupied housing units in water-source table, 2015", "households", "households_total", "Total", "sum", 0),
        ("PUBLIC_NETWORK_HOUSEHOLD_SHARE", "Share of households with public network as main drinking-water source, 2015", "%", "households_total", "ratio", "none", 2),
    )
    for suffix, name, unit, field, category, aggregation, decimals in definitions:
        calculated = category == "ratio"
        data["indicators"].append({"id": PREFIX + suffix, "name": name,
                                   "theme": "2015 census · Drinking-water source", "unit": unit,
                                   "definition": base_note + (" AreaData calculates 100 × public-network count ÷ source total for the same area and universe." if calculated else " Count is source-reported, not an AreaData estimate."),
                                   "population": "Persons" if field == "persons_total" else "Households",
                                   "source_id": SOURCE_ID, "aggregation": aggregation,
                                   "measurement_method": "areadata_calculated" if calculated else "source_reported",
                                   "series_family": "census", "period_policy": "latest_available_per_indicator",
                                   "display_decimals": decimals})
    observations = []
    for source_name in AREA_NAMES:
        territory_id = "JOR" if source_name == "Jordan" else gov[GOV_ALIASES.get(source_name, source_name)]
        rows = table[source_name]
        for suffix, name, unit, field, category, aggregation, decimals in definitions:
            if category == "ratio":
                numerator = rows["Public Network"]["values"][field]
                denominator = rows["Total"]["values"][field]
                if denominator <= 0 or numerator > denominator:
                    raise ValueError(f"Invalid ratio for {source_name}/{field}")
                value = round(numerator / denominator * 100, 6)
                locator = rows["Public Network"]["locator"] + f", {field}; " + rows["Total"]["locator"] + f", {field}"
                row = {"numerator": numerator, "denominator": denominator,
                       "provenance": "calculated", "measurement_method": "areadata_calculated",
                       "footnote": "AreaData: 100 × source public-network count ÷ source total within the same 2015 table and area."}
            else:
                value = rows[category]["values"][field]
                locator = rows[category]["locator"] + f", {field}"
                row = {"measurement_method": "source_reported"}
            observations.append({"territory_id": territory_id, "indicator_id": PREFIX + suffix,
                                 "period": "2015", "value": value, "status": "observed",
                                 "source_id": SOURCE_ID, "source_locator": locator, **row})
    if len(observations) != 78:
        raise ValueError("Expected 6 × 13 Table 2.17 observations")
    data["observations"] += observations
    stamp = datetime.now(timezone.utc).isoformat()
    retrieved = datetime.fromtimestamp(raw.stat().st_mtime, timezone.utc).isoformat()
    data["sources"].append({"id": SOURCE_ID, "name": "DoS 2015 Population and Housing Census, Table 2.17: main drinking-water source",
                            "url": URL, "publisher": "Jordan Department of Statistics", "reference_period": "2015 census",
                            "geographic_level": "national and 12 governorates",
                            "status": "ready", "retrieved_at": retrieved, "sha256": SHA256,
                            "raw_path": f"raw/official-jordan/{FILENAME}", "license": "terms_review_required",
                            "note": "All nine source categories, seven numeric fields and 13 areas were inventoried and reconciled. Four public-network/total count fields plus two AreaData percentage calculations adopted; other source categories/fields retained in the private inventory."})
    data["generated_at"] = stamp
    data["country"]["geography_note"] = data["country"]["geography_note"].replace(WATER_NOTE, "") + WATER_NOTE
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] + ["jordan-dos-census2015-water-table-2-17"]))
    for gap in data["gaps"]:
        if gap["category"] == "subnational_statistics":
            gap["detail"] += " One 2015 census governorate water-source table is also separately integrated for public-network counts and shares; other thematic census tables remain unassessed." if "One 2015 census governorate" not in gap["detail"] else ""
            gap["next_action"] = "Review remaining 2015 census table catalogue and all unadopted categories/fields; verify official codes and compatible 2015/2025 boundary versions; keep the 2015 water-source universe separate from 2025 population estimates."
    dashboard.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "JOR_CENSUS_WATER_TABLE_2_17.json").write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {"source_url": URL, "source_sha256": SHA256, "status": "partial_table_adoption_not_accepted",
             "areas": len(table), "categories_per_area": 10, "numeric_fields_per_category": list(FIELDS),
             "identities": "For all 13 areas and 10 rows, person/household components reconcile; nine category rows sum to source Total in all seven numeric fields; all 12 governorates sum to national in every category/field.",
             "adopted_indicators": [PREFIX + item[0] for item in definitions], "adopted_observations": len(observations),
             "national_public_network_persons": table["Jordan"]["Public Network"]["values"]["persons_total"],
             "national_table_persons": table["Jordan"]["Total"]["values"]["persons_total"],
             "limitations": ["One of many official 2015 census tables", "No official code or 2015 boundary join",
                             "Public network is not safe-water quality", "Source redistribution terms require review",
                             "No independent country ACCEPT or publication"]}
    (evidence / "JOR_CENSUS_WATER_IMPORT_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"areas": len(table), "categories": 10, "fields": 7,
                      "indicators": 6, "observations": len(observations),
                      "national_public_network_persons": audit["national_public_network_persons"]}))


if __name__ == "__main__":
    main()

"""Adopt four direct PCBS 2017 census counts for 19 source reporting areas."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "pse-pcbs-phc-2017-summary-table2"
RAW_PATH = "raw/palestine-pcbs-2017/pcbs-2017-final-summary.pdf"
SOURCE_HASH = "25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f"
ROWS_PATH = "evidence/PSE_PCBS_2017_TABLE2_ROWS.csv"
ROWS_HASH = "39d66bedf533c076cbd0fe397ac8293b84f4741578844b15d9e7baa9d01e5d07"
METHOD = "pcbs_2017_final_census_count_with_post_enumeration_population_estimates"
FIELDS = (
    ("TOTAL", "total", "Population, both sexes", "people"),
    ("FEMALE", "females", "Female population", "people"),
    ("MALE", "males", "Male population", "people"),
    ("HOUSEHOLDS", "households", "Households", "households"),
)
NAMES = ["Palestine", "West Bank", "Jenin", "Tubas & Northern Valleys", "Tulkarm", "Nablus",
         "Qalqiliya", "Salfit", "Ramallah & Al-Bireh", "Jericho & Al Aghwar", "Jerusalem",
         "Bethlehem", "Hebron", "Gaza Strip", "North Gaza", "Gaza", "Dier al Balah",
         "Khan Yunis", "Rafah"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(name):
    return re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "PSE" or any(item["id"] == SOURCE_ID for item in dataset["sources"]):
        raise ValueError("Expected unmodified PSE bootstrap candidate")
    original = project / RAW_PATH
    receipt = json.loads((project / (RAW_PATH + ".receipt.json")).read_text(encoding="utf-8"))
    if sha(original) != SOURCE_HASH or receipt["sha256"] != SOURCE_HASH or receipt["status"] != "acquired":
        raise ValueError("PCBS official summary original/receipt changed")
    if sha(project / ROWS_PATH) != ROWS_HASH:
        raise ValueError("Re-run pinned PCBS Table 2 structural inspector")
    structure = json.loads((project / "evidence/PSE_PCBS_2017_STRUCTURE.json").read_text(encoding="utf-8"))
    if structure["summary_pdf_sha256"] != SOURCE_HASH or structure["table2_rows"] != 19 or \
            structure["table2_adopted_count_columns"] != 4 or structure["table29_locality_codes"] != 585:
        raise ValueError("PCBS source coverage inspection changed")
    with (project / ROWS_PATH).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if [row["name"] for row in rows] != NAMES:
        raise ValueError("PCBS Table 2 source order changed")
    for row in rows:
        for _, field, _, _ in FIELDS:
            row[field] = int(row[field])
        if row["females"] + row["males"] != row["total"]:
            raise ValueError(f"Sex total mismatch for {row['name']}")
    for region, children in ((rows[1], rows[2:13]), (rows[13], rows[14:])):
        for _, field, _, _ in FIELDS:
            if sum(child[field] for child in children) != region[field]:
                raise ValueError(f"Governorates differ from source {region['name']} {field}")
    for _, field, _, _ in FIELDS:
        if rows[1][field] + rows[13][field] != rows[0][field]:
            raise ValueError(f"Regions differ from source Palestine {field}")

    bootstrap_areas = [item["name"] for item in dataset["territories"] if item["id"] != "PSE"]
    country = next(item for item in dataset["territories"] if item["id"] == "PSE")
    country.update(name="Palestine", type="country", reporting_role="PCBS 2017 national census reporting area",
                   source_id=SOURCE_ID, code_system="PCBS census report label; ISO3 PSE is the dataset key",
                   boundary_version=None)
    dataset["country"].update(name="Palestine", requested_name="Palestine")
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    area_ids = {"Palestine": "PSE"}
    for index, row in enumerate(rows[1:], 1):
        region = index in (1, 13)
        parent = "PSE" if region else (area_ids["West Bank"] if index < 13 else area_ids["Gaza Strip"])
        area_id = "PSE:PCBS2017:" + ("REG:" if region else "GOV:") + slug(row["name"])
        area_ids[row["name"]] = area_id
        dataset["territories"].append({
            "id": area_id, "name": row["name"], "level": "adm1" if region else "adm2",
            "type": "PCBS 2017 census reporting region" if region else "PCBS 2017 census governorate",
            "parent_id": parent, "official_code": None,
            "code_system": "PCBS 2017 Summary Table 2 name; official governorate code not printed here",
            "provider_code": None, "source_id": SOURCE_ID, "boundary_version": None,
            "reconciliation_status": "source_label_only; dated_official_code_and_polygon_not_verified",
        })

    dataset["sources"].append({
        "id": SOURCE_ID, "name": "PCBS Population, Housing and Establishments Census 2017, Final Results Summary, Table 2",
        "url": receipt["source_url"], "publisher": "Palestinian Central Bureau of Statistics",
        "reference_period": "2017 final census", "geographic_level": "Palestine; West Bank and Gaza Strip reporting regions; 16 governorates",
        "status": "ready", "retrieved_at": receipt["retrieved_at"], "raw_path": RAW_PATH,
        "sha256": SOURCE_HASH, "license": "official_publication_redistribution_terms_review_required",
        "note": "Only Table 2 page 71 four printed count fields are adopted. Population includes counted persons and uncounted estimates from the post-enumeration survey (page 71 footnote). The 2017 historical values are not current population; households are a separate count. Table 29 has 585 locality codes but 56 wrapped rows, so no locality counts are adopted. The 270-page detailed report and 2019 area table remain unassessed. WDI national annual estimates use a separate economy series and are not definitionally harmonized. No legal polygon or planning status follows from this table.",
    })
    for suffix, _, label, unit in FIELDS:
        dataset["indicators"].append({
            "id": "PSE_PCBS_2017_" + suffix, "name": label + " (PCBS census 2017)",
            "theme": "Population" if suffix != "HOUSEHOLDS" else "Households", "unit": unit,
            "source_id": SOURCE_ID,
            "definition": "Direct printed count from PCBS PHC 2017 Final Results Summary Table 2, page 71. Population counts include actually enumerated persons and estimates of uncounted population from the post-enumeration survey; 2017 historical reporting areas. Households are a separate count. WDI annual estimates and locality table values are distinct and not substituted.",
            "population": "2017 census reporting population" if suffix != "HOUSEHOLDS" else "2017 census households",
            "aggregation": "none", "measurement_method": METHOD, "series_family": "census",
            "display_role": "primary", "period_policy": "latest_available_per_indicator", "display_decimals": 0,
        })
    for index, row in enumerate(rows):
        for suffix, field, _, _ in FIELDS:
            dataset["observations"].append({
                "territory_id": area_ids[row["name"]], "indicator_id": "PSE_PCBS_2017_" + suffix,
                "period": "2017", "value": row[field], "status": "observed", "source_id": SOURCE_ID,
                "measurement_method": METHOD,
                "source_locator": f"Final Results Summary, Table 2, PDF/printed page 71, source row {index + 1}: {row['name']}, {field}",
            })
    adopted = [item for item in dataset["observations"] if item["indicator_id"].startswith("PSE_PCBS_2017_")]
    if len(dataset["territories"]) != 19 or len(adopted) != 76:
        raise ValueError("Expected 19 reporting areas and 76 direct source observations")
    dataset["country"]["geography_note"] = (
        "PCBS 2017 Summary Table 2 reports Palestine, West Bank/Gaza Strip and 16 governorates; all four adopted count fields reconcile through the source hierarchy. This is a historical census reporting hierarchy, not an assertion of current legal boundaries, planning units or 2026 population. Official codes and dated polygons are not verified. Two bootstrap 2021 provider reference polygons were withheld. World Bank PSE is named 'West Bank and Gaza' in WDI, and its national annual estimates remain separate from PCBS 2017 final counts. No locality observations are adopted from wrapped Table 29.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="PCBS Table 2 establishes 2017 source labels and hierarchy for 2 regions/16 governorates. Official governorate codes, dated legal boundaries and exact WDI/PCBS universe alignment remain unresolved; two 2021 provider polygons withheld.",
                       next_action="Acquire dated PCBS/MoLG official code and boundary editions; reconcile Jerusalem/J1/J2 and Gaza/West Bank geography before any map value join.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="Four PCBS 2017 direct count fields adopted for 19 source areas (76 observations). 585 coded locality rows, other Summary tables, detailed 270-page volume, 2019 area table and later projections are not adopted.",
                       next_action="Inventory all relevant PCBS physical tables/columns; resolve 56 wrapped Table 29 rows and validate locality sums and code/boundary version before adopting finer geography.")
        elif gap["category"] == "planning_documents":
            gap.update(status="not_collected", detail="No verified current governorate/municipal plan, planning statute, adopted budget, actual expenditure or official evaluation has been attached to this candidate.",
                       next_action="Research MoLG/Ministry of Planning legal duties and official plan catalogue; distinguish city plans, governorate plans and national policy, acquisition and institutional status.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["palestine-pcbs-2017-table2-partial"]))
    dataset["analysis"]["latest_values_only"] = True
    now = datetime.now(timezone.utc).isoformat()
    dataset["generated_at"] = now
    tuples = sorted((item["territory_id"], item["indicator_id"], item["value"]) for item in adopted)
    audit = {
        "status": "partial_candidate_not_accepted", "checked_at": now,
        "source_sha256": SOURCE_HASH, "table2_rows_sha256": ROWS_HASH,
        "reporting_regions": 2, "reporting_governorates": 16,
        "source_national_controls": {field: rows[0][field] for _, field, _, _ in FIELDS},
        "domestic_observations_added": len(adopted),
        "adopted_tuple_sha256": hashlib.sha256(json.dumps(tuples, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "withheld_bootstrap_polygon_names": bootstrap_areas,
        "unadopted_locality_source_codes": 585, "split_or_wrapped_locality_rows": 56,
        "unresolved": ["2017 official code and legal polygon crosswalk", "All other census source tables and 270-page detail report", "Full 585-locality extraction", "Current plan and budget authority", "42 scenario and independent acceptance"],
    }
    (project / "evidence/PSE_PCBS_2017_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": 19, "regions": 2, "governorates": 16,
                      "domestic_indicators": 4, "observations_added": 76,
                      "national_total": rows[0]["total"]}))


if __name__ == "__main__":
    main()

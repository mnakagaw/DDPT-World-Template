"""Record the GASTAT Tableau location without adopting unverified observations."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "sau-gastat-population-detailed-age-tableau"
SOURCE_URL = (
    "https://tableau.stats.gov.sa/views/"
    "TA3-PopulationbydetailedAgebyRegionGovernorateNationalityandGender_17298115570530/"
    "NW-PopulationbydetailedAgebyRegionGovernorateNationalityandGender"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "SAU":
        raise ValueError("Expected Saudi Arabia project")
    existing = next((source for source in dataset["sources"] if source["id"] == SOURCE_ID), None)
    if existing and (existing["url"] != SOURCE_URL or existing["status"] != "not_collected"):
        raise ValueError("GASTAT source location differs from the expected uncollected lead")

    before = (len(dataset["indicators"]), len(dataset["observations"]),
              len(dataset["documents"]))
    stamp = datetime.now(timezone.utc).isoformat()
    source = {
        "id": SOURCE_ID,
        "name": "GASTAT Population by Detailed Age Tableau view",
        "url": SOURCE_URL,
        "publisher": "General Authority for Statistics (GASTAT)",
        "reference_period": "unverified in the inspected view",
        "geographic_level": "national, region and governorate selection controls; exported row coverage unverified",
        "status": "not_collected",
        "retrieved_at": stamp,
        "license": "terms_review_required",
        "note": (
            "Official public Tableau view with metadata code TTCENPOP0105, age, region, governorate, "
            "nationality and gender dimensions. The view shows a download dialog, but no data file was "
            "acquired or checked. Period, complete row inventory, values, codes and boundary epoch remain "
            "unverified. This source supplies no adopted observation."
        ),
    }
    if existing is None:
        dataset["sources"].append(source)
    for gap in dataset["gaps"]:
        if gap["category"] == "subnational_statistics":
            gap["detail"] = (
                "2022 census-based population adopted for 13 administrative regions from the official "
                "MOH yearbook citing GASTAT. A direct GASTAT detailed-age Tableau view with region and "
                "governorate controls was located, but its data export and reference period were not "
                "verified. No values from that view are adopted. Official codes, boundary matching and "
                "other subjects remain open."
            )
            gap["next_action"] = (
                "Acquire the direct GASTAT table and verify its period, complete row and field inventory, "
                "population definition, geographic codes and boundary epoch; then research the legal "
                "planning unit and actual planning, budget and evaluation materials."
            )
    dataset["generated_at"] = stamp
    after = (len(dataset["indicators"]), len(dataset["observations"]),
             len(dataset["documents"]))
    if after != before:
        raise AssertionError("Source registration must not add indicators, observations or documents")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "partial_official_locations_identified",
        "checked_at": stamp,
        "origin_registry": "AreaData 2026-09-26 Saudi domestic source pass",
        "census": {"url": SOURCE_URL, "reference_period": "unverified",
                   "acquisition": "not_collected", "metadata_code": "TTCENPOP0105"},
        "planning": None,
        "sources": [
            {"id": "sau-moh-yearbook-2022-census-regions",
             "url": "https://www.moh.gov.sa/en/Ministry/Statistics/book/Documents/Statistical-Yearbook-2022.pdf",
             "site_status": "ready"},
            {"id": SOURCE_ID, "url": SOURCE_URL, "site_status": "not_collected"},
        ],
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = ("Research status: **source_locations_not_pre_researched**\n\n"
           "No country-specific source locations are pre-researched yet. Complete the first required action below.")
    new = ("Research status: **partial_official_locations_identified** (2026-09-26).\n\n"
           "The official MOH Yearbook 2022 Table 1-12 has been acquired and its country/13-region 2022 "
           "population column adopted with source limits. The official GASTAT Population by Detailed Age "
           "Tableau view (TTCENPOP0105) was located, but no export or period was verified; it adds no value. "
           "Planning, codes and census-date boundaries remain open. See SAU_GASTAT_TABLEAU_SOURCE_LOCATION.json.")
    if old in markdown:
        markdown = markdown.replace(old, new)
    elif new not in markdown:
        raise ValueError("Unexpected Saudi source preflight Markdown")
    markdown_path.write_text(markdown, encoding="utf-8")
    audit = {
        "schema_version": "1.0", "checked_at": stamp, "country_area_id": "SAU",
        "source_id": SOURCE_ID, "url": SOURCE_URL, "metadata_code": "TTCENPOP0105",
        "acquisition": "not_collected", "reference_period": "unverified",
        "export_attempt": "Excel crosstab dialog opened; no verifiable downloaded file",
        "visible_dimensions": ["detailed age", "region", "governorate", "nationality", "gender"],
        "row_inventory": "unverified", "observations_adopted": 0, "documents_adopted": 0,
        "candidate_counts": {"indicators": after[0], "observations": after[1], "documents": after[2]},
    }
    audit_path = project / "evidence/SAU_GASTAT_TABLEAU_SOURCE_LOCATION.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_id": SOURCE_ID, "status": "not_collected",
                      "indicators": after[0], "observations": after[1], "documents": after[2]}))


if __name__ == "__main__":
    main()

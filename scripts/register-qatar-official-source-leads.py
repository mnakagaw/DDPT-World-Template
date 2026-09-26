"""Register acquired official Qatar source locations without making plan-status claims."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def load_receipts(project, manifest_path):
    path = manifest_path.resolve(strict=True)
    if not path.is_relative_to(project):
        raise ValueError("Source manifest must be inside the country project")
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    receipts = {}
    for receipt in manifest["receipts"]:
        if receipt["status"] != "acquired":
            raise ValueError(f"Source not acquired: {receipt['file']}")
        file_path = path.parent / receipt["file"]
        if hashlib.sha256(file_path.read_bytes()).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Source hash mismatch: {file_path}")
        receipt = dict(receipt)
        receipt["raw_path"] = str(file_path.relative_to(project)).replace("\\", "/")
        receipts[receipt["file"]] = receipt
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--census-manifest", type=Path, required=True)
    parser.add_argument("--planning-manifest", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    census = load_receipts(project, args.census_manifest)
    planning = load_receipts(project, args.planning_manifest)
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "QAT" or not any(item["id"] == "QAT_CENSUS2020_POP_TOTAL" for item in data["indicators"]):
        raise ValueError("Expected Qatar census partial candidate")
    now = datetime.now(timezone.utc).isoformat()
    candidates = [
        ("qat-npc-census2020-catalogue", census["results-page.html"], "Census 2020 detailed results catalogue",
         "Qatar National Planning Council", "National and eight 2020 census municipalities",
         "Official catalogue and detailed reports acquired. The workbook has 156 numbered tables; only nine provide the adopted subset."),
        ("qat-mm-qnmp-products", planning["qnmp-products.html"], "Qatar National Master Plan product catalogue",
         "Ministry of Municipality (Qatar)", "National and municipality planning products",
         "Official planning-product location only; current adoption, legal force and coverage of each municipality need separate verification."),
        ("qat-mm-qnmp-zoning", planning["qnmp-msdp-zoning.html"], "Municipality spatial development plan zoning page",
         "Ministry of Municipality (Qatar)", "Six named MSDP zoning municipalities; Al Khor and Al Wakra described as future extension",
         "The site describes six named zoning areas and future extension to Al Khor and Al Wakra. Page currency and current operative scope are not established."),
        ("qat-mm-doha-msdp-volume1-2014", planning["doha-municipality-strategy-2017.pdf"], "Doha Municipality Vision and Development Strategy, Volume 1",
         "Ministry of Municipality (Qatar), Qatar National Master Plan", "Doha Municipality; cover dated 1 June 2014",
         "Official PDF acquired and cover plus section 1.1–1.2 read. Despite its URL filename containing Dec 2017, the cover states 1 June 2014. Current plan approval, revision and territory correspondence are unverified; not a site planning document yet."),
        ("qat-gis-municipality-current", planning["municipality-gis-current.json"], "MunicipalityAT GIS service current municipality attributes",
         "Qatar GIS service", "Eight current municipality records; not a December 2020 boundary edition",
         "All eight feature STARTDATE values are after December 2020, including Al Daayen in 2026. Official code candidates and current geometry location only; no 2020 census join or polygon is adopted."),
    ]
    existing = {item["id"] for item in data["sources"]}
    if any(source_id in existing for source_id, *_ in candidates):
        raise ValueError("Qatar source locations already registered")
    for source_id, receipt, name, publisher, geography, note in candidates:
        data["sources"].append({"id": source_id, "name": name, "url": receipt["url"],
            "publisher": publisher, "reference_period": "Source body as acquired on 2026-09-26; source-specific period in note",
            "geographic_level": geography, "status": "partial", "retrieved_at": receipt["retrieved_at"],
            "raw_path": receipt["raw_path"], "sha256": receipt["sha256"],
            "license": "Official source reuse terms require review before external release", "note": note})
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_census_workbook_acquired_partial_municipality_adoption",
        "checked_at": now,
        "origin_registry": "AreaData Qatar NPC Census 2020 and Ministry of Municipality official-source pass, 2026-09-26",
        "census": {"status": "156_numbered_tables_acquired_17_direct_indicators_partially_adopted",
            "note": "The official workbook has 209 sheets, 156 numbered tables and 1588 numeric columns. Seventeen direct count indicators use 153 national/municipality cells from nine tables; all other cells remain priority_unassessed."},
        "local_statistics": {"status": "eight_census_municipalities_partial_direct_counts",
            "note": "Eight December 2020 census municipalities each have 17 direct observations and a distinct national reported control. WDI national series remain a separate source family."},
        "geography": {"status": "census_labels_only_2020_official_codes_and_polygons_unverified",
            "note": "Current official GIS attributes give eight code candidates, but all recorded STARTDATE values postdate the census. No dated polygon or code is joined to the census candidate."},
        "planning": {"status": "official_catalogue_and_historical_doha_original_acquired_not_adopted",
            "note": "QNMP catalogue/zoning pages and the Doha Volume 1 PDF are acquired. Its cover is 1 June 2014 despite a Dec 2017 URL filename. Current legal force, geographic match, individual budgets, implementation and evaluation are unverified."},
        "sources": [{"id": source_id, "url": receipt["url"], "site_status": "acquired_location_only_not_adopted_as_plan_or_geometry"}
                    for source_id, receipt, *_ in candidates],
        "cross_country_candidates": "Generated common-source candidates remain availability_not_checked_for_country except separately acquired WDI national series; no common local source is assumed available."
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (project / "evidence/SOURCE_PREFLIGHT.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Qatar official-source update, 2026-09-26\n\n"
            "The initially unresearched entry is superseded by `SOURCE_PREFLIGHT.json` country_research. "
            "The acquired 209-sheet Census 2020 workbook has 156 numbered tables and 1,588 numeric columns. "
            "Seventeen direct count indicators use 153 published national/municipality cells from nine tables; all other cells remain `priority_unassessed`. "
            "The eight 2020 municipality labels have no accepted historical polygons or official codes. "
            "QNMP catalogue, zoning page and a historical Doha strategy PDF were acquired, but current municipal plan/finance status is not adopted.\n")
    resource = {"status": "partial_source_pass", "checked_at": now,
        "census_manifest": str(args.census_manifest.resolve().relative_to(project)).replace("\\", "/"),
        "planning_manifest": str(args.planning_manifest.resolve().relative_to(project)).replace("\\", "/"),
        "resources": [{"source_id": source_id, "url": receipt["url"], "raw_path": receipt["raw_path"],
                       "sha256": receipt["sha256"], "bytes": receipt["bytes"],
                       "disposition": "official_location_identified_not_plan_or_geometry_adopted"}
                      for source_id, receipt, *_ in candidates]}
    (project / "evidence/SOURCE_RESOURCE_INVENTORY.json").write_text(json.dumps(resource, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"official_source_leads": len(candidates), "census_tables": 156, "adopted_indicators": 17}))


if __name__ == "__main__":
    main()

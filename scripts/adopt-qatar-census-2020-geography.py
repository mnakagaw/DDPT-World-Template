"""Attach audited 2020 GIS municipality codes and display polygons to Qatar R2.

Requires the independent NPC Table 1/zone-population crosscheck and Shapely
topology audit. No zone population or plan status is promoted by this step.
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--geography-manifest", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    manifest_path = args.geography_manifest.resolve(strict=True)
    if not manifest_path.is_relative_to(project):
        raise ValueError("Manifest must be inside the country project")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    receipts = {}
    for receipt in manifest["receipts"]:
        if receipt["status"] != "acquired":
            raise ValueError(f"Unacquired source: {receipt['file']}")
        path = manifest_path.parent / receipt["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Receipt hash mismatch: {path}")
        receipts[receipt["file"]] = receipt
    audit = json.loads((project / "evidence/QAT_CENSUS2020_GEOGRAPHY_AUDIT.json").read_text(encoding="utf-8"))
    topology = json.loads((project / "evidence/QAT_CENSUS2020_TOPOLOGY_AUDIT.json").read_text(encoding="utf-8"))
    derived_path = project / "evidence/QAT_CENSUS2020_MUNICIPAL_BOUNDARIES.geojson"
    if audit["census_zone_features"] != 91 or audit["reported_2020_population_rows"] != 90 or \
            audit["missing_2020_population_zones"] != [{"zone_no": 99, "municipal_code": "7", "status": "source_null_not_zero"}]:
        raise ValueError("Historical geography audit is incomplete or changed")
    if topology["source_geojson_sha256"] != audit["geojson_sha256"] or \
            topology["derived_geojson_sha256"] != hashlib.sha256(derived_path.read_bytes()).hexdigest() or \
            topology["derived_municipality_count"] != 8:
        raise ValueError("Derived polygon topology audit mismatch")
    derived = json.loads(derived_path.read_text(encoding="utf-8"))
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "QAT" or len(data["boundaries"]["features"]) != 0 or \
            any(row["official_code"] is not None for row in data["territories"] if row["parent_id"] == "QAT"):
        raise ValueError("Expected a Qatar partial candidate with no prior historical geography adoption")
    census_indicators = {row["id"] for row in data["indicators"] if row["id"].startswith("QAT_CENSUS2020_")}
    if len(census_indicators) != 17:
        raise ValueError("Expected 17 direct NPC indicators before geography adoption")
    names = {row["id"]: row for row in data["territories"] if row["parent_id"] == "QAT"}
    features = derived["features"]
    if len(features) != 8 or {feature["properties"]["territory_id"] for feature in features} != set(names):
        raise ValueError("Eight GIS and census territory identities do not match")
    controls = {row["municipal_code"]: row for row in audit["municipalities"]}
    if set(controls) != {str(number) for number in range(1, 9)}:
        raise ValueError("Expected all eight GIS municipality codes")
    for feature in features:
        identity = feature["properties"]
        area = names[identity["territory_id"]]
        control = controls[identity["official_code"]]
        if control["gis_name"] != f"{area['name']} Municipality" or \
                identity["source_zone_count"] != control["zone_count"] or \
                identity["boundary_version"] != "Census_Zone_2020":
            raise ValueError(f"GIS/census area or geometry edition mismatch: {area['id']}")
        for suffix, value in (("POP_TOTAL", control["total_2020"]),
                              ("POP_MALE", control["male_2020"]),
                              ("POP_FEMALE", control["female_2020"])):
            rows = [row for row in data["observations"] if row["territory_id"] == area["id"] and
                    row["indicator_id"] == f"QAT_CENSUS2020_{suffix}"]
            if len(rows) != 1 or rows[0]["value"] != value:
                raise ValueError(f"Direct NPC observation does not match GIS control: {area['id']}/{suffix}")
        area["official_code"] = identity["official_code"]
        area["code_system"] = identity["code_system"]
        area["boundary_version"] = identity["boundary_version"]
        area["source_id"] = "qat-gis-census-zone-2020"
        area["census_label_source_id"] = "qat-npc-census2020-table-1"
    for row in data["observations"]:
        if row["territory_id"] in names and row["indicator_id"] in census_indicators:
            row["boundary_version"] = "Census_Zone_2020"
        if row["indicator_id"] in census_indicators:
            row["footnote"] = ("Published December 2020 census table cell; historical GIS municipality code and "
                "display polygon are crosschecked where applicable; later legal boundaries and planning "
                "jurisdictions are not inferred")
    data["boundaries"] = derived
    raw_path = lambda file: str((manifest_path.parent / file).relative_to(project)).replace("\\", "/")
    sources = [
        {"id": "qat-gis-census-zone-2020", "name": "Official Census_Zone_2020 polygons and municipality codes",
         "url": receipts["census-zone-2020-polygons.geojson"]["url"], "publisher": "Qatar GIS service",
         "reference_period": "Census 2020 geographic edition", "geographic_level": "91 census zones / eight municipalities",
         "status": "ready", "retrieved_at": receipts["census-zone-2020-polygons.geojson"]["retrieved_at"],
         "raw_path": raw_path("census-zone-2020-polygons.geojson"),
         "sha256": receipts["census-zone-2020-polygons.geojson"]["sha256"],
         "license": "Qatar GIS service reuse terms require review before external release",
         "note": "The 91 zone polygons and MUNICIPAL_CODE 1–8 were crosschecked against 2020 sex counts and NPC Table 1. Eight display-only municipality polygons were dissolved from the same GIS edition with no simplification. Zone 99 has null male/female population, not zero. This is not a 2026 legal boundary certification."},
        {"id": "qat-mm-qnmp-msdp-eight", "name": "QNMP page describing eight municipality spatial development plans",
         "url": receipts["qnmp-msdp-eight-municipalities.html"]["url"], "publisher": "Ministry of Municipality (Qatar)",
         "reference_period": "Website statement acquired 2026-09-26; current plan editions not established",
         "geographic_level": "eight named municipalities", "status": "partial",
         "retrieved_at": receipts["qnmp-msdp-eight-municipalities.html"]["retrieved_at"],
         "raw_path": raw_path("qnmp-msdp-eight-municipalities.html"),
         "sha256": receipts["qnmp-msdp-eight-municipalities.html"]["sha256"],
         "license": "Ministry website reuse terms require review before external release",
         "note": "The page says QNMP completed an MSDP for each of eight municipalities. It does not by itself establish current operative editions, approval, budgets, execution or evaluation. The separate older zoning page describes only six then-covered zoning regulations."},
    ]
    existing = {source["id"] for source in data["sources"]}
    if any(source["id"] in existing for source in sources):
        raise ValueError("Historical GIS/planning leads already adopted")
    data["sources"].extend(sources)
    for source in data["sources"]:
        if source["id"].startswith("qat-npc-census2020-table-"):
            source["note"] = ("Only the listed cells were semantically adopted; the remaining workbook columns/cells "
                "remain unassessed. Historical 2020 GIS municipality codes and display polygons have a separate "
                "crosscheck; current legal boundaries and planning jurisdictions remain unverified.")
    comparison = next(row for row in data["analysis"]["comparisons"] if row["parent_id"] == "QAT")
    comparison["source_ids"] = ["qat-npc-census2020-table-1", "qat-gis-census-zone-2020"]
    comparison["membership_note"] = ("NPC Census 2020 Table 1 and the official Census_Zone_2020 GIS layer have the same eight municipality labels and exactly matching male/female/total population controls. The 91 zone polygons were dissolved only for this 2020 reference display. Later legal boundaries and plan jurisdictions remain separate.")
    data["country"]["geography_note"] = ("Official GIS Census_Zone_2020 gives 91 zone polygons and municipality codes 1–8. GIS zone sex counts reconcile exactly to NPC Census 2020 Table 1; zone 99 has missing population values, not zero. Same-edition polygons were dissolved for display only. Later administrative changes and current planning jurisdictions are not inferred.")
    for gap in data["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="The official Census_Zone_2020 GIS layer and NPC Table 1 now match for all eight 2020 municipality codes and population controls. All 91 polygons have valid topology and were dissolved for display. The current legal boundary/change register and the source's reuse terms are still unverified.", next_action="Verify 2020-to-current code and boundary change register, legal status and GIS reuse terms before public map release.")
        elif gap["category"] == "planning_documents":
            gap.update(status="not_collected", detail="QNMP says an MSDP was completed for each of eight municipalities, while an older zoning page discusses six then-covered municipalities and future extensions. Current plan editions, approval evidence, budgets, execution and evaluation are not adopted.", next_action="Acquire the eight municipality plan originals and approval/revision records, then individual fiscal and implementation evidence.")
    data["collection"]["notes"].append("GIS Census_Zone_2020 source SHA-256 " + receipts["census-zone-2020-polygons.geojson"]["sha256"] + "; 91 zone shapes match eight NPC Table 1 municipality controls. Zone 99 population remains source-null; no zone population was adopted.")
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    crosswalk = project / "evidence/CODE_CROSSWALK.csv"
    with crosswalk.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["territory_id", "census_2020_name", "official_code", "code_system", "boundary_version", "source_zone_count", "evidence_status"])
        for feature in features:
            prop = feature["properties"]
            area = names[prop["territory_id"]]
            writer.writerow([area["id"], area["name"], area["official_code"], area["code_system"],
                             area["boundary_version"], prop["source_zone_count"],
                             "2020 source crosswalk verified; current edition pending"])
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    research = preflight["country_research"]
    research["geography"] = {"status": "2020_codes_and_polygons_source_matched_current_edition_pending",
        "note": "All 91 GIS Census_Zone_2020 polygons, eight codes/names, and 90 reported plus one null zone-population rows were checked; municipal sex/total controls match NPC Table 1. No current legal boundary is inferred."}
    research["planning"] = {"status": "eight_completed_msdp_claim_location_acquired_current_editions_unverified",
        "note": "QNMP page says eight MSDPs completed. The older zoning page describes six then-covered municipalities and future Al Khor/Al Wakra extension. Applicable editions, approval and fiscal/implementation evidence remain open."}
    research["sources"].extend({"id": source["id"], "url": source["url"],
        "site_status": "historical_geometry_adopted_display_only" if source["id"] == "qat-gis-census-zone-2020" else "acquired_location_not_adopted_as_plan"} for source in sources)
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (project / "evidence/SOURCE_PREFLIGHT.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Qatar 2020 GIS and eight-plan-page update\n\n"
            "Official Census_Zone_2020 gives 91 polygon features and eight municipality codes. "
            "The GIS zone sex counts reconcile to NPC Census 2020 Table 1 for every municipality; "
            "zone 99 has null population values. Eight same-edition dissolved municipality shapes are display-only. "
            "QNMP says eight MSDPs completed, but current applicable editions and approval are unverified.\n")
    inventory_path = project / "evidence/SOURCE_RESOURCE_INVENTORY.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["resources"].extend({"source_id": source["id"], "url": source["url"],
        "raw_path": source["raw_path"], "sha256": source["sha256"],
        "disposition": "historical_geometry_display_only" if source["id"] == "qat-gis-census-zone-2020" else "official_location_identified_current_plan_not_adopted"} for source in sources)
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"historical_municipalities": len(features), "zone_polygons": 91,
        "zone_99_population": "source_null", "planning_documents_adopted": len(data["documents"])}))


if __name__ == "__main__":
    main()

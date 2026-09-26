"""Audit the official 2020 zone/GIS crosswalk against NPC Census 2020 Table 1.

This checks source identity, all 91 rows and coordinates, and independent
published municipality controls. It does not by itself approve GIS reuse or
assert plan authority.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


EXPECTED = [
    ("1", "Doha Municipality", 9),
    ("2", "Al Rayyan Municipality", 10),
    ("3", "Al Wakra Municipality", 11),
    ("4", "Umm Slal Municipality", 12),
    ("5", "Al Daayen Municipality", 15),
    ("6", "Al Khor and Al Thakhira Municipality", 13),
    ("7", "Al Shamal Municipality", 14),
    ("8", "Al Sheehaniya Municipality", 16),
]


def receipt_files(project, manifest_path):
    manifest_path = manifest_path.resolve(strict=True)
    if not manifest_path.is_relative_to(project):
        raise ValueError("Manifest must be inside country project")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    result = {}
    for receipt in manifest["receipts"]:
        if receipt["status"] != "acquired":
            raise ValueError(f"Unacquired source: {receipt['file']}")
        path = manifest_path.parent / receipt["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Receipt hash mismatch: {path}")
        result[receipt["file"]] = (path, receipt)
    return result


def integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected nonnegative integer: {label}: {value!r}")
    return value


def rings(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    raise ValueError(f"Unexpected geometry type: {geometry['type']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--census-manifest", type=Path, required=True)
    parser.add_argument("--geography-manifest", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    census = receipt_files(project, args.census_manifest)
    geography = receipt_files(project, args.geography_manifest)
    original, original_receipt = census["Census_Final_Results.xlsx"]
    layer = json.loads(geography["census-zone-2020-layer.json"][0].read_text(encoding="utf-8-sig"))
    polygons = json.loads(geography["census-zone-2020-polygons.geojson"][0].read_text(encoding="utf-8-sig"))
    population = json.loads(geography["census-zone-population-2020.json"][0].read_text(encoding="utf-8-sig"))
    planning = geography["qnmp-msdp-eight-municipalities.html"][0].read_text(encoding="utf-8-sig")
    if layer["name"] != "Census_Zone_2020" or layer["geometryType"] != "esriGeometryPolygon":
        raise ValueError("Not the Census_Zone_2020 polygon layer")
    fields = {field["name"] for field in layer["fields"]}
    if not {"ZONE_NO", "MUNICIPAL_CODE", "MUNICIPALITY_NAME_EN"} <= fields:
        raise ValueError("Historical code/name fields missing")
    if polygons["type"] != "FeatureCollection" or len(polygons["features"]) != 91:
        raise ValueError("Expected all 91 historical zone polygons")
    if len(population["features"]) != 91:
        raise ValueError("Expected all 91 historical zone population rows")
    if "completed an MSDP for each of the 8 municipalities" not in planning:
        raise ValueError("QNMP eight-plan statement changed")

    expected_names = {code: name for code, name, _ in EXPECTED}
    by_zone = {}
    zone_counts = defaultdict(int)
    vertices = 0
    bounds = [180.0, 90.0, -180.0, -90.0]
    for feature in polygons["features"]:
        prop = feature["properties"]
        zone = integer(prop["ZONE_NO"], "polygon ZONE_NO")
        code = str(prop["MUNICIPAL_CODE"])
        if zone in by_zone or code not in expected_names or prop["MUNICIPALITY_NAME_EN"] != expected_names[code]:
            raise ValueError(f"Duplicate zone or municipality mismatch: {zone}, {code}")
        by_zone[zone] = prop
        zone_counts[code] += 1
        for ring in rings(feature["geometry"]):
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError(f"Unclosed/short polygon ring in zone {zone}")
            vertices += len(ring)
            for coordinate in ring:
                if len(coordinate) < 2 or not (-180 <= coordinate[0] <= 180 and -90 <= coordinate[1] <= 90):
                    raise ValueError(f"Invalid geographic coordinate in zone {zone}")
                bounds[0] = min(bounds[0], coordinate[0])
                bounds[1] = min(bounds[1], coordinate[1])
                bounds[2] = max(bounds[2], coordinate[0])
                bounds[3] = max(bounds[3], coordinate[1])
    counts = defaultdict(lambda: [0, 0])
    population_zones = set()
    missing_population_zones = []
    for feature in population["features"]:
        prop = feature["attributes"]
        zone = integer(prop["ZONE_NO"], "population ZONE_NO")
        if zone in population_zones or zone not in by_zone:
            raise ValueError(f"Population zone mismatch or duplicate: {zone}")
        population_zones.add(zone)
        code = str(by_zone[zone]["MUNICIPAL_CODE"])
        male, female = prop["TOTAL_MALE_2020"], prop["TOTAL_FEMALE_2020"]
        if male is None or female is None:
            if male is not None or female is not None:
                raise ValueError(f"Only one 2020 sex count is missing in zone {zone}")
            missing_population_zones.append({"zone_no": zone, "municipal_code": code,
                "status": "source_null_not_zero"})
            continue
        counts[code][0] += integer(male, "2020 male")
        counts[code][1] += integer(female, "2020 female")
    if len(population_zones) != 91 or sorted(counts) != [str(i) for i in range(1, 9)]:
        raise ValueError("Historical zone population coverage incomplete")

    workbook = load_workbook(original, read_only=True, data_only=True)
    table = workbook["1"]
    controls = []
    for code, gis_name, row in EXPECTED:
        census_name = table[f"A{row}"].value
        if gis_name != f"{census_name} Municipality":
            raise ValueError(f"GIS/census municipality label mismatch: code {code}")
        male = integer(table[f"C{row}"].value, "published male")
        female = integer(table[f"B{row}"].value, "published female")
        total = integer(table[f"D{row}"].value, "published total")
        if counts[code] != [male, female] or male + female != total:
            raise ValueError(f"Zone population does not reconcile for municipality {code}")
        controls.append({"municipal_code": code, "gis_name": gis_name, "census_table_1_row": row,
            "zone_count": zone_counts[code], "male_2020": male, "female_2020": female, "total_2020": total})
    if sum(item["total_2020"] for item in controls) != integer(table["D8"].value, "published national total"):
        raise ValueError("National census/zone crosscheck failed")
    if sum(item["zone_count"] for item in controls) != 91:
        raise ValueError("Zone polygons not fully assigned")
    result = {"status": "historical_code_and_zone_crosswalk_verified_one_null_zone_population_geometry_topology_not_yet_audited",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_workbook_sha256": original_receipt["sha256"],
        "geography_manifest": str(args.geography_manifest.resolve().relative_to(project)).replace("\\", "/"),
        "geojson_sha256": geography["census-zone-2020-polygons.geojson"][1]["sha256"],
        "zone_population_sha256": geography["census-zone-population-2020.json"][1]["sha256"],
        "census_zone_features": len(by_zone), "joined_population_rows": len(population_zones),
        "reported_2020_population_rows": len(population_zones) - len(missing_population_zones),
        "missing_2020_population_zones": missing_population_zones,
        "vertices_in_source_rings": vertices, "bbox_lonlat": bounds, "municipalities": controls,
        "planning_note": "QNMP page says eight MSDPs completed; current approval, edition and contents remain unverified.",
        "adoption_note": "Zone 99 has source-null male and female 2020 values; it is not converted to zero. The sums of reported zone values match the eight published municipality controls, but the zone-level series is not adopted. This audit does not modify the country dataset or accept polygon topology, the 2026 administrative edition, or planning documents."}
    destination = project / "evidence/QAT_CENSUS2020_GEOGRAPHY_AUDIT.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"zones": len(by_zone), "missing_population_zones": missing_population_zones,
        "municipalities": controls,
        "national_total": sum(item["total_2020"] for item in controls), "bbox": bounds}, ensure_ascii=False))


if __name__ == "__main__":
    main()

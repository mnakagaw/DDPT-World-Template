"""Dissolve same-edition Census_Zone_2020 polygons for display-only municipalities.

Requires Shapely 2.1.2. Never repairs invalid source shapes, simplifies rings, or
uses geometry to compute legal area or statistical totals.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import explain_validity


CODE_TO_SLUG = {
    "1": "DOHA", "2": "AL-RAYYAN", "3": "AL-WAKRA", "4": "UMM-SLAL",
    "5": "AL-DAAYEN", "6": "AL-KHOR-AND-AL-THAKHIRA", "7": "AL-SHAMAL",
    "8": "AL-SHEEHANIYA",
}


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
    receipt = next(row for row in manifest["receipts"] if row["file"] == "census-zone-2020-polygons.geojson")
    original_path = manifest_path.parent / receipt["file"]
    actual_sha = hashlib.sha256(original_path.read_bytes()).hexdigest()
    if receipt["status"] != "acquired" or actual_sha != receipt["sha256"]:
        raise ValueError("Historical polygon receipt mismatch")
    audit_path = project / "evidence/QAT_CENSUS2020_GEOGRAPHY_AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["geojson_sha256"] != actual_sha or audit["census_zone_features"] != 91:
        raise ValueError("Historical code and population audit is required")
    source = json.loads(original_path.read_text(encoding="utf-8-sig"))
    if source["type"] != "FeatureCollection" or len(source["features"]) != 91:
        raise ValueError("Expected 91 Census_Zone_2020 polygons")

    groups = defaultdict(list)
    seen_zones = set()
    for feature in source["features"]:
        properties = feature["properties"]
        code, zone = str(properties["MUNICIPAL_CODE"]), properties["ZONE_NO"]
        if code not in CODE_TO_SLUG or zone in seen_zones:
            raise ValueError(f"Unexpected municipality code or duplicate zone: {code}, {zone}")
        seen_zones.add(zone)
        geometry = shape(feature["geometry"])
        if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"} or not geometry.is_valid:
            raise ValueError(f"Invalid source polygon zone {zone}: {explain_validity(geometry)}")
        groups[code].append(geometry)
    if len(seen_zones) != 91:
        raise ValueError("Incomplete zone polygons")

    dissolved = {}
    evidence = []
    for code in sorted(CODE_TO_SLUG):
        source_shapes = groups[code]
        result = unary_union(source_shapes)
        if result.is_empty or result.geom_type not in {"Polygon", "MultiPolygon"} or not result.is_valid:
            raise ValueError(f"Invalid dissolved municipality {code}: {explain_validity(result)}")
        source_area = sum(geometry.area for geometry in source_shapes)
        if abs(source_area - result.area) > 1e-9:
            raise ValueError(f"Overlapping or lost source zone geometry for municipality {code}")
        dissolved[code] = result
        evidence.append({"municipal_code": code, "source_zone_count": len(source_shapes),
            "result_polygon_count": len(result.geoms) if result.geom_type == "MultiPolygon" else 1,
            "source_to_dissolved_area_difference_in_coordinate_space": source_area - result.area,
            "valid_geometry": True})
    codes = sorted(dissolved)
    for index, first in enumerate(codes):
        for second in codes[index + 1:]:
            if dissolved[first].intersection(dissolved[second]).area > 1e-9:
                raise ValueError(f"Overlapping municipalities {first} and {second}")

    features = []
    for code in codes:
        features.append({"type": "Feature", "properties": {
            "territory_id": f"QAT:CENSUS2020:MUNICIPALITY:{CODE_TO_SLUG[code]}",
            "source_id": "qat-gis-census-zone-2020",
            "official_code": code,
            "code_system": "Qatar GIS Census_Zone_2020 MUNICIPAL_CODE",
            "boundary_version": "Census_Zone_2020",
            "display_only_dissolve": True,
            "source_zone_count": len(groups[code]),
        }, "geometry": mapping(dissolved[code])})
    output = {"type": "FeatureCollection", "features": features}
    output_path = project / "evidence/QAT_CENSUS2020_MUNICIPAL_BOUNDARIES.geojson"
    output_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    result = {"status": "geometry_topology_pass_display_only_not_yet_adopted",
        "checked_at": datetime.now(timezone.utc).isoformat(), "library": "Shapely 2.1.2",
        "source_geojson_sha256": actual_sha,
        "derived_geojson_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "source_zone_count": len(seen_zones), "derived_municipality_count": len(features),
        "municipalities": evidence,
        "note": "All 91 source polygons validated; same-source, same-edition zones dissolved with no simplification or repair. This is display geometry only. Source reuse terms and any later administrative change remain separate."}
    (project / "evidence/QAT_CENSUS2020_TOPOLOGY_AUDIT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_zones": len(seen_zones), "municipalities": len(features),
        "derived_sha256": result["derived_geojson_sha256"], "details": evidence}, ensure_ascii=False))


if __name__ == "__main__":
    main()

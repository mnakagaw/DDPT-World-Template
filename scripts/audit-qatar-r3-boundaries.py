#!/usr/bin/env python3
"""Compare historical display geometry with current GIS without equating them."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import shape


def digest(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--legal-run", required=True)
parser.add_argument("--gis-run", required=True)
args = parser.parse_args()
project = Path(args.project).resolve(strict=True)
legal_dir = project / "raw/qatar-r3-legal" / args.legal_run
gis_dir = project / "raw/qatar-r3-official-pages" / args.gis_run
legal_manifest = json.loads((legal_dir / "manifest.json").read_text(encoding="utf-8-sig"))
gis_manifest = json.loads((gis_dir / "manifest.json").read_text(encoding="utf-8-sig"))
for directory, manifest in ((legal_dir, legal_manifest), (gis_dir, gis_manifest)):
    for receipt in manifest["receipts"]:
        if receipt["status"] != "acquired" or digest(directory / receipt["file"]) != {
            "sha256": receipt["sha256"], "bytes": receipt["bytes"]
        }:
            raise SystemExit(f"Source receipt mismatch: {directory / receipt['file']}")

historic_path = project / "evidence/QAT_CENSUS2020_MUNICIPAL_BOUNDARIES.geojson"
current_path = gis_dir / "municipality-current-polygons.geojson"
historic = json.loads(historic_path.read_text(encoding="utf-8"))
current = json.loads(current_path.read_text(encoding="utf-8"))
historic_by_code = {int(f["properties"]["official_code"]): f for f in historic["features"]}
current_by_code = {int(f["properties"]["MNCP_NO"]): f for f in current["features"]}
if set(historic_by_code) != set(range(1, 9)) or set(current_by_code) != set(range(1, 9)):
    raise SystemExit("Expected eight historical/current municipality code pairs")
rows = []
for code in range(1, 9):
    old_feature, new_feature = historic_by_code[code], current_by_code[code]
    old_shape, new_shape = shape(old_feature["geometry"]), shape(new_feature["geometry"])
    if not old_shape.is_valid or not new_shape.is_valid:
        raise SystemExit(f"Invalid geometry for municipality {code}")
    rows.append({
        "official_code": str(code),
        "census_2020_territory_id": old_feature["properties"]["territory_id"],
        "current_gis_name": new_feature["properties"]["ENAME"],
        "historic_source_zone_count": old_feature["properties"]["source_zone_count"],
        "symmetric_difference_fraction_of_union_in_lonlat_coordinates": round(
            old_shape.symmetric_difference(new_shape).area / old_shape.union(new_shape).area, 9),
        "same_shape": old_shape.equals(new_shape),
        "current_gis_startdate_field": new_feature["properties"].get("STARTDATE"),
        "startdate_interpretation": "GIS feature metadata only; legal effective date unverified",
    })

attachment_sources = []
for filename, source_url, kind in (
    ("resolution-109-2024-gazette-attachment.pdf", "https://almeezan.qa/ClarificationsNoteDetails.aspx?id=19975&language=ar", "gazette_page_219"),
    ("resolution-109-2024-map-attachment.jpg", "https://almeezan.qa/ClarificationsNoteDetails.aspx?id=20065&language=ar", "map_and_coordinate_image"),
):
    path = legal_dir / filename
    raw = path.read_bytes()
    expected = b"%PDF-" if filename.endswith(".pdf") else b"\xff\xd8\xff"
    if not raw.startswith(expected):
        raise SystemExit(f"Unexpected attachment signature: {path}")
    attachment_sources.append({"url": source_url, "file": str(path.relative_to(project)).replace("\\", "/"),
                               "kind": kind, "http_status": 200, **digest(path)})

result = {
    "audited_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "historical_vs_current_geography_not_equivalent",
    "historic_geometry": {"file": str(historic_path.relative_to(project)).replace("\\", "/"),
                          "boundary_version": "Census_Zone_2020", "purpose": "display_only_dissolve", **digest(historic_path)},
    "current_gis_geometry": {"file": str(current_path.relative_to(project)).replace("\\", "/"),
                             "layer_url": "https://services.gisqatar.org.qa/server/rest/services/Vector/MunicipalityAT/MapServer/0",
                             **digest(current_path)},
    "legal_change": {
        "resolution": "Qatar Minister of Municipality Resolution 109 of 2024, amending Resolution 68 of 2011",
        "legal_portal_url": "https://almeezan.qa/LawPage.aspx?id=9617&language=ar",
        "effective_date_reported_in_article_3": "2024-05-30",
        "gazette_issue_date": "2024-07-10",
        "article_1_scope": "Al Wakra Municipality geographical boundary according to attached map and coordinates",
        "source_attachment_links": attachment_sources,
        "map_machine_georeferenced": False,
        "current_gis_matches_legal_annex": "unverified",
        "review_method": "Original official Gazette page and attached map inspected visually; no legal geometry constructed from image",
    },
    "comparison_method": "Shapely polygon symmetric difference / union in longitude-latitude coordinates; dimensionless diagnostic, not geodesic area or attribution of cause",
    "municipalities": rows,
    "adoption_rule": "Keep Census 2020 values on their dated census municipality geography; do not transfer them to current legal polygons or reinterpret GIS STARTDATE as legal effect without an official crosswalk and annex verification",
}
out = project / "evidence/QAT_R3_BOUNDARY_RECONCILIATION.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"municipalities": len(rows), "al_wakra_difference_fraction": rows[2]["symmetric_difference_fraction_of_union_in_lonlat_coordinates"],
                  "legal_attachments": len(attachment_sources)}, ensure_ascii=False))

#!/usr/bin/env python3
"""Acquire and normalize Belize ministry-attributed district boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


SERVICE = "https://services3.arcgis.com/UIDEa9S9iqq5orpE/ArcGIS/rest/services/Bze_Districts/FeatureServer/0"
DISTRICT_IDS = {"Corozal": 1, "Orange Walk": 2, "Belize": 3, "Cayo": 4, "Stann Creek": 5, "Toledo": 6}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    raw_dir = project / "raw/discovered-source-files/BLZ"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "district-boundaries-ministry-natural-resources-wgs84.geojson"
    metadata_path = raw_dir / "district-boundaries-ministry-natural-resources-metadata.json"
    query = SERVICE + "/query"
    response = requests.get(query, params={"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}, timeout=120)
    response.raise_for_status()
    raw_path.write_bytes(response.content)
    metadata_response = requests.get(SERVICE, params={"f": "json"}, timeout=60)
    metadata_response.raise_for_status()
    metadata_path.write_bytes(metadata_response.content)
    raw = response.json()
    groups = {name: [] for name in DISTRICT_IDS}
    codes = {}
    for feature in raw.get("features", []):
        name = feature.get("properties", {}).get("ADM1_NAME")
        if name not in groups:
            raise ValueError(f"Unexpected district: {name}")
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            groups[name].append(geometry["coordinates"])
        elif geometry["type"] == "MultiPolygon":
            groups[name].extend(geometry["coordinates"])
        else:
            raise ValueError(f"Unexpected geometry type: {geometry['type']}")
        codes[name] = feature["properties"].get("ADM1_CODE")
    features = []
    for name, district_number in DISTRICT_IDS.items():
        if not groups[name]:
            raise ValueError(f"Missing district geometry: {name}")
        features.append({
            "type": "Feature",
            "properties": {
                "territory_id": f"BLZ:C2022:DIST:{district_number}",
                "source_id": "BLZ_MNR_DISTRICT_BOUNDARIES",
                "geometry_edition": "Belize Ministry of Natural Resources attributed ArcGIS FeatureServer; retrieved 2026-09-18",
                "reference_only": True,
                "join_method": f"Exact published district name matched to SIB 2022 Census district; provider code {codes[name]}",
                "provider_code": codes[name],
                "provider_layer": "Bze_Districts/FeatureServer/0",
            },
            "geometry": {"type": "MultiPolygon", "coordinates": groups[name]},
        })
    metadata = metadata_response.json()
    now = datetime.now(timezone.utc).isoformat()
    bundle = {
        "schema_version": "1.0",
        "generated_at": now,
        "country_area_id": "BLZ",
        "source": {
            "id": "BLZ_MNR_DISTRICT_BOUNDARIES",
            "name": "Belize district boundaries",
            "publisher": "Ministry of Natural Resources, Belize",
            "url": SERVICE,
            "status": "ready",
            "retrieved_at": now,
            "reference_period": "Provider layer edition not stated; retrieved 2026-09-18",
            "license": "Reuse terms not stated in the service metadata; used for attributed reference display.",
            "geographic_level": "district",
            "note": "Six districts dissolved from 287 mainland and island polygon parts, transformed by ArcGIS to EPSG:4326 and matched to Census geography by exact district name.",
            "copyright_text": metadata.get("copyrightText") or "Ministry of Natural Resources, Belize",
        },
        "feature_count": len(features),
        "features": features,
        "territory_updates": [
            {
                "id": f"BLZ:C2022:DIST:{district_number}",
                "official_code": codes[name],
                "code_system": "Ministry of Natural Resources ADM1_CODE",
                "boundary_version": "Bze_Districts FeatureServer retrieved 2026-09-18",
                "source_id": "BLZ_C2022_GENERAL_CHARACTERISTICS",
                "geography_note": "SIB 2022 Census district name matched exactly to the Ministry of Natural Resources district layer and its ADM1_CODE.",
            }
            for name, district_number in DISTRICT_IDS.items()
        ],
        "receipts": [{
            "url": response.url,
            "path": raw_path.relative_to(project).as_posix(),
            "sha256": hashlib.sha256(response.content).hexdigest(),
            "bytes": len(response.content),
            "source_feature_count": len(raw.get("features", [])),
            "normalized_feature_count": len(features),
            "status": "acquired_dissolved_and_name_matched",
        }],
    }
    output = project / "evidence/BLZ_BOUNDARY_BUNDLE.json"
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_features": len(raw.get("features", [])), "features": len(features), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

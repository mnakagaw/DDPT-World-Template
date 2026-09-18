#!/usr/bin/env python3
"""Normalize official SEGEPLAN Guatemala department and municipality WFS layers."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    raw_root = project / "raw/discovered-source-files/GTM"
    layers = [
        {
            "level": "department",
            "path": raw_root / "department-boundaries-segeplan-wgs84.geojson",
            "url": "https://ideg.segeplan.gob.gt/geoserver/agrip/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=agrip:03_Limites_departamentales&outputFormat=application/json&srsName=EPSG:4326",
            "code": "cod_dep",
            "id": lambda value: f"GTM:C2018:DEP:{int(value)}",
        },
        {
            "level": "municipality",
            "path": raw_root / "municipal-boundaries-segeplan-wgs84.geojson",
            "url": "https://ideg.segeplan.gob.gt/geoserver/agrip/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=agrip:04_Limites_municipales_340&outputFormat=application/json&srsName=EPSG:4326",
            "code": "codigo_mun",
            "id": lambda value: f"GTM:C2018:MUN:{int(value)}",
        },
    ]
    features, receipts = [], []
    for layer in layers:
        data = json.loads(layer["path"].read_text(encoding="utf-8"))
        if data.get("crs", {}).get("properties", {}).get("name") != "urn:ogc:def:crs:EPSG::4326":
            raise ValueError(f"Layer is not EPSG:4326: {layer['path']}")
        seen = set()
        for source in data["features"]:
            territory_id = layer["id"](source["properties"][layer["code"]])
            if territory_id in seen:
                raise ValueError(f"Duplicate boundary code: {territory_id}")
            seen.add(territory_id)
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "territory_id": territory_id,
                        "source_id": "GTM_SEGEPLAN_ADMIN_BOUNDARIES",
                        "geometry_edition": "SEGEPLAN GeoServer layer retrieved 2026-09-18",
                        "reference_only": True,
                        "join_method": f"Exact official numeric {layer['code']} matched to the INE 2018 Census code",
                        "provider_layer": "agrip:03_Limites_departamentales" if layer["level"] == "department" else "agrip:04_Limites_municipales_340",
                    },
                    "geometry": source["geometry"],
                }
            )
        expected = 22 if layer["level"] == "department" else 340
        if len(seen) != expected:
            raise ValueError(f"{layer['level']} feature count {len(seen)} != {expected}")
        receipts.append({"level": layer["level"], "url": layer["url"], "path": layer["path"].relative_to(project).as_posix(), "sha256": digest(layer["path"]), "bytes": layer["path"].stat().st_size, "feature_count": len(seen), "status": "acquired_and_code_matched"})
    bundle = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "country_area_id": "GTM",
        "source": {
            "id": "GTM_SEGEPLAN_ADMIN_BOUNDARIES",
            "name": "Guatemala department and municipality boundaries",
            "publisher": "Secretaría de Planificación y Programación de la Presidencia (SEGEPLAN)",
            "url": "https://ideg.segeplan.gob.gt/geoserver/gwc/demo",
            "status": "ready",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "reference_period": "SEGEPLAN published layers; municipal alternative layer identifies IGN 2021",
            "license": "Reuse terms not stated in the WFS response; geometry is used for attributed reference display and excluded from the public package until terms review.",
            "geographic_level": "department and municipality",
            "raw_files": receipts,
            "note": "22 departments and 340 municipalities. Geometry is transformed by GeoServer to EPSG:4326 and joined by exact numeric Census geography codes, not names.",
        },
        "feature_count": len(features),
        "features": features,
        "receipts": receipts,
    }
    output = project / "evidence/GTM_BOUNDARY_BUNDLE.json"
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"features": len(features), "receipts": len(receipts), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

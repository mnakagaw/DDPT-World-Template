#!/usr/bin/env python3
"""Archive the public Armenia geoportal map leads without adopting polygons.

The official site is copyright-protected. Saved map bytes stay in the ignored
country candidate for source review; no geometry is committed or displayed.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
RAW = PROJECT / "raw" / "geoportal"
EVIDENCE = PROJECT / "evidence"
MAP_URL = "https://geoportal.am/map_geoportal"
MAX_BYTES = 10_000_000


def acquire(url: str, name: str) -> dict:
    response = requests.get(url, timeout=45)
    if len(response.content) > MAX_BYTES:
        raise ValueError(f"Geoportal response too large: {url}")
    path = RAW / name
    path.write_bytes(response.content)
    return {"url": response.url, "http_status": response.status_code,
            "content_type": response.headers.get("content-type"), "last_modified": response.headers.get("last-modified"),
            "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(),
            "path": str(path.relative_to(PROJECT)).replace("\\", "/"),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    receipts = [acquire(MAP_URL, "map_geoportal.html")]
    if receipts[0]["http_status"] != 200:
        raise ValueError("Official map page unavailable")
    page = (RAW / "map_geoportal.html").read_text(encoding="utf-8")
    script_match = re.search(r"https://geoportal\.am/openlayers/js/main_free_mix\.js\?ver=[0-9.]+", page)
    if not script_match:
        raise ValueError("Map script link changed; inspect page")
    receipts.append(acquire(script_match.group(), "main_free_mix.js"))
    script = (RAW / "main_free_mix.js").read_text(encoding="utf-8")
    for name in ("marzer.geojson", "community_settlement.geojson"):
        if f"/openlayers/data/{name}" not in script:
            raise ValueError(f"Referenced layer changed: {name}")
        receipts.append(acquire(urljoin(MAP_URL, f"/openlayers/data/{name}"), name))
    marz_receipt = next(row for row in receipts if row["path"].endswith("marzer.geojson"))
    if marz_receipt["http_status"] != 200:
        raise ValueError("Referenced marz layer unavailable")
    data = json.loads((RAW / "marzer.geojson").read_text(encoding="utf-8"))
    features = data.get("features", [])
    inventory = {"source_page": MAP_URL, "source_script": script_match.group(),
                 "as_of_utc": datetime.now(timezone.utc).isoformat(),
                 "marz_geojson_status": marz_receipt["http_status"], "marz_feature_count": len(features),
                 "marz_crs": data.get("crs"),
                 "marz_property_keys": sorted({key for feature in features for key in feature.get("properties", {})}),
                 "marz_names": [feature.get("properties", {}).get("Province_N") for feature in features],
                 "marz_has_feature_ids": any(feature.get("id") for feature in features),
                 "community_endpoint_status": next(row["http_status"] for row in receipts if row["path"].endswith("community_settlement.geojson")),
                 "disposition": "source_location_inspected_no_polygons_adopted",
                 "reason": "The referenced marz file has no official classifier code/validity metadata; the referenced settlement endpoint returned 404. Source rights and community boundary edition are unverified. Name similarity cannot establish a legal/dated join."}
    (EVIDENCE / "ARM_GEOPORTAL_RECEIPTS.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "ARM_GEOPORTAL_LAYER_INVENTORY.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"marz_features": len(features), "marz_properties": inventory["marz_property_keys"],
                      "community_endpoint_status": inventory["community_endpoint_status"],
                      "polygons_adopted": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

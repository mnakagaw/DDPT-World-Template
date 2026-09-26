"""Inventory the NCSI/MOI wilayat map register without adopting its polygons."""

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import requests


URL = "https://ncsigeostatportal.ncsi.gov.om/server/rest/services/NCSIData/WilayatB/FeatureServer/3"
ROOT = "raw/oman-ecensus-moi/"
MOI_HASH = "63225e0a09ad41a41d5bd3b98b506e9117defdd67b8a7bbc0770ed686c63419b"


def arabic_key(value):
    value = re.sub(r"^(?:محافظة|ولاية)\s+", "", value.strip()).replace("ـ", "")
    value = re.sub(r"[\u064b-\u065f]", "", value)
    value = value.translate(str.maketrans("أإآىةؤئ", "ااايهوي"))
    return "".join(char for char in value if char.isalnum())


def acquire(session, project, name, url, params):
    response = session.get(url, params=params, timeout=50)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(f"Official ArcGIS service rejected {name}: {data['error']}")
    relative = ROOT + name
    body = response.content
    (project / relative).write_bytes(body)
    receipt = {"source_url": url, "request_params": params, "final_url": response.url,
               "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
               "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
               "raw_path": relative, "status": "acquired", "redistribution_terms": "review_required",
               "method": "GET"}
    (project / (relative + ".receipt.json")).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data, receipt


def date(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc).date().isoformat() if value else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    moi_path = project / (ROOT + "moi-governorate-wilayat-2025.xlsx")
    if hashlib.sha256(moi_path.read_bytes()).hexdigest() != MOI_HASH:
        raise ValueError("Ministry of Interior directory version changed")
    book = openpyxl.load_workbook(moi_path, read_only=True, data_only=True)
    moi_rows = list(book["الولايات"].values)[1:]
    book.close()
    moi_names = {arabic_key(row[1]): row for row in moi_rows}
    if len(moi_names) != 63:
        raise ValueError("MOI Arabic wilayat names are not unique")
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData source-audit/1.0"})
    metadata, metadata_receipt = acquire(session, project, "ncsi-wilayat-layer-metadata.json", URL, {"f": "json"})
    register, register_receipt = acquire(session, project, "ncsi-wilayat-attributes.json", URL + "/query",
        {"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json"})
    rows = [feature["attributes"] for feature in register.get("features", [])]
    fields = {field["name"] for field in metadata.get("fields", [])}
    required = {"NSDIFID", "NAMEAR", "NAMEEN", "FEATURELOADDATE", "FEATUREUPDATEDATE",
                "WilayaID", "GovernorateID"}
    if not required.issubset(fields) or len(rows) != 63 or register.get("exceededTransferLimit"):
        raise ValueError("NCSI wilayat register structure or coverage changed")
    ncsi_names = {arabic_key(row["NAMEAR"]): row for row in rows}
    if len(ncsi_names) != 63:
        raise ValueError("NCSI Arabic wilayat names are not unique")
    matched = sorted(set(moi_names) & set(ncsi_names))
    crosswalk = [{"name_key": key, "moi_wilayat_id": moi_names[key][0],
                  "moi_region_id": moi_names[key][3], "ncsi_wilaya_id": ncsi_names[key]["WilayaID"],
                  "ncsi_governorate_id": ncsi_names[key]["GovernorateID"],
                  "ncsi_nsdifid": ncsi_names[key]["NSDIFID"],
                  "ncsi_feature_load_date": date(ncsi_names[key]["FEATURELOADDATE"]),
                  "ncsi_feature_update_date": date(ncsi_names[key]["FEATUREUPDATEDATE"])}
                 for key in matched]
    audit = {"status": "official_map_attribute_register_only_no_polygon_or_2020_boundary_adoption",
             "checked_at": datetime.now(timezone.utc).isoformat(), "layer_url": URL,
             "metadata_receipt_sha256": metadata_receipt["sha256"],
             "attributes_receipt_sha256": register_receipt["sha256"],
             "metadata_fields": sorted(fields), "ncsi_rows": len(rows), "moi_rows": len(moi_rows),
             "arabic_name_matches": len(matched),
             "moi_only": [moi_names[key][1] for key in sorted(set(moi_names) - set(ncsi_names))],
             "ncsi_only": [ncsi_names[key]["NAMEAR"] for key in sorted(set(ncsi_names) - set(moi_names))],
             "feature_load_dates": dict(Counter(str(date(row["FEATURELOADDATE"])) for row in rows)),
             "feature_update_dates": dict(Counter(str(date(row["FEATUREUPDATEDATE"])) for row in rows)),
             "different_code_systems": "NCSI WilayaID/NSDIFID differ from MOI workbook WilayatId; Arabic name matches do not establish 2020 legal code or polygon equivalence",
             "matched_records": crosswalk}
    (project / "evidence/OMN_NCSI_WILAYAT_REGISTER_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ncsi_rows": len(rows), "moi_rows": len(moi_rows), "arabic_matches": len(matched),
                      "moi_only": audit["moi_only"], "ncsi_only": audit["ncsi_only"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

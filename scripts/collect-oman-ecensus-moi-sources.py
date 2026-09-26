"""Acquire Oman eCensus pivot originals and the 2025 Ministry of Interior hierarchy."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


MOI_CATALOGUE = "https://opendata.gov.om/en/datasets/9d822347-6816-4166-96d9-8ead92974fa0"
MOI_XLSX = "https://opendata.gov.om/api/v1/datasets/file/f2e16edb-a795-49d8-8a3c-a6dd72d17b0d/1"
METADATA = "https://www.ecensus.gov.om/dregndrop-api/v1/datasets/table-metadata?table=v_public_ds_population_en&lang=en"
AR_METADATA = "https://www.ecensus.gov.om/dregndrop-api/v1/datasets/table-metadata?table=v_public_ds_population_ar&lang=ar"
PIVOT = "https://www.ecensus.gov.om/dregndrop-api/v1/datasets/pivot-query?lang=en"
AR_PIVOT = "https://www.ecensus.gov.om/dregndrop-api/v1/datasets/pivot-query?lang=ar"
TABLE = "v_public_ds_population_en"


def pivot_body(rows):
    return {"table": TABLE, "layout": {"rows": rows, "columns": ["RUN_DATE"],
        "measures": [{"field": "AMOUNT", "type": "sum", "name": "Amount"}]}, "filters": []}


def arabic_wilayat_body():
    return {"table": "v_public_ds_population_ar", "layout": {
        "rows": ["الجنسية - عماني أو وافد", "الموقع حسب المحافظة", "الموقع حسب الولاية"],
        "columns": ["التاريخ المرجعي"],
        "measures": [{"field": "المجموع", "type": "sum", "name": "المجموع"}]},
        "filters": []}


def acquire(session, project, name, url, body=None):
    relative = "raw/oman-ecensus-moi/" + name
    target = project / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    response = session.get(url, timeout=50) if body is None else session.post(url, json=body, timeout=50)
    response.raise_for_status()
    content = response.content
    if not content or (name.endswith(".xlsx") and content[:2] != b"PK"):
        raise ValueError(f"Expected nonempty source original: {name}")
    target.write_bytes(content)
    receipt = {"source_url": url, "final_url": response.url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
               "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(), "raw_path": relative,
               "status": "acquired", "redistribution_terms": "review_required",
               **({"method": "POST", "request_body": body} if body is not None else {"method": "GET"})}
    (project / (relative + ".receipt.json")).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData source-audit/1.0", "Accept": "application/json, text/html, */*"})
    originals = [
        ("moi-governorate-wilayat-catalogue.html", MOI_CATALOGUE, None),
        ("moi-governorate-wilayat-2025.xlsx", MOI_XLSX, None),
        ("ecensus-population-metadata.json", METADATA, None),
        ("ecensus-population-arabic-metadata.json", AR_METADATA, None),
        ("ecensus-population-national-pivot.json", PIVOT, pivot_body(["RESIDENTIAL_STATUS"])),
        ("ecensus-population-governorate-pivot.json", PIVOT, pivot_body(["RESIDENTIAL_STATUS", "LOCATION_GOVERNORATE"])),
        ("ecensus-population-wilayat-pivot.json", PIVOT, pivot_body(["RESIDENTIAL_STATUS", "LOCATION_GOVERNORATE", "LOCATION_WILAYAT"])),
        ("ecensus-population-arabic-wilayat-pivot.json", AR_PIVOT, arabic_wilayat_body()),
    ]
    receipts = []
    for name, url, body in originals:
        receipts.append(acquire(session, project, name, url, body))
    (project / "evidence/OMN_ACQUISITION_SUMMARY.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({"acquired": len(receipts), "bytes": sum(item["bytes"] for item in receipts),
                      "pivots": 4, "moi_sha256": receipts[1]["sha256"]}))


if __name__ == "__main__":
    main()

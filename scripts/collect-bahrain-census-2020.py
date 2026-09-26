"""Receipt the Bahrain official open-data Census 2020 catalogue and all 45 tables.

This inventory acquires data but does not adopt an indicator or settle geography.
"""

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE = "https://www.data.gov.bh/api/explore/v2.1/catalog/datasets"
RAW = "raw/bahrain-census-2020"


def acquire(session, project, name, url, params):
    destination = project / RAW / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            response = session.get(url, params=params, timeout=50)
            response.raise_for_status()
            if "json" not in response.headers.get("Content-Type", "").lower():
                raise ValueError(f"Non-JSON Bahrain official response: {response.url}")
            payload = response.json()
            destination.write_bytes(response.content)
            receipt = {"status": "acquired", "source_url": response.url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type"), "bytes": len(response.content),
                "sha256": hashlib.sha256(response.content).hexdigest(),
                "raw_path": f"{RAW}/{name}", "redistribution_terms": "official_portal_terms_review_required"}
            (project / RAW / (name + ".receipt.json")).write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return payload, receipt
        except (requests.RequestException, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData official-source-audit/1.0", "Accept": "application/json"})
    catalogue = []
    offset = 0
    while True:
        payload, _ = acquire(session, project, f"catalogue-{offset:03d}.json", BASE,
                             {"search": "Census 2020", "limit": 100, "offset": offset})
        catalogue.extend(payload["results"])
        if len(catalogue) >= payload["total_count"]:
            break
        offset += 100
    selected = []
    for item in catalogue:
        title = item.get("metas", {}).get("default", {}).get("title_en") or ""
        if "Census 2020" in title:
            selected.append(item)
    selected.sort(key=lambda item: item["dataset_id"])
    if len(selected) != 45 or len({item["dataset_id"] for item in selected}) != 45:
        raise ValueError(f"Expected 45 unique titled Census 2020 tables, got {len(selected)}")
    inventory = []
    for index, item in enumerate(selected, 1):
        dataset_id = item["dataset_id"]
        meta = item["metas"]["default"]
        expected = meta["records_count"]
        if not item["has_records"] or not isinstance(expected, int) or expected < 1:
            raise ValueError(f"No record count for {dataset_id}")
        fields = [{"name": field["name"], "type": field["type"], "label": field.get("label")}
                  for field in item["fields"]]
        pages = []
        records = []
        for page in range(math.ceil(expected / 100)):
            off = page * 100
            data, receipt = acquire(session, project, f"records-{dataset_id}-{off:03d}.json",
                                    f"{BASE}/{dataset_id}/records", {"limit": 100, "offset": off})
            if data["total_count"] != expected:
                raise ValueError(f"Changing official record count: {dataset_id}")
            records.extend(data["results"])
            pages.append({"offset": off, "row_count": len(data["results"]),
                          "sha256": receipt["sha256"], "raw_path": receipt["raw_path"]})
        if len(records) != expected:
            raise ValueError(f"Missing records: {dataset_id} {len(records)}/{expected}")
        inventory.append({"dataset_id": dataset_id, "title": meta["title_en"],
            "publisher": meta.get("publisher_en") or meta.get("publisher"),
            "data_processed": meta.get("data_processed"), "metadata_processed": meta.get("metadata_processed"),
            "portal_license": meta.get("license"), "record_count": expected,
            "fields": fields, "numeric_fields": [field["name"] for field in fields
                                                  if field["type"] in ("int", "double", "decimal")],
            "pages": pages, "decision": "acquired_values_unassessed"})
        if index % 10 == 0 or index == len(selected):
            print(f"Acquired {index}/{len(selected)} Census 2020 tables", flush=True)
    audit = {"status": "full_portal_census_2020_catalogue_acquired_values_unassessed",
             "catalogue_search": "Census 2020", "catalogue_results": len(catalogue),
             "census_2020_title_count": len(selected), "tables": inventory,
             "limits": ["No records adopted by this collector", "Portal record values require semantic and geography audit",
                        "2020 census and annual 2020 demographic tables may use different source frames"]}
    (project / "evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalogue_results": len(catalogue), "tables": len(selected),
                      "records": sum(item["record_count"] for item in inventory),
                      "numeric_fields": sum(len(item["numeric_fields"]) for item in inventory)}))


if __name__ == "__main__":
    main()

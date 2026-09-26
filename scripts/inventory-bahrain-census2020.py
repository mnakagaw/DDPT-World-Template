"""Acquire and mechanically inventory Bahrain's 45 official 2020 census datasets.

This does not adopt any numeric field. The raw API pages and detailed inventory
remain in the ignored Bahrain project. Existing raw pages are never overwritten.
"""

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


API = "https://www.data.gov.bh/api/explore/v2.1/catalog/datasets"
CATALOG_URL = API + "?limit=100&refine=theme%3ACensus"
LIMIT = 100


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def get_raw(url, path):
    if path.exists():
        raw = path.read_bytes()
    else:
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.4 official-source-audit"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status} for {url}")
                    raw = response.read()
                break
            except (TimeoutError, urllib.error.URLError):
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
        json.loads(raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return raw, json.loads(raw)


def inspect_dataset(project, metadata):
    dataset_id = metadata["dataset_id"]
    if not re.fullmatch(r"[a-z0-9-]+", dataset_id):
        raise ValueError(f"Unsafe dataset ID: {dataset_id}")
    expected_count = metadata["metas"]["default"].get("records_count")
    pages = []
    records = []
    offset = 0
    while True:
        url = f"{API}/{dataset_id}/records?limit={LIMIT}&offset={offset}"
        path = project / "raw/bahrain-open-data/census-pages" / dataset_id / f"offset-{offset:06d}.json"
        raw, response = get_raw(url, path)
        if offset == 0:
            total = response["total_count"]
        elif response["total_count"] != total:
            raise ValueError(f"API total changed during collection for {dataset_id}")
        page = response["results"]
        pages.append({"url": url, "path": path.relative_to(project).as_posix(),
                      "sha256": sha(raw), "bytes": len(raw), "records": len(page)})
        records.extend(page)
        offset += len(page)
        if not page or offset >= total:
            break
    if len(records) != total or expected_count != total:
        raise ValueError(f"Count mismatch {dataset_id}: catalog {expected_count}, API {total}, rows {len(records)}")
    fields = []
    for field in metadata["fields"]:
        name = field["name"]
        numeric = sum(isinstance(row.get(name), (int, float)) and not isinstance(row.get(name), bool)
                      for row in records)
        fields.append({"name": name, "label": field.get("label"), "type": field.get("type"),
                       "nonempty_cells": sum(row.get(name) not in (None, "") for row in records),
                       "numeric_cells": numeric,
                       "disposition": "semantic_assessment_pending" if numeric else "dimension_or_text_unassessed"})
    unknown = sorted(set().union(*(row.keys() for row in records)) - {field["name"] for field in fields})
    if unknown:
        raise ValueError(f"Unlisted API fields for {dataset_id}: {unknown}")
    if len({json.dumps(row, sort_keys=True, ensure_ascii=False) for row in records}) != total:
        raise ValueError(f"Duplicate record or unstable pages for {dataset_id}")
    governorates = sorted(set(row.get("governorate") for row in records if row.get("governorate")))
    return {"id": dataset_id, "title": metadata["metas"]["default"]["title"],
            "publisher": metadata["metas"]["default"].get("publisher"),
            "data_processed": metadata["metas"]["default"].get("data_processed"),
            "metadata_processed": metadata["metas"]["default"].get("metadata_processed"),
            "license": metadata["metas"]["default"].get("license"),
            "page_url": f"https://www.data.gov.bh/explore/dataset/{dataset_id}/",
            "record_count": total, "governorate_values": governorates,
            "fields": fields, "pages": pages,
            "numeric_columns": sum(bool(field["numeric_cells"]) for field in fields),
            "numeric_cells": sum(field["numeric_cells"] for field in fields)}


def main(project):
    catalog_path = project / "raw/bahrain-open-data/census-catalog-api.json"
    catalog_raw, catalog = get_raw(CATALOG_URL, catalog_path)
    if catalog["total_count"] != 45 or len(catalog["results"]) != 45:
        raise ValueError(f"Census catalogue count changed: {catalog['total_count']}")
    metadata = catalog["results"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(inspect_dataset, project, item): item["dataset_id"] for item in metadata}
        datasets = []
        for future in as_completed(futures):
            datasets.append(future.result())
    datasets.sort(key=lambda row: row["id"])
    total_records = sum(item["record_count"] for item in datasets)
    totals = {"datasets": len(datasets), "records": total_records,
              "numeric_columns": sum(item["numeric_columns"] for item in datasets),
              "numeric_cells": sum(item["numeric_cells"] for item in datasets),
              "governorate_datasets": sum(bool(item["governorate_values"]) for item in datasets)}
    result = {"inventoried_at": datetime.now(timezone.utc).isoformat(),
              "catalog_url": CATALOG_URL, "catalog_path": catalog_path.relative_to(project).as_posix(),
              "catalog_sha256": sha(catalog_raw),
              "scope": "All 45 data.gov.bh Census-theme datasets; every field inventoried mechanically, none adopted by this script.",
              "totals": totals, "datasets": datasets}
    output = project / "evidence/BHR_CENSUS2020_SOURCE_INVENTORY.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

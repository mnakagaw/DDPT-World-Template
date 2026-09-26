"""Archive the official CYSTAT 2021 census API catalogue and priority complete tables.

This is a mechanical inventory. It does not promote any source cell to an
AreaData observation or map 2021 statistical municipalities to 2024 councils.
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


API_ROOT = "https://cystatdb.cystat.gov.cy/api/v1/en/8.CYSTAT-DB"
BASE_PARTS = ("Population", "Census of Population and Housing 2021")
SELECTED = ("1891108E.px", "1891161E.px", "1891164E.px", "1891213E.px",
            "1891515E.px", "1891712E.px", "1895114E.px")
UA = "AreaData/0.4 official-source-inventory"


def raw_hash(raw):
    return hashlib.sha256(raw).hexdigest()


def url_for(parts):
    return API_ROOT + "/" + "/".join(urllib.parse.quote(part, safe="") for part in parts)


def fetch(url, destination, payload=None):
    if destination.exists():
        raw = destination.read_bytes()
    else:
        headers = {"User-Agent": UA}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=payload, headers=headers,
                                         method="POST" if payload is not None else "GET")
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status}: {url}")
                    raw = response.read()
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 4:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = max(8 * (attempt + 1), int(retry_after)) if retry_after and retry_after.isdigit() else 8 * (attempt + 1)
                time.sleep(delay)
            except (TimeoutError, urllib.error.URLError):
                if attempt == 4:
                    raise
                time.sleep(attempt + 1)
        json.loads(raw)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    return raw, json.loads(raw)


def place(project, kind, url):
    return project / "raw/cystat" / kind / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.json"


def main(project):
    root = project / "raw/cystat"
    project.mkdir(parents=True, exist_ok=True)
    pending = [BASE_PARTS]
    seen = set()
    listings = []
    tables = []
    while pending:
        parts = pending.pop()
        if parts in seen:
            continue
        seen.add(parts)
        url = url_for(parts)
        path = place(project, "catalog", url)
        raw, nodes = fetch(url, path)
        if not isinstance(nodes, list):
            raise ValueError(f"Expected PxWeb directory listing: {url}")
        listings.append({"path": list(parts), "url": url,
                         "raw_path": path.relative_to(project).as_posix(),
                         "sha256": raw_hash(raw), "entries": len(nodes)})
        for node in nodes:
            if node.get("type") == "l":
                pending.append((*parts, node["id"]))
            elif node.get("type") == "t":
                tables.append({"id": node["id"], "path": [*parts, node["id"]],
                               "title_in_catalog": node.get("text")})
            else:
                raise ValueError(f"Unknown PxWeb node type: {node}")
    if len({tuple(row["path"]) for row in tables}) != len(tables):
        raise ValueError("Duplicate census table path")
    if set(SELECTED) - {row["id"] for row in tables}:
        raise ValueError("Selected census table disappeared from official catalogue")

    def metadata(row):
        url = url_for(row["path"])
        path = place(project, "metadata", url)
        raw, body = fetch(url, path)
        variables = body.get("variables")
        if not isinstance(variables, list):
            raise ValueError(f"No variable metadata for {row['id']}")
        return {**row, "url": url, "title": body.get("title"),
                "raw_path": path.relative_to(project).as_posix(),
                "sha256": raw_hash(raw),
                "variables": [{"code": value["code"], "label": value.get("text"),
                               "value_count": len(value["values"])} for value in variables]}, body

    details = []
    metadata_by_id = {}
    for catalog_row in tables:
        if catalog_row["id"] in SELECTED:
            time.sleep(1)
            row, body = metadata(catalog_row)
            if row["id"] in metadata_by_id:
                raise ValueError(f"Ambiguous selected table ID: {row['id']}")
            metadata_by_id[row["id"]] = body
        else:
            row = {**catalog_row, "url": url_for(catalog_row["path"]),
                   "disposition": "official_location_identified_not_acquired"}
        details.append(row)
    details.sort(key=lambda row: row["path"])

    selected = []
    for table_id in SELECTED:
        row = next(item for item in details if item["id"] == table_id)
        variables = metadata_by_id[table_id]["variables"]
        query = {"query": [{"code": variable["code"], "selection":
                            {"filter": "item", "values": variable["values"]}}
                           for variable in variables], "response": {"format": "json-stat2"}}
        request_bytes = json.dumps(query, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        url = row["url"]
        result_path = root / f"{table_id[:-3]}-complete.json"
        request_path = root / f"{table_id[:-3]}-request.json"
        if request_path.exists() and request_path.read_bytes() != request_bytes:
            raise ValueError(f"Saved request changed: {table_id}")
        request_path.write_bytes(request_bytes)
        time.sleep(1)
        raw, body = fetch(url, result_path, request_bytes)
        dims = [len(variable["values"]) for variable in variables]
        if body.get("size") != dims or body.get("id") != [variable["code"] for variable in variables]:
            raise ValueError(f"PxWeb response dimensions differ: {table_id}")
        values = body.get("value")
        total = 1
        for size in dims:
            total *= size
        if not isinstance(values, list) or len(values) != total:
            raise ValueError(f"PxWeb response cells incomplete: {table_id}")
        numeric = sum(isinstance(value, (int, float)) and not isinstance(value, bool)
                      for value in values)
        selected.append({"id": table_id, "url": url, "request_path": request_path.relative_to(project).as_posix(),
                         "request_sha256": raw_hash(request_bytes),
                         "raw_path": result_path.relative_to(project).as_posix(),
                         "sha256": raw_hash(raw), "dimension_sizes": dims,
                         "cells": total, "numeric_cells": numeric, "null_or_non_numeric_cells": total - numeric,
                         "source_updated": body.get("updated"), "unit": body.get("dimension", {}).get("ContentsCode", {})})
    inventory = {"checked_at": datetime.now(timezone.utc).isoformat(),
                 "scope": "Official CYSTAT-DB 2021 census API catalogue, plus complete results for seven priority matrices; catalogue metadata is not table-cell semantic acceptance.",
                 "catalog_directories": sorted(listings, key=lambda row: row["path"]),
                 "catalog_tables": details, "selected_raw_tables": selected,
                 "totals": {"directories": len(listings), "tables": len(details),
                            "selected_full_tables": len(selected),
                            "selected_cells": sum(item["cells"] for item in selected),
                            "selected_numeric_cells": sum(item["numeric_cells"] for item in selected),
                            "table_disposition": dict(Counter("acquired_numeric_fields_semantically_unassessed"
                                if item["id"] in SELECTED else "official_location_identified_not_acquired"
                                for item in details))}}
    path = project / "evidence/CYP_CYSTAT2021_SOURCE_INVENTORY.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory["totals"], ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

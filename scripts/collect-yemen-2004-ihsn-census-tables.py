"""Acquire three CSO-authored 2004 census tables archived by IHSN."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


CATALOGUE = "https://datacatalog.ihsn.org/catalog/229/related-materials"
RESOURCES = [(1, 29548), (2, 29549), (3, 29550)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if not project.name.startswith("yemen-areadata-"):
        raise ValueError("Expected a separate Yemen candidate")
    raw = project / "raw/ihsn-cso-2004"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / "acquisition.json"
    if manifest_path.exists():
        raise FileExistsError("Acquisition manifest exists; inspect before retrying")
    receipt = {"catalogue_url": CATALOGUE, "catalogue_producer": "Central Statistical Organization, Yemen",
               "repository": "IHSN survey catalog", "reference_year": 2004,
               "checked_at": datetime.now(timezone.utc).isoformat(), "resources": []}
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData official-source research/0.1"
    for table_number, resource_id in RESOURCES:
        name = f"cso-2004-table-{table_number}.pdf"
        target = raw / name
        if target.exists():
            raise FileExistsError(f"Original exists; refusing overwrite: {target}")
        url = f"https://datacatalog.ihsn.org/catalog/229/download/{resource_id}"
        record = {"table": table_number, "resource_id": resource_id, "url": url,
                  "title": f"Population and Housing Census 2004 - Table {table_number}",
                  "author": "Central Statistical Organization", "path": f"raw/ihsn-cso-2004/{name}"}
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            body = response.content
            if not body.startswith(b"%PDF-") or len(body) > 10_000_000:
                raise ValueError("Response is not an expected-size PDF")
            target.write_bytes(body)
            record.update({"status": "acquired", "final_url": response.url,
                           "content_type": response.headers.get("Content-Type"),
                           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        except (requests.RequestException, ValueError) as error:
            record.update({"status": "failed", "error": str(error)})
        receipt["resources"].append(record)
        manifest_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"resources": receipt["resources"]}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Archive PDFs linked by pinned official QNMP municipality panels."""

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def acquire(item, directory):
    municipality, ordinal, url = item
    suffix = Path(urlparse(url).path).name.lower()
    kind = "strategy" if "municipalitystrategy" in url.lower() else "zoning"
    name = f"{municipality}-{ordinal:02d}-{kind}.pdf"
    path = directory / name
    receipt = {"municipality_panel": municipality, "panel_link_ordinal": ordinal,
               "url": url, "file": name, "retrieved_at": utc_now()}
    try:
        response = requests.get(url, timeout=(20, 120), headers={"User-Agent": "AreaData official-source audit/1.0"})
        receipt["http_status"] = response.status_code
        receipt["content_type"] = response.headers.get("Content-Type", "")
        response.raise_for_status()
        body = response.content
        if not body.startswith(b"%PDF-"):
            raise ValueError(f"Expected PDF header; got {body[:40]!r}")
        path.write_bytes(body)
        receipt.update(status="acquired", bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                       source_filename=suffix)
    except Exception as exc:
        receipt.update(status="failed", error=str(exc))
    (directory / f"{name}.receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--inspection", required=True)
parser.add_argument("--run-id", required=True)
args = parser.parse_args()
project = Path(args.project).resolve()
inspection = Path(args.inspection).resolve()
if not inspection.is_relative_to(project):
    raise SystemExit("Inspection must be inside project")
run_dir = project / "raw" / "qatar-r3-plan-pdfs" / args.run_id
run_dir.mkdir(parents=True, exist_ok=False)
manifest = json.loads(inspection.read_text(encoding="utf-8"))
items = []
for panel in manifest["entries"]:
    if panel["file"].startswith("msdp-"):
        municipality = panel["file"].removeprefix("msdp-").removesuffix(".html")
        items.extend((municipality, n, link["url"])
                     for n, link in enumerate(panel.get("pdf_links", []), start=1))
if len(items) != 12 or len({item[2] for item in items}) != len(items):
    raise SystemExit("Unexpected panel PDF link inventory")
with ThreadPoolExecutor(max_workers=4) as pool:
    receipts = list(pool.map(lambda item: acquire(item, run_dir), items))
out = {"source_inspection": str(inspection.relative_to(project)).replace("\\", "/"),
       "run_id": args.run_id, "receipts": receipts}
(run_dir / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"acquired": sum(r["status"] == "acquired" for r in receipts),
                  "failed": sum(r["status"] == "failed" for r in receipts),
                  "bytes": sum(r.get("bytes", 0) for r in receipts)}, ensure_ascii=False))
if any(r["status"] != "acquired" for r in receipts):
    raise SystemExit(1)

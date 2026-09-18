#!/usr/bin/env python3
"""Fetch a reviewed supplemental-source manifest with bounded, hashed receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def extension(content_type: str, url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".xlsx", ".xls", ".csv", ".geojson", ".json", ".pdf", ".zip", ".html"}:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return ".html" if guessed in {None, ".htm"} else guessed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--manifest", default="data/registries/americas-supplemental-sources.json", type=Path)
    parser.add_argument("--timeout", default=45, type=int)
    parser.add_argument("--max-bytes", default=100 * 1024 * 1024, type=int)
    args = parser.parse_args()
    project = args.project.resolve()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = project / "raw/supplemental-country-sources"
    root.mkdir(parents=True, exist_ok=True)
    receipts = []
    for source in manifest.get("sources", []):
        receipt = {**source, "requested_at": datetime.now(timezone.utc).isoformat(), "status": "failed_with_evidence"}
        try:
            request = urllib.request.Request(source["url"], headers={"User-Agent": "Mozilla/5.0 AreaData source audit/0.10", "Accept": "text/html,application/pdf,application/json,text/csv,*/*"})
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                body = response.read(args.max_bytes + 1)
                if len(body) > args.max_bytes:
                    raise ValueError(f"Response exceeds {args.max_bytes} bytes")
                receipt.update({"http_status": response.status, "final_url": response.url, "content_type": response.headers.get("Content-Type", "")})
            country_dir = root / source["country_area_id"]
            country_dir.mkdir(parents=True, exist_ok=True)
            safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", source["id"])
            target = country_dir / f"{source['domain']}-{safe_id}{extension(receipt['content_type'], receipt['final_url'])}"
            target.write_bytes(body)
            receipt.update({"status": "acquired", "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "path": target.relative_to(project).as_posix()})
        except Exception as exc:
            receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["completed_at"] = datetime.now(timezone.utc).isoformat()
        receipts.append(receipt)
        print(source["country_area_id"], source["id"], receipt["status"])
    output = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "manifest": args.manifest.as_posix(), "receipts": receipts}
    (root / "receipt.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(row["status"] == "acquired" for row in receipts), "failed": sum(row["status"] != "acquired" for row in receipts)}, indent=2))


if __name__ == "__main__":
    main()

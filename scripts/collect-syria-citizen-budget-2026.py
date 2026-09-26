"""Acquire the Syrian Ministry of Finance's 2026 citizen budget PDF."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


URL = "https://docs.mof.gov.sy/citizen_budget_2026.pdf"
RAW_NAME = "citizen-budget-2026.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))["country"]["id"] != "SYR":
        raise ValueError("Expected Syria project")
    out = project / "raw/syria-mof-2026"
    out.mkdir(parents=True, exist_ok=True)
    target = out / RAW_NAME
    receipt_path = out / f"{RAW_NAME}.receipt.json"
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        data = target.read_bytes()
        if receipt.get("source_url") != URL or receipt.get("sha256") != hashlib.sha256(data).hexdigest():
            raise ValueError("Existing source or receipt has changed")
        print(json.dumps(receipt, ensure_ascii=False))
        return
    if target.exists() or receipt_path.exists():
        raise ValueError("Source and receipt must both exist or both be absent")
    response = requests.get(URL, timeout=45, allow_redirects=False)
    response.raise_for_status()
    if response.headers.get("content-type", "").split(";", 1)[0] != "application/pdf":
        raise ValueError("Official URL did not return a PDF")
    data = response.content
    if not data.startswith(b"%PDF-") or len(data) < 100_000:
        raise ValueError("Unexpected PDF response size or signature")
    receipt = {
        "schema_version": "1.0", "source_url": URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "status": "acquired", "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "path": "raw/syria-mof-2026/" + RAW_NAME,
        "redistribution_terms": "review_required",
    }
    target.write_bytes(data)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()

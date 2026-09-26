"""Acquire Jordan DoS's 2025 population estimates PDF with a hash receipt."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


URL = "https://dosweb.dos.gov.jo/DataBank/population/population_Estimares/PopulationEstimates.pdf"
NAME = "jordan-population-estimates-2025.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))["country"]["id"] != "JOR":
        raise ValueError("Expected Jordan project")
    raw = project / "raw/jordan-dos-2025"
    raw.mkdir(parents=True, exist_ok=True)
    target = raw / NAME
    receipt_path = raw / f"{NAME}.receipt.json"
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt["source_url"] != URL or receipt["sha256"] != hashlib.sha256(target.read_bytes()).hexdigest():
            raise ValueError("Existing original or receipt differs")
        print(json.dumps(receipt, ensure_ascii=False))
        return
    if target.exists() or receipt_path.exists():
        raise ValueError("Original and receipt must both exist or both be absent")
    response = requests.get(URL, timeout=45, allow_redirects=False)
    response.raise_for_status()
    if response.headers.get("content-type", "").split(";", 1)[0] != "application/pdf":
        raise ValueError("Expected official PDF")
    data = response.content
    if not data.startswith(b"%PDF-") or len(data) < 50_000:
        raise ValueError("Unexpected official PDF size or signature")
    receipt = {
        "schema_version": "1.0", "source_url": URL, "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code, "content_type": response.headers.get("content-type"),
        "status": "acquired", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "path": "raw/jordan-dos-2025/" + NAME,
        "redistribution_terms": "review_required",
    }
    target.write_bytes(data)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()

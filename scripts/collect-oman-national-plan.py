"""Acquire the Ministry of Economy's official Eleventh Five-Year Plan PDF."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


URL = "https://www.economy.gov.om/PDF/خطة التنمية الخمسية الحادية عشرة.pdf"
CATALOGUE = "https://economy.gov.om/library.aspx"
RELATIVE = "raw/oman-ecensus-moi/oman-eleventh-five-year-plan-2026-2030.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData source-audit/1.0"})
    catalogue = session.get(CATALOGUE, timeout=50)
    catalogue.raise_for_status()
    if URL.encode("utf-8") not in catalogue.content:
        raise ValueError("Official plan URL missing from Ministry of Economy library")
    response = session.get(URL, timeout=90)
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF-") or len(body) < 100_000:
        raise ValueError("Official plan response is not the expected PDF")
    target = project / RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    receipt = {"source_url": URL, "catalogue_url": CATALOGUE, "final_url": response.url,
               "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
               "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
               "raw_path": RELATIVE, "status": "acquired", "redistribution_terms": "review_required",
               "method": "GET"}
    (project / (RELATIVE + ".receipt.json")).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bytes": len(body), "sha256": receipt["sha256"], "path": RELATIVE}))


if __name__ == "__main__":
    main()

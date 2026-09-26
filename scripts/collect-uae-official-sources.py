"""Acquire public UAE originals for a local, unpublished country candidate."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


SOURCES = (
    ("fcsc-uae-in-figures-2005.pdf",
     "https://fcsc.gov.ae/wp-content/uploads/2025/04/%D8%A7%D9%84%D8%A5%D9%85%D8%A7%D8%B1%D8%A7%D8%AA-%D8%A8%D8%A7%D9%84%D8%A3%D8%B1%D9%82%D8%A7%D9%85-2006.pdf",
     "application/pdf", b"%PDF-", 100_000),
    ("scad-abu-dhabi-census-population-2024.html",
     "https://census.scad.gov.ae/home/population?fid=0&lang=en&tab=webreport",
     "text/html", b"", 20_000),
    ("dubai-2040-structure-plan-executive-summary.pdf",
     "https://dmpmedia.dm.gov.ae/uploads/2024/04/Dubai-2040-Urban-Master-Plan-2040-Executive-Summary-v1.pdf",
     "application/pdf", b"%PDF-", 1_000_000),
    ("dubai-urban-planning-law-16-2023.pdf",
     "https://dlp.dubai.gov.ae/Legislation%20Reference/2023/Law%20No.%20%2816%29%20of%202023%20Concerning%20Urban%20Planning.pdf",
     "application/pdf", b"%PDF-", 50_000),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "ARE":
        raise ValueError("Expected United Arab Emirates candidate")
    raw = project / "raw/uae-official"
    raw.mkdir(parents=True, exist_ok=True)
    results = []
    for filename, url, media_type, signature, minimum in SOURCES:
        target = raw / filename
        receipt_path = raw / (filename + ".receipt.json")
        if target.exists() and receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt["source_url"] != url or receipt["sha256"] != hashlib.sha256(target.read_bytes()).hexdigest():
                raise ValueError(f"Original/receipt mismatch: {filename}")
            results.append(receipt)
            continue
        if receipt_path.exists():
            raise ValueError(f"Receipt exists without original: {filename}")
        response = requests.get(url, timeout=65)
        response.raise_for_status()
        content = response.content
        reported_type = response.headers.get("content-type", "").split(";", 1)[0]
        if reported_type != media_type or not content.startswith(signature) or len(content) < minimum:
            raise ValueError(f"Unexpected official source body: {filename}, {reported_type}, {len(content)} bytes")
        if target.exists():
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(content).digest():
                raise ValueError(f"Unreceipted original differs from current download: {filename}")
        else:
            target.write_bytes(content)
        receipt = {
            "schema_version": "1.0", "source_url": url, "final_url": response.url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "http_status": response.status_code,
            "content_type": response.headers.get("content-type"), "status": "acquired",
            "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
            "path": "raw/uae-official/" + filename, "redistribution_terms": "review_required",
        }
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append(receipt)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

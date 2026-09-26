"""Acquire IOM DTM's June 2026 Syria baseline assessment report."""

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


URL = "https://dtm.iom.int/sites/g/files/tmzbdl1461/files/reports/DTM%20Syria_Baseline_Round17.pdf"
PAGE_URL = "https://dtm.iom.int/reports/syrian-arab-republic-population-mobility-and-baseline-assessment-round-17-01-30-june-2026"
TERMS_URL = "https://dtm.iom.int/terms-and-conditions"
NAME = "iom-dtm-syria-baseline-round17-june-2026.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "SYR":
        raise ValueError("Expected Syria project")
    raw = project / "raw/syria-iom-round17"
    raw.mkdir(parents=True, exist_ok=True)
    target = raw / NAME
    receipt_path = raw / f"{NAME}.receipt.json"
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("source_url") != URL or receipt.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
            raise ValueError("Existing report and receipt do not match")
    elif target.exists() or receipt_path.exists():
        raise ValueError("Source and receipt must both exist or both be absent")
    else:
        response = requests.get(URL, timeout=60, allow_redirects=False)
        response.raise_for_status()
        data = response.content
        if response.headers.get("content-type", "").split(";", 1)[0] != "application/pdf" or not data.startswith(b"%PDF-"):
            raise ValueError("IOM URL did not return a PDF")
        receipt = {
            "schema_version": "1.0", "source_url": URL, "catalog_url": PAGE_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "status": "acquired",
            "http_status": response.status_code, "content_type": response.headers.get("content-type"),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "path": "raw/syria-iom-round17/" + NAME,
            "redistribution_terms": "review_required",
        }
        target.write_bytes(data)
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    terms_path = raw / "iom-dtm-terms.html"
    terms_receipt_path = raw / "iom-dtm-terms.html.receipt.json"
    if terms_path.exists() and terms_receipt_path.exists():
        terms_receipt = json.loads(terms_receipt_path.read_text(encoding="utf-8"))
        if terms_receipt.get("source_url") != TERMS_URL or terms_receipt.get("sha256") != hashlib.sha256(terms_path.read_bytes()).hexdigest():
            raise ValueError("Existing terms and receipt do not match")
    elif terms_path.exists() or terms_receipt_path.exists():
        raise ValueError("Terms and receipt must both exist or both be absent")
    else:
        terms_response = requests.get(TERMS_URL, timeout=30, allow_redirects=True)
        terms_response.raise_for_status()
        if urlparse(terms_response.url).hostname != "dtm.iom.int":
            raise ValueError("IOM terms redirected outside dtm.iom.int")
        terms_bytes = terms_response.content
        terms_text = html.unescape(re.sub(r"<[^>]+>", " ", terms_response.text))
        terms_text = re.sub(r"\s+", " ", terms_text).lower()
        if "non-commercial use only" not in terms_text or "explicit prior written permission" not in terms_text:
            raise ValueError(f"IOM terms text changed; review before using report ({terms_response.status_code}, {len(terms_bytes)} bytes)")
        terms_receipt = {
            "schema_version": "1.0", "source_url": TERMS_URL,
            "final_url": terms_response.url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "status": "acquired",
            "http_status": terms_response.status_code,
            "content_type": terms_response.headers.get("content-type"),
            "bytes": len(terms_bytes), "sha256": hashlib.sha256(terms_bytes).hexdigest(),
            "path": "raw/syria-iom-round17/iom-dtm-terms.html",
            "restriction": "non-commercial view/download; explicit prior written permission for extraction and redistribution",
        }
        terms_path.write_bytes(terms_bytes)
        terms_receipt_path.write_text(json.dumps(terms_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": receipt, "terms": terms_receipt}, ensure_ascii=False))


if __name__ == "__main__":
    main()

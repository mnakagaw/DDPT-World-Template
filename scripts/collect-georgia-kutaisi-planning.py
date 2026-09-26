"""Acquire the official Kutaisi medium-term action plan and original 2026 budget act."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ORIGINALS = (
    ("kutaisi-action-plan-2026-2029.pdf", "https://www.kutaisi.gov.ge/public/files/1757933270_%E1%83%A1%E1%83%90%E1%83%A8%E1%83%A3%E1%83%90%E1%83%9A%E1%83%9D%E1%83%95%E1%83%90%E1%83%93%E1%83%98%E1%83%90%E1%83%9C%E1%83%98%202026-2029.pdf"),
    ("kutaisi-budget-2026-original.pdf", "https://www.matsne.gov.ge/ka/document/download/6697241/0/ge/pdf"),
)

EXPECTED_SHA256 = {
    "kutaisi-action-plan-2026-2029.pdf": "7f536be9ac616927aba859bc9e2b9c1878e0f43e5861d9bb26e44e89583d0375",
    "kutaisi-budget-2026-original.pdf": "de9210e873324e0f584e3cacf42a889369d6ea24fd3b0fb5a5dfac52dfbc0581",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "GEO":
        raise ValueError("Expected a Georgia project")
    raw = project / "raw/georgia-kutaisi-planning"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, url in ORIGINALS:
        target = raw / name
        receipt_path = raw / (name + ".receipt.json")
        if target.exists() and receipt_path.exists():
            body = target.read_bytes()
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if hashlib.sha256(body).hexdigest() != receipt.get("sha256") or receipt.get("sha256") != EXPECTED_SHA256[name]:
                raise ValueError(f"Existing original changed locally: {name}")
        else:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            body = response.content
            if len(body) < 1000 or not body.startswith(b"%PDF-") or hashlib.sha256(body).hexdigest() != EXPECTED_SHA256[name]:
                raise ValueError(f"Unexpected PDF body for {name}")
            target.write_bytes(body)
            receipt = {
                "source_url": url, "response_url": response.url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "raw_path": f"raw/georgia-kutaisi-planning/{name}",
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "status": "acquired", "http_status": response.status_code,
                "transport": "requests default TLS certificate verification",
                "redistribution_terms": "review_required",
            }
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipts.append(receipt)
        print(name, len(body), receipt["sha256"])
    (project / "evidence/GEO_KUTAISI_PLAN_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

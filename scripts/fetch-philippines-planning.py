"""Acquire selected official Philippine planning and Quezon City fiscal documents."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


SOURCES = [
    ("phl-dilg-cdp-toolkit", "https://region1.dilg.gov.ph/images/Transparency/BOOKS/CDP-TOOLKIT-FINAL%20AS%20OF%20APRIL%208%202022.pdf", "national_guide"),
    ("phl-qc-cdp-2026-2031", "https://quezoncity.gov.ph/wp-content/uploads/2020/09/Quezon-City-Comprehensive-Development-Plan-2026-2031-04.30.26.pdf", "local_plan"),
    ("phl-qc-cdp-adoption-2025", "https://d2hj2alpj62gbw.cloudfront.net/resolutions/approved/SP-10311,%20S-2025.pdf", "adoption_resolution"),
    ("phl-qc-ldip-2027-2029", "https://quezoncity.gov.ph/wp-content/uploads/2020/09/Quezon-City-Local-Development-Investment-Program-2027-2029-07.01.26.pdf", "local_investment_program"),
    ("phl-qc-aip-2026", "https://quezoncity.gov.ph/wp-content/uploads/2025/11/SP-10255-S-2025.pdf", "annual_investment_resolution"),
    ("phl-qc-budget-2026", "https://quezoncity.gov.ph/wp-content/uploads/2026/01/SP-3465-S-2025.pdf", "annual_budget_ordinance"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    out = args.project / "raw" / "planning"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for source_id, url, kind in SOURCES:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        body = response.content
        if not body.startswith(b"%PDF-"):
            raise ValueError(f"Non-PDF response for {source_id}: {response.status_code}")
        target = out / (source_id + ".pdf")
        target.write_bytes(body)
        records.append({"id": source_id, "url": url, "kind": kind,
                        "raw_path": str(target.relative_to(args.project)).replace("\\", "/"),
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "http_status": response.status_code, "content_type": response.headers.get("Content-Type")})
        print(json.dumps({"id": source_id, "bytes": len(body)}), flush=True)
    manifest = args.project / "evidence" / "PHL_PLANNING_SOURCE_MANIFEST.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "sources": records}, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({"sources": len(records), "manifest": str(manifest)}))


if __name__ == "__main__":
    main()

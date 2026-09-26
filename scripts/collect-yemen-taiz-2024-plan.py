"""Acquire the Taiz planning office's full 2024-2026 plan as private evidence."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


CATALOGUE = "https://www.mopic-taiz.com/plans_projects_post/taiz-economic-and-social-development-plan-2024-2026-2/"
URL = "https://www.mopic-taiz.com/wp-content/uploads/2023/11/Taiz-Economic-and-Social-Development-Plan-3-1.pdf"
NAME = "taiz-economic-and-social-development-plan-2024-2026.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if not project.name.startswith("yemen-areadata-"):
        raise ValueError("Expected a separate Yemen candidate")
    raw = project / "raw/taiz-planning-2024"
    raw.mkdir(parents=True, exist_ok=True)
    pdf = raw / NAME
    receipt_path = raw / f"{NAME}.receipt.json"
    if pdf.exists() or receipt_path.exists():
        raise FileExistsError("Plan original or receipt exists; inspect before retrying")
    response = requests.get(URL, timeout=120, headers={"User-Agent": "AreaData official-source research/0.1"})
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF-") or len(body) > 40_000_000:
        raise ValueError("Plan response is not an expected-size PDF")
    pdf.write_bytes(body)
    receipt = {"catalogue_url": CATALOGUE, "source_url": URL,
               "final_url": response.url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "content_type": response.headers.get("Content-Type"),
               "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
               "path": f"raw/taiz-planning-2024/{NAME}",
               "status": "acquired", "adoption_state": "not_yet_inspected",
               "publisher_attribution": "Taiz Governorate Planning and International Cooperation Office"}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bytes": receipt["bytes"], "sha256": receipt["sha256"]}))


if __name__ == "__main__":
    main()

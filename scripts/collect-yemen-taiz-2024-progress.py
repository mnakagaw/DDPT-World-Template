"""Acquire Taiz planning office's 2024 progress/2025 priorities PDF."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


URL = "https://www.mopic-taiz.com/wp-content/uploads/2025/01/%D8%B9%D8%B1%D8%B6-%D8%A3%D9%88%D9%84%D9%88%D9%8A%D8%A7%D8%AA-2025%D9%85-%D9%88%D8%AA%D9%82%D8%B1%D9%8A%D8%B1-2024-1.pdf"
NAME = "taiz-2024-progress-2025-priorities.pdf"


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
        raise FileExistsError("Progress source already acquired; inspect before retrying")
    response = requests.get(URL, timeout=90, headers={"User-Agent": "AreaData source research/0.1"})
    response.raise_for_status()
    content = response.content
    if not content.startswith(b"%PDF-") or len(content) > 20_000_000:
        raise ValueError("Progress response is not an expected-size PDF")
    pdf.write_bytes(content)
    receipt = {"source_url": URL, "final_url": response.url,
               "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "content_type": response.headers.get("Content-Type"),
               "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
               "path": f"raw/taiz-planning-2024/{NAME}",
               "status": "acquired", "adoption_state": "not_yet_inspected",
               "publisher_attribution": "Taiz Planning and International Cooperation Office"}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bytes": receipt["bytes"], "sha256": receipt["sha256"]}))


if __name__ == "__main__":
    main()

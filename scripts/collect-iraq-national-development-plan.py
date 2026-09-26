"""Acquire the official Iraqi National Development Plan PDF as private evidence."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


URL = "https://www.mop.gov.iq/documents/economic-policies/development-plans/National%20Development%20Plan%202024-2028.pdf"
FILENAME = "iraq-national-development-plan-2024-2028.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if not project.name.startswith("iraq-areadata-"):
        raise ValueError("Expected a separate Iraq candidate project")
    raw = project / "raw"
    target = raw / FILENAME
    receipt = raw / f"{FILENAME}.receipt.json"
    if target.exists() or receipt.exists():
        raise FileExistsError("A plan acquisition already exists; inspect it before retrying")
    response = requests.get(URL, timeout=90, headers={"User-Agent": "AreaData official source audit/0.1"})
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF-") or len(body) > 35_000_000:
        raise ValueError("Official response lacks a PDF signature or exceeds the review limit")
    target.write_bytes(body)
    details = {"source_url": URL, "final_url": response.url,
               "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "response_status": response.status_code,
               "content_type": response.headers.get("Content-Type"),
               "object_path": f"raw/{FILENAME}", "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest(),
               "process_state": "acquired", "adoption_state": "not_yet_inspected"}
    receipt.write_text(json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bytes": len(body), "sha256": details["sha256"],
                      "status": details["process_state"]}))


if __name__ == "__main__":
    main()

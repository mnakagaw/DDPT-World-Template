"""Collect the Taiz CSO branch's 2024 statistical yearbook as private evidence."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


CATALOGUE = "https://cso-taizgov.org/cso/publications.php"
VIEWER = "https://cso-taizgov.org/cso/viewer.php?file=68b524c99d174.pdf&title=%D9%83%D8%AA%D8%A7%D8%A8+%D8%A7%D9%84%D8%A7%D8%AD%D8%B5%D8%A7%D8%A1+%D8%A7%D9%84%D8%B3%D9%86%D9%88%D9%8A+2024&type=book"
URL = "https://cso-taizgov.org/cso/files/books/68b524c99d174.pdf"
FILENAME = "taiz-cso-statistical-yearbook-2024.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if not project.name.startswith("yemen-areadata-"):
        raise ValueError("Expected a separate Yemen candidate")
    raw = project / "raw/taiz-cso-2024"
    raw.mkdir(parents=True, exist_ok=True)
    pdf = raw / FILENAME
    receipt_path = raw / f"{FILENAME}.receipt.json"
    if pdf.exists() or receipt_path.exists():
        raise FileExistsError("A Taiz yearbook acquisition exists; inspect before retrying")
    response = requests.get(URL, timeout=180, headers={"User-Agent": "AreaData source research/0.1"})
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF-") or len(body) > 60_000_000:
        raise ValueError("Response is not an expected-size PDF")
    pdf.write_bytes(body)
    receipt = {"catalogue_url": CATALOGUE, "viewer_url": VIEWER, "source_url": URL,
               "final_url": response.url, "checked_at": datetime.now(timezone.utc).isoformat(),
               "content_type": response.headers.get("Content-Type"), "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest(), "path": f"raw/taiz-cso-2024/{FILENAME}",
               "status": "acquired", "adoption_state": "not_yet_inspected",
               "source_description": "Taiz Central Statistical Organization branch 2024 statistical yearbook"}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bytes": receipt["bytes"], "sha256": receipt["sha256"],
                      "status": receipt["status"]}))


if __name__ == "__main__":
    main()

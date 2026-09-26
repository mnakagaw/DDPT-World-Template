"""Acquire the pinned Maldives legal-context pages and Fonadhoo plan PDF.

Changed official pages are retained for review, but not silently promoted into the
country importer: the manifest hash must be deliberately updated after audit.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from pypdf import PdfReader


MANIFEST = Path(__file__).resolve().parents[1] / "config/maldives-planning-source-manifest.json"


def main(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    receipt = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "sources": []}
    for item in manifest["sources"]:
        row = {"id": item["id"], "url": item["url"], "expected_sha256": item["sha256"]}
        try:
            response = requests.get(item["url"], timeout=90)
            response.raise_for_status()
            body = response.content
            suffix = Path(item["raw_path"]).suffix.lower()
            if suffix == ".pdf" and not body.startswith(b"%PDF-"):
                raise ValueError("Expected PDF body")
            if suffix == ".html" and b"<html" not in body[:1000].lower():
                raise ValueError("Expected HTML body")
            path = project / item["raw_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            current_hash = hashlib.sha256(body).hexdigest()
            row.update({"raw_path": item["raw_path"], "bytes": len(body),
                        "sha256": current_hash,
                        "matches_manifest": len(body) == item["bytes"] and
                        current_hash == item["sha256"]})
            if path.exists() and path.read_bytes() != body:
                changed = project / "evidence/reacquisition" / f"{item['id']}-{current_hash[:12]}{suffix}"
                changed.parent.mkdir(parents=True, exist_ok=True)
                changed.write_bytes(body)
                row.update({"status": "changed_original", "candidate_path": str(changed)})
            else:
                if not path.exists():
                    path.write_bytes(body)
                row["status"] = "downloaded" if row["matches_manifest"] else "changed_original"
            if suffix == ".pdf":
                row["pages"] = len(PdfReader(changed if "candidate_path" in row else path).pages)
        except Exception as exc:
            row.update({"status": "failed", "error": str(exc), "matches_manifest": False})
        receipt["sources"].append(row)
    out = project / "evidence/MDV_PLANNING_ACQUISITION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(x["status"] == "downloaded" for x in receipt["sources"]),
                      "pinned_matches": sum(x["matches_manifest"] for x in receipt["sources"]),
                      "failures_or_changes": [x["id"] for x in receipt["sources"] if x["status"] != "downloaded"],
                      "receipt": str(out)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

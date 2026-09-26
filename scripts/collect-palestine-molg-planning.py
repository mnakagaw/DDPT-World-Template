"""Acquire two Ministry of Local Government planning originals for scope review."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ORIGINALS = (
    ("molg-local-development-planning-guide.pdf",
     "https://molg.pna.ps/uploads/files/SDIP_d2ff2339671b4f1fbbd1c083e0ccd038.pdf"),
    ("molg-local-government-sector-strategy-2025-2027.pdf",
     "https://www.molg.pna.ps/uploads/files/%D8%A7%D9%84%D9%86%D8%B3%D8%AE%D8%A9%20%D8%A7%D9%84%D9%86%D9%87%D8%A7%D8%A6%D9%8A%D8%A9%20-%20%D8%A7%D9%84%D8%AE%D8%B7%D8%A9%20%D8%A7%D9%84%D8%A7%D8%B3%D8%AA%D8%B1%D8%A7%D8%AA%D9%8A%D8%AC%D9%8A%D8%A9%20%D9%83%D8%A7%D9%85%D9%84%D8%A9%20%D9%84%D9%82%D8%B7%D8%A7%D8%B9%20%D8%A7%D9%84%D8%AD%D9%83%D9%85%20%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%20-2025-2027_24690cbe335f4e548e8e7d73c9702de7.pdf"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    raw = project / "raw/palestine-molg-planning"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, url in ORIGINALS:
        target = raw / name
        subprocess.run(["curl.exe", "--fail", "--location", "--silent", "--show-error",
                        "--max-time", "90", "--output", str(target), url], check=True)
        body = target.read_bytes()
        if len(body) < 100000 or not body.startswith(b"%PDF-"):
            raise ValueError(f"Unexpected Ministry of Local Government PDF: {name}")
        receipt = {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                   "raw_path": "raw/palestine-molg-planning/" + name, "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(), "status": "acquired",
                   "transport": "curl.exe system CA verification; no insecure option",
                   "redistribution_terms": "review_required"}
        (raw / (name + ".receipt.json")).write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipts.append(receipt)
    (project / "evidence/PSE_MOLG_PLANNING_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": len(receipts), "bytes": sum(row["bytes"] for row in receipts),
                      "sha256": {Path(row["raw_path"]).name: row["sha256"] for row in receipts}}))


if __name__ == "__main__":
    main()

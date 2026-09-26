"""Acquire Palestinian Central Bureau of Statistics 2017 census PDFs safely."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ORIGINALS = (
    ("pcbs-2017-final-summary.pdf", "https://www.pcbs.gov.ps/Downloads/book2383.pdf", b"%PDF-"),
    ("pcbs-2017-detailed-population.pdf", "https://www.pcbs.gov.ps/Downloads/book2425.pdf", b"%PDF-"),
    ("pcbs-2017-governorate-area.html", "https://www.pcbs.gov.ps/Portals/_Rainbow/Documents/Land-use-table%201E-2019.html", b""),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    raw = project / "raw/palestine-pcbs-2017"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, url, signature in ORIGINALS:
        target = raw / name
        # The host Python CA bundle does not trust the PCBS chain; Windows curl
        # verifies it with the system trust store. Never pass --insecure/-k.
        subprocess.run(["curl.exe", "--fail", "--location", "--silent", "--show-error",
                        "--output", str(target), url], check=True)
        body = target.read_bytes()
        if len(body) < 1000 or not body.startswith(signature):
            raise ValueError(f"Official original has unexpected bytes: {name}")
        receipt = {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                   "raw_path": "raw/palestine-pcbs-2017/" + name, "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(), "status": "acquired",
                   "transport": "curl.exe system CA verification; no insecure option",
                   "redistribution_terms": "review_required"}
        (raw / (name + ".receipt.json")).write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipts.append(receipt)
    (project / "evidence/PSE_PCBS_2017_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": len(receipts), "bytes": sum(x["bytes"] for x in receipts),
                      "sha256": {Path(x["raw_path"]).name: x["sha256"] for x in receipts}}))


if __name__ == "__main__":
    main()

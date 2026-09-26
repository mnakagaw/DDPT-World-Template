"""Acquire pinned Kuwait 2021 registration-census originals with receipts."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ORIGINALS = (
    ("table1-governorate-nationality-gender.pdf",
     "https://census.csb.gov.kw/CensusData_EN?handler=ExportPDF&st_id=4",
     "368bbce7a09929686fb9777ad36e6ab3a8f99dd2d48987bd02a61611130a96b3", b"%PDF-"),
    ("table1-governorate-nationality-gender.xlsx",
     "https://census.csb.gov.kw/CensusData_EN?st_id=4&handler=ExportExcel",
     "1ef400667d1cd91b68aba1c446fb63861a65cd45d269b4090707b27893f89bd7", b"PK"),
    ("table51-usual-residence.pdf",
     "https://census.csb.gov.kw/CensusData_EN?handler=ExportPDF&st_id=71",
     "23292eaaaa4e70bef182b11bfb082e6eb589e45a00fa0b4b1382628c4dd8a18a", b"%PDF-"),
    ("table51-usual-residence.xlsx",
     "https://census.csb.gov.kw/CensusData_EN?handler=ExportExcel&st_id=71",
     "1b3f865e3ec52558a1a516176fc53b73436b27659c2579bf9c1a1fc4468daa51", b"PK"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    raw = project / "raw/kuwait-csb-2021"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, url, expected_hash, signature in ORIGINALS:
        target = raw / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected_hash:
            body = target.read_bytes()
            transport = "previously acquired; SHA-256 rechecked"
        else:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            body = response.content
            transport = "requests default TLS certificate verification"
            if hashlib.sha256(body).hexdigest() == expected_hash:
                target.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        if len(body) < 1000 or not body.startswith(signature) or digest != expected_hash:
            raise ValueError(f"Kuwait original changed or invalid: {name} {digest}")
        old = target.with_name(name + ".receipt.json")
        retrieved_at = datetime.now(timezone.utc).isoformat()
        if old.exists():
            previous = json.loads(old.read_text(encoding="utf-8"))
            if previous.get("sha256") == digest:
                retrieved_at = previous["retrieved_at"]
        receipt = {"source_url": url, "retrieved_at": retrieved_at,
                   "raw_path": "raw/kuwait-csb-2021/" + name, "bytes": len(body),
                   "sha256": digest, "status": "acquired", "transport": transport,
                   "redistribution_terms": "review_required"}
        old.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipts.append(receipt)
    (project / "evidence/KWT_CSB_2021_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": len(receipts), "sha256": {Path(r["raw_path"]).name: r["sha256"]
                                                     for r in receipts}}))


if __name__ == "__main__":
    main()

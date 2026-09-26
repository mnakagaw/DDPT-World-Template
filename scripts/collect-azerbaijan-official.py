"""Acquire pinned Azerbaijan statistical and Astara planning originals with receipts."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ORIGINALS = (
    ("2019-census-volume-a.zip", "https://www.stat.gov.az/menu/6/statistical_yearbooks/source/Siyahiyaalinma-2019%2C%20Cild%20A.zip", b"PK"),
    ("2019-census-volume-b.zip", "https://www.stat.gov.az/menu/6/statistical_yearbooks/source/Siyahiyaalinma-2019%2C%20Cild%20B.zip", b"PK"),
    ("2026-resident-population-by-area.xls", "https://www.stat.gov.az/source/demoqraphy/en/001_17en.xls", b"\xd0\xcf\x11\xe0"),
    ("2026-population-sex-settlement.xls", "https://www.stat.gov.az/source/demoqraphy/en/001_19en.xls", b"\xd0\xcf\x11\xe0"),
    ("2020-2026-population-age-by-area.xls", "https://www.stat.gov.az/source/demoqraphy/en/001_23en.xls", b"\xd0\xcf\x11\xe0"),
    ("2025-area-population-density.xls", "https://www.stat.gov.az/source/demoqraphy/en/001_15en.xls", b"\xd0\xcf\x11\xe0"),
    ("2025-administrative-division.xls", "https://www.stat.gov.az/source/demoqraphy/en/001_16en.xls", b"\xd0\xcf\x11\xe0"),
    ("2024-administrative-classification.pdf", "https://www.stat.gov.az/menu/5/classifications/source/Inzibati-1.05.2024.pdf", b"%PDF-"),
    ("astara-master-plan-approval-291-2025.pdf", "https://arxkom.gov.az/storage/uploads/daom/73_minister_file_az_6926b13319ba8.pdf", b"%PDF-"),
    ("astara-master-plan-map.pdf", "https://arxkom.gov.az/storage/media/newmedia/2026/03/37464/ab6d00c4-e031-4ec2-8048-1d4633e9d34d.pdf", b"%PDF-"),
    ("astara-master-plan-announcement.html", "https://www.arxkom.gov.az/media/xeberler/astara-seherinin-2039-cu-iledek-olan-dovr-ucun-inkisaf-prioritetleri-mueyyen-edildi", b"<"),
)

EXPECTED_SHA256 = {
    "2019-census-volume-a.zip": "503b379af477e7022255cd02936dbb3cb3b777632a00b023f6d56e61d5028f05",
    "2019-census-volume-b.zip": "be113eb342a218429a9d1e5112f7a232fa099e0ed270cf18ee1aa77a4de3e080",
    "2026-resident-population-by-area.xls": "34057c449d9114277d5608b99c44e29a8d3dc9fc8ec5f9fce02a4911f2e35162",
    "2026-population-sex-settlement.xls": "fa66767c497fb1dd48f70762b26a0269519828ca26dccd087f6adbcc4c808b89",
    "2020-2026-population-age-by-area.xls": "6d47885ee89077fb2412ee8c145a32edefa6b873da680bfcb746b36ca33ebf3c",
    "2025-area-population-density.xls": "de9bc5a8caa091383712cfacfbc591836e5dad28f8023c5b4b276f063e25b56c",
    "2025-administrative-division.xls": "ab668765d8acb555cefd067f00f630a964bdef19b92b611663be9e9d8922fefe",
    "2024-administrative-classification.pdf": "2445d60a6d7294d47ab7886eada3b27d86c8cdf9794da1962e3ba233952ef6b9",
    "astara-master-plan-approval-291-2025.pdf": "41cb058a92213802a1885d866baa279de8c11ac537eb1ea8580e6f9949b41957",
    "astara-master-plan-map.pdf": "7fa691485094422e014aa2aa7314cd1224d8c69926a31fe6973398ef5b7261de",
    "astara-master-plan-announcement.html": "ff7448249c9fec2008cdb0bfb6ff1a72df1fd13d48db917bc81d086db26700e0",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "AZE":
        raise ValueError("Expected an Azerbaijan candidate")
    raw_dir = project / "raw/azerbaijan-official"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    receipts = []
    for filename, url, signature in ORIGINALS:
        destination = raw_dir / filename
        receipt_file = raw_dir / (filename + ".receipt.json")
        if destination.exists() or receipt_file.exists():
            if not destination.exists() or not receipt_file.exists():
                raise ValueError(f"Incomplete prior acquisition: {filename}")
            body = destination.read_bytes()
            receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
            if hashlib.sha256(body).hexdigest() != receipt["sha256"] or receipt["sha256"] != EXPECTED_SHA256[filename]:
                raise ValueError(f"Original differs from receipt: {filename}")
        else:
            response = session.get(url, timeout=180)
            response.raise_for_status()
            body = response.content
            if len(body) < 1000 or not body.startswith(signature) or hashlib.sha256(body).hexdigest() != EXPECTED_SHA256[filename]:
                raise ValueError(f"Unexpected response for {filename}: {len(body)} bytes")
            receipt = {
                "source_url": url,
                "response_url": response.url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "raw_path": f"raw/azerbaijan-official/{filename}",
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "status": "acquired",
                "http_status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "last_modified": response.headers.get("last-modified"),
                "etag": response.headers.get("etag"),
                "transport": "requests default TLS certificate verification",
                "redistribution_terms": "review_required",
            }
            destination.write_bytes(body)
            receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipts.append(receipt)
        print(filename, len(body), receipt["sha256"])
    (project / "evidence/AZE_OFFICIAL_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": receipts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

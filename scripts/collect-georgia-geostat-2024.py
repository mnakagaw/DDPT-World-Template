"""Collect a pinned subset of Geostat's 2024 census originals with receipts."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ORIGINALS = (
    ("01-administrative-territorial-units-sex.xlsx", "https://geostat.ge/media/81091/1.Population-of-Georgia-by-administrative-territorial-units-and-sex.xlsx", b"PK"),
    ("02-self-governed-units-urban-rural-sex.xlsx", "https://geostat.ge/media/80611/2.-Population-of-Georgia-by-self-governed-units%2C-urban-rural-settlements-and-sex.xlsx", b"PK"),
    ("03-birthplace-age-sex.xlsx", "https://geostat.ge/media/80612/3.-Population-of-Georgia-by-place-of-birth%2C-5-year-age-groups-and-sex.xlsx", b"PK"),
    ("04-internal-migration.xlsx", "https://geostat.ge/media/80613/4.-Internal-migrants-by-usual-place-of-residence-and.xlsx", b"PK"),
    ("05-idp-age-settlement-sex.xlsx", "https://geostat.ge/media/80615/5.-Number-of-IDPs-in-Georgia-by-5-year-age-groups%2C-urban-rural-settlements-and-sex.xlsx", b"PK"),
    ("06-idp-residence-origin-sex.xlsx", "https://geostat.ge/media/80616/6.-IDPs-by-usual-place-of-residence%2C-place-of-residence-before-acquiring-IDP-status%2C-sex.xlsx", b"PK"),
    ("2024-census-main-results.pdf", "https://geostat.ge/media/80541/Main-Results-of-the-2024-Population-and-Agricultural-Census.pdf", b"%PDF-"),
)

EXPECTED_SHA256 = {
    "01-administrative-territorial-units-sex.xlsx": "d6348f94cb4827c4c9433f3ee5820ec35dc016254316ae65eb07fe923edc0de1",
    "02-self-governed-units-urban-rural-sex.xlsx": "b3629935b5d8107c924ae8f5472a1537f6689227373a9e2936dcc46b20753474",
    "03-birthplace-age-sex.xlsx": "a91e975fd60ee5d36d3edf26ce7f1a7e86968ede2d4250ad74da8e385659c5d8",
    "04-internal-migration.xlsx": "db139407771f5b9568392468ee752a0909bb80d06ec64a40f0e598d71afdd351",
    "05-idp-age-settlement-sex.xlsx": "91033bd00e1edc25b7932b925fb45a7f2ce19cb3d411ab7aca98e8c0cb153a4a",
    "06-idp-residence-origin-sex.xlsx": "a4d2483aa428f43b6e87f152e130216cd8b27bf2e41859b0a7961c8bf876b711",
    "2024-census-main-results.pdf": "45219a3cc2d93d7b2b4805f25e90d07b6bb82c2705ceead35a7f92e0cc16d214",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "GEO":
        raise ValueError("Expected a Georgia project")
    raw = project / "raw/georgia-geostat-2024"
    raw.mkdir(parents=True, exist_ok=True)
    rows = []
    session = requests.Session()
    for name, url, signature in ORIGINALS:
        target = raw / name
        receipt_path = raw / (name + ".receipt.json")
        if target.exists() and receipt_path.exists():
            body = target.read_bytes()
            previous = json.loads(receipt_path.read_text(encoding="utf-8"))
            if hashlib.sha256(body).hexdigest() != previous.get("sha256") or previous.get("sha256") != EXPECTED_SHA256[name]:
                raise ValueError(f"Existing original changed locally: {name}")
            receipt = previous
        else:
            response = session.get(url, timeout=90)
            response.raise_for_status()
            body = response.content
            if len(body) < 1000 or not body.startswith(signature) or hashlib.sha256(body).hexdigest() != EXPECTED_SHA256[name]:
                raise ValueError(f"Unexpected body for {name}: {len(body)} bytes")
            target.write_bytes(body)
            receipt = {
                "source_url": url, "response_url": response.url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "raw_path": f"raw/georgia-geostat-2024/{name}",
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "status": "acquired", "http_status": response.status_code,
                "transport": "requests default TLS certificate verification",
                "redistribution_terms": "review_required",
            }
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append(receipt)
        print(name, len(body), receipt["sha256"])
    (project / "evidence/GEO_GEOSTAT_2024_ACQUISITION.json").write_text(
        json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "receipts": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

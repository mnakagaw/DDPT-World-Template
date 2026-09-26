"""Acquire the six linked CBS 2022 Census Excel originals without overwriting them."""

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


BASE = "https://www.cbs.gov.il/he/publications/LochutTlushim/2025/"
FILES = (
    ("selected-localities-statistical-areas.xlsx", "Selected data, by localities and statistical areas - the 2022 Census.xlsx"),
    ("population-group-religion-age-sex.xlsx", "Population by population group, religion, age, and sex - 2022 Census estimate.xlsx"),
    ("population-households-locality.xlsx", "Population and households by locality - 2022 Census estimate.xlsx"),
    ("population-selected-characteristics.xlsx", "Population by selected characteristics - 2022 Census estimate, end of 2021 population estimate and 2008 Census estimate.xlsx"),
    ("households-selected-characteristics.xlsx", "Households by selected characteristics - 2022 Census estimate and 2008 Census estimate.xlsx"),
    ("broad-geographical-units.xlsx", "Summarized file of broad geographical units - census 2022.xlsx"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "ISR":
        raise ValueError("Expected Israel candidate")
    raw = project / "raw/israel-cbs-census-2022"
    raw.mkdir(parents=True, exist_ok=True)
    results = []
    for filename, official_name in FILES:
        url = BASE + quote(official_name, safe="")
        target = raw / filename
        receipt_path = raw / (filename + ".receipt.json")
        if target.exists() and receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("source_url") != url or receipt.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
                raise ValueError(f"Original/receipt mismatch: {filename}")
            results.append(receipt)
            continue
        if target.exists() or receipt_path.exists():
            raise ValueError(f"Incomplete immutable original/receipt pair: {filename}")
        attempt = {"schema_version": "1.0", "source_url": url, "official_link_title": official_name,
                   "retrieved_at": datetime.now(timezone.utc).isoformat(), "path": "raw/israel-cbs-census-2022/" + filename}
        try:
            response = requests.get(url, timeout=120)
            attempt.update(final_url=response.url, http_status=response.status_code,
                           content_type=response.headers.get("content-type"), bytes=len(response.content))
            response.raise_for_status()
            if len(response.content) < 2_000 or not response.content.startswith(b"PK"):
                raise ValueError("Response is not an Excel ZIP package")
            target.write_bytes(response.content)
            if not zipfile.is_zipfile(target):
                target.unlink()
                raise ValueError("Response fails ZIP integrity check")
            attempt.update(status="acquired", sha256=hashlib.sha256(response.content).hexdigest(),
                           redistribution_terms="review_required")
            receipt_path.write_text(json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (requests.RequestException, ValueError) as exc:
            attempt.update(status="failed_with_evidence", error=f"{type(exc).__name__}: {exc}")
            (raw / (filename + ".failure.json")).write_text(json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append(attempt)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

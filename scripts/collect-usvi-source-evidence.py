#!/usr/bin/env python3
"""Acquire official U.S. Virgin Islands census, planning and budget evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "census-usvi.html": "https://www.census.gov/data/tables/2020/dec/2020-us-virgin-islands.html",
    "dpnr-planning.html": "https://dpnr.vi.gov/comprehensive-coastal-zone-planning/what-we-do/",
    "legislature-plan-adoption.html": "https://legvi.org/35th-legislature-of-the-virgin-islands-advances-key-nominations-zoning-approvals-and-bills-to-governor-for-action/",
    "omb-ceds.html": "https://omb.vi.gov/comprehensive-economic-development-strategy-2020-2025/",
    "omb-publications.html": "https://omb.vi.gov/publications/",
    "fy2025-budget.pdf": "https://omb.vi.gov/wp-content/uploads/2025/04/FY-2025-USVI-Proposed-Executive-Budget-Book.pdf",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, url in SOURCES.items():
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "AreaData/0.10.2 source collector",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read()
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
            (out / name).write_bytes(body)
            entries.append(
                {
                    "name": name,
                    "url": url,
                    "final_url": final_url,
                    "status": "acquired",
                    "content_type": content_type,
                    "bytes": len(body),
                    "sha256": digest(body),
                }
            )
        except Exception as error:
            entries.append(
                {
                    "name": name,
                    "url": url,
                    "status": "failed_with_evidence",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
    receipt = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "country_area_id": "VIR",
        "files": entries,
        "scope_limit": (
            "A direct request failure does not mean that the source, plan or legal action "
            "does not exist. Acquired official catalog bodies and failed requests remain "
            "separately identified."
        ),
    }
    (out / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "acquired": sum(row["status"] == "acquired" for row in entries),
                "failed_with_evidence": sum(
                    row["status"] != "acquired" for row in entries
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

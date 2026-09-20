#!/usr/bin/env python3
"""Acquire Puerto Rico official context, planning and budget source bodies."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "eia_customers_2024.html": "https://www.eia.gov/electricity/annual/table.php?t=epa_12_01.html",
    "pr_health_obesity_action_plan.pdf": "https://www.salud.pr.gov/CMS/DOWNLOAD/10416",
    "planning_physical.html": "https://www.jp.pr.gov/planificacion-fisica",
    "planning_regulation_24.pdf": "https://jp.pr.gov/wp-content/uploads/2021/06/reg24.pdf",
    "planning_cayey_final.pdf": "https://jp.pr.gov/wp-content/uploads/2026/04/JP-PT-70-05-Plan-Final.pdf",
    "budget_municipal.html": "https://www.ogp.pr.gov/ogp/gerencia-municipal",
    "essential_services.html": "https://www.ogp.pr.gov/ogp/servicios-esenciales",
    "census_prcs.html": "https://www.census.gov/library/stories/2025/05/puerto-rico-community-survey.html",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, url in SOURCES.items():
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.10.2 source collector", "Accept-Language": "en,es;q=0.9"})
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read()
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
            (out / name).write_bytes(body)
            entries.append({"name": name, "url": url, "final_url": final_url, "status": "acquired", "content_type": content_type, "bytes": len(body), "sha256": digest(body)})
        except Exception as error:
            entries.append({"name": name, "url": url, "status": "failed_with_evidence", "error": f"{type(error).__name__}: {error}"})
    receipt = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "PRI", "files": entries, "scope_limit": "A direct request failure does not mean that the source or planning activity does not exist. Indexed official pages and acquired catalog bodies remain separately identified."}
    (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(row["status"] == "acquired" for row in entries), "failed_with_evidence": sum(row["status"] != "acquired" for row in entries)}, indent=2))


if __name__ == "__main__":
    main()

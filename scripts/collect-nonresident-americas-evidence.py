#!/usr/bin/env python3
"""Acquire official evidence for nonresident Americas M49 areas."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "bvt-npolar-overview.html": "https://npolar.no/en/themes/bouvetoya/",
    "bvt-seasonal-station.html": "https://npolar.no/en/norvegia/",
    "bvt-reserve-regulations.html": "https://npolar.no/en/regulations-bouvetoya-nature-reserve/",
    "bvt-government-conservation.html": "https://www.regjeringen.no/en/documents/meld.-st.-29-20202021/id2843433/?ch=3",
    "bvt-uninhabited-source.pdf": "https://brage.npolar.no/npolar-xmlui/bitstream/handle/11250/173650/Skrifter175.pdf?isAllowed=y&sequence=1",
    "bvt-ssb-regional-classification.pdf": "https://www.ssb.no/offentlig-sektor/offentlig-forvaltning/artikler/regionale-inndelinger-2020/_/attachment/inline/33ea12e7-3c8e-4a1e-be0b-cfd6ca476b66%3A083a78030f49bbe43587436b9713748301e15506/NOT%202021-29_web.pdf",
    "sgs-faq.html": "https://gov.gs/frequently-asked-questions/",
    "sgs-about.html": "https://gov.gs/about-sgssi/",
    "sgs-stewardship.html": "https://gov.gs/stewardship-framework-for-sgssi/",
    "sgs-marine-protected-area.html": "https://gov.gs/marine-protected-area/",
    "sgs-gazettes.html": "https://laws.gov.gs/gazettes/",
    "sgs-terrestrial-plan.pdf": "https://www.gov.gs/wp-content/uploads/2023/10/TPA-management-plan-FINAL-.pdf",
    "sgs-marine-plan-2026.pdf": "https://gov.gs/wp-content/uploads/2026/03/SGSSI-MPA-Management-Plan-2026_website.pdf",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url in SOURCES.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.10.2 source collector", "Accept-Language": "en;q=0.9,nb;q=0.8"})
            with urllib.request.urlopen(req, timeout=120) as response:
                body = response.read()
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
            (out / name).write_bytes(body)
            rows.append({"name": name, "url": url, "final_url": final_url, "status": "acquired", "content_type": content_type, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        except Exception as error:
            rows.append({"name": name, "url": url, "status": "failed_with_evidence", "error": f"{type(error).__name__}: {error}"})
    receipt = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_ids": ["BVT", "SGS"], "files": rows, "scope_limit": "No-permanent-resident status is distinct from the number of temporary officials, scientists or visitors present. Structural inapplicability applies only to resident Census and municipal-planning fields and does not imply that environmental management or government activity is absent."}
    (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(row["status"] == "acquired" for row in rows), "failed_with_evidence": sum(row["status"] != "acquired" for row in rows)}, indent=2))


if __name__ == "__main__":
    main()

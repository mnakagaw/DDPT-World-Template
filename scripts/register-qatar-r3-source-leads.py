#!/usr/bin/env python3
"""Register public official Qatar R3 locations without adopting plan contents."""

import argparse
import hashlib
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--pdf-run", required=True)
parser.add_argument("--legal-run", required=True)
args = parser.parse_args()
project = Path(args.project).resolve(strict=True)
pdf_dir = project / "raw/qatar-r3-plan-pdfs" / args.pdf_run
legal_dir = project / "raw/qatar-r3-legal" / args.legal_run
pdf_manifest = json.loads((pdf_dir / "manifest.json").read_text(encoding="utf-8-sig"))
legal_manifest = json.loads((legal_dir / "manifest.json").read_text(encoding="utf-8-sig"))
path = project / "data/dashboard.json"
dataset = json.loads(path.read_text(encoding="utf-8"))
if dataset["country"]["id"] != "QAT":
    raise SystemExit("Wrong country dataset")
existing = {source["id"]: source for source in dataset["sources"]}


def verified_raw(directory, receipt):
    raw = (directory / receipt["file"]).read_bytes()
    if receipt["status"] != "acquired" or len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        raise SystemExit(f"Raw source receipt mismatch: {receipt['file']}")
    return str((directory / receipt["file"]).relative_to(project)).replace("\\", "/")


new_sources = []
for receipt in pdf_manifest["receipts"]:
    relative = verified_raw(pdf_dir, receipt)
    municipality = receipt["municipality_panel"]
    zoning = "zoning" in receipt["file"]
    if municipality == "doha" and not zoning:
        continue  # Already registered in R2 with this URL.
    source_id = f"qat-mm-{municipality}-" + (f"zoning-{receipt['panel_link_ordinal']}" if zoning else "msdp-volume1")
    new_sources.append({
        "id": source_id,
        "name": f"QNMP {municipality} " + ("November 2017 zoning map" if zoning else "Municipality Vision and Development Strategy Volume 1"),
        "url": receipt["url"],
        "publisher": "Ministry of Municipality (Qatar), Qatar National Master Plan",
        "reference_period": "November 2017 map" if zoning else "Historical MSDP Volume 1; content date differs by municipality",
        "geographic_level": f"{municipality} municipality or historical plan area",
        "status": "partial", "retrieved_at": receipt["retrieved_at"],
        "raw_path": relative, "sha256": receipt["sha256"],
        "license": ("Map copyright notice requires express UPDS permission to reproduce; link only" if zoning
                    else "PDF reuse rights for republication not verified; link only"),
        "note": ("Official map PDF acquired. Current operative map, boundary correspondence and re-use permission are not established. No map bytes transferred to Kit or public hosting."
                 if zoning else "Official historical Volume 1 PDF acquired; current revision, approval, planning area, budget, actual implementation and evaluation remain unverified. Not adopted as an operative planning document."),
    })

law = next(r for r in legal_manifest["receipts"] if r["file"] == "resolution-109-2024.html")
new_sources.append({
    "id": "qat-law-wakra-boundary-109-2024",
    "name": "Ministerial Resolution 109 of 2024 changing Al Wakra Municipality boundary",
    "url": law["url"], "publisher": "Qatar Al Meezan legal portal / Ministry of Municipality",
    "reference_period": "Effective 2024-05-30; Gazette 2024-07-10",
    "geographic_level": "Al Wakra municipality legal boundary; annex map and coordinates",
    "status": "partial", "retrieved_at": law["retrieved_at"],
    "raw_path": verified_raw(legal_dir, law), "sha256": law["sha256"],
    "license": "Official legal page; map/image republication terms not established; link only",
    "note": "Article 1 amends Al Wakra boundary using attached map/coordinates, effective on issue under Article 3. Gazette page and annex inspected. Current GIS polygon versus annex not georeferenced; do not transfer Census 2020 values to current boundary.",
})

urls = {source["url"] for source in dataset["sources"]}
for source in new_sources:
    if source["id"] in existing:
        if existing[source["id"]] != source:
            raise SystemExit(f"Existing source ID differs: {source['id']}")
    elif source["url"] in urls:
        raise SystemExit(f"Duplicate source URL: {source['url']}")
    else:
        dataset["sources"].append(source)
        urls.add(source["url"])
path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"new_locations": len(new_sources), "total_dataset_sources": len(dataset["sources"]),
                  "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))

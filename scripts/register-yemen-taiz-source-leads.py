"""Register acquired Yemen/Taiz sources without silently adopting data."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


YEARBOOK_SHA256 = "9781f9ea9c4a186bba726b42e994fbb72021c72290bbac09db91bd20c6f34504"
PROGRESS_SHA256 = "2a924ead6b1c958016e05a38a3a43c74fe43ab289c8047b5a87e1b1ddd5aeca9"


def checked_receipt(project, name, expected_hash):
    raw = project / name
    receipt = json.loads((project / f"{name}.receipt.json").read_text(encoding="utf-8"))
    if (hashlib.sha256(raw.read_bytes()).hexdigest() != expected_hash or
            receipt["sha256"] != expected_hash or receipt["status"] != "acquired"):
        raise ValueError(f"Original/receipt changed: {name}")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "YEM":
        raise ValueError("Expected Yemen candidate")
    yearbook = checked_receipt(project, "raw/taiz-cso-2024/taiz-cso-statistical-yearbook-2024.pdf", YEARBOOK_SHA256)
    progress = checked_receipt(project, "raw/taiz-planning-2024/taiz-2024-progress-2025-priorities.pdf", PROGRESS_SHA256)
    archive = json.loads((project / "raw/ihsn-cso-2004/acquisition.json").read_text(encoding="utf-8"))
    if len(archive["resources"]) != 3 or any(item["status"] != "acquired" for item in archive["resources"]):
        raise ValueError("CSO-authored IHSN tables not fully acquired")
    for item in archive["resources"]:
        if hashlib.sha256((project / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("IHSN table original differs from receipt")
    sources = [
        {"id": "yem-ihsn-cso-2004-census-table-archive",
         "name": "IHSN archive of Yemen CSO 2004 census tables 1-3",
         "url": archive["catalogue_url"], "publisher": "IHSN archive; Yemen CSO-authored PDFs",
         "reference_period": "2004", "geographic_level": "national and governorate where published",
         "status": "partial", "retrieved_at": archive["checked_at"],
         "license": "terms_review_required",
         "note": "Archived CSO-authored material: Table 1 covers housing; Tables 2-3 are employment sample population tables, not whole-population census counts. The 2004 geography is not 2017 reference geometry."},
        {"id": "yem-taiz-cso-statistical-yearbook-2024",
         "name": "Taiz Governorate Statistical Yearbook 2024, seventh edition",
         "url": yearbook["source_url"], "publisher": "Central Statistical Organization, Taiz branch",
         "reference_period": "2024", "geographic_level": "Taiz governorate and 23 printed districts",
         "status": "ready", "retrieved_at": yearbook["checked_at"],
         "sha256": YEARBOOK_SHA256, "raw_path": yearbook["path"],
         "license": "terms_review_required",
         "note": "314-page local yearbook. PDF pages 39, 42 and 43 were checked. District population and household sums differ from printed governorate totals; sex labels conflict with page 39. No observations adopted or official boundary/code crosswalk verified."},
        {"id": "yem-taiz-mopic-progress-2024-priorities-2025",
         "name": "Taiz planning office 2024 progress and 2025 priorities presentation",
         "url": progress["source_url"],
         "publisher": "Taiz Governorate Planning and International Cooperation Office",
         "reference_period": "2024 report; 2025 priorities; 2024-2026 plan",
         "geographic_level": "Taiz governorate",
         "status": "ready", "retrieved_at": progress["retrieved_at"],
         "sha256": PROGRESS_SHA256, "raw_path": progress["path"],
         "license": "terms_review_required",
         "note": "22-page presentation checks 2024 implemented versus ongoing project counts and 2025 priorities. Costs are estimated USD, not approved budgets or actual expenditure; no official approval or legal-boundary match inferred."},
    ]
    existing = {source["id"] for source in dataset["sources"]}
    if existing.intersection(source["id"] for source in sources):
        raise ValueError("Source lead is already registered")
    dataset["sources"].extend(sources)
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["yemen-taiz-source-location-audit-2024"]))
    for gap in dataset["gaps"]:
        if gap["category"] == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = ("A Taiz branch 2024 yearbook and three CSO-authored 2004 archive tables were acquired. "
                             "The 23 Taiz district 2024 population and household rows have printed-total discrepancies, "
                             "and sex-labelled totals conflict across pages. No local observation has been adopted.")
            gap["next_action"] = ("Resolve source table discrepancies with the publisher, inventory all yearbook fields, "
                                  "then obtain official district codes and versioned boundaries before district adoption.")
        elif gap["category"] == "planning_documents":
            gap["status"] = "partial"
            gap["detail"] = ("The Taiz planning office's 2024 progress/2025 priorities presentation was acquired and selected slides checked. "
                             "It is not the complete plan, an approved budget, actual expenditure or official evaluation. "
                             "No Taiz document is attributed to a territory until a verified source-entity match is recorded.")
            gap["next_action"] = ("Acquire the full Taiz 2024-2026 plan and legally relevant unit/code register; "
                                  "separate 2024 implementation, 2025 priorities, budgets, execution and evaluations.")
    dataset["generated_at"] = datetime.now(timezone.utc).isoformat()
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources_added": len(sources), "observations_added": 0, "documents_added": 0}))


if __name__ == "__main__":
    main()

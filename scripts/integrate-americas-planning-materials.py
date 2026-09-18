#!/usr/bin/env python3
"""Expose the acquired Belize and Guatemala planning references in AreaData."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LABELS = {
    "horizon-2030-legal-framework": ("Horizon 2030 national development framework", "plan", None),
    "government-elibrary": ("Belize Government e-library", "reference", None),
    "national-plans-catalog": ("Belize national plans catalogue", "reference", None),
    "approved-budget-2025-2026": ("Approved Estimates of Revenue and Expenditure 2025-2026", "budget", "2025-2026"),
    "budget-catalog": ("Belize approved estimates catalogue", "budget", None),
    "municipal-code-detail": ("Guatemala Municipal Code, Decreto 12-2002 (official record)", "reference", None),
    "municipal-code-pdf": ("Guatemala Municipal Code, Decreto 12-2002 (official PDF)", "reference", None),
    "pdm-ot-implementation-guide": ("SEGEPLAN guide for implementation of PDM-OT", "reference", None),
    "municipal-plan-catalog": ("SEGEPLAN municipal development and territorial plans catalogue", "plan", None),
    "municipal-budget-catalog": ("MINFIN municipal budget data catalogue", "budget", None),
    "municipal-ranking-package": ("SEGEPLAN municipal management ranking package 2020-2021", "evaluation", "2020-2021"),
    "municipal-ranking-csv": ("SEGEPLAN municipal management ranking data 2020-2021", "evaluation", "2020-2021"),
}

PUBLISHERS = {
    "BLZ": "Government of Belize",
    "GTM": "Government of Guatemala",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    data_path = project / "data/dashboard.json"
    receipt_path = project / "raw/supplemental-country-sources/receipt.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))

    source_ids = {source["id"] for source in data["sources"]}
    document_ids = {document["id"] for document in data["documents"]}
    added_sources = 0
    added_documents = 0
    for row in receipt["receipts"]:
        if row["id"] not in LABELS:
            continue
        title, category, period = LABELS[row["id"]]
        source_id = f"{row['country_area_id']}_PLANNING_{row['id'].upper().replace('-', '_')}"
        if source_id not in source_ids:
            source = {
                "id": source_id,
                "name": title,
                "publisher": PUBLISHERS[row["country_area_id"]],
                "url": row["url"],
                "status": "ready" if row["status"] == "acquired" else "partial",
                "retrieved_at": row.get("completed_at"),
                "license": "Reuse terms not verified; AreaData links to the official source and does not redistribute the original through the public site.",
                "note": (
                    "Official planning reference acquired and retained with a content hash."
                    if row["status"] == "acquired"
                    else "Official URL retained; the automated acquisition failure is recorded in the supplemental receipt."
                ),
            }
            if row["status"] == "acquired":
                source.update({"raw_path": row["path"], "sha256": row["sha256"]})
            data["sources"].append(source)
            source_ids.add(source_id)
            added_sources += 1
        else:
            next(source for source in data["sources"] if source["id"] == source_id).setdefault(
                "license",
                "Reuse terms not verified; AreaData links to the official source and does not redistribute the original through the public site.",
            )
        document_id = f"{row['country_area_id'].lower()}-{row['id']}"
        if document_id in document_ids:
            continue
        document = {
            "id": document_id,
            "territory_id": row["country_area_id"],
            "category": category,
            "title": title,
            "kind": "official-reference",
            "url": row["url"],
            "availability": "body_acquired" if row["status"] == "acquired" else "failed",
            "official_status": "unverified",
            "source_id": source_id,
        }
        if period:
            document["period"] = period
            document["target_period"] = {"label": period, "kind": "multi_year"}
        data["documents"].append(document)
        document_ids.add(document_id)
        added_documents += 1

    data["planning"] = {
        "title": "Planning laws, plans and implementation resources",
        "purpose": "Review the official materials collected for the selected country or area and prepare an evidence base without treating a link, acquisition or catalogue entry as proof of approval or implementation.",
        "sections": [
            {"id": "plan", "label": "Development plans"},
            {"id": "budget", "label": "Budgets and annual plans"},
            {"id": "implementation", "label": "Implementation and financial results"},
            {"id": "evaluation", "label": "Official assessments"},
            {"id": "reference", "label": "Laws, guidance and catalogues"},
        ],
        "outputs": ["markdown", "html", "evidence_csv", "documents_csv"],
        "map": {"mode": "coverage"},
        "update": {
            "status": "current",
            "message": "Belize and Guatemala planning references were checked for this release; other country and area records retain explicit source-audit gaps.",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "last_success_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added_sources": added_sources, "added_documents": added_documents, "document_count": len(data["documents"])}, indent=2))


if __name__ == "__main__":
    main()

"""Adopt the verified national plan as a country document, not a governorate plan."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


FILENAME = "iraq-national-development-plan-2024-2028.pdf"
PDF_SHA256 = "db54c12c6c096ec3338b2ee38d2737b5b091554701e14ced6231d8fa464c9f84"
SOURCE_ID = "irq-mop-national-development-plan-2024-2028"
DOCUMENT_ID = "irq-national-development-plan-2024-2028"


def pdf_page(path, page):
    output = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page),
                             "-layout", "-enc", "UTF-8", str(path), "-"],
                            capture_output=True, check=True)
    return output.stdout.decode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    pdf = project / "raw" / FILENAME
    receipt = json.loads((project / "raw" / f"{FILENAME}.receipt.json").read_text(encoding="utf-8"))
    if (hashlib.sha256(pdf.read_bytes()).hexdigest() != PDF_SHA256 or
            receipt["sha256"] != PDF_SHA256 or receipt["source_url"] !=
            "https://www.mop.gov.iq/documents/economic-policies/development-plans/National%20Development%20Plan%202024-2028.pdf"):
        raise ValueError("National plan PDF or acquisition receipt differs from pinned official source")
    cover = pdf_page(pdf, 1)
    publication = pdf_page(pdf, 2)
    spatial = pdf_page(pdf, 157)
    for phrase in ["Republic of Iraq", "The Ministry of Planning", "National Development Plan", "2024-2028"]:
        if phrase not in cover:
            raise ValueError(f"Cover does not contain {phrase}")
    if "May 2024" not in publication:
        raise ValueError("Plan publication page changed")
    for phrase in ["Program to promote spatial", "development and optimize",
                   "Ring roads 4 in Baghdad governorate",
                   "Baghdad-Amara railway", "Ministry of Transport"]:
        if phrase not in spatial:
            raise ValueError(f"Printed page 156 does not contain {phrase}")
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "IRQ" or any(item["id"] == DOCUMENT_ID for item in dataset["documents"]):
        raise ValueError("Expected Iraq candidate before national-plan import")
    national = next(item for item in dataset["territories"] if item["id"] == "IRQ")
    checked_at = datetime.now(timezone.utc).isoformat()
    evidence = {"source_id": SOURCE_ID,
                "locator": "PDF page 157, printed page 156; cover PDF pages 1-2",
                "checked_at": checked_at, "authority": "Republic of Iraq, Ministry of Planning"}
    dataset["sources"].append({"id": SOURCE_ID,
        "name": "Republic of Iraq National Development Plan 2024-2028",
        "url": receipt["source_url"], "publisher": "Iraq Ministry of Planning",
        "reference_period": "2024-2028", "geographic_level": "national plan",
        "status": "ready", "retrieved_at": receipt["retrieved_at"], "sha256": PDF_SHA256,
        "raw_path": f"raw/{FILENAME}", "license": "terms_review_required",
        "note": "The national plan is verified only for cover, publication and selected spatial-programme page; it is not a Baghdad governorate plan, budget, implementation result or evaluation."})
    dataset["documents"].append({"id": DOCUMENT_ID,
        "territory_id": "IRQ", "category": "plan", "kind": "plan",
        "title": "National Development Plan 2024-2028 (Republic of Iraq)",
        "url": receipt["source_url"], "period": "2024-2028",
        "target_period": {"label": "2024-2028", "kind": "multi_year"},
        "availability": "content_verified", "official_status": "unverified",
        "source_id": SOURCE_ID,
        "territory_match": {"territory_id": "IRQ", "country_id": "IRQ",
            "type": national["type"], "code_system": national["code_system"],
            "official_code": national["official_code"],
            "boundary_version": national["boundary_version"],
            "method": "The official ministry PDF cover explicitly names the Republic of Iraq and a national development plan. Its Baghdad references are nationally proposed activities, not a verified governorate plan.",
            "source_id": SOURCE_ID, "locator": "PDF pages 1-2 title and publisher; PDF page 157 / printed page 156 spatial programme",
            "checked_at": checked_at},
        "content": {"summary": "The Ministry of Planning's national 2024-2028 plan includes a programme to promote spatial development and the comparative advantages of governorates. A checked programme page lists suggested transport activities for Baghdad and identifies executing ministries; it does not report their completion.",
                    "priorities": ["Promote spatial development across governorates"],
                    "evidence": evidence}})
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap["status"] = "partial"
            gap["detail"] = ("The official 2024-2028 National Development Plan is adopted as a country document. "
                             "No governorate-specific plan, budget, implementation report or evaluation is adopted; national suggested activities are not local approvals or actual expenditure.")
            gap["next_action"] = ("Find current governorate plans and the legal planning unit, then acquire and verify "
                                  "their budget, execution and evaluation records separately.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                   ["iraq-mop-national-development-plan-2024-2028"]))
    audit = {"country": "IRQ", "checked_at": checked_at, "pdf_sha256": PDF_SHA256,
             "pdf_pages": 180, "checked_pages": [1, 2, 157],
             "printed_page": 156, "document_territory_id": "IRQ",
             "document_period": "2024-2028", "document_availability": "content_verified_selected_pages",
             "official_approval_state": "unverified",
             "plan_claim": "National suggested activities, not verified governorate plan or implementation",
             "not_adopted": ["Baghdad governorate plan", "governorate budgets", "project execution",
                             "official evaluations", "unreviewed pages and programme rows"]}
    (project / "evidence/MOP_NDP_2024_2028_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents_added": 1, "territory": "IRQ", "checked_pdf_pages": [1, 2, 157]}))


if __name__ == "__main__":
    main()

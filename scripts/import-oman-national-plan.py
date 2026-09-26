"""Attach checked pages of Oman's adopted national plan to the national area only."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RELATIVE = "raw/oman-ecensus-moi/oman-eleventh-five-year-plan-2026-2030.pdf"
PDF_SHA256 = "66362a395113a6db83acdf1c1a6887635a69df6bca66fad077bffca5dea6a58b"
SOURCE_ID = "omn-moe-eleventh-five-year-plan-2026-2030"
STATUS_SOURCE_ID = "omn-fm-royal-decree-1-2026-plan-announcement"
DOCUMENT_ID = "omn-eleventh-five-year-national-plan-2026-2030"
STATUS_URL = "https://www.fm.gov.om/en/about-oman/state/economy/"


def page_text(pdf, page):
    output = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page),
                             "-layout", "-enc", "UTF-8", str(pdf), "-"],
                            capture_output=True, check=True)
    return output.stdout.decode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    pdf = project / RELATIVE
    receipt = json.loads((project / (RELATIVE + ".receipt.json")).read_text(encoding="utf-8"))
    if (hashlib.sha256(pdf.read_bytes()).hexdigest() != PDF_SHA256 or
            receipt["sha256"] != PDF_SHA256 or
            receipt["source_url"] != "https://www.economy.gov.om/PDF/خطة التنمية الخمسية الحادية عشرة.pdf"):
        raise ValueError("Official plan PDF or receipt differs from pinned original")
    cover = page_text(pdf, 1)
    contents = page_text(pdf, 6)
    national = page_text(pdf, 16)
    governorates = page_text(pdf, 50)
    if "2040" not in cover or "الخطة التنفيذية الثانية" not in cover or \
            "خطة التنمية الخمسية الحادية عشرة" not in contents or \
            "2026" not in national or "2030" not in national or \
            "التنمية المتوازنة بين المحافظات" not in governorates:
        raise ValueError("Checked plan pages no longer support national period/geography summary")
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "OMN" or any(item["id"] == DOCUMENT_ID for item in dataset["documents"]):
        raise ValueError("Expected Oman candidate before plan import")
    nation = next(item for item in dataset["territories"] if item["id"] == "OMN")
    checked_at = datetime.now(timezone.utc).isoformat()
    dataset["sources"].extend([
        {"id": SOURCE_ID, "name": "Oman Eleventh Five-Year Development Plan, main Arabic volume",
         "url": receipt["source_url"], "publisher": "Ministry of Economy (Oman)",
         "reference_period": "2026-2030", "geographic_level": "national plan; governorate development priority, not 11 local plan documents",
         "status": "ready", "retrieved_at": receipt["retrieved_at"], "sha256": PDF_SHA256,
         "raw_path": RELATIVE, "license": "terms_review_required",
         "note": "124-page official PDF acquired. Cover, contents, introduction page 16 and governorate-development page 50 were checked; other pages, programme annexes and all governorate-specific implementations are not adopted here."},
        {"id": STATUS_SOURCE_ID, "name": "Foreign Ministry economy page naming Royal Decree 1/2026",
         "url": STATUS_URL, "publisher": "Ministry of Foreign Affairs (Oman)",
         "reference_period": "2026-2030 national plan approval", "geographic_level": "national",
         "status": "partial", "retrieved_at": checked_at, "license": "terms_review_required",
         "note": "Official government page says the Eleventh Five-Year Development Plan was launched through Royal Decree 1/2026. The Gazette's original decree was located separately; no governorate-plan approval is inferred."},
    ])
    dataset["documents"].append({
        "id": DOCUMENT_ID, "territory_id": "OMN", "category": "plan", "kind": "plan",
        "title": "Eleventh Five-Year Development Plan 2026–2030 (national, main Arabic volume)",
        "url": receipt["source_url"], "period": "2026-2030",
        "target_period": {"label": "2026-2030", "kind": "multi_year"},
        "availability": "content_verified", "official_status": "adopted_national",
        "official_evidence": {"source_id": STATUS_SOURCE_ID,
            "locator": "Official Economy page, paragraph naming launch through Royal Decree 1/2026",
            "checked_at": checked_at, "authority": "Ministry of Foreign Affairs (Oman)"},
        "source_id": SOURCE_ID,
        "territory_match": {"territory_id": "OMN", "country_id": "OMN",
            "type": nation["type"], "code_system": nation["code_system"],
            "official_code": nation["official_code"], "boundary_version": nation["boundary_version"],
            "method": "Ministry of Economy PDF identifies an Oman national development plan; its governorate discussion is a national priority, not a verified separate governorate plan.",
            "source_id": SOURCE_ID, "locator": "PDF cover, contents page 6, national introduction page 16, balanced governorate development page 50",
            "checked_at": checked_at},
        "content": {"summary": "The official national 2026–2030 plan is the second implementation plan for Oman Vision 2040. A checked chapter discusses balanced development among governorates. Its historical programme figures on page 50 refer to the prior period and are not attached as current local budgets or implementation results.",
            "priorities": ["Balanced development among governorates"],
            "evidence": {"source_id": SOURCE_ID,
                "locator": "PDF page 16 (national plan period/role) and page 50 (balanced governorate development)",
                "checked_at": checked_at, "authority": "Ministry of Economy (Oman)"}},
    })
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Ministry of Economy's adopted national 2026–2030 plan is attached to Oman; selected PDF pages were checked. No governorate- or wilayat-specific plan, budget, actual spending or evaluation has been linked to a verified local planning unit.",
                       next_action="Audit full plan/strategic-programme volumes, current planning law and governorate development plans; acquire local budget, execution and evaluation originals with dated territorial matches.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                   ["oman-moe-national-plan-2026-2030-partial"]))
    dataset["generated_at"] = checked_at
    audit = {"status": "national_plan_selected_pages_verified_local_planning_open",
             "checked_at": checked_at, "pdf_sha256": PDF_SHA256, "pdf_pages": 124,
             "checked_pdf_pages": [1, 6, 16, 50], "document_territory_id": "OMN",
             "plan_period": "2026-2030", "approval_source_url": STATUS_URL,
             "not_adopted": ["individual governorate or wilayat plans", "local budget allocations",
                             "actual expenditure", "implementation progress", "official evaluation",
                             "unread main-volume pages and programme annexes"]}
    (project / "evidence/OMN_NATIONAL_PLAN_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents_added": 1, "territory": "OMN", "checked_pdf_pages": [1, 6, 16, 50]}))


if __name__ == "__main__":
    main()

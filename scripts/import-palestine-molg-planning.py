"""Attach checked Ministry of Local Government strategy and town-planning guide nationally."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RAW = "raw/palestine-molg-planning/"
FILES = (
    ("molg-local-development-planning-guide.pdf", "27fbc38788da1bd1d0554fffbdf68ee831cbf415c1a407d5112d9e7f360bb210"),
    ("molg-local-government-sector-strategy-2025-2027.pdf", "ec7d2dbf55526fc5d523b62e804e28570c1aed88240f308a796fa60956b7be54"),
)
GUIDE_SOURCE = "pse-molg-sdip-towns-guide-2018"
PLAN_SOURCE = "pse-molg-sector-strategy-2025-2027"


def page_text(pdf, number):
    return subprocess.check_output(["pdftotext", "-f", str(number), "-l", str(number),
                                    "-layout", "-enc", "UTF-8", str(pdf), "-"]).decode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    originals = {}
    for name, expected in FILES:
        relative = RAW + name
        pdf = project / relative
        receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != expected or \
                receipt["sha256"] != expected or receipt["status"] != "acquired":
            raise ValueError(f"Ministry planning original or receipt changed: {name}")
        originals[name] = (pdf, receipt)
    guide = originals[FILES[0][0]][0]
    plan = originals[FILES[1][0]][0]
    if "2018" not in page_text(guide, 1) or "2018" not in page_text(guide, 2) or \
            "SDIP" not in page_text(guide, 1) or \
            "2027" not in page_text(plan, 1) or "2025" not in page_text(plan, 1) or \
            "2027" not in page_text(plan, 5) or "2025" not in page_text(plan, 5):
        raise ValueError("Checked Ministry title, edition or plan-period pages changed")
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "PSE" or dataset["documents"]:
        raise ValueError("Expected PCBS-improved PSE candidate with no attached planning documents")
    nation = next(item for item in dataset["territories"] if item["id"] == "PSE")
    now = datetime.now(timezone.utc).isoformat()
    specs = (
        (FILES[0][0], GUIDE_SOURCE, "Ministry of Local Government 2018 local development planning guide for Palestinian cities and towns",
         "National methodology for city/town local government units; not a governorate or municipal plan document",
         "reference", "planning_guidance", "2018", {"label": "2018", "kind": "as_of"},
         "Official 2018 third-edition SDIP methodology for Palestinian cities and towns. It names Ministry of Local Government and other contributors. It does not establish the approval or present status of any individual city, town or governorate plan.",
         "PDF pages 1-2: 2018 cover, title, third-edition preparation history"),
        (FILES[1][0], PLAN_SOURCE, "Ministry of Local Government sector strategy 2025–2027",
         "National ministry sector strategy; not 16 governorate strategies or individual local-government plans",
         "plan", "sector_strategy", "2025-2027", {"label": "2025-2027", "kind": "multi_year"},
         "Published Ministry of Local Government 2025–2027 sector strategy. Checked cover, contents and executive-summary pages describe local-government performance, services, governance, sustainability, public participation and post-crisis recovery. Budget and monitoring chapters are listed in contents; no budget amount, spending result or achieved outcome is adopted here.",
         "PDF pages 1-5, 51 and 55: cover, contents, executive summary and selected strategic-results/intervention pages"),
    )
    for name, source_id, title, geographic_level, category, kind, period, target_period, summary, locator in specs:
        _, receipt = originals[name]
        dataset["sources"].append({
            "id": source_id, "name": title, "url": receipt["source_url"],
            "publisher": "Ministry of Local Government (Palestine)",
            "reference_period": period, "geographic_level": geographic_level,
            "status": "ready", "retrieved_at": receipt["retrieved_at"],
            "raw_path": RAW + name, "sha256": receipt["sha256"],
            "license": "official_publication_redistribution_terms_review_required",
            "note": "Selected pages checked only. This original is a national-level sector or methodology reference; it is not evidence of a specific governorate or city plan's adoption, budget execution or evaluation.",
        })
        dataset["documents"].append({
            "id": source_id + "-document", "territory_id": "PSE", "category": category,
            "kind": kind, "title": title, "url": receipt["source_url"], "period": period,
            "target_period": target_period, "availability": "content_verified",
            "official_status": "unknown", "source_id": source_id,
            "territory_match": {
                "territory_id": "PSE", "country_id": "PSE", "type": nation["type"],
                "code_system": nation["code_system"], "official_code": nation["official_code"],
                "boundary_version": nation["boundary_version"],
                "method": "Ministry PDF is national sector/methodology material; its text does not verify a specific local planning unit or individual local plan.",
                "source_id": source_id, "locator": locator, "checked_at": now,
            },
            "content": {"summary": summary,
                "evidence": {"source_id": source_id, "locator": locator,
                             "checked_at": now, "authority": "Ministry of Local Government (Palestine)"}},
        })
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Acquired and checked selected pages of a 2018 Ministry city/town planning guide and the published 2025–2027 national local-government sector strategy. Both are attached only to the national context. No current governorate or municipal plan, adopted local budget, actual expenditure or evaluation is verified.",
                       next_action="Determine current legal planning duties for governorates, municipalities and village councils; acquire individual plan originals and dated approval/budget/execution evidence by official area/code.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["palestine-molg-planning-national-reference-partial"]))
    dataset["generated_at"] = now
    audit = {"status": "selected_national_molg_pages_verified_local_planning_open", "checked_at": now,
             "guide_sha256": FILES[0][1], "guide_pages": 149, "guide_checked_pdf_pages": [1, 2],
             "sector_strategy_sha256": FILES[1][1], "sector_strategy_pages": 171,
             "sector_strategy_checked_pdf_pages": [1, 2, 5, 51, 55],
             "document_territory_id": "PSE", "local_documents_attached": 0,
             "not_adopted": ["governorate or city plans", "individual legal approval status",
                             "national strategy budget amounts as local budgets", "actual expenditures",
                             "implementation or evaluation results", "unchecked PDF content"]}
    (project / "evidence/PSE_MOLG_PLANNING_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents_added": 2, "territory": "PSE", "local_documents": 0,
                      "checked_pdf_pages": {"guide": [1, 2], "strategy": [1, 2, 5, 51, 55]}}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify pinned QNMP panel PDFs and record their limited documentary roles."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--pdf-run", required=True)
parser.add_argument("--page-inspection", required=True)
args = parser.parse_args()
project = Path(args.project).resolve(strict=True)
directory = project / "raw/qatar-r3-plan-pdfs" / args.pdf_run
manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8-sig"))
inspection = json.loads(Path(args.page_inspection).resolve(strict=True).read_text(encoding="utf-8"))
links_by_panel = {e["file"].removeprefix("msdp-").removesuffix(".html"): e.get("pdf_links", [])
                  for e in inspection["entries"] if e["file"].startswith("msdp-")}
if len(links_by_panel) != 8 or len(manifest["receipts"]) != 12:
    raise SystemExit("Expected eight panels and twelve PDF links")

documents = []
for receipt in manifest["receipts"]:
    if receipt["status"] != "acquired":
        raise SystemExit(f"Missing plan original: {receipt['url']}")
    path = directory / receipt["file"]
    raw = path.read_bytes()
    if not raw.startswith(b"%PDF-") or len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        raise SystemExit(f"PDF receipt mismatch: {path}")
    txt_path = path.with_suffix(".txt")
    if not txt_path.exists():
        raise SystemExit(f"Extracted text missing: {txt_path}")
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    normalized = " ".join(text.split())
    info = subprocess.check_output(["pdfinfo", str(path)], text=True, errors="replace")
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    zoning = "zoning" in receipt["file"]
    entry = {
        "municipality_panel": receipt["municipality_panel"],
        "document_type": "zoning_map" if zoning else "msdp_volume_1_vision_and_strategy",
        "official_url": receipt["url"],
        "local_file": str(path.relative_to(project)).replace("\\", "/"),
        "sha256": receipt["sha256"],
        "bytes": receipt["bytes"],
        "pages": pages,
        "cover_or_map_label_excerpt": normalized[:220],
        "source_date_read_from_content": (
            "November 2017" if zoning and re.search(r"November\s+2017", text, re.I)
            else "June 2014" if not zoning and re.search(r"(?:1\s+)?June\s+2014", text[:1500], re.I)
            else "undated_or_unverified"
        ),
        "publication_filename_period_is_not_document_date": True,
        "current_operative_edition": "unverified",
        "approval_for_this_municipality": "unverified",
        "budget_execution_or_evaluation_original": False,
        "reuse_status": (
            "map_reproduction_requires_express_UPDS_permission" if zoning and re.search(r"without the express permission of UPDS", text, re.I)
            else "not_verified"
        ),
    }
    if not zoning:
        entry["strategy_implementation_section_present"] = bool(re.search(r"Strategy Implementation", text, re.I))
        entry["five_year_review_rule_present"] = bool(re.search(r"reviewed every 5 years", text, re.I))
        entry["al_rayyan_and_al_shahhaniya_combined_title"] = "Al Rayyan and Al Shahhaniya Municipality" in text[:500]
    documents.append(entry)

municipalities = []
for name, links in links_by_panel.items():
    panel_docs = [d for d in documents if d["municipality_panel"] == name]
    municipalities.append({"municipality_panel": name, "official_panel_url": next(
        e["url"] for e in inspection["entries"] if e["file"] == f"msdp-{name}.html"),
                           "linked_pdf_count": len(links),
                           "strategy_pdf_count": sum(d["document_type"] == "msdp_volume_1_vision_and_strategy" for d in panel_docs),
                           "zoning_pdf_count": sum(d["document_type"] == "zoning_map" for d in panel_docs),
                           "panel_strategy_status": "Coming Soon" if name in {"khor", "sheehaniya", "wakra"} else "linked_old_volume_1",
                           "current_operative_plan": "unverified",
                           "individual_budget_execution_evaluation": "not_found_in_this_panel_or_linked_PDF_set"})

result = {
    "status": "partial_source_acquisition_not_plan_acceptance",
    "official_eight_plan_claim": "https://www.mm.gov.qa/QatarMasterPlan/English/MSDP-Municipalities.aspx?panel=about",
    "older_six_zoning_scope_statement": "https://www.mm.gov.qa/QatarMasterPlan/English/msdp-zoning.aspx",
    "scope_conflict": "The about page says eight plans completed; the older zoning page names six and treats Khor/Wakra as future; three municipality strategy panels say Coming Soon. Do not infer each currently operative plan edition from the eight-plan claim.",
    "documents": documents,
    "municipalities": municipalities,
    "no_publication_rule": "Link to official PDFs only until reuse rights are reviewed; never redistribute the zoning maps without express permission.",
}
out = project / "evidence/QAT_R3_MSDP_ORIGINALS_AUDIT.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pdfs": len(documents), "strategies": sum(d["document_type"] == "msdp_volume_1_vision_and_strategy" for d in documents),
                  "zoning_maps": sum(d["document_type"] == "zoning_map" for d in documents),
                  "no_strategy_panels": [m["municipality_panel"] for m in municipalities if not m["strategy_pdf_count"]]}, ensure_ascii=False))

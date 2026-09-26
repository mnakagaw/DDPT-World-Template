"""Add a verified national budget reference and a restricted IOM research source."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


BUDGET_ID = "syr-mof-citizen-budget-2026"
BUDGET_DOC_ID = "syr-national-citizen-budget-2026"
BUDGET_HASH = "9d460f4694527f2d8245a0869f9d3ef20b09e14eb806ddc4df4895d94f7409fd"
IOM_ID = "syr-iom-dtm-baseline-round17-june-2026"
IOM_HASH = "0243b2e01aad3a91184d697090ab060ea50f7ce4ae8619eb49f3a18a38021474"
IOM_TERMS_HASH = "d062f8f595ac0342e300ff1dea3e364c4ca375744c37e84d0a38f7e900c49717"


def checked_receipt(project, relative_path, expected_hash):
    original = project / relative_path
    receipt = json.loads((project / (relative_path + ".receipt.json")).read_text(encoding="utf-8"))
    if receipt["status"] != "acquired" or receipt["sha256"] != expected_hash:
        raise ValueError(f"Unexpected source receipt: {relative_path}")
    if hashlib.sha256(original.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f"Unexpected source bytes: {relative_path}")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    budget = checked_receipt(project, "raw/syria-mof-2026/citizen-budget-2026.pdf", BUDGET_HASH)
    iom = checked_receipt(project, "raw/syria-iom-round17/iom-dtm-syria-baseline-round17-june-2026.pdf", IOM_HASH)
    terms = checked_receipt(project, "raw/syria-iom-round17/iom-dtm-terms.html", IOM_TERMS_HASH)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "SYR":
        raise ValueError("Expected Syria project")
    if any(source["id"] in {BUDGET_ID, IOM_ID} for source in dataset["sources"]):
        raise ValueError("Sources already registered")
    if any(document["id"] == BUDGET_DOC_ID for document in dataset["documents"]):
        raise ValueError("Budget document already registered")
    before = (len(dataset["indicators"]), len(dataset["observations"]))
    checked_at = datetime.now(timezone.utc).isoformat()
    national = next(t for t in dataset["territories"] if t["id"] == "SYR")
    dataset["sources"].extend([
        {
            "id": BUDGET_ID, "name": "Citizen Budget 2026, Syrian Ministry of Finance",
            "url": budget["source_url"], "publisher": "Syrian Ministry of Finance",
            "reference_period": "2026 national budget; selected 2025 activity review",
            "geographic_level": "national; page 50 describes a target for 14 governorate plans",
            "status": "ready", "retrieved_at": budget["retrieved_at"],
            "sha256": BUDGET_HASH, "raw_path": budget["path"],
            "license": "terms_review_required",
            "note": "52-page official citizen budget. Visually checked cover, page 17 economic assumptions and page 50 planning authority activities/targets. The 14 local development plans are a 2026 preparation target, not completed or approved plans. No governorate budget or execution value is adopted.",
        },
        {
            "id": IOM_ID, "name": "IOM DTM Syria Population Mobility and Baseline Assessment, round 17",
            "url": iom["source_url"], "catalog_url": iom["catalog_url"],
            "publisher": "International Organization for Migration, DTM Syria",
            "reference_period": "1-30 June 2026", "geographic_level": "national and governorate report table; underlying assessment spans localities",
            "status": "partial", "retrieved_at": iom["retrieved_at"],
            "sha256": IOM_HASH, "raw_path": iom["path"],
            "license": "IOM DTM terms restrict extraction and redistribution without prior written permission",
            "license_url": terms["final_url"],
            "note": "Nine-page key-informant humanitarian baseline report, not a census. A 14-governorate population/mobility table and methodology were inspected privately. No numeric value is adopted or republished because IOM DTM terms require written permission for extraction/redistribution; official code and 2017 reference-boundary correspondence are also unverified.",
        },
    ])
    evidence = {"source_id": BUDGET_ID, "locator": "PDF pages 1, 17 and 50; printed page 50 for planning target",
                "checked_at": checked_at, "authority": "Syrian Ministry of Finance"}
    dataset["documents"].append({
        "id": BUDGET_DOC_ID, "territory_id": "SYR", "category": "budget", "kind": "budget",
        "title": "Syrian Citizen Budget 2026 (national reference)",
        "url": budget["source_url"], "period": "2026",
        "target_period": {"label": "2026", "kind": "calendar_year"},
        "availability": "content_verified", "official_status": "unverified",
        "source_id": BUDGET_ID,
        "territory_match": {
            "territory_id": "SYR", "country_id": "SYR", "type": national["type"],
            "code_system": national["code_system"], "official_code": national["official_code"],
            "boundary_version": national["boundary_version"],
            "method": "The ministry cover and page 18 identify the Syrian Arab Republic and national 2026 citizen budget; no governorate budget identity is inferred.",
            "source_id": BUDGET_ID, "locator": "PDF pages 1 and 18", "checked_at": checked_at,
        },
        "content": {
            "summary": "The Ministry of Finance's citizen budget presents national 2026 fiscal context. Page 50 states an authority target to prepare 14 governorate local development plans during 2026; it does not document completion or approval of any selected governorate's plan.",
            "evidence": evidence,
        },
    })
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap["status"] = "partial"
            gap["detail"] = ("The national Ministry of Finance Citizen Budget 2026 is acquired and selected pages verified. "
                             "Its target to prepare 14 governorate local plans does not establish that any plan exists or is approved. "
                             "Governorate plans, budgets, expenditure and evaluations remain uncollected.")
            gap["next_action"] = ("Acquire the applicable planning decree/guidance and the actual plans, governorate budgets, "
                                  "implementation and evaluations; verify each document's entity and legal status.")
        elif gap["category"] == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = ("An IOM DTM June 2026 humanitarian report with a governorate table was acquired for private review, "
                             "but no value was adopted under its extraction/redistribution terms. National WDI values remain "
                             "separate. Official national census and sectoral local values are still absent.")
            gap["next_action"] = ("Locate accessible official statistical originals and current administrative codes. "
                                  "Seek IOM permission before any extraction or redistribution, and keep humanitarian "
                                  "estimates separate from census counts.")
    dataset["generated_at"] = checked_at
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                   ["syria-mof-2026-budget-reference", "syria-iom-round17-restricted-source-audit"]))
    if (len(dataset["indicators"]), len(dataset["observations"])) != before:
        raise AssertionError("Source registration unexpectedly changed indicators or observations")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "partial_official_locations_identified", "checked_at": checked_at,
        "origin_registry": "AreaData 2026-09-26 Syria source pass",
        "census": {"url": "https://psc.gov.sy/site2/arabic", "acquisition": "failed_404_on_2026-09-26",
                   "note": "Official SANA announcement linked this 2026 statistics/planning portal; the checked path returned 404. No census table acquired."},
        "planning": {"url": budget["source_url"], "document": "national Citizen Budget 2026",
                     "acquisition": "success", "governorate_plan_status": "2026 target only"},
        "sources": [
            {"id": BUDGET_ID, "url": budget["source_url"], "site_status": "ready"},
            {"id": IOM_ID, "url": iom["source_url"], "site_status": "acquired_restricted_not_adopted"},
        ],
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = ("Research status: **source_locations_not_pre_researched**\n\n"
           "No country-specific source locations are pre-researched yet. Complete the first required action below.")
    new = ("Research status: **partial_official_locations_identified** (2026-09-26).\n\n"
           "The national Ministry of Finance Citizen Budget 2026 was acquired, and its cover, economic-context page "
           "and planning target page were visually checked. It is registered as a national budget reference only. "
           "The IOM DTM June 2026 report was acquired for private review, but no value was adopted because the "
           "publisher's terms require written permission for extraction and redistribution. An official SANA link "
           "to the new Planning and Statistics Authority portal returned 404 on this check; no census table was acquired. "
           "Local statistics, current codes and boundaries, completed governorate plans, budgets, implementation and "
           "evaluation remain open. See SYR_SOURCE_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Syria source preflight Markdown")
    markdown_path.write_text(markdown.replace(old, new), encoding="utf-8")
    audit = {
        "schema_version": "1.0", "checked_at": checked_at, "country_area_id": "SYR",
        "dataset_counts": {"territories": len(dataset["territories"]), "indicators": before[0],
                           "observations": before[1], "documents": len(dataset["documents"])},
        "mof_budget": {"sha256": BUDGET_HASH, "pdf_pages": 52, "visually_checked_pages": [1, 17, 18, 50],
                       "adopted_as": "national budget reference only", "governorate_plan_status": "target_to_prepare_14_not_verified_completed"},
        "iom_report": {"sha256": IOM_HASH, "pdf_pages": 9,
                       "private_review_pages": [1, 3, 4, 5, 6, 7, 8, 9],
                       "terms_sha256": IOM_TERMS_HASH,
                       "terms_url": terms["final_url"], "observations_adopted": 0,
                       "reason": "Written permission required for extraction and redistribution; report is a humanitarian estimate, not a census; code/boundary join unverified",
                       "field_disposition": [
                           {"pages": "3-6", "fields": "national/flow/stock mobility counts and percentages", "decision": "not_adopted"},
                           {"pages": "7", "fields": "governorate name, total population, four rounded mobility-share percentages", "decision": "not_adopted"},
                           {"pages": "8", "fields": "methodology coverage and key-informant profile counts/percentages", "decision": "methodology_only_not_indicator"},
                       ]},
        "unresolved": ["official census table", "current official codes and boundaries", "legal planning unit",
                       "actual governorate plans", "local budgets", "implementation and evaluation"],
    }
    (project / "evidence/SYR_SOURCE_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents_added": 1, "sources_added": 2,
                      "domestic_observations_added": 0, "territories": len(dataset["territories"])}))


if __name__ == "__main__":
    main()

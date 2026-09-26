"""Register verified Oman planning/finance locations without adopting their values."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = (
    ("omn-south-sharqiyah-governor-article11", "South Al Sharqiyah Governorate: Governor duties under Article 11",
     "https://ssg.gov.om/the-governor", "South Al Sharqiyah Governorate (Oman)",
     "Royal Decree 36/2022 Article 11 quoted on official page; current application to verify",
     "governorate institutional responsibility, not a wilayat plan",
     "The page describes the governor preparing and monitoring governorate development-plan projects and preparing an annual governorate budget/final account for Ministry of Finance submission. It does not establish an approved local plan, executed budget or wilayat planning duty."),
    ("omn-mof-e-library", "Oman Ministry of Finance e-library",
     "https://www.mof.gov.om/e-library", "Ministry of Finance (Oman)",
     "budget and final-account publications; editions to inspect",
     "national government publications and governorate-labelled schedules",
     "Official catalogue lists state budget and final-account products. Publication location only; no local budget or expenditure value adopted."),
    ("omn-mof-2024-final-account-schedules", "Oman 2024 state final-account schedules",
     "https://www.mof.gov.om/download.aspx?id=L1VwbG9hZHNBbGwvRmluYWxBY2NvdW50LzE3NDg3Nzg3MDU0NDJTY2hlZHVsZXMgb2YgdGhlIHN0YXRlcyBmaW5hbCBhY2NvdW50IGZvciBmaXNjYWwgeWVhciAyMDI0LnBkZg%3D%3D",
     "Ministry of Finance (Oman)", "fiscal year 2024 final-account schedules",
     "governorate-labelled government-unit development expenditure, scope to audit",
     "PDF pages 47-49 contain governorate-labelled government-unit rows. Neither those rows nor any national figures are adopted; they must not be interpreted as all expenditure geographically occurring within a governorate."),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    ids = {item["id"] for item in dataset["sources"]}
    if dataset["country"]["id"] != "OMN" or "omn-ecensus-2020-housing-units" not in ids or \
            any(item[0] in ids for item in LEADS):
        raise ValueError("Run once after Oman housing import")
    now = datetime.now(timezone.utc).isoformat()
    for source_id, name, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": name, "url": url,
            "publisher": publisher, "reference_period": period, "geographic_level": geography,
            "status": "partial", "retrieved_at": now, "license": "terms_review_required", "note": note})
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap["detail"] += (" Official governorate-duties and 2024 final-account locations have now been identified,"
                              " but no approved local plan, budget amount, actual expenditure or evaluation is adopted.")
            gap["next_action"] = ("Acquire the applicable decree and individual governorate plan/budget/final-account originals;"
                                  " audit government-unit versus geographic expenditure and verify periods and legal approval before adoption.")
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    country_research = preflight["country_research"]
    country_research["planning"]["note"] += (" South Al Sharqiyah's official governor page quotes Article 11"
        " duties, and MOF publishes a 2024 final-account PDF with governorate-labelled government-unit"
        " rows. These are location leads only; no local plan, budget or spending value is adopted.")
    country_research["sources"].extend({"id": item[0], "url": item[2],
        "site_status": "official_location_identified"} for item in LEADS)
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = project / "evidence/SOURCE_PREFLIGHT.md"
    with md_path.open("a", encoding="utf-8") as handle:
        handle.write("\n\nAdditional 2026-09-26 Oman locations: South Al Sharqiyah governor Article 11 duties;"
                     " Ministry of Finance e-library and 2024 final-account schedules. No local plan,"
                     " budget, spending or evaluation amount is adopted from these locations.\n")
    print(json.dumps({"official_location_leads_added": len(LEADS)}))


if __name__ == "__main__":
    main()

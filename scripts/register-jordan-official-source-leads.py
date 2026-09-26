"""Record Jordan official source locations without adopting their unseen content."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = [
    {
        "id": "jor-dos-census-2015-tables-catalog",
        "name": "Jordan DoS Population and Housing Census 2015 table catalogue",
        "url": "https://dosweb.dos.gov.jo/censuses/population_housing/census2015/census2015_tables/",
        "publisher": "Jordan Department of Statistics", "reference_period": "2015 census",
        "geographic_level": "national, governorate and administrative divisions by table",
        "note": "Official catalogue lists population, buildings, housing, education, employment, refugee and disability tables. Individual original tables, codes, geographic scope, denominators and reuse terms require independent audit; no 2015 numeric value was adopted here.",
    },
    {
        "id": "jor-moi-governorate-administrative-list",
        "name": "Jordan Ministry of Interior governorates and administrative centers",
        "url": "https://moi.gov.jo/En/List/Governorates_and_Sectors",
        "publisher": "Jordan Ministry of Interior", "reference_period": "accessed 2026-09-26",
        "geographic_level": "12 governorates; districts and lower divisions need review",
        "note": "The official list confirms the 12 governorate identities and spelling variants. It is not a coded boundary register and does not establish 2006-to-2025 polygon equivalence.",
    },
    {
        "id": "jor-mola-local-administration-law-2021-location",
        "name": "Jordan Ministry of Local Administration 2021 Local Administration Law listing",
        "url": "https://www.mola.gov.jo/Ar/Pages/%D8%A7%D9%84%D9%82%D9%88%D8%A7%D9%86%D9%8A%D9%86",
        "publisher": "Jordan Ministry of Local Administration", "reference_period": "2021 law, listed 2026-09-26",
        "geographic_level": "national local-administration framework",
        "note": "The official legislation page lists Law 22 of 2021 and a PDF link. Its provisions were not reviewed here; compare with 2026 Law 16 and effective date before assigning planning duties.",
    },
    {
        "id": "jor-mola-governorate-planning-guide-location",
        "name": "Guide for Preparation of Governorate Strategic Development and Implementation Plans",
        "url": "https://www.mola.gov.jo/ebv4.0/root_storage/ar/eb_list_page/guide_for_the_preparation_of_governorate_strategic_development_and_implementation_plans.pdf",
        "publisher": "Jordan Ministry of Local Administration", "reference_period": "2018 guide",
        "geographic_level": "governorate planning guidance",
        "note": "Official guide location. Search-indexed text refers to the 2015 decentralization law; current applicability and consistency with 2021/2026 legislation, complete content and reuse terms require review. It is not an actual governorate plan.",
    },
    {
        "id": "jor-mopic-planning-law-2024",
        "name": "Planning and International Cooperation Law No. 10 of 2024",
        "url": "https://www.mop.gov.jo/En/Pages/Planning_Law",
        "publisher": "Jordan Ministry of Planning and International Cooperation",
        "reference_period": "2024 national planning law",
        "geographic_level": "national planning institutions",
        "note": "Official ministry text identifies its role in methodologies, development visions, plans and executive programs. It does not by itself identify a selected governorate's approved plan, budget, execution or evaluation.",
    },
    {
        "id": "jor-pm-local-administration-law-2026-gazette-location",
        "name": "Official Gazette listing of Local Administration Law No. 16 of 2026",
        "url": "https://www.pm.gov.jo/Ar/Pages/NewsPaperDetails/6072",
        "publisher": "Jordan Prime Ministry", "reference_period": "published 2026-09-10; future effective date",
        "geographic_level": "national local-administration framework",
        "note": "Official Gazette page links the enacted law. Jordan News Agency reports it takes effect 60 days after 2026-09-10, so it was not yet effective at the 2026-09-26 check. Full text and transition from 2021 law need legal review; no local plan status is inferred.",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "JOR":
        raise ValueError("Expected Jordan project")
    if any(item["id"] == "jor-dos-population-estimates-end-2025" for item in dataset["sources"]) is False:
        raise ValueError("Import the DoS 2025 PDF first")
    existing = {item["id"] for item in dataset["sources"]}
    if any(item["id"] in existing for item in LEADS):
        raise ValueError("Jordan source leads already registered")
    checked_at = datetime.now(timezone.utc).isoformat()
    for lead in LEADS:
        dataset["sources"].append({**lead, "status": "partial", "retrieved_at": checked_at,
                                   "license": "terms_review_required"})
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap["status"] = "partial"
            gap["detail"] = "Official locations for 2021 and 2026 local-administration laws, a 2018 governorate planning guide and the 2024 national planning law were identified. No actual selected-governorate plan, municipal plan, budget, execution or evaluation was acquired or adopted."
            gap["next_action"] = "Review effective/transition provisions and current planning guidance; acquire actual plans and financial/implementation evidence for representative governorates and municipalities."
    dataset["generated_at"] = checked_at
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": checked_at,
        "origin_registry": "AreaData 2026-09-26 Jordan official source pass",
        "census": {"url": LEADS[0]["url"], "acquisition": "catalogue_only_not_tables",
                   "note": "2015 population census is separate from acquired end-2025 population estimates."},
        "planning": {"url": LEADS[3]["url"], "acquisition": "guide_location_only",
                     "note": "Guide refers to an older 2015 law; 2026 local-administration law was not yet effective on this check. No actual local plan acquired."},
        "sources": [{"id": "jor-dos-population-estimates-end-2025", "url": "https://dosweb.dos.gov.jo/DataBank/population/population_Estimares/PopulationEstimates.pdf", "site_status": "acquired_partial_fields_adopted"}] +
                   [{"id": item["id"], "url": item["url"], "site_status": "official_location_identified"} for item in LEADS],
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "Jordan DoS end-2025 population estimates PDF was acquired, and Tables 2.2 and 2.3 were adopted for country and 12 governorates after row/column reconciliation. The separate 2015 census catalogue, Ministry of Interior governorate list, planning law and guide locations were identified only. The 2026 local-administration law was published but was not yet effective on this check. Current codes/boundaries and actual local plans, budgets, execution and evaluations remain open. See JOR_SOURCE_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Jordan source preflight Markdown")
    markdown_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"source_leads_added": len(LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

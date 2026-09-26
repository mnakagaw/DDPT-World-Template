"""Record Bahrain official source locations without adopting their legal or fiscal claims."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = [
    ("bhr-iga-census2020-catalogue", "Bahrain official Census 2020 table catalogue",
     "https://www.data.gov.bh/api/explore/v2.1/catalog/datasets?search=Census%202020&limit=100&offset=0",
     "Information & eGovernment Authority (Bahrain)", "2020 Census; portal as checked 2026-09-26",
     "45 titled tables; 20 with governorate dimensions", "official_portal_terms_review_required",
     "All 45 table bodies and receipts are inventoried locally. Only five selected tables contribute to 10 partial indicators; the remaining fields need semantic audit."),
    ("bhr-municipal-regulation-2002", "2002 implementing regulation of Municipalities Law, Articles 36–39",
     "https://www.lloc.gov.bh/Legislation/HTM/RCAB1602",
     "Legislation and Legal Opinion Commission (Bahrain)", "2002 original; 2026 operative text unverified",
     "municipal local-plan and budget provisions", "official_legal_source_terms_review_required",
     "Official search result locates Articles 36–39; 2026 amendments and consolidated applicability remain unverified. No municipality plan or budget is acquired."),
    ("bhr-urban-planning-law-1994", "Urban Planning Law, Decree-Law 2/1994",
     "https://www.lloc.gov.bh/Legislation/HTM/L0294",
     "Legislation and Legal Opinion Commission (Bahrain)", "1994 original; later amendments to verify",
     "national urban-planning framework", "official_legal_source_terms_review_required",
     "This is a separate planning authority framework. Current consolidated text and relation to municipal local plans have not been audited."),
    ("bhr-municipal-budget-2025-2026-aggregate", "Approved budget for the four municipalities, fiscal years 2025–2026",
     "https://www.mun.gov.bh/newportal/en/municipal-affairs/approved-budget-fiscal-years-2025-and-2026",
     "Ministry of Municipalities Affairs and Agriculture (Bahrain)", "FY 2025–2026",
     "aggregate four-municipality page; not an individual municipal account",
     "official_page_reuse_terms_review_required",
     "Official page location identified; direct original and line items not acquired. Do not assign aggregate figures to any municipality or infer expenditure/evaluation."),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dashboard = project / "data/dashboard.json"
    data = json.loads(dashboard.read_text(encoding="utf-8"))
    inventory = json.loads((project / "evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json").read_text(encoding="utf-8"))
    if data["country"]["id"] != "BHR" or len(inventory["tables"]) != 45:
        raise ValueError("Expected acquired Bahrain candidate")
    if any(source["id"] == LEADS[0][0] for source in data["sources"]):
        raise ValueError("Bahrain source leads already registered")
    now = datetime.now(timezone.utc).isoformat()
    for source_id, name, url, publisher, period, level, license_name, note in LEADS:
        data["sources"].append({"id": source_id, "name": name, "url": url,
            "publisher": publisher, "reference_period": period,
            "geographic_level": level, "status": "partial", "retrieved_at": now,
            "license": license_name, "note": note})
    data["generated_at"] = now
    dashboard.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_census_catalogue_acquired_partial_indicator_adoption",
        "checked_at": now,
        "origin_registry": "AreaData Bahrain iGA Census 2020 catalogue and official legal/finance location pass 2026-09-26",
        "census": {"status": "45_tables_acquired_10_indicators_partially_adopted",
            "note": "All 45 titled Census 2020 API tables and 2602 source rows acquired with receipts. Five tables provide 40 governorate observations, each a source-cell sum. Six other tables crosscheck them; remaining fields are priority_unassessed. The census total 1501635 differs from the separate 2020 annual estimate 1472204."},
        "local_statistics": {"status": "four_governorate_census_subset",
            "note": "Four 2020 census reporting governorate names, 10 indicators and 40 values. National values are AreaData complete-cover sums; WDI national series remain separate."},
        "geography": {"status": "four_labels_matched_official_codes_and_polygons_unverified",
            "note": "Four labels appear in the 2014 legal amendment search result. The legal map annex, official code table, 2020/2026 polygons and municipal crosswalk were not acquired. 2017 provider shapes were withheld."},
        "planning": {"status": "legal_and_aggregate_budget_locations_only",
            "note": "2002 municipal regulation Articles 36–39 and separate urban planning law located, but 2026 consolidated applicability and individual approved plans/budgets/expenditure/evaluations are unverified. Aggregate four-municipality budget page is not a local record."},
        "sources": ([{"id": source["id"], "site_status": "acquired_selected_cells_adopted"}
                     for source in data["sources"] if source["id"].startswith("bhr-iga-census2020-") and source["id"] != LEADS[0][0]]
                    + [{"id": LEADS[0][0], "site_status": "acquired_all_45_tables_partial_semantic_assessment"},
                       {"id": "bhr-governorates-2014-amendment", "site_status": "official_location_identified_no_annex"}]
                    + [{"id": source_id, "url": url, "site_status": "official_location_identified"}
                       for source_id, _, url, *_ in LEADS[1:]]
                    + [{"id": "bhr-moh-census-2020-annual-demographic-table",
                        "url": "https://www.moh.gov.bh/Content/Files/Publications/statistics/HS2020/PDF/CH-02-census_2020-2.pdf",
                        "site_status": "official_location_identified_distinct_annual_series_not_adopted"}]),
        "cross_country_candidates": "Generated common-source candidates remain availability_not_checked_for_country except acquired WDI national series; no common local source is assumed available."}
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = project / "evidence/SOURCE_PREFLIGHT.md"
    with summary.open("a", encoding="utf-8") as handle:
        handle.write("\n## Bahrain official-source update, 2026-09-26\n\n"
                     "The initially unresearched country entry is superseded by `SOURCE_PREFLIGHT.json` country_research. "
                     "The acquired 45-table/2,602-row portal inventory, field register, source receipts and import audit are under `evidence/` and `raw/`. "
                     "Five tables supply 10 partial 2020 census indicators; six other tables crosscheck them. All other fields are priority_unassessed. "
                     "The four census governorate names lack verified official codes and dated polygons. "
                     "Municipal plan law, national urban-planning law and a four-municipality aggregate budget page have locations only; no individual approved plan/finance original is adopted. "
                     "Portal Terms of Use require attribution, download dates, a transformation notice and their prescribed disclaimer before external release.\n")
    print(json.dumps({"registered_leads": len(LEADS), "census_tables": len(inventory["tables"])}))


if __name__ == "__main__":
    main()

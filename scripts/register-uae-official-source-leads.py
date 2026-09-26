"""Register UAE official source locations with no unreviewed observation adoption."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = [
    {
        "id": "are-fcsc-uaestat-emirate-vital-dataflow",
        "name": "UAE.Stat births by emirate dataflow FCSA:DF_BIRTHS(1.9.0)",
        "url": "https://uaestat.fcsc.gov.ae/en",
        "publisher": "Federal Competitiveness and Statistics Centre",
        "reference_period": "annual births dataflow, site lists update 2026-03-25",
        "geographic_level": "national and seven emirate filters; actual exported coverage unverified",
        "note": "The official data explorer lists births by emirate, gender and citizenship. Direct acquisition returned HTTP 403 in this environment. No value, denominator, code crosswalk or period has been adopted. Independently obtain its dataflow/export and confirm terms before use.",
    },
    {
        "id": "are-dsc-dubai-population-bulletin-2024-location",
        "name": "Dubai population bulletin, end 2024",
        "url": "https://www.dsc.gov.ae/Publication/Population%20Bulletin%20Emirate%20of%20Dubai%20-%202024.pdf",
        "publisher": "Dubai Data and Statistics Establishment",
        "reference_period": "end 2024 estimates, reportedly revised using 2025 register approach",
        "geographic_level": "Dubai emirate only",
        "note": "Official search-indexed PDF location reports end-2024 Dubai estimates, but direct acquisition returned HTTP 403. The original was not locally acquired, audited or adopted; do not combine the indexed value with Abu Dhabi's register census as one federal series.",
    },
    {
        "id": "are-uae-seven-local-governments-overview",
        "name": "UAE Government overview of the seven local governments",
        "url": "https://u.ae/en/about-the-uae/the-uae-government/the-local-governments-of-the-seven-emirates",
        "publisher": "Official Platform of the UAE Government",
        "reference_period": "page updated 2024-12-30; checked 2026-09-26",
        "geographic_level": "seven emirates, institution overview without official boundary codes",
        "note": "The official overview says local governments differ in functions and structure. It is an institutional location, not a coded boundary register or one national local-planning law. Check each emirate's actual plan and planning authority separately.",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "ARE" or not any(source["id"] == "are-fcsc-census-figures-2005" for source in dataset["sources"]):
        raise ValueError("Import UAE official originals first")
    existing = {item["id"] for item in dataset["sources"]}
    if any(lead["id"] in existing for lead in LEADS):
        raise ValueError("UAE source leads already registered")
    checked_at = datetime.now(timezone.utc).isoformat()
    for lead in LEADS:
        dataset["sources"].append({**lead, "status": "partial", "retrieved_at": checked_at,
                                   "license": "terms_review_required"})
    dataset["generated_at"] = checked_at
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": checked_at,
        "origin_registry": "AreaData 2026-09-26 UAE official source pass",
        "census": {"url": "https://census.scad.gov.ae/home/population?fid=0&lang=en&tab=webreport",
                   "acquisition": "Abu Dhabi 2024 web report acquired; national 2023 census coverage not inferred",
                   "note": "The UNSD-linked census page pertains to Abu Dhabi; it is not evidence of 2023 national census values for all emirates."},
        "planning": {"url": "https://dmpmedia.dm.gov.ae/uploads/2024/04/Dubai-2040-Urban-Master-Plan-2040-Executive-Summary-v1.pdf",
                     "acquisition": "Dubai plan summary and 2023 law acquired; other emirates not covered",
                     "note": "Do not transfer Dubai's urban planning law, plan structure or period to other emirates."},
        "sources": [
            {"id": source_id, "site_status": "acquired_partial_content_adopted" if source_id in
             ("are-fcsc-census-figures-2005", "are-scad-abu-dhabi-census-2024") else "body_acquired_selected_content_verified"}
            for source_id in ("are-fcsc-census-figures-2005", "are-scad-abu-dhabi-census-2024",
                              "are-dubai-2040-structure-plan", "are-dubai-urban-planning-law-16-2023")
        ] + [{"id": lead["id"], "url": lead["url"],
              "site_status": "acquisition_failed_http_403" if "fcsc-uaestat" in lead["id"] or "dsc-dubai" in lead["id"]
                             else "official_location_identified"} for lead in LEADS],
        "cross_country_candidates": "The generated common-source list remains a discovery plan; country/theme/period/geography availability has not been individually verified in this pass.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "FCSC's historical 1975–2005 census table, the Abu Dhabi 2024 register census web report, the Dubai 2040 structure-plan executive summary and Dubai's 2023 urban planning law were acquired. Four historical count series, three Abu Dhabi 2024 counts and two Dubai documents are adopted with scoped status. The Dubai 2024 population bulletin and UAE.Stat emirate-vitals dataflow were located but direct acquisition returned HTTP 403; no values were used. Official geography/code reconciliation, current comparable values for six emirates, other emirates' planning/budget evidence and the common-source availability checks remain open. See ARE_OFFICIAL_IMPORT_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected UAE source preflight Markdown")
    markdown_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"source_leads_added": len(LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

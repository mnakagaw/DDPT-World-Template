"""Register PCBS/MoLG source locations without upgrading unassessed products."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = (
    ("pse-pcbs-2017-detailed-population", "PCBS PHC 2017 detailed population final results",
     "raw/palestine-pcbs-2017/pcbs-2017-detailed-population.pdf",
     "Palestinian Central Bureau of Statistics", "2017 census", "national, governorate and locality tables to inventory",
     "270-page detailed volume acquired but physical tables, numeric columns, locality semantics and adoption remain unassessed."),
    ("pse-pcbs-2017-governorate-area", "PCBS governorate land-area table (2017 geography, hosted in 2019 table)",
     "raw/palestine-pcbs-2017/pcbs-2017-governorate-area.html",
     "Palestinian Central Bureau of Statistics", "2017 territorial area; page hosted in 2019 collection",
     "governorate", "Acquired area table says 2017 governorate geography was rearranged based on census localities. Area values and boundary equivalence are not adopted as population or legal polygons."),
)
WEB_LEADS = (
    ("pse-pcbs-report-history", "PCBS official report-history catalogue",
     "https://www.pcbs.gov.ps/en/reference/report-history/", "Palestinian Central Bureau of Statistics",
     "2017 census and other report editions", "national and governorate report originals linked separately",
     "Official catalogue locates further 2017 census reports. The full product inventory, tables and reuse terms are not assessed; this is a location lead only."),
    ("pse-molg-governorate-planning-guide", "MoLG strategic governorate planning facilitator guide",
     "https://www.molg.pna.ps/uploads/userfiles/file/pdfs/DSDPmanualArabic.pdf",
     "Ministry of Local Government (Palestine)", "historical guide hosted by ministry; current standing to verify",
     "governorate regional-planning guidance, not an individual approved plan",
     "Official ministry catalogue links the guide and the direct PDF returned HTTP 200. The body was not acquired or assessed; current legal applicability and individual governorate plans remain open."),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    existing = {item["id"] for item in dataset["sources"]}
    required = {"pse-pcbs-phc-2017-summary-table2", "pse-molg-sdip-towns-guide-2018",
                "pse-molg-sector-strategy-2025-2027"}
    if dataset["country"]["id"] != "PSE" or not required.issubset(existing) or \
            any(item[0] in existing for item in LEADS + WEB_LEADS):
        raise ValueError("Import PCBS and MoLG originals once before registering source leads")
    now = datetime.now(timezone.utc).isoformat()
    for source_id, name, relative, publisher, period, geography, note in LEADS:
        pdf = project / relative
        receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != receipt["sha256"] or receipt["status"] != "acquired":
            raise ValueError(f"Acquired source lead original/receipt differs: {relative}")
        dataset["sources"].append({"id": source_id, "name": name, "url": receipt["source_url"],
            "publisher": publisher, "reference_period": period, "geographic_level": geography,
            "status": "partial", "retrieved_at": receipt["retrieved_at"],
            "raw_path": relative, "sha256": receipt["sha256"],
            "license": "official_publication_redistribution_terms_review_required", "note": note})
    for source_id, name, url, publisher, period, geography, note in WEB_LEADS:
        dataset["sources"].append({"id": source_id, "name": name, "url": url,
            "publisher": publisher, "reference_period": period, "geographic_level": geography,
            "status": "not_collected", "retrieved_at": now, "license": "terms_review_required",
            "note": note})
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": now,
        "origin_registry": "AreaData 2026-09-26 PCBS 2017/MoLG source pass",
        "census": {"status": "summary_table2_four_counts_adopted_other_tables_open",
            "note": "PCBS 2017 Final Summary Table 2 gives 19 reporting rows and four adopted counts (76 observations). Summary Table 29 has 585 coded locality rows, 56 wrapped; none adopted. Detailed 270-page report is acquired but not semantically inventoried."},
        "local_statistics": {"status": "historical_governorate_counts_partially_adopted",
            "note": "2017 nation, two regions and 16 governorates. 2019-hosted governorate area table, detailed report, post-2017 projections and common international candidates remain unassessed, not zero or absent."},
        "geography": {"status": "pcbs_2017_source_hierarchy_only",
            "note": "Table 2 source labels and exact totals checked. No official governorate codes or 2017 legal polygons verified; two bootstrap 2021 provider polygons withheld. Jerusalem J1/J2 and locality codes require separate audit."},
        "planning": {"status": "national_molg_guidance_and_strategy_selected_pages_acquired_local_originals_missing",
            "note": "2018 municipal SDIP guide and 2025–2027 national MoLG sector strategy attached as two national references. Governorate planning guide located only. No individual governorate or municipal plan, approval, local budget, spending or evaluation verified."},
        "sources": ([{"id": "pse-pcbs-phc-2017-summary-table2", "site_status": "acquired_four_count_columns_adopted"},
                     {"id": "pse-molg-sdip-towns-guide-2018", "site_status": "acquired_selected_pages_national_reference"},
                     {"id": "pse-molg-sector-strategy-2025-2027", "site_status": "acquired_selected_pages_national_reference"}] +
                    [{"id": item[0], "site_status": "acquired_not_adopted"} for item in LEADS] +
                    [{"id": item[0], "site_status": "official_location_identified"} for item in WEB_LEADS]),
        "cross_country_candidates": "Generated common-source list is a discovery plan; country/theme/year/geography availability is not closed by this pass.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = md_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "PCBS 2017 Summary Table 2 four count fields were adopted for Palestine, two reporting regions and 16 governorates (76 records). Table 29 locality rows, detailed population tables, governorate area measures, official codes and 2017 legal polygons remain unadopted. A 2018 city/town planning guide and the 2025–2027 MoLG national sector strategy were acquired and selected pages checked; individual local plans, approval, budget, actual expenditure and evaluation remain unverified. The governorate planning guide and PCBS catalogue are location leads. See PSE_PCBS_2017_STRUCTURE.json and PSE_MOLG_PLANNING_IMPORT_AUDIT.json. Cross-country candidate availability is not implied.")
    if old not in markdown:
        raise ValueError("Unexpected Palestine source preflight Markdown")
    md_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"acquired_or_partially_acquired_sources": len(LEADS) + len(required),
                      "location_leads": len(WEB_LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

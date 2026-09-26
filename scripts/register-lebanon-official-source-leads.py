"""Record checked Lebanon source locations without promoting their contents to indicators."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = (
    ("lbn-cas-lfhlcs-2018-19-survey-page", "CAS LFHLCS 2018–19 survey catalogue",
     "https://www.cas.gov.lb/surveys-censuses/labour-force-and-household-living-conditions-survey-2018-2019-lebanon/",
     "Central Administration of Statistics (Lebanon)", "April 2018–March 2019 survey",
     "national, eight governorates and 26 caza in source reporting geography",
     "Survey catalogue, not a census. The report and demography workbook were acquired separately; the remaining thematic workbooks and response/coverage documentation need a full audit."),
    ("lbn-cas-subnational-mics-2023", "CAS Sub-national Lebanon MICS 2023 catalogue",
     "https://www.cas.gov.lb/surveys-censuses/sub-national-lebanon-multiple-indicator-cluster-survey-2023/",
     "Central Administration of Statistics (Lebanon)", "2023 survey",
     "published results for five of eight governorates plus specified settlement/camp groups",
     "Official page and statistical-snapshot report located. Security conditions prevented fieldwork in three governorates; their results must not be read as zero. No MICS value was adopted."),
    ("lbn-dglac-administrative-structures", "DGLAC administrative structures",
     "https://dglac.gov.lb/en/administrative-structures",
     "Directorate General of Local Administrations and Councils (Lebanon)",
     "current page checked 2026-09-26; legal effective dates to verify",
     "governorates, districts, municipalities and municipal unions",
     "Institutional location only. Obtain the current legal text, authoritative identifiers, boundaries and planning duties before mapping survey units to municipal planning actors."),
    ("lbn-dglac-municipalities", "DGLAC municipality directory",
     "https://www.dglac.gov.lb/en/municipalities",
     "Directorate General of Local Administrations and Councils (Lebanon)",
     "directory checked 2026-09-26; edition to verify", "municipalities",
     "Official directory location, not an acquired coded and dated municipality table. No municipality plan, budget or implementation record was linked."),
    ("lbn-dgu-master-plan", "Directorate General of Urban Planning master plan page",
     "https://dgu.gov.lb/MasterPlan.html", "Directorate General of Urban Planning (Lebanon)",
     "plan catalogue page checked 2026-09-26", "spatial master-plan areas; relation to municipal units unverified",
     "Official planning-document discovery location only. No specific approved plan, status, boundary, implementation or evaluation original was acquired for a selected municipality."),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    ids = {item["id"] for item in dataset["sources"]}
    if dataset["country"]["id"] != "LBN" or "lbn-cas-lfhlcs-2018-19-hl5" not in ids or \
            any(item[0] in ids for item in LEADS):
        raise ValueError("Import LFHLCS once before registering Lebanon leads")
    now = datetime.now(timezone.utc).isoformat()
    for source_id, title, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": publisher, "reference_period": period, "geographic_level": geography,
            "status": "partial", "retrieved_at": now, "license": "terms_review_required",
            "note": note})
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": now,
        "origin_registry": "AreaData 2026-09-26 Lebanon CAS/MOPH/DGLAC/DGU official-source pass",
        "census": {"status": "no_population_census_original_acquired",
            "note": "The acquired LFHLCS is a sample survey with weighted midyear-2018 estimates, not a census. Do not infer that no population census exists from this one collection pass. Locate the full official census/product catalogue and assess expected coverage."},
        "local_statistics": {"status": "selected_survey_fields_acquired_and_adopted",
            "note": "CAS LFHLCS Demography HL5 Women, Men and Women & Men: 105 records for nation, eight source governorates and 26 caza. Twenty-three other demography table sheets and 26 acquired English district profiles remain semantically unassessed. 2023 MICS has incomplete governorate coverage and no adopted values."},
        "geography": {"status": "reference_only_unreconciled",
            "note": "MOPH ArcGIS has nine ADM1 and 26 ADM2 features; LFHLCS reports eight governorates. Caza shapes are name matched reference only; legal/temporal boundary edition and code equivalence are unverified."},
        "planning": {"status": "official_locations_identified_no_local_original",
            "note": "DGLAC administrative/municipal locations and DGU master-plan page identified. No verified selected-area plan, legal obligation, approved budget, actual spending or official evaluation acquired."},
        "sources": ([{"id": source_id, "site_status": "acquired_partial_indicator_adoption" if source_id == "lbn-cas-lfhlcs-2018-19-hl5" else "acquired_not_adopted_or_reference_only"}
                     for source_id in ("lbn-cas-lfhlcs-2018-19-hl5", "lbn-cas-lfhlcs-2018-19-full-report",
                                       "lbn-cas-lfs-district-profiles-2018-19", "lbn-moph-adm1-map", "lbn-moph-adm2-map")] +
                    [{"id": item[0], "url": item[2], "site_status": "official_location_identified"} for item in LEADS]),
        "cross_country_candidates": "The generated common-source list remains a discovery plan; individual country/theme/period/geography availability has not been checked in this pass.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "CAS LFHLCS 2018–19 survey Demography XLS, full report and 26 English district profiles were acquired. The survey is not a census. Only three HL5 sex-count fields were adopted for nation, eight source governorates and 26 caza (105 records); other fields/profile contents remain unassessed. MOPH has nine undated governorate reference features and 26 caza outlines, so source geography and current map/official codes are not reconciled. CAS MICS 2023, DGLAC administrative/municipal pages and DGU master-plan page are official locations only; no local plan, approved budget, expenditure or evaluation was acquired. Census catalogue coverage and common-source availability remain open. See LBN_LFHLCS_HL5_IMPORT_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Lebanon source preflight Markdown")
    markdown_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"acquired_sources": 5, "location_leads": len(LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

"""Register inspected/acquired Israel source locations without promoting unreviewed data."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


OTHER_WORKBOOKS = (
    ("selected-localities-statistical-areas.xlsx", "isr-cbs-census-2022-selected-localities-statistical-areas",
     "Selected census data by localities and statistical areas", "locality and statistical area; many fields"),
    ("population-group-religion-age-sex.xlsx", "isr-cbs-census-2022-population-group-religion-age-sex",
     "Census estimate by population group, religion, age and sex", "geography and universe by sheet to audit"),
    ("population-households-locality.xlsx", "isr-cbs-census-2022-population-households-locality",
     "Census population and households by locality", "locality codes; households exclude individual institutional residents"),
    ("population-selected-characteristics.xlsx", "isr-cbs-census-2022-population-selected-characteristics",
     "Census and population estimates by selected characteristics", "2022 census, end-2021 estimate and 2008 census remain separate"),
    ("households-selected-characteristics.xlsx", "isr-cbs-census-2022-households-selected-characteristics",
     "Census households by selected characteristics", "2022 and 2008 census estimates remain separate"),
)
LEADS = (
    ("isr-cbs-census-2022-catalogue", "CBS Population Census 2022 catalogue and selected tables",
     "https://www.cbs.gov.il/en/Surveys/Pages/Population-Census.aspx", "Central Bureau of Statistics (Israel)",
     "2022 census; files linked in 2025 path", "national, district, locality, statistical area", "Six Excel originals were acquired separately. The catalogue contains a sample questionnaire not yet acquired; its full expected product list needs disposition."),
    ("isr-cbs-dictionary-geo-api", "CBS geographic dictionary API documentation",
     "https://www.cbs.gov.il/en/cbsNewBrand/Pages/API-Dictionary.aspx", "Central Bureau of Statistics (Israel)",
     "API documentation checked 2026-09-26", "district, subdistrict, locality, planning committee code lists", "The documentation identifies code/year keys and locality, district and planning-committee endpoints. Exact current API responses, terms and boundary equivalence were not acquired."),
    ("isr-knesset-planning-building-law-1965", "Planning and Building Law, 1965, official legislation record",
     "https://main.knesset.gov.il/Activity/Legislation/Laws/pages/lawprimary.aspx?lawitemid=2000613&st=lawlaws&t=lawlaws", "Knesset",
     "1965 law; current consolidated amendment status unverified", "national, district and local planning institutions to audit", "Official legislation location was identified; full current Hebrew text, amendment history and applicable duties were not audited. An older English translation must not be treated as the latest law."),
    ("isr-iplan-xplan-catalogue", "Planning Administration XPLAN public plan discovery service",
     "https://www.gov.il/en/service/searching-plans-submitted-planning-institutes-in-xplan-site", "Planning Administration (Israel)",
     "digital plans; portal coverage by district/date varies", "plan footprints and planning areas, not automatically CBS districts", "Government service page says plans have processing stages and source documents; XPLAN does not cover every older/pending plan. No specific plan record was acquired or attached to a district."),
    ("isr-moin-local-authorities-audited-2024", "Ministry of Interior audited local-authority financial reports, 2024",
     "https://data.gov.il/he/datasets/interior_affairs/local-authorities/6e153ddd-d4d4-4450-a78c-20f594a7986a", "Ministry of Interior (Israel)",
     "2024 annual audited reports, portal updated 2026-05-27", "local authorities; code crosswalk unverified", "The official government data portal lists 2024 audited local-authority financial report rows. Dataset was not downloaded or reconciled; budget authorization, actual expenditure and audit findings must remain distinct."),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "ISR" or not any(s["id"] == "isr-cbs-census-2022-broad-geographical" for s in dataset["sources"]):
        raise ValueError("Import CBS district subset first")
    ids = {s["id"] for s in dataset["sources"]}
    if any(source_id in ids for _, source_id, *_ in OTHER_WORKBOOKS) or any(lead[0] in ids for lead in LEADS):
        raise ValueError("Israel source leads already registered")
    now = datetime.now(timezone.utc).isoformat()
    source_states = [{"id": "isr-cbs-census-2022-broad-geographical", "site_status": "acquired_partial_indicator_adoption"}]
    for filename, source_id, title, geography in OTHER_WORKBOOKS:
        relative = "raw/israel-cbs-census-2022/" + filename
        receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
        if receipt["status"] != "acquired":
            raise ValueError(f"Workbook original not acquired: {filename}")
        dataset["sources"].append({"id": source_id, "name": title, "url": receipt["source_url"],
            "publisher": "Central Bureau of Statistics (Israel)", "reference_period": "2022 Census and other period stated in workbook",
            "geographic_level": geography, "status": "partial", "retrieved_at": receipt["retrieved_at"],
            "sha256": receipt["sha256"], "raw_path": relative, "license": "terms_review_required",
            "note": "Original acquired and structural columns inventoried, but no indicator from this workbook has been adopted. Check every sheet and numeric field, coverage, suppression and code/boundary match before use."})
        source_states.append({"id": source_id, "site_status": "acquired_not_adopted"})
    for source_id, title, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": title, "url": url, "publisher": publisher,
            "reference_period": period, "geographic_level": geography, "status": "partial",
            "retrieved_at": now, "license": "terms_review_required", "note": note})
        source_states.append({"id": source_id, "url": url, "site_status": "official_location_identified"})
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": now,
        "origin_registry": "AreaData 2026-09-26 Israel official CBS census pass",
        "census": {"url": LEADS[0][2], "acquisition": "Six linked 2022 Excel originals acquired; twelve columns from the broad geography sheet adopted for nation and six districts only",
                   "note": "The CBS nationwide row includes the separately reported Judea and Samaria Area (code 7). Other products, locality values and unassessed columns are not a completed census inventory."},
        "planning": {"url": LEADS[3][2], "acquisition": "XPLAN service location identified; no local plan original acquired",
                     "note": "Planning law and local committee geography require current text and record-level audit. No plan approval/budget/execution/evaluation is inferred."},
        "sources": source_states,
        "cross_country_candidates": "The generated common-source list remains a discovery plan; country/theme/period/geography availability has not been individually checked in this pass.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "The CBS 2022 census catalogue's six Excel originals were acquired. Twelve selected columns from the nationwide/six-district broad-geography sheet were integrated; the separately reported Judea and Samaria Area (CBS code 7) remains source-only. All 14 sheet structures and columns were enumerated, but the remaining numeric fields, localities and statistical areas are not semantically decided. The CBS geographic dictionary API, current Planning and Building Law, XPLAN plan search and Ministry of Interior local audited-finance dataset were located, not acquired as usable plan/budget observations. Legal boundaries, the current planning regime and common-source availability remain open. See ISR_CBS_2022_IMPORT_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Israel source preflight Markdown")
    markdown_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"acquired_workbooks": 6, "location_leads": len(LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

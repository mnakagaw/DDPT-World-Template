"""Record Oman official source locations and acquisition limits in the preflight."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LEADS = (
    ("omn-ecensus-library", "Oman eCensus public library",
     "https://www.ecensus.gov.om/web/#/en/library",
     "National Centre for Statistics and Information (Oman)", "2020 census products; later reference dates require separate assessment",
     "population, housing and establishments products", "Catalogue location only. The adopted Population Dataset has more fields, dates and geography than the three checked 2020 nationality counts."),
    ("omn-moe-library", "Oman Ministry of Economy plan publication library",
     "https://economy.gov.om/library.aspx", "Ministry of Economy (Oman)",
     "current library checked 2026-09-26", "national five-year plans and strategic-programme publications",
     "Official library links the acquired 2026–2030 main plan PDF, a community version, a strategic-programme volume and prior-plan performance products. These other originals and any governorate-specific products are unassessed."),
    ("omn-mohup-national-spatial-strategy", "Oman National Spatial Strategy overview",
     "https://oman.housing.gov.om/onss", "Ministry of Housing and Urban Planning (Oman)",
     "national long-term spatial framework; edition/effective period to audit", "all 11 governorates; local plan application unverified",
     "Official overview identifies a national spatial strategy. The plan body, governorate plans, legal duties, boundaries and implementation records have not been acquired."),
    ("omn-mjla-gazette-169-decree-1-2026", "Official Gazette 169, Royal Decree 1/2026",
     "https://www.mjla.gov.om/modules/decrees/download.php?file=1396",
     "Ministry of Justice and Legal Affairs (Oman)", "1 January 2026 approval of 2026–2030 national plan",
     "national legal record; not a governorate plan approval", "Official Gazette PDF was located through the government search index, but local TLS chain verification failed; it was not saved as an acquired original. The Foreign Ministry's official page independently names Royal Decree 1/2026."),
    ("omn-ncsi-sdmx-population-metadata", "NCSI population SDMX metadata",
     "https://data.gov.om/api/1.0/sdmx/OMPOP2016", "National Centre for Statistics and Information (Oman)",
     "multiple population/census periods to classify", "national/governorate/wilayat dimensions in metadata; exact products unassessed",
     "Metadata endpoint responded, but the corresponding data endpoint returned HTTP 403 in this environment. No value adopted; this is not evidence of absence or a zero count."),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    path = project / "data/dashboard.json"
    dataset = json.loads(path.read_text(encoding="utf-8"))
    ids = {item["id"] for item in dataset["sources"]}
    required = {"omn-ecensus-2020-population", "omn-moi-governorate-wilayat-2025",
                "omn-moe-eleventh-five-year-plan-2026-2030"}
    if dataset["country"]["id"] != "OMN" or not required.issubset(ids) or \
            any(item[0] in ids for item in LEADS):
        raise ValueError("Import Oman census/directory/plan once before lead registration")
    now = datetime.now(timezone.utc).isoformat()
    map_audit = json.loads((project / "evidence/OMN_NCSI_WILAYAT_REGISTER_AUDIT.json").read_text(encoding="utf-8"))
    if map_audit["ncsi_rows"] != 63 or map_audit["arabic_name_matches"] != 63:
        raise ValueError("NCSI map-attribute audit incomplete")
    dataset["sources"].append({"id": "omn-ncsi-wilayat-feature-register",
        "name": "NCSI national spatial-data wilayat feature-register attributes",
        "url": map_audit["layer_url"],
        "publisher": "NCSI geospatial service; stated feature owner: Ministry of Interior (Oman)",
        "reference_period": "service edition and legal validity dates unverified; most feature-load fields say 2017-03-02",
        "geographic_level": "63 wilayat feature attributes; no polygons adopted",
        "status": "partial", "retrieved_at": now,
        "raw_path": "raw/oman-ecensus-moi/ncsi-wilayat-attributes.json",
        "sha256": map_audit["attributes_receipt_sha256"], "license": "terms_review_required",
        "note": "63 Arabic names matched the MOI 2025 list, but NCSI WilayaID/NSDIFID and MOI WilayatId are distinct code systems. Metadata and attributes acquired; polygon geometries, service edition and 2020 census legal equivalence are not certified."})
    for source_id, name, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": name, "url": url,
            "publisher": publisher, "reference_period": period, "geographic_level": geography,
            "status": "partial", "retrieved_at": now, "license": "terms_review_required", "note": note})
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap["detail"] += " A separate official NCSI/MOI spatial-data service has 63 wilayat attribute rows with all 63 Arabic names matching MOI 2025; its IDs differ from MOI IDs and no polygons or dated legal 2020 equivalence were adopted."
            gap["next_action"] = "Acquire and validate the official layer geometries and dated boundary/code history, including the two 2025-listed wilayats absent from 2020 numeric cells; keep name matches separate from legal equivalence."
    dataset["generated_at"] = now
    path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_locations_partly_acquired", "checked_at": now,
        "origin_registry": "AreaData 2026-09-26 Oman eCensus/MOI/NCSI/Ministry of Economy official-source pass",
        "census": {"status": "2020_population_subset_acquired_and_adopted",
            "note": "Official eCensus Population Dataset 2020-12-12: nation, 11 governorates and 61 wilayats with numeric nationality counts; 219 local records in three indicators. Later six-date portal snapshots, other fields/products and national executive-summary originals are unassessed. Two wilayats have null 2020 cells."},
        "local_statistics": {"status": "three_population_indicators_partially_adopted",
            "note": "Omani/expatriate source counts and exact local totals; no other eCensus fields or service statistics adopted. NCSI SDMX data fetch returned HTTP 403; metadata alone gives no values."},
        "geography": {"status": "2025_arabic_names_matched_temporal_boundary_unverified",
            "note": "MOI 2025 workbook has 11 governors/63 wilayats. Official NCSI layer also has 63 attribute rows and matching Arabic names but a distinct code system. No current polygon or 2020 legal equivalence adopted; seven bootstrap polygons withheld."},
        "planning": {"status": "national_plan_selected_pages_acquired_local_originals_missing",
            "note": "Ministry of Economy's 124-page national 2026–2030 main plan PDF acquired; pages 1, 6, 16 and 50 checked. Foreign Ministry names Royal Decree 1/2026. No verified governorate/wilayat plan, local budget, spending or evaluation. ONSS, programme volumes and Gazette are leads, not locally adopted originals."},
        "sources": [
            {"id": "omn-ecensus-2020-population", "site_status": "acquired_partial_indicator_adoption"},
            {"id": "omn-moi-governorate-wilayat-2025", "site_status": "acquired_name_id_crosswalk_only"},
            {"id": "omn-ncsi-wilayat-feature-register", "site_status": "acquired_attributes_no_polygons"},
            {"id": "omn-moe-eleventh-five-year-plan-2026-2030", "site_status": "acquired_selected_pages_adopted_national_only"},
            {"id": "omn-fm-royal-decree-1-2026-plan-announcement", "site_status": "official_page_checked_no_local_original"},
        ] + [{"id": item[0], "url": item[2], "site_status": "official_location_identified"}
             for item in LEADS],
        "cross_country_candidates": "The generated common-source list remains a discovery plan; individual Oman/theme/period/geography availability is not closed by this pass.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = md_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_locations_partly_acquired** (2026-09-26).\n\n"
           "Official eCensus 2020-12-12 nationality counts were adopted for the country, 11 governors and 61 wilayats (219 records). The 2025 MOI directory lists 63 wilayats; two have null 2020 cells. The separate NCSI map service has 63 matching Arabic names but different identifiers, and no polygon or temporal legal equivalence was adopted. The Ministry of Economy's 2026–2030 national plan PDF was acquired and selected pages checked; no local plans, budget, spending or evaluations were attached. Other eCensus products, spatial-plan originals, official Gazette and common-source availability remain open. See OMN_ECENSUS_2020_IMPORT_AUDIT.json, OMN_NCSI_WILAYAT_REGISTER_AUDIT.json and OMN_NATIONAL_PLAN_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Oman source preflight Markdown")
    md_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"acquired_or_partially_acquired_sources": 5,
                      "location_leads": len(LEADS), "source_total": len(dataset["sources"])}))


if __name__ == "__main__":
    main()

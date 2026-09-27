"""Import audited historical 2019 GSO/UNFPA Table 1 values without a 2025 code join."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "vnm-gso-unfpa-census2019-results"
BOUNDARY = "GSO/UNFPA 2019 census reporting geography; matching official polygons unavailable"
METHOD = "GSO/UNFPA 2019 Population and Housing Census results, direct Table 1 person counts"
FIELDS = {
    "total": ("VNM_GSO2019_POP", "2019 census population", "Persons in the published census Table 1 population"),
    "male": ("VNM_GSO2019_MALE", "2019 census male population", "Enumerated male persons"),
    "female": ("VNM_GSO2019_FEMALE", "2019 census female population", "Enumerated female persons"),
    "urban_total": ("VNM_GSO2019_URBAN_POP", "2019 census urban population", "Enumerated persons classified as urban"),
    "urban_male": ("VNM_GSO2019_URBAN_MALE", "2019 census urban male population", "Enumerated male persons classified as urban"),
    "urban_female": ("VNM_GSO2019_URBAN_FEMALE", "2019 census urban female population", "Enumerated female persons classified as urban"),
    "rural_total": ("VNM_GSO2019_RURAL_POP", "2019 census rural population", "Enumerated persons classified as rural"),
    "rural_male": ("VNM_GSO2019_RURAL_MALE", "2019 census rural male population", "Enumerated male persons classified as rural"),
    "rural_female": ("VNM_GSO2019_RURAL_FEMALE", "2019 census rural female population", "Enumerated female persons classified as rural"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(project):
    audit = json.loads((project / "evidence/VNM_CENSUS2019_AUDIT.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "config/vietnam-census2019-source-manifest.json").read_text(
        encoding="utf-8"))["sources"][0]
    raw = project / manifest["raw_path"]
    require(raw.stat().st_size == manifest["bytes"] and digest(raw) == manifest["sha256"],
            "Pinned GSO/UNFPA report mismatch")
    require(audit["source_sha256"] == manifest["sha256"] and audit["numeric_cells_audited"] == 630
            and audit["row_counts"] == {"country": 1, "socioeconomic_region": 6,
                                       "census_province_city_2019": 63}, "Table 1 audit changed")
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "VNM", "Expected Viet Nam project")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    provinces = [row for row in audit["table_1_rows"]
                 if row["section"] == "census_province_city_2019"]
    national = next(row for row in audit["table_1_rows"] if row["section"] == "country")
    # The generated geoBoundaries ADM1 reference has 64 old provider shapes and
    # no vetted identity/crosswalk to either 2019 census units or 2025 units.
    data["territories"] = [x for x in data["territories"] if x["id"] == "VNM"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0].update({"boundary_version": BOUNDARY, "source_id": SOURCE_ID})
    data["country"]["geography_note"] = (
        "This is a historical 1 April 2019 census view with 63 provinces/cities. Its source-table "
        "row ordinals are local IDs, not official administrative codes. In 2025 Viet Nam reorganised "
        "into 34 province-level units and two local-government levels. No code/boundary crosswalk is "
        "adopted; 2008 geoBoundaries shapes are removed. National WDI annual estimates and direct "
        "2019 census counts remain separate indicators.")
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("vnm-")]
    data["sources"].append({"id": SOURCE_ID, "name": "Results of the 2019 Viet Nam Population and Housing Census",
        "url": manifest["url"], "catalogue_url": manifest["catalogue_url"],
        "publisher": "General Statistics Office of Viet Nam and UNFPA Viet Nam",
        "reference_period": "1 April 2019", "geographic_level": "country and 2019 province/city",
        "status": "ready", "retrieved_at": manifest["retrieved_at"],
        "sha256": manifest["sha256"], "raw_path": manifest["raw_path"],
        "license": "Reuse conditions require verification before redistributing the original PDF",
        "note": "Table 1 direct counts only. Detailed tables 2-60 unassessed. "
                "PDF acquired from the official UNFPA Viet Nam publication; the separate NSO "
                "Completed Results original and district tables were not acquired."})
    for source_id, title, url, note in [
        ("vnm-nso-completed2019-catalogue", "NSO Completed Results of the 2019 census catalogue",
         "https://www.nso.gov.vn/en/data-and-statistics/2020/11/completed-results-of-the-2019-viet-nam-population-and-housing-census/",
         "Official catalogue says the separate Completed Results publication has 26 detailed tabulations through district level. Original body not acquired: NSO host reset connections in this run."),
        ("vnm-nso-completed2019-original", "NSO Completed Results of the 2019 census original PDF",
         "https://www.nso.gov.vn/wp-content/uploads/2019/12/Ket-qua-toan-bo-Tong-dieu-tra-dan-so-va-nha-o-2019.pdf",
         "Official original PDF location indexed but connection reset; no district values acquired or adopted."),
        ("vnm-nso-census-warehouse2019", "NSO 2019 census data warehouse",
         "https://portal.thongke.gov.vn/khodulieudanso2019/Default.aspx",
         "Official data-warehouse location indexed; host did not resolve in this environment. No table content or geographic availability adopted."),
        ("vnm-nso-pressrelease2019", "NSO release of 2019 census results",
         "https://www.nso.gov.vn/en/events/2019/12/press-release-on-results-of-the-population-and-housing-census-01-4-2019/",
         "Official press release independently states national population 96,208,984 and notes 9% sample subjects; no new province observation adopted from it."),
    ]:
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": "National Statistics Office of Viet Nam", "reference_period": "2019 census",
            "geographic_level": "catalogue; table geography must be checked",
            "status": "partial", "retrieved_at": now,
            "license": "Official public page; reuse terms unverified", "note": note})
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith("VNM_GSO2019_")]
    data["observations"] = [x for x in data["observations"]
                            if not x["indicator_id"].startswith("VNM_GSO2019_")]
    for field, (indicator_id, name, population) in FIELDS.items():
        data["indicators"].append({"id": indicator_id, "name": name, "theme": "Population",
            "unit": "people", "definition": "Direct 1 April 2019 census Table 1 count; urban/rural "
                "classification and sex are as published. Historical 63-province geography, not "
                "2025 province or commune units. No aggregation or WDI harmonisation applied.",
            "population": population, "source_id": SOURCE_ID, "aggregation": "none",
            "display_decimals": 0, "measurement_method": METHOD})

    def observation(tid, field, value, locator):
        data["observations"].append({"territory_id": tid,
            "indicator_id": FIELDS[field][0], "period": "2019", "value": value,
            "status": "observed", "source_id": SOURCE_ID,
            "measurement_method": METHOD, "population_scope": FIELDS[field][2],
            "provenance": "source_reported", "boundary_version": BOUNDARY,
            "source_locator": locator + ", column " + field})

    for field, value in national["values"].items():
        observation("VNM", field, value, national["source_locator"])
    province_ids = []
    for row in provinces:
        ordinal = row["source_row_ordinal"]
        tid = f"VNM:GSO2019:P{ordinal:02d}"
        province_ids.append(tid)
        data["territories"].append({"id": tid, "name": row["name"],
            "level": "census_province_city_2019", "type": "2019 census province/city reporting unit",
            "parent_id": "VNM", "official_code": None,
            "code_system": "GSO/UNFPA Table 1 row ordinal; not an official administrative code",
            "source_row_ordinal": ordinal, "boundary_version": BOUNDARY,
            "source_id": SOURCE_ID,
            "reconciliation_status": "2019 table row verified; official code, matched polygon and 2025 crosswalk pending"})
        for field, value in row["values"].items():
            observation(tid, field, value, row["source_locator"])
    require(len(data["territories"]) == 64 and len(province_ids) == 63,
            "Expected country plus 63 historical province/city areas")
    require(sum(x["values"]["total"] for x in provinces) == national["values"]["total"],
            "Published country/province sum mismatch")
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("vnm-")]
    reference_docs = [
        ("vnm-law-planning-2017", "2017 Law on Planning, official catalogue", "planning_law",
         "https://vanban.chinhphu.vn/default.aspx?docid=192206&pageid=27160", "2017",
         "Catalogue and law PDF link identified; amendments and application to 2025 local government unassessed."),
        ("vnm-law-local-government-2025", "2025 Law on Local Government Organization", "planning_law",
         "https://xaydungchinhsach.chinhphu.vn/toan-van-luat-so-72-2025-qh15-to-chuc-chinh-quyen-dia-phuong-119250618161434371.htm", "2025",
         "Current two-level local-government framework identified; planning powers need article-level review."),
        ("vnm-resolution-province-reform-2025", "Resolution 202/2025/QH15: 34 province-level units", "geography_reference",
         "https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-quyet-so-202-2025-qh15-ve-sap-xep-don-vi-hanh-chinh-cap-tinh-119250612174148722.htm", "2025",
         "2025 structure is distinct from the 63 historical 2019 census areas; no crosswalk adopted."),
        ("vnm-decision-code-list-2025", "2025 administrative code list (Decision 19/2025/QD-TTg)", "geography_reference",
         "https://xaydungchinhsach.chinhphu.vn/bang-danh-muc-va-ma-so-cua-34-tinh-thanh-moi-cac-don-vi-hanh-chinh-cap-xa-moi-11925070418263625.htm", "2025",
         "34 province and 3,321 commune codes for 2025 edition; not 2019 Table 1 codes."),
        ("vnm-hanoi-plan-2026-2030-location", "Hà Nội 2026–2030 socioeconomic plan, source location", "plan",
         "https://vanban.hanoi.gov.vn/van-ban-chi-dao-dieu-hanh/ve-ke-hoach-phat-trien-kinh-te-xa-hoi-5-nam-2026-2030-239036", "2026–2030",
         "Current-city example; attachment content and post-2025 boundary not reconciled to historical 2019 Hà Nội."),
        ("vnm-kienhung-plan-2026-location", "Kiến Hưng ward 2026 socioeconomic plan, source location", "plan",
         "https://kienhung.hanoi.gov.vn/van-ban-chi-dao-dieu-hanh/nghi-quyet-ve-ke-hoach-phat-trien-kinh-te-xa-hoi-nam-2026-230295", "2026",
         "Current ward example only; not assigned to a 2019 census area. Attachment content unassessed."),
    ]
    for source_id, title, kind, url, period, note in reference_docs:
        availability = "unverified" if source_id.startswith(("vnm-hanoi-", "vnm-kienhung-")) else "link_verified"
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": "Government of Viet Nam" if not source_id.startswith("vnm-hanoi-")
                and not source_id.startswith("vnm-kienhung-") else "Hà Nội local government",
            "reference_period": period, "geographic_level": "national or current local reference",
            "status": "partial", "retrieved_at": now,
            "license": "Official public page; reuse terms unverified", "note": note})
        data["documents"].append({"id": source_id, "territory_id": "VNM",
            "category": "reference", "kind": kind, "title": title, "url": url,
            "source_id": source_id, "period": period, "availability": availability,
            "official_status": "unverified", "note": note})
    data["planning"] = {"title": "Local planning and supporting evidence",
        "purpose": "Inspect selected-area historical census conditions and locate the current competent province or commune plan, budget, implementation and evaluation for the actual 2025 jurisdiction.",
        "system": {"label": "Viet Nam planning and local government references",
            "scope": "2019 census areas are statistical reporting areas. In 2025 local-government geography changed; plan ownership must be verified against current jurisdictions.",
            "cycle": "Current statutory and operational cycles require plan-by-plan verification.",
            "source_ids": ["vnm-law-planning-2017", "vnm-law-local-government-2025",
                           "vnm-resolution-province-reform-2025", "vnm-decision-code-list-2025"]},
        "sections": [{"id": key, "label": label} for key, label in (
            ("plan", "Local development and socioeconomic plans"),
            ("budget", "Budgets"), ("implementation", "Implementation and actual spending"),
            ("evaluation", "Official evaluation"), ("reference", "Census and legal references"))]}
    data["analysis"]["comparisons"] = [{"parent_id": "VNM", "member_ids": province_ids,
        "label": "2019 GSO/UNFPA province and city census rows",
        "membership_note": "The 63 historical province/city Table 1 rows form a complete non-overlapping 2019 country roster for all nine adopted person-count fields; each direct column sums to the printed country row. This is not the 2025 administrative roster. Six separately printed socio-economic regions are retained in the audit, not mixed into this comparison.",
        "source_ids": [SOURCE_ID]}]
    data["analysis"]["terminal_territory_ids"] = province_ids
    data["analysis"]["default_indicator_id"] = FIELDS["total"][0]
    data["analysis"]["latest_values_only"] = True
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
        "gso-unfpa-2019-census-table1-historical-province"] ))
    data["collection"]["notes"] = [
        "2019 GSO/UNFPA Table 1: nine direct person-count columns for country plus 63 historical provinces/cities (576 adopted observations); all 630 numeric cells including six socio-economic-region rows audited for arithmetic and national reconciliation.",
        "The report's other 59 detailed tables and the separate district-level Completed Results publication are unassessed/not acquired. No district value was inferred from a province.",
        "The 2019 official administrative codes, compatible polygons and post-2025 34-province/3,321-commune crosswalk remain pending; 2008 geoBoundaries reference shapes are removed.",
        "Current planning law, province reform, code directory and two example plan locations found. Hà Nội local catalogues timed out when fetching their bodies. No actual current local plan/budget/expenditure/evaluation body is adopted for a 2019 census area.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith((
            "Initial national-data site inputs only", "2019 GSO/UNFPA Table 1:",
            "The report's other 59", "The 2019 official administrative codes",
            "Current planning law, province reform"))],
    ]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "Table 1 identifies 63 2019 province/city rows by order and name. Official 2019 codes/polygons and 2025 reform crosswalk are not confirmed.",
         "next_action": "Acquire official dated 2019 code/shape originals, audit name and territorial identity, then separately build the 2025 34-province/3,321-commune edition."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Nine direct Table 1 fields are adopted at 2019 country/province level only; six region rows retained in audit. Tables 2-60 and separate district tables require numerical-column, denominator and sample review.",
         "next_action": "Acquire NSO Completed Results original and official historical codes; inspect all report numeric columns, sampled subjects and district tables before adoption."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Official laws and example current local plan locations found. The example plans are post-2025 jurisdictions and cannot be mapped to a 2019 row without verified crosswalk. No actual local plan/budget/expenditure/evaluation content adopted.",
         "next_action": "Acquire representative current province and commune plans, budgets, execution and evaluations; verify authority, period, attachment contents and 2019-to-2025 identity."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]), "adopted_observations": 64 * 9,
        "source_rows_audited": audit["row_counts"], "numeric_cells_audited": 630,
        "observations_by_indicator": dict(Counter(x["indicator_id"] for x in data["observations"]
            if x["indicator_id"].startswith("VNM_GSO2019_"))),
        "country_population": national["values"]["total"],
        "official_compatible_polygons": 0, "independent_acceptance": False,
        "dataset_sha256": digest(data_path)}
    (project / "evidence/VNM_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

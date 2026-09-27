"""Import audited NESDC 2024p province values without a DOPA code/shape join."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from thailand_gpp2024_fields import SECTOR_FIELDS, SECTOR_IDS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "tha-nesdc-gpp2024-workbook"
BOUNDARY = "NESDC GPP 2024p reporting roster; compatible province polygons not verified"
METHOD = "NESDC GPP 2024p at current market prices, provisional published workbook values"
FIELDS = {
    "gpp_million_baht": ("THA_NESDC_GPP_MTHB", "2024p gross provincial product",
                         "Economy", "million Baht", "GPP/GDP at current market prices"),
    "population_thousand_persons": ("THA_NESDC_GPP_POP_THOUSAND", "2024p GPP population denominator",
                                    "Population", "thousand persons", "NESDC population used for GPP per capita"),
    "gpp_per_capita_baht": ("THA_NESDC_GPP_PC_BAHT", "2024p GPP per capita",
                            "Economy", "Baht per person", "NESDC published GPP/GDP per capita"),
}
COLS = {"gpp_million_baht": "C", "population_thousand_persons": "D",
        "gpp_per_capita_baht": "E"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(project):
    audit = json.loads((project / "evidence/THA_GPP2024_AUDIT.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "config/thailand-gpp2024-source-manifest.json").read_text(
        encoding="utf-8"))
    source = next(s for s in manifest["sources"] if s["id"] == SOURCE_ID)
    raw = project / source["raw_path"]
    require(raw.stat().st_size == source["bytes"] and digest(raw) == source["sha256"]
            and audit["source_sha256"] == source["sha256"] and
            audit["numeric_cells_audited"] == 2210 and
            audit["adopted_direct_observations"] == 1872 and
            len(audit["provinces"]) == 77,
            "Pinned GPP 2024p audit changed")
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "THA", "Expected Thailand project")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data["territories"] = [t for t in data["territories"] if t["id"] == "THA"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0].update({"boundary_version": BOUNDARY, "source_id": SOURCE_ID})
    data["country"]["geography_note"] = (
        "This is the NESDC GPP 2024p province reporting roster: 77 provinces including Bangkok. "
        "Its four-digit workbook codes are NESDC economic-region/province labels, not verified "
        "DOPA legal administrative codes. The unrelated 2017 geoBoundaries reference shapes were "
        "removed pending exact code/edition matching. Seven NESDC economic regions are audit-only. "
        "NESDC 2024p population denominators, BORA registration and the NSO 2025 resident census "
        "are distinct series; national WDI values remain separate indicators.")
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("tha-")]
    data["sources"].append({"id": SOURCE_ID,
        "name": "Table of Gross Regional and Provincial Product 2024p",
        "url": source["url"], "catalogue_url": source["catalogue_url"],
        "publisher": "National Economic and Social Development Council, Thailand",
        "reference_period": "2024p (provisional)", "geographic_level": "country, seven economic regions and 77 provinces",
        "status": "ready", "retrieved_at": manifest["retrieved_at"],
        "sha256": source["sha256"], "raw_path": source["raw_path"],
        "license": "Official public workbook; redistribution terms require verification",
        "note": "PER CAPITA columns C:E and 2024p current-price sector column AE in WK/GRP/seven province sheets audited. Country and 77 provinces have 24 direct indicators; seven region rows audit-only. Historical, chain-volume and cluster fields remain priority_unassessed. Population is the GPP per capita denominator, not a census or registration count."})
    for source_id, title, url, publisher, period, note in [
        ("tha-nesdc-gpp-catalogue", "NESDC GPP releases catalogue",
         "https://www.nesdc.go.th/en/info/gross-regional-and-provincial-product-gpp/",
         "National Economic and Social Development Council", "2024p workbook listing",
         "Official release index acquired and hash-pinned; workbook linked there. Other editions need separate audits."),
        ("tha-nesdc-provincial-plan-guide", "NESDC provincial and cluster plan review guidance PDF",
         next(s["url"] for s in manifest["sources"] if s["id"] == "tha-nesdc-provincial-plan-guide"),
         "National Economic and Social Development Council", "2023–2027; FY2025–2027 review",
         "Six-page body acquired; extracted first-line draft label and province/cluster plan scope. Full legal force, all guidance and forms remain unassessed."),
        ("tha-nesdc-provincial-planning-catalogue", "NESDC province and provincial-cluster planning catalogue",
         "https://www.nesdc.go.th/downloadable-documents/province-provincial-cluster/",
         "National Economic and Social Development Council", "FY2025–2027 indexed materials",
         "Official catalogue acquired. Its multiple plan, budget-framework, form and update links need item-by-item review."),
        ("tha-nso-census2025-catalogue", "NSO 2025 population and housing census portal",
         "https://www.nso.go.th/nsoweb/main/summano/aE?set_lang=en",
         "National Statistical Office", "1 April 2025",
         "Portal distinguishes resident census from registered population; preliminary summary is visible. Final-report PDF location indexed but direct request returned HTTP 418, so no province census values adopted."),
        ("tha-nso-census2025-final-location", "NSO 2025 census final report location",
         "https://www.nso.go.th/nsoweb/storage/title_presentation/2026/20260907134505_55192.pdf",
         "National Statistical Office", "2025 census, September 2026 publication",
         "Official search-index PDF location; direct request returned HTTP 418 and browser PDF view did not load. Province tables and report contents unacquired."),
        ("tha-bora-registration-downloads", "BORA population-registration download catalogue",
         "https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php",
         "Bureau of Registration Administration, Department of Provincial Administration", "2025 and earlier",
         "Official indexed catalogue exposes year and province/district/subdistrict/village downloads with registration codes; host DNS did not resolve locally, no file acquired."),
        ("tha-dopa-administrative-codes-location", "DOPA administrative-code search location",
         "https://stat.bora.dopa.go.th/stat/statnew/statMenu/newStat/ccaa.php",
         "Department of Provincial Administration", "current edition unverified",
         "Official indexed province/district/subdistrict code register; body and dated version not acquired, no code join."),
        ("tha-chiangmai-strategy-index", "Chiang Mai provincial plan and progress catalogue",
         "https://www.chiangmai.go.th/web2563/strategy/",
         "Chiang Mai Province", "FY2025–2026 indexed",
         "Official search index lists plan, annual action, budget-progress and implementation reports. Direct PDF requests timed out; content/approval/current status unverified."),
        ("tha-chiangmai-plan-2025-location", "Chiang Mai 2023–2027 plan, FY2025 review PDF location",
         "https://www.chiangmai.go.th/managing/public/D12/12D29Apr2025204613.pdf",
         "Chiang Mai Province", "2023–2027; FY2025 review",
         "Official search-index PDF location only. Request timed out; actual plan body, issuer decision and territorial identity crosswalk unverified."),
        ("tha-open-data-district-registration-catalogue", "Thai Open Government district population registration dataset",
         "https://data.go.th/en/dataset/0405_01_0005",
         "Digital Government Development Agency / National Statistical Office", "2021–2025 indexed",
         "Official catalogue location indexed as DOPA-based district/sex population. Requests returned HTTP 403; CSV/JSON bodies, local coverage, code edition and rights were not acquired or adopted."),
    ]:
        item = {"id": source_id, "name": title, "url": url, "publisher": publisher,
                "reference_period": period, "geographic_level": "national or source-specific current province",
                "status": "partial", "retrieved_at": manifest["retrieved_at"],
                "license": "Official public location; item terms unverified", "note": note}
        pinned = next((s for s in manifest["sources"] if s["id"] == source_id), None)
        if pinned:
            item.update({"raw_path": pinned["raw_path"], "sha256": pinned["sha256"]})
        data["sources"].append(item)
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith("THA_NESDC_")]
    data["observations"] = [x for x in data["observations"]
                            if not x["indicator_id"].startswith("THA_NESDC_")]
    for field, (indicator_id, name, theme, unit, population) in FIELDS.items():
        data["indicators"].append({"id": indicator_id, "name": name, "theme": theme,
            "unit": unit,
            "definition": "Direct provisional 2024p NESDC national-accounts workbook value on its published 77-province roster. "
                "GPP at current market prices and its population denominator; per-capita is published, not a province average. "
                "Not harmonised with WDI, registration population or resident census.",
            "population": population, "source_id": SOURCE_ID, "aggregation": "none",
            "display_decimals": 1 if field != "gpp_per_capita_baht" else 0,
            "measurement_method": METHOD})
    for key, label, group in SECTOR_FIELDS:
        data["indicators"].append({"id": SECTOR_IDS[label],
            "name": f"2024p current-price {label}", "theme": "Economy",
            "unit": "million Baht",
            "definition": "Direct 2024p provisional NESDC current-market-price sector row. "
                "Broad Agriculture, Industrial and Services rows overlap their detailed components; "
                "do not sum all displayed sector indicators. The duplicate agriculture alias "
                "and Non-Agriculture subtotal are audit-only. No real-price/CVM or historical comparison is implied.",
            "population": "NESDC 2024p current-price country or GPP province reporting unit",
            "source_id": SOURCE_ID, "aggregation": "none", "display_decimals": 1,
            "measurement_method": METHOD,
            "source_group": group})

    def observation(tid, field, value, row):
        data["observations"].append({"territory_id": tid,
            "indicator_id": FIELDS[field][0], "period": "2024p", "value": value,
            "status": "observed", "source_id": SOURCE_ID,
            "measurement_method": METHOD, "population_scope": FIELDS[field][4],
            "provenance": "source_reported", "boundary_version": BOUNDARY,
            "source_locator": f"PER CAPITA!{COLS[field]}{row}"})

    for field, value in audit["country"]["values"].items():
        observation("THA", field, value, audit["country"]["row"])
    def sector_observations(tid, block_key):
        sector = audit["sector_2024p_current_price"][block_key]
        for _, label, _ in SECTOR_FIELDS:
            cell = sector["fields"][label]
            data["observations"].append({"territory_id": tid,
                "indicator_id": SECTOR_IDS[label], "period": "2024p",
                "value": cell["value"], "status": "observed", "source_id": SOURCE_ID,
                "measurement_method": METHOD,
                "population_scope": "NESDC 2024p current-price country or GPP province reporting unit",
                "provenance": "source_reported", "boundary_version": BOUNDARY,
                "source_locator": cell["locator"]})
    sector_observations("THA", "THA")
    province_ids = []
    for row in audit["provinces"]:
        tid = f"THA:NESDC2024:{row['nesdc_code']}"
        province_ids.append(tid)
        data["territories"].append({"id": tid, "name": row["name"].title(),
            "level": "province_2024p", "type": "NESDC GPP 2024p province reporting unit",
            "parent_id": "THA", "official_code": None,
            "code_system": "NESDC economic-region/province workbook code; DOPA administrative code unverified",
            "provider_code": row["nesdc_code"], "nesdc_region": row["region"],
            "boundary_version": BOUNDARY, "source_id": SOURCE_ID,
            "reconciliation_status": "workbook row verified; legal code, geometry and current plan jurisdiction not joined"})
        for field, value in row["values"].items():
            observation(tid, field, value, row["row"])
        sector_observations(tid, row["nesdc_code"])
    require(len(data["territories"]) == 78 and len(province_ids) == 77,
            "Country plus 77 provinces expected")
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("tha-")]
    for source_id, kind, title, period, availability, note in [
        ("tha-nesdc-provincial-plan-guide", "planning_guidance",
         "NESDC province/cluster plan review guidance; draft-status caution", "2023–2027", "body_acquired",
         "Six-page PDF acquired; first page and plan-scope sections inspected. Extracted text begins with a draft label. Do not infer binding current law or plan approval."),
        ("tha-nesdc-provincial-planning-catalogue", "planning_guidance",
         "NESDC provincial planning and budget catalogue", "FY2025–2027 indexed", "link_verified",
         "Catalogue lists multi-year plan rules, annual plans and budget framework; each body and current applicability need separate review."),
        ("tha-nso-census2025-catalogue", "census_reference",
         "NSO 2025 resident census portal", "2025", "link_verified",
         "Preliminary summary only; official final PDF could not be acquired and no province census count is adopted."),
        ("tha-bora-registration-downloads", "statistics_reference",
         "BORA population registration downloads", "2025", "unverified",
         "Indexed by web search, but host DNS failed; registered population is a separate series."),
        ("tha-chiangmai-strategy-index", "plan",
         "Chiang Mai current plan, action and progress catalogue", "FY2025–2026", "unverified",
         "Current province example only. Direct plan and project PDF fetch timed out; no local content, approval, budget actual or administrative code join adopted."),
    ]:
        item = next(s for s in data["sources"] if s["id"] == source_id)
        data["documents"].append({"id": source_id, "territory_id": "THA",
            "category": "reference", "kind": kind, "title": title,
            "url": item["url"], "source_id": source_id, "period": period,
            "availability": availability, "official_status": "unverified", "note": note})
    data["planning"] = {"title": "Provincial planning and supporting evidence",
        "purpose": "Review a selected province's economic baseline, then acquire its actual provincial plan, annual action, budget, implementation and evaluation from the competent issuing body.",
        "system": {"label": "Thailand province and provincial-cluster planning references",
            "scope": "NESDC guide addresses provinces and provincial clusters. Local administrative organisations have distinct powers and geography that require separate legal review; a GPP province code alone does not assign a plan.",
            "cycle": "The acquired NESDC guide concerns the 2023–2027 plans and FY2025–2027 reviews; current application and local documents require verification.",
            "source_ids": ["tha-nesdc-provincial-plan-guide", "tha-nesdc-provincial-planning-catalogue"]},
        "sections": [{"id": key, "label": label} for key, label in (
            ("plan", "Provincial and local plans"), ("budget", "Budgets and projects"),
            ("implementation", "Implementation and actual spending"),
            ("evaluation", "Official evaluation"), ("reference", "Statistical and planning references"))]}
    data["analysis"]["comparisons"] = [{"parent_id": "THA", "member_ids": province_ids,
        "label": "NESDC 2024p GPP province rows",
        "membership_note": "All 77 non-overlapping provisional 2024p province GPP, population-denominator and 21 current-price sector rows reconcile to their published whole-kingdom row. Seven NESDC economic-region rows remain audit-only. Sector aggregates overlap their detail; per-capita values are direct printed values and are never summed or averaged. This is not a DOPA code/shape or provincial-plan authority crosswalk.",
        "source_ids": [SOURCE_ID]}]
    data["analysis"]["terminal_territory_ids"] = province_ids
    data["analysis"]["default_indicator_id"] = FIELDS["gpp_per_capita_baht"][0]
    data["analysis"]["latest_values_only"] = True
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
        "nesdc-gpp-2024p-province"] ))
    data["collection"]["notes"] = [
        "NESDC 2024p provisional country plus 77 provinces: GPP, its population denominator, per capita and 21 distinct current-price sector rows (1,872 direct observations); seven regional rows and two redundant sector rows audit-only. All 2,210 source cells reconciled.",
        "NO!AE691 prints a Kam Phaeng Phet detailed-table population 1.53195298 thousand above PER CAPITA!D47; only the latter denominator reconciles to published GPP per capita and province/national totals. The conflicting detailed-table population is not adopted.",
        "NESDC 1995–2023, chain-volume, Regions to GDP and CLUSTERS fields are priority_unassessed, not absent. NSO 2025 resident census and BORA registration sources were located but not acquired from their blocked hosts.",
        "NESDC workbook four-digit codes are not adopted as legal DOPA codes. No exact matched current polygon is available; the 2017 provider shapes were removed.",
        "NESDC province/cluster planning catalogue and six-page draft-labelled guide acquired. Chiang Mai plan/budget/progress locations indexed, but their PDFs timed out; no selected province plan or actual expenditure is adopted.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith((
            "Initial national-data site inputs only", "NESDC PER CAPITA sheet:",
            "NESDC 2024p provisional country plus", "Other eleven NESDC",
            "NO!AE691 prints",
            "NESDC 1995–2023", "NESDC workbook four-digit codes",
            "NESDC province/cluster planning catalogue"))],
    ]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "NESDC supplies 77 province economic-roster codes; DOPA official administrative codes, dated boundary and matched polygons are not confirmed.",
         "next_action": "Acquire the DOPA code register and dated province polygons; reconcile exactly, including Bangkok, before displaying an official boundary."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "GPP workbook provides 24 adopted 2024p indicators per province. NO!AE691 detailed population conflicts with PER CAPITA!D47 and is withheld. Historical 1995–2023, CVM, Regions to GDP and CLUSTERS fields remain unassessed; NSO 2025 census final province tables are unacquired. BORA registration downloads failed DNS locally.",
         "next_action": "Audit the remaining workbook periods/measurements and obtain official NSO 2025 census and BORA files from working official endpoints, keeping populations distinct."},
        {"category": "planning_documents", "status": "partial",
         "detail": "NESDC planning guidance body and catalogue are acquired, but the guide has a draft label; Chiang Mai plan, budget-progress and implementation PDFs timed out. No local plan content, status, actual spending or evaluation adopted.",
         "next_action": "Acquire current provincial/cluster legal rules and representative issuer-approved plans, budget, actual spending, implementation and evaluation; resolve source-level and legal jurisdiction."},
    ])
    failed_wdi = {gap["source_id"]: gap for gap in data["gaps"]
                  if gap["category"] == "source_collection" and gap["status"] == "failed"
                  and gap.get("source_id", "").startswith("wb-")}
    for gap in data["gaps"]:
        if gap["category"] == "indicator_coverage" and gap.get("source_id") in failed_wdi:
            gap["status"] = "failed"
            gap["detail"] = ("WDI request failed in this run; country availability and values remain "
                             "unknown. No zero or source absence is inferred.")
            gap["next_action"] = failed_wdi[gap["source_id"]]["next_action"]
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]),
        "adopted_observations": audit["adopted_direct_observations"],
        "source_numeric_cells_audited": audit["numeric_cells_audited"], "provinces": 77,
        "observations_by_indicator": dict(Counter(x["indicator_id"] for x in data["observations"]
            if x["indicator_id"].startswith("THA_NESDC_"))),
        "country_gpp_million_baht": audit["country"]["values"]["gpp_million_baht"],
        "country_population_thousand": audit["country"]["values"]["population_thousand_persons"],
        "official_compatible_polygons": 0, "independent_acceptance": False,
        "dataset_sha256": digest(data_path)}
    (project / "evidence/THA_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

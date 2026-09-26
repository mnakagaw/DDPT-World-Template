"""Build a scoped Pakistan 2023 census candidate from pinned PBS Table 1 files.

Only the directly reported country-table scope, four provinces and 136 districts
are represented. The PBS Table 1 national scope excludes AJK and GB in these
source files. District workbook row numbers are reproducible locators, never
official geographic codes or proof of current local-government jurisdiction.
"""

import argparse
import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path


inventory = runpy.run_path(str(Path(__file__).with_name("inventory-pakistan-pbs2023.py")))
FILES = inventory["FILES"]
HASHES = inventory["HASHES"]
SOURCE_NAMES = inventory["SOURCE_NAMES"]
ADOPTED = inventory["ADOPTED"]
FIELDS = inventory["FIELDS"]
source_rows = inventory["source_rows"]
sha256 = inventory["sha256"]
require = inventory["require"]

SCOPE = "PAK:PBS2023:TABLE1_SCOPE"
PREFIX = "PAK_PBS2023_T1_"
CATALOGUE = "pak-pbs2023-result-excel"
METHOD = "PBS_2023_census_Table1_direct_reported_count"
BOUNDARY = "PBS 2023 census reporting geography; matching official polygons not acquired"
REGIONS = {"kp": "Khyber Pakhtunkhwa", "punjab": "Punjab", "sindh": "Sindh",
           "balochistan": "Balochistan"}
ADOPTION = (
    ("total", "population_2023", "POPULATION", "2023 Census Table 1 population", "C"),
    ("total", "male_2023", "MALE", "2023 Census Table 1 males", "D"),
    ("total", "female_2023", "FEMALE", "2023 Census Table 1 females", "E"),
    ("total", "transgender_2023", "TRANSGENDER", "2023 Census Table 1 transgender persons", "F"),
    ("rural", "population_2023", "RURAL", "2023 Census Table 1 rural population", "C"),
    ("urban", "population_2023", "URBAN", "2023 Census Table 1 urban population", "C"),
)
LEGAL = (
    ("pak-punjab-local-government-act-2025", "Punjab Local Government Act 2025",
     "https://lgcd.punjab.gov.pk/system/files/PLGA_2025.pdf", "lgcd.punjab.gov.pk", "punjab",
     "Law is listed by Punjab LG&CD; local-body types and amendments must be read before assigning a 2023 census district as a 2026 planning unit."),
    ("pak-kp-local-government-act-2013", "Khyber Pakhtunkhwa Local Government Act 2013",
     "https://www.pakp.gov.pk/act/the-khyber-pakhtunkhwa-local-government-act-2013/", "pakp.gov.pk", "kp",
     "Provincial Assembly law location; later amendments and current bodies require exact-version review."),
    ("pak-kp-tehsil-rules-2022", "KP City/Tehsil Local Government Rules of Business 2022",
     "https://kpcode.kp.gov.pk/uploads/Khyber_Pakhtunkhwa_CityTehsil_Local_Government_Rules_of_Business_2022.pdf", "kpcode.kp.gov.pk", "kp",
     "Rules address a Tehsil annual development plan with Tehsil Council approval; actual area plan and budget not acquired."),
    ("pak-sindh-local-government-act-2013", "Sindh Local Government Act 2013, Section 76",
     "https://www.sindhlaws.gov.pk/setup/publications_SindhCode/PUB-NEW-18-000156.pdf", "sindhlaws.gov.pk", "sindh",
     "Section 76 concerns Council development plans and budgets; current amendments, actual councils and plans require verification."),
    ("pak-balochistan-local-government-act-2010", "Balochistan Local Government Act 2010, Sections 86, 94-95",
     "https://balochistan.gov.pk/wp-content/uploads/2024/10/Balochistan-Local-Government-Act-2010.pdf", "balochistan.gov.pk", "balochistan",
     "Base law discusses Local Council development plans and budget; 2013-2023 amendments and actual plans remain to be checked."),
    ("pak-ict-local-government-act-2015", "Islamabad Capital Territory Local Government Act 2015, Sections 48-49",
     "https://pakistancode.gov.pk/pdffiles/administrator2cd0fb199558bc5fb239d66d51d21e27.pdf", "pakistancode.gov.pk", "islamabad",
     "Official code edition has Development Plan approval and budget provisions; later amendments and current bodies require exact-version review."),
)
OTHER_LOCATIONS = (
    ("pak-pbs-census2023-gis", "PBS Census 2023 GIS and administrative unit sources",
     "https://www.pbs.gov.pk/gis/", "Pakistan Bureau of Statistics",
     "PBS explains frozen census geography and census block codes; source-compatible polygon and district code crosswalk not acquired."),
    ("pak-pbs-admin-districts-2023", "PBS administrative districts as of 1 March 2023",
     "https://www.pbs.gov.pk/wp-content/uploads/2020/07/List-of-Administrative-Districts-2023.pdf",
     "Pakistan Bureau of Statistics", "District list location verified; serial numbers not adopted as official area codes."),
    ("pak-pbs-fop-census-district-codes-2023", "PBS Census 2023 field operation plan: census district codes",
     "https://www.pbs.gov.pk/wp-content/uploads/2020/07/FOP_final_26-2-23_final.pdf",
     "Pakistan Bureau of Statistics", "Census District code list location verified; several census districts can occur within one administrative district. No code was joined to Table 1 administrative district rows."),
    ("pak-pc-psdp-2026-27", "Federal PSDP 2026-27 and expenditure catalogue",
     "https://www.pc.gov.pk/web/psdp", "Ministry of Planning, Development & Special Initiatives",
     "Federal programme and expenditure locations; no 2023 census district plan, budget or execution is inferred."),
    ("pak-pc-development-manual", "Planning Commission development project manual catalogue",
     "https://www.pc.gov.pk/web/downloads", "Ministry of Planning, Development & Special Initiatives",
     "National project guidance location, not an area-specific approved plan."),
)


def sid(key):
    return f"pak-pbs2023-table1-{key}"


def region_id(key):
    return f"PAK:PBS2023:PROVINCE:{key.upper()}"


def district_id(key, group):
    return f"PAK:PBS2023:DIST:{key.upper()}:R{group['row']}"


def main(project):
    evidence = project / "evidence"
    audit = json.loads((evidence / "PAK_PBS2023_TABLE1_AUDIT.json").read_text(encoding="utf-8"))
    require(audit["catalogue_sha256"] == HASHES["pbs2023-result-excel-catalog.html"] and
            audit["all_populated_numeric_cells"] == 19899 and audit["numbered_catalogue_tables"] == 33,
            "Run the pinned full source inventory first")
    require(audit["districts"] == {"kp": 35, "punjab": 36, "sindh": 30,
                                    "balochistan": 34, "islamabad": 1}, "District ledger changed")
    require(audit["exceptions"] == [
        {"source": "kp", "row": 473, "field": "population_2023", "issue": "rural_plus_urban_differs"},
        {"source": "kp", "row": 474, "field": "population_2023", "issue": "sex_sum_differs"}],
        "Source inconsistency ledger changed")
    require(ADOPTED == {(r, f) for r, f, *_ in ADOPTION}, "Inventory adoption list changed")
    raw = project / "raw"
    for name, expected in HASHES.items():
        require(sha256(raw / name) == expected, f"Source hash changed: {name}")
    groups = {key: source_rows(raw / name, key)[0] for key, name in FILES.items()}
    national = groups["national"][0]
    require(national["name"] == "PAKISTAN" and
            national["parts"]["total"]["values"][1] == 241499431,
            "Table 1 population/scope changed")
    data_file = project / "data/dashboard.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "PAK", "Expected Pakistan candidate")
    data["territories"] = [t for t in data["territories"] if t["id"] == "PAK"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("pak-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("pak-")]
    now = datetime.now(timezone.utc).isoformat()
    data["country"]["geography_note"] = (
        "PBS Census 2023 Table 1 reports 241,499,431 people for the four provinces and Islamabad Capital Territory "
        "listed in its national workbook. PBS GIS lists Azad Jammu & Kashmir and Gilgit-Baltistan separately; "
        "they are not included in this Table 1 workbook scope. Table 1 reports headcounts from restricted "
        "areas for which later detailed characteristics were not obtained. Census reporting rows have no "
        "official district codes in these XLSX files; 2023 polygons and current local-government boundaries "
        "are not joined. WDI national economy estimates remain separate.")
    data["territories"].append({
        "id": SCOPE, "name": "Four provinces and ICT (PBS Census 2023 Table 1)",
        "level": "census_coverage", "type": "statistical_coverage_area", "parent_id": "PAK",
        "official_code": None, "code_system": "PBS Table 1 national reporting scope; no separate area code in source",
        "boundary_version": BOUNDARY, "source_id": sid("national"),
        "reconciliation_status": "Source workbook scope verified; AJK/GB not included; polygons unacquired",
    })
    for key, name in REGIONS.items():
        data["territories"].append({
            "id": region_id(key), "name": f"{name} (2023 census)",
            "level": "province_2023", "type": "census_province", "parent_id": SCOPE,
            "official_code": None, "code_system": "PBS Table 1 named province; no code in acquired workbook",
            "boundary_version": BOUNDARY, "source_id": sid(key),
            "reconciliation_status": "Named PBS 2023 reporting unit; official code and compatible polygon unacquired",
        })
    by_territory = [(SCOPE, "national", national)]
    for key in REGIONS:
        group = groups[key][0]
        require(group["level"] == "province", f"First row not province: {key}")
        by_territory.append((region_id(key), key, group))
    district_ids = []
    for key in ("kp", "punjab", "sindh", "balochistan", "islamabad"):
        for group in groups[key]:
            if group["level"] != "district":
                continue
            tid = district_id(key, group)
            district_ids.append(tid)
            name = group["name"].removesuffix(" DISTRICT").title()
            data["territories"].append({
                "id": tid, "name": f"{name} District (2023 census)",
                "level": "district_2023", "type": "census_district",
                "parent_id": region_id(key) if key != "islamabad" else SCOPE,
                "official_code": None,
                "code_system": "PBS 2023 Table 1 workbook row; internal ID is not an official code",
                "source_row": group["row"], "boundary_version": BOUNDARY,
                "source_id": sid(key),
                "reconciliation_status": "Direct PBS 2023 named district; official code, local-government match and compatible polygon unacquired",
            })
            by_territory.append((tid, key, group))
    require(len(district_ids) == 136 and len(data["territories"]) == 142,
            "Expected root, scope, four provinces and 136 districts")
    data["sources"].append({
        "id": CATALOGUE, "name": "PBS 7th Population and Housing Census detailed Excel table catalogue",
        "url": inventory["CATALOGUE_URL"], "publisher": "Pakistan Bureau of Statistics",
        "reference_period": "2023 census", "geographic_level": "national to lower reporting units",
        "status": "partial", "raw_path": "raw/pbs2023-result-excel-catalog.html",
        "sha256": HASHES["pbs2023-result-excel-catalog.html"], "retrieved_at": now,
        "license": "Official public catalogue; redistribution terms for workbook bodies need review",
        "note": "33 numbered entries/305 unique-in-row XLSX links; only six Table 1 files acquired. Table 10 KP link in catalogue incorrectly points to Table 1 KP districts, and is not treated as Table 10 acquisition.",
    })
    for key, name in FILES.items():
        data["sources"].append({
            "id": sid(key), "name": f"PBS Census 2023 Table 1, {key} direct XLSX",
            "url": SOURCE_NAMES[key], "publisher": "Pakistan Bureau of Statistics",
            "reference_period": "2023 census", "geographic_level": "national Table 1 scope" if key == "national"
            else "2023 named province and district reporting units",
            "status": "partial", "raw_path": f"raw/{name}", "sha256": HASHES[name],
            "retrieved_at": now, "license": "Official public XLSX; redistribution terms need review",
            "note": "Acquired and full numerical column inventory completed. Only six 2023 count/row-class combinations at scope/province/district are adopted. All other numbers and lower unit rows remain unassessed. See source locator per observation and PAK_PBS2023_TABLE1_AUDIT.json.",
        })
    for source_id, title, url, publisher, note in OTHER_LOCATIONS:
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": publisher, "reference_period": "location checked 2026-09-27",
            "geographic_level": "national", "status": "not_collected", "retrieved_at": now,
            "license": "Link verified; exact body and redistribution terms require review", "note": note})
    for source_id, title, url, publisher, region, note in LEGAL:
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": publisher, "reference_period": "cited law version; amendments pending review",
            "geographic_level": f"{region} legal source", "status": "not_collected",
            "retrieved_at": now, "license": "Official law location; local copy and latest amendments not acquired",
            "note": note})
    for row_class, field, suffix, label, column in ADOPTION:
        iid = PREFIX + suffix
        data["indicators"].append({
            "id": iid, "name": label, "theme": "Population", "unit": "people",
            "definition": f"Direct count in PBS 2023 Census Table 1, {row_class} reporting row, {field}. "
                          "This Table 1 headcount coverage differs from the detailed-characteristic base in later tables. "
                          "The Table 1 Pakistan row is a separate four-province-plus-ICT scope, not a WDI estimate.",
            "population": "PBS 2023 Table 1 reporting population in four provinces and ICT",
            "source_id": CATALOGUE, "aggregation": "none", "measurement_method": METHOD,
            "series_family": "census", "display_decimals": 0,
        })
        field_index = FIELDS.index(field)
        for territory, key, group in by_territory:
            part = group["parts"][row_class]
            value = part["values"][field_index]
            require(type(value) is int and value >= 0,
                    f"Missing/noninteger adopted cell: {key}:{part['row']}:{field}")
            data["observations"].append({
                "territory_id": territory, "indicator_id": iid, "period": "2023",
                "value": value, "status": "observed", "source_id": sid(key),
                "measurement_method": METHOD, "provenance": "source_reported",
                "source_locator": f"Sheet1!{column}{part['row']}; name={group['name']}; class={row_class}; file={FILES[key]}",
                "boundary_version": BOUNDARY,
            })
    comparisons = [{
        "parent_id": SCOPE,
        "member_ids": [*[region_id(k) for k in REGIONS], district_id("islamabad", groups["islamabad"][0])],
        "label": "Four provinces and Islamabad district, PBS Census 2023 Table 1",
        "membership_note": "These five Table 1 source rows exactly cover its national headcount. AJK and GB are not in the Table 1 source scope; no WDI or current-local-government equivalence.",
        "source_ids": [sid(x) for x in FILES],
    }]
    for key, name in REGIONS.items():
        members = [district_id(key, g) for g in groups[key] if g["level"] == "district"]
        comparisons.append({
            "parent_id": region_id(key), "member_ids": members,
            "label": f"PBS Census 2023 districts of {name}",
            "membership_note": "All directly reported 2023 Table 1 district rows exactly cover their source province counts. Uncoded census reporting geography, not verified local council membership.",
            "source_ids": [sid(key)],
        })
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = district_ids
    data["analysis"]["default_indicator_id"] = "SP.POP.TOTL"
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {
        "title": "Provincial local planning sources and Census 2023 evidence",
        "purpose": "Use the selected 2023 census reporting area for diagnosis, then identify the competent current local government and acquire its actual plan, budget, expenditure and evaluation.",
        "system": {
            "label": "Province- and ICT-specific local government law; federal PSDP shown as national reference only",
            "scope": "Punjab, KP, Sindh, Balochistan and ICT have different local government laws and planning units. A census district is not automatically a local council.",
            "cycle": "Provincial/ICT current plan periods and statuses unverified; federal FY 2026-27 PSDP location checked",
            "source_ids": [x[0] for x in LEGAL] + ["pak-pc-psdp-2026-27"],
        },
        "sections": [
            {"id": "plan", "label": "Applicable local development plans"},
            {"id": "budget", "label": "Local budget and allocations"},
            {"id": "implementation", "label": "Expenditure and implementation"},
            {"id": "evaluation", "label": "Official evaluation"},
            {"id": "reference", "label": "Census and legal source locations"},
        ],
    }
    data["documents"].append({
        "id": "pak-pbs-table1-national-reference", "territory_id": SCOPE,
        "category": "reference", "kind": "census_source", "title": "PBS 2023 Census Table 1 national XLSX",
        "url": SOURCE_NAMES["national"], "source_id": sid("national"), "period": "2023",
        "availability": "body_acquired", "official_status": "official_statistical_release",
        "territory_match": {"territory_id": SCOPE, "country_id": "PAK",
            "type": "statistical_coverage_area",
            "code_system": "PBS Table 1 national reporting scope; no separate area code in source",
            "official_code": None, "boundary_version": BOUNDARY,
            "method": "The Pakistan Table 1 total equals its four province and ICT rows; the source workbook has no AJK/GB rows",
            "source_id": sid("national"), "locator": "Sheet1!A5:A27 reporting ledger; C5:C27 population",
            "checked_at": now},
        "official_evidence": {"source_id": sid("national"),
            "locator": "Sheet1!A1 Table 1 title; Sheet1!A5 Pakistan reporting row; Sheet1!A29/A31/A33 coverage notes",
            "checked_at": now},
        "note": "Source headcount covers four provinces and ICT, with the Table 1 restricted-area caveat. Not an approved local plan.",
    })
    data["documents"].append({
        "id": "pak-pc-federal-psdp-reference", "territory_id": "PAK",
        "category": "reference", "kind": "national_programme_location",
        "title": "Federal Public Sector Development Programme FY 2026-27 catalogue",
        "url": "https://www.pc.gov.pk/web/psdp", "source_id": "pak-pc-psdp-2026-27",
        "period": "FY 2026-27", "availability": "link_verified", "official_status": "unverified",
        "note": "Federal programme location only; no district-specific local plan, approval or execution adopted.",
    })
    for source_id, title, url, _, key, note in LEGAL:
        territory = region_id(key) if key in REGIONS else district_id("islamabad", groups["islamabad"][0])
        data["documents"].append({
            "id": source_id + "-reference", "territory_id": territory,
            "category": "reference", "kind": "legal_framework_location",
            "title": title, "url": url, "source_id": source_id,
            "period": "cited law version; current amendments pending review",
            "availability": "link_verified", "official_status": "unverified",
            "note": note + " No area-specific approved plan or budget body acquired.",
        })
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "pbs-2023-table1-four-provinces-ict-selected-counts"]))
    data["collection"]["notes"] = [
        "PBS 2023 Table 1 direct population counts integrated for a separate four-province-plus-ICT scope, four provinces and 136 districts; source anomalies and uncoded geography remain open.",
        *[n for n in data["collection"].get("notes", []) if not n.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "pending",
         "detail": "Six PBS 2023 Table 1 XLSX supply named 2023 provinces and 136 districts, but no official codes in their rows. The 2019 provider ADM1 polygons, 2023 PBS GIS layers, AJK/GB and current local councils are not joined.",
         "next_action": "Acquire the official dated PBS district code and polygon ledger; distinguish Census District codes from administrative districts and current local bodies before joining."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Six Table 1 XLSX and all 19,899 numeric cells inventoried. Six 2023 direct-count combinations adopted for Table 1 scope, four provinces and 136 districts. KP Topi Tehsil rural population C474 contradicts its sex sum and its total/rural/urban triplet; tehsil rows unadopted. The other 32 numbered catalogue entries and derived fields remain unassessed; Table 4 onwards have a different detailed base per Table 1 note.",
         "next_action": "Review Table 4 and priority education, water, housing and locality originals separately, including denominator, coverage, lower-unit anomalies and publication terms."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Official provincial and ICT law locations and federal PSDP location checked. Current law amendments, exact competent local bodies, local plans, budgets, expenditure and evaluation bodies have not been acquired or mapped to census districts.",
         "next_action": "Acquire applicable consolidated law versions and a representative council plan/budget/expenditure per province/ICT; record actual approval and scope separately from source location."},
    ])
    data["generated_at"] = now
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipts = []
    for name in HASHES:
        file = raw / name
        receipts.append({
            "source_url": inventory["CATALOGUE_URL"] if name.endswith("catalog.html") else
                          SOURCE_NAMES[next(k for k, v in FILES.items() if v == name)],
            "raw_path": f"raw/{name}", "sha256": HASHES[name], "bytes": file.stat().st_size,
            "saved_at_utc": datetime.fromtimestamp(file.stat().st_mtime, timezone.utc).isoformat(),
            "transfer_status": "saved_catalogue_html" if name.endswith("catalog.html")
                               else "downloaded_with_curl_fail_on_http_error",
            "note": "Local file timestamp only; server Last-Modified/ETag not captured.",
        })
    (evidence / "SOURCE_RECEIPTS.json").write_text(
        json.dumps({"recorded_at_utc": now, "receipts": receipts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    result = {"catalogue_sha256": HASHES["pbs2023-result-excel-catalog.html"],
              "sources": {key: HASHES[file] for key, file in FILES.items()},
              "territories": len(data["territories"]), "census_scope_population": 241499431,
              "domestic_indicators": len(ADOPTION), "domestic_observations": 141 * len(ADOPTION),
              "comparison_sets": len(comparisons), "source_exceptions": audit["exceptions"],
              "current_compatible_polygons": 0, "local_plan_bodies_acquired": 0,
              "independent_acceptance": False,
              "dataset_sha256": hashlib.sha256(data_file.read_bytes()).hexdigest()}
    (evidence / "PAK_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

"""Import only verified direct 2019 NIS rows with explicit population scopes."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "khm-nis-final-census2019-report"
CODE_SOURCE_ID = "khm-ncdd-gazetteer-district-0314"
CODE_SYSTEM = "NIS General Population Census 2019 geographic code, zero-padded 2/4/6 digits"
BOUNDARY = "NIS 2019 census reporting geography; compatible official polygons not verified"
NORMAL_METHOD = "NIS 2019 census final report provincial P tables: normal or regular households only"
ALL_METHOD = "NIS 2019 census final results Table 2.1.1: all enumerated persons, excluding migrants working abroad"
BAD_ALL_FIELDS = {"0302", "0801"}
BAD_POP_FIELDS = {"2202"}
P_FIELDS = {
    "normal_household_population": ("KHM_NIS2019_REGULAR_POP", "Normal household population", "people", 0),
    "male": ("KHM_NIS2019_REGULAR_MALE", "Male normal household population", "people", 0),
    "female": ("KHM_NIS2019_REGULAR_FEMALE", "Female normal household population", "people", 0),
    "households": ("KHM_NIS2019_REGULAR_HOUSEHOLDS", "Normal or regular households", "households", 0),
    "sex_ratio": ("KHM_NIS2019_REGULAR_SEX_RATIO", "Normal household sex ratio", "males per 100 females", 1),
    "household_size": ("KHM_NIS2019_REGULAR_HOUSEHOLD_SIZE", "Average normal household size", "people per household", 1),
}
ALL_FIELDS = {
    "all_person_population": ("KHM_NIS2019_ALL_PERSON_POP", "2019 census population, all persons"),
    "male": ("KHM_NIS2019_ALL_PERSON_MALE", "2019 census male population, all persons"),
    "female": ("KHM_NIS2019_ALL_PERSON_FEMALE", "2019 census female population, all persons"),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(project):
    audit = json.loads((project / "evidence/KHM_CENSUS2019_AUDIT.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "config/cambodia-census2019-source-manifest.json").read_text(
        encoding="utf-8"))["sources"]
    for source in sources:
        raw = project / source["raw_path"]
        require(raw.stat().st_size == source["bytes"] and digest(raw) == source["sha256"],
                "Pinned original mismatch: " + source["id"])
    require(audit["source_sha256"] == sources[0]["sha256"] and
            audit["p_table_level_counts"] == {"district": 202, "commune": 1646} and
            audit["p_table_normal_household_country_population"] == 15184511 and
            audit["final_all_person_rows"][0]["all_person_final"] == 15552211 and
            not audit["unparsed_numeric_rows"], "2019 census audit incomplete")
    mismatch_parents = {x["parent_code"] for x in audit["parent_child_mismatches"]}
    require(mismatch_parents == {"03", "0302", "08", "0801", "14", "17", "22", "2202"},
            "Census exception set changed; reassess before import")
    require({x["code"] for x in audit["sex_field_mismatches"]} == {"0302"},
            "Sex-field discrepancy set changed")
    require(len(audit["printed_code_exceptions"]) == 1 and
            audit["printed_code_exceptions"][0]["inferred_code"] == "0314" and
            audit["printed_code_exceptions"][0]["confirmation_source_id"] == CODE_SOURCE_ID,
            "Srei Santhor code crosswalk changed")

    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "KHM", "Expected Cambodia project")
    data["territories"] = [x for x in data["territories"] if x["id"] == "KHM"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["country"]["geography_note"] = (
        "The 2019 NIS report prints province, district/municipality/khan and commune/sangkat "
        "reporting codes. Province P tables count normal or regular household residents only "
        "(15,184,511 nationally); final all-person Table 2.1.1 counts 15,552,211. These "
        "different population scopes are separate indicators. The P tables have 202 district "
        "rows versus 204 districts/cities/khans in the overview, plus eight parent-child "
        "mismatch locations. The 2017 geoBoundaries reference is not joined to 2019 codes.")
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith("KHM_NIS2019_")]
    data["observations"] = [x for x in data["observations"]
                            if not x["indicator_id"].startswith("KHM_NIS2019_")]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("khm-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("khm-")]
    for field, (indicator_id, label, unit, decimals) in P_FIELDS.items():
        data["indicators"].append({"id": indicator_id, "name": label, "theme": "Population",
            "unit": unit, "definition": "Direct 2019 NIS provincial P table value for normal/regular households only. "
                "Institutional, homeless, boat households and transient population are outside this "
                "series. Printed source errors are withheld; province-child mismatches are not "
                "silently reconciled. Sex ratio and household size are source-reported rounded values.",
            "population": "Persons or households in normal/regular households in the NIS 2019 census geography",
            "source_id": SOURCE_ID, "aggregation": "none", "display_decimals": decimals,
            "measurement_method": NORMAL_METHOD})
    for field, (indicator_id, label) in ALL_FIELDS.items():
        data["indicators"].append({"id": indicator_id, "name": label, "theme": "Population",
            "unit": "people", "definition": "Direct all-person count from 2019 NIS final results Table 2.1.1. "
                "Includes household types excluded from the regular-household P tables; "
                "excludes migrants working abroad as the report footnote states. Available only "
                "for the country and 25 provinces.",
            "population": "All persons enumerated in the 2019 final census for the stated area",
            "source_id": SOURCE_ID, "aggregation": "none", "display_decimals": 0,
            "measurement_method": ALL_METHOD})

    def tid(code):
        return "KHM:NIS2019:" + code

    heads = audit["p_table_province_heads"]
    all_rows = audit["table_2_1_1_all_person_rows"]
    accepted_name_aliases = {"Siemreap": "Siem Reap", "Tboung Khmum": "Tbong Khmum"}
    for index, head in enumerate(heads):
        all_row = all_rows[index + 1]
        require(accepted_name_aliases.get(head["name"], head["name"]) == all_row["name"],
                f"Province P/2.1.1 names do not align at code {head['code']}")
    totals_by_province = {x["province_code"]: x for x in audit["p_table_province_subtotals"]
                          if x["label"] == "Total"}
    p_rows = audit["p_table_rows"]
    districts = [x for x in p_rows if x["level"] == "district"]
    communes = [x for x in p_rows if x["level"] == "commune"]

    for index, head in enumerate(heads):
        code = head["code"]
        data["territories"].append({"id": tid(code), "name": all_rows[index + 1]["name"],
            "level": "census_province_2019", "type": "2019 NIS census province/capital reporting unit",
            "parent_id": "KHM", "official_code": code, "code_system": CODE_SYSTEM,
            "boundary_version": BOUNDARY, "source_id": SOURCE_ID,
            "reconciliation_status": "2019 NIS code and report row; official compatible polygon unverified"})
    for row in [*districts, *communes]:
        code = row["code"]
        parent_code = code[:2] if row["level"] == "district" else code[:4]
        reconciliation = ("NIS P-03 printed district code 211, resolved to 0314 by child "
                          "prefix and NCDD gazetteer; boundary edition unverified") if code == "0314" else (
                          "2019 NIS report code and row; compatible polygon and current legal subtype unverified")
        data["territories"].append({"id": tid(code), "name": row["name"],
            "level": "census_district_2019" if row["level"] == "district" else "census_commune_2019",
            "type": "2019 census district/municipality/khan reporting unit; legal subtype unclassified"
                if row["level"] == "district" else
                "2019 census commune/sangkat reporting unit; legal subtype unclassified",
            "parent_id": tid(parent_code), "official_code": code, "code_system": CODE_SYSTEM,
            "boundary_version": BOUNDARY, "source_id": SOURCE_ID,
            "reconciliation_status": reconciliation})
    require(len(data["territories"]) == 1874, "Expected country, 25 province, 202 district and 1646 commune areas")

    def observation(territory_id, indicator_id, value, locator, method, scope):
        data["observations"].append({"territory_id": territory_id,
            "indicator_id": indicator_id, "period": "2019", "value": value,
            "status": "observed", "source_id": SOURCE_ID,
            "measurement_method": method, "population_scope": scope,
            "provenance": "source_reported", "boundary_version": BOUNDARY,
            "source_locator": locator})

    for row in all_rows:
        code = None if row["name"] == "Cambodia" else heads[all_rows.index(row) - 1]["code"]
        for field, (indicator_id, _) in ALL_FIELDS.items():
            observation("KHM" if code is None else tid(code), indicator_id, row[field],
                f"Table 2.1.1, PDF p.43 / printed p.15, row {row['name']}, {field}",
                ALL_METHOD, "All persons enumerated; migrants working abroad excluded")
    observation("KHM", P_FIELDS["normal_household_population"][0],
        audit["p_table_normal_household_country_population"],
        "Appendix Table PT 01, PDF p.237 / printed p.205, Total/Normal or Regular Household",
        NORMAL_METHOD, "Normal or regular household residents only")
    observation("KHM", P_FIELDS["households"][0], audit["p_table_country_normal_households"],
        "Table 10.2.1, PDF p.138, Total/2019 number of normal households",
        NORMAL_METHOD, "Normal or regular households only")

    for head in heads:
        total = totals_by_province[head["code"]]
        for field, (indicator_id, _, _, _) in P_FIELDS.items():
            observation(tid(head["code"]), indicator_id, total[field],
                f"Province {total['table_id']} Total, PDF p.{total['pdf_page']} / printed p.{total['printed_page']}, {field}",
                NORMAL_METHOD, "Normal or regular households only")
    for row in [*districts, *communes]:
        code = row["code"]
        for field, (indicator_id, _, _, _) in P_FIELDS.items():
            if code in BAD_ALL_FIELDS or (code in BAD_POP_FIELDS and field != "households"):
                continue
            locator = (f"Province {row['table_id']}, PDF p.{row['pdf_page']} / printed "
                       f"p.{row['printed_page']}, code {code}, {field}")
            if code == "0314":
                locator += "; printed as 211, code 0314 confirmed by NCDD gazetteer"
            observation(tid(code), indicator_id, row[field], locator,
                        NORMAL_METHOD, "Normal or regular households only")

    now = datetime.now(timezone.utc).isoformat()
    for source in sources:
        data["sources"].append({"id": source["id"],
            "name": "NIS General Population Census 2019 Final Results" if source["id"] == SOURCE_ID
                    else "NCDD Gazetteer, Srei Santhor district 0314",
            "url": source["url"], "publisher": "National Institute of Statistics" if source["id"] == SOURCE_ID
                         else "National Committee for Sub-National Democratic Development",
            "reference_period": "2019 census" if source["id"] == SOURCE_ID else "current page; 2019 applicability not generalized",
            "geographic_level": "country to commune" if source["id"] == SOURCE_ID else "Srei Santhor district and communes",
            "status": "partial", "raw_path": source["raw_path"], "sha256": source["sha256"],
            "retrieved_at": source["retrieved_at"],
            "license": "Official public source; redistribution/reuse terms require review",
            "note": source["scope"]})
    reference_sources = [
        ("khm-nis-census-catalogue", "NIS General Population Census catalogue",
         "https://nis.gov.kh/en/general-population-census-of-cambodia/", "National Institute of Statistics",
         "2019 final report and earlier editions listed; catalogue checked, not exhaustive acquisition"),
        ("khm-ncdd-gazetteer-index", "NCDD Gazetteer index",
         "https://db.ncdd.gov.kh/gazetteer/view/index.castle", "NCDD",
         "Current administrative code directory; date and 2019 boundary crosswalk require separate review"),
        ("khm-ncdd-cdb-online", "NCDD Commune/Village Databook",
         "https://db.ncdd.gov.kh/cdbonline/home/index.castle", "NCDD / Ministry of Planning",
         "Year, province, district, commune and sector selector; availability and original values not yet acquired"),
        ("khm-ncdd-subnational-law-2008", "2008 subnational administration law catalogue",
         "https://library.ncdd.gov.kh/detail/3004?lang=en", "Royal Government of Cambodia / NCDD Library",
         "Catalogue located; PDF request returned 403 in this run; current amendments unassessed"),
        ("khm-ncdd-capital-province-guide", "Capital/Provincial five-year development plan guide",
         "https://library.ncdd.gov.kh/detail/14761", "NCDD Library",
         "2013 catalogue and download URL located; PDF request returned 403; current effect unassessed"),
        ("khm-ncdd-commune-guide", "Commune/Sangkat development plan and investment guide",
         "https://library.ncdd.gov.kh/detail/530?lang=en", "NCDD Library",
         "2007 guide catalogue located; later revisions and applicability unassessed"),
    ]
    for source_id, title, url, publisher, note in reference_sources:
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": publisher, "reference_period": "catalogue checked 2026-09-27",
            "geographic_level": "national or subnational reference", "status": "partial",
            "retrieved_at": now, "license": "Official public page; reuse terms unverified",
            "note": note})
    for source_id, title, url, kind, period, note in [
        ("khm-ncdd-subnational-law-2008", "Subnational administration law catalogue",
         "https://library.ncdd.gov.kh/detail/3004?lang=en", "planning_law", "2008", "Law catalogue located; law body and current amendments unassessed."),
        ("khm-ncdd-capital-province-guide", "Capital/Provincial plan guideline catalogue",
         "https://library.ncdd.gov.kh/detail/14761", "planning_guide", "2013", "Guide location verified; PDF fetch 403, body and current effect unassessed."),
        ("khm-ncdd-commune-guide", "Commune/Sangkat planning guideline catalogue",
         "https://library.ncdd.gov.kh/detail/530?lang=en", "planning_guide", "2007", "Guide location verified; later revisions and present effect unassessed."),
    ]:
        data["documents"].append({"id": source_id, "territory_id": "KHM",
            "category": "reference", "kind": kind, "title": title, "url": url,
            "source_id": source_id, "period": period, "availability": "link_verified",
            "official_status": "unverified", "note": note})
    data["planning"] = {"title": "Subnational development plans and supporting evidence",
        "purpose": "Use 2019 census reporting areas to inspect local conditions; identify the competent current council, its development plan, investment programme, budget, implementation and evaluation for the selected legal jurisdiction.",
        "system": {"label": "Cambodia subnational planning references (current effect under review)",
            "scope": "Capital/province, municipality/district/khan, and commune/sangkat planning references have been located; the census hierarchy alone does not establish current legal jurisdiction or plan adoption.",
            "cycle": "Historical guidance names five-year plans and rolling investment programmes; current rules and each plan's actual period require confirmation.",
            "source_ids": ["khm-ncdd-subnational-law-2008", "khm-ncdd-capital-province-guide",
                           "khm-ncdd-commune-guide"]},
        "sections": [{"id": key, "label": label} for key, label in (
            ("plan", "Local development plans"),
            ("budget", "Investment programmes and budgets"),
            ("implementation", "Implementation and actual expenditure"),
            ("evaluation", "Official evaluation"),
            ("reference", "Census, law and planning references"))]}
    by_parent = defaultdict(list)
    for territory in data["territories"]:
        if territory["parent_id"]:
            by_parent[territory["parent_id"]].append(territory["id"])
    data["analysis"]["comparisons"] = []
    for parent_id, children in by_parent.items():
        code = parent_id.removeprefix("KHM:NIS2019:")
        note = ("Complete code-prefix reporting roster. Direct P-table values are shown, but "
                "the published child sum conflicts with the parent for at least one field; "
                "affected printed district values are withheld and no parent value is calculated "
                "from children. See KHM_CENSUS2019_AUDIT.json.") if code in mismatch_parents else (
                "Complete code-prefix P-table reporting roster; adopted direct normal-household "
                "count fields reconcile to this parent. All-person population is available only "
                "at country/province level and is never inherited by district or commune.")
        data["analysis"]["comparisons"].append({"parent_id": parent_id,
            "member_ids": children, "label": "2019 NIS direct reporting children",
            "membership_note": note,
            "source_ids": [SOURCE_ID]})
    data["analysis"]["terminal_territory_ids"] = [tid(x["code"]) for x in communes]
    data["analysis"]["default_indicator_id"] = P_FIELDS["normal_household_population"][0]
    data["analysis"]["latest_values_only"] = True
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "nis-2019-final-report-selected-direct-tables"]))
    data["collection"]["notes"] = [
        "2019 NIS final all-person Table 2.1.1: country and 25 provinces, three direct population/sex fields. This population scope differs from normal/regular-household P tables.",
        "Province P tables: 25 province, 202 district and 1,646 commune rows, six numeric fields inventoried. District 0302/0801 printed errors and 2202 population/sex conflict are withheld from affected indicators; eight parent-child mismatch locations are not used for complete comparisons.",
        "The report overview lists 204 cities/districts/khans, two more than the P tables parsed; the reason and current official code/boundary edition remain unresolved.",
        "NCDD Gazetteer independently confirms Srei Santhor 0314 where the NIS P-03 row prints 211. Other current code/boundary correspondence is not asserted.",
        "No local plan, budget execution or official local evaluation acquired. NCDD law/guide catalogue links are discovery only; attempted PDF downloads returned 403.",
        "Initial 2017 geoBoundaries shapes removed because compatible 2019 official polygons were not verified.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "2019 NIS table codes identify reporting rows; only the 0314 printing exception is independently checked against NCDD. No compatible official 2019 polygons, full legal subtype or 2025 crosswalk is adopted.",
         "next_action": "Acquire dated official code/gazetteer and polygon originals, reconcile all 2019 levels and identify the two overview district rows absent from P tables."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Only direct Table 2.1.1 all-person counts and provincial P-table regular-household fields are adopted. Eight parent-child mismatch locations, three district rows with withheld fields and the other report tables require semantic review.",
         "next_action": "Resolve P-table printed errors using another NIS publication or correction, inspect remaining census tables and CDB source availability by theme/year/geography."},
        {"category": "planning_documents", "status": "partial",
         "detail": "NCDD law and plan-guidance catalogue pages located; PDFs returned 403 via CLI. Local plan, investment programme, budget actual and official evaluation contents were not acquired.",
         "next_action": "Acquire current law/guide and representative capital/province, district and commune plans, investment, budget, execution and evaluation bodies; inspect approval and periods."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]),
        "local_population_scope": "2019 normal or regular households only",
        "all_person_country": 15552211, "normal_household_country": 15184511,
        "source_table_numeric_fields": "P tables six fields; Table 2.1.1 three fields",
        "observations_by_indicator": dict(Counter(x["indicator_id"] for x in data["observations"]
            if x["indicator_id"].startswith("KHM_NIS2019_"))),
        "mismatch_parent_locations": len(mismatch_parents),
        "official_compatible_polygons": 0, "independent_acceptance": False,
        "dataset_sha256": digest(data_path)}
    (project / "evidence/KHM_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

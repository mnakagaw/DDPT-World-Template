"""Import one directly reported 2024 POPCEN column with June 2024 PSGC IDs."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


INDICATOR = "PHL_POPCEN2024_POPULATION"
BOUNDARY = "PSA POPCEN 2024 reporting geography / PSGC as of 30 June 2024; compatible official polygons unverified"
CODE_SYSTEM = "Philippine Standard Geographic Code, second quarter 2024 (10-digit)"
QC_ID = "PHL:PSGC:1381300000"
METHOD = "2024 Census of Population (POPCEN), direct PSA Table A/B count as of 1 July 2024"
ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tid(row):
    return "PHL:PSGC:" + row["code"] if row["code"] else "PHL:POPCEN:SGA-2024"


def evidence(source_id, locator, date):
    return {"source_id": source_id, "locator": locator, "checked_at": date,
            "authority": "Quezon City Council"}


def main(project):
    source_manifest = json.loads((project / "evidence/PHL_SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    planning_manifest = json.loads((project / "evidence/PHL_PLANNING_SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    pinned_planning = json.loads((ROOT / "config/philippines-planning-source-manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/PHL_POPCEN_AUDIT.json").read_text(encoding="utf-8"))
    require(audit["table_a_national_2024"] == 112729484 and
            audit["table_b_region_sum_2024"] == 112727776 and
            audit["non_territorial_diplomatic_persons"] == 1708 and
            len(audit["table_b_rows"]) == 1743 and
            not audit["reporting_parent_mismatches"], "POPCEN audit is incomplete")
    for item in [*source_manifest["sources"], *planning_manifest["sources"]]:
        path = project / item["raw_path"]
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"],
                "Original changed: " + item["id"])
    source_by_id = {x["id"]: x for x in source_manifest["sources"]}
    planning_by_id = {x["id"]: x for x in planning_manifest["sources"]}
    require(len(pinned_planning["sources"]) == 6, "Expected six pinned planning originals")
    for item in pinned_planning["sources"]:
        live = planning_by_id[item["id"]]
        require(all(live.get(key) == value for key, value in item.items()),
                "Acquired planning original differs from pinned metadata: " + item["id"])

    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "PHL", "Expected Philippines project")
    data["territories"] = [x for x in data["territories"] if x["id"] == "PHL"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "2024 POPCEN country count includes 1,708 people outside territorial region totals"
    data["country"]["geography_note"] = (
        "PSA 2024 POPCEN uses 18 region reporting rows, 82 province rows, 149 cities, "
        "1,493 municipalities and a separate Special Geographic Area subtotal. The census "
        "country count includes 1,708 Filipinos at diplomatic missions abroad; its region "
        "totals are lower by exactly that amount. Q2 2024 PSGC codes identify reporting rows "
        "but its historical 2020 population field has unrecast values in ten Table B locations. "
        "No compatible official 2024 polygon is joined. Statistical regions and SGA are not LGUs.")
    data["indicators"] = [x for x in data["indicators"] if x["id"] != INDICATOR]
    data["observations"] = [x for x in data["observations"] if x["indicator_id"] != INDICATOR]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("phl-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("phl-")]

    data["indicators"].append({"id": INDICATOR, "name": "2024 POPCEN population",
        "theme": "Population", "unit": "people",
        "definition": "Direct official 2024 Census of Population count as of 1 July 2024. "
            "Country total includes 1,708 Filipinos in diplomatic missions abroad; region "
            "totals cover domestic areas only. Province subtotals exclude HUCs. Distinct from "
            "World Bank midyear population estimates and Table B historical recasts.",
        "population": "Persons counted in the 2024 POPCEN for the stated PSA reporting geography",
        "source_id": "phl-popcen-table-a", "aggregation": "none",
        "display_decimals": 0, "measurement_method": METHOD})

    data["observations"].append({"territory_id": "PHL", "indicator_id": INDICATOR,
        "period": "2024", "value": audit["table_a_national_2024"], "status": "observed",
        "source_id": "phl-popcen-table-a", "measurement_method": METHOD,
        "population_scope": "Country total including 1,708 Filipinos at diplomatic missions abroad",
        "provenance": "source_reported", "boundary_version": BOUNDARY,
        "source_locator": "Table A/Table A!I7, national direct count; note B172 on 1,708 diplomatic persons"})

    by_parent = defaultdict(list)
    for row in audit["table_b_rows"]:
        id_ = tid(row)
        parent = row["parent_id"]
        level = row["level"]
        row_type = {
            "Reg": "PSA statistical region reporting row; not a local government unit",
            "Prov": "PSA province reporting subtotal excluding highly urbanized cities",
            "City": f"PSGC city ({row['city_class']}); POPCEN reporting row",
            "Mun": "PSGC municipality; POPCEN reporting row",
            "SGA": "POPCEN Special Geographic Area reporting subtotal; not a PSGC local government unit",
        }[level]
        territory = {"id": id_, "name": row["psgc_name"] or "Special Geographic Area (SGA)",
            "level": {"Reg": "census_region_2024", "Prov": "census_province_2024",
                      "City": "census_city_2024", "Mun": "census_municipality_2024",
                      "SGA": "census_special_area_2024"}[level],
            "type": row_type, "parent_id": parent, "official_code": row["code"],
            "code_system": CODE_SYSTEM if row["code"] else "PSA POPCEN Table B reporting label; no PSGC code",
            "boundary_version": BOUNDARY,
            "source_id": "phl-popcen-table-b",
            "reconciliation_status": "Q2 PSGC code and direct 2024 Table B row checked; current boundary and legal planning match unverified"
            if row["code"] else "Special subtotal; no PSGC LGU code or legal planning jurisdiction"}
        data["territories"].append(territory)
        by_parent[parent].append(id_)
        data["observations"].append({"territory_id": id_, "indicator_id": INDICATOR,
            "period": "2024", "value": row["population"]["2024"], "status": "observed",
            "source_id": "phl-popcen-table-b", "measurement_method": METHOD,
            "population_scope": "Persons in the specified PSA 2024 POPCEN reporting area; HUCs outside province subtotal",
            "provenance": "source_reported", "boundary_version": BOUNDARY,
            "source_locator": row["source_locator"] + " (column F 2024 count; " +
                (row["code"] or "SGA no PSGC code") + ")"})

    require(len(data["territories"]) == 1744 and len(by_parent["PHL"]) == 18 and
            len([x for x in data["observations"] if x["indicator_id"] == INDICATOR]) == 1744,
            "Imported POPCEN coverage differs from audit")
    qc = next(x for x in data["territories"] if x["id"] == QC_ID)
    require(qc["name"] == "Quezon City" and qc["parent_id"] == "PHL:PSGC:1300000000",
            "Quezon City official-code crosswalk changed")
    data["analysis"]["comparisons"] = []
    for parent, members in by_parent.items():
        if parent == "PHL":
            note = "All 18 domestic region totals are direct PSA rows; their sum is 1,708 below the country value because the country includes diplomatic persons abroad. Do not aggregate regions to replace the country observation."
        else:
            note = "Complete non-overlapping 2024 POPCEN direct reporting children reconcile exactly to the parent direct observation. This reporting partition does not assert legal LGU subordination or current official polygons."
        data["analysis"]["comparisons"].append({"parent_id": parent,
            "member_ids": members, "label": "2024 POPCEN reporting children",
            "membership_note": note, "source_ids": ["phl-popcen-table-b"]})
    data["analysis"]["terminal_territory_ids"] = [tid(x) for x in audit["table_b_rows"]
        if x["level"] in ("City", "Mun")]
    data["analysis"]["default_indicator_id"] = INDICATOR
    data["analysis"]["latest_values_only"] = True

    now = datetime.now(timezone.utc).isoformat()
    checked = now[:10]
    for item in source_manifest["sources"]:
        is_adopted = item["id"] in {"phl-popcen-table-a", "phl-popcen-table-b", "phl-psgc-2024q2-datafile"}
        data["sources"].append({"id": item["id"], "name": item["id"].replace("phl-", "PSA "),
            "url": item["url"], "release_page": item["release_page"],
            "publisher": "Philippine Statistics Authority", "reference_period":
                "1 July 2024 POPCEN" if item["category"] == "popcen" else
                "PSGC 30 June 2024" if item["category"] == "psgc_june" else "PSGC 31 December 2024",
            "geographic_level": "country to barangay" if "table-c" in item["id"] else "country to municipality",
            "status": "ready" if is_adopted else "partial",
            "raw_path": item["raw_path"], "sha256": item["sha256"],
            "retrieved_at": item["retrieved_at"], "license": "Public PSA release; reuse terms require review",
            "note": "2024 population direct column adopted; other years/PGR not adopted"
                if item["id"] in {"phl-popcen-table-a", "phl-popcen-table-b"} else
                "Q2 official codes used for 2024 Table B rows; PSGC 2020 population is not substituted"
                if item["id"] == "phl-psgc-2024q2-datafile" else
                "Archived and numeric columns inventoried; meaning or barangay crosswalk not yet assessed. "
                "Q4 PSGC is a later edition and is not joined to July 2024 observations."})
    for item in planning_manifest["sources"]:
        data["sources"].append({"id": item["id"], "name": item["id"].replace("phl-", ""),
            "url": item["url"], "publisher": "Department of the Interior and Local Government"
                if "dilg" in item["id"] else "Quezon City Government / City Council",
            "reference_period": "2022 guide" if "dilg" in item["id"] else
                "2026–2031" if "cdp-2026" in item["id"] else
                "2027–2029" if "ldip" in item["id"] else "2025–2026",
            "geographic_level": "national guidance" if "dilg" in item["id"] else "Quezon City",
            "status": "partial", "raw_path": item["raw_path"], "sha256": item["sha256"],
            "retrieved_at": item["retrieved_at"],
            "license": "Official public PDF; reuse terms unverified",
            "note": "Body acquired; selected pages inspected. Full substantive audit and update status remain partial."})
    catalogue = [
        ("phl-popcen-release-page", "https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president",
         "Philippine Statistics Authority", "2024 POPCEN official release page with attached Tables A/B/C"),
        ("phl-psgc-2024q2-release-page", "https://psa.gov.ph/content/second-quarter-2024-psgc-updates-creation-negros-island-region-and-correction-names-two",
         "Philippine Statistics Authority", "2024 Q2 PSGC official release and attachment catalogue"),
        ("phl-psgc-2024q4-release-page", "https://psa.gov.ph/content/fourth-quarter-2024-psgc-updates-correction-names-three-barangays",
         "Philippine Statistics Authority", "2024 Q4 PSGC later-release and attachment catalogue"),
        ("phl-local-government-code-7160", "https://officialgazette.gov.ph/1991/10/10/republic-act-no-7160/",
         "Official Gazette", "1991 Local Government Code sections 106, 109 and 114 read online; body not locally archived"),
        ("phl-qc-cdp-council-record", "https://qccouncil.quezoncity.gov.ph/resolutions/22291",
         "Quezon City Council", "SP-10311 S-2025 adoption catalogue"),
        ("phl-qc-ldip-council-record", "https://qccouncil.quezoncity.gov.ph/councilors/167",
         "Quezon City Council", "Council member legislative list names SP-10515 S-2026 approving LDIP; resolution body unacquired"),
        ("phl-qc-aip-council-record", "https://qccouncil.quezoncity.gov.ph/resolutions/22255",
         "Quezon City Council", "SP-10255 S-2025 AIP adoption catalogue"),
        ("phl-qc-budget-council-record", "https://qccouncil.quezoncity.gov.ph/ordinances/14359",
         "Quezon City Council", "SP-3465 S-2025 budget ordinance catalogue"),
    ]
    for source_id, url, publisher, note in catalogue:
        data["sources"].append({"id": source_id, "name": note, "url": url,
            "publisher": publisher, "reference_period": "2024–2026 official record",
            "geographic_level": "national" if "7160" in source_id or "psa.gov.ph" in url else "Quezon City",
            "status": "partial", "retrieved_at": now,
            "license": "Official public page; reuse terms unverified",
            "note": note + "; web location and visible text checked; not an archived source body."})

    def territory_match(territory_id, source_id, locator, method):
        territory = next(x for x in data["territories"] if x["id"] == territory_id)
        return {"territory_id": territory_id, "country_id": "PHL",
                "type": territory["type"], "official_code": territory["official_code"],
                "code_system": territory["code_system"],
                "boundary_version": territory["boundary_version"],
                "method": method, "source_id": source_id, "locator": locator,
                "checked_at": checked}

    def document(source_id, title, territory_id, category, kind, period, note,
                 availability="body_acquired", status="unverified", status_source=None,
                 status_locator=None):
        item = planning_by_id[source_id]
        doc = {"id": source_id, "territory_id": territory_id, "category": category,
            "kind": kind, "title": title, "url": item["url"], "source_id": source_id,
            "period": period, "availability": availability, "official_status": status,
            "note": note,
            "territory_match": territory_match(territory_id,
                "phl-psgc-2024q2-datafile" if territory_id == QC_ID else "phl-local-government-code-7160",
                "PSGC code 1381300000, Quezon City unique city row" if territory_id == QC_ID else "Republic Act No. 7160 national law",
                "Official Quezon City publisher and document title matched to unique Q2 PSGC city; "
                "the document does not state the PSGC code" if territory_id == QC_ID else
                "National legal/guidance reference; no local plan asserted")}
        if status_source:
            doc["official_evidence"] = evidence(status_source, status_locator, checked)
        data["documents"].append(doc)
        return doc

    data["documents"].append({"id": "phl-local-government-code-7160", "territory_id": "PHL",
        "category": "reference", "kind": "planning_law", "title": "Republic Act No. 7160, Local Government Code",
        "url": "https://officialgazette.gov.ph/1991/10/10/republic-act-no-7160/",
        "source_id": "phl-local-government-code-7160", "period": "1991 law",
        "availability": "link_verified", "official_status": "unverified",
        "note": "Sections 106, 109 and 114 identify local development councils, sanggunian approval and investment-program functions. Current amendments and all implementing rules not audited."})
    document("phl-dilg-cdp-toolkit", "DILG Comprehensive Development Plan Facilitator's Toolkit",
        "PHL", "reference", "planning_guide", "2022 edition",
        "502-page DILG Region I guide; cover and selected contents reviewed, complete forms and current amendments not assessed.")
    document("phl-qc-cdp-2026-2031", "Quezon City Comprehensive Development Plan 2026–2031",
        QC_ID, "plan", "published-plan", "2026–2031",
        "720-page city plan body acquired. Council record SP-10311 S-2025 adopts the revised plan; full plan contents and implementation unassessed.",
        status="approved", status_source="phl-qc-cdp-council-record",
        status_locator="SP-10311 S-2025 record title adopting the revised CDP 2026–2031")
    document("phl-qc-ldip-2027-2029", "Quezon City Local Development Investment Program 2027–2029",
        QC_ID, "plan", "published-plan", "2027–2029",
        "497-page LDIP body acquired. Council legislative list names SP-10515 S-2026 approving/adopting this LDIP; resolution body and full LDIP contents unassessed.",
        status="approved", status_source="phl-qc-ldip-council-record",
        status_locator="SP-10515 S-2026 in city council member legislative list")
    document("phl-qc-aip-2026", "Quezon City FY2026 Annual Investment Program adoption",
        QC_ID, "budget", "annual-plan", "FY2026",
        "SP-10255 S-2025 adopts an AIP of PHP 56,902,941,000. This is a program amount, not the enacted budget or actual expenditure.",
        status="approved", status_source="phl-qc-aip-council-record",
        status_locator="SP-10255 S-2025 record title with AIP amount PHP 56,902,941,000")
    document("phl-qc-budget-2026", "Quezon City calendar 2026 annual budget ordinance",
        QC_ID, "budget", "budget", "CY2026",
        "SP-3465 S-2025 approves the CY2026 budget of PHP 43,300,000,000. This is an appropriation, not AIP amount, cash expenditure or plan achievement.",
        status="approved", status_source="phl-qc-budget-council-record",
        status_locator="SP-3465 S-2025 official ordinance record title, PHP 43.3 billion")

    data["planning"] = {"title": "Local development plans and supporting evidence",
        "purpose": "Use the July 2024 census to diagnose selected reporting areas, then check the actual local-government plan, annual investment program, budget, implementation and evaluation for the matching jurisdiction.",
        "system": {"label": "Philippine Local Government Code, section 106 local development planning",
            "scope": "Provinces, cities, municipalities and barangays are local government units with development councils and sanggunian approval. Statistical regions and the POPCEN Special Geographic Area are not local government units; a reporting parent does not by itself establish legal planning authority.",
            "cycle": "Plan periods and annual investment/budget periods are document-specific; no single global cycle is imposed.",
            "source_ids": ["phl-local-government-code-7160", "phl-dilg-cdp-toolkit"]},
        "sections": [{"id": k, "label": label} for k, label in (
            ("plan", "Local development plans and investment programs"),
            ("budget", "Annual investment and appropriated budget"),
            ("implementation", "Implementation and actual expenditure"),
            ("evaluation", "Official evaluation"),
            ("reference", "Census, code and planning references"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
        "psa-popcen-2024-table-a-b-q2-psgc-selected-direct-counts"]))
    data["collection"]["notes"] = [
        "PSA Table A/B 2024 population direct column: national and 1,743 region/province/city/municipality/SGA rows. All 101 reporting parent-child totals reconcile; national contains 1,708 diplomatic persons outside region totals.",
        "Thirty PSA originals archived and all 26 workbook/sheet numeric columns inventoried. Table C barangay counts, older population columns, PGR, and further census themes remain priority_unassessed.",
        "Quezon City CDP, LDIP, AIP and budget originals acquired and council catalogue adoption records checked; program, appropriation, expenditure and evaluation remain distinct. No actual expenditure or official evaluation body acquired.",
        "No official 2024-compatible polygons; initial 2020 geoBoundaries reference shapes removed; no automatic 2024 legal-boundary join.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "Q2 PSGC codes and Table B 2024 reporting rows joined; ten source-code/historical-count exceptions recorded. No 2024-compatible official polygons or legal LGU boundary crosswalk acquired.",
         "next_action": "Acquire PSA/NAMRIA dated official polygons and legal-unit crosswalk; resolve NIR, SGA, Maguindanao and Makati/Taguig before any map join."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Only direct 2024 population from Table A/B adopted. Table C's barangay column and earlier-year populations/PGR were inventoried but their matching, definitions and comparability remain priority_unassessed.",
         "next_action": "Reconcile all Table C barangay rows to dated PSGC codes, then audit 2024 census household/sector tables and temporal geography before adopting further indicators."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Quezon City CDP/LDIP bodies and official adoption catalogue records acquired; FY2026 AIP and budget ordinances acquired. Other LGUs, full contents, actual expenditure and official evaluation remain unassessed or uncollected.",
         "next_action": "Audit QC plan and fiscal contents and council resolution body; acquire representative province, component city, municipality and barangay plans/budgets, implementation and evaluation sources."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]), "table_b_rows": 1743,
        "direct_census_observations": 1744, "national_population": 112729484,
        "psgc_q2_matched_rows": 1742, "special_reporting_subtotals_without_psgc_code": 1,
        "official_compatible_polygons": 0, "source_code_exceptions": 10,
        "qc_documents": 4, "independent_acceptance": False,
        "dataset_sha256": digest(data_path)}
    (project / "evidence/PHL_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

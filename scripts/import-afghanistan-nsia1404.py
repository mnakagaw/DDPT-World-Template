"""Build a bounded Afghanistan candidate from NSIA's 1404 population PDF.

Only Table 4 direct 2025-26 population/sex counts are adopted. The country row
includes nomadic population; the 34 province rows cover settled population.
No inferred provincial nomadic allocation, official codes, current polygons,
plans or budgets are attached.
"""

import argparse
import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path


inventory = runpy.run_path(str(Path(__file__).with_name(
    "inventory-afghanistan-nsia1404.py")))
SHA256 = inventory["SHA256"]
SOURCE_URL = inventory["URL"]
require = inventory["require"]
SCOPE = "AFG:NSIA1404:SETTLED_PROVINCES"
SOURCE = "afg-nsia-population-1404"
PREFIX = "AFG_NSIA1404_"
PERIOD = "2025-26"
METHOD = "NSIA population estimate based on 2002-05 household listing and 2004 base"
BOUNDARY = "NSIA 1404 named province reporting geography; official compatible polygon unacquired"
FIELDS = (
    ("POP_EST", "both sexes", "Estimated resident population, NSIA 1404"),
    ("FEMALE_EST", "female", "Estimated female resident population, NSIA 1404"),
    ("MALE_EST", "male", "Estimated male resident population, NSIA 1404"),
)
REFERENCES = (
    ("afg-km-urban-laws-index", "Kabul Municipality urban laws index",
     "https://km.gov.af/19134/urban-laws-and-regulations", "Kabul Municipality",
     "Lists old Official Gazette municipal, master-plan and urban-development laws. Current force, amendments and jurisdiction beyond Kabul city are unverified."),
    ("afg-km-annual-development-plans", "Kabul Municipality annual development plans catalogue",
     "https://km.gov.af/19100/annual-development-plans", "Kabul Municipality",
     "Lists financial years 1395-1400, not a verified current plan or a plan for all Kabul Province. Linked plan bodies not acquired."),
    ("afg-km-city-plans", "Kabul city plans interactive catalogue",
     "https://kmplan.km.gov.af/", "Kabul Municipality",
     "City planning map catalogue; plan selection and exact current version/body unassessed. Not a Kabul Province plan."),
    ("afg-mudh-herat-city-masterplan-announcement",
     "MUDH announcement of Herat city master-plan handover, 1405/5/20",
     "https://www.mudh.gov.af/dr/%D9%85%D8%A7%D8%B3%D8%AA%D8%B1%D9%BE%D9%84%D8%A7%D9%86-%D9%88%D9%84%D8%A7%DB%8C%D8%AA-%D9%87%D8%B1%D8%A7%D8%AA-%D8%AC%D9%87%D8%AA-%D8%AA%D8%B7%D8%A8%DB%8C%D9%82-%D8%B1%D8%B3%D9%85%D8%A7-%D8%A8%D9%87-%D9%88%D8%A7%D9%84%DB%8C-%D9%87%D8%B1%D8%A7%D8%AA-%D8%AA%D8%B3%D9%84%DB%8C%D9%85-%D8%AF%D8%A7%D8%AF%D9%87-%D8%B4%D8%AF",
     "Ministry of Urban Development and Housing",
     "Official news says a Herat city urban master plan was handed to the provincial governor for implementation. The plan body, legal effect, exact city boundary and budget are not acquired; do not attach it as a province-wide plan."),
    ("afg-mof-budget-document-catalogue", "Ministry of Finance budget-document catalogue",
     "https://www.mof.gov.af/en/budget-document", "Ministry of Finance",
     "National budget-document index; visible older years are not province-specific current budget or expenditure evidence."),
)


def province_id(serial):
    return f"AFG:NSIA1404:PROVINCE:{serial:02d}"


def main(project):
    audit_file = project / "evidence/AFG_NSIA1404_AUDIT.json"
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    require(audit["sha256"] == SHA256 and audit["numbered_tables"] == 76 and
            len(audit["province_rows"]) == 34 and
            audit["table_76_population_checks"] == 34,
            "Run pinned complete table inventory and province cross-check first")
    scope = audit["table_4_scopes"]
    require(scope["Total Population"]["2025-26 both sexes"] == 36435197 and
            scope["Total"]["2025-26 both sexes"] == 34935197 and
            scope["Nomadic"]["2025-26 both sexes"] == 1500000,
            "NSIA scope totals changed")
    require(audit["table_76_household_note"]["province_rows_minus_settled"] == 302048,
            "Household non-reconciliation changed; re-audit source before adoption")
    file = project / "data/dashboard.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "AFG", "Expected Afghanistan project")
    data["territories"] = [x for x in data["territories"] if x["id"] == "AFG"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("afg-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("afg-")]
    now = datetime.now(timezone.utc).isoformat()
    data["country"]["geography_note"] = (
        "NSIA 1404 (2025-26) estimated 36,435,197 people nationally, including a fixed "
        "1,500,000 nomadic estimate. Its 34 named provinces total 34,935,197 settled people. "
        "These are not a new census and differ in method from WDI midyear economy estimates. "
        "The generator's 2007 geoBoundaries ADM1 shapes were not joined to NSIA 1404 "
        "province rows. No official province code, 1404 polygon, municipal boundary or "
        "legal planning-unit match is claimed.")
    data["territories"].append({
        "id": SCOPE, "name": "Settled population of 34 provinces (NSIA 1404)",
        "level": "population_coverage", "type": "statistical_coverage_area",
        "parent_id": "AFG", "official_code": None,
        "code_system": "NSIA Table 4 settled-province subtotal; no separate official area code",
        "boundary_version": BOUNDARY, "source_id": SOURCE,
        "reconciliation_status": "All 34 Table 4 province rows sum to this settled subtotal; nomadic population remains outside province allocation.",
    })
    for row in audit["province_rows"]:
        data["territories"].append({
            "id": province_id(row["source_serial"]),
            "name": f"{row['name']} (NSIA 1404)", "level": "province_1404",
            "type": "statistical_province", "parent_id": SCOPE,
            "official_code": None,
            "code_system": "NSIA Table 4 row serial is only an internal locator, not an official code",
            "source_row": row["source_serial"], "boundary_version": BOUNDARY,
            "source_id": SOURCE,
            "reconciliation_status": "Direct named NSIA Table 4 province estimate; code, current municipal jurisdiction and matching official polygon unverified.",
        })
    require(len(data["territories"]) == 36, "Expected root, settled scope and 34 provinces")
    data["sources"].append({
        "id": SOURCE, "name": "NSIA Estimated Population of Afghanistan 2025-26, Tables 4 and 76",
        "url": SOURCE_URL, "publisher": "National Statistics and Information Authority",
        "reference_period": "Solar Hijri 1404 / 2025-26 population estimate",
        "geographic_level": "national, settled 34 provinces; other tables include administrative units",
        "status": "partial", "raw_path": "raw/nsia-population-1404.pdf",
        "sha256": SHA256, "retrieved_at": now,
        "license": "Official public PDF; redistribution terms unverified",
        "note": "168-page PDF downloaded from NSIA :8443 after TLS certificate-name mismatch; server authentication was not verified by TLS. EUAA independently links this URL. All 76 numbered tables and their numeric-column groups inventoried. Only 1404 Table 4 direct counts adopted; Table 76 corroborates province population but household totals conflict.",
    })
    for source_id, title, url, publisher, note in REFERENCES:
        data["sources"].append({
            "id": source_id, "name": title, "url": url, "publisher": publisher,
            "reference_period": "official location checked 2026-09-27",
            "geographic_level": "national reference or named city as described in note",
            "status": "not_collected", "retrieved_at": now,
            "license": "Official page location only; document body and reuse terms unverified",
            "note": note,
        })
    for suffix, sex, label in FIELDS:
        key = f"2025-26 {sex}"
        full_id, settled_id = PREFIX + "FULL_" + suffix, PREFIX + "SETTLED_" + suffix
        data["indicators"].extend([
            {"id": full_id, "name": label + " (full country)",
             "theme": "Population", "unit": "people",
             "definition": "NSIA 1404 direct national estimate including 1.5 million nomadic people. National scope only; not a new census or WDI midyear series.",
             "population": "all estimated residents of Afghanistan including nomadic people",
             "source_id": SOURCE, "aggregation": "none", "measurement_method": METHOD,
             "display_decimals": 0},
            {"id": settled_id, "name": label + " (settled provinces)",
             "theme": "Population", "unit": "people",
             "definition": "NSIA 1404 direct estimate of settled people in the 34 named provinces. Nomadic population is excluded and not allocated to provinces. Not a new census or WDI midyear series.",
             "population": "settled residents of the 34 NSIA 1404 named provinces, excluding nomadic people",
             "source_id": SOURCE, "aggregation": "none", "measurement_method": METHOD,
             "display_decimals": 0},
        ])
        data["observations"].append({
            "territory_id": "AFG", "indicator_id": full_id,
            "period": PERIOD, "value": scope["Total Population"][key],
            "status": "observed", "source_id": SOURCE,
            "measurement_method": METHOD, "provenance": "source_reported",
            "source_locator": f"PDF p31 Table 4 Total Population, 1404/{key}",
            "population_scope": "full_national_including_nomadic",
            "boundary_version": None,
        })
        data["observations"].append({
            "territory_id": SCOPE, "indicator_id": settled_id,
            "period": PERIOD, "value": scope["Total"][key],
            "status": "observed", "source_id": SOURCE,
            "measurement_method": METHOD, "provenance": "source_reported",
            "source_locator": f"PDF p31 Table 4 Total (settled provinces), 1404/{key}",
            "population_scope": "settled_provinces_excluding_nomadic",
            "boundary_version": BOUNDARY,
        })
        for row in audit["province_rows"]:
            data["observations"].append({
                "territory_id": province_id(row["source_serial"]),
                "indicator_id": settled_id, "period": PERIOD,
                "value": row["values"][key], "status": "observed",
                "source_id": SOURCE, "measurement_method": METHOD,
                "provenance": "source_reported", "source_locator":
                f"PDF p{row['pdf_page']} Table 4 serial {row['source_serial']} "
                f"{row['name']}, 1404/{key}; population cross-check PDF p167 Table 76",
                "population_scope": "settled_province_excluding_nomadic",
                "boundary_version": BOUNDARY,
            })
    data["analysis"]["comparisons"] = [{
        "parent_id": "AFG", "member_ids": [SCOPE],
        "label": "Settled-only coverage; nomadic population is unallocated",
        "membership_note": "This single statistical coverage area contains the 34 named province rows, not the whole national population. The separately reported 1.5 million nomadic people are not assigned to provinces. Do not sum this child as a complete country estimate or compare its settled-only series with the full-national series.",
        "source_ids": [SOURCE],
    }, {
        "parent_id": SCOPE,
        "member_ids": [province_id(row["source_serial"]) for row in audit["province_rows"]],
        "label": "NSIA 1404 settled population in 34 provinces",
        "membership_note": "The complete 34 named Table 4 province rows equal the separately reported settled-province subtotal for female, male and both sexes. Nomadic people are included only in the full national row and are not assigned to provinces.",
        "source_ids": [SOURCE],
    }]
    data["analysis"]["terminal_territory_ids"] = [
        province_id(row["source_serial"]) for row in audit["province_rows"]]
    data["analysis"]["default_indicator_id"] = "SP.POP.TOTL"
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {
        "title": "Urban planning source locations and province population evidence",
        "purpose": "Diagnose the selected NSIA statistical province, then identify the responsible current planning body and obtain its actual plan, budget, implementation and evaluation for the correct city or province scope.",
        "system": {
            "label": "City, municipality and province planning authority must be resolved for each location",
            "scope": "Kabul municipal pages and Herat city master-plan announcement are city references, not adopted plans for whole NSIA provinces.",
            "cycle": "Current local plan cycles, legal effect, budgets and implementation unverified",
            "source_ids": [x[0] for x in REFERENCES],
        },
        "sections": [
            {"id": "plan", "label": "Area-specific adopted plan"},
            {"id": "budget", "label": "Budget and allocations"},
            {"id": "implementation", "label": "Expenditure and implementation"},
            {"id": "evaluation", "label": "Official evaluation"},
            {"id": "reference", "label": "Population and planning-source locations"},
        ],
    }
    data["documents"].append({
        "id": "afg-nsia-population-source-reference", "territory_id": SCOPE,
        "category": "reference", "kind": "official_population_estimate_source",
        "title": "NSIA 1404 estimated population, Table 4",
        "url": SOURCE_URL, "source_id": SOURCE, "period": PERIOD,
        "availability": "body_acquired", "official_status": "official_statistical_release",
        "territory_match": {"territory_id": SCOPE, "country_id": "AFG",
            "type": "statistical_coverage_area",
            "code_system": "NSIA Table 4 settled-province subtotal; no separate official area code",
            "official_code": None, "boundary_version": BOUNDARY,
            "method": "Table 4 settled subtotal equals all 34 named province rows in female, male and both-sex 1404 columns; nomadic people are outside the scope",
            "source_id": SOURCE, "locator": "PDF p31 Table 4 Total row and pp31-32 province rows",
            "checked_at": now},
        "official_evidence": {"source_id": SOURCE,
            "locator": "PDF cover p1 and preface p5; Table 4 pp31-32 direct 1404 counts",
            "checked_at": now},
        "note": "Source PDF and 76-table inventory retained locally. This is a population estimate, not a census or an adopted area plan. NSIA TLS certificate name did not verify during acquisition.",
    })
    for source_id, title, url, _, note in REFERENCES:
        data["documents"].append({
            "id": source_id + "-reference", "territory_id": "AFG",
            "category": "reference", "kind": "planning_source_location",
            "title": title, "url": url, "source_id": source_id,
            "period": "location checked 2026-09-27", "availability": "link_verified",
            "official_status": "unverified", "note": note,
        })
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []),
        "nsia-1404-table4-selected-official-estimates"]))
    data["collection"]["notes"] = [
        "NSIA 1404 Table 4 direct 2025-26 estimated population/sex counts connected for national full scope, settled subtotal and 34 settled provinces; not a new census. Other 75 tables remain semantically unassessed.",
        *[note for note in data["collection"].get("notes", [])
          if not note.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [gap for gap in data["gaps"] if gap["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "pending",
         "detail": "NSIA Table 4 lists 34 named provinces but no official area codes. The generated 2007 provider ADM1 reference shapes do not establish a 1404 official province match and were removed from the adopted candidate.",
         "next_action": "Acquire a dated official administrative-code and polygon register; reconcile province and district names/versions before map joins."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "The 168-page NSIA 1404 estimate has 76 numbered tables. Table 4 latest-year female, male and both-sex direct counts are adopted for 34 provinces and two explicit national scopes. Table 76 matches all province population totals but its household totals conflict; other tables/fields and district units remain unassessed. WDI and NSIA definitions differ.",
         "next_action": "Audit remaining tables, especially age/sex, rural/urban, district administrative units and 2023-25 trends; resolve household discrepancies and source terms before adopting."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Kabul city law/annual-plan/catalogue locations and an official Herat city master-plan handover statement were identified. Their actual current plan bodies, exact city boundaries, province planning authority, legal force, budgets, expenditure and evaluations have not been acquired or matched.",
         "next_action": "Obtain applicable current legal and plan bodies for representative city and provincial scopes, then verify approval, period, boundary, financial and implementation evidence separately."},
    ])
    data["generated_at"] = now
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "source_url": SOURCE_URL, "raw_path": "raw/nsia-population-1404.pdf",
        "sha256": SHA256, "bytes": (project / "raw/nsia-population-1404.pdf").stat().st_size,
        "saved_at_utc": datetime.fromtimestamp(
            (project / "raw/nsia-population-1404.pdf").stat().st_mtime,
            timezone.utc).isoformat(),
        "transfer": "curl --insecure, HTTP 200, application/pdf; prior certificate-validating curl failed SEC_E_WRONG_PRINCIPAL",
        "limitation": "TLS peer identity not verified; external EUAA primary EU publication linked exact NSIA URL and the PDF's own cover/metadata were inspected. Reacquire with valid TLS or an authenticated official mirror before independent acceptance.",
    }
    (project / "evidence/AFG_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "source_sha256": SHA256, "source_tables": 76,
        "territories": len(data["territories"]), "official_compatible_polygons": 0,
        "domestic_indicators": len(FIELDS) * 2,
        "domestic_observations": len(FIELDS) * 36,
        "national_full_population": 36435197,
        "settled_scope_population": 34935197,
        "nomadic_unallocated_population": 1500000,
        "comparison_sets": 2, "area_plan_bodies_acquired": 0,
        "independent_acceptance": False,
        "dataset_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
    }
    (project / "evidence/AFG_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

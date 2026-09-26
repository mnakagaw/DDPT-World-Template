"""Adopt checked Kuwait census Table 1 counts, without assigning Not Stated or Table 51 areas."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "kwt-csb-registration-census-2021-table1"
AREA_SOURCE_ID = "kwt-csb-registration-census-2021-table51"
RAW_DIR = "raw/kuwait-csb-2021/"
FIELDS = (
    ("ALL_TOTAL", "all_total", "Population, all nationalities and sexes"),
    ("ALL_FEMALE", "all_female", "Female population, all nationalities"),
    ("ALL_MALE", "all_male", "Male population, all nationalities"),
    ("KUWAITI_TOTAL", "kuwaiti_total", "Kuwaiti population, both sexes"),
    ("KUWAITI_FEMALE", "kuwaiti_female", "Kuwaiti female population"),
    ("KUWAITI_MALE", "kuwaiti_male", "Kuwaiti male population"),
    ("NONKUWAITI_TOTAL", "nonkuwaiti_total", "Non-Kuwaiti population, both sexes"),
    ("NONKUWAITI_FEMALE", "nonkuwaiti_female", "Non-Kuwaiti female population"),
    ("NONKUWAITI_MALE", "nonkuwaiti_male", "Non-Kuwaiti male population"),
)
LEADS = (
    ("kwt-csb-census-governorate-web", "2021 registration census governorate table and exclusion note",
     "https://census.csb.gov.kw/Census_Gov_EN", "Central Statistical Bureau / PACI",
     "2021 registration census", "national and six governorates",
     "The webpage repeats the Table 1 counts and notes three excluded non-Kuwaiti categories. Webpage checked, no separate body pinned."),
    ("kwt-csb-census-methodology", "2021 registration census methods and purpose",
     "https://census.csb.gov.kw/CensusInfo_EN", "Central Statistical Bureau",
     "2021 registration census", "national methodology",
     "Official explanation identifies an administrative-register census rather than traditional field enumeration."),
    ("kwt-csb-census-catalogue", "2021 census population, building and establishment tables",
     "https://census.csb.gov.kw/CensusData_EN?CatID=1", "Central Statistical Bureau",
     "2021 registration census", "national, governorate and area tables",
     "Table 1 and Table 51 were acquired; other population/building/establishment tables remain unassessed."),
    ("kwt-csb-population-publications", "Population estimates and final census bulletin catalogue",
     "https://csb.gov.kw/Pages/Statistics_en?ID=67&ParentCatID=+1", "Central Statistical Bureau",
     "2022 census bulletin and 2023-2025 estimates listed", "national; local scope to inspect",
     "Catalogue lists the final census by gender/nationality for 1 January 2022 and later population estimates. These are separate publications and have not been equated to the Table 1 register extraction date or adopted."),
    ("kwt-municipality-law-33-2016", "Kuwait Municipality Law 33/2016 official PDF",
     "https://www.baladia.gov.kw/sites/ar/municipalityLaws/Documents/%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%A7%D9%84%D8%A8%D9%84%D8%AF%D9%8A%D8%A9%20%D8%B1%D9%82%D9%85%2033%20%D9%84%D8%B3%D9%86%D8%A9%202016.pdf",
     "Kuwait Municipality", "2016 law; current amendments to verify", "national urban-planning law",
     "Official PDF location identified via search, but direct download connection reset. Full current law and governorate planning duties have not been audited."),
    ("kwt-scpd-annual-plan-2021-22", "Kuwait annual development plan 2021/2022",
     "https://scpd.gov.kw/archive/plan%2021-2022.pdf",
     "General Secretariat of the Supreme Council for Planning and Development",
     "2021/2022 historical national annual plan", "national development planning",
     "Official PDF location identified, but direct acquisition timed out. It is historical and cannot be treated as an approved current governorate plan or current budget."),
    ("kwt-mpw-third-master-plan", "Third Kuwait national structural plan archive",
     "https://www.mpw.gov.kw/sites/ar/Pages/InfoPages/ImprovingHeirachyPlan.aspx",
     "Ministry of Public Works", "historical third master-plan archive", "national spatial planning",
     "Official page lists planning workbooks and PDFs; direct acquisition timed out. It does not establish the current fourth plan or six local plans."),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "KWT" or any(source["id"] == SOURCE_ID for source in dataset["sources"]):
        raise ValueError("Expected unmodified Kuwait bootstrap candidate")
    structure = json.loads((project / "evidence/KWT_CSB_2021_STRUCTURE.json").read_text(encoding="utf-8"))
    if structure["table1_excel_pdf_rows_checked"] != 8 or structure["table1_numeric_columns_checked"] != 9 or \
            structure["table51_named_area_rows"] != 157:
        raise ValueError("Run full two-table inspector first")
    for name, digest in structure["raw_sha256"].items():
        original = project / RAW_DIR / name
        receipt = json.loads((project / RAW_DIR / (name + ".receipt.json")).read_text(encoding="utf-8"))
        if sha(original) != digest or receipt["sha256"] != digest or receipt["status"] != "acquired":
            raise ValueError(f"Kuwait census original/receipt changed: {name}")
    with (project / "evidence/KWT_CSB_2021_TABLE1_ROWS.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 8 or [r["source_name_en"] for r in rows][-2:] != ["Not Stated", "Total"]:
        raise ValueError("Table 1 reporting rows changed")
    for row in rows:
        for _, field, _ in FIELDS:
            row[field] = int(row[field])
    for _, field, _ in FIELDS:
        if sum(row[field] for row in rows[:7]) != rows[7][field]:
            raise ValueError(f"Governorates plus unassigned do not match national {field}")
    if rows[7]["all_total"] != 4385717 or rows[6]["all_total"] != 4578:
        raise ValueError("Pinned national and unassigned values changed")

    country = next(item for item in dataset["territories"] if item["id"] == "KWT")
    country.update(source_id=SOURCE_ID, type="country", reporting_role="2021 register-census national total",
                   code_system="ISO3 KWT dataset key; CSB Table 1 source label", boundary_version=None)
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    ids = ["KWT"]
    for row in rows[:6]:
        label = row["source_name_en"].removesuffix(" Governorate")
        slug = re.sub(r"[^A-Z0-9]+", "-", label.upper()).strip("-")
        territory_id = "KWT:CSB2021:GOV:" + slug
        ids.append(territory_id)
        dataset["territories"].append({
            "id": territory_id, "name": label, "level": "adm1", "type": "2021 census governorate",
            "parent_id": "KWT", "official_code": None,
            "code_system": "CSB/PACI registration census 2021 Table 1 name; official code not printed",
            "provider_code": None, "source_id": SOURCE_ID, "boundary_version": None,
            "reconciliation_status": "source_label_only; current_official_code_and_polygon_not_verified",
        })
    xlsx = json.loads((project / RAW_DIR / "table1-governorate-nationality-gender.xlsx.receipt.json").read_text(encoding="utf-8"))
    area = json.loads((project / RAW_DIR / "table51-usual-residence.xlsx.receipt.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    dataset["sources"].append({
        "id": SOURCE_ID, "name": "Kuwait 2021 registration census, Table 1: governorate, nationality and gender",
        "url": xlsx["source_url"], "publisher": "Central Statistical Bureau / Public Authority for Civil Information",
        "reference_period": "2021 registration census; precise register-extraction date not verified from Table 1",
        "geographic_level": "national, six governorates and nonterritorial Not Stated row",
        "status": "ready", "retrieved_at": xlsx["retrieved_at"], "raw_path": xlsx["raw_path"],
        "sha256": xlsx["sha256"], "license": "official_publication_redistribution_terms_review_required",
        "note": "Nine direct count columns are adopted for national and six governorate rows; the 4,578-person Not Stated row remains in the audit and is not assigned to a governorate. The companion PDF independently matches all 72 source cells. The official governorate webpage notes excluded non-Kuwaiti categories. This is a historical register census, not the WDI annual population series. The homepage displays a different headline count; Table 1 is the pinned final tabulation. No official codes or legal polygons are certified here.",
    })
    dataset["sources"].append({
        "id": AREA_SOURCE_ID, "name": "Kuwait 2021 registration census, Table 51: habitual-residence area population",
        "url": area["source_url"], "publisher": "Central Statistical Bureau / Public Authority for Civil Information",
        "reference_period": "2021 registration census", "geographic_level": "157 source area labels, Not Stated and national total",
        "status": "partial", "retrieved_at": area["retrieved_at"], "raw_path": area["raw_path"],
        "sha256": area["sha256"], "license": "official_publication_redistribution_terms_review_required",
        "note": "All 159 Excel rows match the companion PDF; 157 named area values are withheld from the dataset pending official area codes, explicit parent-governorate keys and dated boundaries. Contiguous arithmetic row-block matches do not by themselves certify an official crosswalk.",
    })
    for source_id, name, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": name, "url": url,
                                   "publisher": publisher, "reference_period": period,
                                   "geographic_level": geography, "status": "not_collected",
                                   "retrieved_at": now, "license": "terms_review_required", "note": note})
    for suffix, field, label in FIELDS:
        qualifier = "non-Kuwaiti residents within the PACI registration-census tabulation" if field.startswith("nonkuwaiti") \
            else "Kuwaiti residents within the PACI registration-census tabulation" if field.startswith("kuwaiti") \
            else "people within the PACI registration-census tabulation"
        dataset["indicators"].append({
            "id": "KWT_CSB_2021_" + suffix, "name": label + " (2021 registration census)",
            "theme": "Population", "unit": "people", "source_id": SOURCE_ID,
            "definition": "Direct printed count in CSB/PACI 2021 registration census Table 1, Excel Sheet1 and matching PDF page 1. Non-Kuwaiti exclusions are stated on the official governorate webpage. The nonterritorial Not Stated row is not assigned to one of the six governorates; country and governorate counts are independently reported. Not WDI annual estimates.",
            "population": qualifier, "aggregation": "none",
            "measurement_method": "paci_administrative_register_census_2021_table1",
            "series_family": "census", "display_role": "primary",
            "period_policy": "latest_available_per_indicator", "display_decimals": 0,
        })
    for row, territory_id in zip(rows[:6] + [rows[7]], ids[1:] + ["KWT"]):
        for suffix, field, _ in FIELDS:
            dataset["observations"].append({
                "territory_id": territory_id, "indicator_id": "KWT_CSB_2021_" + suffix,
                "period": "2021", "value": row[field], "status": "observed", "source_id": SOURCE_ID,
                "measurement_method": "paci_administrative_register_census_2021_table1",
                "source_locator": f"Table 1, Excel Sheet1 row {row['source_excel_row']}, {field}; PDF page 1",
            })
    adopted = [item for item in dataset["observations"] if item["indicator_id"].startswith("KWT_CSB_2021_")]
    if len(dataset["territories"]) != 7 or len(adopted) != 63:
        raise ValueError("Expected national plus six governorates and 63 adopted cells")
    dataset["country"]["geography_note"] = (
        "The CSB/PACI 2021 registration census reports a national total of 4,385,717, six governorates totalling 4,381,139 and a separate nonterritorial Not Stated row of 4,578. Nine count fields are direct Table 1 values, not aggregates from six governorates and not current estimates. The official webpage notes excluded non-Kuwaiti categories. No official governorate codes, dated legal polygons or Table 51 area parent keys have been matched. Six bootstrap 2017 provider shapes are withheld. WDI national annual series remains separate.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="Six 2021 census governorate source labels identified. Official area/governorate codes and 2021 legal boundaries are not verified; six 2017 provider reference shapes are withheld.",
                       next_action="Acquire PACI/CSB official 2021 governorate and area-code directory and dated polygons; test one-to-one names and legal status before any map join.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="Nine direct Table 1 fields for national and six governorate rows were adopted (63 cells). A separate Not Stated row of 4,578 people prevents a six-governorate complete-total assertion. Table 51 has 157 area counts but remains unadopted pending code and parent keys. Other census tables and later estimates remain unassessed.",
                       next_action="Inventory remaining official census tables and 2022/2025 population bulletins; obtain coded Table 51 crosswalk and compare definitions/periods before adoption.")
        elif gap["category"] == "planning_documents":
            gap.update(status="not_collected", detail="Kuwait Municipality Law 33/2016, the historical national 2021/22 annual plan and third master-plan archive were located, but their bodies could not be acquired directly in this pass. No current governorate plan, adoption, budget, expenditure or evaluation is verified.",
                       next_action="Acquire current law/amendments, fourth master plan and plan/budget originals; identify actual statutory planning authority and local planning unit.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["kuwait-csb-2021-table1-partial"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tuples = sorted((item["territory_id"], item["indicator_id"], item["value"]) for item in adopted)
    audit = {"status": "partial_candidate_not_accepted", "checked_at": now,
             "table1_xlsx_sha256": xlsx["sha256"], "table1_pdf_sha256": structure["raw_sha256"]["table1-governorate-nationality-gender.pdf"],
             "table51_xlsx_sha256": area["sha256"], "source_national_total": 4385717,
             "source_six_governorates_total": 4381139, "nonterritorial_not_stated": 4578,
             "table1_direct_columns": 9, "domestic_observations_added": 63,
             "adopted_tuple_sha256": hashlib.sha256(json.dumps(tuples, ensure_ascii=False).encode("utf-8")).hexdigest(),
             "withheld_provider_shapes": 6, "table51_unadopted_named_area_rows": 157,
             "planning_documents_adopted": 0,
             "unresolved": ["Official codes and dated polygons", "Precise source register reference date", "All other census tables and later estimates", "Current local planning authority, documents and budgets", "42 scenarios and independent acceptance"]}
    (project / "evidence/KWT_CSB_2021_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_2021_census_table1_partially_adopted", "checked_at": now,
        "census": "Table 1 PDF/XLSX all nine count columns and eight rows checked; 63 national/governorate cells adopted; Not Stated is nonterritorial.",
        "area_statistics": "Table 51 PDF/XLSX 157 named area rows acquired and checked, not adopted without codes/parent keys.",
        "geography": "Six 2021 governorate labels only; no official code or dated legal polygon; six 2017 provider shapes withheld.",
        "planning": "Law 33/2016, historical national plan and third master-plan archive located only; current local plans, budgets, actual expenditure and evaluation not verified.",
        "cross_country_candidates": "Original common-source discovery list is not an availability or adoption result.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = md_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_2021_census_table1_partially_adopted** (2026-09-26).\n\n"
           "CSB/PACI 2021 registration census Table 1 PDF/XLSX was acquired and all nine count columns and eight source rows crosschecked. National and six governorate rows supply 63 direct observations; the 4,578-person Not Stated row remains nonterritorial. Table 51 has 157 named area rows, all acquired and crosschecked but none adopted without official codes and parent keys. 2017 provider polygons are withheld. Official law/national-plan/master-plan locations were identified but not acquired; no current governorate plans, budgets, expenditure or evaluations are verified. The other common-source availability items remain open. See KWT_CSB_2021_STRUCTURE.json and KWT_CSB_2021_IMPORT_AUDIT.json.")
    if old not in markdown:
        raise ValueError("Unexpected Kuwait source preflight Markdown")
    md_path.write_text(markdown.replace(old, new), encoding="utf-8")
    print(json.dumps({"territories": 7, "governorates": 6, "domestic_indicators": 9,
                      "observations_added": 63, "national": 4385717, "not_stated": 4578,
                      "area_rows_unadopted": 157, "official_sources_added": len(LEADS) + 2}))


if __name__ == "__main__":
    main()

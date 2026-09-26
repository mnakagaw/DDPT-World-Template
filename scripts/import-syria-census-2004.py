"""Import source-reported counts from archived Syrian CBS 2004 census PDFs.

The OCHA-mirrored XLS supplies row-order English names and P-codes only. Its
values differ from the official PDFs in 70 district/subdistrict rows, so the
PDF numbers control every adopted observation. P-codes are provider IDs, not
verified Syrian legal codes. The 2017 geoBoundaries polygons are display-only.
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RAW_HASHES = {
    "syr_pop_2004_sycensus_0.xls": "3ef15cc2cd20f4a37f07016a4e9485319caf4f4eeed7a4cd9ecadbdbd4af3d61",
    "cbs2004-pop-moh.pdf": "296374d5d2f306e803a4cf7631000e93576e08e57a3d527eb57e922e518ab628",
    "cbs2004-pop-man.pdf": "21c02896cc6d4b19561f17c2a55a0109e8d7dd2e1c6de9558485e44edcf5cfa7",
}
PDF_GOV_URL = "https://web.archive.org/web/20140124131814id_/http://cbssyr.sy/General%20census/census%202004/pop-moh.pdf"
PDF_DIST_URL = "https://web.archive.org/web/20130310211017/http://www.cbssyr.org/General%20census/census%202004/pop-man.pdf"
XLS_URL = "https://web.archive.org/web/20160307093758/https://www.humanitarianresponse.info/files/syr_pop_2004_sycensus_0.xls"
SOURCE_GOV = "syr-cbs2004-population-governorates-archived"
SOURCE_DIST = "syr-cbs2004-population-districts-archived"
SOURCE_XLS = "syr-ocha-mirror-2004-census-workbook"
SOURCE_PLANNING_LEAD = "syr-sana-local-planning-methodology-2025"
SOURCE_BUDGET_LEAD = "syr-mof-citizen-budget-2026"
PREFIX = "SYR_CBS_CENSUS_2004_"
NAME_CROSSWALK = {"Lattakia": "Lattakia", "Idleb": "Idleb", "Daraa": "Dar'a"}
FIELDS = (
    ("POP", "Population, 2004 census", "people", "Persons in the CBS 2004 population and housing census"),
    ("MALE", "Male population, 2004 census", "people", "Male persons in the CBS 2004 census"),
    ("FEMALE", "Female population, 2004 census", "people", "Female persons in the CBS 2004 census"),
    ("HOUSEHOLDS", "Households, 2004 census", "households", "Households in the CBS 2004 census"),
    ("OCCUPIED_HOUSING", "Occupied dwellings, 2004 census", "dwellings", "Occupied housing units in the CBS 2004 census"),
    ("VACANT_HOUSING", "Vacant dwellings, 2004 census", "dwellings", "Vacant housing units in the CBS 2004 census"),
)


def add_observation(items, territory_id, suffix, value, source_id, locator):
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid 2004 CBS count at {locator}: {value!r}")
    items.append({"territory_id": territory_id, "indicator_id": PREFIX + suffix,
                  "period": "2004", "value": value, "status": "observed",
                  "measurement_method": "source_reported", "source_id": source_id,
                  "source_locator": locator})


def main(project):
    raw = project / "raw" / "official"
    for filename, expected in RAW_HASHES.items():
        digest = hashlib.sha256((raw / filename).read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError(f"Pinned source changed: {filename}: {digest}")
    evidence = project / "evidence"
    normalized = json.loads((evidence / "SYR_CBS2004_NORMALIZED.json").read_text(encoding="utf-8"))
    audit = json.loads((evidence / "SYR_CBS2004_AUDIT.json").read_text(encoding="utf-8"))
    if (len(normalized["governorates"]), len(normalized["districts"]), len(normalized["subdistricts"])) != (14, 61, 270):
        raise ValueError("CBS source territory roster changed")
    if audit["pdf_xls_differences"] != 213:
        raise ValueError("Expected PDF/XLS discrepancies require re-audit")
    dataset_path = project / "data" / "dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "SYR":
        raise ValueError("Expected Syrian Arab Republic country project")
    dataset["territories"] = [area for area in dataset["territories"] if not area["id"].startswith("SYR:OCHA2004:")]
    dataset["indicators"] = [item for item in dataset["indicators"] if not item["id"].startswith(PREFIX)]
    dataset["observations"] = [item for item in dataset["observations"] if not item["indicator_id"].startswith(PREFIX)]
    dataset["sources"] = [item for item in dataset["sources"] if item["id"] not in {SOURCE_GOV, SOURCE_DIST, SOURCE_XLS, SOURCE_PLANNING_LEAD, SOURCE_BUDGET_LEAD}]
    reference = {area["name"]: area for area in dataset["territories"] if area["parent_id"] == "SYR"}
    if len(reference) != 14 or len(dataset["boundaries"]["features"]) != 14:
        raise ValueError("Reference governorate geometry changed")
    observations = []
    gov_ids = {}
    for row in normalized["governorates"]:
        name = NAME_CROSSWALK.get(row["name_en"], row["name_en"])
        if name not in reference:
            raise ValueError(f"Unmatched 2004 governorate source name: {row['name_en']}")
        area = reference[name]
        code = row["code"]
        gov_ids[code] = area["id"]
        area["source_name_ar"] = row["name_ar"]
        area["census_source_pcode"] = code
        area["census_reconciliation"] = "2004 CBS census name to 2017 geoBoundaries polygon; geometry is display reference only"
        for suffix, field in (("POP", "population"), ("MALE", "male"), ("FEMALE", "female"),
                              ("HOUSEHOLDS", "households"), ("OCCUPIED_HOUSING", "occupied_housing"),
                              ("VACANT_HOUSING", "vacant_housing")):
            add_observation(observations, area["id"], suffix, row[field], SOURCE_GOV,
                            f"CBS 2004 governorate PDF p.1 row {row['source_row']} ({code}), {field}")
    if set(gov_ids) != {f"SY{i:02d}" for i in range(1, 15)}:
        raise ValueError("Governorate P-code roster changed")
    new_areas = []
    district_ids = {}
    for row in normalized["districts"]:
        code = row["code"]
        parent_id = gov_ids[row["governorate_code"]]
        territory_id = f"SYR:OCHA2004:ADM2:{code}"
        district_ids[code] = territory_id
        new_areas.append({"id": territory_id, "country_id": "SYR", "parent_id": parent_id,
            "level": "adm2", "type": "District", "name": row["name_en"],
            "source_name_ar": row["name_ar"], "source_pcode": code,
            "source_id": SOURCE_DIST, "official_code": None, "boundary_version": None,
            "reconciliation_status": "2004 CBS PDF page order to OCHA-mirrored P-code; official code/boundary unverified"})
        for suffix, field in (("POP", "population"), ("MALE", "male"), ("FEMALE", "female")):
            add_observation(observations, territory_id, suffix, row[field], SOURCE_DIST,
                            f"CBS 2004 district PDF p.{row['pdf_page']} total row ({code}), {field}")
    for row in normalized["subdistricts"]:
        code = row["code"]
        parent_id = district_ids[row["district_code"]]
        territory_id = f"SYR:OCHA2004:ADM3:{code}"
        new_areas.append({"id": territory_id, "country_id": "SYR", "parent_id": parent_id,
            "level": "adm3", "type": "Sub-District", "name": row["name_en"],
            "source_name_ar": row["name_ar"], "source_pcode": code,
            "source_id": SOURCE_DIST, "official_code": None, "boundary_version": None,
            "reconciliation_status": "2004 CBS PDF row order to OCHA-mirrored P-code; official code/boundary unverified"})
        for suffix, field in (("POP", "population"), ("MALE", "male"), ("FEMALE", "female")):
            add_observation(observations, territory_id, suffix, row[field], SOURCE_DIST,
                            f"CBS 2004 district PDF p.{row['pdf_page']} row {row['pdf_row_in_page']} ({code}), {field}")
    if len(new_areas) != 331 or len({area["id"] for area in new_areas}) != 331:
        raise ValueError("2004 census lower-area roster or IDs invalid")
    national = normalized["national"]
    for suffix, field in (("POP", "population"), ("MALE", "male"), ("FEMALE", "female"),
                          ("HOUSEHOLDS", "households"), ("OCCUPIED_HOUSING", "occupied_housing"),
                          ("VACANT_HOUSING", "vacant_housing")):
        add_observation(observations, "SYR", suffix, national[field], SOURCE_GOV,
                        f"CBS 2004 governorate PDF p.1 national total, {field}")
    if len(observations) != 15 * 6 + 331 * 3:
        raise ValueError("2004 census observation count differs")
    dataset["territories"] += new_areas
    for suffix, name, unit, definition in FIELDS:
        local = suffix in {"POP", "MALE", "FEMALE"}
        dataset["indicators"].append({"id": PREFIX + suffix, "name": name,
            "theme": "CBS 2004 census, historical", "unit": unit,
            "definition": definition + ". Source-reported 2004 historical value; not a current population or housing estimate."
                          + (" District and sub-district PDF counts are authoritative where the OCHA-mirrored workbook differs." if local else " Housing counts are shown only for the country and governorates because lower PDF rows have unresolved discrepancies."),
            "population": "Persons enumerated in the 2004 Syrian CBS census" if unit == "people" else
                          "Households or dwellings recorded in the 2004 Syrian CBS census",
            "source_id": SOURCE_DIST if local else SOURCE_GOV,
            "aggregation": "sum", "measurement_method": "source_reported",
            "period_policy": "latest_available_per_indicator", "display_decimals": 0})
    dataset["observations"] += observations
    stamp = datetime.now(timezone.utc).isoformat()
    retrieved = lambda filename: datetime.fromtimestamp((raw / filename).stat().st_mtime, timezone.utc).isoformat()
    dataset["generated_at"] = stamp
    dataset["sources"] += [
        {"id": SOURCE_GOV, "name": "CBS 2004 census population and housing by governorate (archived original)",
         "url": PDF_GOV_URL, "publisher": "Syrian Central Bureau of Statistics",
         "reference_period": "2004 census", "geographic_level": "country, governorate",
         "status": "ready", "retrieved_at": retrieved("cbs2004-pop-moh.pdf"), "sha256": RAW_HASHES["cbs2004-pop-moh.pdf"],
         "raw_path": "raw/official/cbs2004-pop-moh.pdf", "license": "terms_review_required",
         "note": "Original CBS website PDF preserved by the Internet Archive. Seven numeric columns, 14 governorates and national total. Official site currently returns 403; current reuse terms unresolved."},
        {"id": SOURCE_DIST, "name": "CBS 2004 census population and housing by district/sub-district (archived original)",
         "url": PDF_DIST_URL, "publisher": "Syrian Central Bureau of Statistics",
         "reference_period": "2004 census", "geographic_level": "district, sub-district",
         "status": "ready", "retrieved_at": retrieved("cbs2004-pop-man.pdf"), "sha256": RAW_HASHES["cbs2004-pop-man.pdf"],
         "raw_path": "raw/official/cbs2004-pop-man.pdf", "license": "terms_review_required",
         "note": "Original CBS website 61-page PDF preserved by the Internet Archive. Population and sex counts adopted; housing/household columns withheld below governorate because source rows contain unresolved anomalies."},
        {"id": SOURCE_XLS, "name": "OCHA-hosted mirror of Syrian 2004 census workbook (archived)",
         "url": XLS_URL, "publisher": "UN OCHA mirror of Syrian CBS census material",
         "reference_period": "2004 census with separate 2009 and 2010 sheets", "geographic_level": "governorate to city/locality",
         "status": "partial", "retrieved_at": retrieved("syr_pop_2004_sycensus_0.xls"), "sha256": RAW_HASHES["syr_pop_2004_sycensus_0.xls"],
         "raw_path": "raw/official/syr_pop_2004_sycensus_0.xls", "license": "terms_review_required",
         "note": "Six sheets and every numeric field inventoried. English labels and P-codes used for source-scoped identity; 213 field-level differences from CBS PDFs retained in private audit. XLS numbers are not substituted for adopted PDF observations."},
        {"id": SOURCE_PLANNING_LEAD, "name": "SANA report on proposed local development planning method, 23 October 2025",
         "url": "https://sana.sy/locals/2313737/", "publisher": "Syrian Arab News Agency",
         "reference_period": "2025", "geographic_level": "governorates; exact legal planning unit unverified",
         "status": "not_collected", "retrieved_at": stamp, "license": "terms_review_required",
         "note": "Official news reports discussion of a proposed governorate local-development planning methodology. It is a source-location lead, not an enacted guide, local plan, approved budget or proof of a current legal obligation. Obtain the methodology and governing law before adoption."},
        {"id": SOURCE_BUDGET_LEAD, "name": "Ministry of Finance citizen budget 2026, national document lead",
         "url": "https://docs.mof.gov.sy/citizen_budget_2026.pdf", "publisher": "Syrian Ministry of Finance",
         "reference_period": "2026", "geographic_level": "national; subnational detail not audited",
         "status": "not_collected", "retrieved_at": stamp, "license": "terms_review_required",
         "note": "Official national citizen-budget PDF location identified. Its table fields and possible geographic breakdown are unassessed. It is not evidence of a chosen governorate's approved plan, budget execution or official evaluation."},
    ]
    dataset["country"]["geography_note"] = (
        "CBS 2004 census records 14 governorates, 61 districts and 270 sub-districts. English names and P-codes come from an OCHA-mirrored workbook; these are provider identifiers, not verified Syrian legal codes. The 2017 geoBoundaries governorate polygons are name-matched navigation references, not certified 2004 or current boundaries. No district/sub-district geometry is joined. This historical census cannot describe post-2011 displacement or current residents.")
    dataset["gaps"] = [item for item in dataset["gaps"] if item["category"] not in {"subnational_statistics", "planning_documents"}]
    dataset["gaps"].append({"category": "subnational_statistics", "status": "partial",
        "detail": "Archived official CBS 2004 PDFs supply historical population and sex counts for 14 governorates, 61 districts and 270 sub-districts; household/occupied/vacant dwelling counts are adopted only at country/governorate. The OCHA mirror differs in 213 field-level values, so its values are not silently used. City/locality data and other numeric rates are inventoried but not adopted. Current subnational census/administrative population remains unavailable in this candidate.",
        "next_action": "Find current statistical authority releases, verify legal territorial codes and boundary editions, resolve PDF/XLS differences and review all remaining census and recent sector tables."})
    dataset["gaps"].append({"category": "planning_documents", "status": "not_collected",
        "detail": "The 2025-2026 reorganization of Syria's Planning and Statistics Authority and local-development planning are under research. No selected governorate or municipal plan, budget execution, implementation report or official evaluation has been content-verified.",
        "next_action": "Verify current law and planning responsibilities, then obtain actual local plans, budgets and official evaluations with period and approval evidence."})
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["syria-cbs-2004-census-archived-pdf"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["analysis"]["default_indicator_id"] = PREFIX + "POP"
    dataset["analysis"]["population_context"] = {
        "primary_indicator_id": PREFIX + "POP", "reference_indicator_id": "SP.POP.TOTL",
        "reference_period": "2025",
        "note": "The 2004 Syrian census and World Bank's 2025 national population estimate differ in period and method; do not treat their gap as a simple change rate."
    }
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": dict(Counter(area["level"] for area in new_areas)),
                      "domestic_indicators": len(FIELDS), "domestic_observations": len(observations),
                      "national_census_population": national["population"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

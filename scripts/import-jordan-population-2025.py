"""Import Jordan DoS 2025 estimated population from pinned official workbooks.

The 2025 figures are annual estimates based on the 2015 census, not 2025
census counts. District and sub-district IDs are provisional source-scoped IDs;
only the DoS table hierarchy is asserted. geoBoundaries 2006 governorate shapes
remain navigation references and do not certify the 2025 boundary.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl


ESTIMATES = ("PopulationEstimates.xlsx", "0917681306aa728e501464a8a42c0ec31ed81e66cf16245862ede53f007f7002")
LOCALITY = ("PopulationEstimatesbyLocality.xlsx", "ebf49f985570c25de141a26c75fc70790a0f7225fb351b3ecd04b68402bd0ef8")
MUNICIPALITIES = ("Municipalities.xlsx", "3f880201fd685830e5c77f6505797a2bc91086412f72a758399dd4f92dda4b97")
PLANNING_GUIDE = ("GovernoratePlanningGuide.pdf", "ebb981db5b5afd468e3662461a0f84445732ab916b512d57f65ddd526efab85a")
LOCAL_LAW = ("LocalAdministrationLaw2021.pdf", "715f73dc331e62764ee2ec7433ba06e402953ec706ac683df8f4e1f46d8569ac")
URL_BASE = "https://dosweb.dos.gov.jo/databank/Population/Population_Estimares/"
SOURCE_EST = "jor-dos-2025-population-estimates"
SOURCE_LOC = "jor-dos-2025-population-by-locality"
SOURCE_MUN = "jor-dos-2025-municipalities"
SOURCE_CENSUS = "jor-dos-2015-census-table-catalogue"
SOURCE_GUIDE = "jor-moi-governorate-planning-guide-2018"
SOURCE_LAW = "jor-mola-local-administration-law-2021"
GUIDE_URL = "https://www.mola.gov.jo/ebv4.0/root_storage/ar/eb_list_page/guide_for_the_preparation_of_governorate_strategic_development_and_implementation_plans.pdf"
LAW_URL = "https://mola.gov.jo/EBV4.0/Root_Storage/AR/EB_Info_Page/%D9%82%D8%A7%D9%86%D9%88%D9%86_%D8%A7%D9%84%D8%A7%D8%AF%D8%A7%D8%B1%D8%A9_%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%D8%A92021.pdf"
PREFIX = "JOR_DOS_EST_2025_"
GOV_NAME = {
    "Amman": "Amman", "Balqa": "Balqa", "Zarqa": "Zarqa",
    "Madaba": "Madaba", "Irbid": "Irbid", "Mafraq": "Mafraq",
    "Jarash": "Jerash", "Ajlun": "Ajloun", "Ajloun": "Ajloun", "Karak": "Karak",
    "Tafiela": "Tafilah", "Ma'an": "Ma'an", "Aqaba": "Aqaba",
}
ESTIMATE_GOV_ORDER = ("Amman", "Balqa", "Zarqa", "Madaba", "Irbid", "Mafraq",
                      "Jarash", "Ajlun", "Karak", "Tafiela", "Ma'an", "Aqaba")
FIELDS_LOCAL = (
    ("POP", "Population estimate, end 2025", "people", "Source-reported total in DoS column D; columns B and C reconcile to D"),
    ("MALE", "Male population estimate, end 2025", "people", "Male residents in DoS source row"),
    ("FEMALE", "Female population estimate, end 2025", "people", "Female residents in DoS source row"),
    ("HOUSEHOLDS", "Household estimate, end 2025", "households", "Households in DoS source row"),
)
FIELDS_GOV = (
    ("URBAN", "Urban locality population estimate, end 2025", "people", "DoS 2025 Table 2.3; urban is locality of 5,000 or more under the 2015 census definition"),
    ("RURAL", "Rural locality population estimate, end 2025", "people", "DoS 2025 Table 2.3 rural category"),
    ("AREA_KM2", "Governorate area in 2025 DoS table", "km²", "DoS 2025 Table 2.6 reported area; not calculated from geoBoundaries"),
    ("DENSITY", "Population density in 2025 DoS table", "people/km²", "DoS 2025 Table 2.6 reported population divided by reported area"),
)


def check_hash(path, expected):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f"Source hash mismatch: {path}: {digest}")
    return path.stat().st_size


def integer(value, locator):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected nonnegative integer at {locator}: {value!r}")
    return value


def english(value):
    return " ".join(str(value or "").replace("*", "").replace("(1)", "").split())


def add_observation(items, territory_id, suffix, value, source_id, locator):
    items.append({"territory_id": territory_id, "indicator_id": PREFIX + suffix,
                  "period": "2025", "value": value, "status": "observed",
                  "measurement_method": "source_reported", "source_id": source_id,
                  "source_locator": locator})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    project = Path(args.project)
    raw = project / "raw" / "official-jordan"
    size_est = check_hash(raw / ESTIMATES[0], ESTIMATES[1])
    size_loc = check_hash(raw / LOCALITY[0], LOCALITY[1])
    size_mun = check_hash(raw / MUNICIPALITIES[0], MUNICIPALITIES[1])
    size_guide = check_hash(raw / PLANNING_GUIDE[0], PLANNING_GUIDE[1])
    size_law = check_hash(raw / LOCAL_LAW[0], LOCAL_LAW[1])
    estimates = openpyxl.load_workbook(raw / ESTIMATES[0], read_only=True, data_only=True)
    locality = openpyxl.load_workbook(raw / LOCALITY[0], read_only=True, data_only=True)
    source_rows = list(locality["الملخص "].values)
    sex_rows = list(estimates["2.3"].values)
    area_rows = list(estimates["2.7"].values)
    if "2025" not in str(source_rows[1][0]) or "2025" not in str(sex_rows[2][0]):
        raise ValueError("DoS 2025 source title changed")
    if "2025" not in str(area_rows[23][0]):
        raise ValueError("DoS 2025 area table title changed")
    if [english(value) for value in sex_rows[3][:6]] != ["المحافظة", "ذكور", "اناث", "المجموع", "Total", "Governorate"]:
        raise ValueError("Table 2.2 source fields changed")
    if [english(value) for value in source_rows[3][:5]] != ["", "ذكور Male", "إناث Female", "المجموع Total", "الأسر HouseHolds"]:
        raise ValueError("Locality summary source fields changed")
    national = source_rows[121]
    if english(national[5]) != "Total" or tuple(national[1:5]) != (6319900, 5617100, 11937000, 2475767):
        raise ValueError("DoS 2025 national source totals changed")
    dataset_path = project / "data" / "dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "JOR":
        raise ValueError("Expected Jordan country project")
    dataset["territories"] = [area for area in dataset["territories"]
                              if not area["id"].startswith("JOR:DOS2025:")]
    dataset["sources"] = [source for source in dataset["sources"]
                          if source["id"] not in {SOURCE_LOC, SOURCE_EST, SOURCE_MUN, SOURCE_CENSUS, SOURCE_GUIDE, SOURCE_LAW}]
    governors = {area["name"]: area for area in dataset["territories"] if area["parent_id"] == "JOR"}
    if set(governors) != set(GOV_NAME.values()) or len(dataset["boundaries"]["features"]) != 12:
        raise ValueError("Reference governorate roster or geometry changed")
    observations = []
    territories = []
    crosswalk = []
    child_values = defaultdict(list)
    row_values = {}
    current_gov = current_district = None
    roster = Counter()
    held_rows = []
    for row_number in range(5, 122):
        row = source_rows[row_number - 1]
        arabic, male, female, population, households, label = row[:6]
        if not isinstance(arabic, str) or not isinstance(label, str):
            raise ValueError(f"Unrecognised non-data row in locality summary {row_number}")
        for col, value in zip("BCDE", (male, female, population, households)):
            integer(value, f"الملخص !{col}{row_number}")
        if male + female != population:
            raise ValueError(f"Male+female mismatch at locality summary row {row_number}")
        label = english(label)
        if 118 <= row_number <= 121:
            # The source lists two district *centres* and two qadaa as four
            # disjoint reporting rows. It has no complete district totals.
            # Do not invent a parent or compare the mixed ranks as peers.
            held_rows.append({"row": row_number, "source_name_ar": arabic.strip(),
                              "source_name_en": label, "population": population,
                              "disposition": "not_adopted_mixed_rank_parent_not_verified"})
            continue
        if arabic.strip().startswith("محافظة"):
            kind = "governorate"
            source_name = label.removesuffix(" Governorate")
            if source_name not in GOV_NAME:
                raise ValueError(f"Governorate source label not crosswalked: {source_name}")
            area = governors[GOV_NAME[source_name]]
            area["source_name_en"] = label
            area["source_name_ar"] = arabic.strip()
            area["source_locator"] = f"الملخص !A{row_number}:F{row_number}"
            area["reconciliation_status"] = "official_dos_name_to_2006_reference_shape_only"
            territory_id = area["id"]
            current_gov, current_district = area, None
            parent_id = "JOR"
        elif arabic.strip().startswith(("لواء", "مركز لواء")):
            kind = "district"
            if current_gov is None:
                raise ValueError(f"District before governorate at row {row_number}")
            parent_id = current_gov["id"]
            digest = hashlib.sha1((parent_id + "|district|" + arabic.strip()).encode()).hexdigest()[:16]
            territory_id = f"JOR:DOS2025:ADM2:{digest}"
            area = {"id": territory_id, "country_id": "JOR", "parent_id": parent_id,
                    "level": "adm2", "type": "District", "name": label,
                    "source_name_ar": arabic.strip(), "source_locator": f"الملخص !A{row_number}:F{row_number}",
                    "source_id": SOURCE_LOC, "official_code": None, "boundary_version": None,
                    "reconciliation_status": "official_dos_hierarchy_provisional_id_no_boundary"}
            territories.append(area)
            current_district = area
        elif arabic.strip().startswith("قضاء"):
            kind = "subdistrict"
            if current_district is None:
                raise ValueError(f"Sub-district before district at row {row_number}")
            parent_id = current_district["id"]
            digest = hashlib.sha1((parent_id + "|subdistrict|" + arabic.strip()).encode()).hexdigest()[:16]
            territory_id = f"JOR:DOS2025:ADM3:{digest}"
            area = {"id": territory_id, "country_id": "JOR", "parent_id": parent_id,
                    "level": "adm3", "type": "Sub-District", "name": label,
                    "source_name_ar": arabic.strip(), "source_locator": f"الملخص !A{row_number}:F{row_number}",
                    "source_id": SOURCE_LOC, "official_code": None, "boundary_version": None,
                    "reconciliation_status": "official_dos_hierarchy_provisional_id_no_boundary"}
            territories.append(area)
        else:
            raise ValueError(f"Unknown administrative type at row {row_number}: {arabic}")
        roster[kind] += 1
        row_values[territory_id] = (male, female, population, households)
        child_values[parent_id].append((male, female, population, households))
        for suffix, value, col in (("POP", population, "D"), ("MALE", male, "B"),
                                   ("FEMALE", female, "C"), ("HOUSEHOLDS", households, "E")):
            add_observation(observations, territory_id, suffix, value, SOURCE_LOC,
                            f"الملخص !{col}{row_number}")
        crosswalk.append((row_number, kind, parent_id, territory_id, arabic.strip(), label,
                          "" if kind != "governorate" else area.get("provider_code", ""),
                          "" if kind != "governorate" else area.get("boundary_version", ""),
                          "name_only_reference" if kind == "governorate" else "official_source_hierarchy_no_code_or_shape"))
    if roster != Counter({"governorate": 12, "district": 49, "subdistrict": 52}) or len(held_rows) != 4:
        raise ValueError(f"DoS source hierarchy counts changed: {roster}")
    if len({area["id"] for area in territories}) != len(territories):
        raise ValueError("Provisional geography ID collision")
    for parent_id, children in child_values.items():
        if parent_id == "JOR":
            expected = tuple(national[1:5])
        else:
            expected = row_values[parent_id]
        actual = tuple(sum(row[index] for row in children) for index in range(4))
        if actual != expected:
            raise ValueError(f"Source hierarchy totals do not reconcile for {parent_id}: {actual} != {expected}")
    for suffix, value, col in (("POP", national[3], "D"), ("MALE", national[1], "B"),
                               ("FEMALE", national[2], "C"), ("HOUSEHOLDS", national[4], "E")):
        add_observation(observations, "JOR", suffix, value, SOURCE_LOC, f"الملخص !{col}122")
    # Cross-check Table 2.2 sex totals and Table 2.3 urban/rural totals.
    for offset, source_name in enumerate(ESTIMATE_GOV_ORDER, 6):
        sex = sex_rows[offset - 1]
        urban = sex_rows[offset + 20]
        if english(sex[5]) != source_name or english(urban[4]) != source_name:
            raise ValueError(f"DoS governorate order changed at {offset}")
        area = governors[GOV_NAME[source_name]]
        if tuple(sex[1:4]) != row_values[area["id"]][:3]:
            raise ValueError(f"Table 2.2 and locality source differ for {source_name}")
        if urban[1] + urban[2] != urban[3] or urban[3] != sex[3]:
            raise ValueError(f"Table 2.3 urban+rural mismatch for {source_name}")
        for suffix, value, col in (("URBAN", urban[1], "B"), ("RURAL", urban[2], "C")):
            add_observation(observations, area["id"], suffix, integer(value, f"2.3!{col}{offset+21}"),
                            SOURCE_EST, f"2.3!{col}{offset+21}")
    if tuple(sex_rows[17][1:4]) != tuple(national[1:4]) or tuple(sex_rows[38][1:4]) != (10784700, 1152300, 11937000):
        raise ValueError("DoS 2025 sex or urban/rural national totals changed")
    for suffix, value, col in (("URBAN", sex_rows[38][1], "B"), ("RURAL", sex_rows[38][2], "C")):
        add_observation(observations, "JOR", suffix, value, SOURCE_EST, f"2.3!{col}39")
    # Table 2.6 supplies reported area and density; verify its population column.
    for offset, source_name in enumerate(ESTIMATE_GOV_ORDER, 29):
        row = area_rows[offset - 1]
        if english(row[7]) != source_name:
            raise ValueError(f"DoS area table order changed at {offset}")
        area = governors[GOV_NAME[source_name]]
        if row[3] != row_values[area["id"]][2] or abs(row[3] / row[4] - row[6]) > 1e-6:
            raise ValueError(f"DoS area/density identity failed for {source_name}")
        for suffix, value, col in (("AREA_KM2", row[4], "E"), ("DENSITY", row[6], "G")):
            add_observation(observations, area["id"], suffix, value, SOURCE_EST, f"2.7!{col}{offset}")
    total_area = area_rows[40]
    if total_area[3] != national[3] or abs(total_area[3] / total_area[4] - total_area[6]) > 1e-6:
        raise ValueError("DoS national area/density identity failed")
    for suffix, value, col in (("AREA_KM2", total_area[4], "E"), ("DENSITY", total_area[6], "G")):
        add_observation(observations, "JOR", suffix, value, SOURCE_EST, f"2.7!{col}41")
    assert len(observations) == (113 + 1) * 4 + 13 * 4
    dataset["territories"] += territories
    indicators = []
    for suffix, name, unit, definition in FIELDS_LOCAL + FIELDS_GOV:
        population_estimate = suffix not in {"AREA_KM2", "DENSITY"}
        indicators.append({"id": PREFIX + suffix, "name": name, "theme": "DoS population estimates 2025",
                           "unit": unit, "definition": definition + (". These are 2025 annual estimates based on the 2015 census, not 2025 enumeration counts." if population_estimate else ". Area is source-reported; density uses the 2025 population estimate and source-reported area."),
                           "population": "Residents of Jordan as estimated by the Department of Statistics at end 2025" if population_estimate else "Jordan national territory or governorate as represented in DoS Table 2.6",
                           "source_id": SOURCE_LOC if suffix in {"POP", "MALE", "FEMALE", "HOUSEHOLDS"} else SOURCE_EST,
                           "aggregation": "none" if suffix == "DENSITY" else "sum",
                           "measurement_method": "source_reported",
                           "period_policy": "latest_available_per_indicator",
                           "display_decimals": 2 if suffix in {"AREA_KM2", "DENSITY"} else 0})
    dataset["indicators"] = [item for item in dataset["indicators"] if not item["id"].startswith(PREFIX)] + indicators
    dataset["observations"] = [item for item in dataset["observations"] if not item["indicator_id"].startswith(PREFIX)] + observations
    stamp = datetime.now(timezone.utc).isoformat()
    retrieved = {filename: datetime.fromtimestamp((raw / filename).stat().st_mtime, timezone.utc).isoformat()
                 for filename in (LOCALITY[0], ESTIMATES[0], MUNICIPALITIES[0], PLANNING_GUIDE[0], LOCAL_LAW[0])}
    dataset["generated_at"] = stamp
    dataset["sources"] += [
        {"id": SOURCE_LOC, "name": "DoS 2025 Population Estimates by Locality, Sex and Households",
         "url": URL_BASE + LOCALITY[0], "publisher": "Jordan Department of Statistics",
         "reference_period": "End of 2025", "geographic_level": "country, governorate, district, sub-district",
         "status": "ready", "retrieved_at": retrieved[LOCALITY[0]], "sha256": LOCALITY[1],
         "raw_path": f"raw/official-jordan/{LOCALITY[0]}", "license": "terms_review_required",
         "note": "Summary sheet only adopted. Twelve detailed locality sheets remain inventoried but not joined to official codes or boundaries."},
        {"id": SOURCE_EST, "name": "DoS 2025 Population Estimates, Tables 2.2, 2.3 and 2.6",
         "url": URL_BASE + ESTIMATES[0], "publisher": "Jordan Department of Statistics",
         "reference_period": "End of 2025", "geographic_level": "country, governorate",
         "status": "ready", "retrieved_at": retrieved[ESTIMATES[0]], "sha256": ESTIMATES[1],
         "raw_path": f"raw/official-jordan/{ESTIMATES[0]}", "license": "terms_review_required",
         "note": "National and governorate male/female, urban/rural, area and density are source-reported estimates. Historic and administrative-division tables have separate dispositions."},
        {"id": SOURCE_MUN, "name": "DoS 2025 Population Estimates by Municipality",
         "url": URL_BASE + MUNICIPALITIES[0], "publisher": "Jordan Department of Statistics",
         "reference_period": "End of 2025", "geographic_level": "municipality and locality",
         "status": "partial", "retrieved_at": retrieved[MUNICIPALITIES[0]], "sha256": MUNICIPALITIES[1],
         "raw_path": f"raw/official-jordan/{MUNICIPALITIES[0]}", "license": "terms_review_required",
         "note": "Acquired and mechanically inventoried only. Municipalities are a separate classification from the administrative district hierarchy; no values are adopted."},
        {"id": SOURCE_CENSUS, "name": "DoS 2015 Population and Housing Census statistical table catalogue",
         "url": "https://dosweb.dos.gov.jo/censuses/population_housing/census2015/census2015_tables/",
         "publisher": "Jordan Department of Statistics", "reference_period": "2015",
         "geographic_level": "varies by table; governorate listed in multiple tables",
         "status": "not_collected", "retrieved_at": stamp, "license": "terms_review_required",
         "note": "Official catalogue location verified. Individual thematic tables, cell meanings, geography and reuse terms have not been acquired or audited."},
        {"id": SOURCE_GUIDE, "name": "Guide for the Preparation of Governorate Strategic Development and Implementation Plans",
         "url": GUIDE_URL, "publisher": "Jordan Ministry of Interior",
         "reference_period": "2018 guidance", "geographic_level": "governorate",
         "status": "partial", "retrieved_at": retrieved[PLANNING_GUIDE[0]], "sha256": PLANNING_GUIDE[1],
         "raw_path": f"raw/official-jordan/{PLANNING_GUIDE[0]}", "license": "terms_review_required",
         "note": "2018 PDF acquired and its cover, contents and data-analysis sections inspected. It cites the 2015 decentralization law; current applicability under the 2021 local administration law and actual governorate plans remain unverified."},
        {"id": SOURCE_LAW, "name": "Local Administration Law No. 22 of 2021",
         "url": LAW_URL, "publisher": "Jordan Ministry of Local Administration",
         "reference_period": "2021 law", "geographic_level": "governorate and municipality; provisions unassessed",
         "status": "partial", "retrieved_at": retrieved[LOCAL_LAW[0]], "sha256": LOCAL_LAW[1],
         "raw_path": f"raw/official-jordan/{LOCAL_LAW[0]}", "license": "terms_review_required",
         "note": "Official 53-page image PDF acquired and title checked. Articles, amendments, current applicability, planning responsibilities and actual local documents remain unassessed; OCR or manual legal review required."},
    ]
    dataset["country"]["geography_note"] = (
        "DoS 2025 population estimates supply 12 governorates; 49 districts and 52 sub-districts are provisionally represented for 11 governorates. Four Aqaba district-centre/qadaa rows are withheld because the source has no complete district parents, so a same-rank comparison cannot be verified. The lower levels use provisional source-scoped IDs without official codes or matched shapes. Governorate geometry is a 2006 geoBoundaries reference matched by name only, not a certified 2025 boundary. Municipalities and localities are separate classifications; the 2025 estimates are not census counts.")
    dataset["gaps"] = [item for item in dataset["gaps"] if item["category"] != "subnational_statistics"]
    dataset["gaps"].append({"category": "subnational_statistics", "status": "partial",
                            "detail": "Official 2025 annual population estimates integrated for 12 governorates and for 49 districts plus 52 sub-districts in 11 governorates. Four Aqaba lower rows are held because the parent hierarchy and mixed-rank comparison are unresolved. Detailed locality and municipality workbooks, 2015 census thematic tables and other sectors await semantic/geographic review.",
                            "next_action": "Acquire official administrative codes and 2025 boundary version; inventory and adopt eligible census, locality, municipal and sector tables without conflating administrative and municipal units."})
    dataset["gaps"] = [item for item in dataset["gaps"] if item["category"] != "planning_documents"]
    dataset["gaps"].append({"category": "planning_documents", "status": "not_collected",
                            "detail": "A 2018 governorate planning guide and the 2021 local administration law were acquired as general sources. Their current legal relationship and applicability have not been established. No selected-governorate or municipality plan, budget, implementation report or official evaluation has been collected or verified.",
                            "next_action": "Review the image-only 2021 law and any amendments; verify current planning responsibilities and obtain actual selected-area plans, budgets, implementation and evaluation with period and approval status."})
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["jordan-dos-2025-population-estimates"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["analysis"]["default_indicator_id"] = PREFIX + "POP"
    dataset["analysis"]["population_context"] = {
        "primary_indicator_id": PREFIX + "POP",
        "reference_indicator_id": "SP.POP.TOTL",
        "reference_period": "2025",
        "note": "Jordan DoS end-2025 annual estimate and World Bank midyear estimate are separate series and must not be merged."
    }
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    with (evidence / "CODE_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("source_row", "administrative_type", "parent_id", "territory_id",
                         "source_name_ar", "source_name_en", "reference_provider_id",
                         "reference_boundary_version", "reconciliation_status"))
        writer.writerows(crosswalk)
    audit = {"country": "JOR", "status": "partial_import_not_accepted",
             "source_hashes": {LOCALITY[0]: LOCALITY[1], ESTIMATES[0]: ESTIMATES[1],
                               MUNICIPALITIES[0]: MUNICIPALITIES[1], PLANNING_GUIDE[0]: PLANNING_GUIDE[1],
                               LOCAL_LAW[0]: LOCAL_LAW[1]},
             "source_bytes": {LOCALITY[0]: size_loc, ESTIMATES[0]: size_est,
                              MUNICIPALITIES[0]: size_mun, PLANNING_GUIDE[0]: size_guide, LOCAL_LAW[0]: size_law},
             "adopted_tables": ["PopulationEstimatesbyLocality.xlsx/الملخص : rows 5-122, B:E",
                                "PopulationEstimates.xlsx/2.3: Table 2.3 rows 27-39, B:D",
                                "PopulationEstimates.xlsx/2.7: Table 2.6 rows 29-41, D:G"],
             "distinct_local_indicators": 8, "domestic_observations": len(observations),
             "territories": dict(roster), "held_aqaba_rows": held_rows,
             "national_population": national[3],
             "national_households": national[4],
             "reconciliation": "Sex components, all parent/child summary rows, governorate/national totals, urban+rural, and reported population/area/density agree within source precision.",
             "not_adopted": ["Detailed locality tables: code and locality/municipality mapping pending",
                             "Municipality workbook: separate institution/territory classification pending",
                             "2015 census thematic tables: not yet acquired and reviewed",
                             "Historic Table 2.1, Table 2.4 duplicate admin population, Table 2.5 national age/sex: separately inventoried, not adopted"],
             "unresolved": ["Official codes at all levels", "2025 legal boundary equivalence",
                            "Current legal planning units and actual planning documents",
                            "License and redistribution terms", "Independent audit and publication"]}
    (evidence / "JOR_POPULATION_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename, digest, size, url in ((LOCALITY[0], LOCALITY[1], size_loc, URL_BASE + LOCALITY[0]),
                                        (ESTIMATES[0], ESTIMATES[1], size_est, URL_BASE + ESTIMATES[0]),
                                        (MUNICIPALITIES[0], MUNICIPALITIES[1], size_mun, URL_BASE + MUNICIPALITIES[0]),
                                        (PLANNING_GUIDE[0], PLANNING_GUIDE[1], size_guide, GUIDE_URL),
                                        (LOCAL_LAW[0], LOCAL_LAW[1], size_law, LAW_URL)):
        receipt = {"url": url, "retrieved_at_utc": retrieved[filename],
                   "receipt_recorded_at_utc": stamp,
                   "size_bytes": size, "sha256": digest,
                   "redistribution_terms": "review_required", "signature": "PDF" if filename.endswith('.pdf') else "PK ZIP XLSX"}
        (raw / f"{filename}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": dict(roster), "indicators": 8,
                      "domestic_observations": len(observations), "national_population": national[3]}))


if __name__ == "__main__":
    main()

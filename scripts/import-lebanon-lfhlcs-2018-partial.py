"""Adopt CAS LFHLCS HL5 survey estimates in its eight-governorate/26-caza scope."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import xlrd


RAW = "raw/lebanon-cas-moph/"
HASHES = {
    "lfhlcs-2018-19-demography.xls": "780f52f78949de142593717cde07cda03256d5759b534096443cf77a4e315486",
    "lfhlcs-2018-19-full-report.pdf": "589b164265045769ae5bf646e86fc2e4f05bbdbd47e07743c7f7b2583d457990",
    "moph-adm1.geojson": "a1cee334dec0d77c00e351b4fad3b1b4fbdaf27bbbce2fbffa34270fc456f3cf",
    "moph-adm2.geojson": "27ffa8eb11f9c6e5f90108ab308ec241c39a1763777a30b93ce2efd46546b154",
}
FIELDS = ((2, "WOMEN", "Female residents"), (3, "MEN", "Male residents"),
          (4, "TOTAL", "Residents, both sexes"))
CAS_TO_MOPH = {
    "Beirut": "Beirut", "Baabda": "Baabda", "Matn": "El Meten", "Chouf": "Chouf",
    "Aley": "Aley", "Keserwan": "Kesrwane", "Jbeil": "Jbeil", "Tripoli": "Tripoli",
    "Koura": "El Koura", "Zgharta": "Zgharta", "Batroun": "El Batroun",
    "Bcharre": "Bcharre", "Minieh-Danniyeh": "El Minieh-Dennie", "Akkar": "Akkar",
    "Zahleh": "Zahle", "West Beqaa": "West Bekaa", "Rachaya": "Rachaya",
    "Baalbek": "Baalbek", "Hermel": "El Hermel", "Saida": "Saida", "Tyr": "Sour",
    "Jezzine": "Jezzine", "Nabatieh": "El Nabatieh", "Bint Jbeil": "Bent Jbeil",
    "Marjaayoun": "Marjaayoun", "Hasbaya": "Hasbaya",
}
SOURCE_ID = "lbn-cas-lfhlcs-2018-19-hl5"
MOPH_VERSION = "MOPH_Administrative_Zones_undated_acquired_20260926"
SURVEY_VERSION = "CAS_LFHLCS_2018_19_reporting_geography"


def verified_receipt(project, filename):
    relative = RAW + filename
    path = project / relative
    receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != HASHES[filename] or receipt["sha256"] != actual or receipt["status"] != "acquired":
        raise ValueError(f"Original changed: {filename}")
    return receipt


def people(thousands):
    if not isinstance(thousands, (int, float)) or isinstance(thousands, bool):
        raise ValueError("HL5 expected numeric estimate")
    return round(thousands * 10) * 100


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "LBN" or any(s["id"] == SOURCE_ID for s in dataset["sources"]):
        raise ValueError("Expected unimproved Lebanon candidate")
    receipts = {name: verified_receipt(project, name) for name in HASHES}
    book = xlrd.open_workbook(project / (RAW + "lfhlcs-2018-19-demography.xls"), on_demand=True)
    sheet = book.sheet_by_name("HL5")
    if sheet.nrows != 42 or sheet.ncols != 7 or "in thousands" not in sheet.cell_value(0, 0):
        raise ValueError("HL5 table layout changed")
    if [sheet.cell_value(4, index) for index in (2, 3, 4)] != ["Women", "Men", "Women & Men"]:
        raise ValueError("HL5 sex-column labels changed")
    governors, districts = {}, []
    current_governor = None
    for row_index in range(6, 40):
        row = sheet.row_values(row_index)
        if row[0]:
            current_governor = str(row[0]).strip()
        if row[1] == "Total":
            if current_governor in governors:
                raise ValueError("Duplicate governorate total")
            governors[current_governor] = (row_index + 1, row)
        elif row[1]:
            districts.append((current_governor, str(row[1]).strip(), row_index + 1, row))
        else:
            raise ValueError(f"Unexpected HL5 row {row_index + 1}")
    national = (41, sheet.row_values(40))
    if national[1][0] != "Lebanon" or len(governors) != 8 or len(districts) != 26 or \
            set(CAS_TO_MOPH) != {name for _, name, _, _ in districts}:
        raise ValueError("HL5 reporting geography changed")
    if abs(national[1][4] - 4842.467432738223) > 1e-6 or people(national[1][4]) != 4_842_500:
        raise ValueError("HL5 national/PDF Table 1.1 control changed")
    for col, _, _ in FIELDS:
        if abs(sum(row[col] for _, row in governors.values()) - national[1][col]) > 1e-6:
            raise ValueError("HL5 governorate/national control changed")
        for name, (_, total) in governors.items():
            if abs(sum(row[col] for governor, _, _, row in districts if governor == name) - total[col]) > 1e-6:
                raise ValueError(f"HL5 caza/governorate control changed: {name}")
    for _, _, _, row in districts:
        if abs(row[2] + row[3] - row[4]) > 1e-6:
            raise ValueError("HL5 sex total changed")
    book.release_resources()
    catalogue = json.loads((project / "evidence/LBN_CAS_DISTRICT_PROFILE_CATALOG.json").read_text(encoding="utf-8"))
    pairs = {(item["region"], item["district"]) for item in catalogue["entries"] if item["language"] == "English"}
    if pairs != {(governor, name) for governor, name, _, _ in districts}:
        raise ValueError("CAS profile catalogue/HL5 caza universe differs")
    geo1 = json.loads((project / (RAW + "moph-adm1.geojson")).read_text(encoding="utf-8"))
    geo2 = json.loads((project / (RAW + "moph-adm2.geojson")).read_text(encoding="utf-8"))
    if len(geo1["features"]) != 9 or len(geo2["features"]) != 26:
        raise ValueError("MOPH map service coverage changed")
    moph = {feature["properties"]["NAME"]: feature for feature in geo2["features"]}
    if set(moph) != set(CAS_TO_MOPH.values()) or len({feature["properties"]["PCODE"] for feature in geo2["features"]}) != 26:
        raise ValueError("MOPH 26 caza names/codes changed")
    now = datetime.now(timezone.utc).isoformat()
    original_provider_territories = [area["name"] for area in dataset["territories"] if area["parent_id"] == "LBN"]
    country = next(area for area in dataset["territories"] if area["id"] == "LBN")
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    gov_ids = {}
    for name in governors:
        gov_id = "LBN:CAS-LFHLCS-2018:GOV:" + name.upper().replace(" ", "-")
        gov_ids[name] = gov_id
        dataset["territories"].append({"id": gov_id, "name": name, "level": "adm1",
            "type": "LFHLCS 2018-19 governorate reporting area", "parent_id": "LBN",
            "official_code": None, "code_system": "CAS LFHLCS 2018-19 reporting name; no source code",
            "boundary_version": None, "source_id": SOURCE_ID,
            "reconciliation_status": "source_native_eight_governorate_reporting_area; boundary_polygon_unverified"})
    district_ids, crosswalk = {}, []
    for governor, name, row_number, row in districts:
        feature = moph[CAS_TO_MOPH[name]]
        code = feature["properties"]["PCODE"]
        territory_id = "LBN:MOPH:ADM2:" + code
        district_ids[name] = territory_id
        dataset["territories"].append({"id": territory_id, "name": name, "level": "adm2",
            "type": "Caza / CAS LFHLCS 2018-19 reporting district", "parent_id": gov_ids[governor],
            "official_code": None, "code_system": "MOPH ArcGIS PCODE (legal status/version unverified)",
            "provider_code": code, "boundary_version": MOPH_VERSION, "source_id": SOURCE_ID,
            "source_governorate": governor, "provider_name": CAS_TO_MOPH[name],
            "reconciliation_status": "cas_moph_name_correspondence_only; dated_legal_boundary_equivalence_unverified"})
        dataset["boundaries"]["features"].append({"type": "Feature", "properties": {
            "territory_id": territory_id, "name": name, "provider_name": CAS_TO_MOPH[name],
            "provider_code": code, "boundary_version": MOPH_VERSION}, "geometry": feature["geometry"]})
        crosswalk.append((governor, name, row_number, CAS_TO_MOPH[name], code, territory_id,
                          "name_correspondence_only; temporal/legal boundary equivalence unverified"))
    dataset["sources"].extend([
        {"id": SOURCE_ID, "name": "CAS Labour Force and Household Living Conditions Survey 2018-19, Demography XLS Table HL5",
         "url": receipts["lfhlcs-2018-19-demography.xls"]["url"], "publisher": "Central Administration of Statistics (Lebanon)",
         "reference_period": "April 2018–March 2019 fieldwork; midyear 2018 population estimate",
         "geographic_level": "Lebanon, eight source-reporting governorates and 26 caza; residential-dwelling residents only",
         "status": "ready", "retrieved_at": receipts["lfhlcs-2018-19-demography.xls"]["retrieved_at"],
         "raw_path": RAW + "lfhlcs-2018-19-demography.xls", "sha256": HASHES["lfhlcs-2018-19-demography.xls"],
         "license": "terms_review_required", "note": "Sample-survey estimate, not a census. Only HL5 Women, Men and Women & Men columns adopted; weighted thousands were scaled and rounded to 100 persons as in report Table 1.1. Other 23 table sheets remain unassessed."},
        {"id": "lbn-cas-lfhlcs-2018-19-full-report", "name": "CAS LFHLCS 2018-19 full report",
         "url": receipts["lfhlcs-2018-19-full-report.pdf"]["url"], "publisher": "Central Administration of Statistics (Lebanon)",
         "reference_period": "2018–19 survey", "geographic_level": "eight survey governorates and 26 caza",
         "status": "partial", "retrieved_at": receipts["lfhlcs-2018-19-full-report.pdf"]["retrieved_at"],
         "raw_path": RAW + "lfhlcs-2018-19-full-report.pdf", "sha256": HASHES["lfhlcs-2018-19-full-report.pdf"],
         "license": "terms_review_required", "note": "PDF pages 19–21 visually checked for midyear reference, resident universe, eight governorates/26 caza and rounded Table 1.1; remaining report content not fully audited."},
        {"id": "lbn-cas-lfs-district-profiles-2018-19", "name": "CAS/UNDP 26 district statistical profiles catalogue",
         "url": catalogue["catalogue_url"], "publisher": "Central Administration of Statistics (Lebanon)",
         "reference_period": "2018–19 survey; 2020 publication", "geographic_level": "26 caza, eight source governorates",
         "status": "partial", "retrieved_at": now, "raw_path": RAW + "cas-district-catalogue.html",
         "sha256": catalogue["catalogue_sha256"], "license": "terms_review_required",
         "note": "All 26 English PDFs acquired and 26 Arabic alternatives inventoried. Akkar PDF p7 was visually checked; no extra numeric field was adopted from profiles. Their contents remain to be audited."},
        *[{"id": f"lbn-moph-adm{level}-map", "name": f"Ministry of Public Health Administrative Zones ADM{level} ArcGIS layer",
           "url": receipts[f"moph-adm{level}.geojson"]["url"], "publisher": "Ministry of Public Health (Lebanon)",
           "reference_period": "map service edition/date not stated; retrieved 2026-09-26",
           "geographic_level": f"{9 if level == 1 else 26} administrative map features",
           "status": "partial", "retrieved_at": receipts[f"moph-adm{level}.geojson"]["retrieved_at"],
           "raw_path": RAW + f"moph-adm{level}.geojson", "sha256": HASHES[f"moph-adm{level}.geojson"],
           "license": "terms_review_required", "note": "Government-hosted reference map with PCODE fields, not a verified legal code/boundary edition. ADM1 has nine features including KSH, unlike CAS survey's eight governorates. ADM2 has 26 name-matched reference polygons."}
          for level in (1, 2)]
    ])
    for col, suffix, title in FIELDS:
        indicator_id = "LBN_CAS_LFHLCS_2018_" + suffix
        dataset["indicators"].append({"id": indicator_id, "name": title + " (LFHLCS 2018–19 estimate)",
            "theme": "Demography", "unit": "people",
            "definition": "Weighted midyear-2018 sample-survey estimate of residents living in residential dwellings, excluding persons in non-residential units. CAS Table HL5 reports thousands; values are scaled to people and rounded to the nearest 100, matching report Table 1.1 precision. This is not a population census. Survey governorates use the source's eight-unit reporting geography; MOPH map shows nine governorates in an undated edition.",
            "population": "Residents of Lebanon living in residential dwellings during LFHLCS 2018–19",
            "source_id": SOURCE_ID, "aggregation": "none", "measurement_method": "survey_estimate_scaled_rounded",
            "series_family": "survey", "display_role": "primary", "period_policy": "latest_available_per_indicator",
            "display_decimals": 0})
        rows = [("LBN", *national, False)] + [(gov_ids[name], *entry, False) for name, entry in governors.items()] + \
               [(district_ids[name], row_number, row, True) for _, name, row_number, row in districts]
        for territory_id, row_number, row, mismatch in rows:
            record = {"territory_id": territory_id, "indicator_id": indicator_id, "period": "2018",
                      "value": people(row[col]), "status": "observed", "measurement_method": "survey_estimate_scaled_rounded",
                      "source_id": SOURCE_ID,
                      "source_locator": f"HL5!{chr(65 + col)}{row_number}; {title}; original thousands={row[col]}; multiplied by 1000 and rounded to 100 people"}
            if mismatch:
                record["boundary_version"] = SURVEY_VERSION
            dataset["observations"].append(record)
    dataset["country"]["geography_note"] = (
        "CAS LFHLCS 2018–19 reports eight survey governorates and 26 caza; its estimate covers residents of residential dwellings and is not a census. The Ministry of Public Health's undated map service has nine governorate features including KSH, so its ADM1 shapes are not silently assigned to CAS survey governorates. The 26 MOPH caza outlines are name-matched reference drawings only; survey-value to current boundary equivalence is unverified and numeric polygon coloring is withheld. National WDI series remain separate.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="CAS 2018-19 survey: eight reporting governorates/26 caza. MOPH undated map: nine governorates/26 caza, with KSH separate; 2017 geoBoundaries also has nine ADM1 units. Twenty-six caza names match MOPH polygons, but legal code/edition and temporal equivalence are unverified. Survey governorates have no asserted polygon.",
                       next_action="Obtain dated legal governorate/caza boundary and code tables; resolve the KSH split and confirm 2018-19 survey geography before map coloring or current-unit attribution.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="CAS LFHLCS Table HL5 supplies weighted midyear-2018 resident estimates by sex for nation, eight source governorates and 26 caza (105 adopted records). Twenty-three other demography table sheets and 26 district profiles are acquired but not semantically adopted.",
                       next_action="Audit remaining survey table fields and 26 profiles; inspect the 2023 MICS restricted geographic coverage; collect current comparable local statistics without treating surveys as a census.")
        elif gap["category"] == "planning_documents":
            gap.update(status="not_collected", detail="No municipality/municipal-union plan, approved budget, actual expenditure or official evaluation has been acquired or linked to a verified planning unit.",
                       next_action="Check current municipal law, DGLAC/DGU responsibilities, municipal plans and finance/implementation records by verified municipal identifier.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["lebanon-cas-lfhlcs-2018-hl5-partial"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["generated_at"] = now
    evidence = project / "evidence"
    with (evidence / "LBN_CAS_MOPH_CAZA_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("cas_2018_governorate", "cas_caza", "hl5_row", "moph_name", "moph_pcode",
                         "territory_id", "decision"))
        writer.writerows(crosswalk)
    audit = {"status": "partial_candidate_not_accepted", "checked_at": now, "source_hashes": HASHES,
             "source_table": "HL5", "source_sheet_count": 26, "adopted_columns": ["Women", "Men", "Women & Men"],
             "adopted_source_governorates": list(governors), "adopted_caza_count": 26,
             "observations_added": 105, "source_national_estimated_people": people(national[1][4]),
             "original_provider_adm1_names": original_provider_territories,
             "moph_adm1_names": [item["properties"]["NAME"] for item in geo1["features"]],
             "survey_eight_vs_map_nine_unresolved": True,
             "all_numeric_columns_decided": False,
             "unresolved": ["Dated legal code/boundary equivalence", "KSH survey/current governorate scope",
                            "Remaining demography workbook fields and 26 profile contents", "2023 MICS coverage and values",
                            "Municipal planning institutions, plans/budgets/execution/evaluation", "42 scenarios and independent acceptance"]}
    (evidence / "LBN_LFHLCS_HL5_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"governorates": len(governors), "caza": len(districts), "indicators": len(FIELDS),
                      "observations_added": 105, "national_estimate": people(national[1][4]),
                      "active_boundary_features": len(dataset["boundaries"]["features"])}))


if __name__ == "__main__":
    main()

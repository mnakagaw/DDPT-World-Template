"""Adopt the verified 12-Dec-2020 Oman eCensus population geographic subset."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl


RAW = "raw/oman-ecensus-moi/"
SOURCE_ID = "omn-ecensus-2020-population"
MOI_ID = "omn-moi-governorate-wilayat-2025"
MOI_HASH = "63225e0a09ad41a41d5bd3b98b506e9117defdd67b8a7bbc0770ed686c63419b"
DATE = "2020-12-12"
METHOD = "electronic_census_2020_population_snapshot"
STATUS_TO_SUFFIX = {"Omani": "OMANI", "Expat": "EXPAT"}


def verified_receipt(project, name):
    relative = RAW + name
    body = (project / relative).read_bytes()
    receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
    if receipt["status"] != "acquired" or receipt["sha256"] != hashlib.sha256(body).hexdigest():
        raise ValueError(f"Original or receipt changed: {name}")
    return body, receipt


def slug(value):
    return "-".join(value.upper().replace("'", "").split())


def integer(value, label):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Expected nonnegative integer census count: {label}={value}")
    return value


def values_by_status(data, geography):
    if data["headers"]["column_headers"][0] != [DATE]:
        raise ValueError("eCensus first reference date changed")
    result = defaultdict(dict)
    for index, (labels, cells) in enumerate(zip(data["headers"]["row_headers"], data["data"])):
        if labels[0] not in STATUS_TO_SUFFIX:
            raise ValueError(f"eCensus nationality category changed: {labels[0]}")
        value = cells[0][0]
        key = tuple(labels[1:])
        if key in result and labels[0] in result[key]:
            raise ValueError(f"Duplicate census source row: {labels}")
        result[key][labels[0]] = {"value": value, "row": index + 1}
    if geography == "national" and set(result) != {()}:
        raise ValueError("National pivot has unexpected geography")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "OMN" or any(s["id"] == SOURCE_ID for s in dataset["sources"]):
        raise ValueError("Expected unimproved Oman candidate")
    files = ("moi-governorate-wilayat-2025.xlsx", "ecensus-population-metadata.json",
             "ecensus-population-arabic-metadata.json", "ecensus-population-national-pivot.json",
             "ecensus-population-governorate-pivot.json", "ecensus-population-wilayat-pivot.json",
             "ecensus-population-arabic-wilayat-pivot.json")
    originals = {name: verified_receipt(project, name) for name in files}
    if originals["moi-governorate-wilayat-2025.xlsx"][1]["sha256"] != MOI_HASH:
        raise ValueError("MOI directory edition changed")
    structure = json.loads((project / "evidence/OMN_ECENSUS_MOI_STRUCTURE.json").read_text(encoding="utf-8"))
    if structure["moi_governorates"] != 11 or structure["moi_wilayats"] != 63 or \
            structure["2020_observed_nationality_wilayat_rows"] != 122:
        raise ValueError("Run structural inspection first")
    crosswalk = list(csv.DictReader((project / "evidence/OMN_ECENSUS_MOI_WILAYAT_CROSSWALK.csv").open(encoding="utf-8", newline="")))
    if len(crosswalk) != 130:
        raise ValueError("Bilingual source/MOI crosswalk changed")
    book = openpyxl.load_workbook(project / (RAW + "moi-governorate-wilayat-2025.xlsx"), read_only=True, data_only=True)
    gov_directory = {str(row[0]): row for row in list(book["المحافظات"].values)[1:]}
    wil_directory = {str(row[0]): row for row in list(book["الولايات"].values)[1:]}
    book.close()
    pivots = {kind: json.loads(originals[f"ecensus-population-{kind}-pivot.json"][0])
              for kind in ("national", "governorate", "wilayat")}
    values = {kind: values_by_status(pivot, kind) for kind, pivot in pivots.items()}
    national = values["national"][()]
    if {key: integer(item["value"], key) for key, item in national.items()} != \
            {"Expat": 1_739_692, "Omani": 2_731_456} or \
            pivots["national"]["totals"]["column_totals"][0] != [4_471_148]:
        raise ValueError("2020 eCensus national control changed")
    governor_values = {name: group for (name,), group in values["governorate"].items() if name != "Unknown"}
    if len(governor_values) != 11 or sum(group[status]["value"] for group in governor_values.values() for status in STATUS_TO_SUFFIX) != 4_471_148:
        raise ValueError("2020 eCensus governorate coverage changed")
    wilayat_values = {(gov, wil): group for (gov, wil), group in values["wilayat"].items()
                      if gov != "Unknown" and wil.upper() != "UNKNOWN"}
    observed_wil = {key: group for key, group in wilayat_values.items()
                    if all(group[status]["value"] is not None for status in STATUS_TO_SUFFIX)}
    unreported_wil = {key: group for key, group in wilayat_values.items()
                      if all(group[status]["value"] is None for status in STATUS_TO_SUFFIX)}
    if len(observed_wil) != 61 or len(unreported_wil) != 2 or \
            {key[1] for key in unreported_wil} != {"ALJABAL ALAKDAR", "SINAW"}:
        raise ValueError("2020 eCensus wilayat coverage changed")
    for governor, group in governor_values.items():
        for status in STATUS_TO_SUFFIX:
            if sum(integer(row[status]["value"], f"{key}/{status}") for key, row in observed_wil.items() if key[0] == governor) != group[status]["value"]:
                raise ValueError(f"2020 wilayat/governorate sum changed: {governor}/{status}")
    crosswalk_by_pair = {}
    for row in crosswalk:
        if row["disposition"] == "source_exception_unassigned":
            continue
        key = (row["english_governorate"], row["english_wilayat"])
        if key in crosswalk_by_pair:
            if (crosswalk_by_pair[key]["moi_region_id"], crosswalk_by_pair[key]["moi_wilayat_id"]) != \
                    (row["moi_region_id"], row["moi_wilayat_id"]):
                raise ValueError("Omani/Expat geographic crosswalk differs")
        else:
            crosswalk_by_pair[key] = row
    if set(crosswalk_by_pair) != set(wilayat_values):
        raise ValueError("Crosswalk does not cover source wilayat universe")
    now = datetime.now(timezone.utc).isoformat()
    old_provider_adm1 = [area["name"] for area in dataset["territories"] if area["parent_id"] == "OMN"]
    country = next(area for area in dataset["territories"] if area["id"] == "OMN")
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    governor_ids = {}
    for name, group in governor_values.items():
        matched = {crosswalk_by_pair[key]["moi_region_id"] for key in observed_wil if key[0] == name}
        if len(matched) != 1:
            raise ValueError(f"No unique MOI governorate name crosswalk: {name}")
        moi_id = matched.pop()
        gov_id = "OMN:ECENSUS2020:GOV:" + slug(name)
        governor_ids[name] = gov_id
        dataset["territories"].append({"id": gov_id, "name": name, "level": "adm1",
            "type": "2020 eCensus governorate reporting area", "parent_id": "OMN",
            "official_code": None, "code_system": "eCensus 2020 source label; MOI 2025 ID is a name crosswalk, not a 2020 legal code",
            "provider_code": moi_id, "source_id": SOURCE_ID, "boundary_version": None,
            "reconciliation_status": "ecensus_arabic_name_matches_moi_2025; dated_legal_boundary_equivalence_unverified"})
    wilayat_ids = {}
    for governor, wilayat in observed_wil:
        mapped = crosswalk_by_pair[(governor, wilayat)]
        moi_id = mapped["moi_wilayat_id"]
        if moi_id not in wil_directory or str(wil_directory[moi_id][3]) != mapped["moi_region_id"]:
            raise ValueError("MOI wilayat ID/parent changed")
        territory_id = "OMN:ECENSUS2020:WIL:" + slug(governor) + ":" + slug(wilayat)
        wilayat_ids[(governor, wilayat)] = territory_id
        dataset["territories"].append({"id": territory_id, "name": wilayat, "level": "adm2",
            "type": "2020 eCensus wilayat reporting area", "parent_id": governor_ids[governor],
            "official_code": None, "code_system": "eCensus 2020 source name; MOI 2025 WilayatId matched through Arabic label",
            "provider_code": moi_id, "moi_arabic_name": mapped["arabic_wilayat"],
            "source_id": SOURCE_ID, "boundary_version": None,
            "reconciliation_status": "bilingual_ecensus_value_signature_and_arabic_name_match_moi_2025; dated_legal_boundary_equivalence_unverified"})
    portal = "https://www.ecensus.gov.om/web/#/en/datasets"
    dataset["sources"].extend([
        {"id": SOURCE_ID, "name": "NCSI Electronic Census 2020 public population dataset, 12 December 2020",
         "url": portal, "publisher": "National Centre for Statistics and Information (Oman)",
         "reference_period": "12 December 2020 census snapshot only; later portal reference dates are distinct",
         "geographic_level": "Sultanate, 11 source governorates and 61 wilayats with 2020 counts; two later-listed wilayats have null 2020 cells",
         "status": "ready", "retrieved_at": originals["ecensus-population-wilayat-pivot.json"][1]["retrieved_at"],
         "raw_path": RAW + "ecensus-population-wilayat-pivot.json",
         "sha256": originals["ecensus-population-wilayat-pivot.json"][1]["sha256"],
         "license": "official_open_data_terms_review_required",
         "note": "Official eCensus table-builder API; national, governorate and wilayat pivot originals plus English/Arabic metadata and Arabic pivot are separately receipted. English 'Residential Status' is Arabic nationality (Omani/expatriate). National total is source pivot total; local totals are marked calculated from two source counts. Only 2020-12-12 cells adopted."},
        {"id": MOI_ID, "name": "Ministry of Interior governorate and wilayat name/ID directory, October 2025",
         "url": originals["moi-governorate-wilayat-2025.xlsx"][1]["source_url"],
         "publisher": "Ministry of Interior (Oman)", "reference_period": "2021–2025 in workbook metadata; published October 2025",
         "geographic_level": "11 governorates and 63 wilayats in 2025 directory",
         "status": "partial", "retrieved_at": originals["moi-governorate-wilayat-2025.xlsx"][1]["retrieved_at"],
         "raw_path": RAW + "moi-governorate-wilayat-2025.xlsx", "sha256": MOI_HASH,
         "license": "Oman Open Data License; terms_review_required",
         "note": "RegionId/WilayatId and Arabic/English names acquired; provider IDs are not asserted to be 2020 census legal codes. WinCount and other workbook fields are not adopted as numeric indicators. The two 2025-listed wilayats with null 2020 census cells stay source-only."},
    ])
    indicators = (
        ("TOTAL", "Population, all nationality categories", "Both Omani and expatriate categories; country source total, local sums of source counts"),
        ("OMANI", "Omani population", "Omani nationality category in the source's Arabic metadata"),
        ("EXPAT", "Expatriate population", "Expatriate category in the source's Arabic metadata"),
    )
    for suffix, title, population in indicators:
        indicator_id = "OMN_ECENSUS_2020_" + suffix
        dataset["indicators"].append({"id": indicator_id, "name": title + " (eCensus 2020)",
            "theme": "Population", "unit": "people", "source_id": SOURCE_ID,
            "definition": "Count in the official eCensus public Population Dataset at reference date 12 December 2020. The Arabic field labels Omani/expatriate as nationality; the English field calls it Residential Status. Local total is the transparent sum of the two source count categories. The 2025 Ministry of Interior directory is a name/ID crosswalk, not a certified 2020 boundary edition. Later eCensus dates and WDI annual estimates remain separate.",
            "population": population, "aggregation": "none", "measurement_method": METHOD,
            "series_family": "census", "display_role": "primary", "period_policy": "latest_available_per_indicator",
            "display_decimals": 0})
    units = [("OMN", national, "national")]
    units += [(governor_ids[name], group, "governorate:" + name) for name, group in governor_values.items()]
    units += [(wilayat_ids[key], group, "wilayat:" + "/".join(key)) for key, group in observed_wil.items()]
    for territory_id, group, context in units:
        counts = {status: integer(group[status]["value"], context + "/" + status) for status in STATUS_TO_SUFFIX}
        total = counts["Omani"] + counts["Expat"]
        if territory_id == "OMN" and total != pivots["national"]["totals"]["column_totals"][0][0]:
            raise ValueError("National source grand total disagrees with categories")
        for suffix, value in (("OMANI", counts["Omani"]), ("EXPAT", counts["Expat"]), ("TOTAL", total)):
            calculated = suffix == "TOTAL" and territory_id != "OMN"
            row = {"territory_id": territory_id, "indicator_id": "OMN_ECENSUS_2020_" + suffix,
                   "period": "2020", "value": value, "status": "observed", "source_id": SOURCE_ID,
                   "measurement_method": METHOD,
                   "source_locator": f"{context}; RUN_DATE={DATE}; " + (
                       f"Omani pivot row {group['Omani']['row']} + Expat pivot row {group['Expat']['row']}" if calculated else
                       ("national source grand total" if suffix == "TOTAL" else f"{suffix} pivot row {group['Omani' if suffix == 'OMANI' else 'Expat']['row']}"))}
            if calculated:
                row["provenance"] = "calculated"
                row["footnote"] = f"Same-date Omani {counts['Omani']:,} + expatriate {counts['Expat']:,} = {total:,}; both direct eCensus source cells, no geographic roll-up."
            dataset["observations"].append(row)
    if len(dataset["territories"]) != 73 or len([o for o in dataset["observations"] if o["indicator_id"].startswith("OMN_ECENSUS_2020_")]) != 219:
        raise ValueError("Adopted 2020 geography/counts changed")
    dataset["country"]["geography_note"] = (
        "The official eCensus 12-Dec-2020 population pivot has 11 reporting governorates and 61 wilayats with numeric counts. The October-2025 Ministry of Interior directory lists 11 governorates/63 wilayats; ALJABAL ALAKDAR and SINAW have null 2020 eCensus cells and are retained in the source crosswalk, not invented as zero or mapped as 2020 units. Arabic source names were matched to the MOI directory, but current legal boundary/code equivalence is unverified. No 2020 polygon is asserted; bootstrap seven reference polygons are withheld. WDI national estimates and later eCensus portal dates are separate.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="Official eCensus 2020 names and Arabic labels match 11/61 units in MOI October-2025 directory, but source 2020 codes/boundary polygons and temporal legal equivalence remain unverified. Two 2025-listed wilayats have null 2020 eCensus cells. Seven bootstrap ADM1 reference polygons were withheld.",
                       next_action="Acquire dated official 2020/2025 governorate/wilayat code and boundary editions; reconcile newly listed wilayats and source exceptions before numeric map coloring.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="NCSI 12-Dec-2020 eCensus nationality counts adopted for nation, 11 governorates and 61 wilayats: 219 records in three indicators. Other demographic fields, housing/enterprise datasets and later portal reference dates remain unassessed.",
                       next_action="Audit all eCensus fields and products; decide 2021/2023-26 annual snapshots separately, with definitions and geographic availability.")
        elif gap["category"] == "planning_documents":
            gap.update(status="not_collected", detail="No governorate/wilayat-specific official plan, approved budget, actual expenditure or evaluation has been acquired or linked to a verified planning unit.",
                       next_action="Inspect current national spatial strategy, 11th Five-Year Plan, governorate development plans, legal planning duties and local finance/evaluation originals.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["oman-ecensus-2020-population-partial"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["generated_at"] = now
    audited = sorted((o["territory_id"], o["indicator_id"], o["value"]) for o in dataset["observations"]
                     if o["indicator_id"].startswith("OMN_ECENSUS_2020_"))
    audit = {"status": "partial_candidate_not_accepted", "checked_at": now,
             "moi_sha256": MOI_HASH, "source_national_total": 4_471_148,
             "source_national_omani": 2_731_456, "source_national_expat": 1_739_692,
             "2020_reporting_governorates": 11, "2020_observed_wilayats": 61,
             "2025_directory_governorates": 11, "2025_directory_wilayats": 63,
             "2020_unreported_wilayats": sorted(["/".join(key) for key in unreported_wil]),
             "original_bootstrap_adm1_names": old_provider_adm1,
             "domestic_observations_added": 219,
             "adopted_tuple_sha256": hashlib.sha256(json.dumps(audited, ensure_ascii=False).encode("utf-8")).hexdigest(),
             "unresolved": ["Dated 2020/2025 legal code and boundary crosswalk", "Other census population fields and datasets",
                            "Later annual date/value classification", "Governorate development plans and finance/evaluation",
                            "42 scenarios and independent acceptance"]}
    (project / "evidence/OMN_ECENSUS_2020_IMPORT_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": len(dataset["territories"]), "governorates": 11,
                      "observed_wilayats": 61, "indicators": 3, "observations_added": 219,
                      "national_total": 4_471_148}, ensure_ascii=False))


if __name__ == "__main__":
    main()

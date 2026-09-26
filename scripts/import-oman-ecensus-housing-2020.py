"""Add source-reported 12-Dec-2020 housing-unit counts to an Oman candidate.

No occupancy, water, sanitation, or household interpretation is implied.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RAW = "raw/oman-ecensus-moi/"
DATE = "2020-12-12"
SOURCE_ID = "omn-ecensus-2020-housing-units"
INDICATOR_ID = "OMN_ECENSUS_2020_HOUSING_UNITS"
METHOD = "electronic_census_2020_housing_unit_snapshot"


def verified(project, name):
    relative = RAW + name
    body = (project / relative).read_bytes()
    receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
    if receipt["status"] != "acquired" or receipt["sha256"] != hashlib.sha256(body).hexdigest():
        raise ValueError(f"Housing original/receipt mismatch: {name}")
    return json.loads(body), receipt


def source_rows(payload, scope):
    dates = [x[0] for x in payload["headers"]["column_headers"]]
    if not dates or dates[0] != DATE:
        raise ValueError(f"Housing 2020 date missing/changed: {scope}")
    headers = payload["headers"]["row_headers"]
    values = payload["data"]
    if len(headers) != len(values):
        raise ValueError(f"Housing header/value length mismatch: {scope}")
    expected_width = {"national": 0, "governorate": 1, "wilayat": 2}[scope]
    result = {}
    for row_number, (labels, cells) in enumerate(zip(headers, values), 1):
        if len(labels) != expected_width:
            raise ValueError(f"Unexpected housing row labels: {scope}/{row_number}")
        key = tuple(labels)
        if key in result:
            raise ValueError(f"Duplicate housing area: {scope}/{key}")
        value = cells[0][0]
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            raise ValueError(f"Invalid housing count: {scope}/{key}={value}")
        result[key] = {"value": value, "source_row": row_number}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "OMN" or any(x["id"] == INDICATOR_ID for x in dataset["indicators"]):
        raise ValueError("Expected Oman candidate without this housing indicator")
    inventory = json.loads((project / "evidence/OMN_ECENSUS_PRODUCT_INVENTORY.json").read_text(encoding="utf-8"))
    tables = {x["table"]: x for x in inventory["products"]}
    meta, _ = verified(project, "ecensus-metadata-v_public_ds_housing_unit_en.json")
    if len(tables) != 13 or meta["table_name"] != "v_public_ds_housing_unit_en" or \
            {"HOUSING_UNIT_USE_TYPE", "HOUSING_UNIT_TYPE", "HOUSING_UNIT_OCCUPANCY",
             "LOCATION_GOVERNORATE", "LOCATION_WILAYAT", "RUN_DATE"} - \
            {x["field"] for x in meta["columns"]} or \
            {x["field"] for x in meta["measures"]} != {"AMOUNT"}:
        raise ValueError("Housing source metadata changed")
    payloads = {}
    receipts = {}
    for scope in ("national", "governorate", "wilayat"):
        payloads[scope], receipts[scope] = verified(project, f"ecensus-housing-unit-{scope}-pivot.json")
    rows = {scope: source_rows(payloads[scope], scope) for scope in payloads}
    if set(rows["national"]) != {()} or len(rows["governorate"]) != 11 or len(rows["wilayat"]) != 63:
        raise ValueError("Housing geography coverage changed")
    null_wilayats = {key for key, row in rows["wilayat"].items() if row["value"] is None}
    if null_wilayats != {("Ad Dakhliyah", "ALJABAL ALAKDAR"), ("Ash Sharqiyah North", "SINAW")}:
        raise ValueError(f"Housing null-area geography changed: {null_wilayats}")
    observed = {key: row for key, row in rows["wilayat"].items() if row["value"] is not None}
    if len(observed) != 61 or set(rows["governorate"]) != {key[:1] for key in observed}:
        raise ValueError("Housing 2020 wilayat coverage changed")
    national = rows["national"][()]["value"]
    if national != 1_312_327 or payloads["national"]["totals"]["column_totals"][0][0] != national or \
            sum(x["value"] for x in rows["governorate"].values()) != national or \
            sum(x["value"] for x in observed.values()) != national:
        raise ValueError("Housing national/governorate/wilayat source controls differ")
    for (gov,), group in rows["governorate"].items():
        if sum(x["value"] for key, x in observed.items() if key[0] == gov) != group["value"]:
            raise ValueError(f"Housing wilayat sum differs from source governorate: {gov}")
    gov_ids = {x["name"]: x["id"] for x in dataset["territories"]
               if x.get("type") == "2020 eCensus governorate reporting area"}
    wil_ids = {(next(y["name"] for y in dataset["territories"] if y["id"] == x["parent_id"]), x["name"]): x["id"]
               for x in dataset["territories"] if x.get("type") == "2020 eCensus wilayat reporting area"}
    if len(gov_ids) != 11 or len(wil_ids) != 61 or set(gov_ids) != {key[0] for key in rows["governorate"]} or \
            set(wil_ids) != set(observed):
        raise ValueError("Housing area labels do not join exactly to the 2020 population reporting units")
    dataset["sources"].append({"id": SOURCE_ID, "name": "NCSI eCensus 2020 Housing Units Dataset",
        "url": "https://www.ecensus.gov.om/web/#/en/datasets", "publisher": "National Centre for Statistics and Information (Oman)",
        "reference_period": "12 December 2020 snapshot only", "geographic_level": "Oman, 11 source governorates and 61 wilayats with 2020 housing-unit counts",
        "status": "ready", "retrieved_at": receipts["wilayat"]["retrieved_at"],
        "raw_path": RAW + "ecensus-housing-unit-wilayat-pivot.json", "sha256": receipts["wilayat"]["sha256"],
        "license": "official_open_data_terms_review_required",
        "note": "Official API AMOUNT summed over all use, type and occupancy categories. National, governorate and wilayat pivots are separately receipted and agree. This is a count of housing units, not households, occupied units or adequate housing. Only 2020-12-12 cells are adopted; no 2020 polygon is asserted."})
    dataset["indicators"].append({"id": INDICATOR_ID, "name": "Housing units (eCensus 2020)",
        "theme": "Housing", "unit": "housing units", "source_id": SOURCE_ID,
        "definition": "Housing-unit count in the official eCensus Housing Units Dataset at 12 December 2020, summed over all source use, type and occupancy categories. Not a household count, occupied-unit count, housing quality or service-access rate. No dated 2020 legal boundary/polygon equivalence is asserted.",
        "population": "All housing units in the source table, regardless of use/type/occupancy",
        "aggregation": "none", "measurement_method": METHOD, "series_family": "census",
        "display_role": "primary", "period_policy": "latest_available_per_indicator", "display_decimals": 0})
    mapped = [("OMN", rows["national"][()], "national")]
    mapped += [(gov_ids[key[0]], row, f"governorate:{key[0]}") for key, row in rows["governorate"].items()]
    mapped += [(wil_ids[key], row, f"wilayat:{'/'.join(key)}") for key, row in observed.items()]
    for area_id, row, locator in mapped:
        dataset["observations"].append({"territory_id": area_id, "indicator_id": INDICATOR_ID,
            "period": "2020", "value": row["value"], "status": "observed", "source_id": SOURCE_ID,
            "measurement_method": METHOD,
            "source_locator": f"{locator}; RUN_DATE={DATE}; source pivot row {row['source_row']}; AMOUNT sum over all housing-unit categories"})
    if len(mapped) != 73:
        raise ValueError("Housing adoption should contain exactly 73 values")
    for gap in dataset["gaps"]:
        if gap["category"] == "subnational_statistics":
            gap["status"] = "partial"
            gap["detail"] = ("NCSI 12-Dec-2020 eCensus nationality counts remain adopted for nation, 11 governorates and 61 wilayats: 219 records in three indicators. "
                             "A separately receipted housing-unit pivot now contributes 73 counts at the same date and reporting units. "
                             "The other 11 public products have metadata only; housing use/type/occupancy breakdowns, other demographic fields and later dates are not adopted.")
            gap["next_action"] = ("Audit values, definitions and geographic coverage for the other 11 products and housing subgroups; "
                                  "assess 2021/2023-26 snapshots separately and retain the 2020 legal boundary/code gap.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["oman-ecensus-2020-housing-units-partial"]))
    dataset["country"]["geography_note"] += (" The 12-Dec-2020 housing-unit pivot reports an independent 73-area unit-count series "
                                              "on the same eCensus reporting IDs; it is not a household or occupancy measure.")
    dataset["generated_at"] = datetime.now(timezone.utc).isoformat()
    audit = {"status": "partial_candidate_not_accepted", "source": SOURCE_ID,
             "indicator": INDICATOR_ID, "source_national_housing_units": national,
             "governorate_rows": 11, "wilayat_observed_rows": 61,
             "wilayat_2020_null_rows": sorted("/".join(x) for x in null_wilayats),
             "observations_added": len(mapped),
             "source_receipts": {scope: item["sha256"] for scope, item in receipts.items()},
             "unresolved": ["Other eCensus products and housing breakdowns not value-audited",
                            "2020 legal code/polygon edition", "Local planning and financial originals",
                            "Full 42-scenario and independent acceptance"]}
    tables["v_public_ds_housing_unit_en"]["decision"] = "2020_total_housing_units_73_observations_adopted"
    (project / "evidence/OMN_ECENSUS_PRODUCT_INVENTORY.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (project / "evidence/OMN_ECENSUS_2020_HOUSING_IMPORT_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"indicator": INDICATOR_ID, "observations_added": len(mapped), "national": national}))


if __name__ == "__main__":
    main()

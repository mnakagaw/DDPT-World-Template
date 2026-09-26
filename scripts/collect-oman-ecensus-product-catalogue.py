"""Acquire the complete public eCensus product catalogue and 2020 housing-unit pivots.

This collector does not make an acceptance or boundary-equivalence decision.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE = "https://www.ecensus.gov.om/dregndrop-api/v1/datasets"
RAW = "raw/oman-ecensus-moi/"


def acquire(session, project, name, url, body=None):
    response = session.get(url, timeout=90) if body is None else session.post(url, json=body, timeout=90)
    response.raise_for_status()
    content = response.content
    if not content:
        raise ValueError(f"Empty official response: {name}")
    payload = json.loads(content)
    path = project / (RAW + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    receipt = {
        "status": "acquired", "source_url": url, "final_url": response.url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
        "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
        "raw_path": RAW + name, "redistribution_terms": "review_required",
        "method": "POST" if body is not None else "GET",
    }
    if body is not None:
        receipt["request_body"] = body
    (project / (RAW + name + ".receipt.json")).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload, receipt


def pivot_body(rows):
    return {"table": "v_public_ds_housing_unit_en", "layout": {
        "rows": rows, "columns": ["RUN_DATE"],
        "measures": [{"field": "AMOUNT", "type": "sum", "name": "Amount"}]}, "filters": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData source-audit/1.0", "Accept": "application/json, */*"})
    catalogue, cat_receipt = acquire(session, project, "ecensus-product-catalogue.json", BASE + "/categories")
    if not isinstance(catalogue, list) or {x["id"] for x in catalogue} != {"population", "housing", "enterprises"}:
        raise ValueError("Unexpected eCensus catalogue category structure")
    products = [item for category in catalogue for item in category["dashboards"]]
    if len(products) != 13 or len({item["id"]["en"] for item in products}) != 13:
        raise ValueError("Unexpected eCensus product inventory")
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    population_ids = {"OMN_ECENSUS_2020_TOTAL", "OMN_ECENSUS_2020_OMANI", "OMN_ECENSUS_2020_EXPAT"}
    population_rows = [x for x in dataset["observations"] if x["indicator_id"] in population_ids]
    if dataset["country"]["id"] != "OMN" or len(population_rows) != 219:
        raise ValueError("Run on the Oman candidate with 219 adopted 2020 population rows")
    records = []
    for category in catalogue:
        for product in category["dashboards"]:
            table = product["id"]["en"]
            metadata, receipt = acquire(session, project, f"ecensus-metadata-{table}.json",
                                        BASE + f"/table-metadata?table={table}&lang=en")
            if metadata.get("table_name") != table or not metadata.get("measures"):
                raise ValueError(f"Unexpected product metadata: {table}")
            records.append({"category": category["id"], "table": table,
                            "name": product["name"]["en"],
                            "fields": [x["field"] for x in metadata["columns"]],
                            "measures": [x["field"] for x in metadata["measures"]],
                            "metadata_sha256": receipt["sha256"],
                            "decision": "2020_population_219_observations_already_adopted" if table == "v_public_ds_population_en"
                                        else "housing_2020_pivots_acquired_not_yet_adopted" if table == "v_public_ds_housing_unit_en"
                                        else "metadata_only_values_not_adopted"})
    housing = "v_public_ds_housing_unit_en"
    for scope, rows in (("national", []), ("governorate", ["LOCATION_GOVERNORATE"]),
                        ("wilayat", ["LOCATION_GOVERNORATE", "LOCATION_WILAYAT"])):
        body = pivot_body(rows)
        payload, _ = acquire(session, project, f"ecensus-housing-unit-{scope}-pivot.json",
                             BASE + "/pivot-query?lang=en", body)
        if not payload.get("headers") or not payload.get("data"):
            raise ValueError(f"Unexpected housing pivot response: {scope}")
    report = {"status": "full_public_product_metadata_inventory_housing_pivots_acquired",
              "catalogue_sha256": cat_receipt["sha256"], "product_count": len(records),
              "products": records, "limits": ["No non-housing product values audited or adopted here",
                 "Housing occupancy and use-type breakdowns not yet adopted",
                 "No 2020 official polygon/code equivalence established"]}
    (project / "evidence/OMN_ECENSUS_PRODUCT_INVENTORY.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"products": len(records), "categories": len(catalogue), "housing_pivots": 3}))


if __name__ == "__main__":
    main()

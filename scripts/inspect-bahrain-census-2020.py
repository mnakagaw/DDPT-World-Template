"""Verify Bahrain Census 2020 receipts and inventory every acquired value field."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    inventory = json.loads((project / "evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json").read_text(encoding="utf-8"))
    if inventory["census_2020_title_count"] != 45 or len(inventory["tables"]) != 45:
        raise ValueError("Incomplete Bahrain census inventory")
    register = []
    totals = Counter()
    for table in inventory["tables"]:
        records = []
        for page in table["pages"]:
            original = project / page["raw_path"]
            data = original.read_bytes()
            receipt = json.loads((project / (page["raw_path"] + ".receipt.json")).read_text(encoding="utf-8"))
            digest = hashlib.sha256(data).hexdigest()
            if receipt["status"] != "acquired" or receipt["sha256"] != digest or page["sha256"] != digest:
                raise ValueError(f"Bahrain original/receipt mismatch: {page['raw_path']}")
            payload = json.loads(data)
            if payload["total_count"] != table["record_count"] or len(payload["results"]) != page["row_count"]:
                raise ValueError(f"Bahrain row count changed: {page['raw_path']}")
            records.extend(payload["results"])
        if len(records) != table["record_count"]:
            raise ValueError(f"Incomplete Bahrain table: {table['dataset_id']}")
        dimensions = [field["name"] for field in table["fields"] if field["name"] not in table["numeric_fields"]]
        cardinality = {name: len({str(record.get(name)) for record in records}) for name in dimensions}
        for field in table["numeric_fields"]:
            numbers = [record.get(field) for record in records]
            numeric = [value for value in numbers if isinstance(value, (int, float)) and not isinstance(value, bool)]
            if len(numeric) + numbers.count(None) != len(numbers):
                raise ValueError(f"Non-numeric value in {table['dataset_id']}/{field}")
            register.append({"dataset_id": table["dataset_id"], "title": table["title"],
                "value_field": field, "source_rows": len(records), "numeric_cells": len(numeric),
                "null_cells": len(records) - len(numeric),
                "min": min(numeric) if numeric else "", "max": max(numeric) if numeric else "",
                "dimensions": "; ".join(f"{key}={count}" for key, count in cardinality.items()),
                "has_governorate": "governorate" in dimensions,
                "decision": "priority_unassessed", "reason": "Source field and category definitions not yet audited for adoption"})
            totals["numeric_cells"] += len(numeric)
            totals["null_cells"] += len(records) - len(numeric)
        totals["source_rows"] += len(records)
        totals["governorate_tables"] += int("governorate" in dimensions)
    output = project / "evidence/BHR_CENSUS_2020_FIELD_REGISTER.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(register[0]))
        writer.writeheader()
        writer.writerows(register)
    print(json.dumps({"tables": len(inventory["tables"]), "numeric_fields": len(register), **totals}))


if __name__ == "__main__":
    main()

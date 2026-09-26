"""Compare independent official Bahrain Census 2020 acquisitions and adopted cells."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def load(project):
    project = project.resolve(strict=True)
    inventory = json.loads((project / "evidence/BHR_CENSUS_2020_PORTAL_INVENTORY.json").read_text(encoding="utf-8"))
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if len(inventory["tables"]) != 45 or dataset["country"]["id"] != "BHR":
        raise ValueError("Invalid Bahrain acquisition")
    tables = {}
    for table in inventory["tables"]:
        records = []
        for page in table["pages"]:
            body = (project / page["raw_path"]).read_bytes()
            receipt = json.loads((project / (page["raw_path"] + ".receipt.json")).read_text(encoding="utf-8"))
            if hashlib.sha256(body).hexdigest() != page["sha256"] or page["sha256"] != receipt["sha256"]:
                raise ValueError(f"Receipt mismatch: {page['raw_path']}")
            records.extend(json.loads(body)["results"])
        if len(records) != table["record_count"]:
            raise ValueError(f"Incomplete table: {table['dataset_id']}")
        canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        tables[table["dataset_id"]] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    tuples = sorted((row["territory_id"], row["indicator_id"], row["period"], row["value"])
                    for row in dataset["observations"] if row["indicator_id"].startswith("BHR_CENSUS2020_"))
    return inventory, dataset, tables, tuples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    first_i, first_d, first_tables, first_tuples = load(args.first)
    second_i, second_d, second_tables, second_tuples = load(args.second)
    if first_tables != second_tables or first_tuples != second_tuples or len(first_tuples) != 40:
        raise ValueError("Independent Bahrain source table bodies or adopted tuples changed")
    report = {"status": "replay_substantive_match", "checked_at": datetime.now(timezone.utc).isoformat(),
              "first": str(args.first), "second": str(args.second),
              "catalogue_hit_counts": [first_i["catalogue_results"], second_i["catalogue_results"]],
              "matched_table_bodies": len(first_tables), "matched_domestic_tuples": len(first_tuples),
              "second_dataset_sha256": hashlib.sha256((args.second / "data/dashboard.json").read_bytes()).hexdigest(),
              "first_dataset_sha256": hashlib.sha256((args.first / "data/dashboard.json").read_bytes()).hexdigest(),
              "note": "Raw response receipts are each checked against their own bytes. WDI and retrieval timestamps are not required to be byte-identical. The first candidate predates the provenance correction; compare its numeric tuples, not its classification."}
    output = args.second / "evidence/BHR_REPLAY_COMPARISON.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "matched_table_bodies", "matched_domestic_tuples")}))


if __name__ == "__main__":
    main()

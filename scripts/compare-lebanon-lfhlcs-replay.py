"""Compare adopted LFHLCS evidence in two independently generated candidates."""

import argparse
import json
from pathlib import Path


def load(project):
    data = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    source_ids = {"lbn-cas-lfhlcs-2018-19-hl5", "lbn-cas-lfhlcs-2018-19-full-report",
                  "lbn-moph-adm1-map", "lbn-moph-adm2-map"}
    hashes = {item["id"]: item["sha256"] for item in data["sources"] if item["id"] in source_ids}
    tuples = sorted((item["territory_id"], item["indicator_id"], item["period"],
                     item["value"], item["status"], item["source_id"],
                     item.get("boundary_version")) for item in data["observations"]
                    if item["indicator_id"].startswith("LBN_CAS_LFHLCS_2018_"))
    inventory = json.loads((project / "evidence/LBN_LFHLCS_DEMOGRAPHY_STRUCTURE.json").read_text(encoding="utf-8"))
    columns = (project / "evidence/LBN_LFHLCS_DEMOGRAPHY_COLUMNS.csv").read_bytes()
    return hashes, tuples, inventory, columns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    first, second = load(args.first.resolve(strict=True)), load(args.second.resolve(strict=True))
    labels = ("four pinned originals", "105 adopted observation tuples", "sheet structure", "column inventory")
    for label, left, right in zip(labels, first, second):
        if left != right:
            raise ValueError(f"Replay differs: {label}")
    if len(first[1]) != 105 or len(first[0]) != 4:
        raise ValueError("Replay adoption/hash scope changed")
    print(json.dumps({"matched": list(labels), "domestic_observations": len(first[1]),
                      "originals": first[0]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

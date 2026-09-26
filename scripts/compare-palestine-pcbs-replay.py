"""Compare independently bootstrapped Palestine candidates against pinned originals."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_HASHES = {
    "raw/palestine-pcbs-2017/pcbs-2017-final-summary.pdf": "25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f",
    "raw/palestine-pcbs-2017/pcbs-2017-detailed-population.pdf": "0ab9b57187f3924a128069a685a83295a23d80ab7d706dc8e690b8df2e9d0520",
    "raw/palestine-pcbs-2017/pcbs-2017-governorate-area.html": "33eebd91cecdeffecc42076406e22fe5b232f852037ce1ff5f8ab0a04c2fc233",
    "raw/palestine-molg-planning/molg-local-development-planning-guide.pdf": "27fbc38788da1bd1d0554fffbdf68ee831cbf415c1a407d5112d9e7f360bb210",
    "raw/palestine-molg-planning/molg-local-government-sector-strategy-2025-2027.pdf": "ec7d2dbf55526fc5d523b62e804e28570c1aed88240f308a796fa60956b7be54",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(project):
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/PSE_PCBS_2017_IMPORT_AUDIT.json").read_text(encoding="utf-8"))
    for relative, expected in SOURCE_HASHES.items():
        if digest(project / relative) != expected:
            raise ValueError(f"Source original differs in {project}: {relative}")
        receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
        if receipt["sha256"] != expected or receipt["status"] != "acquired":
            raise ValueError(f"Source receipt differs in {project}: {relative}")
    if digest(project / "evidence/PSE_PCBS_2017_TABLE2_ROWS.csv") != \
            "39d66bedf533c076cbd0fe397ac8293b84f4741578844b15d9e7baa9d01e5d07":
        raise ValueError("Table 2 extracted source rows differ")
    if dataset["country"]["id"] != "PSE" or len(dataset["documents"]) != 2 or len(dataset["sources"]) != 21:
        raise ValueError("Candidate country or national document scope differs")
    observations = sorted((row["territory_id"], row["indicator_id"], row["period"], row["value"],
                           row["source_id"], row["source_locator"]) for row in dataset["observations"]
                          if row["indicator_id"].startswith("PSE_PCBS_2017_"))
    areas = sorted((row["id"], json.dumps(row, sort_keys=True, ensure_ascii=False))
                   for row in dataset["territories"])
    docs = sorted((row["id"], row["territory_id"], row["category"], row["period"], row["source_id"],
                   row["availability"], row["official_status"]) for row in dataset["documents"])
    source_leads = sorted((row["id"], row["url"], row["status"], row.get("sha256"))
                          for row in dataset["sources"] if row["id"].startswith("pse-"))
    if len(observations) != 76 or len(areas) != 19 or audit["domestic_observations_added"] != 76:
        raise ValueError("Replayed geographic or indicator scope differs")
    return observations, areas, docs, source_leads, audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    args = parser.parse_args()
    project, replay = args.project.resolve(strict=True), args.replay.resolve(strict=True)
    first, second = load(project), load(replay)
    if first[:4] != second[:4] or first[4]["adopted_tuple_sha256"] != second[4]["adopted_tuple_sha256"]:
        raise ValueError("Independent PSE replay differs from original candidate")
    report = {"status": "independent_bootstrap_and_pinned_original_replay_match",
              "checked_at": datetime.now(timezone.utc).isoformat(),
              "source_hashes": SOURCE_HASHES, "territories": len(first[1]),
              "domestic_observations": len(first[0]), "national_documents": len(first[2]),
              "official_source_records": len(first[3]),
              "adopted_tuple_sha256": first[4]["adopted_tuple_sha256"],
              "limitations": ["Replay checks extraction/serialization, not complete census table semantics",
                              "Local plans, legal boundaries, 42 scenarios and independent acceptance remain open"]}
    (project / "evidence/PSE_REPLAY_COMPARISON.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "territories": report["territories"],
                      "domestic_observations": report["domestic_observations"],
                      "national_documents": report["national_documents"],
                      "adopted_tuple_sha256": report["adopted_tuple_sha256"]}))


if __name__ == "__main__":
    main()

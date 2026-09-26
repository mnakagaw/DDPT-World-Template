"""Compare two independently created Oman partial candidates on source semantics."""

import argparse
import hashlib
import json
from pathlib import Path


def load(project, relative):
    return json.loads((project / relative).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(project):
    import_audit = load(project, "evidence/OMN_ECENSUS_2020_IMPORT_AUDIT.json")
    structure = load(project, "evidence/OMN_ECENSUS_MOI_STRUCTURE.json")
    map_audit = load(project, "evidence/OMN_NCSI_WILAYAT_REGISTER_AUDIT.json")
    plan = load(project, "evidence/OMN_NATIONAL_PLAN_AUDIT.json")
    dataset = load(project, "data/dashboard.json")
    source_ids = {item["id"] for item in dataset["sources"]}
    if dataset["country"]["id"] != "OMN" or len(dataset["documents"]) != 1 or \
            dataset["documents"][0]["territory_id"] != "OMN" or \
            "omn-ncsi-wilayat-feature-register" not in source_ids:
        raise ValueError("Replay is not the registered Oman candidate")
    document = dataset["documents"][0]
    crosswalk = project / "evidence/OMN_ECENSUS_MOI_WILAYAT_CROSSWALK.csv"
    inventory = project / "evidence/OMN_MOI_COLUMN_INVENTORY.csv"
    return {
        "adopted_tuple_sha256": import_audit["adopted_tuple_sha256"],
        "moi_sha256": import_audit["moi_sha256"],
        "plan_sha256": plan["pdf_sha256"],
        "moi_inventory_sha256": sha(inventory),
        "ecensus_moi_crosswalk_sha256": sha(crosswalk),
        "ecensus_reference_dates": structure["ecensus_reference_dates"],
        "ecensus_en_metadata_fields": structure["ecensus_en_metadata_fields"],
        "ecensus_ar_metadata_fields": structure["ecensus_ar_metadata_fields"],
        "moi_columns": structure["moi_columns"],
        "map_name_join": [(row["name_key"], row["moi_wilayat_id"], row["ncsi_wilaya_id"],
                           row["ncsi_nsdifid"], row["ncsi_feature_load_date"])
                          for row in map_audit["matched_records"]],
        "map_load_dates": map_audit["feature_load_dates"],
        "territories": [(item["id"], item["parent_id"], item["provider_code"],
                         item["boundary_version"]) for item in dataset["territories"] if item["id"] != "OMN"],
        "document": {**{key: document[key] for key in ("id", "territory_id", "period", "availability",
                                                        "official_status", "source_id")},
                     "summary": document["content"]["summary"],
                     "priorities": document["content"]["priorities"],
                     "content_evidence_source": document["content"]["evidence"]["source_id"],
                     "content_evidence_locator": document["content"]["evidence"]["locator"],
                     "approval_evidence_source": document["official_evidence"]["source_id"],
                     "approval_evidence_locator": document["official_evidence"]["locator"]},
        "domestic_observations": import_audit["domestic_observations_added"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    first = signature(args.first.resolve(strict=True))
    second = signature(args.second.resolve(strict=True))
    differences = [key for key in first if first[key] != second[key]]
    if differences:
        raise ValueError("Oman replay differs: " + ", ".join(differences))
    print(json.dumps({"status": "replay_semantics_match", "adopted_tuple_sha256": first["adopted_tuple_sha256"],
                      "moi_sha256": first["moi_sha256"], "plan_sha256": first["plan_sha256"],
                      "territories": len(first["territories"]) + 1,
                      "domestic_observations": first["domestic_observations"],
                      "map_name_matches": len(first["map_name_join"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

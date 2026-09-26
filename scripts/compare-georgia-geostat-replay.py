"""Compare two independent Georgia bootstraps after the pinned domestic adapter runs."""

import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(project):
    dataset = read(project / "data/dashboard.json")
    if dataset["country"]["id"] != "GEO":
        raise ValueError(f"Not a Georgia candidate: {project}")
    territories = sorted((r["id"], r["name"], r["parent_id"], r["type"], r["official_code"], r["boundary_version"])
                         for r in dataset["territories"])
    observations = sorted((r["territory_id"], r["indicator_id"], r["period"], r["status"], r["value"])
                          for r in dataset["observations"] if r["indicator_id"].startswith("GEO_GEOSTAT_2024_"))
    documents = sorted((r["id"], r["territory_id"], r["category"], r["period"], r["availability"], r["official_status"])
                       for r in dataset["documents"])
    sources = sorted((r["id"], r.get("sha256")) for r in dataset["sources"] if r["id"].startswith("geo-"))
    audit = read(project / "evidence/GEO_GEOSTAT_2024_IMPORT_AUDIT.json")
    return {"territories": territories, "observations": observations, "documents": documents,
            "sources": sources, "adopted_tuple_sha256": audit["adopted_tuple_sha256"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    args = parser.parse_args()
    first, second = args.project.resolve(strict=True), args.replay.resolve(strict=True)
    a, b = snapshot(first), snapshot(second)
    if a != b:
        for key in a:
            if a[key] != b[key]:
                raise ValueError(f"Independent replay differs in {key}")
    result = {"status": "matched", "projects": [str(first), str(second)],
              "territories": len(a["territories"]), "domestic_observations": len(a["observations"]),
              "documents": len(a["documents"]), "source_records": len(a["sources"]),
              "adopted_tuple_sha256": a["adopted_tuple_sha256"],
              "snapshot_sha256": hashlib.sha256(json.dumps(a, ensure_ascii=False).encode("utf-8")).hexdigest()}
    (first / "evidence/GEO_GEOSTAT_2024_REPLAY.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

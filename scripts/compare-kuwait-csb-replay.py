"""Compare adopted Kuwait domestic census data across independent bootstraps."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def snapshot(project):
    data = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if data["country"]["id"] != "KWT":
        raise ValueError("Expected Kuwait project")
    observations = sorted((item["territory_id"], item["indicator_id"], item["period"], item["value"],
                           item["source_id"], item["source_locator"])
                          for item in data["observations"] if item["indicator_id"].startswith("KWT_CSB_2021_"))
    areas = sorted((item["id"], item["parent_id"], item["name"], item.get("official_code"),
                    item.get("boundary_version")) for item in data["territories"])
    sources = sorted((item["id"], item["url"], item.get("sha256"), item["status"])
                     for item in data["sources"] if item["id"].startswith("kwt-"))
    if len(observations) != 63 or len(areas) != 7 or len(sources) != 9 or data["documents"] or \
            data["boundaries"]["features"]:
        raise ValueError("Unexpected Kuwait candidate scope")
    return {"observations": observations, "territories": areas, "official_sources": sources}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    args = parser.parse_args()
    first = args.project.resolve(strict=True)
    second = args.replay.resolve(strict=True)
    if first == second:
        raise ValueError("Replay must be an independent project directory")
    a, b = snapshot(first), snapshot(second)
    if a != b:
        raise ValueError("Kuwait original candidate and independent replay differ")
    result = {"status": "producer_replay_match_partial_candidate", "checked_at": datetime.now(timezone.utc).isoformat(),
              "first_project": str(first), "replay_project": str(second),
              "territories": len(a["territories"]), "domestic_observations": len(a["observations"]),
              "official_sources": len(a["official_sources"]),
              "observations_sha256": digest(a["observations"]), "territories_sha256": digest(a["territories"]),
              "source_records_sha256": digest(a["official_sources"]),
              "meaning": "Reproducible producer import only; no independent ACCEPT or public release."}
    (first / "evidence/KWT_CSB_2021_REPLAY.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "territories", "domestic_observations", "official_sources", "observations_sha256")}))


if __name__ == "__main__":
    main()

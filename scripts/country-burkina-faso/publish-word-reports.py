"""Build a DOCX for every BFA census area and expose them in the local static site.

Run after build-country.mjs. A later site rebuild requires rerunning this script.
"""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import sys


parser = ArgumentParser()
parser.add_argument("--project", required=True)
args = parser.parse_args()
project = Path(args.project).resolve()
dataset_path = project / "data/dashboard.json"
site_dataset_path = project / "site/data/dashboard.json"
dataset_bytes = dataset_path.read_bytes()
dataset = json.loads(dataset_bytes)
site_dataset = json.loads(site_dataset_path.read_text(encoding="utf-8"))
assert dataset["country"]["id"] == "BFA"
assert [x["id"] for x in dataset["territories"]] == [x["id"] for x in site_dataset["territories"]]

script = Path(__file__).with_name("build-diagnostic-word.py")
output_dir = project / "site/exports/diagnostic"
output_dir.mkdir(parents=True, exist_ok=True)
manifest = {"dataset_sha256": sha256(dataset_bytes).hexdigest(), "files": []}
for index, area in enumerate(dataset["territories"]):
    filename = f"area-{index:04d}.docx"
    target = output_dir / filename
    result = subprocess.run(
        [sys.executable, str(script), "--project", str(project),
         "--territory", area["id"], "--out", str(target)],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode:
        raise RuntimeError(f"Word generation stopped at index {index}, {area['id']}: {result.stderr}")
    report = json.loads(result.stdout)
    manifest["files"].append({"index": index, "territory_id": area["id"],
                              "name": area["name"], "path": f"exports/diagnostic/{filename}",
                              "sha256": report["sha256"],
                              "observed_values_in_table": report["observed_values_in_table"],
                              "pyramid": report["pyramid"]})
    if (index + 1) % 50 == 0:
        print(f"Built {index + 1}/{len(dataset['territories'])} Word reports", flush=True)

manifest_path = project / "evidence/WORD_REPORT_MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
public_manifest = project / "site/exports/diagnostic/manifest.json"
public_manifest.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(f"Built {len(manifest['files'])} Word reports and {manifest_path}")

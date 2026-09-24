"""Write source and indicator inventories for the local Burkina Faso project.

Run from a copy under PROJECT/scripts after all data adapters. The inventory
deliberately records unreviewed tables as pending, never as absent or unusable.
"""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw/insd-rgph-2019"
EVIDENCE = ROOT / "evidence"
DATA = json.loads((ROOT / "data/dashboard.json").read_text(encoding="utf-8"))
RECEIPTS = json.loads((RAW / "receipts.json").read_text(encoding="utf-8"))
TABLE_TEXT = (RAW / "statistical_tables.txt").read_text(encoding="utf-8")
EVIDENCE.mkdir(exist_ok=True)


def dump(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


table_headings = re.findall(
    r"(?mi)^\s*Tableau\s+([IVX]+\.\d+[A-Za-z]?)\s*[:.]?\s+([^\n]+)",
    TABLE_TEXT,
)
tables = {}
for identifier, title in table_headings:
    tables.setdefault(identifier.upper(), title.strip())
assert len(tables) == 581, len(tables)
adopted_tables = {"I.20", "III.9", "VII.11", "VII.50", "VII.55", "VII.65", "VIII.7", "IX.1"}
assert adopted_tables <= tables.keys()
with (EVIDENCE / "SOURCE_TABLE_INVENTORY.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["source_id", "table_id", "heading_first_line", "adoption_status", "next_action"])
    for identifier, title in tables.items():
        adopted = identifier in adopted_tables
        writer.writerow([
            "bfa-insd-rgph2019-statistical-tables", identifier, title,
            "adopted_selected_columns" if adopted else "not_yet_numeric_column_reviewed",
            "check adopted column, definition and printed page" if adopted else
            "inspect full table, geography, denominators and numeric columns before adoption",
        ])

dataset_sources = {source["id"]: source for source in DATA["sources"]}
adopted_resources = {
    "localities.pdf": "bfa-insd-rgph2019-localities",
    "statistical_tables.pdf": "bfa-insd-rgph2019-statistical-tables",
    "communal_disparities.pdf": "bfa-insd-communal-contraceptive-model-2023",
    "poverty_map.pdf": "bfa-insd-poverty-atlas-2019",
}
resources = []
for receipt in RECEIPTS:
    name = receipt["name"]
    artifact = RAW / name
    assert artifact.is_file() and artifact.read_bytes().startswith(b"%PDF-")
    actual = sha256(artifact.read_bytes()).hexdigest()
    assert actual == receipt["sha256"], name
    source_id = adopted_resources.get(name)
    if source_id:
        assert source_id in dataset_sources
    resources.append({
        "name": name, "url": receipt["url"], "sha256": actual,
        "bytes": artifact.stat().st_size, "acquisition_status": "acquired_pdf_hash_verified",
        "adoption_status": "selected_tables_adopted" if source_id else "not_yet_full_content_inventoried",
        "dataset_source_id": source_id,
        "raw_redistribution": "not_authorized_by_this_inventory",
    })
dump("SOURCE_RESOURCE_INVENTORY.json", {
    "resource_count": len(resources), "statistical_table_identifiers": len(tables),
    "adopted_statistical_table_identifiers": len(adopted_tables),
    "caution": "Acquisition and heading inventory do not mean that every numeric table or column was reviewed or adopted.",
    "resources": resources,
})

areas = {area["id"]: area for area in DATA["territories"]}
observed = defaultdict(list)
for observation in DATA["observations"]:
    if observation["status"] == "observed":
        observed[observation["indicator_id"]].append(observation)
with (EVIDENCE / "INDICATOR_INVENTORY.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["indicator_id", "title", "theme", "unit", "source_id", "periods", "national", "adm1", "adm2", "adm3", "observation_count"])
    for indicator in DATA["indicators"]:
        rows = observed[indicator["id"]]
        levels = Counter(areas[row["territory_id"]]["level"] for row in rows)
        writer.writerow([
            indicator["id"], indicator["name"], indicator["theme"], indicator["unit"], indicator["source_id"],
            "; ".join(sorted({row["period"] for row in rows})),
            *(levels.get(level, 0) for level in ("national", "adm1", "adm2", "adm3")),
            len(rows),
        ])

theme_level = defaultdict(lambda: Counter())
for indicator in DATA["indicators"]:
    for row in observed[indicator["id"]]:
        theme_level[indicator["theme"]][areas[row["territory_id"]]["level"]] += 1
dump("THEME_COVERAGE.json", {
    "territories_by_level": dict(Counter(area["level"] for area in DATA["territories"])),
    "indicator_count": len(DATA["indicators"]),
    "observations": len(DATA["observations"]),
    "observed_by_theme_and_level": {theme: dict(levels) for theme, levels in sorted(theme_level.items())},
    "interpretation": "Counts are observed indicator-area-period records, not a claim that every item is available at every level.",
})
print(f"Inventoried {len(resources)} acquired PDFs and {len(tables)} table IDs; {len(adopted_tables)} selected statistical tables adopted")

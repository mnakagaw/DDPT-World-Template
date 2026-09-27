"""Check six built Brunei cases against independently transcribed PDF cells.

Expected numbers come from DEPS Annex B1/B2, A1/C1 and A2 printed pages
80, 81, 109–113 and 153–156, not from the importer or output JSON.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/brunei-bpp2021-source-manifest.json"
PREFIX = "BRN_BPP2021_"
DIRECT = ("POP_TOTAL", "POP_MALE", "POP_FEMALE", "HOUSEHOLDS",
          "OCCUPIED_QUARTERS", "BRUNEI_CITIZENS", "PERMANENT_RESIDENTS",
          "TEMPORARY_RESIDENTS")
AGES = ("AGE_0_14", "AGE_15_64", "AGE_65_PLUS")
# The first five are Annex B 2021, the last three Annex A1/C1 2021.
CASES = {
    "Brunei": ("BRN", (440715, 232194, 208521, 87137, 83810, 333669, 25834, 81212), (90376, 322445, 27894), None),
    "BruneiMuara": ("BRN:DEPS:BPP2021:DISTRICT:BRUNEI-MUARA", (318530, 167650, 150880, 61776, 59472, 241255, 13715, 63560), (65520, 234726, 18284), "Brunei Muara District Plan"),
    "Belait": ("BRN:DEPS:BPP2021:DISTRICT:BELAIT", (65531, 34914, 30617, 14011, 13389, 43343, 9802, 12386), (12762, 47558, 5211), "Belait District Plan"),
    "Temburong": ("BRN:DEPS:BPP2021:DISTRICT:TEMBURONG", (9444, 5031, 4413, 2056, 1892, 7723, 907, 814), (1966, 6674, 804), "Temburong District Plan"),
    "Kianggeh": ("BRN:DEPS:BPP2021:MUKIM:BRUNEI-MUARA:KIANGGEH", (8102, 4164, 3938, 2251, 2174, 3229, 628, 4245), None, "Brunei Muara District Plan"),
    "Melilas": ("BRN:DEPS:BPP2021:MUKIM:BELAIT:MELILAS", (29, 15, 14, 9, 9, 24, 5, 0), None, "Belait District Plan"),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    data = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["sources"]:
        body = (project / item["raw_path"]).read_bytes()
        require(len(body) == item["bytes"] and hashlib.sha256(body).hexdigest() == item["sha256"],
                f"Source changed: {item['id']}")
    require(len(data["territories"]) == 44, "Territory roster changed")
    require(len([o for o in data["observations"] if o["indicator_id"].startswith(PREFIX)]) == 367,
            "Adopted observation count changed")
    require(data["boundaries"]["features"] == [], "Unmatched reference geometry reintroduced")
    out = project / "evidence/output-verification"
    checked = 0
    for stem, (tid, direct, ages, expected_plan) in CASES.items():
        overall = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-diagnostic.csv")
                   if r["Record scope"] == "overall"}
        evidence = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-evidence.csv")}
        require(all(row["Territory ID"] == tid for row in overall.values()), f"Wrong diagnostic territory {stem}")
        require(all(row["Territory ID"] == tid for row in evidence.values()), f"Wrong evidence territory {stem}")
        for key, expected in zip(DIRECT, direct):
            indicator = PREFIX + key
            for label, rows in (("diagnostic", overall), ("evidence", evidence)):
                row = rows.get(indicator)
                require(row and row["Status"] == "observed" and row["Value"] == str(expected),
                        f"{stem} {label} {key}: expected {expected}, got {row}")
                checked += 1
        for key, expected in zip(AGES, ages if ages is not None else (None,) * 3):
            indicator = PREFIX + key
            for label, rows in (("diagnostic", overall), ("evidence", evidence)):
                row = rows.get(indicator)
                require(row is not None, f"{stem} {label} missing {key}")
                if expected is None:
                    require(row["Status"] == "not_collected" and row["Value"] == "",
                            f"{stem} {label} should show missing age data {key}")
                else:
                    require(row["Status"] == "calculated" and row["Value"] == str(expected),
                            f"{stem} {label} {key}: expected {expected}")
                    if label == "diagnostic":
                        require(row["Value provenance"] == "calculated" and
                                "Annex A2" in row["Aggregation note"],
                                f"{stem} {key} calculation source is not labelled")
                checked += 1
        if stem != "Brunei":
            for rows in (overall, evidence):
                wdi = rows["SP.POP.TOTL"]
                require(wdi["Status"] == "not_collected" and wdi["Value"] == "",
                        f"National WDI value leaked to {stem}")
        for suffix in ("diagnostic.html", "diagnostic.md", "planning.html"):
            text = (out / f"{stem}-{suffix}").read_text(encoding="utf-8")
            require("undefined" not in text and "BRN_BPP2021_POP_TOTAL" in text,
                    f"Broken {suffix} for {stem}")
            if expected_plan and suffix == "planning.html":
                require(expected_plan in text, f"Missing parent district plan context for {stem}")
                for other in ("Brunei Muara District Plan", "Belait District Plan", "Temburong District Plan", "Tutong District Plan"):
                    if other != expected_plan:
                        require(other not in text, f"Another district plan leaked to {stem}: {other}")
    result = {"cases": len(CASES), "direct_and_age_export_cells_checked": checked,
              "pinned_official_pdfs": len(manifest["sources"]),
              "published_status": "partial_candidate_unpublished"}
    print(json.dumps(result))


if __name__ == "__main__":
    main()

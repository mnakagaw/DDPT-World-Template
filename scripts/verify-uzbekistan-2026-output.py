"""Check built Uzbekistan exports against independently transcribed 2026 sources.

The SIAT numbers below are from the five source CSV Code/2026 cells. Census
numbers are from the rendered preliminary report, printed pp.4–5.
"""

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/uzbekistan-2026-source-manifest.json"
PREFIX = "UZB_2026_"
FIELDS = ("TOTAL", "MALE", "FEMALE", "URBAN", "RURAL")
CASES = {
    "Uzbekistan": ("UZB", (38236.7, 19257.7, 18979.0, 19471.7, 18765.0),
                   (39047321, 19766166, 19281155, 21276729, 17770592)),
    "Karakalpakstan": ("UZB:COATO:1735", (2053.2, 1031.5, 1021.7, 999.6, 1053.6),
                       (2149932, 1088446, 1061486, 1179397, 970535)),
    "NukusCity": ("UZB:COATO:1735401", (349.4, 172.7, 176.7, 349.4, 0.0), None),
    "BozatauDistrict": ("UZB:COATO:1735209", (21.8, 11.1, 10.7, 5.6, 16.2), None),
    "AndijanRegion": ("UZB:COATO:1703", (3521.8, 1784.4, 1737.4, 1838.8, 1683.0),
                      (3531777, 1778354, 1753423, 1843214, 1688563)),
    "AndijanCity": ("UZB:COATO:1703401", (503.5, 253.9, 249.6, 503.5, 0.0), None),
    "TashkentRegion": ("UZB:COATO:1727", (3160.7, 1586.4, 1574.3, 1575.0, 1585.7),
                       (3763093, 1897430, 1865663, 2209439, 1553654)),
    "TashkentCity": ("UZB:COATO:1726", (3178.1, 1561.2, 1616.9, 3178.1, 0.0),
                     (3224838, 1612832, 1612006, 3224838, 0)),
    "YangikhayotDistrict": ("UZB:COATO:1726292", (200.5, 98.1, 102.4, 200.5, 0.0), None),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


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
                f"Pinned source changed: {item['id']}")
    require(len(data["territories"]) == 221 and data["boundaries"]["features"] == [],
            "Territory roster or unverified polygons changed")
    require(len([r for r in data["observations"] if r["indicator_id"].startswith(PREFIX)]) == 1180,
            "Adopted 2026 observation count changed")
    require(not any(o["source_id"] == "uzb-mof-local-budget-2026-table" for o in data["observations"]),
            "Ambiguous budget table was adopted")
    out = project / "evidence/output-verification"
    checked = 0
    for stem, (tid, siat, census) in CASES.items():
        diagnostic = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-diagnostic.csv")
                      if r["Record scope"] == "overall"}
        evidence = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-evidence.csv")}
        for rows in (diagnostic, evidence):
            require(all(r["Territory ID"] == tid for r in rows.values()),
                    f"Other territory leaked into {stem} export")
            for key, expected in zip(FIELDS, siat):
                row = rows[PREFIX + "SIAT_" + key]
                require(row["Status"] == "observed" and Decimal(row["Value"]) == Decimal(str(expected)),
                        f"{stem} SIAT {key}: {row['Value']} != {expected}")
                checked += 1
            for key, expected in zip(FIELDS, census if census is not None else (None,) * 5):
                row = rows[PREFIX + "CENSUS_" + key]
                if expected is None:
                    require(row["Status"] == "not_collected" and row["Value"] == "",
                            f"{stem} must show missing district census {key}")
                else:
                    require(row["Status"] == "observed" and row["Value"] == str(expected),
                            f"{stem} census {key}: {row['Value']} != {expected}")
                checked += 1
        if stem != "Uzbekistan":
            for rows in (diagnostic, evidence):
                row = rows["SP.POP.TOTL"]
                require(row["Status"] == "not_collected" and row["Value"] == "",
                        f"WDI national estimate leaked into {stem}")
        for suffix in ("diagnostic.html", "diagnostic.md", "planning.html"):
            body = (out / f"{stem}-{suffix}").read_text(encoding="utf-8")
            require("undefined" not in body and PREFIX + "SIAT_TOTAL" in body,
                    f"Broken {suffix}: {stem}")
        planning = (out / f"{stem}-planning.html").read_text(encoding="utf-8")
        if stem in ("Karakalpakstan", "AndijanRegion", "TashkentRegion", "TashkentCity"):
            region = next(t["name"] for t in data["territories"] if t["id"] == tid)
            require(region + ": 2030 strategy preparation task" in planning and
                    region + ": MOF 2026 local-budget table location" in planning,
                    f"Selected regional source locations missing: {stem}")
        elif stem != "Uzbekistan":
            require("MOF 2026 local-budget table location" not in planning,
                    f"Parent regional budget location misattributed to {stem}")
    print(json.dumps({"cases":len(CASES), "export_value_or_missing_cells_checked":checked,
                      "pinned_sources":len(manifest["sources"]),
                      "published_status":"partial_candidate_unpublished"}))


if __name__ == "__main__":
    main()

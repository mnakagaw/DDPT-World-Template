"""Check actual Timor-Leste exports against independently read official PDF cells."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
AREAS = (
    "Aileu", "Ainaro", "Atauro", "Baucau", "Bobonaro", "Covalima",
    "Dili", "Ermera", "Lautém", "Liquiça", "Manatuto", "Manufahi",
    "Oecusse", "Viqueque",
)
CASES = {"TLS": "Timor-Leste", "Dili": "Dili", "Atauro": "Atauro",
         "Baucau": "Baucau", "Oecusse": "Oecusse"}
DIRECT_KEYS = (
    "POP_TOTAL", "AREA", "DENSITY", "LIT_AGE5_TOTAL", "LIT_AGE5_LITERATE",
    "LIT_AGE5_ILLITERATE", "SCHOOL_AGE3_29_TOTAL",
    "SCHOOL_AGE3_29_ATTENDING", "SCHOOL_AGE3_29_NOT_ATTENDING",
)
ALL_KEYS = DIRECT_KEYS + ("LIT_AGE5_RATE", "SCHOOL_AGE3_29_ATTEND_RATE")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pdf_text(path, first, last):
    result = subprocess.run(
        ["pdftotext", "-f", str(first), "-l", str(last), "-layout", str(path), "-"],
        check=True, capture_output=True,
    )
    return result.stdout.decode("utf-8")


def source_table(path, first, last, columns):
    """Take only the first summary row for each expected geography."""
    rows = {}
    pattern = re.compile(r"^\s*(" + "|".join(re.escape(n) for n in
                         ("Timor-Leste",) + AREAS) + r")\s+(.+)$")
    for line in pdf_text(path, first, last).splitlines():
        match = pattern.match(line)
        if not match:
            continue
        cells = re.findall(r"(?<!\S)(?:[\d,]+(?:\.\d+)?|-)(?!\S)", match[2])
        if len(cells) == columns:
            require(match[1] not in rows, f"Duplicate source row {match[1]}")
            rows[match[1]] = [float(x.replace(",", "")) for x in cells]
    require(len(rows) == 15 and set(rows) == {"Timor-Leste", *AREAS},
            f"Source row roster incomplete at PDF pages {first}-{last}")
    return rows


def expected_cells(census):
    population = source_table(census, 103, 103, 6)
    literacy = source_table(census, 119, 124, 9)
    school = source_table(census, 125, 131, 9)
    result = {}
    for name in ("Timor-Leste",) + AREAS:
        p, l, s = population[name], literacy[name], school[name]
        require(l[0] == l[1] + l[2] and s[0] == s[1] + s[2],
                f"Original summary count mismatch: {name}")
        result[name] = {
            "POP_TOTAL": p[0], "AREA": p[4], "DENSITY": p[5],
            "LIT_AGE5_TOTAL": l[0], "LIT_AGE5_LITERATE": l[1],
            "LIT_AGE5_ILLITERATE": l[2],
            "LIT_AGE5_RATE": round(100 * l[1] / l[0], 2),
            "SCHOOL_AGE3_29_TOTAL": s[0],
            "SCHOOL_AGE3_29_ATTENDING": s[1],
            "SCHOOL_AGE3_29_NOT_ATTENDING": s[2],
            "SCHOOL_AGE3_29_ATTEND_RATE": round(100 * s[1] / s[0], 2),
        }
    return result


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def compare(row, name, key, value, source_url):
    label = f"{name}/{key}"
    require(row["Period"] == "2022" and row["Status"] == "observed",
            f"Period or status mismatch: {label}")
    require(row["Source URL"] == source_url and
            row["Source ID"] == "tls-inetl-phc2022-main-report",
            f"Source mismatch: {label}")
    table = "4.3" if key in {"POP_TOTAL", "AREA", "DENSITY"} else \
        "4.11" if key.startswith("LIT_") else "4.12"
    require(f"Table {table}, row {name}," in row["Source locator"],
            f"Source locator mismatch: {label}")
    require(abs(float(row["Value"]) - value) < 0.001,
            f"Source/export value mismatch: {label}: {row['Value']} vs {value}")
    require(row["Observation boundary edition"].startswith("INETL Population and Housing Census 2022"),
            f"Boundary edition mismatch: {label}")
    # The export's Value provenance describes its use of an exact area
    # observation. The calculation method carries direct/derived provenance.
    require(row["Value provenance"] == "source_reported", f"Exact observation mismatch: {label}")
    if key.endswith("_RATE"):
        require(row["Method"] == "AreaData ratio of directly reported INETL counts",
                f"Derived rate method mismatch: {label}")
    else:
        require(row["Method"] == "INETL 2022 census directly published table cell",
                f"Direct cell method mismatch: {label}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    manifest = json.loads((ROOT / "config/timor-leste-phc2022-source-manifest.json").read_text(encoding="utf-8"))
    source = next(s for s in manifest["sources"] if s["id"] == "tls-inetl-phc2022-main-report")
    census = project / source["raw_path"]
    require(hashlib.sha256(census.read_bytes()).hexdigest() == source["sha256"],
            "Census original SHA-256 differs")
    expected = expected_cells(census)
    dashboard_bytes = (project / "data/dashboard.json").read_bytes()
    data = json.loads(dashboard_bytes)
    require(data["country"]["id"] == "TLS" and len(data["territories"]) == 15 and
            not data["boundaries"]["features"], "Candidate geography changed")
    report = json.loads((project / "evidence/TLS_PHC2022_AUDIT.json").read_text(encoding="utf-8"))
    require(report["selection"] == {"territories": 15, "indicators": 11,
            "direct_observations": 135, "derived_observations": 30,
            "total_observations": 165}, "Candidate selection changed")
    exported = subprocess.run(
        ["node", str(ROOT / "scripts/export-timor-leste-phc2022-cases.mjs"), str(project)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    export_state = json.loads(exported.stdout)
    require(export_state["comparison"] == {"total": 14, "observed": 14},
            "National internal comparison coverage changed")
    out = project / "evidence/output-verification"
    checks = []
    for stem, name in CASES.items():
        selected_id = export_state["cases"][stem]
        rows = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-diagnostic.csv")
                if r["Record scope"] == "overall"}
        for key in ALL_KEYS:
            row = rows.get("TLS_PHC2022_" + key)
            require(row is not None and row["Territory ID"] == selected_id,
                    f"Selected region/indicator mismatch: {stem}/{key}")
            compare(row, name, key, expected[name][key], source["url"])
        for suffix in ("diagnostic.html", "diagnostic.md", "planning.html", "evidence.csv"):
            body = (out / f"{stem}-{suffix}").read_text(encoding="utf-8")
            require("undefined" not in body and "NaN" not in body and name in body,
                    f"Output content problem: {stem}/{suffix}")
        if stem != "TLS":
            evidence = {r["Indicator ID"]: r for r in csv_rows(out / f"{stem}-evidence.csv")}
            for key in ALL_KEYS:
                require(abs(float(evidence["TLS_PHC2022_" + key]["Value"]) -
                            expected[name][key]) < 0.001,
                        f"Evidence CSV value mismatch: {stem}/{key}")
            for wdi in (r for r in csv_rows(out / f"{stem}-diagnostic.csv")
                        if r["Record scope"] == "overall" and r["Indicator ID"] == "SP.POP.TOTL"):
                require(wdi["Status"] == "not_collected" and not wdi["Value"],
                        f"National WDI value leaked into {stem}")
        checks.append({"case": stem, "territory_id": selected_id,
                       "direct_source_cells": 9, "derived_source_ratios": 2,
                       "outputs": 5})
    national = csv_rows(out / "TLS-diagnostic.csv")
    compared = [r for r in national if r["Record scope"] == "within_area" and
                r["Indicator ID"].startswith("TLS_PHC2022_")]
    require(len(compared) == 14 * 11, f"Unexpected internal comparison rows: {len(compared)}")
    grouped = {}
    for row in compared:
        name = row["Territory"]
        key = row["Indicator ID"].removeprefix("TLS_PHC2022_")
        require(name in AREAS and key in ALL_KEYS and (name, key) not in grouped,
                f"Duplicate or unexpected comparison row {name}/{key}")
        compare(row, name, key, expected[name][key], source["url"])
        grouped[name, key] = row
    require(set(grouped) == {(name, key) for name in AREAS for key in ALL_KEYS},
            "Within-area comparison not complete")

    plan = {stem: (out / f"{stem}-planning.html").read_text(encoding="utf-8")
            for stem in CASES}
    dili_title = "Díli municipal strategic development plan 2026–2030"
    atauro_title = "Ataúro development plan 2026–2030, published draft"
    for stem in CASES:
        require((dili_title in plan[stem]) == (stem == "Dili"),
                f"Díli plan scope incorrect: {stem}")
        require((atauro_title in plan[stem]) == (stem == "Atauro"),
                f"Ataúro plan scope incorrect: {stem}")
        require(("US$19,502,642" in plan[stem]) == (stem == "Dili"),
                f"Díli planned budget scope incorrect: {stem}")
    budget_source = next(s for s in manifest["sources"] if s["id"] == "tls-dili-paa-2026")
    budget_text = pdf_text(project / budget_source["raw_path"], 8, 8)
    require("Total Orsamentu" in budget_text and "$19,502,642" in budget_text,
            "Source budget total does not match planned figure")
    result = {"country_id": "TLS", "dataset_sha256": hashlib.sha256(dashboard_bytes).hexdigest(),
              "checked_cases": checks, "national_comparison_rows": 14,
              "national_comparison_indicator_cells": len(compared),
              "source_cells_checked_in_cases": len(CASES) * 9,
              "derived_ratios_checked_in_cases": len(CASES) * 2,
              "source_cells_checked_in_comparison": 14 * 9,
              "derived_ratios_checked_in_comparison": 14 * 2,
              "budget_source_checked": True, "document_scope_checked": True,
              "independent_acceptance": False}
    (project / "evidence/TLS_OUTPUT_VERIFICATION.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked_cases": len(CASES),
                      "national_comparison_rows": result["national_comparison_rows"],
                      "national_comparison_indicator_cells": len(compared),
                      "dataset_sha256": result["dataset_sha256"]}))


if __name__ == "__main__":
    main()

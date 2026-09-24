"""Adopt two visually reviewed 2019 RGPH regional columns, with exact row replay."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import csv
import json
import re
import subprocess
import unicodedata


ap = ArgumentParser()
ap.add_argument("--project", required=True)
args = ap.parse_args()
project = Path(args.project)
source = project / "raw/insd-rgph-2019/statistical_tables.pdf"
assert sha256(source.read_bytes()).hexdigest() == "a665f61e49581cb39e85fdd3d70cb699acf3ec7b964dfbb2852fd35cfc19d7f2"
dataset_path = project / "data/dashboard.json"
data = json.loads(dataset_path.read_text(encoding="utf-8"))
assert data["country"]["id"] == "BFA"


def norm(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in value if not unicodedata.combining(c)))


areas = {norm(area["name"]): area for area in data["territories"] if area["level"] == "adm1"}
assert len(areas) == 13


def page_text(page):
    result = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(source), "-"],
                            capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def rows_between(text, start, stop, value_columns):
    section = text.split(start, 1)[1].split(stop, 1)[0]
    found = []
    number = r"\d+(?:[,.]\d+)?"
    row_re = re.compile(r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ -]*?)\s+" + r"\s+".join([f"({number})"] * value_columns) + r"\s*$")
    for line in section.splitlines():
        match = row_re.match(line)
        if match:
            found.append((match.group(1).strip(), [float(x.replace(",", ".")) for x in match.groups()[1:]]))
    return found


tables = [
    {
        "table": "II.6", "page": 50, "stop": "Tableau II.7", "columns": 2, "value_column": 0,
        "id": "BFA_RGPH2019_CRUDE_BIRTH_RATE_REGIONAL", "name": "Crude birth rate, 2019 census",
        "theme": "Population and demography", "unit": "births per 1,000 residents",
        "definition": "Annual live births per 1,000 inhabitants, as published by INSD for 2019 census regions. This is the crude birth rate (TBN), not the standardized comparative birth index (ICN).",
        "population": "Resident population; live births in the preceding 12 months",
        "upstream_column": "TBN", "national_expected": 39.4,
    },
    {
        "table": "III.11", "page": 69, "stop": "INSD-Résultats", "columns": 3, "value_column": 2,
        "id": "BFA_RGPH2019_JUVENILE_MORTALITY_QUOTIENT_REGIONAL", "name": "Juvenile mortality quotient ages 1 to 4, 2019 census",
        "theme": "Health and nutrition", "unit": "per 1,000 children reaching age 1",
        "definition": "INSD published 4q1 quotient: among 1,000 children who reached their first birthday, the number dying before age five. This is not infant mortality (1q0) or under-five mortality from live birth (5q0).",
        "population": "Children surviving to their first birthday",
        "upstream_column": "Quotient de mortalité juvénile (4q1) / Ensemble", "national_expected": 33.3,
    },
]

existing_indicators = {item["id"] for item in data["indicators"]}
existing_obs = {(row["territory_id"], row["indicator_id"], row["period"]) for row in data["observations"]}
audit = []
for spec in tables:
    text = page_text(spec["page"])
    label = f"Tableau {spec['table']}"
    if spec["table"] == "III.11":
        # The footer follows this table on the same page.
        rows = rows_between(text, label, spec["stop"], spec["columns"])
    else:
        rows = rows_between(text, label, spec["stop"], spec["columns"])
    assert len(rows) == 14, (label, rows)
    assert len({norm(name) for name, _ in rows}) == 14
    indicator = {
        "id": spec["id"], "name": spec["name"], "theme": spec["theme"], "unit": spec["unit"],
        "definition": spec["definition"], "population": spec["population"],
        "source_id": "bfa-insd-rgph2019-statistical-tables", "aggregation": "none",
        "measurement_method": "INSD published 2019 RGPH rate or mortality quotient; source-reported, not an AreaData calculation",
        "series_family": "census", "display_role": "primary", "period_policy": "source_year",
        "upstream_source_id": "bfa-insd-rgph2019-statistical-tables",
        "upstream_table": label, "upstream_column": spec["upstream_column"],
    }
    if spec["id"] not in existing_indicators:
        data["indicators"].append(indicator)
    seen = set()
    for name, values in rows:
        area = {"id": "BFA", "name": "Burkina Faso"} if norm(name) in {"ensemble", "burkinafaso"} else areas[norm(name)]
        value = values[spec["value_column"]]
        if area["id"] == "BFA":
            assert value == spec["national_expected"]
        assert area["id"] not in seen
        seen.add(area["id"])
        key = (area["id"], spec["id"], "2019")
        observation = {
            "territory_id": area["id"], "indicator_id": spec["id"], "period": "2019",
            "value": value, "status": "observed", "source_id": "bfa-insd-rgph2019-statistical-tables",
            "value_origin": "source_reported_table", "source_locator": f"{label}, {spec['upstream_column']}, physical PDF page {spec['page']}",
        }
        if key not in existing_obs:
            data["observations"].append(observation)
        audit.append({"table": label, "pdf_page": spec["page"], "territory_id": area["id"],
                      "source_row": name, "column": spec["upstream_column"], "value": value,
                      "unit": spec["unit"], "period": "2019", "decision": "adopted_source_reported"})
    assert len(seen) == 14

dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with (project / "evidence/PRIORITY_TABLE_ADOPTION.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=audit[0].keys())
    writer.writeheader()
    writer.writerows(audit)
print(json.dumps({"indicators": len(data["indicators"]), "observations": len(data["observations"]),
                  "new_rows_verified": len(audit)}, ensure_ascii=False))

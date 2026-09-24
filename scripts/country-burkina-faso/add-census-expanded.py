"""Adopt seven additional, explicitly defined regional columns from the INSD RGPH tables.

The parser reads the acquired PDF's layout text, checks every historical region,
the national printed value, column count, and source hash before adding values.
It never maps the 2019 geography onto the 2025 administrative division.
"""
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw/insd-rgph-2019"
DATA = ROOT / "data/dashboard.json"
SOURCE_ID = "bfa-insd-rgph2019-statistical-tables"
base = json.loads(DATA.read_text(encoding="utf-8"))
source = next(item for item in base["sources"] if item["id"] == SOURCE_ID)
assert sha256((RAW / "statistical_tables.pdf").read_bytes()).hexdigest() == source["sha256"]
lines = (RAW / "statistical_tables.txt").read_text(encoding="utf-8").splitlines()


def key(value):
    return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().upper())


regions = {key(area["name"]): area for area in base["territories"] if area["level"] == "adm1"}
assert len(regions) == 13
decimal = re.compile(r"(?<!\d)\d{1,3},\d(?!\d)")


def table_rows(table_id, count, last_section=False):
    heading = re.compile(r"^\s*Tableau\s+" + re.escape(table_id) + r"\s*:", re.I)
    starts = [index for index, line in enumerate(lines) if index > 900 and heading.match(line)]
    assert starts, table_id
    # VIII.19 publishes several age bands; its final continuation is the
    # requested 6-16 column. IX.22 continues across a page break, so start
    # with its first body heading and retain all rows before IX.23.
    start = starts[-1] if last_section else starts[0]
    next_table = re.compile(r"^\s*Tableau\s+[IVX]+\.\d+[A-Za-z]?\s*:", re.I)
    values = {}
    for line in lines[start + 1:]:
        if next_table.match(line) and not heading.match(line):
            break
        numbers = decimal.findall(line)
        if len(numbers) != count:
            continue
        name = key(line[:decimal.search(line).start()].strip())
        if name in regions or name == "BURKINAFASO":
            parsed = [float(item.replace(",", ".")) for item in numbers]
            if name in values:
                assert values[name] == parsed, (table_id, name)
            values[name] = parsed
    assert set(values) == set(regions) | {"BURKINAFASO"}, (table_id, sorted(values))
    return values


# ID, table, published column, decimal column count, national printed value,
# theme, title, and exact meaning. The title is deliberately narrower than an
# SDG or administrative-service indicator with a different denominator.
specs = [
    ("SCHOOL_ATTENDING_6_16", "VIII.19", 2, 4, 45.9, "Education",
     "Residents aged 6-16 attending school", "Percentage of resident children aged 6-16 classified as Scolarisé in the source's school-status distribution; not a net enrolment rate.", True),
    ("GROSS_PRESCHOOL_ENROLMENT", "VIII.27", 0, 12, 3.6, "Education",
     "Gross preschool enrolment rate", "Published gross preschool enrolment rate, overall sex and residence column; not net attendance.", False),
    ("NET_POSTPRIMARY_ENROLMENT", "VIII.43", 0, 12, 21.2, "Education",
     "Net post-primary enrolment rate", "Published net post-primary enrolment rate for ages 12-15, overall sex and residence column; not the adjusted net rate.", False),
    ("NET_SECONDARY_ENROLMENT", "VIII.50", 0, 12, 6.3, "Education",
     "Net secondary enrolment rate", "Published net secondary enrolment rate for ages 16-18, overall sex and residence column; not gross enrolment.", False),
    ("ILO_UNEMPLOYMENT_RATE", "IX.22", 5, 6, 7.1, "Livelihoods, poverty and economy",
     "Unemployment rate (ILO/BIT definition)", "Published BIT unemployment rate, Ensemble column. The combined unemployment rate is a separate measure and is not substituted.", False),
    ("WASTEWATER_STREET_NATURE", "VII.74", 1, 7, 74.3, "Housing, water, sanitation and energy",
     "Households draining wastewater to street or nature", "Percentage of households whose principal wastewater disposal mode is Rue/Nature; not the SDG safely managed sanitation rate.", False),
    ("DISABILITY_PREVALENCE_5PLUS", "XII.4", 2, 3, 1.1, "Health and nutrition",
     "Disability prevalence, age 5+", "Published prevalence of disability among residents aged at least 5, overall-sex column; based on the census disability definition.", False),
]
existing = {item["id"] for item in base["indicators"]}
for suffix, table_id, column, count, national, theme, title, definition, last_section in specs:
    indicator_id = "BFA_RGPH2019_" + suffix + "_REGIONAL"
    assert indicator_id not in existing, indicator_id
    values = table_rows(table_id, count, last_section)
    assert values["BURKINAFASO"][column] == national, (table_id, values["BURKINAFASO"])
    base["indicators"].append({
        "id": indicator_id, "name": title, "theme": theme, "unit": "%",
        "definition": definition, "source_id": SOURCE_ID, "aggregation": "none",
        "measurement_method": "INSD published 2019 RGPH table; source-reported rate or share",
        "series_family": "census", "display_role": "primary", "period_policy": "source_year",
        "upstream_source_id": SOURCE_ID, "upstream_table": "Tableau " + table_id,
        "upstream_column": {"VIII.19": "6-16 ans / Scolarisé", "VIII.27": "Ensemble / Ens",
            "VIII.43": "Ensemble / Ens", "VIII.50": "Ensemble / Ens",
            "IX.22": "Taux chômage BIT / Ensemble", "VII.74": "Rue/Nature",
            "XII.4": "Ensemble personnes handicapées / Prévalence (%)"}[table_id],
    })
    for area_key, row in values.items():
        base["observations"].append({
            "territory_id": "BFA" if area_key == "BURKINAFASO" else regions[area_key]["id"],
            "indicator_id": indicator_id, "period": "2019", "value": row[column],
            "status": "observed", "source_id": SOURCE_ID,
            "value_origin": "source_reported_table",
            "source_locator": "Tableau " + table_id + ", " + base["indicators"][-1]["upstream_column"],
        })

base["collection"]["adapters"].append("insd-rgph-2019-expanded-regional-tables")
base["collection"]["notes"].append("Seven further INSD columns were checked against all 13 historical regions and their national printed values; no province or commune value was inferred.")
DATA.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"new_indicators": len(specs), "new_observations": len(specs) * 14}))

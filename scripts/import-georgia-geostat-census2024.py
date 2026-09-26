"""Import a checked subset of Geostat's final 2024 census XLSX tables.

The 48-table catalog and column inventory remain private in the country project.
This adapter adopts six tables and keeps their source scope and row locators.
"""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


PREFIX = "GEO_GEOSTAT24_"
SELECTED = ("909-02", "910-02", "912-01", "913-01", "915-01")
TOP_ROWS = (8, 19, 26, 30, 43, 52, 57, 62, 72, 79, 87)
NEXT_ROWS = TOP_ROWS[1:] + (92,)
AGE_LABELS = [f"{x}-{x+4}" for x in range(0, 85, 5)] + ["85+"]
ALIASES = {
    "910-02": {"Adjara A.R.": "Adjara of Autonomous Republic", "Tkibuli Municipality": "Tqibuli Municipality",
               "Tskaltubo Municipality": "Tsqaltubo Municipality", "Dedoplistskaro Municipality": "Dedoplistsqaro Municipality",
               "Tetritskaro Municipality": "Tetritsqaro Municipality"},
    "913-01": {"C. Kutaisi": "C. Kutaisi Municipality"},
}


def check(condition, detail):
    if not condition:
        raise ValueError(detail)


def count(ws, row, col):
    value = ws.cell(row, col).value
    if value == "-":  # Source legend: "Magnitude nil".
        return 0
    check(isinstance(value, int) and not isinstance(value, bool) and value >= 0,
          f"Non-count at {ws.title}!{row}:{col}: {value!r}")
    return value


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]+", "-", name.upper())).strip("-")


def source_id(table_id):
    return f"geo-geostat-census2024-{table_id}"


def load_selected(project):
    catalog = json.loads((project / "evidence/GEO_GEOSTAT2024_CATALOG_INVENTORY.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in catalog["tables"]}
    check(len(catalog["tables"]) == 48, "Geostat 48-table catalog changed")
    sheets = {}
    for key in SELECTED:
        t = by_id[key]
        path = project / t["path"]
        check(path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == t["sha256"],
              f"Missing/changed original {key}")
        wb = load_workbook(path, read_only=False, data_only=True)
        check(len(wb.worksheets) == 1, f"Unexpected sheets in {key}")
        sheets[key] = wb.active
    return by_id, sheets


def population_table(ws):
    check([ws.cell(6, col).value for col in range(2, 11)] ==
          ["Both Sexes", "Males", "Females"] * 3, "Population column labels changed")
    rows = {}
    for r in range(7, 92):
        name = ws.cell(r, 1).value
        check(isinstance(name, str) and name, f"Missing geography at 909-02 row {r}")
        values = [count(ws, r, c) for c in range(2, 11)]
        for start in (0, 3, 6):
            check(values[start] == values[start+1] + values[start+2], f"Sex subtotal {name}")
        for sex in range(3):
            check(values[sex] == values[3+sex] + values[6+sex], f"Urban/rural subtotal {name}")
        rows[r] = {"name": name, "values": values}
    for parent, next_row in zip(TOP_ROWS, NEXT_ROWS):
        for col in range(9):
            check(rows[parent]["values"][col] == sum(rows[r]["values"][col] for r in range(parent+1, next_row)),
                  f"Child coverage {rows[parent]['name']} column {col}")
    for col in range(9):
        check(rows[7]["values"][col] == sum(rows[r]["values"][col] for r in TOP_ROWS),
              f"National coverage column {col}")
    check(rows[7]["values"][0] == 3929581, "Final census national total changed")
    ids = {7: "GEO"}
    for parent, next_row in zip(TOP_ROWS, NEXT_ROWS):
        name = rows[parent]["name"]
        ids[parent] = "GEO:GEOSTAT24:TBILISI" if parent == 8 else f"GEO:GEOSTAT24:REGION:{slug(name)}"
        for r in range(parent+1, next_row):
            ids[r] = (f"GEO:GEOSTAT24:TBILISI:DISTRICT:{slug(rows[r]['name'])}" if parent == 8 else
                      f"GEO:GEOSTAT24:MUNICIPALITY:{slug(name)}:{slug(rows[r]['name'])}")
    check(len(ids) == 85 and len(set(ids.values())) == 85, "Territory ID uniqueness")
    non_district_rows = [7, 8, *range(19, 92)]
    check(len(non_district_rows) == 75, "Region/municipality row count")
    return rows, ids, non_district_rows


def matching_name(table_id, actual, expected):
    check(actual == ALIASES.get(table_id, {}).get(expected, expected),
          f"Geography crosswalk {table_id}: expected {expected!r}, got {actual!r}")


def age_table(ws, pop_rows, source_rows):
    result = {}
    for i, base_row in enumerate(source_rows):
        row = 7 + 19*i
        matching_name("910-02", ws.cell(row, 1).value, pop_rows[base_row]["name"])
        totals = [count(ws, row, c) for c in range(2, 11)]
        check(totals == pop_rows[base_row]["values"], f"Age/population all nine fields {row}")
        groups = []
        for j, label in enumerate(AGE_LABELS, 1):
            rr = row+j
            check(ws.cell(rr, 1).value == label, f"Age label {rr}")
            values = [count(ws, rr, c) for c in range(2, 11)]
            for start in (0, 3, 6):
                check(values[start] == values[start+1] + values[start+2], f"Age sex {rr}")
            for sex in range(3):
                check(values[sex] == values[sex+3] + values[sex+6], f"Age urban/rural {rr}")
            groups.append(values)
        for col in range(9):
            check(sum(g[col] for g in groups) == totals[col], f"Age total {row} column {col}")
        result[base_row] = {"row": row, "groups": groups}
    return result


def education_table(ws, pop_rows, source_rows, ages):
    result = {}
    for i, base_row in enumerate(source_rows):
        row = 8+i
        matching_name("912-01", ws.cell(row, 1).value, pop_rows[base_row]["name"])
        values = [count(ws, row, c) for c in range(2, 29)]
        for block in (0, 9, 18):
            check(values[block] == sum(values[block+1:block+9]), f"Education category subtotal {row}")
        for col in range(9):
            check(values[col] == values[9+col] + values[18+col], f"Education sex subtotal {row}:{col}")
        check(values[0] == sum(g[0] for g in ages[base_row]["groups"][2:]),
              f"Education age10+ denominator vs age table {row}")
        result[base_row] = {"row": row, "values": values}
    return result


def labour_table(ws, pop_rows, source_rows, ages):
    result = {}
    for i, base_row in enumerate(source_rows):
        row = 10+i
        matching_name("913-01", ws.cell(row, 1).value, pop_rows[base_row]["name"])
        values = [count(ws, row, c) for c in range(2, 38)]
        for block in (0, 12, 24):
            check(values[block] == values[block+1] + values[block+10] + values[block+11],
                  f"Labour 15+ universe {row}")
            check(values[block+1] == values[block+2] + values[block+9], f"Labour force {row}")
            check(values[block+2] == sum(values[block+3:block+9]), f"Employment classes {row}")
        for col in range(12):
            check(values[col] == values[12+col] + values[24+col], f"Labour sex subtotal {row}:{col}")
        check(values[0] == sum(g[0] for g in ages[base_row]["groups"][3:]),
              f"Labour age15+ denominator vs age table {row}")
        result[base_row] = {"row": row, "values": values}
    return result


def households_table(ws, pop_rows, source_rows):
    result = {}
    for i, base_row in enumerate(source_rows):
        row = 9+i
        matching_name("915-01", ws.cell(row, 1).value, pop_rows[base_row]["name"])
        # Total, urban and rural each contain persons, household count, size 1..10+, mean.
        parts = []
        for start in (2, 15, 28):
            persons = count(ws, row, start)
            households = count(ws, row, start+1)
            sizes = [count(ws, row, c) for c in range(start+2, start+12)]
            mean = ws.cell(row, start+12).value
            check(households == sum(sizes), f"Household-size categories {row}:{start}")
            check((isinstance(mean, (float, int)) and abs(mean - persons/households) < 0.01)
                  if households else mean == "-", f"Mean household size {row}:{start}")
            parts.append((persons, households, sizes))
        for field in (0, 1):
            check(parts[0][field] == parts[1][field] + parts[2][field], f"Households urban/rural {row}")
        for j in range(10):
            check(parts[0][2][j] == parts[1][2][j] + parts[2][2][j], f"Household-size urban/rural {row}:{j}")
        check(parts[0][0] <= pop_rows[base_row]["values"][0], f"Private household residents > census total {row}")
        result[base_row] = {"row": row, "persons": parts[0][0], "households": parts[0][1]}
    return result


def main(project):
    by_id, sheets = load_selected(project)
    pop, ids, source_rows = population_table(sheets["909-02"])
    ages = age_table(sheets["910-02"], pop, source_rows)
    education = education_table(sheets["912-01"], pop, source_rows, ages)
    labour = labour_table(sheets["913-01"], pop, source_rows, ages)
    households = households_table(sheets["915-01"], pop, source_rows)
    path = project / "data/dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    check(data["country"]["id"] == "GEO", "Expected Georgia candidate")
    data["territories"] = [t for t in data["territories"] if t["id"] == "GEO"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [i for i in data["indicators"] if not i["id"].startswith(PREFIX)]
    data["observations"] = [o for o in data["observations"] if not o["indicator_id"].startswith(PREFIX)]
    data["sources"] = [s for s in data["sources"] if not s["id"].startswith(("geo-geostat-census2024-", "geo-matsne-"))
                       and s["id"] not in ("geo-geostat-census2024-catalog", "geo-geostat-gis-portal", "geo-batumi-budget-portal")]
    data["country"]["geography_note"] = (
        "Geostat's final 2024 census counts usual residents at 14 November 2024 and excludes occupied territories. "
        "The 11 top-level reporting rows sum to the published national value, and all 9 sex/urban-rural fields reconcile "
        "through 63 municipalities and 10 Tbilisi districts. These are pinned source-row identities, not verified official "
        "administrative codes or year-compatible polygons; 2015 geoBoundaries shapes are unjoined. WDI midyear estimates "
        "and 2025/2026 administrative population estimates remain distinct from the census.")
    data["territories"][0]["source_id"] = source_id("909-02")
    data["territories"][0]["reconciliation_status"] = "2024 Geostat census direct national row; occupied territories excluded"
    for parent, next_row in zip(TOP_ROWS, NEXT_ROWS):
        name = pop[parent]["name"]
        data["territories"].append({"id": ids[parent], "name": name, "level": "geostat_top_level",
            "type": "Tbilisi self-governed municipality and top-level reporting area" if parent == 8 else "Geostat region/autonomous-republic reporting area",
            "parent_id": "GEO", "official_code": None,
            "code_system": "Geostat 2024 census Table 909-02 source row; official administrative code not acquired",
            "boundary_version": None, "source_id": source_id("909-02"),
            "reconciliation_status": "Source row and nine-column child subtotal checked; current code and polygon unverified"})
        for r in range(parent+1, next_row):
            data["territories"].append({"id": ids[r], "name": pop[r]["name"],
                "level": "tbilisi_district" if parent == 8 else "municipality",
                "type": "Tbilisi census district for internal diagnosis" if parent == 8 else "Self-governed city or municipality as labelled by Geostat",
                "parent_id": ids[parent], "official_code": None,
                "code_system": "Geostat 2024 census Table 909-02 source row; official administrative code not acquired",
                "boundary_version": None, "source_id": source_id("909-02"),
                "reconciliation_status": "Source row and nine-column parent subtotal checked; official code/polygon unverified"})
    data["analysis"]["comparisons"] = [{"parent_id": "GEO", "member_ids": [ids[r] for r in TOP_ROWS],
        "label": "Geostat 2024 census top-level reporting areas", "source_ids": [source_id(k) for k in SELECTED],
        "membership_note": "Eleven source rows exclude occupied territories, as does the directly reported census national value. All nine population fields match that national row. Tbilisi is a self-governed municipality and one top-level reporting row."}]
    for parent, next_row in zip(TOP_ROWS, NEXT_ROWS):
        data["analysis"]["comparisons"].append({"parent_id": ids[parent],
            "member_ids": [ids[r] for r in range(parent+1, next_row)],
            "label": f"2024 census internal rows of {pop[parent]['name']}",
            "source_ids": [source_id("909-02")],
            "membership_note": "All nine sex/urban-rural population columns sum exactly to the parent. These are source-row matches, not official code/boundary certification. Other themes are absent for Tbilisi districts." if parent == 8 else
                               "All nine sex/urban-rural population columns sum exactly to the parent. These are source-row matches, not official code/boundary certification."})
    data["analysis"]["terminal_territory_ids"] = [ids[r] for r in range(20, 92) if r not in TOP_ROWS]
    data["analysis"]["terminal_territory_ids"] += [ids[r] for r in range(9, 19)]
    data["analysis"]["default_indicator_id"] = PREFIX + "POP_TOTAL"
    data["analysis"]["latest_values_only"] = True
    data["analysis"].pop("population_context", None)

    specs = [
        ("POP_TOTAL", "2024 census population", "Population", "people", "Usual residents in the 2024 census, excluding occupied territories", "909-02", "source_reported", 0),
        ("POP_MALE", "2024 census male population", "Population", "people", "Male usual residents", "909-02", "source_reported", 0),
        ("POP_FEMALE", "2024 census female population", "Population", "people", "Female usual residents", "909-02", "source_reported", 0),
        ("POP_URBAN", "2024 census urban population", "Population", "people", "Usual residents in urban settlements", "909-02", "source_reported", 0),
        ("POP_URBAN_MALE", "2024 census urban male population", "Population", "people", "Male usual residents in urban settlements", "909-02", "source_reported", 0),
        ("POP_URBAN_FEMALE", "2024 census urban female population", "Population", "people", "Female usual residents in urban settlements", "909-02", "source_reported", 0),
        ("POP_RURAL", "2024 census rural population", "Population", "people", "Usual residents in rural settlements", "909-02", "source_reported", 0),
        ("POP_RURAL_MALE", "2024 census rural male population", "Population", "people", "Male usual residents in rural settlements", "909-02", "source_reported", 0),
        ("POP_RURAL_FEMALE", "2024 census rural female population", "Population", "people", "Female usual residents in rural settlements", "909-02", "source_reported", 0),
        ("AGE_0_14", "2024 census population aged 0–14", "Population", "people", "All usual residents in three non-overlapping five-year age bands", "910-02", "areadata_calculated", 0),
        ("AGE_15_64", "2024 census population aged 15–64", "Population", "people", "All usual residents in ten non-overlapping five-year age bands", "910-02", "areadata_calculated", 0),
        ("AGE_65_PLUS", "2024 census population aged 65+", "Population", "people", "All usual residents in five non-overlapping age bands", "910-02", "areadata_calculated", 0),
        ("EDU_10PLUS_TOTAL", "2024 census education-table population aged 10+", "Education", "people", "All usual residents aged 10+ including education status not stated", "912-01", "source_reported", 0),
        ("EDU_HIGHER_10PLUS", "2024 census higher education, aged 10+", "Education", "people", "Geostat higher-education attainment category among residents aged 10+", "912-01", "source_reported", 0),
        ("EDU_ILLITERATE_10PLUS", "2024 census illiterate, aged 10+", "Education", "people", "Geostat illiterate category among residents aged 10+", "912-01", "source_reported", 0),
        ("LABOUR_15PLUS_TOTAL", "2024 census work-table population aged 15+", "Labour", "people", "All usual residents aged 15+ including activity status not stated", "913-01", "source_reported", 0),
        ("LABOUR_ACTIVE", "2024 census economically active, aged 15+", "Labour", "people", "Economically active usual residents aged 15+", "913-01", "source_reported", 0),
        ("LABOUR_EMPLOYED", "2024 census employed, aged 15+", "Labour", "people", "Employed usual residents aged 15+", "913-01", "source_reported", 0),
        ("LABOUR_UNEMPLOYED", "2024 census unemployed, aged 15+", "Labour", "people", "Unemployed economically active residents aged 15+", "913-01", "source_reported", 0),
        ("LABOUR_UNEMPLOYMENT_SHARE", "2024 census unemployment share of labour force", "Labour", "%", "100 × unemployed divided by economically active, same source row and census period", "913-01", "areadata_calculated", 2),
        ("PRIVATE_HOUSEHOLDS", "2024 census private households", "Households", "households", "Private households; excludes non-private living arrangements", "915-01", "source_reported", 0),
        ("PRIVATE_HOUSEHOLD_RESIDENTS", "2024 census residents in private households", "Households", "people", "Usual residents living in private households; a subset of all census residents", "915-01", "source_reported", 0),
    ]
    for suffix, name, theme, unit, universe, table, method, decimals in specs:
        data["indicators"].append({"id": PREFIX+suffix, "name": name, "theme": theme, "unit": unit,
            "definition": f"{name}. {universe}. Geostat final 2024 census reference date 14 November 2024; occupied territories excluded.",
            "population": universe, "source_id": source_id(table), "aggregation": "none", "measurement_method": method,
            "display_decimals": decimals})

    def emit(base_row, suffix, value, table, locator, note=None):
        observation = {"territory_id": ids[base_row], "indicator_id": PREFIX+suffix, "period": "2024",
                       "value": value, "status": "observed", "source_id": source_id(table),
                       "measurement_method": "areadata_calculated" if note else "source_reported",
                       "source_locator": f"Geostat 2024 census {table}, sheet 1 {locator}"}
        if note:
            observation.update({"provenance": "calculated", "footnote": note})
        data["observations"].append(observation)

    population_fields = ("POP_TOTAL", "POP_MALE", "POP_FEMALE", "POP_URBAN", "POP_URBAN_MALE",
                         "POP_URBAN_FEMALE", "POP_RURAL", "POP_RURAL_MALE", "POP_RURAL_FEMALE")
    for base_row in range(7, 92):
        for index, suffix in enumerate(population_fields):
            emit(base_row, suffix, pop[base_row]["values"][index], "909-02", f"row {base_row}, column {index+2}; '-': magnitude nil")
    for base_row in source_rows:
        age = ages[base_row]
        for suffix, lo, hi in (("AGE_0_14", 0, 3), ("AGE_15_64", 3, 13), ("AGE_65_PLUS", 13, 18)):
            value = sum(g[0] for g in age["groups"][lo:hi])
            emit(base_row, suffix, value, "910-02", f"rows {age['row']+lo+1}–{age['row']+hi}, column B",
                 f"AreaData sum of {hi-lo} non-overlapping source age groups; all 18 groups in this row block equal 909-02 census population.")
        e = education[base_row]
        for suffix, col in (("EDU_10PLUS_TOTAL", 2), ("EDU_HIGHER_10PLUS", 3), ("EDU_ILLITERATE_10PLUS", 9)):
            emit(base_row, suffix, e["values"][col-2], "912-01", f"row {e['row']}, column {col}")
        l = labour[base_row]
        for suffix, col in (("LABOUR_15PLUS_TOTAL", 2), ("LABOUR_ACTIVE", 3),
                            ("LABOUR_EMPLOYED", 4), ("LABOUR_UNEMPLOYED", 11)):
            emit(base_row, suffix, l["values"][col-2], "913-01", f"row {l['row']}, column {col}")
        denominator = l["values"][1]
        check(denominator > 0, f"Zero labour-force denominator {base_row}")
        rate = round(100*l["values"][9]/denominator, 2)
        emit(base_row, "LABOUR_UNEMPLOYMENT_SHARE", rate, "913-01", f"row {l['row']}, column 11 / column 3",
             f"AreaData: 100 × {l['values'][9]:,} unemployed / {denominator:,} economically active = {rate:.2f}%. Source active = employed + unemployed.")
        h = households[base_row]
        emit(base_row, "PRIVATE_HOUSEHOLDS", h["households"], "915-01", f"row {h['row']}, column C")
        emit(base_row, "PRIVATE_HOUSEHOLD_RESIDENTS", h["persons"], "915-01", f"row {h['row']}, column B")

    for key in SELECTED:
        t = by_id[key]
        data["sources"].append({"id": source_id(key), "name": f"Geostat final 2024 population census: {t['title']}",
            "url": t["url"], "publisher": "National Statistics Office of Georgia (Geostat)",
            "reference_period": "2024-11-14 census reference time (some mountainous locations enumerated September 2024)",
            "geographic_level": "national, top-level, municipality; Tbilisi district only in population table",
            "status": "partial", "license": "https://www.geostat.ge/en/page/monacemta-gamoyenebis-pirobebi",
            "raw_path": t["path"], "sha256": t["sha256"], "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "note": "Original XLSX hash pinned. Source numeric cells and arithmetic checked in adopted table. Only explicitly named indicators adopted; census excludes occupied territories; official geography codes and polygons unverified."})
    for ident, name, url, note in [
        ("geo-geostat-census2024-catalog", "Geostat 2024 census thematic table catalog", "https://www.geostat.ge/en/modules/categories/12/2024-population-census-of-georgia-results", "Eight thematic category HTML originals and 48 XLSX originals acquired and mechanically field-inventoried; 43 tables remain semantically unassessed and not adopted."),
        ("geo-geostat-gis-portal", "Geostat GIS portal", "https://gis.geostat.ge/en/", "Official GIS portal location only. No 2024-compatible code edition or municipality/Tbilisi district polygon was acquired or joined."),
        ("geo-matsne-spatial-code", "Georgia Code on Spatial Planning, Architecture and Construction Activities", "https://matsne.gov.ge/en/document/view/4276845", "Municipality spatial planning and approval provisions located; current consolidation, special regulation exceptions and actual municipal plans require legal and document audit."),
        ("geo-matsne-local-self-government-code", "Georgia Organic Law Local Self-Government Code", "https://matsne.gov.ge/en/document/view/2244429", "Municipal budget and spatial-planning powers located; current consolidation and implementation require audit."),
        ("geo-matsne-ordinance260", "Government Ordinance 260 on spatial-planning document procedure", "https://matsne.gov.ge/ka/document/view/4579368?publication=0", "Official ordinance location only. Amendments, operative rules, applicable municipality and current manual/form require legal audit."),
        ("geo-matsne-tbilisi-plan2019", "Tbilisi 2019 land-use general plan record", "https://www.matsne.gov.ge/ka/document/view/4508064", "Official document location only. Current amendments, operative plan body, approval and selected-district application were not adopted."),
        ("geo-matsne-tbilisi-budget2026-initial", "Tbilisi 2026 initial budget ordinance", "https://www.matsne.gov.ge/ka/document/view/6712283", "Initial ordinance location only; later consolidation requires review, so no current 2026 budget amount or execution is adopted."),
        ("geo-batumi-budget-portal", "Batumi municipality budget portal", "https://batumi.gov.ge/budget", "Official municipal budget catalogue location only. Current ordinance, line items, amendments and execution were not adopted."),
    ]:
        publisher = "Geostat" if ident.startswith("geo-geostat") else ("Batumi Municipality" if ident.startswith("geo-batumi") else "Legislative Herald of Georgia")
        source = {"id": ident, "name": name, "url": url, "publisher": publisher,
            "reference_period": "location checked 2026-09-26", "geographic_level": "Georgia",
            "status": "partial" if ident == "geo-geostat-census2024-catalog" else "not_collected",
            "license": "https://www.geostat.ge/en/page/monacemta-gamoyenebis-pirobebi" if ident.startswith("geo-geostat") else "source_terms_review_required",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "note": note}
        if ident == "geo-geostat-census2024-catalog":
            catalog = json.loads((project / "evidence/GEO_GEOSTAT2024_CATALOG_INVENTORY.json").read_text(encoding="utf-8"))
            source.update({"raw_path": catalog["catalogs"][0]["path"], "sha256": catalog["catalogs"][0]["sha256"]})
        data["sources"].append(source)
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    ("subnational_statistics", "boundary_reconciliation", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Five selected Geostat final-2024 census XLSX tables add 22 local indicators on population, age, education, labour and private households. All 48 catalog XLSX originals are retained and 85,449 numeric cells mechanically inventoried; 43 tables have no semantic adoption decision. The 2015/2025/2026 population series is separate.",
         "next_action": "Semantically assess the other 43 tables and sectoral local series; classify every source field, scope and denominator before expansion."},
        {"category": "boundary_reconciliation", "status": "not_collected",
         "detail": "Geostat 2024 source rows and all nine population fields reconcile through region, municipality and Tbilisi district. No official administrative code or year-compatible polygon has been matched. Twelve 2015 geoBoundaries reference shapes remain unjoined; occupied territories are excluded from census counts.",
         "next_action": "Acquire official administrative classification/code edition and census-compatible region/municipality boundaries; reconcile exceptions and settlement hierarchy."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "Spatial-planning and local-self-government law locations are known. Current consolidation, municipality-specific plans, budgets, implementation and evaluation are not audited or adopted.",
         "next_action": "Read current consolidated codes and ordinances, locate approved plans and budget/implementation records for contrasting municipalities and special-regulation areas."},
    ]
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] +
                                                 ["georgia-geostat-final-census2024-five-table-partial-v1"]))
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    imported = [o for o in data["observations"] if o["indicator_id"].startswith(PREFIX)]
    check(len(data["territories"]) == 85 and len(specs) == 22 and len(imported) == 1740,
          f"Georgia adoption counts changed: {len(data['territories'])} territories, {len(specs)} indicators, {len(imported)} observations")
    check(len({(o["territory_id"], o["indicator_id"], o["period"]) for o in imported}) == len(imported),
          "Duplicate adopted observation")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {"selected_tables": list(SELECTED), "original_sha256": {k: by_id[k]["sha256"] for k in SELECTED},
             "source_table_rows": {"909-02": [7, 91], "910-02": [7, 1431], "912-01": [8, 82],
                                   "913-01": [10, 84], "915-01": [9, 83]},
             "source_name_aliases": ALIASES, "top_level_rows": list(TOP_ROWS),
             "checks": ["all nine population fields: sex, urban/rural, child and national subtotals",
                        "all 18 age groups: sex, urban/rural and matching 909-02 totals",
                        "all education fields: category and sex totals, 10+ vs age table",
                        "all labour fields: status and sex totals, 15+ vs age table",
                        "all household fields: size categories, urban/rural, average size and resident subset"],
             "adopted_indicator_ids": [PREFIX+s[0] for s in specs], "adopted_observations": len(imported),
             "unassessed_originals": sorted(set(by_id)-set(SELECTED)),
             "warning": "Numeric mechanics for all 48 originals are inventoried, but semantic adoption is completed for five selected tables only. Official codes and polygons are unverified."}
    (project / "evidence/GEO_GEOSTAT2024_FIVE_TABLE_ADOPTION_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": len(data["territories"]), "top_level": len(TOP_ROWS),
                      "tbilisi_districts": 10, "other_municipalities": 63,
                      "indicators": len(specs), "observations": len(imported),
                      "national_census_population": pop[7]["values"][0]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

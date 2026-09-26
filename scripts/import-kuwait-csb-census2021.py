"""Import audited fields from eight pinned CSB registration-census tables.

All selected table numeric cells are inventoried and reconciled. Adoption is a
smaller, explicitly named subset; the rest are retained in private field audit.
"""

import argparse
import json
import re
import runpy
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


manifest = runpy.run_path(str(Path(__file__).with_name("fetch-kuwait-csb-census2021.py")))
TABLES, digest, source_url = manifest["TABLES"], manifest["digest"], manifest["source_url"]
PREFIX = "KWT_CSB21_"
AREA_NAMES = ["The Capital Governorate", "Hawalli Governorate", "Al-Ahmadi Governorate",
              "Al-Jahra Governorate", "Al-Farwaniya Governorate", "Mubarak Al-Kabeer Governorate",
              "Not Stated", "Total"]
AREA_IDS = ["KWT:CSB2021:GOV:CAPITAL", "KWT:CSB2021:GOV:HAWALLI",
            "KWT:CSB2021:GOV:AL-AHMADI", "KWT:CSB2021:GOV:AL-JAHRA",
            "KWT:CSB2021:GOV:AL-FARWANIYA", "KWT:CSB2021:GOV:MUBARAK-AL-KABEER",
            "KWT:CSB2021:GEOGRAPHY-NOT-STATED", "KWT"]
AREA_GROUP_COUNTS = [33, 17, 41, 33, 20, 13]
AGE_LABELS = [f"{n}-{n+4}" for n in range(0, 85, 5)] + ["> 84"]
TABLE_NAMES = {1: "Population by governorate, nationality and sex",
               2: "Population by governorate, age and sex",
               10: "Population aged 10+ by governorate, educational status and sex",
               22: "Economically active population aged 15+ by governorate, nationality group and sex",
               26: "Population aged 15+ by governorate, work status and sex",
               42: "People with disabilities by governorate, age and sex",
               51: "Population habitually residing by Area, total count",
               52: "Population habitually residing by Area, nationality and sex"}


def cell(ws, row, col):
    value = ws.cell(row, col).value
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected nonnegative integer in Table sheet {ws.title} {row}:{col}; got {value!r}")
    return value


def check(condition, message):
    if not condition:
        raise ValueError(message)


def same_name(actual, expected):
    return isinstance(actual, str) and " ".join(actual.split()) == expected


def source_id(table):
    return f"kwt-csb-registration2021-table{table}"


def local_id(name):
    return "KWT:CSB2021:AREA:" + re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]+", "-", name.upper())).strip("-")


def group_table(ws, table, start, first_col, categories, header_row, header_first_col, area_label_col):
    expected = [ws.cell(header_row, header_first_col + j).value for j in range(categories)]
    check(all(isinstance(x, str) and x.strip() for x in expected), f"Table {table} headers changed")
    rows = []
    for i, (name, aid) in enumerate(zip(AREA_NAMES, AREA_IDS)):
        base = start + 3*i
        check(same_name(ws.cell(base, area_label_col).value, name), f"Table {table} area order at row {base}")
        record = {"area_id": aid, "area": name, "source_rows": [base, base+1, base+2],
                  "columns": expected, "male": [], "female": [], "total": []}
        for category in range(categories):
            col = first_col + category
            male, female, total = [cell(ws, base+sex, col) for sex in range(3)]
            check(male + female == total, f"Table {table} sex subtotal {name}/{expected[category]}")
            for key, value in (("male", male), ("female", female), ("total", total)):
                record[key].append(value)
        for sex in ("male", "female", "total"):
            check(sum(record[sex][:-1]) == record[sex][-1], f"Table {table} category sum {name}/{sex}")
        rows.append(record)
    for sex in ("male", "female", "total"):
        for j in range(categories):
            check(sum(row[sex][j] for row in rows[:7]) == rows[7][sex][j],
                  f"Table {table} national reconciliation {sex}/{j}")
    return rows


def parse_tables(raw):
    sheets = {}
    for table, (_, expected_xlsx, expected_pdf) in TABLES.items():
        for ext, expected in (("xlsx", expected_xlsx), ("pdf", expected_pdf)):
            path = raw / f"CSB_2021_Census_Table{table}.{ext}"
            check(path.exists() and digest(path) == expected, f"Missing/changed Table {table} {ext}")
        sheets[table] = load_workbook(raw / f"CSB_2021_Census_Table{table}.xlsx", read_only=False, data_only=True).active
    t1 = sheets[1]
    check([t1.cell(16, c).value for c in range(3, 12)] == ["Male", "Female", "Total"]*3,
          "Table 1 nine headers changed")
    pop = []
    for i, (name, aid) in enumerate(zip(AREA_NAMES, AREA_IDS)):
        row = 17+i
        check(same_name(t1.cell(row, 12).value, name), f"Table 1 area order at row {row}")
        values = [cell(t1, row, c) for c in range(3, 12)]
        check(all(values[j] + values[j+1] == values[j+2] for j in (0, 3, 6)), f"Table 1 sex subtotals {name}")
        check(all(values[j] + values[j+3] == values[j+6] for j in range(3)), f"Table 1 nationality subtotals {name}")
        pop.append({"area_id": aid, "area": name, "source_row": row,
                    "columns": ["Kuwaiti male", "Kuwaiti female", "Kuwaiti total", "Non-Kuwaiti male",
                                "Non-Kuwaiti female", "Non-Kuwaiti total", "All male", "All female", "All total"],
                    "values": values})
    for col in range(9):
        check(sum(row["values"][col] for row in pop[:7]) == pop[7]["values"][col],
              f"Table 1 national reconciliation column {col}")
    check(pop[7]["values"][8] == 4385717 and pop[6]["values"][8] == 4578,
          "Pinned national population or geography-not-stated residual changed")

    t2 = sheets[2]
    check([t2.cell(14, c).value for c in range(4, 12)] == AREA_NAMES, "Table 2 area headers changed")
    age = []
    for index, age_label in enumerate(AGE_LABELS):
        base = 15 + 3*index
        check(t2.cell(base, 13).value == age_label, f"Table 2 age label at {base}")
        item = {"age": age_label, "source_rows": [base, base+1, base+2], "areas": {}}
        for i, aid in enumerate(AREA_IDS):
            values = [cell(t2, base+sex, 4+i) for sex in range(3)]
            check(values[0]+values[1] == values[2], f"Table 2 age-sex sum {age_label}/{aid}")
            item["areas"][aid] = values
        for sex in range(3):
            check(sum(item["areas"][aid][sex] for aid in AREA_IDS[:7]) == item["areas"]["KWT"][sex],
                  f"Table 2 age national {age_label}/{sex}")
        age.append(item)
    for i, aid in enumerate(AREA_IDS):
        for sex in range(3):
            total = cell(t2, 69+sex, 4+i)
            check(sum(item["areas"][aid][sex] for item in age) == total, f"Table 2 age total {aid}/{sex}")
            check(total == pop[i]["values"][6+sex], f"Table 2 vs Table 1 {aid}/{sex}")
    t10 = group_table(sheets[10], 10, 14, 4, 10, 13, 4, 15)
    t22 = group_table(sheets[22], 22, 13, 3, 9, 12, 3, 13)
    t26 = group_table(sheets[26], 26, 14, 3, 9, 13, 3, 13)
    check(t10[7]["total"][-1] == 3812160, "Pinned education universe changed")
    check(t22[7]["total"][-1] == 2570091 and t26[7]["total"][-1] == 3525872,
          "Pinned work universes changed")
    for a, b in zip(t22, t26):
        for sex in ("male", "female", "total"):
            check(a[sex][-1] == sum(b[sex][:4]), f"Economically active definition differs {a['area']}/{sex}")

    t42 = sheets[42]
    check([t42.cell(14, 2+3*i).value for i in range(8)] == AREA_NAMES,
          "Table 42 area headers changed")
    disability = []
    for index, age_label in enumerate(AGE_LABELS):
        row = 17+index
        check(t42.cell(row, 26).value == age_label, f"Table 42 age label {row}")
        item = {"age": age_label, "source_row": row, "areas": {}}
        for i, aid in enumerate(AREA_IDS):
            values = [cell(t42, row, 2+3*i+sex) for sex in range(3)]
            check(values[0]+values[1] == values[2], f"Table 42 sex subtotal {aid}/{age_label}")
            item["areas"][aid] = values
        for sex in range(3):
            check(sum(item["areas"][aid][sex] for aid in AREA_IDS[:7]) == item["areas"]["KWT"][sex],
                  f"Table 42 national {age_label}/{sex}")
        disability.append(item)
    disability_totals = []
    for i, aid in enumerate(AREA_IDS):
        values = [cell(t42, 35, 2+3*i+sex) for sex in range(3)]
        check(values[0]+values[1] == values[2], f"Table 42 total sexes {aid}")
        for sex in range(3):
            check(sum(item["areas"][aid][sex] for item in disability) == values[sex],
                  f"Table 42 ages vs total {aid}/{sex}")
        disability_totals.append(values)
    check(disability_totals[-1][2] == 55232, "Pinned disability total changed")
    t51, t52 = sheets[51], sheets[52]
    check(t51.cell(8, 1).value == "Total population by habitual residence status (Area)" and
          t52.cell(8, 1).value == "Population habitually residing (area) by nationality and gender",
          "Area table title or population scope changed")
    check([t52.cell(15, c).value for c in range(2, 11)] == ["Male", "Female", "Total"]*3,
          "Table 52 nine headers changed")
    local_areas = []
    for index in range(sum(AREA_GROUP_COUNTS)):
        row51, row52 = 12+index, 16+index
        name = t51.cell(row51, 3).value
        check(isinstance(name, str) and name and name == t52.cell(row52, 11).value,
              f"Tables 51/52 Area name/order at {row51}/{row52}")
        values = [cell(t52, row52, col) for col in range(2, 11)]
        check(cell(t51, row51, 2) == values[8], f"Tables 51/52 Area total {name}")
        check(all(values[j]+values[j+1] == values[j+2] for j in (0, 3, 6)) and
              all(values[j]+values[j+3] == values[j+6] for j in range(3)),
              f"Table 52 sex/nationality subtotals {name}")
        local_areas.append({"id": local_id(name), "name": name, "row51": row51,
                            "row52": row52, "values": values})
    check(len(local_areas) == 157 and len({r["id"] for r in local_areas}) == 157,
          "Table 52 Area identity or uniqueness changed")
    offset = 0
    for gov_index, count in enumerate(AREA_GROUP_COUNTS):
        group = local_areas[offset:offset+count]
        for col in range(9):
            check(sum(row["values"][col] for row in group) == pop[gov_index]["values"][col],
                  f"Tables 52→1 Area block vs governorate {AREA_NAMES[gov_index]} column {col}")
        for row in group:
            row["inferred_governorate_id"] = AREA_IDS[gov_index]
        offset += count
    check(offset == 157, "Orphan Area row")
    for source_row51, source_row52, pop_index in ((169, 173, 6), (170, 174, 7)):
        check(t51.cell(source_row51, 3).value == t52.cell(source_row52, 11).value and
              cell(t51, source_row51, 2) == pop[pop_index]["values"][8],
              "Area tables residual/national name or total changed")
        for col in range(9):
            check(cell(t52, source_row52, 2+col) == pop[pop_index]["values"][col],
                  f"Table 52 residual/national vs Table 1 column {col}")
    return {"population": pop, "age": age, "education": t10,
            "labour_force": t22, "work_status": t26, "disability_age": disability,
            "disability_totals": disability_totals, "local_areas": local_areas,
            "area_group_counts": AREA_GROUP_COUNTS}


def main(project):
    raw = project / "raw" / "official"
    parsed = parse_tables(raw)
    path = project / "data" / "dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    check(data["country"]["id"] == "KWT", "Expected Kuwait project")
    data["sources"] = [s for s in data["sources"] if not s["id"].startswith("kwt-csb-") and
                       s["id"] not in ("kwt-baladia-municipal-law", "kwt-scpd-plan-archive")]
    data["indicators"] = [i for i in data["indicators"] if not i["id"].startswith(PREFIX)]
    data["observations"] = [o for o in data["observations"] if not o["indicator_id"].startswith(PREFIX)]
    data["territories"] = [t for t in data["territories"] if t["id"] == "KWT"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["country"]["geography_note"] = (
        "The 2021 CSB/PACI registration census reports six governorates, a distinct geography-not-stated residual "
        "of 4,578 people, and a directly reported national total of 4,385,717. Tables 51/52 add 157 named "
        "Area rows; their six contiguous source blocks reconcile to all nine published governorate columns, "
        "but official Area codes and parent geography remain to be independently confirmed. The six governorates "
        "alone are incomplete national geographic coverage. No official code or year-compatible polygon is reconciled; "
        "the six geoBoundaries reference shapes remain unjoined. Registration census, annual estimates and WDI "
        "midyear estimates have distinct populations and methods.")
    data["territories"][0]["source_id"] = source_id(1)
    data["territories"][0]["reconciliation_status"] = "CSB Table 1 direct national registration total including unassigned geography"
    for i in range(7):
        data["territories"].append({"id": AREA_IDS[i], "name": AREA_NAMES[i],
            "level": "csb_governorate" if i < 6 else "csb_geography_not_stated",
            "type": "CSB 2021 registration-census governorate" if i < 6 else "CSB geography-not-stated reporting residual",
            "parent_id": "KWT", "official_code": None,
            "code_system": "CSB 2021 Table 1 source name; official code unverified", "boundary_version": None,
            "source_id": source_id(1),
            "reconciliation_status": "Direct census reporting row; official code, polygon and legal planning unit unverified"})
    data["analysis"]["comparisons"] = [{"parent_id": "KWT", "member_ids": AREA_IDS[:6],
        "label": "Six CSB 2021 registration-census governorates",
        "source_ids": [source_id(n) for n in TABLES],
        "membership_note": "Six governorate rows exclude 4,578 geography-not-stated people; these members are NOT complete national population coverage. National is a direct reported row, never a governorate sum. Same source/year fields are comparable within their individual universe."}]
    data["analysis"]["terminal_territory_ids"] = [AREA_IDS[6]] + [r["id"] for r in parsed["local_areas"]]
    data["analysis"]["default_indicator_id"] = PREFIX + "POP_TOTAL"
    data["analysis"]["latest_values_only"] = True
    data["analysis"].pop("population_context", None)
    for gov_index, count in enumerate(AREA_GROUP_COUNTS):
        members = [r for r in parsed["local_areas"] if r["inferred_governorate_id"] == AREA_IDS[gov_index]]
        check(len(members) == count, "Area group count changed")
        data["analysis"]["comparisons"].append({"parent_id": AREA_IDS[gov_index],
            "member_ids": [r["id"] for r in members],
            "label": f"CSB 2021 Area rows matching {AREA_NAMES[gov_index]}",
            "source_ids": [source_id(1), source_id(51), source_id(52)],
            "membership_note": f"Tables 51/52 list {count} contiguous Area rows in this block; all nine Table 52 nationality/sex columns sum exactly to this Table 1 governorate row. This is a source-table reconciliation, not verified official Area codes, polygons or legal plan-making units."})
    for row in parsed["local_areas"]:
        data["territories"].append({"id": row["id"], "name": row["name"],
            "level": "csb_area", "type": "CSB 2021 Area reporting unit",
            "parent_id": row["inferred_governorate_id"], "official_code": None,
            "code_system": "CSB 2021 Table 52 source name; code unverified",
            "boundary_version": None, "source_id": source_id(52),
            "reconciliation_status": "Parent inferred from contiguous source block and nine-column subtotal; current administrative identity and polygon unverified"})

    # Each adopted indicator states its source universe. All parent aggregation is disabled.
    specs = [
        ("POP_TOTAL", "Registered census population", 1, "people", "All people counted in CSB/PACI 2021 registration census", "source_reported", 0),
        ("POP_KUWAITI", "Registered Kuwaiti population", 1, "people", "Kuwaiti people counted in the registration census", "source_reported", 0),
        ("POP_NONKUWAITI", "Registered non-Kuwaiti population", 1, "people", "Non-Kuwaiti people counted within this census definition; excluded categories are stated by CSB", "source_reported", 0),
        ("POP_MALE", "Registered male population", 1, "people", "All male people counted in the registration census", "source_reported", 0),
        ("POP_FEMALE", "Registered female population", 1, "people", "All female people counted in the registration census", "source_reported", 0),
        ("AGE_0_14", "Registered population aged 0–14", 2, "people", "All census people in age groups 0–4, 5–9, 10–14", "areadata_calculated", 0),
        ("AGE_15_64", "Registered population aged 15–64", 2, "people", "All census people in ten five-year age groups 15–19 through 60–64", "areadata_calculated", 0),
        ("AGE_65_PLUS", "Registered population aged 65+", 2, "people", "All census people in five groups 65–69 through over 84", "areadata_calculated", 0),
        ("EDU_10PLUS_TOTAL", "Population aged 10+ in education table", 10, "people", "Registered people aged 10+; includes education status not stated", "source_reported", 0),
        ("EDU_10PLUS_ILLITERATE", "Illiterate population aged 10+", 10, "people", "CSB educational-status category Illiterate among registered people aged 10+", "source_reported", 0),
        ("EDU_10PLUS_UNIVERSITY", "University education, population aged 10+", 10, "people", "CSB educational-status category University; excludes Above University", "source_reported", 0),
        ("EDU_10PLUS_NOT_STATED", "Education not stated, population aged 10+", 10, "people", "CSB educational-status category Not Stated", "source_reported", 0),
        ("LABOUR_15PLUS", "Economically active population aged 15+", 22, "people", "CSB labour force: government, non-government, domestic workers and unemployed", "source_reported", 0),
        ("AGE_15PLUS_WORK_TABLE", "Population aged 15+ in work-status table", 26, "people", "All registered people aged 15+ in CSB work-status table including status not stated", "source_reported", 0),
        ("UNEMPLOYED_15PLUS", "Unemployed people aged 15+", 26, "people", "CSB work-status category Unemployed", "source_reported", 0),
        ("UNEMPLOYMENT_RATE", "Unemployment share of census labour force", 26, "%", "100 × Table 26 unemployed divided by Table 22 economically active in the same census area; verified category reconciliation", "areadata_calculated", 2),
        ("DISABILITY_TOTAL", "Registered people with disabilities", 42, "people", "CSB count of people with disabilities across all 18 reported age groups", "source_reported", 0),
    ]
    for suffix, name, table, unit, universe, method, decimals in specs:
        data["indicators"].append({"id": PREFIX + suffix, "name": name,
            "theme": {1: "Population", 2: "Population", 10: "Education", 22: "Labour", 26: "Labour", 42: "Disability"}[table],
            "unit": unit, "definition": name + ". " + universe + ". Period is the 2021 registration census, not a current estimate.",
            "population": universe, "source_id": source_id(table), "aggregation": "none",
            "measurement_method": method, "display_decimals": decimals})

    def emit(aid, suffix, value, table, locator, calculated=None):
        obs = {"territory_id": aid, "indicator_id": PREFIX + suffix, "period": "2021",
               "value": value, "status": "observed", "source_id": source_id(table),
               "measurement_method": "areadata_calculated" if calculated else "source_reported",
               "source_locator": f"CSB Registration Census 2021, Table {table}, XLSX Sheet1 {locator}"}
        if calculated:
            obs.update({"provenance": "calculated", "footnote": calculated})
        data["observations"].append(obs)

    for i, aid in enumerate(AREA_IDS):
        p = parsed["population"][i]
        for suffix, index, label in (("POP_TOTAL", 8, "all total"), ("POP_KUWAITI", 2, "Kuwaiti total"),
                                     ("POP_NONKUWAITI", 5, "non-Kuwaiti total"),
                                     ("POP_MALE", 6, "all male"), ("POP_FEMALE", 7, "all female")):
            emit(aid, suffix, p["values"][index], 1, f"row {p['source_row']}, {p['area']}, {label}")
        for suffix, lo, hi in (("AGE_0_14", 0, 3), ("AGE_15_64", 3, 13), ("AGE_65_PLUS", 13, 18)):
            groups = parsed["age"][lo:hi]
            value = sum(g["areas"][aid][2] for g in groups)
            emit(aid, suffix, value, 2, f"rows {groups[0]['source_rows'][2]}–{groups[-1]['source_rows'][2]}, {p['area']}, total sex",
                 f"AreaData sum of {len(groups)} non-overlapping five-year age groups in Table 2; "
                 f"all 18 age groups sum to the Table 1 population total for {p['area']}.")
        e = parsed["education"][i]
        for suffix, index in (("EDU_10PLUS_TOTAL", 9), ("EDU_10PLUS_ILLITERATE", 0),
                              ("EDU_10PLUS_UNIVERSITY", 6), ("EDU_10PLUS_NOT_STATED", 8)):
            emit(aid, suffix, e["total"][index], 10,
                 f"row {e['source_rows'][2]}, {p['area']}, {e['columns'][index]}")
        l = parsed["labour_force"][i]
        emit(aid, "LABOUR_15PLUS", l["total"][-1], 22,
             f"row {l['source_rows'][2]}, {p['area']}, total economically active")
        w = parsed["work_status"][i]
        emit(aid, "AGE_15PLUS_WORK_TABLE", w["total"][-1], 26,
             f"row {w['source_rows'][2]}, {p['area']}, age 15+ total")
        emit(aid, "UNEMPLOYED_15PLUS", w["total"][3], 26,
             f"row {w['source_rows'][2]}, {p['area']}, unemployed")
        denominator = l["total"][-1]
        check(denominator > 0, f"Zero labour-force denominator: {aid}")
        rate = round(100 * w["total"][3] / denominator, 2)
        emit(aid, "UNEMPLOYMENT_RATE", rate, 26,
             f"Table 26 row {w['source_rows'][2]} unemployed / Table 22 row {l['source_rows'][2]} labour-force total, {p['area']}",
             f"AreaData: 100 × {w['total'][3]:,} unemployed / {denominator:,} economically active = {rate:.2f}%. "
             "Table 22 total matches Table 26 four active-work categories in the same area.")
        emit(aid, "DISABILITY_TOTAL", parsed["disability_totals"][i][2], 42,
             f"row 35, {p['area']}, total both sexes")
    for row in parsed["local_areas"]:
        for suffix, index, label in (("POP_TOTAL", 8, "all total"), ("POP_KUWAITI", 2, "Kuwaiti total"),
                                     ("POP_NONKUWAITI", 5, "non-Kuwaiti total"),
                                     ("POP_MALE", 6, "all male"), ("POP_FEMALE", 7, "all female")):
            emit(row["id"], suffix, row["values"][index], 52,
                 f"row {row['row52']}, Area {row['name']}, {label}; Table 51 row {row['row51']} total cross-check")

    for table, (st_id, xlsx_sha, pdf_sha) in TABLES.items():
        raw_xlsx = raw / f"CSB_2021_Census_Table{table}.xlsx"
        data["sources"].append({"id": source_id(table),
            "name": f"CSB Registration Census 2021 Table {table}: {TABLE_NAMES[table]}",
            "url": source_url(st_id, "xlsx"), "publisher": "Central Statistical Bureau of Kuwait; data source Public Authority for Civil Information",
            "reference_period": "2021 registration census (CSB catalog separately lists 1 January 2022 status)",
            "geographic_level": "six governorates, geography not stated, national",
            "status": "partial", "license": "terms_review_required",
            "raw_path": f"raw/official/CSB_2021_Census_Table{table}.xlsx", "sha256": xlsx_sha,
            "raw_files": [{"url": source_url(st_id, "xlsx"), "raw_path": f"raw/official/CSB_2021_Census_Table{table}.xlsx", "sha256": xlsx_sha},
                          {"url": source_url(st_id, "pdf"), "raw_path": f"raw/official/CSB_2021_Census_Table{table}.pdf", "sha256": pdf_sha}],
            "retrieved_at": datetime.fromtimestamp(raw_xlsx.stat().st_mtime, timezone.utc).isoformat(),
            "note": "Pinned XLSX and official PDF verified. All numeric cells in the selected table audited; only named indicators adopted. Census scope excludes some non-Kuwaiti categories according to CSB. Other census tables remain unassessed."})
    for ident, name, url, geography, note in [
        ("kwt-csb-census-catalog", "CSB 2021 census tables catalog", "https://census.csb.gov.kw/CensusData_EN?CatID=1", "national and governorate", "Official catalog located; other census tables not yet audited/adopted."),
        ("kwt-csb-2011-geography", "CSB 2011 Census administrative division and GIS portal", "https://gis.csb.gov.kw/media/pdf/1_Chapter1_Administrative_Division_of_Kuwait.pdf", "2011 governorates and localities", "Historical geography source only; 2021 code and polygons unverified."),
        ("kwt-baladia-municipal-law", "Kuwait Municipality legal catalog, Municipal Law 33/2016", "https://www.baladia.gov.kw/sites/ar/municipalityServices/Lists/SubLows/DispForm.aspx?ID=1", "national municipal law", "Law location only; full operative text, powers and local plan maker not audited."),
        ("kwt-scpd-plan-archive", "Supreme Council for Planning and Development plan archive", "https://scpd.gov.kw/archive/plan%2021-2022.pdf", "national historic annual plan", "Historical plan location only; current plan and governorate applicability unverified."),
    ]:
        data["sources"].append({"id": ident, "name": name, "url": url,
            "publisher": "Government of Kuwait", "reference_period": "catalog checked 2026-09-26",
            "geographic_level": geography, "status": "not_collected", "license": "terms_review_required",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "note": note})
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    ("subnational_statistics", "boundary_reconciliation", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Eight selected CSB 2021 registration-census tables yield population by nationality/sex for 157 Area rows and population, age, education, labour and disability fields for six governorates, unassigned geography and national. The wider census catalog and later series remain unassessed; source universe excludes stated non-Kuwaiti categories.",
         "next_action": "Inventory all census catalog tables and later official governorate statistical series; assess each numeric field, definition and adoption."},
        {"category": "boundary_reconciliation", "status": "not_collected",
         "detail": "CSB governorate and 157 Area reporting names have no verified official codes or 2021-compatible polygons. Area-to-governorate membership is inferred from source row order plus exact nine-column subtotals, not confirmed by a code crosswalk. The 2011 official GIS report and six geoBoundaries shapes are unjoined.",
         "next_action": "Acquire official 2021/current Area and governorate codes and boundary edition; independently confirm each Area parent and local planning unit."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "Municipal-law and national-plan catalog locations identified but no operative legal text or actual local plan, decision, fiscal execution or evaluation adopted.",
         "next_action": "Audit current law/plan-making bodies and full plans for contrasting governorates and municipalities before assigning plan status."},
    ]
    data["collection"]["adapters"] = sorted(set([a for a in data["collection"]["adapters"]
                                                  if a != "kuwait-csb-registration-census2021-six-table-partial-v1"] +
                                                  ["kuwait-csb-registration-census2021-eight-table-partial-v1"]))
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    imported = [o for o in data["observations"] if o["indicator_id"].startswith(PREFIX)]
    check(len(data["territories"]) == 165 and len({t["id"] for t in data["territories"]}) == 165,
          "CSB territory count/uniqueness changed")
    check(len(imported) == 921 and len({(o["territory_id"], o["indicator_id"], o["period"]) for o in imported}) == 921,
          "CSB imported observation count/uniqueness changed")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    audit = {"scope": "all numeric cells in eight selected tables; other catalog tables unassessed",
             "source_table_numbers": list(TABLES), "source_original_sha256":
             {str(n): {"xlsx": hashes[1], "pdf": hashes[2]} for n, hashes in TABLES.items()},
             "field_disposition": {"adopted": [x[0] for x in specs],
                                   "retained_unadopted": "all other source age/sex/nationality/education/work-status cells in source_rows",
                                   "not_assessed": "all other CSB census catalog tables"},
             "checks": ["all sex subtotals", "all source category subtotals", "national = six governorates + geography-not-stated for every numeric column", "Table 2 age-sex totals = Table 1", "Table 22 labour force = Table 26 four economically active statuses", "Table 42 age totals", "Table 51 Area totals = Table 52 Area totals", "six contiguous Table 52 Area blocks = Table 1 governorates in every nine numeric columns"],
             "source_rows": parsed, "adopted_observations": len(imported),
             "governorate_comparison_excludes_unassigned": 4578}
    (evidence / "KWT_CSB2021_EIGHT_TABLE_FIELD_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": 165, "governorates": 6, "area_reporting_units": 157, "unassigned_geography": 4578,
                      "indicators": len(specs), "observations": len(imported),
                      "national_population": 4385717, "labour_force": 2570091,
                      "disability_count": 55232}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

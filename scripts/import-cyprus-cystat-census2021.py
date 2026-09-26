"""Import a bounded, source-audited subset of Cyprus's final 2021 census.

The census covers government-controlled areas only. 2021 locality codes are
statistical geography and are not joined to current councils or polygons.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


HASHES = {
    "1891108E": "e7c9df59efa6e96994dd4f223ad3b8bd284848ed645d2c8b3e69a110618ab958",
    "1891161E": "c2de98df8ce554f10eed471befa0fa194cc44258a130dbb72fba0c5b8b2b6ddf",
    "1891164E": "d1c2f80c69d75a22e73621abaef26a2c32f7029d281df0d0411a3a762c9f5388",
    "1891213E": "1de1f16c680cd035452be1fef7a9cd8d35bad3c53dc37d0af2d287757f5e556a",
    "1891515E": "9d001491952641c29031a347126b316fcf2f5d5b0f54acf6deaebe2386a1f5d3",
    "1891712E": "b434c092f4640150e655c1901209bc63136f81c2b52dad2445e3270fbee3a17c",
    "1895114E": "3407a5221510e7e35d5a424a7d572a7ae85094aae055d6533e4371bf33df2311",
}
FINAL_RELEASE_HASH = "8748a4db1f53a7d11203deef6a53c126c996344b4217d789d1de99ed9d7037bd"
GEOCODES_2015_HASH = "500b4e39457d7edcf33cd7cef93e2df4db26cc5ea97761b0d53f597ef9a1398f"
DISTRICTS = {"1": "Lefkosia", "3": "Ammochostos", "4": "Larnaka", "5": "Lemesos", "6": "Pafos"}
PREFIX = "CYP_CYSTAT_"
SCOPE = "CYP:CYSTAT:CTRL2021"
METHOD = "CYSTAT_final_2021_census_usual_residents_government_controlled_area"
PERIOD = "2021-10-01"


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sid(table):
    return f"cyp-cystat-2021-{table.lower()}"


def tid(code):
    if code == "TOTAL" or code == "Total":
        return SCOPE
    if len(code) == 1:
        return f"CYP:CYSTAT:DIST:{code}"
    if len(code) == 4:
        return f"CYP:CYSTAT:LOC:{code}"
    if len(code) == 6:
        return f"CYP:CYSTAT:QTR:{code}"
    raise ValueError(f"Unexpected census geography code {code}")


class Matrix:
    def __init__(self, table, body):
        self.table = table
        self.body = body
        self.dimensions = [body["dimension"][key]["category"] for key in body["id"]]
        self.codes = list(self.dimensions[0]["index"])
        self.loc_index = self.dimensions[0]["index"]
        self.labels = self.dimensions[0]["label"]
        self.sizes = body["size"]
        self.values = body["value"]

    def cell(self, code, *others):
        keys = (code, *map(str, others))
        require(len(keys) == len(self.sizes), f"{self.table}: wrong coordinates {keys}")
        offset = 0
        for category, size, key in zip(self.dimensions, self.sizes, keys):
            offset = offset * size + category["index"][key]
        return self.values[offset]

    def all_cells(self, code):
        width = len(self.values) // len(self.codes)
        start = self.loc_index[code] * width
        return self.values[start:start + width]


def load_sources(project):
    inventory_path = project / "evidence/CYP_CYSTAT2021_SOURCE_INVENTORY.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    require(inventory["totals"]["directories"] == 12 and inventory["totals"]["tables"] == 46 and
            inventory["totals"]["selected_full_tables"] == 7 and
            inventory["totals"]["selected_cells"] == 49964 and
            inventory["totals"]["selected_numeric_cells"] == 49957,
            "Official census inventory changed")
    by_id = {row["id"][:-3]: row for row in inventory["selected_raw_tables"]}
    require(set(by_id) == set(HASHES), "Selected matrices changed")
    matrices = {}
    for table, expected in HASHES.items():
        row = by_id[table]
        file = project / row["raw_path"]
        require(digest(file) == row["sha256"] == expected, f"Raw {table} hash changed")
        request_file = project / row["request_path"]
        require(digest(request_file) == row["request_sha256"], f"Request {table} hash changed")
        matrices[table] = Matrix(table, json.loads(file.read_text(encoding="utf-8")))
    release = project / "raw/cystat/Census2021-Final_Results-EN-090824.pdf"
    require(digest(release) == FINAL_RELEASE_HASH, "Final census release changed")
    return inventory, by_id, matrices


def audit(m):
    pop, housing, quarters, citizenship, education, labour, sizes = (
        m[key] for key in HASHES)
    require({key: len(value.codes) for key, value in m.items()} == {
        "1891108E": 416, "1891161E": 410, "1891164E": 509,
        "1891213E": 402, "1891515E": 402, "1891712E": 402, "1895114E": 408},
        "Census location counts changed")
    pop_only = set(pop.codes) - set(housing.codes)
    require(len(pop_only) == 6 and all(pop.cell(code, 0, 0) == 0 for code in pop_only),
            "Six absent housing localities are no longer all zero population")
    require(set(housing.codes) <= set(pop.codes), "Housing geography codes changed")
    require(set(citizenship.codes) == set(education.codes) == set(labour.codes) and
            len(set(pop.codes) - set(citizenship.codes)) == 14 and
            all(pop.cell(code, 0, 0) == 0 for code in set(pop.codes) - set(citizenship.codes)),
            "Citizenship, education or labour geography cover changed")
    require(set(quarters.codes) - set(housing.codes) ==
            {code for code in quarters.codes if len(code) == 6} and
            set(housing.codes) <= set(quarters.codes), "Quarter code hierarchy changed")
    check_counts = Counter()

    def check_parent(table, field_coordinates):
        for district in DISTRICTS:
            children = [code for code in table.codes if len(code) == 4 and code.startswith(district)]
            require(children, f"{table.table}: no children for district {district}")
            for fields in field_coordinates:
                require(table.cell(district, *fields) == sum(table.cell(code, *fields) for code in children),
                        f"{table.table}: incomplete district {district}, {fields}")
                check_counts["district_field_sums"] += 1
        top = "Total" if table.table == "1895114E" else "TOTAL"
        for fields in field_coordinates:
            require(table.cell(top, *fields) == sum(table.cell(code, *fields) for code in DISTRICTS),
                    f"{table.table}: incomplete national cover, {fields}")
            check_counts["coverage_field_sums"] += 1

    for code in pop.codes:
        for age in range(18):
            require(pop.cell(code, 0, age) == pop.cell(code, 1, age) + pop.cell(code, 2, age),
                    f"Population sex sum: {code}, {age}")
            check_counts["population_sex"] += 1
        for sex in range(3):
            require(pop.cell(code, sex, 0) == sum(pop.cell(code, sex, age) for age in range(1, 18)),
                    f"Population age sum: {code}, {sex}")
            check_counts["population_age"] += 1
    check_parent(pop, [(sex, age) for sex in range(3) for age in range(18)])
    require(pop.cell("TOTAL", 0, 0) == 923381 and pop.cell("TOTAL", 1, 0) == 449708 and
            pop.cell("TOTAL", 2, 0) == 473673 and
            {code: pop.cell(code, 0, 0) for code in DISTRICTS} ==
            {"1": 350035, "3": 54318, "4": 155765, "5": 262157, "6": 101106},
            "Census release population cross-check failed")
    for code in housing.codes:
        row = housing.all_cells(code)
        require(row[0] == row[1] + row[2] and row[7] == row[4] + row[6] and
                row[7] == pop.cell(code, 0, 0) and row == quarters.all_cells(code),
                f"Housing/population/quarter overlap conflict: {code}")
        check_counts["housing_overlap"] += 1
    check_parent(housing, [(field,) for field in range(8)])
    require(housing.all_cells("TOTAL") == [492931, 354818, 138113, 357858, 917953, 231, 5428, 923381],
            "Census release housing/household cross-check failed")
    qchildren = defaultdict(list)
    for code in quarters.codes:
        if len(code) == 6:
            qchildren[code[:4]].append(code)
    require(len(qchildren) == 18 and sum(map(len, qchildren.values())) == 99,
            "Quarter parent/count changed")
    for parent, children in qchildren.items():
        for field in range(8):
            require(quarters.cell(parent, field) == sum(quarters.cell(code, field) for code in children),
                    f"Quarter parent conflict: {parent}, {field}")
            check_counts["quarter_field_sums"] += 1
    for code in citizenship.codes:
        for sex in range(3):
            require(citizenship.cell(code, 0, sex) ==
                    sum(citizenship.cell(code, group, sex) for group in range(1, 5)),
                    f"Citizenship categories: {code}")
        for group in range(5):
            require(citizenship.cell(code, group, 0) ==
                    citizenship.cell(code, group, 1) + citizenship.cell(code, group, 2),
                    f"Citizenship sex: {code}")
        require(citizenship.cell(code, 0, 0) == pop.cell(code, 0, 0),
                f"Citizenship population conflict: {code}")
        check_counts["citizenship_rows"] += 1
    check_parent(citizenship, [(group, sex) for group in range(5) for sex in range(3)])
    for code in education.codes:
        age15 = sum(pop.cell(code, 0, age) for age in range(4, 18))
        require(education.cell(code, 0, 0) == age15, f"Education age15+ mismatch: {code}")
        for sex in range(3):
            require(education.cell(code, sex, 0) ==
                    sum(education.cell(code, sex, category) for category in range(1, 7)),
                    f"Education categories: {code}")
        for category in range(7):
            require(education.cell(code, 0, category) ==
                    education.cell(code, 1, category) + education.cell(code, 2, category),
                    f"Education sex: {code}")
        check_counts["education_rows"] += 1
    check_parent(education, [(sex, category) for sex in range(3) for category in range(7)])
    for code in labour.codes:
        row = labour.all_cells(code)
        require(row[0] == row[1] + row[4] + row[5] and row[1] == row[2] + row[3] and
                row[0] == education.cell(code, 0, 0), f"Labour decomposition: {code}")
        check_counts["labour_rows"] += 1
    check_parent(labour, [(field,) for field in range(6)])
    require(labour.cell("TOTAL", 0) == 780770, "Final age15+ total changed")
    require(set(sizes.codes) - set(pop.codes) == {"Total"} and
            all(code in pop.codes for code in sizes.codes if code != "Total"),
            "Household-size codes changed")
    missing_averages = []
    for code in sizes.codes:
        row = sizes.all_cells(code)
        require(row[0] == sum(row[1:7]), f"Household size categories: {code}")
        if row[7] is None:
            require(row[0] == 0, f"Average household size missing despite households: {code}")
            missing_averages.append(code)
        else:
            require(isinstance(row[7], (int, float)) and row[7] >= 1,
                    f"Invalid average household size: {code}")
        other_code = "TOTAL" if code == "Total" else code
        if other_code in housing.codes:
            require(row[0] == housing.cell(other_code, 3), f"Household total conflict: {code}")
        check_counts["household_size_rows"] += 1
    check_parent(sizes, [(field,) for field in range(7)])  # averages are not additive
    require(len(missing_averages) == 7 and sizes.cell("Total", 0) == 357858 and
            sizes.cell("Total", 7) == 2.57, "Household-size release cross-check failed")
    return {"checks": dict(check_counts), "population_only_zero_localities": sorted(pop_only),
            "social_table_omitted_zero_population_localities": sorted(set(pop.codes) - set(citizenship.codes)),
            "quarter_parent_count": len(qchildren), "quarter_count": 99,
            "household_average_not_applicable_codes": missing_averages,
            "quarter_parents": {code: len(children) for code, children in qchildren.items()}}


def write_field_inventory(project, m):
    path = project / "evidence/INDICATOR_INVENTORY.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_id", "source_hash", "table", "variable_coordinates", "original_label",
                         "unit", "universe", "period", "geography_type", "role", "indicator_id",
                         "decision", "reason", "locator"])
        for table, matrix in m.items():
            categories = matrix.dimensions[1:]
            def recurse(depth, coords, labels):
                if depth == len(categories):
                    role = "supporting_or_duplicate"
                    decision = "priority_unassessed"
                    indicator_id = ""
                    if table == "1891108E":
                        sex, age = coords
                        if age == "0" and sex in {"0", "1", "2"}:
                            role, decision = "direct_count", "adopted"
                            indicator_id = PREFIX + {"0": "POP_TOTAL", "1": "POP_MALE", "2": "POP_FEMALE"}[sex]
                        elif sex == "0" and age != "0":
                            role, decision = "broad_age_component", "auxiliary_adopted"
                            age_number = int(age)
                            indicator_id = PREFIX + ("POP_0_14" if age_number <= 3 else
                                                     "POP_15_64" if age_number <= 13 else "POP_65_PLUS")
                    elif table in {"1891161E", "1891164E"}:
                        field = int(coords[0])
                        if field < 7:
                            role, decision = "direct_count", (
                                "adopted_quarters_only" if table == "1891164E" else "adopted")
                            indicator_id = PREFIX + (
                                "HOUSING_TOTAL", "HOUSING_USUAL", "HOUSING_VACANT_TEMP",
                                "HOUSEHOLDS", "HOUSEHOLD_POP", "INSTITUTIONS", "INSTITUTION_POP"
                            )[field]
                        elif table == "1891164E":
                            role, decision, indicator_id = "quarter_population", "adopted_quarters_only", PREFIX + "POP_TOTAL"
                        else:
                            role, decision = "duplicate_population_check", "cross_check_only"
                    elif table == "1891213E":
                        group, sex = coords
                        if group in {"1", "2", "3", "4"} and sex == "0":
                            role, decision = "direct_citizenship_count", "adopted"
                            indicator_id = PREFIX + {"1": "CIT_CYPRIOT", "2": "CIT_OTHER_EU",
                                                     "3": "CIT_NON_EU", "4": "CIT_NOT_STATED"}[group]
                        elif group == "0":
                            role, decision = "population_duplicate", "cross_check_only"
                    elif table == "1891515E":
                        sex, category = coords
                        if sex == "0" and category in {"0", "1", "5"}:
                            role, decision = "direct_education_count", "adopted"
                            indicator_id = PREFIX + {"0": "EDU_15PLUS", "1": "EDU_UPTO_LOWER",
                                                     "5": "EDU_UNIVERSITY"}[category]
                    elif table == "1891712E":
                        if coords[0] in {"1", "2", "3", "4"}:
                            role, decision = "direct_labour_count", "adopted"
                            indicator_id = PREFIX + {"1": "LAB_ACTIVE", "2": "LAB_EMPLOYED",
                                                     "3": "LAB_UNEMPLOYED", "4": "LAB_INACTIVE"}[coords[0]]
                        elif coords[0] == "0":
                            role, decision = "age15_population_duplicate", "cross_check_only"
                    elif table == "1895114E":
                        if coords[0] in {"1", "6", "7"}:
                            role, decision = "direct_household_size", "adopted"
                            indicator_id = PREFIX + {"1": "HH_ONE_PERSON", "6": "HH_SIX_PLUS",
                                                     "7": "HH_AVG_SIZE"}[coords[0]]
                        elif coords[0] == "0":
                            role, decision = "households_duplicate", "cross_check_only"
                    writer.writerow([sid(table), HASHES[table], table, "/".join(coords),
                        " / ".join(labels), "households" if table == "1895114E" and coords[0] != "7"
                        else "persons per household" if table == "1895114E"
                        else "persons" if table in {"1891108E", "1891213E", "1891515E", "1891712E"}
                        else ("housing units" if coords[0] in {"0", "1", "2"} else
                              "households" if coords[0] == "3" else
                              "persons" if coords[0] in {"4", "6", "7"} else "institutions"),
                        "2021 census government-controlled areas",
                        PERIOD, "district / 2021 census locality / quarter depending on table", role,
                        indicator_id, decision,
                        "Some source columns are held for semantic and geographic review; source rows remain in raw archive.",
                        f"{table}: dimension codes {'/'.join(coords)}"])
                    return
                category = categories[depth]
                for key in category["index"]:
                    recurse(depth + 1, [*coords, key], [*labels, category["label"][key]])
            recurse(0, [], [])
    return path


def import_project(project):
    inventory, raw_by_id, m = load_sources(project)
    result = audit(m)
    write_field_inventory(project, m)
    pop, housing, quarters, citizenship, education, labour, sizes = (
        m[key] for key in HASHES)
    data_file = project / "data/dashboard.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "CYP", "Expected Cyprus candidate")
    data["territories"] = [row for row in data["territories"] if row["id"] == "CYP"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [row for row in data["indicators"] if not row["id"].startswith(PREFIX)]
    data["observations"] = [row for row in data["observations"] if not row["indicator_id"].startswith(PREFIX)]
    data["sources"] = [row for row in data["sources"] if not row["id"].startswith("cyp-")]
    data["documents"] = [row for row in data["documents"] if not row["id"].startswith("cyp-")]
    data["country"]["geography_note"] = (
        "CYSTAT 2021 final census covers only the government-controlled areas. Its 923,381 usual residents "
        "belong to a distinct census coverage node, not to the whole-island country or WDI midyear series. "
        "CYSTAT district, municipality/community and quarter codes describe 2021 statistical geography, "
        "not verified 2024 local-governance units. All 410 locality and 99 quarter codes occur in the "
        "official 2015 GEOCODES classification, but that older match does not establish boundary identity. "
        "The 2017 geoBoundaries provider shapes are not joined. "
        "No official source-compatible polygons or 2024 code crosswalk have been obtained.")
    data["territories"].append({"id": SCOPE, "name": "Government-controlled areas (2021 census)",
        "level": "census_coverage", "type": "statistical_coverage_area", "parent_id": "CYP",
        "official_code": "TOTAL", "code_system": "CYSTAT-DB 2021 census total (controlled areas)",
        "boundary_version": None, "source_id": sid("1891108E"),
        "reconciliation_status": "Official 2021 census reporting scope; no whole-island inference"})
    for code, name in DISTRICTS.items():
        data["territories"].append({"id": tid(code), "name": f"{name} District (2021 census)",
            "level": "district", "type": "census_2021_district", "parent_id": SCOPE,
            "official_code": code, "code_system": "CYSTAT-DB 2021 census district code",
            "boundary_version": None, "source_id": sid("1891108E"),
            "reconciliation_status": "Matched by CYSTAT code across seven tables; no source-compatible polygon joined"})
    local_codes = [code for code in pop.codes if len(code) == 4]
    require(len(local_codes) == 410, "2021 locality registry changed")
    for code in local_codes:
        data["territories"].append({"id": tid(code), "name": pop.labels[code],
            "level": "census_2021_locality", "type": "municipality_or_community_statistical_area",
            "parent_id": tid(code[0]), "official_code": code,
            "code_system": "CYSTAT-DB 2021 census municipality/community statistical code",
            "boundary_version": None, "source_id": sid("1891108E"),
            "reconciliation_status": "2021 census area code only; 2024 council/municipality identity and current boundary not matched"})
    quarter_codes = [code for code in quarters.codes if len(code) == 6]
    require(len(quarter_codes) == 99, "Quarter registry changed")
    geocodes_file = project / "raw/cystat/GEOCODES-2015.csv"
    require(digest(geocodes_file) == GEOCODES_2015_HASH, "Official 2015 GEOCODES CSV changed")
    with geocodes_file.open(encoding="utf-8-sig", newline="") as stream:
        geocodes_rows = list(csv.DictReader(stream))
    old_local_codes = {row["Municipality/Community Code"] for row in geocodes_rows}
    old_quarter_codes = {row["Quarters Code"].replace("-", "") for row in geocodes_rows
                         if "-" in row["Quarters Code"]}
    require(len(geocodes_rows) == 772 and len(old_local_codes) == 615 and
            len(old_quarter_codes) == 157, "Official 2015 code ledger changed")
    require(set(local_codes) <= old_local_codes and set(quarter_codes) <= old_quarter_codes and
            all(row["District Code"] == row["Municipality/Community Code"][0]
                for row in geocodes_rows), "2021 census code absent from 2015 official classification")
    result["historical_geocodes_check"] = {
        "source_rows": len(geocodes_rows), "source_local_codes": len(old_local_codes),
        "source_quarter_codes": len(old_quarter_codes),
        "census_local_codes_found": len(local_codes), "census_quarter_codes_found": len(quarter_codes),
        "source_sha256": GEOCODES_2015_HASH,
        "limitation": "Code existence only; the 2015 edition does not establish 2021 or 2024 boundary identity."}
    for code in quarter_codes:
        data["territories"].append({"id": tid(code), "name": quarters.labels[code],
            "level": "census_2021_quarter", "type": "census_quarter", "parent_id": tid(code[:4]),
            "official_code": code, "code_system": "CYSTAT-DB 2021 census quarter code",
            "boundary_version": None, "source_id": sid("1891164E"),
            "reconciliation_status": "2021 census quarter code; no official polygon joined"})
    now = datetime.now(timezone.utc).isoformat()
    catalogue = next(row for row in inventory["catalog_directories"]
                     if row["path"] == ["Population", "Census of Population and Housing 2021"])
    data["sources"].append({"id": "cyp-cystat-2021-catalog", "name": "CYSTAT-DB 2021 census table catalogue",
        "url": catalogue["url"], "publisher": "Statistical Service of Cyprus", "reference_period": PERIOD,
        "geographic_level": "government-controlled area and coded 2021 census localities",
        "status": "partial", "raw_path": catalogue["raw_path"], "sha256": catalogue["sha256"],
        "retrieved_at": inventory["checked_at"], "license": "Source page marks copyright; redistribution terms need review",
        "note": "46 listed matrices in 12 official API directories; seven complete matrices archived, 39 location-only."})
    for table, row in raw_by_id.items():
        data["sources"].append({"id": sid(table), "name": m[table].body["label"],
            "url": row["url"], "publisher": "Statistical Service of Cyprus",
            "reference_period": PERIOD, "geographic_level": "government-controlled area, five districts and source-coded lower localities",
            "status": "partial", "raw_path": row["raw_path"], "sha256": row["sha256"],
            "retrieved_at": inventory["checked_at"],
            "license": "PxWeb table marks copyright; confirm redistribution terms before publication",
            "note": "Complete matrix archived by POST; exact request, response hash and cell disposition in private source inventory. Only selected fields adopted."})
    data["sources"].append({"id": "cyp-cystat-2021-final-release",
        "name": "Census of Population and Housing 2021: Final Results (9-page press release)",
        "url": "https://library.cystat.gov.cy/NEW/Census2021-Final_Results-EN-090824.pdf",
        "publisher": "Statistical Service of Cyprus", "reference_period": PERIOD,
        "geographic_level": "government-controlled areas; district summary",
        "status": "partial", "raw_path": "raw/cystat/Census2021-Final_Results-EN-090824.pdf",
        "sha256": FINAL_RELEASE_HASH, "retrieved_at": now,
        "license": "Official government press release; redistribution terms need review",
        "note": "Nine pages; population, housing and household national/district figures cross-check the seven API tables."})
    data["sources"].append({"id": "cyp-cystat-geocodes-2015",
        "name": "CYSTAT GEOCODES 2015 municipality, community and quarter classification",
        "url": "https://www.data.gov.cy/index.php/en/dataset/821",
        "publisher": "Statistical Service of Cyprus", "reference_period": "2015-12-31",
        "geographic_level": "district, municipality/community and quarter classification",
        "status": "partial", "raw_path": "raw/cystat/GEOCODES-2015.csv",
        "sha256": GEOCODES_2015_HASH, "retrieved_at": now,
        "license": "Government open-data page states CC BY 4.0",
        "note": "All 410 census locality and 99 quarter codes occur in the older 2015 classification; this is code-existence evidence, not a 2021/2024 boundary or council crosswalk."})
    data["sources"].append({"id": "cyp-dls-admin-units-inspire",
        "name": "Department of Lands and Surveys INSPIRE administrative units",
        "url": "https://data.gov.cy/en/dataset/542",
        "publisher": "Cyprus Department of Lands and Surveys",
        "reference_period": "2016 source coverage; catalogue modified 2026-03-16",
        "geographic_level": "district, municipality/community and parish polygons",
        "status": "not_collected", "retrieved_at": now,
        "license": "Government open-data catalogue states CC BY 4.0; inspect layer-specific terms",
        "note": "Official spatial-service location only. Layer, geometry version, code attributes and match to 2021 census/2024 governance remain unverified; no polygons joined."})
    data["sources"].append({"id": "cyp-dtph-development-plans-catalogue",
        "name": "Department of Town Planning and Housing development plan catalogue",
        "url": "https://www.gov.cy/moi-tph/documents/schedia-anaptyxis/",
        "publisher": "Cyprus Department of Town Planning and Housing",
        "reference_period": "Catalogue indexed September 2026", "geographic_level": "national plan index with plan-specific areas",
        "status": "not_collected", "retrieved_at": now,
        "license": "Source location only; terms and document bodies need review",
        "note": "Official indexed catalogue identifies Local Plans, Area Plans and Policy Statements. Direct body retrieval returned HTTP 403; plan entries require exact area and edition audit."})
    data["sources"].append({"id": "cyp-dtlgos-reform-2024",
        "name": "Ministry of Interior: District Local Government Organisations",
        "url": "https://www.gov.cy/moi/ypoyrgeio/domh/topiki-aytodioikisi/eparchiakoi-organismoi-aytodioikisis/",
        "publisher": "Cyprus Ministry of Interior", "reference_period": "2024 onward",
        "geographic_level": "five government-controlled districts", "status": "not_collected",
        "retrieved_at": now, "license": "Source location only; terms need review",
        "note": "Official indexed page states five organisations began 1 July 2024; not a crosswalk from 2021 census localities."})
    data["sources"].append({"id": "cyp-dtph-local-plan-process-2026",
        "name": "DTPH 2026 local-plan preparation for Lefkosia, Lemesos, Larnaka and Pafos",
        "url": "https://www.gov.cy/moi-tph/documents/ekponisi-topikon-schedion-leykosias-lemesoy-larnakas-kai-pafoy/",
        "publisher": "Cyprus Department of Town Planning and Housing",
        "reference_period": "2026-06 to 2026-10",
        "geographic_level": "four named local-plan areas, exact boundaries unverified",
        "status": "not_collected", "retrieved_at": now,
        "license": "Source location only; linked circular and report bodies need review",
        "note": "Official indexed page records a 2026 plan-preparation/consultation process; it is not a newly approved plan or a 2021-statistical-area crosswalk."})

    def indicator(key, name, theme, unit, definition, table, decimals=0):
        iid = PREFIX + key
        data["indicators"].append({"id": iid, "name": name, "theme": theme, "unit": unit,
            "definition": definition, "population": "2021 census government-controlled area, specified source universe",
            "source_id": sid(table), "aggregation": "none", "measurement_method": METHOD,
            "display_decimals": decimals, "series_family": "census"})
        return iid

    definitions = [
        ("POP_TOTAL", "2021 census usual residents", "Population", "people", "Usual residents in government-controlled areas, 1 October 2021; whole-island population is not implied.", "1891108E"),
        ("POP_MALE", "2021 census males", "Population", "people", "Male usual residents of the 2021 census scope.", "1891108E"),
        ("POP_FEMALE", "2021 census females", "Population", "people", "Female usual residents of the 2021 census scope.", "1891108E"),
        ("POP_0_14", "2021 census age 0–14", "Population", "people", "AreaData sum of three disjoint five-year age groups, 0–14.", "1891108E"),
        ("POP_15_64", "2021 census age 15–64", "Population", "people", "AreaData sum of ten disjoint five-year age groups, 15–64.", "1891108E"),
        ("POP_65_PLUS", "2021 census age 65+", "Population", "people", "AreaData sum of four disjoint age groups, 65 years and older.", "1891108E"),
        ("HOUSING_TOTAL", "2021 housing units", "Housing", "housing units", "All housing units enumerated by the 2021 census.", "1891161E"),
        ("HOUSING_USUAL", "2021 usual-residence housing units", "Housing", "housing units", "Housing units of usual residence.", "1891161E"),
        ("HOUSING_VACANT_TEMP", "2021 vacant or temporary-residence housing units", "Housing", "housing units", "Vacant or temporary-residence housing units; includes seasonal/secondary dwellings and other categories in source note.", "1891161E"),
        ("HOUSEHOLDS", "2021 households", "Households", "households", "Number of enumerated households; source housing matrix.", "1891161E"),
        ("HOUSEHOLD_POP", "2021 household population", "Households", "people", "Persons living in households, excluding institution population.", "1891161E"),
        ("INSTITUTIONS", "2021 institutions", "Housing", "institutions", "Number of institutions counted by census.", "1891161E"),
        ("INSTITUTION_POP", "2021 institution population", "Population", "people", "Persons living in institutions, distinct from household population.", "1891161E"),
        ("CIT_CYPRIOT", "2021 Cypriot citizens", "Citizenship", "people", "Source citizenship group includes persons who declared Cypriot as second citizenship.", "1891213E"),
        ("CIT_OTHER_EU", "2021 other EU citizens", "Citizenship", "people", "Other European Union citizens in the census citizenship-group table.", "1891213E"),
        ("CIT_NON_EU", "2021 non-EU citizens", "Citizenship", "people", "Non-European Union citizens in the census citizenship-group table.", "1891213E"),
        ("CIT_NOT_STATED", "2021 citizenship not stated", "Citizenship", "people", "Persons whose citizenship group was not stated; not zero or foreign citizenship.", "1891213E"),
        ("EDU_15PLUS", "2021 education table population age 15+", "Education", "people", "All persons aged 15+ in the education-attainment matrix; includes attainment not stated.", "1891515E"),
        ("EDU_UPTO_LOWER", "2021 up to lower-secondary education", "Education", "people", "Age 15+ persons with education up to Lower Secondary/Gymnasium, source category.", "1891515E"),
        ("EDU_UNIVERSITY", "2021 university-level attainment", "Education", "people", "Age 15+ persons with university-level tertiary educational attainment.", "1891515E"),
        ("LAB_ACTIVE", "2021 economically active age 15+", "Labour", "people", "Census economically active population aged 15+; distinct from a labour-force survey estimate.", "1891712E"),
        ("LAB_EMPLOYED", "2021 employed age 15+", "Labour", "people", "Census employed persons aged 15+.", "1891712E"),
        ("LAB_UNEMPLOYED", "2021 unemployed age 15+", "Labour", "people", "Census unemployed persons aged 15+; count, not unemployment rate.", "1891712E"),
        ("LAB_INACTIVE", "2021 economically inactive age 15+", "Labour", "people", "Census economically inactive persons aged 15+.", "1891712E"),
        ("HH_ONE_PERSON", "2021 one-person households", "Households", "households", "Households of size one.", "1895114E"),
        ("HH_SIX_PLUS", "2021 households of six or more", "Households", "households", "Households with at least six members; open-ended source class.", "1895114E"),
        ("HH_AVG_SIZE", "2021 average household size", "Households", "persons per household", "Source-reported rounded mean; not additive and not computed where no household exists.", "1895114E"),
    ]
    for item in definitions:
        indicator(*item, decimals=2 if item[0] == "HH_AVG_SIZE" else 0)

    def observe(code, key, value, table, locator, provenance="source_reported", footnote=None):
        require(value is None or isinstance(value, (int, float)), f"Non-numeric {table}, {code}, {key}")
        entry = {"territory_id": tid(code), "indicator_id": PREFIX + key,
            "period": PERIOD, "value": value, "status": "observed" if value is not None else "not_applicable",
            "source_id": sid(table), "measurement_method": METHOD,
            "source_locator": locator, "provenance": provenance}
        if footnote:
            entry["footnote"] = footnote
        data["observations"].append(entry)

    for code in pop.codes:
        observe(code, "POP_TOTAL", pop.cell(code, 0, 0), "1891108E", f"1891108E location {code}, SEX 0, AGE 0")
        observe(code, "POP_MALE", pop.cell(code, 1, 0), "1891108E", f"1891108E location {code}, SEX 1, AGE 0")
        observe(code, "POP_FEMALE", pop.cell(code, 2, 0), "1891108E", f"1891108E location {code}, SEX 2, AGE 0")
        for key, age_codes in (("POP_0_14", range(1, 4)), ("POP_15_64", range(4, 14)),
                               ("POP_65_PLUS", range(14, 18))):
            observe(code, key, sum(pop.cell(code, 0, age) for age in age_codes), "1891108E",
                f"1891108E location {code}, SEX 0, AGE {','.join(map(str, age_codes))}",
                "calculated", "AreaData sum of mutually exclusive census age groups.")
    housing_keys = ("HOUSING_TOTAL", "HOUSING_USUAL", "HOUSING_VACANT_TEMP", "HOUSEHOLDS",
                    "HOUSEHOLD_POP", "INSTITUTIONS", "INSTITUTION_POP")
    for code in housing.codes:
        for field, key in enumerate(housing_keys):
            observe(code, key, housing.cell(code, field), "1891161E",
                    f"1891161E location {code}, contents {field}")
    for code in quarter_codes:
        for field, key in enumerate(housing_keys):
            observe(code, key, quarters.cell(code, field), "1891164E",
                    f"1891164E quarter {code}, contents {field}")
        observe(code, "POP_TOTAL", quarters.cell(code, 7), "1891164E",
                f"1891164E quarter {code}, contents 7")
    for code in citizenship.codes:
        for group, key in ((1, "CIT_CYPRIOT"), (2, "CIT_OTHER_EU"), (3, "CIT_NON_EU"),
                           (4, "CIT_NOT_STATED")):
            observe(code, key, citizenship.cell(code, group, 0), "1891213E",
                    f"1891213E location {code}, CITIZENSHIP GROUP {group}, SEX 0")
    for code in education.codes:
        for category, key in ((0, "EDU_15PLUS"), (1, "EDU_UPTO_LOWER"), (5, "EDU_UNIVERSITY")):
            observe(code, key, education.cell(code, 0, category), "1891515E",
                    f"1891515E location {code}, SEX 0, EDUCATIONAL ATTAINMENT {category}")
    for code in labour.codes:
        for field, key in ((1, "LAB_ACTIVE"), (2, "LAB_EMPLOYED"), (3, "LAB_UNEMPLOYED"),
                           (4, "LAB_INACTIVE")):
            observe(code, key, labour.cell(code, field), "1891712E",
                    f"1891712E location {code}, activity {field}")
    for code in sizes.codes:
        for field, key in ((1, "HH_ONE_PERSON"), (6, "HH_SIX_PLUS"), (7, "HH_AVG_SIZE")):
            observe(code, key, sizes.cell(code, field), "1895114E",
                    f"1895114E location {code}, household size {field}",
                    footnote="N.A. because the source records zero households." if field == 7 and sizes.cell(code, field) is None else None)

    comparisons = [{"parent_id": SCOPE, "member_ids": [tid(code) for code in DISTRICTS],
        "label": "Five government-controlled census districts (2021)",
        "membership_note": "Complete, nonoverlapping official CYSTAT census district cover of the controlled area. Not an all-island total or a 2024 council crosswalk.",
        "source_ids": [sid("1891108E")]}]
    for code in DISTRICTS:
        children = [item for item in local_codes if item.startswith(code)]
        comparisons.append({"parent_id": tid(code), "member_ids": [tid(child) for child in children],
            "label": f"{DISTRICTS[code]} 2021 census municipality/community areas",
            "membership_note": "The complete CYSTAT 2021 statistical-area ledger, including source population-zero areas. Housing/social fields absent for some zero-population areas remain missing. No 2024 boundary identity is inferred.",
            "source_ids": [sid("1891108E")]})
    quarter_by_parent = defaultdict(list)
    for code in quarter_codes:
        quarter_by_parent[code[:4]].append(code)
    for code, children in quarter_by_parent.items():
        comparisons.append({"parent_id": tid(code), "member_ids": [tid(child) for child in children],
            "label": f"{pop.labels[code]} 2021 census quarters",
            "membership_note": "Complete, nonoverlapping quarter cover for the eight housing and population fields in CYSTAT matrix 1891164E. No quarter age, citizenship, education or labour observations are inferred.",
            "source_ids": [sid("1891164E")]})
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = [tid(code) for code in local_codes if code not in quarter_by_parent] + [tid(code) for code in quarter_codes]
    data["analysis"]["default_indicator_id"] = PREFIX + "POP_TOTAL"
    data["analysis"]["latest_values_only"] = True

    data["planning"] = {"title": "Development plan source locations",
        "purpose": "Locate official Local Plans, Area Plans and Policy Statements for the selected place; confirm exact area, edition and legal effect before using them in a plan.",
        "system": {"label": "Department of Town Planning and Housing development plans and five district local-government organisations",
            "scope": "Plan-specific areas and 2024 competent bodies must be reconciled separately from 2021 statistical localities",
            "cycle": "Plan-specific publication and revision dates; no universal five-year municipal cycle assumed",
            "source_ids": ["cyp-dtph-development-plans-catalogue", "cyp-dtlgos-reform-2024",
                           "cyp-dtph-local-plan-process-2026"]},
        "sections": [{"id": "plan", "label": "Local and area plans"},
                     {"id": "budget", "label": "Budgets and programmes"},
                     {"id": "implementation", "label": "Implementation and execution"},
                     {"id": "evaluation", "label": "Official evaluations"},
                     {"id": "reference", "label": "Planning law, policy and guidance"}]}
    for territory_id, title, note in ((SCOPE, "Official development plan catalogue",
        "Catalogue identifies Local Plans, Area Plans and Policy Statements by area. Body access returned HTTP 403; exact plan coverage and current effect are not established."),
        (tid("3"), "Paralimni, Agia Napa and Deryneia 2024 Local Plan location",
        "Official catalogue and Gazette identify a 2024 plan for these areas, not the whole Ammochostos district; PDF body retrieval timed out and precise 2024/2021 boundary reconciliation is pending.")):
        data["documents"].append({"id": "cyp-development-catalogue-" + territory_id.split(":")[-1].lower(),
            "territory_id": territory_id, "category": "plan" if territory_id != SCOPE else "reference",
            "kind": "plan_catalogue_or_location", "title": title,
            "url": "https://www.gov.cy/moi-tph/documents/schedia-anaptyxis/",
            "source_id": "cyp-dtph-development-plans-catalogue", "period": "2024 or indexed 2026",
            "availability": "link_verified",
            "official_status": "unverified", "note": note})
    data["documents"].append({"id": "cyp-2021-census-final-release-document",
        "territory_id": SCOPE, "category": "reference", "kind": "census_final_release",
        "title": "CYSTAT Census 2021 final results, 9 August 2024",
        "url": "https://library.cystat.gov.cy/NEW/Census2021-Final_Results-EN-090824.pdf",
        "source_id": "cyp-cystat-2021-final-release", "period": PERIOD,
        "availability": "body_acquired", "official_status": "final_statistical_release",
        "territory_match": {"territory_id": SCOPE, "country_id": "CYP",
            "type": "statistical_coverage_area",
            "code_system": "CYSTAT-DB 2021 census total (controlled areas)",
            "official_code": "TOTAL", "boundary_version": None,
            "method": "Release explicitly states government-controlled census coverage; not a whole-island territory",
            "source_id": "cyp-cystat-2021-final-release", "locator": "p. 1 scope statement",
            "checked_at": now},
        "official_evidence": {"source_id": "cyp-cystat-2021-final-release",
            "locator": "p. 1 final-results title, publication date and scope", "checked_at": now},
        "note": "Nine-page source release. Census reference, not a plan or a budget."})
    data["collection"]["status"] = "partial"
    data["collection"]["note"] = "Seven of 46 official census tables acquired in full; selected direct/counted fields adopted after source reconciliation. Current legal geography, official polygons, planning bodies and 39 further table bodies remain unresolved."
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
        "cystat-2021-census-selected-matrices"]))
    data["collection"]["notes"] = [
        "Official final 2021 census source geography and selected fields have been partially integrated; this is not a completed planning dashboard.",
        *[note for note in data["collection"].get("notes", [])
          if not note.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [gap for gap in data["gaps"] if gap["category"] not in
        {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "pending",
         "detail": "All 410 locality and 99 quarter codes are present in official 2015 GEOCODES, but that older classification does not prove 2021/2024 boundaries. DLS INSPIRE spatial services are located but unacquired; 2017 geoBoundaries shapes remain unjoined.",
         "next_action": "Acquire date-specific DLS layers and the 2024 local-government crosswalk; reconcile district, locality and quarter geometries before map joining."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Seven complete CYSTAT census matrices support 27 selected indicators across the controlled area, five districts, 410 statistical localities and 99 quarters. Thirty-nine other catalogue matrices remain location-only; some zero-population localities have no housing or social matrix row.",
         "next_action": "Audit the remaining 39 matrix bodies and unadopted fields, including definitions, comparability, eligibility and source terms. Leave absent cells missing."},
        {"category": "planning_documents", "status": "partial",
         "detail": "The official development-plan catalogue and a 2024 plan location are identified, but local plan body retrieval returned 403 or timed out. No budget, execution or evaluation body has been acquired.",
         "next_action": "Acquire exact plan/map editions and fiscal records, then verify current legal effect and 2024-to-2021 geographic fit per area."},
    ])
    data["generated_at"] = now
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result.update({"territories": len(data["territories"]),
        "domestic_indicators": len(definitions),
        "domestic_observations": sum(row["indicator_id"].startswith(PREFIX) for row in data["observations"]),
        "direct_or_source_reported": sum(row["indicator_id"].startswith(PREFIX) and
            row.get("provenance") == "source_reported" for row in data["observations"]),
        "calculated": sum(row["indicator_id"].startswith(PREFIX) and
            row.get("provenance") == "calculated" for row in data["observations"]),
        "not_applicable": sum(row["indicator_id"].startswith(PREFIX) and
            row["status"] == "not_applicable" for row in data["observations"]),
        "comparisons": len(comparisons), "dataset_sha256": digest(data_file)})
    audit_file = project / "evidence/CYP_CYSTAT2021_AUDIT.json"
    audit_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    import_project(parser.parse_args().project)

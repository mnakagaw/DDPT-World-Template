"""Import selected Bahrain 2020 census and annual governorate fields.

The 45 Census-theme datasets are mechanically inventoried separately. This
adapter adopts only cross-checked, explicitly named fields; it does not join
unverified 2017 provider polygons or infer governorate planning authority.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PREFIX = "BHR_IGA_"
GOVERNORATES = ("Capital", "Muharraq", "Northern", "Southern")
CATALOG_SHA256 = "32d387cfc741d3d97fe72b3a4ba70a6474c6a9a3660cc28def16c1631c00eb4c"
ANNUAL_SHA256 = (
    "f2056a5f0b9ed06131b52ded5ceea12854c749b5945f7fbb601ef6cfd7aacd43",
    "c1c04f78750e82ed67c57a8051d736cd31ab39177fb3cc76f89e455dd89cd70a",
    "af9ae2694217d12f58a5a39fcf0e6be20f0f46a2780cdae47612e11b9a63a576",
    "4722d51cc64add201a2b0da2f1dc2e2fb1a037933ff62721ad29c630538d3340",
)
AREA_SHA256 = "779f27e89bbc8789157c418b125ee534c1580a1f3301a92a8fa22f8276f909e6"
PLAN_FILES = {
    "bhr-lloc-urban-planning-1994": ("bhr-urban-planning-law-1994.html", "a496642d3dcc3609e541419e9515983c657920f016e4d2625816b7db25afea7a"),
    "bhr-lloc-urban-planning-amendment-2022": ("bhr-urban-planning-amendment-2022.html", "1dabccceb352a853eeaf093051955a8a988bc78b2a7b397ccec8179f9b4811fd"),
    "bhr-lloc-zoning-decision-93-2023": ("bhr-zoning-decision-93-2023.html", "146046b478db467f740b0028ecf10623286f2280dff51c8790ea2722b8226f56"),
    "bhr-upda-manual-catalogue-2023": ("upda-manual-catalogue.html", "c3e079ed0f308007908e89913f5258655017ef8dbe531d46b6335ef35e0c428f"),
    "bhr-upda-procedures-manual-2023": ("upda-procedures-manual-2023.pdf", "5e78a44775072d6dc27fdc83f6895fff764c2fb3471fbceee070fb120f6905f3"),
    "bhr-capital-zones-decision-15-2017": ("capital-zones-map.pdf", "f54b701e3035e8c11dbc8879a8e746cde92101ab5608a97bab80c59e2584d6ad"),
}
DATASETS = {
    "pop": "population-by-governorate-nationality-and-sex-census-2020",
    "pop_detail": "population-by-governorate-nationality-groups-and-sex-census-2020",
    "pop_religion": "population-by-religion-nationality-and-sex-census-2020",
    "household": "total-households-by-governorate-and-type-of-household-census-2020",
    "household_nat": "private-households-by-governorate-and-household-nationality-census-2020",
    "household_distribution": "distribution-households-by-governorate-and-nationality-of-households-census-2020",
    "household_size": "private-households-by-household-size-and-governorate-census-2020",
    "household_persons": "distribution-population-by-governorate-and-nationality-of-households-census-2020",
    "housing": "housing-units-by-housing-type-and-governorate-census-2020",
    "housing_occupancy": "housing-units-by-housing-type-and-occupancy-census-2020",
    "school": "school-enrolled-population-3-years-and-above-by-governorate-nationality-and-sex-",
    "school_stage": "school-enrolled-population-3-years-and-above-by-sex-governorate-and-schooling-st",
    "active": "economically-active-population-15-years-and-above-by-governorate-nationality-and",
    "labour": "population-15-years-and-above-by-governorate-and-labour-force-participation-cens",
    "marital": "population-15-years-and-above-by-sex-governorate-and-marital-status-census-2020",
    "buildings_usage": "buildings-by-building-current-usage-and-governorate-census-2020",
    "buildings_type": "buildings-by-building-type-and-governorate-census-2020",
    "buildings_ownership": "buildings-by-ownership-type-and-governorate-census-2020",
}
PRIMARY = {"pop", "household", "household_persons", "housing", "school", "active", "labour", "marital"}
VALIDATION = {"pop_detail", "pop_religion", "household_nat", "household_distribution", "household_size",
              "housing_occupancy", "school_stage"}
CONFLICT = {"buildings_usage", "buildings_type", "buildings_ownership"}


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_id(key):
    return "bhr-iga-census2020-" + key.replace("_", "-")


def main(project):
    raw_root = project / "raw/bahrain-open-data"
    inventory = json.loads((project / "evidence/BHR_CENSUS2020_SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    check(inventory["catalog_sha256"] == CATALOG_SHA256 and
          sha(project / inventory["catalog_path"]) == CATALOG_SHA256, "Census catalogue changed")
    check(inventory["totals"] == {"datasets": 45, "records": 2602, "numeric_columns": 45,
                                  "numeric_cells": 2598, "governorate_datasets": 20},
          "Census source universe changed")
    by_id = {item["id"]: item for item in inventory["datasets"]}
    check(len(by_id) == 45 and len(set(DATASETS.values())) == len(DATASETS), "Dataset IDs changed")
    tables = {}
    for key, dataset_id in DATASETS.items():
        meta = by_id[dataset_id]
        rows = []
        for page in meta["pages"]:
            path = project / page["path"]
            check(sha(path) == page["sha256"], f"API page changed: {path}")
            response = json.loads(path.read_text(encoding="utf-8"))
            check(response["total_count"] == meta["record_count"] and
                  len(response["results"]) == page["records"], f"API page count changed: {dataset_id}")
            rows.extend(response["results"])
        check(len(rows) == meta["record_count"], f"Incomplete source: {dataset_id}")
        tables[key] = rows

    def select(key, **filters):
        found = [(number, row) for number, row in enumerate(tables[key], 1)
                 if all(row.get(field) == value for field, value in filters.items())]
        return found

    def sum_rows(key, field, rows, count=None):
        if count is not None:
            check(len(rows) == count, f"{key}: expected {count} rows, got {len(rows)}")
        values = [row[field] for _, row in rows]
        check(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                  for value in values), f"Non-count in {key}.{field}")
        return sum(values)

    # Cross-check duplicate tables and a complete, non-overlapping four-governorate population cover.
    for gov in GOVERNORATES:
        basic = select("pop", governorate=gov)
        detailed = select("pop_detail", governorate=gov)
        check(len(basic) == 4 and len(detailed) == 16, f"Population cells changed in {gov}")
        for nationality in ("Bahraini", "Non-Bahraini"):
            for sex in ("Female", "Male"):
                direct = sum_rows("pop", "population", select("pop", governorate=gov,
                                  nationality=nationality, sex=sex), 1)
                subset = [item for item in detailed if item[1]["sex"] == sex and
                          (item[1]["nationality_groups"] == "Bahraini") == (nationality == "Bahraini")]
                check(direct == sum_rows("pop_detail", "population", subset,
                                         1 if nationality == "Bahraini" else 7),
                      f"Population nationality/sex conflict: {gov}, {nationality}, {sex}")
    check(sum_rows("pop", "population", select("pop"), 16) == 1501635,
          "Census national total changed")
    check(sum_rows("pop_religion", "population", select("pop_religion"), 8) == 1501635,
          "Census national religion cross-check failed")
    pinned_governorate_population = {"Capital": 548345, "Muharraq": 268106,
                                     "Northern": 379637, "Southern": 305547}
    for gov, expected in pinned_governorate_population.items():
        check(sum_rows("pop", "population", select("pop", governorate=gov), 4) == expected,
              f"Census governorate population changed: {gov}")

    for gov in GOVERNORATES:
        private = sum_rows("household", "household", select("household", governorate=gov,
                           type_of_household="Private Households"), 1)
        check(len(select("household", governorate=gov)) == 2 and
              private == sum_rows("household_nat", "household", select("household_nat", governorate=gov), 2) ==
              sum_rows("household_distribution", "households", select("household_distribution", governorate=gov), 2) ==
              sum_rows("household_size", "household", select("household_size", governorate=gov), 24),
              f"Private household cross-check failed: {gov}")
        check(len(select("household_persons", governorate=gov)) == 2,
              f"Private-household person rows changed: {gov}")
        check(len(select("housing", governorate=gov)) == 5, f"Housing-type rows changed: {gov}")
        check(sum_rows("school", "school_enrolled_population", select("school", governorate=gov), 4) ==
              sum_rows("school_stage", "school_enrolled_population", select("school_stage", governorate=gov), 28),
              f"School enrollment cross-check failed: {gov}")
        active = sum_rows("active", "population", select("active", governorate=gov), 4)
        labour = select("labour", governorate=gov)
        check(len(labour) == 32 and active == sum_rows("labour", "population", [item for item in labour
              if item[1]["labour_force_participation"] in ("Employed", "Unemployed")], 8),
              f"Economically active cross-check failed: {gov}")
        check(sum_rows("labour", "population", labour, 32) ==
              sum_rows("marital", "population", select("marital", governorate=gov), 16),
              f"Age-15-plus population cross-check failed: {gov}")
    check(sum_rows("housing", "housing", select("housing"), 20) ==
          sum_rows("housing_occupancy", "housing", select("housing_occupancy"), 10) == 387126,
          "National housing-unit cross-check failed")
    check(sum_rows("household", "household", select("household"), 8) == 245983,
          "National household total changed")
    check(sum_rows("school", "school_enrolled_population", select("school"), 16) == 309557,
          "National school-enrolled count changed")
    check(sum_rows("active", "population", select("active"), 16) == 875558,
          "National economically active count changed")

    # The building totals disagree by governorate even though their national totals coincide.
    expected_buildings = {"buildings_usage": (84421, 50560, 84982, 54770),
                          "buildings_type": (84421, 54770, 84982, 50560),
                          "buildings_ownership": (84421, 54770, 84982, 50560)}
    for key, expected in expected_buildings.items():
        actual = tuple(sum_rows(key, "buildings", select(key, governorate=gov)) for gov in GOVERNORATES)
        check(actual == expected, f"Building conflict changed: {key} {actual}")
    for key in ("buildings_type", "buildings_ownership"):
        invalid = [row for row in tables[key] if row.get("governorate") == "#REF!"]
        check(len(invalid) == 1 and invalid[0].get("buildings") is None,
              f"Building malformed source row changed: {key}")

    annual_files = [raw_root / f"annual-governorate-{offset}.json" for offset in (0, 100, 200, 300)]
    check(tuple(sha(path) for path in annual_files) == ANNUAL_SHA256, "Annual population raw pages changed")
    annual_meta_file = raw_root / "annual-governorate-metadata.json"
    check(sha(annual_meta_file) == "b7b58e8d35427a62262270b3e3ae8c47aa0045a85fa5f3bded56081f5531fc02",
          "Annual population metadata changed")
    annual = []
    for file in annual_files:
        page = json.loads(file.read_text(encoding="utf-8"))
        check(page["total_count"] == 320, "Annual population API count changed")
        annual.extend(page["results"])
    check(len(annual) == len({json.dumps(row, sort_keys=True) for row in annual}) == 320,
          "Annual population pages incomplete or duplicate")
    annual_adopted = [row for row in annual if row["year"] in {f"{year}-06" for year in range(2020, 2026)}]
    check(len(annual_adopted) == 96 and set(row["governorate"] for row in annual_adopted) == set(GOVERNORATES),
          "June 2020-2025 annual population coverage changed")
    check(sum(row["population"] for row in annual_adopted if row["year"] == "2025-06") == 1603260,
          "June 2025 annual population changed")
    check(sum(row["population"] for row in annual_adopted if row["year"] == "2020-06") == 1472204,
          "June 2020 annual population changed")
    for year in range(2020, 2026):
        for gov in GOVERNORATES:
            group = [row for row in annual_adopted if row["year"] == f"{year}-06" and
                     row["governorate"] == gov]
            check(len(group) == 4 and {(row["nationality"], row["sex"]) for row in group} ==
                  {(nat, sex) for nat in ("Bahraini", "Non-Bahraini") for sex in ("Male", "Female")},
                  f"Incomplete annual demographic group: {gov}, {year}")

    area_file = raw_root / "area-2023-records.json"
    check(sha(area_file) == AREA_SHA256 and
          sha(raw_root / "area-2023-metadata.json") == "d1009daa25983a01905c13b21854c3220ed40e2ae7f3d7f6b6e75370c66d2ac7",
          "Official governorate area source changed")
    area = json.loads(area_file.read_text(encoding="utf-8"))
    check(area["total_count"] == len(area["results"]) == 79, "Area source rows changed")
    area_2024 = {row["governorate"]: row for row in area["results"] if row["year"] == "2024"}
    check({gov: area_2024[gov]["value"] for gov in GOVERNORATES} ==
          {"Capital": 79.23, "Muharraq": 74.1, "Northern": 145.69, "Southern": 488.77},
          "2024 official area values changed")
    for source, (_name, expected_hash) in PLAN_FILES.items():
        check(sha(raw_root / PLAN_FILES[source][0]) == expected_hash,
              f"Planning source changed: {source}")

    now = datetime.now(timezone.utc).isoformat()
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    check(data["country"]["id"] == "BHR", "Expected Bahrain candidate")
    data["territories"] = [row for row in data["territories"] if row["id"] == "BHR"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [row for row in data["indicators"] if not row["id"].startswith(PREFIX)]
    data["observations"] = [row for row in data["observations"] if not row["indicator_id"].startswith(PREFIX)]
    data["sources"] = [row for row in data["sources"] if not row["id"].startswith("bhr-")]
    data["documents"] = [row for row in data["documents"] if not row["id"].startswith("bhr-")]
    data["country"]["geography_note"] = (
        "The iGA 2020 census, annual population and area datasets identify Capital, Muharraq, Northern and "
        "Southern by name/Arabic label. The government area dataset says five governorates were redivided to "
        "four in 2014. Official governorate codes and census-compatible polygons have not been acquired; "
        "2017 geoBoundaries reference shapes are unjoined. The 2020 census is an administrative-record census, "
        "separate from June annual portal population and WDI midyear estimates. Governorates are statistical "
        "diagnostic areas, not presumed legal authors of an urban plan.")
    local_names = {row["governorate"]: row["lmhfz"] for row in tables["pop"]}
    tid = lambda gov: f"BHR:IGA:GOV:{gov.upper()}"
    for gov in GOVERNORATES:
        data["territories"].append({"id": tid(gov), "name": gov, "name_local": local_names[gov],
            "level": "governorate", "type": "governorate", "parent_id": "BHR", "official_code": None,
            "code_system": "iGA 2020 Census governorate name; official code not acquired", "boundary_version": None,
            "source_id": source_id("pop"),
            "reconciliation_status": "English/Arabic name agrees across iGA 2020 census, annual population and area tables; official polygon/code join unverified"})
    data["analysis"]["comparisons"] = [{"parent_id": "BHR",
        "member_ids": [tid(gov) for gov in GOVERNORATES],
        "label": "Four post-2014 Bahrain governorates in official iGA tables",
        "source_ids": [source_id("pop"), "bhr-iga-pop-governorate-annual", "bhr-iga-area-governorate-2024"],
        "membership_note": "Four named governorates appear in each adopted source. Compare only the same indicator, year, unit and population concept. Source totals and AreaData calculations are labelled; no official code or polygon edition is joined."}]
    data["analysis"]["default_indicator_id"] = PREFIX + "CENSUS_POP_TOTAL"
    data["analysis"]["latest_values_only"] = True
    data["analysis"].pop("population_context", None)

    indicator_specs = [
        ("CENSUS_POP_TOTAL", "Census 2020 population", "Population", "people", "pop", "All persons in the 2020 iGA administrative-record census; AreaData sums mutually exclusive nationality/sex cells."),
        ("CENSUS_POP_MALE", "Census 2020 male population", "Population", "people", "pop", "Male persons across both nationality groups."),
        ("CENSUS_POP_FEMALE", "Census 2020 female population", "Population", "people", "pop", "Female persons across both nationality groups."),
        ("CENSUS_POP_BAHRAINI", "Census 2020 Bahraini population", "Population", "people", "pop", "Bahraini persons, both sexes."),
        ("CENSUS_POP_NONBAHRAINI", "Census 2020 non-Bahraini population", "Population", "people", "pop", "Non-Bahraini persons, both sexes."),
        ("CENSUS_BAHRAINI_MALE", "Census 2020 Bahraini male population", "Population", "people", "pop", "Direct nationality by sex source cell for each governorate."),
        ("CENSUS_BAHRAINI_FEMALE", "Census 2020 Bahraini female population", "Population", "people", "pop", "Direct nationality by sex source cell for each governorate."),
        ("CENSUS_NONBAHRAINI_MALE", "Census 2020 non-Bahraini male population", "Population", "people", "pop", "Direct nationality by sex source cell for each governorate."),
        ("CENSUS_NONBAHRAINI_FEMALE", "Census 2020 non-Bahraini female population", "Population", "people", "pop", "Direct nationality by sex source cell for each governorate."),
        ("CENSUS_PRIVATE_HOUSEHOLDS", "Census 2020 private households", "Households", "households", "household", "Private household count, distinct from collective households; verified against three other iGA tables."),
        ("CENSUS_COLLECTIVE_HOUSEHOLDS", "Census 2020 collective households", "Households", "households", "household", "Collective household count in the source household-type table."),
        ("CENSUS_PRIVATE_HOUSEHOLD_PERSONS", "Census 2020 persons in private households", "Households", "people", "household_persons", "Persons classified by nationality of private household; not total population."),
        ("CENSUS_HOUSING_UNITS", "Census 2020 housing units, all types and occupancy", "Housing", "housing units", "housing", "AreaData sum of five disjoint housing types; all occupancy states. National sum matches separate type-by-occupancy table."),
        ("CENSUS_HOUSING_FLATS", "Census 2020 flat housing units", "Housing", "housing units", "housing", "Housing units of Flat type, all occupancy states."),
        ("CENSUS_SCHOOL_ENROLLED_3PLUS", "Census 2020 school-enrolled population aged 3+", "Education", "people", "school", "School-enrolled persons aged 3+, both nationality/sex groups; the seven-stage table independently reconciles."),
        ("CENSUS_ECON_ACTIVE_15PLUS", "Census 2020 economically active population aged 15+", "Labour", "people", "active", "Employed plus unemployed persons aged 15+; verified against the detailed participation table; not an employment rate."),
        ("CENSUS_UNEMPLOYED_15PLUS", "Census 2020 unemployed population aged 15+", "Labour", "people", "labour", "Unemployed persons aged 15+ in the detailed participation table; not an unemployment rate."),
        ("CENSUS_POP_15PLUS", "Census 2020 population aged 15+", "Population", "people", "marital", "Persons aged 15+ summed across disjoint marital-status, nationality and sex classes; agrees with detailed labour table."),
        ("JUNE_POP_TOTAL", "Official June population, both nationalities", "Population", "people", None, "iGA annual governorate table, June of the displayed year; metadata does not specify its statistical method. Separate from 2020 census and WDI."),
        ("JUNE_POP_BAHRAINI", "Official June Bahraini population", "Population", "people", None, "iGA annual governorate table, June of the displayed year, Bahraini persons; methodology not specified in dataset metadata."),
        ("JUNE_POP_NONBAHRAINI", "Official June non-Bahraini population", "Population", "people", None, "iGA annual governorate table, June of the displayed year, non-Bahraini persons; methodology not specified in dataset metadata."),
        ("AREA_KM2_2024", "Governorate area, 2024", "Geography", "km²", None, "Source-reported 2024 governorate area in square kilometres. This is not a verified boundary polygon or calculated population density."),
    ]
    for suffix, name, theme, unit, key, definition in indicator_specs:
        sid = source_id(key) if key else ("bhr-iga-area-governorate-2024" if suffix == "AREA_KM2_2024"
                                         else "bhr-iga-pop-governorate-annual")
        entry = {"id": PREFIX + suffix, "name": name, "theme": theme, "unit": unit,
                 "definition": definition, "population": definition, "source_id": sid,
                 "aggregation": "none", "measurement_method": (
                     "iGA_administrative_record_census_2020" if suffix.startswith("CENSUS_") else
                     "iGA_annual_portal_population_method_unspecified" if suffix.startswith("JUNE_") else
                     "iGA_governorate_area_source_report_2024"),
                 "display_decimals": 2 if suffix == "AREA_KM2_2024" else 0}
        if suffix == "CENSUS_POP_TOTAL":
            entry["series_family"] = "census"
        data["indicators"].append(entry)

    def emit(suffix, area_id, period, value, key, rows, field, note=""):
        check(rows and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0,
              f"Invalid observation {suffix} {area_id} {period}")
        direct = len(rows) == 1 and area_id != "BHR" and not note.startswith("AreaData sum")
        source = source_id(key) if key in DATASETS else ("bhr-iga-area-governorate-2024" if key == "area"
                                                     else "bhr-iga-pop-governorate-annual")
        numbers = ",".join(str(number) for number, _row in rows)
        dataset_name = DATASETS[key] if key in DATASETS else ("02-area-by-governorate-2023" if key == "area"
                                                            else "02-population-by-governorate-nationality-sex")
        observation = {"territory_id": area_id, "indicator_id": PREFIX + suffix,
            "period": period, "value": value, "status": "observed", "source_id": source,
            "measurement_method": (
                "iGA_administrative_record_census_2020" if suffix.startswith("CENSUS_") else
                "iGA_annual_portal_population_method_unspecified" if suffix.startswith("JUNE_") else
                "iGA_governorate_area_source_report_2024"),
            "source_locator": f"iGA Open Data API dataset {dataset_name}, archived record indices {numbers}, field {field}"}
        if not direct:
            observation["provenance"] = "calculated"
            observation["footnote"] = note or f"AreaData sum of {len(rows)} non-overlapping official source cells."
        elif note:
            observation["footnote"] = note
        data["observations"].append(observation)

    for gov in GOVERNORATES:
        area_id = tid(gov)
        demographics = {
            "CENSUS_POP_TOTAL": {}, "CENSUS_POP_MALE": {"sex": "Male"},
            "CENSUS_POP_FEMALE": {"sex": "Female"},
            "CENSUS_POP_BAHRAINI": {"nationality": "Bahraini"},
            "CENSUS_POP_NONBAHRAINI": {"nationality": "Non-Bahraini"},
            "CENSUS_BAHRAINI_MALE": {"nationality": "Bahraini", "sex": "Male"},
            "CENSUS_BAHRAINI_FEMALE": {"nationality": "Bahraini", "sex": "Female"},
            "CENSUS_NONBAHRAINI_MALE": {"nationality": "Non-Bahraini", "sex": "Male"},
            "CENSUS_NONBAHRAINI_FEMALE": {"nationality": "Non-Bahraini", "sex": "Female"},
        }
        for suffix, filters in demographics.items():
            selected = select("pop", governorate=gov, **filters)
            emit(suffix, area_id, "2020", sum_rows("pop", "population", selected), "pop", selected,
                 "population", "AreaData sum of mutually exclusive nationality/sex cells." if len(selected) > 1 else "")
        for suffix, kind in (("CENSUS_PRIVATE_HOUSEHOLDS", "Private Households"),
                             ("CENSUS_COLLECTIVE_HOUSEHOLDS", "Collective Households")):
            selected = select("household", governorate=gov, type_of_household=kind)
            emit(suffix, area_id, "2020", sum_rows("household", "household", selected, 1),
                 "household", selected, "household")
        selected = select("household_persons", governorate=gov)
        emit("CENSUS_PRIVATE_HOUSEHOLD_PERSONS", area_id, "2020",
             sum_rows("household_persons", "population", selected, 2), "household_persons", selected,
             "population", "AreaData sum of persons by nationality of private household; excludes other population universes.")
        selected = select("housing", governorate=gov)
        emit("CENSUS_HOUSING_UNITS", area_id, "2020", sum_rows("housing", "housing", selected, 5),
             "housing", selected, "housing", "AreaData sum of five disjoint housing types, all occupancy states.")
        selected = select("housing", governorate=gov, housing_type="Flat")
        emit("CENSUS_HOUSING_FLATS", area_id, "2020", sum_rows("housing", "housing", selected, 1),
             "housing", selected, "housing")
        selected = select("school", governorate=gov)
        emit("CENSUS_SCHOOL_ENROLLED_3PLUS", area_id, "2020",
             sum_rows("school", "school_enrolled_population", selected, 4), "school", selected,
             "school_enrolled_population", "AreaData sum of four nationality/sex cells; checked against seven-stage table.")
        selected = select("active", governorate=gov)
        emit("CENSUS_ECON_ACTIVE_15PLUS", area_id, "2020",
             sum_rows("active", "population", selected, 4), "active", selected,
             "population", "AreaData sum of four nationality/sex cells; equals employed plus unemployed in detailed table.")
        selected = select("labour", governorate=gov, labour_force_participation="Unemployed")
        emit("CENSUS_UNEMPLOYED_15PLUS", area_id, "2020",
             sum_rows("labour", "population", selected, 4), "labour", selected,
             "population", "AreaData sum of four nationality/sex unemployed cells; not an unemployment rate.")
        selected = select("marital", governorate=gov)
        emit("CENSUS_POP_15PLUS", area_id, "2020", sum_rows("marital", "population", selected, 16),
             "marital", selected, "population", "AreaData sum of four mutually exclusive marital states × nationality × sex.")

    # National 2020 observations are explicit complete sums of the four governorate values.
    census_suffixes = [spec[0] for spec in indicator_specs if spec[0].startswith("CENSUS_")]
    national_source_rows = {
        **{suffix: select("pop", **filters) for suffix, filters in demographics.items()},
        "CENSUS_PRIVATE_HOUSEHOLDS": select("household", type_of_household="Private Households"),
        "CENSUS_COLLECTIVE_HOUSEHOLDS": select("household", type_of_household="Collective Households"),
        "CENSUS_PRIVATE_HOUSEHOLD_PERSONS": select("household_persons"),
        "CENSUS_HOUSING_UNITS": select("housing"),
        "CENSUS_HOUSING_FLATS": select("housing", housing_type="Flat"),
        "CENSUS_SCHOOL_ENROLLED_3PLUS": select("school"),
        "CENSUS_ECON_ACTIVE_15PLUS": select("active"),
        "CENSUS_UNEMPLOYED_15PLUS": select("labour", labour_force_participation="Unemployed"),
        "CENSUS_POP_15PLUS": select("marital"),
    }
    for suffix in census_suffixes:
        children = [row for row in data["observations"] if row["indicator_id"] == PREFIX + suffix and
                    row["period"] == "2020" and row["territory_id"] != "BHR"]
        check(len(children) == 4, f"Incomplete national census cover: {suffix}")
        selected = national_source_rows[suffix]
        source_key = next(spec[4] for spec in indicator_specs if spec[0] == suffix)
        field = {"household": "household", "housing": "housing", "school": "school_enrolled_population"}.get(
            source_key, "population")
        check(sum_rows(source_key, field, selected) == sum(row["value"] for row in children),
              f"National source cell and governorate totals diverge: {suffix}")
        emit(suffix, "BHR", "2020", sum(row["value"] for row in children), source_key,
             selected, field,
             "AreaData sum of the four complete, non-overlapping governorate observations for the same 2020 census indicator.")

    for year in range(2020, 2026):
        for gov in GOVERNORATES:
            area_id = tid(gov)
            group = [(number, row) for number, row in enumerate(annual, 1)
                     if row["year"] == f"{year}-06" and row["governorate"] == gov]
            for suffix, nationality in (("JUNE_POP_TOTAL", None),
                                        ("JUNE_POP_BAHRAINI", "Bahraini"),
                                        ("JUNE_POP_NONBAHRAINI", "Non-Bahraini")):
                selected = [item for item in group if nationality is None or item[1]["nationality"] == nationality]
                emit(suffix, area_id, str(year), sum_rows("annual", "population", selected,
                     4 if nationality is None else 2), "annual", selected, "population",
                     f"AreaData sum of {len(selected)} June {year} nationality/sex cells; source date {year}-06. "
                     "This annual table is separate from the 2020 census and WDI.")
        for suffix in ("JUNE_POP_TOTAL", "JUNE_POP_BAHRAINI", "JUNE_POP_NONBAHRAINI"):
            children = [row for row in data["observations"] if row["indicator_id"] == PREFIX + suffix
                        and row["period"] == str(year) and row["territory_id"] != "BHR"]
            check(len(children) == 4, f"Incomplete June national cover: {year} {suffix}")
            nationality = {"JUNE_POP_TOTAL": None, "JUNE_POP_BAHRAINI": "Bahraini",
                           "JUNE_POP_NONBAHRAINI": "Non-Bahraini"}[suffix]
            source_rows = [(number, row) for number, row in enumerate(annual, 1)
                           if row["year"] == f"{year}-06" and
                           (nationality is None or row["nationality"] == nationality)]
            check(sum_rows("annual", "population", source_rows, 16 if nationality is None else 8) ==
                  sum(row["value"] for row in children), f"June national source conflict: {year} {suffix}")
            emit(suffix, "BHR", str(year), sum(row["value"] for row in children), "annual",
                 source_rows, "population",
                 f"AreaData sum of all four June {year} governorates with the same nationality definition; "
                 "source date is June, distinct from the census reference.")
    for gov in GOVERNORATES:
        row = area_2024[gov]
        selected = [(number, value) for number, value in enumerate(area["results"], 1) if value is row]
        emit("AREA_KM2_2024", tid(gov), "2024", row["value"], "area", selected, "value",
             "Source-reported area, not a boundary polygon or a density denominator validated for 2020 census geography.")

    # Sources touched by adoption, independent cross-check or explicitly withheld conflict.
    for key in sorted(DATASETS):
        meta = by_id[DATASETS[key]]
        first = meta["pages"][0]
        data["sources"].append({"id": source_id(key), "name": meta["title"],
            "url": meta["page_url"], "publisher": "Information & eGovernment Authority",
            "reference_period": "2020 administrative-record census", "geographic_level":
                "four governorates" if meta["governorate_values"] else "national",
            "status": "partial", "raw_path": first["path"], "sha256": first["sha256"],
            "retrieved_at": now, "license": "Bahrain Open Data Portal FAQ permits free reuse; attribute the source",
            "note": ("Selected cells adopted after cross-table checks" if key in PRIMARY else
                     "Cross-check only; no separate indicator adopted" if key in VALIDATION else
                     "Excluded from governorate indicators: two building tables swap Muharraq/Southern totals, and two contain a #REF! null row")
                    + ". Exact API-page URLs and hashes are in the private 45-dataset inventory."})
    data["sources"].append({"id": "bhr-iga-census2020-catalog", "name": "Bahrain Open Data Census 2020 dataset catalogue",
        "url": "https://www.data.gov.bh/api/explore/v2.1/catalog/datasets?limit=100&refine=theme%3ACensus",
        "publisher": "Information & eGovernment Authority", "reference_period": "2020 Census theme; checked 2026-09-27",
        "geographic_level": "national and published governorate tables", "status": "partial",
        "raw_path": inventory["catalog_path"], "sha256": CATALOG_SHA256, "retrieved_at": now,
        "license": "Bahrain Open Data Portal FAQ permits free reuse; attribute the source",
        "note": "45 datasets, 2,602 records and 45 numeric fields inventoried mechanically. Only selected fields are adopted."})
    for sid, name, url, raw_file, scope, period, note in (
        ("bhr-iga-pop-governorate-annual", "iGA population by governorate, nationality and sex",
         "https://www.data.gov.bh/explore/dataset/02-population-by-governorate-nationality-sex/",
         annual_files[0], "four governorates", "June 2020-2025 selected; other months/years unadopted",
         "Annual portal population table; metadata does not state method. Four archived API pages and hashes are in the private audit."),
        ("bhr-iga-area-governorate-2024", "iGA area by governorate",
         "https://www.data.gov.bh/explore/dataset/02-area-by-governorate-2023/",
         area_file, "four governorates", "2024 selected; 2007-2023 historical rows unadopted",
         "2024 km² official rows; not a source-compatible polygon or census-area correction.")):
        data["sources"].append({"id": sid, "name": name, "url": url,
            "publisher": "Information & eGovernment Authority", "reference_period": period,
            "geographic_level": scope, "status": "partial", "raw_path": raw_file.relative_to(project).as_posix(),
            "sha256": sha(raw_file), "retrieved_at": now,
            "license": "Bahrain Open Data Portal FAQ permits free reuse; attribute the source",
            "note": note})
    plan_source_specs = (
        ("bhr-lloc-urban-planning-1994", "Legislative Decree No. 2 of 1994 on Urban Planning",
         "https://www.lloc.gov.bh/Legislation/HTM/L0294", "Legislation and Legal Opinion Commission", "national law; later amendments exist"),
        ("bhr-lloc-urban-planning-amendment-2022", "Legislative Decree No. 32 of 2022, planning amendments",
         "https://www.lloc.gov.bh/Legislation/HTM/L3222", "Legislation and Legal Opinion Commission", "2022 amendment"),
        ("bhr-lloc-zoning-decision-93-2023", "Decision No. 93 of 2023, zoning regulations",
         "https://www.lloc.gov.bh/Legislation/HTM/RCAB9323", "Legislation and Legal Opinion Commission", "2023 regulation"),
        ("bhr-upda-manual-catalogue-2023", "UPDA urban planning procedures manual catalogue",
         "https://planning.bh/en/urban_planning_manual.html", "Urban Planning and Development Authority", "June 2023 version 1.2 listing"),
        ("bhr-upda-procedures-manual-2023", "UPDA Unified Planning Procedures Manual, June 2023",
         "https://planning.bh/pdf/uppm/Urban%20Planning%20and%20Development%20Authority%20Procedures%20Manual_English%202023.pdf",
         "Urban Planning and Development Authority", "June 2023; 83 pages"),
        ("bhr-capital-zones-decision-15-2017", "Capital Governorate zoning-map decision and maps, No. 15 of 2017",
         "https://planning.bh/pdf/Rules%20and%20Regulations/Zoning%20and%20Construction%20Regulations/Capital%20Zones%20Maps%20-%20%D8%AE%D8%B1%D8%A7%D8%A6%D8%B7%20%D8%AA%D8%B5%D9%86%D9%8A%D9%81%20%D8%A7%D9%84%D8%B9%D8%A7%D8%B5%D9%85%D8%A9.pdf",
         "Urban Planning and Development Authority / Official Gazette", "2017 approval; current map applicability unverified"),
    )
    for sid, name, url, publisher, period in plan_source_specs:
        filename, _expected = PLAN_FILES[sid]
        file = raw_root / filename
        data["sources"].append({"id": sid, "name": name, "url": url, "publisher": publisher,
            "reference_period": period, "geographic_level": "Capital Governorate" if sid.startswith("bhr-capital") else "national planning framework",
            "status": "partial", "raw_path": file.relative_to(project).as_posix(),
            "sha256": sha(file), "retrieved_at": now,
            "note": "Acquired for planning-role review; not evidence of a complete current governorate development plan or fiscal execution."})

    data["documents"] = [row for row in data["documents"] if not row["id"].startswith("bhr-")]
    data["documents"].append({"id": "bhr-upda-procedures-manual-2023-document",
        "territory_id": "BHR", "category": "reference", "kind": "urban-planning-procedure-manual",
        "title": "UPDA Unified Planning Procedures Manual, version 1.2, June 2023",
        "url": next(item[2] for item in plan_source_specs if item[0] == "bhr-upda-procedures-manual-2023"),
        "source_id": "bhr-upda-procedures-manual-2023", "period": "June 2023",
        "availability": "body_acquired", "official_status": "unverified",
        "territory_match": {"territory_id": "BHR", "country_id": "BHR", "type": "country",
            "code_system": "World Bank economy code", "official_code": None, "boundary_version": None,
            "method": "National-level government procedure manual, not a governorate plan",
            "source_id": "bhr-upda-manual-catalogue-2023", "locator": "UPDA manual catalogue version 1.2",
            "checked_at": "2026-09-27"},
        "note": "83-page manual acquired; pp. 5 and 9-10 distinguish UPDA, competent municipality and planning applications. It is not a governorate development plan or approved fiscal programme. Current amendments/application should be checked."})
    data["documents"].append({"id": "bhr-capital-zoning-maps-2017-document",
        "territory_id": tid("Capital"), "category": "plan", "kind": "historical-zoning-map-decision",
        "title": "Capital Governorate approved zoning maps, Decision No. 15 of 2017",
        "url": next(item[2] for item in plan_source_specs if item[0] == "bhr-capital-zones-decision-15-2017"),
        "source_id": "bhr-capital-zones-decision-15-2017", "period": "2017",
        "availability": "body_acquired", "official_status": "unverified",
        "territory_match": {"territory_id": tid("Capital"), "country_id": "BHR", "type": "governorate",
            "code_system": "iGA 2020 Census governorate name; official code not acquired",
            "official_code": None, "boundary_version": None,
            "method": "PDF cover identifies Capital Governorate; precise 2017/2020 boundaries and revisions unverified",
            "source_id": "bhr-capital-zones-decision-15-2017", "locator": "PDF p. 1, Official Gazette issue 3301, 16 February 2017",
            "checked_at": "2026-09-27"},
        "note": "Six-page Official Gazette decision and zoning maps were acquired. They show approval at issue date in 2017; 2023 zoning-regulation changes and subsequent map revisions require review. Do not treat as a current complete Capital plan, budget or evaluation."})
    data["planning"] = {"title": "Urban planning and zoning sources",
        "purpose": "Use official UPDA/legislative plans and maps as references for area diagnosis; preserve each decision's period and verification state.",
        "system": {"label": "National urban planning law, UPDA planning procedures and detailed zoning decisions",
            "scope": "Central urban planning authority and competent municipalities; governorate is a statistical diagnosis area, not a presumed plan-making body",
            "cycle": "General/detailed plans and zoning decisions have their own legal editions; no fixed governorate plan cycle established",
            "source_ids": ["bhr-lloc-urban-planning-1994", "bhr-lloc-urban-planning-amendment-2022",
                           "bhr-lloc-zoning-decision-93-2023", "bhr-upda-procedures-manual-2023"]},
        "sections": [{"id": "plan", "label": "Zoning and spatial plan references"},
                     {"id": "budget", "label": "Budgets and programmes"},
                     {"id": "implementation", "label": "Implementation and execution"},
                     {"id": "evaluation", "label": "Official evaluations"},
                     {"id": "reference", "label": "Law and procedural guidance"}]}
    data["gaps"] = [
        {"category": "administrative_boundaries", "status": "not_collected",
         "detail": "2020 census and annual official tables identify four governorates by name, but no official code/polygon edition was acquired. The collected 2017 geoBoundaries shapes remain unjoined.",
         "next_action": "Obtain dated official governorate and finer block/area boundaries and codes; audit 2014 redivision and 2020/2025 comparability."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "All 45 Census-theme datasets and 2,602 records were mechanically inventoried; eight selected local datasets supply partial indicators, seven were cross-checks, three building tables have a governorate conflict and 27 remain unassessed. Annual June 2020-2025 and 2024 area are separate series.",
         "next_action": "Semantically audit remaining census fields and current sector datasets; obtain method notes for the annual population table and lower-area statistics."},
        {"category": "source_data_quality", "status": "partial",
         "detail": "The 2020 building-type and ownership tables swap Muharraq/Southern governorate totals relative to building-current-usage, despite a common national total; each has one #REF! null row. No governorate building indicator was adopted.",
         "next_action": "Seek iGA correction/metadata and reconcile governorate labels before using building counts."},
        {"category": "planning_documents", "status": "partial",
         "detail": "A national UPDA procedures manual and 2017 Capital zoning-map decision were acquired. Current map revisions, governorate/municipal planning roles, actual current plan bodies, budgets, execution and evaluations are unverified.",
         "next_action": "Audit each current zoning-map decision and territorial scope, municipal consultation, programmes, fiscal execution and official evaluations."},
    ]
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys(data["collection"]["adapters"] +
        ["iga-census2020-governorate-selected-fields", "iga-annual-population-june", "iga-area-2024", "upda-planning-reference"] ))
    note = ("Bahrain is a partial domestic edition: selected 2020 census and June annual governorate values, "
            "no official polygon/code join, full census semantic audit, current complete plan, or independent ACCEPT.")
    if note not in data["collection"]["notes"]:
        data["collection"]["notes"].append(note)

    disposition = []
    keyed = {dataset_id: key for key, dataset_id in DATASETS.items()}
    for meta in inventory["datasets"]:
        key = keyed.get(meta["id"])
        for field in meta["fields"]:
            if not field["numeric_cells"]:
                continue
            state = ("selected_cells_adopted_other_fields_unassessed" if key in PRIMARY else
                     "used_for_independent_crosscheck_not_adopted" if key in VALIDATION else
                     "excluded_source_governorate_conflict" if key in CONFLICT else "priority_unassessed")
            disposition.append({"dataset_id": meta["id"], "field": field["name"],
                "numeric_cells": field["numeric_cells"], "decision": state,
                "source_page_hashes": [page["sha256"] for page in meta["pages"]]})
    check(len(disposition) == 45 and Counter(row["decision"] for row in disposition) == {
        "selected_cells_adopted_other_fields_unassessed": 8,
        "used_for_independent_crosscheck_not_adopted": 7,
        "excluded_source_governorate_conflict": 3,
        "priority_unassessed": 27}, "Field dispositions changed")
    audit = {"checked_at": now, "catalog_sha256": CATALOG_SHA256,
        "scope": "Every numeric column in all 45 Census-theme API datasets. Selected adoption is narrower than mechanical inventory; no unassessed field is zero or rejected by default.",
        "field_disposition": disposition,
        "independent_checks": {"census_total_2020": 1501635, "census_governorate_total": pinned_governorate_population,
            "june_population_2020": 1472204, "june_population_2025": 1603260,
            "housing_units_all_occupancy": 387126, "households_private_and_collective": 245983,
            "school_enrolled_age3plus": 309557, "economically_active_age15plus": 875558,
            "building_conflict": expected_buildings,
            "excluded_buildings_null_rows": 2},
        "adopted_domestic_observations": len([row for row in data["observations"] if row["indicator_id"].startswith(PREFIX)]),
        "limitations": ["No official polygon/code edition matched", "Annual population method not stated in dataset metadata",
                        "2017 Capital zoning maps not proven current", "Independent ACCEPT incomplete"]}
    (project / "evidence/BHR_CENSUS2020_FIELD_DISPOSITION.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": len(data["territories"]),
        "domestic_indicators": len(indicator_specs), "domestic_observations": audit["adopted_domestic_observations"],
        "source_terms": "Bahrain open data FAQ checked; legal source terms require review",
        "census_total": 1501635, "june_2025_total": 1603260}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

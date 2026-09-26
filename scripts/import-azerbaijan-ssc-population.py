"""Import a narrowly audited SSC Azerbaijan population edition.

Input is the official, hash-pinned 2026 table 1.15, sex table 1.19 and
2024 administrative classification. The 2019 value is the published rounded
census-based count, not an exact person-level count or a current estimate.
"""

import argparse
import hashlib
import json
import re
import runpy
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import xlrd

_fetch = runpy.run_path(str(Path(__file__).with_name("fetch-azerbaijan-ssc-sources.py")))
SOURCES, sha256 = _fetch["SOURCES"], _fetch["sha256"]


PROJECT_SOURCE = "aze-ssc-demography-table-1-15"
SEX_SOURCE = "aze-ssc-demography-table-1-19"
CODE_SOURCE = "aze-ssc-administrative-classification-2024"
CENSUS_A = "aze-ssc-census-2019-volume-a"
CENSUS_B = "aze-ssc-census-2019-volume-b"
PLAN_LAW = "aze-urban-planning-construction-code"
PLAN_CATALOG = "aze-state-urban-planning-plan-catalog"
IDS = {
    "census_2019": "AZE_SSC_CENSUS_2019_THOUSANDS",
    "resident_2026": "AZE_SSC_RESIDENT_2026_THOUSANDS",
    "male_2026": "AZE_SSC_MALE_2026_THOUSANDS",
    "female_2026": "AZE_SSC_FEMALE_2026_THOUSANDS",
}
ALIAS_CODES = {
    "Baku city - total": "00000002",
    "Sabunchu district": "00500003",
    "Nakhchivan city": "10400002",
    "Khankendi city": "70400002",
    "Khojaly district": "70100001",
    "Khojavend district": "70300001",
    "Khachmaz district": "30200001",
    "Mingachevir city": "90200002",
    "Goychay district": "40800001",
    "Lachin district": "60200001",
    "Neftchala district": "80700001",
}
TYPE_MISMATCH = {"Lankaran district": "80200002", "Yevlakh district": "90100002", "Shaki district": "40400002"}
TRANSLIT = str.maketrans({"ə": "a", "ğ": "gh", "ı": "i", "ş": "sh", "ç": "ch", "ö": "o", "ü": "u", "x": "kh", "q": "g", "c": "j"})


def norm(label):
    label = label.lower()
    for term in ("rayonu", "şəhəri", "district", "city - total", "city"):
        label = label.replace(term, "")
    return re.sub(r"[^a-z]", "", label.translate(TRANSLIT))


def exact_one(value):
    if not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric source cell, received {value!r}")
    return round(float(value), 1)


def extract_codes(path):
    pages = subprocess.check_output(["pdftotext", "-layout", str(path), "-"]).decode("utf-8").split("\f")
    by_code = {}
    for page_no, page in enumerate(pages, 1):
        if not (10 <= page_no <= 113):
            continue
        for line in page.splitlines():
            head = re.match(r"^\s*([A-ZÇƏĞİÖŞÜ][A-ZÇƏĞİÖŞÜ\s]+?)\s*[-–]\s*(\d{8})\s*$", line)
            if head and head.group(2).endswith(("1", "2")):
                by_code.setdefault(head.group(2), {"label": head.group(1).strip(), "pdf_page": page_no})
            for sub in re.finditer(r"(\d{8})\s+(?:[IVX]+\.\s+)([^\d]+?rayonu)", line, re.I):
                if sub.group(1).endswith("3"):
                    by_code.setdefault(sub.group(1), {"label": sub.group(2).strip(), "pdf_page": page_no})
    if len(by_code) != 87:
        raise ValueError(f"Expected 87 first-level city/rayon codes, found {len(by_code)}")
    by_name = defaultdict(list)
    for code, item in by_code.items():
        by_name[norm(item["label"])].append(code)
    return by_code, by_name


def table_rows(sheet):
    rows = []
    for index in range(4, sheet.nrows):
        value = sheet.cell_value(index, 4)
        name = str(sheet.cell_value(index, 1)).strip()
        if isinstance(value, (int, float)) and name:
            rows.append({"excel_row": index + 1, "name": name,
                         "area_thousand_sq_km": sheet.cell_value(index, 2),
                         "census_2019_raw": sheet.cell_value(index, 3),
                         "resident_2026": exact_one(value),
                         "density_raw": sheet.cell_value(index, 5)})
    if len(rows) != 101 or rows[0]["name"] != "Republic of Azerbaijan":
        raise ValueError("SSC table 1.15 row inventory changed")
    if rows[0]["census_2019_raw"] != 9951.4 or rows[0]["resident_2026"] != 10262.4:
        raise ValueError("National source anchors changed")
    return rows


def match_codes(rows, by_code, by_name):
    matches = {}
    used = set()
    for row in rows[1:]:
        name = row["name"]
        if name.endswith("economic region - total"):
            continue
        if name in TYPE_MISMATCH:
            code, status = TYPE_MISMATCH[name], "unresolved_type_mismatch"
        elif name in ALIAS_CODES:
            code, status = ALIAS_CODES[name], "manual_transliteration_checked"
        else:
            options = by_name[norm(name)]
            if len(options) != 1:
                raise ValueError(f"No unique official code for {name}: {options}")
            code, status = options[0], "exact_transliteration_checked"
        if code not in by_code or code in used:
            raise ValueError(f"Missing or repeated official code: {name} {code}")
        used.add(code)
        matches[row["excel_row"]] = {"source_name": name, "candidate_code": code,
            "classification_label": by_code[code]["label"], "classification_pdf_page": by_code[code]["pdf_page"],
            "status": status, "official_code_adopted": status != "unresolved_type_mismatch"}
    if len(matches) != 87 or used != set(by_code):
        raise ValueError(f"Code roster differs: {len(matches)} rows, {len(used)} unique codes")
    return matches


def sex_rows(sheet, area_rows):
    index = defaultdict(list)
    for i in range(6, sheet.nrows):
        label = str(sheet.cell_value(i, 1)).strip()
        if label:
            index[label].append(i)
    result = {}
    for row in area_rows:
        options = [i for i in index[row["name"]]
                   if isinstance(sheet.cell_value(i, 2), (int, float))
                   and abs(exact_one(sheet.cell_value(i, 2)) - row["resident_2026"]) < 0.01]
        if len(options) != 1:
            raise ValueError(f"Sex table has no unique matching row: {row['name']} {options}")
        i = options[0]
        male, female = exact_one(sheet.cell_value(i, 3)), exact_one(sheet.cell_value(i, 4))
        if abs(male + female - row["resident_2026"]) > 0.101:
            raise ValueError(f"Sex cells differ from total beyond source rounding: {row['name']}")
        result[row["excel_row"]] = {"excel_row": i + 1, "name": row["name"],
                                     "total": row["resident_2026"], "male": male, "female": female}
    if len(result) != 101:
        raise ValueError("Sex source row coverage changed")
    return result


def source(url_id, name, url, raw, note, level, status="partial"):
    result = {"id": url_id, "name": name, "url": url, "publisher": "State Statistical Committee of the Republic of Azerbaijan",
              "reference_period": "2019 / 2026" if "demography" in url_id else "source edition",
              "geographic_level": level, "status": status, "license": "terms_review_required", "note": note}
    if raw is not None:
        result.update({"raw_path": "raw/official/" + raw.name, "sha256": sha256(raw),
                       "retrieved_at": datetime.fromtimestamp(raw.stat().st_mtime, timezone.utc).isoformat()})
    return result


def observation(area, indicator, period, value, source_id, locator):
    return {"territory_id": area, "indicator_id": indicator, "period": period,
            "value": exact_one(value), "status": "observed", "measurement_method": "source_reported",
            "source_id": source_id, "source_locator": locator}


def main(project):
    raw, evidence = project / "raw" / "official", project / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    for filename, (_, expected, _) in SOURCES.items():
        if sha256(raw / filename) != expected:
            raise ValueError(f"Raw source changed: {filename}")
    area = xlrd.open_workbook(raw / "ssc-area-population-density.xls").sheet_by_index(0)
    historical = xlrd.open_workbook(raw / "ssc-resident-population-regions.xls").sheet_by_index(0)
    sex = xlrd.open_workbook(raw / "ssc-population-sex-2026.xls").sheet_by_index(0)
    rows = table_rows(area)
    by_code, by_name = extract_codes(raw / "ssc-admin-classification-2024.pdf")
    matches, sex_match = match_codes(rows, by_code, by_name), sex_rows(sex, rows)
    if historical.nrows != 394 or historical.ncols != 7 or sex.nrows != 474 or sex.ncols != 11:
        raise ValueError("One of the other source sheets changed shape")
    field_inventory = [
        {"file": "ssc-area-population-density.xls", "sheet": area.name, "rows": area.nrows,
         "fields": [
            {"column": "C", "meaning": "area, thousand square kilometres", "decision": "not_adopted", "reason": "Boundary edition and 2026 legal area reconciliation open"},
            {"column": "D", "meaning": "2019 census-based resident population, thousand people", "decision": "adopted_partial", "reason": "Aghdara source cell is ellipsis; 2019 geography versus 2024 code/2026 group not fully reconciled"},
            {"column": "E", "meaning": "01.01.2026 resident population, thousand people", "decision": "adopted_partial", "reason": "Published estimates; no official 2026 polygon join"},
            {"column": "F", "meaning": "01.01.2026 population density per square kilometre", "decision": "not_adopted", "reason": "Area/boundary provenance and Excel formula precision need review"}]},
        {"file": "ssc-population-sex-2026.xls", "sheet": sex.name, "rows": sex.nrows,
         "fields": [
            {"column": "C", "meaning": "total population", "decision": "cross_checked", "reason": "Matches table 1.15 on all 101 selected rows"},
            {"column": "D", "meaning": "men", "decision": "adopted_partial"},
            {"column": "E", "meaning": "women", "decision": "adopted_partial"},
            *[{"column": column, "meaning": meaning, "decision": "not_adopted", "reason": "Settlement rows and urban/rural classification require separate field and geography audit"}
              for column, meaning in zip("FGHIJK", ("urban total", "urban men", "urban women", "rural total", "rural men", "rural women"))]]},
        {"file": "ssc-resident-population-regions.xls", "sheet": historical.name, "rows": historical.nrows,
         "fields": [{"column": column, "meaning": f"census population {year}, thousand people", "decision": "not_adopted",
                     "reason": "Historical and urban/rural geography differs; 2019 selected from table 1.15 and this table not fully row-audited"}
                    for column, year in zip("CDEFG", (1979, 1989, 1999, 2009, 2019))]},
    ]
    path = project / "data" / "dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "AZE":
        raise ValueError("Expected Azerbaijan project")
    own_source_ids = {PROJECT_SOURCE, SEX_SOURCE, CODE_SOURCE, CENSUS_A, CENSUS_B, PLAN_LAW, PLAN_CATALOG}
    data["territories"] = [t for t in data["territories"] if not t["id"].startswith(("AZE:SSC:", "AZE:SSC24:")) and not t["id"].startswith("AZE:gbOpen:")]
    data["indicators"] = [x for x in data["indicators"] if x["id"] not in IDS.values()]
    data["observations"] = [x for x in data["observations"] if x["indicator_id"] not in IDS.values()]
    data["sources"] = [x for x in data["sources"] if x["id"] not in own_source_ids]
    if len(data["territories"]) != 1:
        raise ValueError("Unexpected baseline territory roster")
    data["territories"][0]["official_code"] = None
    data["territories"][0]["boundary_version"] = "AZE-ADM1-63332228"
    data["territories"][0]["boundary_note"] = "2021 provider components combined for national location display only; not the legal or 2026 statistical boundary"
    territories, observations = [], []
    current_parent = None
    for row in rows:
        name = row["name"]
        if row["excel_row"] == 5:
            area_id = "AZE"
        elif name.endswith("economic region - total"):
            slug = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_").removesuffix("_TOTAL")
            area_id = "AZE:SSC:ECON:" + slug
            current_parent = area_id
            territories.append({"id": area_id, "name": name.replace(" - total", ""),
                "level": "economic_region", "type": "SSC statistical economic region", "parent_id": "AZE",
                "official_code": None, "boundary_version": None, "source_id": PROJECT_SOURCE,
                "reconciliation_status": "statistical grouping; no official polygon or administrative code joined"})
        elif name == "Baku city - total":
            area_id = "AZE:SSC24:00000002"
            current_parent = area_id
            territories.append({"id": area_id, "name": "Baku city", "level": "city", "type": "city",
                "parent_id": "AZE", "official_code": "00000002", "code_system": "SSC administrative classification 2024",
                "boundary_version": None, "source_id": CODE_SOURCE,
                "reconciliation_status": "2024 code identified; 2026 boundary polygon unverified"})
        else:
            match = matches[row["excel_row"]]
            code = match["candidate_code"]
            adopted = match["official_code_adopted"]
            area_id = ("AZE:SSC24:" + code) if adopted else ("AZE:SSC:ROW:" + str(row["excel_row"]))
            area_type = "city district" if code.endswith("3") else ("city" if name.endswith("city") else "rayon")
            territories.append({"id": area_id, "name": name, "level": "local_administrative_unit",
                "type": area_type if adopted else "SSC source area, type unresolved",
                "parent_id": current_parent, "official_code": code if adopted else None,
                "candidate_official_code": code if not adopted else None,
                "code_system": "SSC administrative classification 2024" if adopted else None,
                "boundary_version": None, "source_id": PROJECT_SOURCE,
                "reconciliation_status": "2024 code identified; 2026 polygon unverified" if adopted else "2026 source calls this district, 2024 classification calls matching area city; hold code pending area correspondence"})
        locator = f"SSC table 1.15, sheet 1.15., Excel row {row['excel_row']} ({name})"
        if isinstance(row["census_2019_raw"], (int, float)):
            observations.append(observation(area_id, IDS["census_2019"], "2019", row["census_2019_raw"], PROJECT_SOURCE, locator + ", column D; based on 2019 census, rounded thousands"))
        elif row["census_2019_raw"] != "..." or name != "Aghdara district":
            raise ValueError(f"Unexpected 2019 missing cell: {name} {row['census_2019_raw']!r}")
        observations.append(observation(area_id, IDS["resident_2026"], "2026-01-01", row["resident_2026"], PROJECT_SOURCE, locator + ", column E"))
        sex_row = sex_match[row["excel_row"]]
        for key, column in (("male_2026", "D"), ("female_2026", "E")):
            observations.append(observation(area_id, IDS[key], "2026-01-01", sex_row["male" if key == "male_2026" else "female"], SEX_SOURCE,
                f"SSC table 1.19, sheet 1.19., Excel row {sex_row['excel_row']} ({name}), column {column}"))
    if len(territories) != 100 or len(observations) != 403:
        raise ValueError(f"Unexpected import coverage: {len(territories)} areas, {len(observations)} values")
    data["territories"] += territories
    data["observations"] += observations
    # Table 1.15 expressly lists each parent and its direct members. This
    # source-backed cohort permits comparison across city/rayon labels without
    # claiming that the statistical economic regions are legal governments.
    area_by_id = {area["id"]: area for area in data["territories"]}
    parent_ids = ["AZE"] + [area["id"] for area in territories if any(child["parent_id"] == area["id"] for child in territories)]
    data["analysis"]["comparisons"] = [{
        "parent_id": parent_id,
        "member_ids": [area["id"] for area in territories if area["parent_id"] == parent_id],
        "label": f"SSC table 1.15 component areas of {area_by_id[parent_id]['name']}",
        "membership_note": "The official SSC table 1.15 explicitly lists this same-date, same-definition cohort under the named parent; direct values are source-reported rounded thousands. No polygon or legal planning-unit equivalence is inferred.",
        "source_ids": [PROJECT_SOURCE],
    } for parent_id in parent_ids]
    unit = "thousand people (rounded to 0.1)"
    data["indicators"] += [
        {"id": IDS["census_2019"], "name": "Resident population, 2019 census basis", "theme": "SSC local population",
         "unit": unit, "definition": "SSC table 1.15 census-based resident population in thousands; the 2019 territory coverage and subsequent 2024 code/2026 economic grouping require historical reconciliation. Aghdara has an explicit missing mark, not zero.",
         "population": "Residents covered by the 2019 census table", "source_id": PROJECT_SOURCE, "aggregation": "none", "measurement_method": "source_reported", "display_decimals": 1},
        {"id": IDS["resident_2026"], "name": "Resident population, 1 January 2026", "theme": "SSC local population",
         "unit": unit, "definition": "SSC table 1.15 resident population estimate at 01.01.2026, expressed in rounded thousands; distinct from WDI national midyear estimates and the 2019 census.",
         "population": "Resident population in SSC statistical geography", "source_id": PROJECT_SOURCE, "aggregation": "none", "measurement_method": "source_reported", "display_decimals": 1},
        {"id": IDS["male_2026"], "name": "Men, 1 January 2026", "theme": "SSC local population",
         "unit": unit, "definition": "Men in the SSC 01.01.2026 resident population table, rounded to 0.1 thousand; avoid using rounded totals to derive exact ratios.",
         "population": "Men in resident population", "source_id": SEX_SOURCE, "aggregation": "none", "measurement_method": "source_reported", "display_decimals": 1},
        {"id": IDS["female_2026"], "name": "Women, 1 January 2026", "theme": "SSC local population",
         "unit": unit, "definition": "Women in the SSC 01.01.2026 resident population table, rounded to 0.1 thousand; avoid using rounded totals to derive exact ratios.",
         "population": "Women in resident population", "source_id": SEX_SOURCE, "aggregation": "none", "measurement_method": "source_reported", "display_decimals": 1},
    ]
    for key, title, note, level in (
        (PROJECT_SOURCE, "SSC demography table 1.15: area, 2019 and 2026 population", "Only rounded 2019 census-basis and 2026 resident population columns adopted; 2019 Aghdara is missing. Area and density columns are inventoried but not adopted.", "national, statistical economic region, city, rayon"),
        (SEX_SOURCE, "SSC demography table 1.19: population by sex, 2026", "101 national/parent/local rows matched by label and total to table 1.15. Settlement rows and urban/rural fields remain unadopted.", "national, statistical economic region, city, rayon, settlement"),
        (CODE_SOURCE, "SSC 2024 administrative territorial classification", "87 first-level official codes enumerated. Three source table district labels correspond to classification city labels; their code adoption remains unresolved. This PDF is not a 2026 boundary polygon.", "city, rayon, city district"),
        (CENSUS_A, "2019 population census Volume A", "Official 470-page census volume acquired from ZIP. Contains multiple demographic, education and employment tables; only catalogue-level inspection, no direct Volume A fields adopted.", "varies by table"),
        (CENSUS_B, "2019 population census Volume B", "Official 584-page census volume acquired from ZIP. Contains household, housing and migration tables; only catalogue-level inspection, no direct Volume B fields adopted.", "varies by table"),
    ):
        filename = {PROJECT_SOURCE: "ssc-area-population-density.xls", SEX_SOURCE: "ssc-population-sex-2026.xls",
                    CODE_SOURCE: "ssc-admin-classification-2024.pdf", CENSUS_A: "ssc-census-2019-volume-a.zip", CENSUS_B: "ssc-census-2019-volume-b.zip"}[key]
        data["sources"].append(source(key, title, SOURCES[filename][0], raw / filename, note, level))
    data["sources"] += [
        {"id": PLAN_LAW, "name": "Azerbaijan Urban Planning and Construction Code", "url": "https://president.az/az/articles/view/5773",
         "publisher": "Official website of the President of Azerbaijan", "reference_period": "2012 enactment; current amendments require verification",
         "geographic_level": "national law; region/rayon/city/settlement plan categories", "status": "not_collected", "retrieved_at": datetime.now(timezone.utc).isoformat(), "license": "terms_review_required",
         "note": "Articles 17–20 define territorial planning types and documents. No local plan approval or current consolidated legal text verified."},
        {"id": PLAN_CATALOG, "name": "State Committee on Urban Planning and Architecture master-plan catalogue",
         "url": "https://arxkom.gov.az/en/sehersalma/bas-planlar", "publisher": "State Committee on Urban Planning and Architecture",
         "reference_period": "catalogue checked 2026-09-26", "geographic_level": "selected cities/regions",
         "status": "not_collected", "retrieved_at": datetime.now(timezone.utc).isoformat(), "license": "terms_review_required",
         "note": "Official plan locations only; individual current plan bodies, approval instruments and implementation reports have not been assessed."},
    ]
    original_features = data["boundaries"]["features"]
    if len(original_features) == 2:
        if {f["properties"]["name"] for f in original_features} != {"Contiguous Azerbaijan", "Nakhchivan Autonomous Republic"}:
            raise ValueError("Unexpected reference geometry roster")
        if {f["properties"]["boundary_version"] for f in original_features} != {"AZE-ADM1-63332228"}:
            raise ValueError("Mixed reference geometry editions")
        coordinates = []
        for feature in original_features:
            geometry = feature["geometry"]
            coordinates += [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        data["boundaries"] = {"type": "FeatureCollection", "features": [{"type": "Feature",
            "properties": {"territory_id": "AZE", "name": "Azerbaijan location outline (2021 reference)",
                           "boundary_version": "AZE-ADM1-63332228", "display_only": True,
                           "source_note": "Two geoBoundaries gbOpen 2021 components combined only for national location display; not a legal or 2026 statistical boundary"},
            "geometry": {"type": "MultiPolygon", "coordinates": coordinates}}]}
    elif len(original_features) != 1 or original_features[0]["properties"].get("territory_id") != "AZE":
        raise ValueError("Unexpected already-combined reference geometry")
    data["country"]["geography_note"] = "SSC 2026 economic-region/population rows are separate from 2024 administrative codes. All 87 first-level code candidates were inventoried; Lankaran, Shaki and Yevlakh source labels say district while the classification says city, so those three official-code joins are held. No 2026 local polygons were verified. The combined 2021 geoBoundaries outline is only national location display."
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in ("subnational_statistics", "boundary_reconciliation", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial", "detail": "101 source rows for 2019 census-basis and 2026 population/sex; Aghdara 2019 missing. 2019 census volumes A/B and other numeric fields remain semantically unaudited; 2026 urban/rural/settlement rows unadopted.",
         "next_action": "Audit all volume tables and numeric fields, reconcile historical geography and expand comparable local themes."},
        {"category": "boundary_reconciliation", "status": "partial", "detail": "2024 code table supplies 84 adopted first-level code joins including Baku; three label-type conflicts held. 2021 two-part provider geometry used only as country outline; no official city/rayon polygons verified.",
         "next_action": "Resolve Lankaran, Shaki, Yevlakh type/coverage and obtain official 2026 municipal/rayon geometry and any 2019 crosswalk."},
        {"category": "planning_documents", "status": "not_collected", "detail": "Urban Planning and Construction Code articles 17–20 and state plan catalogue located. Actual selected-area plan bodies, approval, local budget, implementation and evaluation not acquired.",
         "next_action": "Obtain current law text and official plan body/approval for representative Baku, a rayon, and Nakhchivan; then local fiscal and implementation records."},
    ]
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] + ["azerbaijan-ssc-population-partial-v1"]))
    data["analysis"]["latest_values_only"] = True
    data["analysis"]["default_indicator_id"] = IDS["resident_2026"]
    # The reference WDI series is in people, whereas SSC publishes rounded
    # thousands. The shared population-context card subtracts raw numbers, so
    # do not configure that cross-source comparison without a unit-aware rule.
    data["analysis"].pop("population_context", None)
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inventory = {"source_files": {n: {"sha256": expected, "bytes": (raw / n).stat().st_size}
                                   for n, (_, expected, _) in SOURCES.items()},
                 "field_inventory": field_inventory, "row_counts": {"national": 1, "source_parent_regions": 14,
                 "local_rows": 86, "official_code_candidates": len(matches), "official_codes_held": 3,
                 "sex_rows_matched": len(sex_match)},
                 "official_code_crosswalk": [{"excel_row": k, **v} for k, v in sorted(matches.items())],
                 "exceptions": {"2019_Aghdara": "source ellipsis, not zero", "three_type_mismatches": list(TYPE_MISMATCH),
                                "reference_outline": "2021 provider shapes, display only; no legal/statistical boundary use"},
                 "unassessed_sources": ["2019 census Volume A 470 pages", "2019 census Volume B 584 pages"]}
    (evidence / "AZE_SSC_SOURCE_FIELD_AUDIT.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"local_indicators": len(IDS), "domestic_observations": len(observations),
                      "territories_national_plus_local": 1 + len(territories), "code_rows": len(matches),
                      "held_code_rows": len(TYPE_MISMATCH)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

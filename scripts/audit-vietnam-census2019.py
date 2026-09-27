"""Audit the GSO/UNFPA 2019 census Table 1 before a historical-area import."""

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["total", "male", "female", "urban_total", "urban_male", "urban_female",
          "rural_total", "rural_male", "rural_female"]
TABLE_TITLE = re.compile(r"(?m)^\s*Table\s+(\d+)\.\s+([^\n\r]+)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(project):
    manifest = json.loads((ROOT / "config/vietnam-census2019-source-manifest.json").read_text(
        encoding="utf-8"))["sources"][0]
    pdf = project / manifest["raw_path"]
    require(pdf.stat().st_size == manifest["bytes"], "GSO/UNFPA PDF size changed")
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    require(digest == manifest["sha256"], "GSO/UNFPA PDF hash changed")
    catalogue = project / manifest["catalogue_raw_path"]
    require(catalogue.stat().st_size == manifest["catalogue_bytes"] and
            hashlib.sha256(catalogue.read_bytes()).hexdigest() == manifest["catalogue_sha256"],
            "UNFPA official catalogue original changed")
    text = (project / "evidence/GSO_UNFPA_2019_LAYOUT.txt").read_text(encoding="utf-8")
    require(text.count("\f") == manifest["pdf_pages"], "Extracted PDF page count changed")
    titles = []
    for match in TABLE_TITLE.finditer(text):
        number = int(match.group(1))
        if 1 <= number <= 60 and "Continue" not in match.group(2):
            titles.append({"table": number, "title": match.group(2).strip(),
                           "pdf_page": text.count("\f", 0, match.end()) + 1,
                           "column_assessment": "priority_unassessed" if number != 1 else "selected_table_audited"})
    # The report also contains numbered narrative tables; retain only the first
    # occurrence of each detailed table to avoid treating the text's citations as data.
    first = {}
    for row in titles:
        first.setdefault(row["table"], row)
    require(set(first) == set(range(1, 61)), "Expected all 60 detailed table headings")
    start = text.index("Table 1. POPULATION BY URBAN, RURAL, SEX, SOCIO-ECONOMIC REGION AND PROVINCE, CITY")
    end = text.index("Table 2. POPULATION BY ETHNIC, URBAN, RURAL AND SEX", start)
    table_text = text[start:end]
    rows = []
    section = "country"
    page = text.count("\f", 0, start) + 1
    for line in table_text.splitlines(keepends=True):
        page += line.count("\f")
        stripped = line.strip()
        if stripped == "Socio-economic region":
            section = "socioeconomic_region"
            continue
        if stripped == "Province, city":
            section = "census_province_city_2019"
            continue
        cells = re.split(r"\s{2,}", stripped)
        if len(cells) != 10 or not all(re.fullmatch(r"\d{1,3}(?: \d{3})*", x) for x in cells[1:]):
            continue
        name = cells[0]
        require(name == "ENTIRE COUNTRY" if section == "country" else name != "ENTIRE COUNTRY",
                "Unexpected country row placement")
        values = {key: int(raw.replace(" ", "")) for key, raw in zip(FIELDS, cells[1:])}
        for prefix in ["", "urban_", "rural_"]:
            require(values[prefix + "total"] == values[prefix + "male"] + values[prefix + "female"],
                    f"Sex total differs in {name}/{prefix}")
        for sex in ["total", "male", "female"]:
            require(values[sex] == values["urban_" + sex] + values["rural_" + sex],
                    f"Urban/rural total differs in {name}/{sex}")
        rows.append({"name": name, "section": section, "pdf_page": page, "values": values})
    by_section = {key: [row for row in rows if row["section"] == key]
                  for key in ["country", "socioeconomic_region", "census_province_city_2019"]}
    require({key: len(value) for key, value in by_section.items()} ==
            {"country": 1, "socioeconomic_region": 6, "census_province_city_2019": 63},
            "Table 1 expected 1+6+63 numeric rows")
    country = by_section["country"][0]["values"]
    require(country["total"] == 96208984 and country["urban_total"] == 33122548,
            "2019 country anchor changed")
    for group in ["socioeconomic_region", "census_province_city_2019"]:
        for field in FIELDS:
            actual = sum(row["values"][field] for row in by_section[group])
            require(actual == country[field], f"{group}/{field}: {actual} vs {country[field]}")
    require(len({row["name"] for row in by_section["census_province_city_2019"]}) == 63,
            "Duplicate historical province/city label")
    for section, section_rows in by_section.items():
        for index, row in enumerate(section_rows):
            row["source_row_ordinal"] = index + 1
            row["source_locator"] = (f"Table 1, PDF p.{row['pdf_page']} / printed p.{row['pdf_page']}, " +
                                     ("ENTIRE COUNTRY" if section == "country" else
                                      f"{section} row {index + 1}: {row['name']}"))
    result = {"source_id": manifest["id"], "source_sha256": digest,
              "table_1_title": first[1]["title"], "table_1_fields": FIELDS,
              "table_1_rows": rows, "row_counts": {k: len(v) for k, v in by_section.items()},
              "numeric_cells_audited": len(rows) * len(FIELDS),
              "other_detailed_tables": [first[i] for i in range(2, 61)],
              "assessment_note": "Table 1 has nine direct person-count columns. Tables 2-60 have their own denominators, sample coverage and geography and are priority_unassessed; their numerical columns are not adopted. The completed-results district tables are a separate official publication whose original could not be fetched from NSO in this run."}
    out = project / "evidence/VNM_CENSUS2019_AUDIT.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["row_counts"], "numeric_cells_audited":
                      result["numeric_cells_audited"], "tables_inventory": len(first),
                      "country_total": country["total"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

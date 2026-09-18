#!/usr/bin/env python3
"""Extract a reviewed set of Guatemala 2018 municipal Census indicators."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string


SPECS = [
    {"id": "GTM_CENSUS_FEMALE_PCT", "name": "Female population", "theme": "Population", "unit": "% of population", "file": "cuadro-a1-", "sheet": "A1", "num": ["E"], "den": ["C"], "definition": "Female residents as a percentage of total enumerated population."},
    {"id": "GTM_CENSUS_AGE_0_14_PCT", "name": "Population aged 0–14", "theme": "Population", "unit": "% of population", "file": "cuadro-a1-", "sheet": "A1", "num": ["F", "G", "H"], "den": ["C"], "definition": "Residents aged 0–14 as a percentage of total enumerated population."},
    {"id": "GTM_CENSUS_URBAN_PCT", "name": "Urban population", "theme": "Population", "unit": "% of population", "file": "cuadro-a1-", "sheet": "A1", "num": ["AA"], "den": ["C"], "definition": "Urban residents as a percentage of total enumerated population."},
    {"id": "GTM_CENSUS_BORN_ABROAD_PCT", "name": "Population born abroad", "theme": "Migration", "unit": "% of population", "file": "cuadro-a4-", "sheet": "A4", "num": ["F"], "den": ["C"], "definition": "Residents born in another country as a percentage of total enumerated population."},
    {"id": "GTM_CENSUS_MAYA_PCT", "name": "Maya population", "theme": "Ethnicity", "unit": "% of population", "file": "cuadro-a5-", "sheet": "A5", "num": ["D"], "den": ["C"], "definition": "People identifying as Maya as a percentage of total enumerated population."},
    {"id": "GTM_CENSUS_DISABILITY_PCT", "name": "Population with at least one reported difficulty", "theme": "Disability", "unit": "% of population age 4+", "file": "cuadro-a8-", "sheet": "A8", "num": ["E"], "den": ["C"], "definition": "People age four or older reporting at least one listed functional difficulty as a percentage of the population age four or older."},
    {"id": "GTM_CENSUS_LITERATE_PCT", "name": "Literate population age 7+", "theme": "Education", "unit": "% of population age 7+", "file": "cuadro-a11-", "sheet": "A11", "num": ["F", "G"], "den": ["C"], "definition": "Literate men and women age seven or older as a percentage of the population age seven or older."},
    {"id": "GTM_CENSUS_ECONOMICALLY_ACTIVE_PCT", "name": "Economically active population age 15+", "theme": "Employment", "unit": "% of population age 15+", "file": "cuadro-a13-", "sheet": "A13", "num": ["D"], "den": ["C"], "definition": "Economically active population as a percentage of the population age 15 or older."},
    {"id": "GTM_CENSUS_HOUSEHOLDS_TOTAL", "name": "Census households", "theme": "Housing", "unit": "households", "file": "cuadro-b1-", "sheet": "B1", "direct": "C", "definition": "Total households enumerated in the 2018 Census."},
    {"id": "GTM_CENSUS_HOME_OWNED_PCT", "name": "Households in an owned dwelling", "theme": "Housing", "unit": "% of households", "file": "cuadro-b1-", "sheet": "B1", "num": ["D"], "den": ["C"], "definition": "Households reporting an owned dwelling as a percentage of enumerated households."},
    {"id": "GTM_CENSUS_WATER_IN_DWELLING_PCT", "name": "Households with piped water in the dwelling", "theme": "Basic services", "unit": "% of households", "file": "cuadro-b2-", "sheet": "B2", "num": ["D"], "den": ["C"], "definition": "Households whose main drinking-water source is a pipe in the dwelling as a percentage of enumerated households."},
    {"id": "GTM_CENSUS_SANITATION_DRAINAGE_PCT", "name": "Households with toilet connected to drainage", "theme": "Basic services", "unit": "% of households", "file": "cuadro-b3-", "sheet": "B3", "num": ["D"], "den": ["C"], "definition": "Households with a toilet connected to the drainage network as a percentage of enumerated households."},
    {"id": "GTM_CENSUS_ELECTRIC_LIGHTING_PCT", "name": "Households using grid electricity for lighting", "theme": "Basic services", "unit": "% of households", "file": "cuadro-b4-", "sheet": "B4", "num": ["D"], "den": ["C"], "definition": "Households using the electricity network as their lighting source as a percentage of enumerated households."},
]


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric {label}; got {value!r}")
    return float(value)


def component(value, label):
    if value in (None, "-"):
        return 0.0
    return number(value, label)


def values(sheet, level, spec):
    code_col, name_col = ("A", "B") if level == "department" else ("C", "D")
    code_index, name_index = column_index_from_string(code_col) - 1, column_index_from_string(name_col) - 1
    # Municipality tables repeat department code/name before the municipality
    # columns, so every measure is two columns to the right of its department
    # table counterpart. The source-column audit below retains the published
    # department-table letters while this offset selects the matching measure.
    measure_offset = 0 if level == "department" else 2
    direct_index = column_index_from_string(spec["direct"]) - 1 + measure_offset if spec.get("direct") else None
    numerator_indexes = [column_index_from_string(column) - 1 + measure_offset for column in spec.get("num", [])]
    denominator_indexes = [column_index_from_string(column) - 1 + measure_offset for column in spec.get("den", [])]
    get = lambda row, index: row[index] if index < len(row) else None
    result = []
    for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
        code = row[code_index] if len(row) > code_index else None
        name = row[name_index] if len(row) > name_index else None
        if not isinstance(code, (int, float)) or not isinstance(name, str) or not name.strip():
            continue
        code_text = str(int(code))
        territory_id = f"GTM:C2018:DEP:{code_text}" if level == "department" else f"GTM:C2018:MUN:{code_text}"
        if spec.get("direct"):
            direct = number(get(row, direct_index), f"{sheet.title}!{spec['direct']}{row_number}")
            result.append({"territory_id": territory_id, "name": name.strip(), "value": direct, "numerator": direct, "denominator": None})
            continue
        numerator = sum(component(get(row, index), f"{sheet.title}!{spec['num'][position]}{row_number}") for position, index in enumerate(numerator_indexes))
        denominator = sum(number(get(row, index), f"{sheet.title}!{spec['den'][position]}{row_number}") for position, index in enumerate(denominator_indexes))
        if denominator <= 0:
            raise ValueError(f"Non-positive denominator at {sheet.title} row {row}")
        result.append({"territory_id": territory_id, "name": name.strip(), "value": numerator / denominator * 100, "numerator": numerator, "denominator": denominator})
    expected = 22 if level == "department" else 340
    if len(result) != expected or len({row["territory_id"] for row in result}) != expected:
        raise ValueError(f"{sheet.title} {level} rows: {len(result)}; expected {expected}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    receipt = json.loads((project / "raw/discovered-source-files/receipt.json").read_text(encoding="utf-8-sig"))
    available = [row for row in receipt["receipts"] if row.get("country_area_id") == "GTM" and row.get("status") == "acquired"]
    indicators, observations, sources, audits = [], [], [], []
    existing_sources = set()
    for spec in SPECS:
        receipt_row = next(row for row in available if spec["file"] in row["url"].lower())
        source_id = f"GTM_C2018_{spec['sheet']}_OFFICIAL_TABLES"
        if source_id not in existing_sources:
            existing_sources.add(source_id)
            sources.append({
                "id": source_id,
                "name": receipt_row.get("label") or f"Guatemala Census 2018 {spec['sheet']} tables",
                "publisher": "Instituto Nacional de Estadística de Guatemala",
                "url": receipt_row["url"],
                "status": "ready",
                "retrieved_at": receipt_row.get("completed_at"),
                "reference_period": "2018",
                "sha256": receipt_row["sha256"],
                "bytes": receipt_row["bytes"],
                "license": "Creative Commons Attribution (official catalog record)",
                "geographic_level": "department and municipality",
                "note": "Official Guatemala 2018 Census workbook. AreaData percentage indicators retain their source columns, numerator and denominator.",
            })
        indicators.append({
            "id": spec["id"], "name": spec["name"], "theme": spec["theme"], "unit": spec["unit"],
            "definition": spec["definition"], "definition_id": spec["id"].lower(),
            "population": spec["unit"].removeprefix("% of ") if spec["unit"].startswith("% of ") else "Enumerated households",
            "measurement_method": "source_reported" if spec.get("direct") else "area_data_ratio_from_source_counts",
            "aggregation": "sum" if spec.get("direct") else "official_only", "source_id": source_id,
            "series_family": "census", "display_role": "primary", "display_decimals": 0 if spec.get("direct") else 1,
        })
        book = load_workbook(project / receipt_row["path"], read_only=True, data_only=True)
        try:
            department_rows = values(book[f"{spec['sheet']}_1"], "department", spec)
            municipal_rows = values(book[f"{spec['sheet']}_2"], "municipality", spec)
        finally:
            book.close()
        source_note = f"INE Guatemala 2018 Census {spec['sheet']} official table."
        for row in department_rows + municipal_rows:
            observation = {"territory_id": row["territory_id"], "indicator_id": spec["id"], "period": "2018", "value": round(row["value"], 8), "status": "observed", "source_id": source_id, "footnote": source_note}
            if row["denominator"] is not None:
                observation.update({"provenance": "calculated", "calculation": {"formula": "numerator / denominator * 100", "numerator": row["numerator"], "denominator": row["denominator"], "numerator_fields": spec["num"], "denominator_fields": spec["den"]}})
            observations.append(observation)
        national_numerator = sum(row["numerator"] for row in department_rows)
        if spec.get("direct"):
            national_value, national_denominator = national_numerator, None
        else:
            national_denominator = sum(row["denominator"] for row in department_rows)
            national_value = national_numerator / national_denominator * 100
        national = {"territory_id": "GTM", "indicator_id": spec["id"], "period": "2018", "value": round(national_value, 8), "status": "observed", "source_id": source_id, "footnote": f"AreaData complete-cover result from all 22 official department rows in {spec['sheet']}_1."}
        if national_denominator is not None:
            national.update({"provenance": "calculated", "calculation": {"formula": "sum(department numerators) / sum(department denominators) * 100", "numerator": national_numerator, "denominator": national_denominator, "numerator_fields": spec["num"], "denominator_fields": spec["den"], "complete_department_count": 22}})
        observations.append(national)
        audits.append({"indicator_id": spec["id"], "department_count": len(department_rows), "municipality_count": len(municipal_rows), "national_value": national_value, "source_id": source_id})
    output = project / "evidence/GTM_CENSUS_THEME_EXTRACTION.json"
    output.write_text(json.dumps({"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "GTM", "period": "2018", "indicators": indicators, "sources": sources, "observations": observations, "audit": audits}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"indicators": len(indicators), "sources": len(sources), "observations": len(observations), "audit_rows": len(audits), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

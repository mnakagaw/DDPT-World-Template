#!/usr/bin/env python3
"""Extract reviewed Belize 2022 Census indicators for national and district areas."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


DISTRICTS = ["Corozal", "Orange Walk", "Belize", "Cayo", "Stann Creek", "Toledo"]
TERRITORIES = {name: f"BLZ:C2022:DIST:{index}" for index, name in enumerate(DISTRICTS, 1)}


def receipt_for(receipts, needle: str):
    return next(row for row in receipts if row.get("status") == "acquired" and needle.lower() in row.get("url", "").lower())


def source(receipt, source_id: str, name: str, level: str, note: str):
    return {
        "id": source_id,
        "name": name,
        "publisher": "Statistical Institute of Belize",
        "url": receipt["url"],
        "status": "ready",
        "retrieved_at": receipt.get("completed_at"),
        "reference_period": "2022",
        "sha256": receipt["sha256"],
        "bytes": receipt["bytes"],
        "license": "Reuse terms not stated; AreaData publishes source-attributed factual observations only.",
        "geographic_level": level,
        "note": note,
    }


def indicator(indicator_id, name, theme, unit, definition, source_id, population, method="area_data_ratio_from_source_counts", decimals=1, source_locator=None):
    row = {
        "id": indicator_id,
        "name": name,
        "theme": theme,
        "unit": unit,
        "definition": definition,
        "definition_id": indicator_id.lower(),
        "population": population,
        "measurement_method": method,
        "aggregation": "official_only",
        "source_id": source_id,
        "series_family": "census",
        "display_role": "primary",
        "display_decimals": decimals,
    }
    if source_locator:
        row["source_locator"] = source_locator
    return row


def observation(territory_id, indicator_id, value, source_id, numerator=None, denominator=None, footnote=None):
    row = {
        "territory_id": territory_id,
        "indicator_id": indicator_id,
        "period": "2022",
        "value": round(float(value), 8),
        "status": "observed",
        "source_id": source_id,
        "footnote": footnote or "Statistical Institute of Belize, 2022 Population and Housing Census.",
    }
    if numerator is not None and denominator is not None:
        row["provenance"] = "calculated"
        row["calculation"] = {
            "formula": "numerator / denominator * 100",
            "numerator": float(numerator),
            "denominator": float(denominator),
        }
    return row


def ratio_rows(indicator_id, source_id, numerators, denominators, include_national=True):
    names = ["National", *DISTRICTS] if include_national else DISTRICTS
    ids = ["BLZ", *TERRITORIES.values()] if include_national else list(TERRITORIES.values())
    return [observation(tid, indicator_id, num / den * 100, source_id, num, den) for tid, name, num, den in zip(ids, names, numerators, denominators)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    receipt_rows = json.loads((project / "raw/discovered-source-files/receipt.json").read_text(encoding="utf-8-sig"))["receipts"]
    receipt_rows = [row for row in receipt_rows if row.get("country_area_id") == "BLZ"]
    general_r = receipt_for(receipt_rows, "GeneralCharacteristics")
    education_r = receipt_for(receipt_rows, "Education.xlsx")
    findings_r = receipt_for(receipt_rows, "CensusKeyFindingsReport_2022")
    mpi_r = receipt_for(receipt_rows, "MultidimensionalPovertyIndexReport_2022")

    sources = [
        source(general_r, "BLZ_C2022_GENERAL_TABLES_REVIEWED", "Belize Census 2022 general-characteristics tables", "national and district", "Reviewed XLSX tables for population, age, sex, urban/rural status and ethnicity."),
        source(education_r, "BLZ_C2022_EDUCATION_TABLES_REVIEWED", "Belize Census 2022 education tables", "national and district", "Reviewed XLSX literacy table; ratios retain source numerator and denominator."),
        source(findings_r, "BLZ_C2022_KEY_FINDINGS_REVIEWED", "Belize Census 2022 Key Findings Report", "national and district", "Reviewed PDF tables for households, water, sanitation, electricity, disability, migration and health."),
        source(mpi_r, "BLZ_C2022_MPI_REVIEWED", "Belize Census 2022 Multidimensional Poverty Index Report", "national and district", "Reviewed PDF Tables 6 and 7 for poverty, food-security deprivation, employment informality and health-service access."),
    ]
    indicators = []
    observations = []
    audit = []

    general_path = project / general_r["path"]
    wb = load_workbook(general_path, read_only=True, data_only=True)
    try:
        # Sex ratios and district totals.
        sex = wb["Sex_Ratio"]
        district_rows = {str(sex.cell(row=r, column=2).value).strip(): r for r in range(5, sex.max_row + 1)}
        names = ["National", *DISTRICTS]
        totals = [float(sex.cell(row=district_rows[name], column=7).value) for name in names]
        females = [float(sex.cell(row=district_rows[name], column=9).value) for name in names]
        indicators.append(indicator("BLZ_CENSUS_FEMALE_PCT", "Female population", "Population", "% of population", "Female residents as a percentage of the enumerated population.", "BLZ_C2022_GENERAL_TABLES_REVIEWED", "enumerated population"))
        observations.extend(ratio_rows("BLZ_CENSUS_FEMALE_PCT", "BLZ_C2022_GENERAL_TABLES_REVIEWED", females, totals))

        # Five-year age table. Each geography begins with Total followed by 0-14 bands.
        age = wb["Age_Groups"]
        age_blocks = {}
        current = None
        for r in range(4, age.max_row + 1):
            label = age.cell(r, 2).value
            band = age.cell(r, 3).value
            value = age.cell(r, 5).value
            if label in names and band == "Total":
                current = str(label)
                age_blocks[current] = {"total": float(value), "young": 0.0}
            elif current and band in {"Less than 1", "1-4", "5-9", "10-14"}:
                age_blocks[current]["young"] += float(value)
        indicators.append(indicator("BLZ_CENSUS_AGE_0_14_PCT", "Population aged 0–14", "Population", "% of population", "Residents aged 0–14 as a percentage of the enumerated population.", "BLZ_C2022_GENERAL_TABLES_REVIEWED", "enumerated population"))
        observations.extend(ratio_rows("BLZ_CENSUS_AGE_0_14_PCT", "BLZ_C2022_GENERAL_TABLES_REVIEWED", [age_blocks[n]["young"] for n in names], [age_blocks[n]["total"] for n in names]))

        # Urban population: the official table identifies rural residuals for every district.
        admin = wb["Admin_Area"]
        admin_values = {str(admin.cell(r, 2).value).strip(): float(admin.cell(r, 4).value) for r in range(4, admin.max_row + 1) if admin.cell(r, 2).value and isinstance(admin.cell(r, 4).value, (int, float))}
        urban_nums = [admin_values["Urban"]]
        urban_dens = [admin_values["National"]]
        for name in DISTRICTS:
            urban_nums.append(admin_values[name] - admin_values[f"{name} Rural"])
            urban_dens.append(admin_values[name])
        indicators.append(indicator("BLZ_CENSUS_URBAN_PCT", "Urban population", "Population", "% of population", "Urban residents as a percentage of the enumerated population; district urban values equal district total minus its published rural subtotal.", "BLZ_C2022_GENERAL_TABLES_REVIEWED", "enumerated population"))
        observations.extend(ratio_rows("BLZ_CENSUS_URBAN_PCT", "BLZ_C2022_GENERAL_TABLES_REVIEWED", urban_nums, urban_dens))

        # Maya (Ketchi + Mopan + Yucatec) from the official ethnicity table.
        eth = wb["Ethnicity_by_District"]
        col_by_name = {"National": 3, "Corozal": 6, "Orange Walk": 9, "Belize": 12, "Cayo": 15, "Stann Creek": 18, "Toledo": 21}
        row_by_eth = {str(eth.cell(r, 2).value).strip(): r for r in range(5, eth.max_row + 1) if eth.cell(r, 2).value}
        maya_nums, maya_dens = [], []
        for name in names:
            col = col_by_name[name]
            den = float(eth.cell(row_by_eth["Total"], col).value)
            vals = []
            for ethnicity in ("Maya Ketchi", "Maya Mopan", "Maya Yucatec"):
                value = eth.cell(row_by_eth[ethnicity], col).value
                vals.append(float(value) if isinstance(value, (int, float)) else 0.0)
            maya_nums.append(sum(vals)); maya_dens.append(den)
        indicators.append(indicator("BLZ_CENSUS_MAYA_PCT", "Maya population", "Ethnicity", "% of population", "People identifying as Ketchi, Mopan or Yucatec Maya as a percentage of the enumerated population; suppressed values under 10 are not imputed.", "BLZ_C2022_GENERAL_TABLES_REVIEWED", "enumerated population"))
        observations.extend(ratio_rows("BLZ_CENSUS_MAYA_PCT", "BLZ_C2022_GENERAL_TABLES_REVIEWED", maya_nums, maya_dens))
    finally:
        wb.close()

    # Adult literacy from the official education workbook.
    wb = load_workbook(project / education_r["path"], read_only=True, data_only=True)
    try:
        ws = wb["Literacy_by_District"]
        lit_names = {"National": "Total Population", **{name: name for name in DISTRICTS}}
        row_for = {}
        for r in range(5, 12):
            label = str(ws.cell(r, 2).value).strip()
            row_for[label] = r
        nums = [float(ws.cell(row_for[lit_names[name]], 4).value) for name in names]
        dens = [float(ws.cell(row_for[lit_names[name]], 3).value) for name in names]
    finally:
        wb.close()
    indicators.append(indicator("BLZ_CENSUS_ADULT_LITERACY_PCT", "Adult literacy rate", "Education", "% of population age 15+", "People age 15 or older who completed at least Standard Five as a percentage of the population age 15 or older.", "BLZ_C2022_EDUCATION_TABLES_REVIEWED", "population age 15+"))
    observations.extend(ratio_rows("BLZ_CENSUS_ADULT_LITERACY_PCT", "BLZ_C2022_EDUCATION_TABLES_REVIEWED", nums, dens))

    # District and national household/service counts transcribed from the printed
    # Appendix B tables. The component rows are retained in `value_audit` so
    # every displayed ratio can be reproduced from the PDF.
    households = [110719, 12148, 14285, 35063, 26818, 12719, 9687]
    service_specs = [
        ("BLZ_CENSUS_HOUSEHOLDS_TOTAL", "Census households", "Housing", "households", "Enumerated households in the 2022 Census.", households, None, 0, "Key Findings Report Appendix B, Tables B.9, B.11 and B.13, printed pages 168–170 (Total rows)"),
        ("BLZ_CENSUS_PIPED_WATER_PCT", "Households using public or private piped water", "Basic services", "% of households", "Households whose main water source is public or private piped water.", [101940, 10648, 13056, 33567, 24807, 11870, 7991], households, 1, "Key Findings Report Appendix B, Table B.9, printed page 168; public-piped plus private-piped rows divided by Total"),
        ("BLZ_CENSUS_IMPROVED_SANITATION_PCT", "Households with sewer or septic sanitation", "Basic services", "% of households", "Households using a toilet connected to public sewer or a septic tank.", [84688, 8223, 10033, 33499, 20419, 9066, 3448], households, 1, "Key Findings Report Appendix B, Table B.11, printed page 169; BWS-sewer plus septic-tank rows divided by Total"),
        ("BLZ_CENSUS_ELECTRIC_LIGHTING_PCT", "Households using electricity, generator or solar lighting", "Basic services", "% of households", "Households whose main lighting source is Belize Electricity Limited, a private generator, solar power or a drop from a neighbour.", [105197, 11297, 13404, 34434, 25231, 12218, 8612], households, 1, "Key Findings Report Appendix B, Table B.13, printed page 170; BEL plus private-generator plus solar plus neighbour-drop rows divided by Total"),
    ]
    value_audit = []
    for iid, name, theme, unit, definition, nums0, dens0, decimals, locator in service_specs:
        method = "source_reported" if dens0 is None else "area_data_ratio_from_source_counts"
        indicators.append(indicator(iid, name, theme, unit, definition, "BLZ_C2022_KEY_FINDINGS_REVIEWED", "enumerated households", method, decimals, locator))
        tids = ["BLZ", *TERRITORIES.values()]
        if dens0 is None:
            observations.extend(observation(tid, iid, num, "BLZ_C2022_KEY_FINDINGS_REVIEWED", footnote=locator) for tid, num in zip(tids, nums0))
        else:
            rows = [observation(tid, iid, num / den * 100, "BLZ_C2022_KEY_FINDINGS_REVIEWED", num, den, locator) for tid, num, den in zip(tids, nums0, dens0)]
            observations.extend(rows)
            value_audit.extend({"territory_id": row["territory_id"], "indicator_id": iid, "source_locator": locator, "numerator": row["calculation"]["numerator"], "denominator": row["calculation"]["denominator"], "value": row["value"]} for row in rows)

    # Census MPI report Tables 6 and 7; all values are source-reported percentages.
    mpi_specs = [
        ("BLZ_CENSUS_MPI_INCIDENCE_PCT", "Population in multidimensional poverty", "Poverty", "% of population", "Incidence of multidimensional poverty under the official Belize Census MPI method.", [26.6, 35.6, 29.2, 11.3, 23.9, 27.4, 63.5]),
        ("BLZ_CENSUS_FOOD_INSECURITY_DEPRIVED_PCT", "Population deprived in food security", "Nutrition", "% of population", "Uncensored Census MPI food-security deprivation headcount ratio.", [16.4, 16.5, 22.0, 14.7, 14.6, 13.0, 22.4]),
        ("BLZ_CENSUS_INFORMAL_EMPLOYMENT_DEPRIVED_PCT", "Population deprived by informal employment", "Employment", "% of population", "Uncensored Census MPI informal-employment deprivation headcount ratio.", [38.0, 49.6, 46.2, 31.7, 39.2, 28.1, 39.9]),
        ("BLZ_CENSUS_HEALTH_ACCESS_DEPRIVED_PCT", "Population deprived in access to health services", "Health", "% of population", "Uncensored Census MPI health-service-access deprivation headcount ratio.", [0.7, 2.5, 1.1, 0.1, 0.5, 0.2, 0.8]),
        ("BLZ_CENSUS_SANITATION_DEPRIVED_PCT", "Population deprived in improved sanitation", "Basic services", "% of population", "Uncensored Census MPI improved-sanitation deprivation headcount ratio.", [22.8, 29.5, 24.3, 8.7, 23.3, 22.8, 53.0]),
    ]
    tids = ["BLZ", *TERRITORIES.values()]
    for iid, name, theme, unit, definition, values in mpi_specs:
        indicators.append(indicator(iid, name, theme, unit, definition, "BLZ_C2022_MPI_REVIEWED", "enumerated population", "source_reported", 1))
        observations.extend(observation(tid, iid, value, "BLZ_C2022_MPI_REVIEWED") for tid, value in zip(tids, values))

    # National-only official Census measures. They remain national and are never copied to districts.
    national_specs = [
        ("BLZ_CENSUS_DISABILITY_PCT", "Population with a reported disability", "Disability", "% of population", "People reported with a disability as a percentage of the enumerated population.", 40182, 397483, "BLZ_C2022_KEY_FINDINGS_REVIEWED"),
        ("BLZ_CENSUS_FOREIGN_BORN_PCT", "Foreign-born population", "Migration", "% of population", "Foreign-born residents as a percentage of the enumerated population.", 45644, 397483, "BLZ_C2022_KEY_FINDINGS_REVIEWED"),
    ]
    for iid, name, theme, unit, definition, num, den, sid in national_specs:
        indicators.append(indicator(iid, name, theme, unit, definition, sid, "enumerated population"))
        observations.append(observation("BLZ", iid, num / den * 100, sid, num, den))

    if len({row["id"] for row in indicators}) != len(indicators):
        raise ValueError("Duplicate indicator id")
    if any(not (0 <= row["value"] <= 100) for row in observations if row["indicator_id"] != "BLZ_CENSUS_HOUSEHOLDS_TOTAL"):
        raise ValueError("Percentage outside 0-100")
    for iid in [row["id"] for row in indicators]:
        matches = [row for row in observations if row["indicator_id"] == iid]
        audit.append({"indicator_id": iid, "observation_count": len(matches), "territories": [row["territory_id"] for row in matches], "source_id": matches[0]["source_id"]})

    out = project / "evidence/BLZ_CENSUS_THEME_EXTRACTION.json"
    out.write_text(json.dumps({
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "country_area_id": "BLZ",
        "period": "2022",
        "indicators": indicators,
        "sources": sources,
        "observations": observations,
        "audit": audit,
        "value_audit": value_audit,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"indicators": len(indicators), "sources": len(sources), "observations": len(observations), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()

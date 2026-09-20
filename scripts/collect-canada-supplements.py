#!/usr/bin/env python3
"""Build Canada theme supplements from retained official/API receipts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


DISABILITY_URL = "https://www150.statcan.gc.ca/n1/en/catalogue/1310037401"
WB_URL = "https://api.worldbank.org/v2/country/CAN/indicator/{indicator}?format=json&per_page=70"
WB_FIELDS = {
    "SH.H2O.BASW.ZS": ("CAN_WB_BASIC_DRINKING_WATER_PCT", "People using at least basic drinking water services", "Basic services", "drinking_water"),
    "SH.STA.BASS.ZS": ("CAN_WB_BASIC_SANITATION_PCT", "People using at least basic sanitation services", "Basic services", "sanitation"),
    "SP.URB.TOTL.IN.ZS": ("CAN_WB_URBAN_POPULATION_PCT", "Urban population", "Population", "urban_rural"),
    "SN.ITK.DEFC.ZS": ("CAN_WB_UNDERNOURISHMENT_PCT", "Prevalence of undernourishment", "Health and nutrition", "nutrition"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw, out = Path(args.raw).resolve(), Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    disability_zip = raw / "canada-disability-2022.zip"
    with zipfile.ZipFile(disability_zip) as archive, archive.open("13100374.csv") as stream:
        rows = list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig")))
    selected = [row for row in rows if row["REF_DATE"] == "2022"
                and row["Age group"] == "Total, 15 years and over"
                and row["Gender"] == "Total, gender"
                and row["Disability"] == "Persons with disabilities"
                and row["Estimates"] == "Percentage of persons"
                and (row["GEO"] == "Canada" or row["DGUID"].startswith("2021A0002"))]
    if len(selected) != 14 or any(not row["VALUE"] for row in selected):
        raise RuntimeError(f"Expected Canada plus 13 province/territory disability rows, got {len(selected)}")

    observations = []
    for row in selected:
        territory_id = "CAN" if row["GEO"] == "Canada" else f"CAN:PR:{row['DGUID'][-2:]}"
        observations.append({
            "territory_id": territory_id,
            "indicator_id": "CAN_CSD2022_DISABILITY_PCT_15PLUS",
            "period": "2022",
            "value": float(row["VALUE"]),
            "status": "observed",
            "source_id": "canada-statcan-disability-2022",
            "definition": "Persons aged 15 years and over with one or more disabilities that limited them in their daily activities, as a percentage of persons aged 15 years and over.",
            "definition_id": "CAN_CSD2022_DISABILITY_PCT_15PLUS",
            "unit": "%",
            "population": "Persons aged 15 years and over",
            "measurement_method": "survey_estimate",
            "source_locator": f"Statistics Canada table 13-10-0374-01; {row['GEO']}; vector {row['VECTOR']}",
        })

    indicators = [{
        "id": "CAN_CSD2022_DISABILITY_PCT_15PLUS",
        "name": "Persons with disabilities, age 15+",
        "theme": "Health and disability",
        "unit": "%",
        "definition": "Persons aged 15 years and over with one or more disabilities that limited them in their daily activities, as a percentage of persons aged 15 years and over.",
        "definition_id": "CAN_CSD2022_DISABILITY_PCT_15PLUS",
        "population": "Persons aged 15 years and over",
        "measurement_method": "survey_estimate",
        "aggregation": "none",
        "period_policy": "fixed_source_period",
        "series_family": "survey",
        "display_role": "primary",
        "source_id": "canada-statcan-disability-2022",
        "source_locator": "Table 13-10-0374-01",
    }]
    sources = [{
        "id": "canada-statcan-disability-2022",
        "name": "Persons with and without disabilities, 2022",
        "publisher": "Statistics Canada",
        "url": DISABILITY_URL,
        "status": "ready",
        "retrieved_at": datetime.now(timezone.utc).date().isoformat(),
        "reference_period": "2022",
        "geographic_level": "Canada and province or territory",
        "license": "Statistics Canada Open Licence",
        "license_url": "https://www.statcan.gc.ca/en/reference/licence",
        "note": "Official Canadian Survey on Disability estimate. It is not a census count and is not copied to census divisions or subdivisions.",
    }]

    latest = {}
    for wb_id, (indicator_id, name, theme, inventory_theme) in WB_FIELDS.items():
        path = raw / f"wb-{wb_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        candidates = [row for row in payload[1] if row.get("value") is not None]
        if not candidates:
            raise RuntimeError(f"No non-missing World Bank observation for {wb_id}")
        row = candidates[0]
        latest[inventory_theme] = {"indicator_id": indicator_id, "period": str(row["date"]), "value": row["value"], "wb_id": wb_id}
        definition = row.get("indicator", {}).get("value") or name
        source_id = f"canada-wb-{wb_id}"
        sources.append({
            "id": source_id, "name": definition, "publisher": "World Bank",
            "url": WB_URL.format(indicator=wb_id), "status": "ready",
            "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": str(row["date"]),
            "geographic_level": "Canada", "license": "World Bank Data Terms of Use",
            "license_url": "https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
            "note": "International-reference national series. It is not copied to Canadian provinces, census divisions or subdivisions.",
        })
        indicators.append({
            "id": indicator_id, "name": definition, "theme": theme, "unit": "%", "definition": definition,
            "definition_id": wb_id, "population": "Canada, source-defined population", "measurement_method": "international_reference_estimate",
            "aggregation": "none", "period_policy": "latest_non_missing_source_period", "series_family": "international_reference",
            "display_role": "context", "source_id": source_id, "source_locator": wb_id,
        })
        observations.append({
            "territory_id": "CAN", "indicator_id": indicator_id, "period": str(row["date"]), "value": row["value"],
            "status": "observed", "source_id": source_id, "definition": definition, "definition_id": wb_id, "unit": "%",
            "population": "Canada, source-defined population", "measurement_method": "international_reference_estimate",
            "source_locator": f"World Bank indicator {wb_id}; Canada; {row['date']}",
        })

    receipts = []
    for path in sorted(raw.iterdir()):
        if path.is_file():
            receipts.append({"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size})
    audit = {
        "schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "CAN",
        "status": "official_disability_and_country_reference_supplements_collected",
        "counts": {"disability_observations": len(selected), "national_reference_observations": len(WB_FIELDS)},
        "latest_reference_values": latest,
        "scope_note": "Disability is available for Canada and 13 provinces/territories. Water, sanitation, urban and undernourishment observations are national only and are not inferred for lower areas.",
        "receipts": receipts,
    }
    bundle = {"schema_version": "1.0", "country_area_id": "CAN", "sources": sources, "indicators": indicators, "observations": observations, "audit": audit}
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out.with_name("canada-supplements-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()

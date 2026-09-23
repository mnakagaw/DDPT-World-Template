"""Extract exact-place, consistently sliced series from the official SDG archive.

The SDG portal combines custodian-agency statistics. Its published geographic
rows are retained as observations; percentages are never summed or averaged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


# One explicitly named population/dimension per indicator. Missing numeric
# values and threshold strings such as '<2.5' are left absent, not coerced.
SLICES = {
    "SI_POV_DAY1": ("International poverty, below $3/day (2021 PPP)", "Poverty", {"Age": "ALLAGE", "Sex": "BOTHSEX", "Location": "ALLAREA", "Education level": "NA"}),
    "SN_ITK_DEFC": ("Prevalence of undernourishment", "Food and nutrition", {"Age": "NA", "Sex": "NA", "Location": "NA", "Education level": "NA"}),
    "SH_H2O_SAFE": ("Safely managed drinking water", "Basic services", {"Age": "NA", "Sex": "NA", "Location": "ALLAREA", "Education level": "NA"}),
    "EG_ACS_ELEC": ("Access to electricity", "Basic services", {"Age": "NA", "Sex": "NA", "Location": "ALLAREA", "Education level": "NA"}),
    "IT_USE_ii99": ("Internet use", "Connectivity", {"Age": "NA", "Sex": "BOTHSEX", "Location": "NA", "Education level": "NA"}),
    "SE_TOT_CPLR": ("Primary education completion", "Education", {"Age": "NA", "Sex": "BOTHSEX", "Location": "ALLAREA", "Education level": "PRIMAR"}),
    "SH_STA_MORT": ("Maternal mortality ratio", "Health", {"Age": "NA", "Sex": "FEMALE", "Location": "NA", "Education level": "NA"}),
    "SL_TLF_UEM": ("Unemployment rate, age 15+", "Employment", {"Age": "15+", "Sex": "BOTHSEX", "Location": "NA", "Education level": "NA"}),
    "SL_TLF_NEET": ("Youth not in employment, education or training, age 15–24", "Employment", {"Age": "15-24", "Sex": "BOTHSEX", "Location": "NA", "Education level": "NA"}),
    "VC_IHR_PSRC": ("Intentional homicide victims per 100,000 people", "Safety", {"Age": "NA", "Sex": "BOTHSEX", "Location": "NA", "Education level": "NA"}),
}

UNITS = {"SH_STA_MORT": "PER_100000_LIVE_BIRTHS", "VC_IHR_PSRC": "PER_100000_POP"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    code_to_id = {str(int(area["official_code"])): area["id"] for area in registry["territories"] if area.get("official_code") and area["id"] != "CUSTOM:CAM-CAR"}
    code_to_id["1"] = "WLD"
    archive_hash = sha256(args.archive)
    records = {}
    source_labels = {code: set() for code in SLICES}
    descriptions = {}
    with zipfile.ZipFile(args.archive) as bundle:
        names = [name for name in bundle.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"Expected one SDG CSV in archive; got {names}")
        with bundle.open(names[0]) as stream:
            rows = csv.DictReader((line.decode("utf-8-sig") for line in stream))
            extra_dimensions = [field for field in rows.fieldnames[rows.fieldnames.index("Units") + 1:] if field not in {"Education level", "Quantile", "Reporting Type", "Observation Status"}]
            for row in rows:
                code = row["SeriesCode"]
                if code not in SLICES or row["GeoAreaCode"] not in code_to_id or row["TimePeriod"] not in {str(year) for year in range(2015, 2026)}:
                    continue
                name, theme, dimensions = SLICES[code]
                expected_quantile = "_T" if code == "SE_TOT_CPLR" else "NA"
                if any(row.get(field) != expected for field, expected in dimensions.items()) or row["Quantile"] != expected_quantile or row["Reporting Type"] != "G" or any(row.get(field) not in {"NA", ""} for field in extra_dimensions):
                    continue
                if row["Units"] != UNITS.get(code, "PERCENT"):
                    continue
                try:
                    value = float(row["Value"])
                except ValueError:
                    continue
                if not (-1000000 < value < 1000000) or row["Units"] == "PERCENT" and not (0 <= value <= 100):
                    continue
                area_id = code_to_id[row["GeoAreaCode"]]
                indicator_id = f"UN_SDG_{code}"
                key = area_id, indicator_id, row["TimePeriod"]
                if key in records:
                    if records[key]["value"] != value:
                        raise ValueError(f"Conflicting exact SDG series cell: {key}")
                    continue
                records[key] = {"territory_id": area_id, "indicator_id": indicator_id, "period": row["TimePeriod"], "value": value, "status": "observed", "source_id": "un-sdg-2026q2-archive", "source_publisher": row["Source"], "nature": row["Nature"], "observation_status": row["Observation Status"]}
                source_labels[code].add(row["Source"])
                descriptions[code] = row["SeriesDescription"]
    observations = [records[key] for key in sorted(records)]
    indicators = []
    for code, (name, theme, dimensions) in SLICES.items():
        indicator_id = f"UN_SDG_{code}"
        rows = [row for row in observations if row["indicator_id"] == indicator_id]
        if not rows:
            raise ValueError(f"No exact observations for {code} and declared dimensions")
        unit = "per 100,000 live births" if code == "SH_STA_MORT" else "per 100,000 people" if code == "VC_IHR_PSRC" else "%"
        indicators.append({"id": indicator_id, "name": name, "theme": theme, "unit": unit, "definition": descriptions[code] + f"; SDG series {code}; selected dimensions " + ", ".join(f"{key}={value}" for key, value in dimensions.items()) + f", Quantile={'_T' if code == 'SE_TOT_CPLR' else 'NA'}. International custodian series distributed through the UN SDG Global Database; may be an estimate rather than a census count.", "definition_id": f"un-sdg-2026q2-{code.lower()}", "population": "Exact published geographic row and declared statistical dimensions", "measurement_method": "UN SDG Global Database, custodian-agency series", "aggregation": "official_only", "series_family": "international_reference", "display_role": "supplementary", "period_policy": "same_period", "display_decimals": 1, "visualization": "percent_bar" if unit == "%" else "trend", "source_id": "un-sdg-2026q2-archive"})
    source = {"id": "un-sdg-2026q2-archive", "name": "UN SDG Global Database — 2026 Q2.2 archive", "publisher": "United Nations Statistics Division; original estimates and reports from named custodian agencies", "url": "https://unstats.un.org/sdgs/indicators/database/archive/", "status": "ready", "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "reference_period": "2015–2025, varying by series and geographic row", "geographic_level": "world_multi_scope_series", "license": "UN SDG database terms; original custodian sources remain attributed", "raw_redistribution_status": "not_in_public_site", "source_files": [{"url": "https://unstats.un.org/sdgs/indicators/database/archive/2026_Q2.2_AllData_After_20260824_CSV.zip", "sha256": archive_hash, "bytes": args.archive.stat().st_size}], "series_custodians": {code: sorted(source_labels[code]) for code in SLICES}, "note": "Only exact UN M49 world, region and country/area rows with the recorded slice are adopted. The custom AreaData region is missing for non-additive rates. Some country/area codes have no comparable row."}
    summary = {"observations": len(observations), "by_indicator": {code: len([row for row in observations if row["indicator_id"] == f"UN_SDG_{code}"]) for code in SLICES}, "geographic_ids": len({row["territory_id"] for row in observations}), "periods": sorted({row["period"] for row in observations})}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema_version": "1.0", "generated_at": source["retrieved_at"], "source": source, "indicators": indicators, "observations": observations, "summary": summary}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(summary, flush=True)


if __name__ == "__main__":
    main()

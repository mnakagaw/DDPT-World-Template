#!/usr/bin/env python3
"""Build an AreaData Dominican Republic adapter from audited DDPT/official data.

The DDPT thematic bundle is treated as a normalized derivative, not as a new
primary source.  Every adopted field retains its ONE/SNS source identity,
numerator, denominator and source year.  National context for ethnicity,
nutrition and poverty is never assigned to a lower territory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


CENSUS_URL = "https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/"
BOUNDARY_URL = "https://geoportal.iderd.gob.do/layers/geonode:RD_MUNICIPIOS/metadata_detail"
HEALTH_URL = "https://datos.gob.do/dataset/establecimientos-de-salud-sns"
ETHNICITY_URL = "https://www.one.gob.do/media/lu3gwjm0/informe-general-enhogar-2021.pdf"
NUTRITION_URL = "https://api.worldbank.org/v2/country/DOM/indicator/SN.ITK.DEFC.ZS?format=json&per_page=100"
POVERTY_URL = "https://www.one.gob.do/media/bbep4boj/boletin-pobreza-monetaria-2024.pdf"

ADOPTED = {
    "population_total": "poblacion-total",
    "age_sex": "mujeres-poblacion",
    "households_housing": "viviendas-desocupadas",
    "drinking_water": "agua-acueducto-vivienda",
    "sanitation": "sin-servicio-sanitario",
    "electricity": "electricidad-tendido-publico",
    "education_literacy": "sin-nivel-instruccion",
    "employment": "participacion-laboral",
    "disability": "discapacidad-censo-5mas",
    "migration": "poblacion-nacida-extranjero",
    "urban_rural": "poblacion-urbana",
    "health": "establecimientos-salud",
}

IDS = {
    "poblacion-total": "DOM_C2022_POP_TOTAL",
    "mujeres-poblacion": "DOM_C2022_FEMALE_PCT",
    "viviendas-desocupadas": "DOM_C2022_VACANT_DWELLINGS_PCT",
    "agua-acueducto-vivienda": "DOM_C2022_INDOOR_AQUEDUCT_WATER_PCT",
    "sin-servicio-sanitario": "DOM_C2022_NO_SANITARY_SERVICE_PCT",
    "electricidad-tendido-publico": "DOM_C2022_PUBLIC_GRID_LIGHTING_PCT",
    "sin-nivel-instruccion": "DOM_C2022_NO_EDUCATION_LEVEL_PCT",
    "participacion-laboral": "DOM_C2022_LABOR_FORCE_PARTICIPATION_PCT",
    "discapacidad-censo-5mas": "DOM_C2022_FUNCTIONAL_DIFFICULTY_PCT",
    "poblacion-nacida-extranjero": "DOM_C2022_FOREIGN_BORN_PCT",
    "poblacion-urbana": "DOM_C2022_URBAN_PCT",
    "establecimientos-salud": "DOM_SNS_HEALTH_FACILITIES",
    "ethnicity": "DOM_ENHOGAR2021_AFRODESCENDANT_PCT",
    "nutrition": "DOM_WB_UNDERNOURISHMENT_PCT",
    "poverty": "DOM_ONE_MONETARY_POVERTY_PCT",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "AreaData evidence collector/0.10"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def compact_code(value) -> str:
    return str(value or "").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ddpt-data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    src = Path(args.ddpt_data).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit(f"Refusing existing output directory: {out}")
    out.mkdir(parents=True)

    paths = {
        "theme": src / "theme-analysis.json",
        "regions": src / "regions-map.json",
        "provinces": src / "adm1.json",
        "municipalities": src / "adm2.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"Required DDPT file is missing: {path}")
    ddpt = read_json(paths["theme"])
    indicators_by_id = {row["indicator_id"]: row for row in ddpt["indicators"]}
    source_by_id = {row["source_id"]: row for row in ddpt["sources"]}
    territory_by_old = {row["territory_id"]: row for row in ddpt["territories"]}

    def new_tid(row: dict) -> str:
        level = row["geographic_level"]
        code = compact_code(row.get("adm2_code") or row.get("province_code") or row.get("code"))
        if level == "region":
            return f"DOM:C2022:REG:{code}"
        if level == "provincia":
            return f"DOM:C2022:PROV:{code.zfill(2)}"
        return f"DOM:C2022:MUN:{code.zfill(5)}"

    id_map = {old: new_tid(row) for old, row in territory_by_old.items()}
    territories = []
    for old, row in territory_by_old.items():
        level = row["geographic_level"]
        if level == "region":
            parent = "DOM"
            typ = "planning_region"
            official_code = compact_code(row.get("code"))
        elif level == "provincia":
            parent = id_map[row["region_territory_id"]]
            typ = "province"
            official_code = compact_code(row.get("province_code") or row.get("code")).zfill(2)
        else:
            parent = id_map[row["province_territory_id"]]
            typ = "municipality"
            official_code = compact_code(row.get("adm2_code") or row.get("code")).zfill(5)
        territories.append({
            "id": id_map[old], "country_id": "DOM", "name": row["name"],
            "level": typ, "type": typ, "parent_id": parent,
            "official_code": official_code,
            "code_system": "ONE X Census 2022 / Dominican territorial master",
            "boundary_version": "IGN/IDERD reference geometry used by DDPT, retrieved before 2026-08-06",
            "source_id": "dom-one-census-2022",
            "geography_note": "The 2022 Census analysis hierarchy retains the DDPT-verified ONE identity. Reference geometry is for display and is not presented as a legal-boundary certification.",
        })
    territories.sort(key=lambda r: (r["level"], r["official_code"]))

    selected_ids = set(ADOPTED.values())
    indicators = []
    definitions = {}
    for old_id in ADOPTED.values():
        row = indicators_by_id[old_id]
        iid = IDS[old_id]
        unit = {"personas": "people", "porcentaje": "%", "establecimientos": "facilities"}.get(row["unit"], row["unit"])
        method = "derived_from_source_counts" if row["aggregation_method"] == "ratio_of_sums" else "source_reported_or_complete_sum"
        indicators.append({
            "id": iid, "name": row["label"],
            "theme": {"one-censo-2022": "Census", "sns-establecimientos": "Health"}.get(row["source_id"], row["theme_id"]),
            "unit": unit, "definition": row["description"], "definition_id": iid,
            "population": row["description"], "measurement_method": method,
            "aggregation": "sum" if row["aggregation_method"] == "sum" else "none",
            "period_policy": "fixed_source_period", "series_family": "census" if row["source_id"] == "one-censo-2022" else "administrative",
            "display_role": "primary", "source_id": "dom-one-census-2022" if row["source_id"] == "one-censo-2022" else "dom-sns-health-facilities-2026",
        })
        definitions[iid] = indicators[-1]

    indicators.extend([
        {"id": IDS["ethnicity"], "name": "Population meeting the ENHOGAR theoretical definition of Afro-descendance", "theme": "Inclusion", "unit": "%", "definition": "National ENHOGAR 2021 estimate using the report's theoretical definition of Afro-descendance; socio-racial self-identification categories are separately described in the source.", "definition_id": IDS["ethnicity"], "population": "Resident population represented by ENHOGAR 2021", "measurement_method": "source_reported", "aggregation": "none", "period_policy": "fixed_source_period", "series_family": "survey", "display_role": "context", "source_id": "dom-one-enhogar-2021"},
        {"id": IDS["nutrition"], "name": "Prevalence of undernourishment", "theme": "Nutrition", "unit": "%", "definition": "FAO-modeled national prevalence of undernourishment distributed through the World Bank API.", "definition_id": IDS["nutrition"], "population": "National population", "measurement_method": "source_reported_modeled_estimate", "aggregation": "none", "period_policy": "latest_available", "series_family": "international_reference", "display_role": "context", "source_id": "dom-world-bank-nutrition"},
        {"id": IDS["poverty"], "name": "General monetary poverty", "theme": "Poverty", "unit": "%", "definition": "Official annual monetary-poverty rate for persons, calculated from ENCFT microdata under the national official method.", "definition_id": IDS["poverty"], "population": "National resident population represented by ENCFT", "measurement_method": "source_reported", "aggregation": "none", "period_policy": "fixed_source_period", "series_family": "survey", "display_role": "context", "source_id": "dom-one-poverty-2024"},
    ])
    definitions.update({row["id"]: row for row in indicators[-3:]})

    observations = []
    by_indicator_regions = defaultdict(list)
    for row in ddpt["observations"]:
        if row["indicator_id"] not in selected_ids:
            continue
        definition = definitions[IDS[row["indicator_id"]]]
        obs = {
            "territory_id": id_map[row["territory_id"]], "indicator_id": definition["id"],
            "period": str(row["period"]), "value": row["value"], "status": "observed",
            "source_id": definition["source_id"], "definition": definition["definition"],
            "definition_id": definition["definition_id"], "unit": definition["unit"],
            "population": definition["population"], "measurement_method": definition["measurement_method"],
            "source_locator": f"DDPT normalized source observation {row['indicator_id']} / {row['territory_id']}",
        }
        if row.get("numerator") is not None:
            obs["numerator"] = row["numerator"]
        if row.get("denominator") is not None:
            obs["denominator"] = row["denominator"]
        observations.append(obs)
        if row["geographic_level"] == "region":
            by_indicator_regions[row["indicator_id"]].append(row)

    # National values are calculated only from the complete, non-overlapping set
    # of all ten adopted planning-region observations.
    national_audit = {}
    for old_id in ADOPTED.values():
        rows = by_indicator_regions[old_id]
        if len(rows) != 10:
            raise SystemExit(f"{old_id}: expected 10 complete region observations, found {len(rows)}")
        definition = definitions[IDS[old_id]]
        if indicators_by_id[old_id]["aggregation_method"] == "sum":
            value = sum(float(row["value"]) for row in rows)
            numerator = sum(float(row.get("numerator") if row.get("numerator") is not None else row["value"]) for row in rows)
            denominator = None
        else:
            if not all(row.get("numerator") is not None and row.get("denominator") not in (None, 0) for row in rows):
                raise SystemExit(f"{old_id}: complete regional ratio numerators/denominators are required")
            numerator = sum(float(row["numerator"]) for row in rows)
            denominator = sum(float(row["denominator"]) for row in rows)
            value = numerator / denominator * 100
        obs = {"territory_id": "DOM", "indicator_id": definition["id"], "period": str(rows[0]["period"]), "value": round(value, 6), "status": "observed", "source_id": definition["source_id"], "definition": definition["definition"], "definition_id": definition["definition_id"], "unit": definition["unit"], "population": definition["population"], "measurement_method": "complete_non_overlapping_region_aggregation", "source_locator": "All 10 DDPT-verified planning regions; component IDs retained in the collection audit", "numerator": round(numerator, 6)}
        if denominator is not None:
            obs["denominator"] = round(denominator, 6)
        observations.append(obs)
        national_audit[old_id] = {"component_count": 10, "component_ids": [id_map[row["territory_id"]] for row in rows], "value": obs["value"], "numerator": obs.get("numerator"), "denominator": obs.get("denominator")}

    wb = fetch_json(NUTRITION_URL)
    wb_rows = wb[1] if isinstance(wb, list) and len(wb) > 1 else []
    latest = next((row for row in wb_rows if row.get("value") is not None), None)
    if not latest:
        raise SystemExit("World Bank/FAO nutrition series returned no value")
    contexts = [
        (definitions[IDS["ethnicity"]], "2021", 81.9, "observed", ETHNICITY_URL, "ENHOGAR-2021 Informe General, afro-descendance discussion"),
        (definitions[IDS["nutrition"]], str(latest["date"]), float(latest["value"]), "observed", NUTRITION_URL, "World Bank API / FAO indicator SN.ITK.DEFC.ZS"),
        (definitions[IDS["poverty"]], "2024", 19.0, "observed", POVERTY_URL, "ONE Boletín de Pobreza Monetaria 2024, national general poverty rate"),
    ]
    for definition, period, value, status, _, locator in contexts:
        observations.append({"territory_id": "DOM", "indicator_id": definition["id"], "period": period, "value": value, "status": status, "source_id": definition["source_id"], "definition": definition["definition"], "definition_id": definition["definition_id"], "unit": definition["unit"], "population": definition["population"], "measurement_method": definition["measurement_method"], "source_locator": locator})

    def feature_set(filename: str, expected_level: str):
        geo = read_json(paths[filename])
        out_features = []
        for feature in geo["features"]:
            props = feature.get("properties", {})
            old = props.get("territory_id")
            if not old and expected_level == "municipio":
                old = f"do-mun-{str(props.get('adm2_code', '')).zfill(5)}"
            if old not in id_map:
                raise SystemExit(f"Boundary {filename} cannot be joined: {props}")
            tid = id_map[old]
            out_features.append({"type": "Feature", "properties": {"territory_id": tid, "name": territory_by_old[old]["name"], "source_id": "dom-iderd-boundaries", "boundary_version": "IGN/IDERD reference geometry used by DDPT, retrieved before 2026-08-06"}, "geometry": feature["geometry"]})
        return out_features

    boundary_features = feature_set("regions", "region") + feature_set("provinces", "provincia") + feature_set("municipalities", "municipio")
    if len(boundary_features) != 200:
        raise SystemExit(f"Expected 200 boundary features, found {len(boundary_features)}")

    children = defaultdict(list)
    for row in territories:
        children[row["parent_id"]].append(row["id"])
    comparisons = []
    for parent, members in sorted(children.items()):
        if parent == "DOM":
            level, label = "planning_region", "Planning regions within the Dominican Republic"
        elif parent.startswith("DOM:C2022:REG:"):
            level, label = "province", "Provinces within the selected planning region"
        else:
            level, label = "municipality", "Municipalities within the selected province"
        comparisons.append({"parent_id": parent, "member_ids": sorted(members), "level": level, "label": label, "membership_note": "Complete membership in the DDPT-verified ONE 2022 territorial master.", "source_ids": ["dom-one-census-2022", "dom-iderd-boundaries"]})

    sources = [
        {"id": "dom-one-census-2022", "name": "X Censo Nacional de Población y Vivienda 2022", "publisher": "Oficina Nacional de Estadística (ONE)", "url": CENSUS_URL, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2022", "geographic_level": "country, 10 planning regions, 32 provinces and 158 municipalities", "license": "Official public statistical publication; reuse terms not stated", "note": "AreaData imports the audited DDPT normalization. Every derived ratio retains the published numerator and denominator; missing values are not converted to zero."},
        {"id": "dom-iderd-boundaries", "name": "Dominican Republic ADM1/ADM2 reference geometry", "publisher": "Instituto Geográfico Nacional / IDERD", "url": BOUNDARY_URL, "status": "ready", "retrieved_at": "2026-08-06", "reference_period": "DDPT reference edition", "geographic_level": "10 planning regions, 32 provinces and 158 municipalities", "license": "Official public geoservice; reuse terms not stated", "note": "Display geometry from the DDPT verified source register; it is not represented as a legal-boundary certification."},
        {"id": "dom-sns-health-facilities-2026", "name": "SNS health-facility registry", "publisher": "Servicio Nacional de Salud", "url": HEALTH_URL, "status": "ready", "retrieved_at": "2026-08-06", "reference_period": "2026", "geographic_level": "municipality, province, planning region and complete country aggregation", "license": "Official open-data catalog", "note": "Facility counts are administrative records and do not measure service quality or health outcomes."},
        {"id": "dom-one-enhogar-2021", "name": "ENHOGAR 2021 Informe General", "publisher": "Oficina Nacional de Estadística (ONE)", "url": ETHNICITY_URL, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2021", "geographic_level": "country", "license": "Official public statistical publication; reuse terms not stated", "note": "National survey context only; no provincial or municipal value is inferred."},
        {"id": "dom-world-bank-nutrition", "name": "World Bank/FAO indicator SN.ITK.DEFC.ZS — Dominican Republic", "publisher": "World Bank and FAO", "url": NUTRITION_URL, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": str(latest["date"]), "geographic_level": "country", "license": "World Bank CC BY 4.0 data terms", "note": "National modeled context only; no lower-area value is inferred."},
        {"id": "dom-one-poverty-2024", "name": "Boletín de Pobreza Monetaria 2024", "publisher": "Oficina Nacional de Estadística (ONE)", "url": POVERTY_URL, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2024", "geographic_level": "country (the source also reports four broad macro-regions that do not equal the 10-region hierarchy)", "license": "Official public statistical publication; reuse terms not stated", "note": "The national published rate is retained. Four source macro-regions are not silently joined to the 10 planning regions."},
    ]

    terminal_ids = [row["id"] for row in territories if row["type"] == "municipality"]
    bundle = {"schema_version": "1.0", "country_area_id": "DOM", "period": "2022", "replace_country_branch": True, "territories": territories, "indicators": indicators, "sources": sources, "observations": observations, "boundaries": {"type": "FeatureCollection", "features": boundary_features}, "comparisons": comparisons, "terminal_territory_ids": terminal_ids}

    for key, path in paths.items():
        shutil.copy2(path, out / path.name)
    (out / "world-bank-nutrition.json").write_text(json.dumps(wb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    bundle_path = out / "dominican-republic-country-depth-bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    theme_counts = Counter()
    for theme, old_id in ADOPTED.items():
        theme_counts[theme] = sum(1 for row in observations if row["indicator_id"] == IDS[old_id])
    theme_counts.update({"ethnicity": 1, "nutrition": 1, "poverty": 1})
    audit = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "DOM", "status": "complete", "source_derivative": "DDPT thematic dataset built from official ONE/SNS inputs", "counts": {"territories": len(territories), "planning_regions": sum(row["type"] == "planning_region" for row in territories), "provinces": sum(row["type"] == "province" for row in territories), "municipalities": len(terminal_ids), "indicators": len(indicators), "observations": len(observations), "boundaries": len(boundary_features)}, "theme_observation_counts": dict(theme_counts), "national_aggregation": national_audit, "context_only": {"ethnicity": {"period": "2021", "value": 81.9, "lower_area_inference": False}, "nutrition": {"period": str(latest["date"]), "value": float(latest["value"]), "lower_area_inference": False}, "poverty": {"period": "2024", "value": 19.0, "lower_area_inference": False}}, "source_files": {key: {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)} for key, path in paths.items()}, "bundle": {"file": bundle_path.name, "bytes": bundle_path.stat().st_size, "sha256": sha256(bundle_path)}, "limits": ["The ethnicity, nutrition and poverty indicators are national context only.", "The poverty publication's four broad macro-regions are not mapped to the 10 planning-region hierarchy.", "Reference geometry is not a legal-boundary certification.", "Health-facility records measure registered facilities, not access or outcomes."]}
    (out / "DOMINICAN_REPUBLIC_COLLECTION_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "counts": audit["counts"], "theme_observation_counts": audit["theme_observation_counts"], "bundle_sha256": audit["bundle"]["sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

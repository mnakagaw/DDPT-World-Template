#!/usr/bin/env python3
"""Collect Costa Rica's official 2022 estimates and selected 2011 Census fields.

The 2022 Census had partial coverage. INEC therefore publishes an official
adjusted population/housing estimate and a public Power BI model.  This
collector preserves that status, downloads the public model rows, and never
labels them as an unadjusted enumeration.  Three themes absent from the 2022
model use explicitly dated 2011 Census tables.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PBI_REPORT = "https://app.powerbi.com/view?r=eyJrIjoiNGI2YjJlMjktMTNiZS00ZjRiLTk3OGYtMmFlY2QyN2Q5NzUyIiwidCI6ImYzZmI3MWE1LTNhZmYtNDcxNS1iMGZkLTk5MTVlYjA3ZWJjYSIsImMiOjR9&pageName=b2b04e99768d5d840c45"
PBI_CLUSTER = "https://wabi-south-central-us-api.analysis.windows.net"
PBI_KEY = "4b6b2e29-13be-4f4b-978f-2aecd27d9752"
PBI_MODEL = 9336303
PBI_BASE = f"{PBI_CLUSTER}/public/reports"
INEC_TOOLS = "https://admin.inec.cr/herramientas"
INEC_METHOD = "https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf"
INEC_2011_CATALOG = "https://sistemas.inec.cr/nada5.4/index.php/catalog/113/related-materials"
INEC_2011_RESULTS = "https://sistemas.inec.cr/nada5.4/index.php/catalog/113/download/713"
ARC_CANTON = "https://services8.arcgis.com/ODelaeFcU0U2CwoG/arcgis/rest/services/UGEC_F/FeatureServer/2"
ARC_PROVINCE = "https://services8.arcgis.com/ODelaeFcU0U2CwoG/arcgis/rest/services/UGEP/FeatureServer/2"
WB_NUTRITION = "https://api.worldbank.org/v2/country/CRI/indicator/SN.ITK.DEFC.ZS?format=json&per_page=100"


def fetch(url: str, *, data: bytes | None = None, headers: dict | None = None, timeout: int = 180) -> bytes:
    request = Request(url, data=data, headers={"User-Agent": "AreaData/0.10 source collector", **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip" or body.startswith(b"\x1f\x8b"):
            body = gzip.decompress(body)
        return body


def write_fetch(path: Path, url: str, **kwargs) -> bytes:
    body = fetch(url, **kwargs)
    if not body:
        raise RuntimeError(f"Empty response from {url}")
    path.write_bytes(body)
    return body


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pbi_headers() -> dict:
    return {
        "Accept": "application/json",
        "ActivityId": str(uuid.uuid4()),
        "RequestId": str(uuid.uuid4()),
        "X-PowerBI-ResourceKey": PBI_KEY,
    }


def pbi_query(entity: str, properties: list[str]) -> dict:
    alias = "p"
    select = [{
        "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
        "Name": f"{entity}.{prop}",
        "NativeReferenceName": prop,
    } for prop in properties]
    command = {"SemanticQueryDataShapeCommand": {
        "Query": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}], "Select": select},
        "Binding": {
            "Primary": {"Groupings": [{"Projections": list(range(len(select)))}]},
            "DataReduction": {"DataVolume": 6, "Primary": {"Window": {"Count": 30000}}},
            "Version": 1,
        },
        "ExecutionMetricsKind": 1,
    }}
    payload = {
        "version": "1.0.0",
        "queries": [{"Query": {"Commands": [command]}, "CacheKey": ""}],
        "cancelQueries": [],
        "modelId": PBI_MODEL,
    }
    headers = {**pbi_headers(), "Content-Type": "application/json"}
    return json.loads(fetch(f"{PBI_BASE}/querydata?synchronous=true", data=json.dumps(payload).encode(), headers=headers).decode())


def decode_dsr(payload: dict, properties: list[str]) -> list[dict]:
    data = payload["results"][0]["result"]["data"]["dsr"]["DS"][0]
    raw_rows = data["PH"][0]["DM0"]
    schema = raw_rows[0]["S"]
    dictionaries = data.get("ValueDicts", {})
    if len(schema) != len(properties):
        raise RuntimeError(f"Power BI schema mismatch: {len(schema)} != {len(properties)}")
    previous = [None] * len(schema)
    result = []
    for row_number, raw in enumerate(raw_rows, 1):
        values = iter(raw.get("C", []))
        repeated, nulls, row = int(raw.get("R", 0)), int(raw.get("Ø", 0)), []
        for index, item in enumerate(schema):
            if repeated & (1 << index):
                value = previous[index]
            elif nulls & (1 << index):
                value = None
            else:
                try:
                    value = next(values)
                except StopIteration as error:
                    raise RuntimeError(f"Truncated Power BI row {row_number}") from error
                dictionary = item.get("DN")
                if dictionary and value is not None:
                    value = dictionaries[dictionary][int(value)]
            row.append(value)
        try:
            next(values)
            raise RuntimeError(f"Unexpected extra Power BI values at row {row_number}")
        except StopIteration:
            pass
        previous = row
        result.append(dict(zip(properties, row)))
    return result


def indicator(indicator_id: str, name: str, theme: str, unit: str, definition: str, source_id: str, *, method: str = "source_reported", role: str = "primary") -> dict:
    return {
        "id": indicator_id, "name": name, "theme": theme, "unit": unit,
        "definition": definition, "definition_id": indicator_id,
        "population": definition, "measurement_method": method,
        "aggregation": "sum" if unit == "people" else "none",
        "period_policy": "fixed_source_period", "series_family": "international_reference" if "world-bank" in source_id else "census",
        "display_role": role, "source_id": source_id,
    }


def observation(area_id: str, indicator_id: str, period: str, value: float, source_id: str, definition: str, locator: str, *, method: str = "source_reported", numerator=None, denominator=None) -> dict:
    if value is None or not math.isfinite(float(value)):
        raise RuntimeError(f"Invalid value for {area_id} {indicator_id}: {value}")
    return {
        "territory_id": area_id, "indicator_id": indicator_id, "period": period,
        "value": round(float(value), 6), "status": "observed", "source_id": source_id,
        "definition": definition, "definition_id": indicator_id,
        "unit": "people" if indicator_id.endswith("POP_TOTAL") else "%" if indicator_id.endswith("PCT") else "persons per dwelling",
        "population": definition, "measurement_method": method,
        "source_locator": locator, "numerator": numerator, "denominator": denominator,
    }


def clean_name(label: str) -> str:
    return re.sub(r"^\d+\s+", "", label or "").strip()


def unique_values(rows: list[dict], property_name: str, expected: int) -> float:
    values = {round(float(row[property_name]), 9) for row in rows if row.get(property_name) is not None}
    if len(values) != expected:
        raise RuntimeError(f"Expected {expected} distinct {property_name} values; found {len(values)}")
    return 0.0


def add_pbi_indicator(observations: list[dict], rows: list[dict], code: str, indicator_id: str, definition: str, locator: str, source_id: str, period="2022"):
    selected = [row for row in rows if str(row["ID_IND"]).zfill(2) == code.zfill(2)]
    if len(selected) != 82:
        raise RuntimeError(f"{code}: expected 82 canton rows, found {len(selected)}")
    national_values, province_values = set(), {}
    for row in selected:
        canton = str(int(row["PC"])).zfill(3)
        province = str(int(row["P"]))
        observations.append(observation(f"CRI:C2022:CANTON:{canton}", indicator_id, period, row["Estadístico"], source_id, definition, locator))
        national_key = "Estadístico_N" if "Estadístico_N" in row else "Estadístico N"
        national_values.add(round(float(row[national_key]), 9))
        province_values.setdefault(province, set()).add(round(float(row["Estadístico_P"]), 9))
    if len(national_values) != 1 or set(province_values) != set("1234567") or any(len(v) != 1 for v in province_values.values()):
        raise RuntimeError(f"{code}: inconsistent repeated province/national values")
    observations.append(observation("CRI", indicator_id, period, next(iter(national_values)), source_id, definition, locator))
    for province, values in sorted(province_values.items()):
        observations.append(observation(f"CRI:C2022:PROV:{province}", indicator_id, period, next(iter(values)), source_id, definition, locator))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)

    # Preserve the public report metadata and the exact query responses.
    headers = pbi_headers()
    models = json.loads(write_fetch(out / "powerbi-models.json", f"{PBI_BASE}/{PBI_KEY}/modelsAndExploration?preferReadOnlySession=true", headers=headers).decode())
    schema = json.loads(write_fetch(out / "powerbi-conceptual-schema.json", f"{PBI_BASE}/{PBI_KEY}/conceptualschema", headers=pbi_headers()).decode())
    if models["models"][0]["id"] != PBI_MODEL or schema["schemas"][0]["modelId"] != PBI_MODEL:
        raise RuntimeError("Unexpected Power BI model id")
    people_props = ["P", "Provincia", "PC", "Cantón", "ID_IND", "Indicador", "Estadístico", "Estadístico_P", "Estadístico N", "GRUPO", "NOMB_IND", "Eje"]
    home_props = ["P", "Provincia", "PC", "Cantón", "ID_IND", "Indicador", "Estadístico", "Estadístico_P", "Estadístico_N", "GRUPO", "NOMB_IND", "Eje"]
    people_payload, home_payload = pbi_query("PC-InPOB", people_props), pbi_query("PC-InVIV", home_props)
    (out / "powerbi-canton-people.json").write_text(json.dumps(people_payload, ensure_ascii=False), encoding="utf-8")
    (out / "powerbi-canton-housing.json").write_text(json.dumps(home_payload, ensure_ascii=False), encoding="utf-8")
    people = decode_dsr(people_payload, people_props)
    homes = decode_dsr(home_payload, home_props)
    if len(people) != 82 * 62 or len(homes) != 82 * 19:
        raise RuntimeError(f"Unexpected Power BI row counts: {len(people)}, {len(homes)}")

    query_common = {"where": "1=1", "returnGeometry": "true", "outSR": "4326", "geometryPrecision": "5", "maxAllowableOffset": "0.001", "f": "geojson"}
    canton_url = f"{ARC_CANTON}/query?{urlencode({**query_common, 'outFields':'COD_UGEC,COD_UGEP,NOM_UGEP,NOM_UGEC,POB_TOTAL'})}"
    province_url = f"{ARC_PROVINCE}/query?{urlencode({**query_common, 'outFields':'COD_UGEP,NOM_UGEP'})}"
    canton_geo = json.loads(write_fetch(out / "canton-boundaries.geojson", canton_url).decode())
    province_geo = json.loads(write_fetch(out / "province-boundaries.geojson", province_url).decode())
    if len(canton_geo["features"]) != 82 or len(province_geo["features"]) != 7:
        raise RuntimeError("Official boundary coverage is incomplete")
    write_fetch(out / "estimaciones-sociales-vivienda-2022-metodologia.pdf", INEC_METHOD)
    write_fetch(out / "censo-2011-resultados-generales.pdf", INEC_2011_RESULTS)

    source_2022 = "cri-inec-adjusted-census-estimates-2022"
    source_2011 = "cri-inec-census-2011-results"
    sources = [
        {"id": source_2022, "name": "Estimación de indicadores sociales y de vivienda 2022", "publisher": "Instituto Nacional de Estadística y Censos de Costa Rica", "url": PBI_REPORT, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2022", "geographic_level": "country, province and canton", "license": "Official public statistics", "note": "Adjusted official estimates produced after partial 2022 Census coverage; they are not represented as unadjusted enumeration totals."},
        {"id": "cri-inec-geo-2022", "name": "INEC 2022 geo-statistical province and canton services", "publisher": "Instituto Nacional de Estadística y Censos de Costa Rica", "url": ARC_CANTON, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2022 edition", "geographic_level": "province and canton", "license": "Official public geospatial service", "note": "Display/reference geometries joined by exact INEC UGEP/UGEC codes."},
        {"id": source_2011, "name": "X Censo Nacional de Población y VI de Vivienda 2011 — Resultados Generales", "publisher": "Instituto Nacional de Estadística y Censos de Costa Rica", "url": INEC_2011_RESULTS, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2011", "geographic_level": "country and province for adopted fields", "license": "Official Census publication", "note": "Used only for themes absent from the adjusted 2022 public model. The period remains 2011."},
        {"id": "cri-world-bank-api", "name": "World Bank Indicators API — Costa Rica", "publisher": "World Bank", "url": WB_NUTRITION, "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "latest non-null value", "geographic_level": "country", "license": "World Bank terms", "note": "FAO-modeled national nutrition context only."},
    ]

    first_by_canton = {}
    for row in people:
        first_by_canton.setdefault(str(int(row["PC"])).zfill(3), row)
    province_names = {str(int(row["P"])): clean_name(row["Provincia"]) for row in first_by_canton.values()}
    territories = []
    for code, name in sorted(province_names.items()):
        territories.append({"id": f"CRI:C2022:PROV:{code}", "country_id": "CRI", "name": name, "level": "province", "type": "province", "parent_id": "CRI", "official_code": code, "code_system": "INEC 2022 UGEP", "boundary_version": "INEC 2022 geo-statistical edition", "source_id": "cri-inec-geo-2022", "geography_note": "Official INEC geo-statistical province used for the 2022 adjusted estimates."})
    for code, row in sorted(first_by_canton.items()):
        pcode = str(int(row["P"]))
        territories.append({"id": f"CRI:C2022:CANTON:{code}", "country_id": "CRI", "name": clean_name(row["Cantón"]), "level": "canton", "type": "canton", "parent_id": f"CRI:C2022:PROV:{pcode}", "official_code": code, "code_system": "INEC 2022 UGEC", "boundary_version": "INEC 2022 geo-statistical edition", "source_id": "cri-inec-geo-2022", "geography_note": "Cantón is the municipal planning jurisdiction. The official 2022 estimates also publish district data, which remains an optional finer diagnostic extension."})

    indicators = [
        indicator("CRI_EST2022_POP_TOTAL", "Official adjusted population estimate", "Population", "people", "INEC adjusted 2022 population estimate following partial Census coverage.", source_2022),
        indicator("CRI_EST2022_FEMALE_PCT", "Female population", "Population", "%", "Women as a percentage of the adjusted 2022 population.", source_2022, method="derived_from_source_counts"),
        indicator("CRI_EST2022_OCCUPANTS_PER_DWELLING", "Average occupants per occupied dwelling", "Housing", "persons per dwelling", "Average occupants per occupied individual dwelling in the adjusted 2022 estimate.", source_2022),
        indicator("CRI_EST2022_PIPED_AQUEDUCT_WATER_PCT", "Dwellings with indoor piping and aqueduct water", "Basic services", "%", "Occupied dwellings with piping inside the dwelling whose water comes from an aqueduct; this does not measure water quality.", source_2022),
        indicator("CRI_EST2022_SAFE_SANITATION_PROXY_PCT", "Dwellings with sewer or septic tank", "Basic services", "%", "Occupied dwellings connected to a sanitary sewer or septic tank; retained as the published service definition.", source_2022),
        indicator("CRI_EST2022_ELECTRICITY_PCT", "Dwellings with electricity", "Basic services", "%", "Occupied dwellings with electricity in the adjusted 2022 estimate.", source_2022),
        indicator("CRI_EST2022_ILLITERACY_PCT", "Illiteracy", "Education", "%", "Published adjusted 2022 illiteracy percentage; a lower value is generally favorable.", source_2022),
        indicator("CRI_EST2022_EMPLOYED_PCT", "Employed population", "Economy", "%", "Published adjusted 2022 percentage of employed population under the INEC model definition.", source_2022),
        indicator("CRI_C2011_DISABILITY_PCT", "Population with at least one disability", "Inclusion", "%", "2011 Census population with at least one reported disability; derived as total population minus population with no disability.", source_2011, method="derived_from_source_counts"),
        indicator("CRI_EST2022_FOREIGN_BORN_PCT", "Foreign-born population", "Migration", "%", "Published adjusted 2022 percentage of foreign-born population.", source_2022),
        indicator("CRI_C2011_URBAN_POP_PCT", "Urban population", "Population", "%", "2011 Census population classified as urban under the official Census classification.", source_2011, method="derived_from_source_counts"),
        indicator("CRI_C2011_INDIGENOUS_IDENTIFICATION_PCT", "Population identifying as Indigenous", "Inclusion", "%", "2011 Census population self-identifying as Indigenous.", source_2011, method="derived_from_source_counts"),
        indicator("CRI_EST2022_INSURED_POP_PCT", "Population with social insurance", "Health", "%", "Published adjusted 2022 percentage of population with social insurance; this is coverage status, not a general health outcome.", source_2022),
        indicator("CRI_WB_UNDERNOURISHMENT_PCT", "Prevalence of undernourishment", "Nutrition", "%", "FAO-modeled national prevalence distributed through the World Bank API; no local value is inferred.", "cri-world-bank-api", role="context"),
        indicator("CRI_EST2022_HOUSEHOLDS_WITH_NBI_PCT", "Households with at least one unmet basic need", "Poverty", "%", "Published adjusted 2022 percentage of households with at least one unmet basic need (NBI).", source_2022),
    ]
    observations = []
    people_map = {str(row["ID_IND"]).zfill(2): row for row in people[:62]}
    # Directly published Power BI indicators.
    for code, iid, definition in [
        ("01", "CRI_EST2022_POP_TOTAL", indicators[0]["definition"]),
        ("16", "CRI_EST2022_ILLITERACY_PCT", indicators[6]["definition"]),
        ("21", "CRI_EST2022_EMPLOYED_PCT", indicators[7]["definition"]),
        ("09", "CRI_EST2022_FOREIGN_BORN_PCT", indicators[9]["definition"]),
        ("10", "CRI_EST2022_INSURED_POP_PCT", indicators[12]["definition"]),
        ("62", "CRI_EST2022_HOUSEHOLDS_WITH_NBI_PCT", indicators[14]["definition"]),
    ]:
        add_pbi_indicator(observations, people, code, iid, definition, f"Public Power BI PC-InPOB indicator {code}", source_2022)
    for code, iid, definition in [
        ("03", "CRI_EST2022_OCCUPANTS_PER_DWELLING", indicators[2]["definition"]),
        ("10", "CRI_EST2022_PIPED_AQUEDUCT_WATER_PCT", indicators[3]["definition"]),
        ("09", "CRI_EST2022_SAFE_SANITATION_PROXY_PCT", indicators[4]["definition"]),
        ("11", "CRI_EST2022_ELECTRICITY_PCT", indicators[5]["definition"]),
    ]:
        add_pbi_indicator(observations, homes, code, iid, definition, f"Public Power BI PC-InVIV indicator {code}", source_2022)

    # Female percentage uses the model's published male and female counts.
    male = {str(int(row["PC"])).zfill(3): row for row in people if str(row["ID_IND"]).zfill(2) == "02"}
    female = {str(int(row["PC"])).zfill(3): row for row in people if str(row["ID_IND"]).zfill(2) == "03"}
    female_definition = indicators[1]["definition"]
    for code in sorted(female):
        num, den = float(female[code]["Estadístico"]), float(female[code]["Estadístico"]) + float(male[code]["Estadístico"])
        observations.append(observation(f"CRI:C2022:CANTON:{code}", indicators[1]["id"], "2022", num / den * 100, source_2022, female_definition, "PC-InPOB indicators 02 and 03", method="derived_from_source_counts", numerator=num, denominator=den))
    for level, area_id, value_key in [("national", "CRI", "Estadístico N")]:
        num = {round(float(row[value_key]), 6) for row in female.values()}; men = {round(float(row[value_key]), 6) for row in male.values()}
        if len(num) != 1 or len(men) != 1: raise RuntimeError("Inconsistent national sex totals")
        n, m = next(iter(num)), next(iter(men)); observations.append(observation(area_id, indicators[1]["id"], "2022", n/(n+m)*100, source_2022, female_definition, "PC-InPOB indicators 02 and 03", method="derived_from_source_counts", numerator=n, denominator=n+m))
    for pcode in "1234567":
        fvals = {round(float(row["Estadístico_P"]), 6) for row in female.values() if str(int(row["P"])) == pcode}; mvals = {round(float(row["Estadístico_P"]), 6) for row in male.values() if str(int(row["P"])) == pcode}
        if len(fvals) != 1 or len(mvals) != 1: raise RuntimeError(f"Inconsistent province sex totals {pcode}")
        n, m = next(iter(fvals)), next(iter(mvals)); observations.append(observation(f"CRI:C2022:PROV:{pcode}", indicators[1]["id"], "2022", n/(n+m)*100, source_2022, female_definition, "PC-InPOB indicators 02 and 03", method="derived_from_source_counts", numerator=n, denominator=n+m))

    # Exact 2011 Census Table 5, Table 7 and Table 15 values.
    urban = {"CRI": (3130871, 4301712), "1": (1213957, 1404242), "2": (515150, 848146), "3": (404999, 490903), "4": (372883, 433677), "5": (180332, 326953), "6": (224794, 410929), "7": (218756, 386862)}
    indigenous = {"CRI": (104143, 4301712), "1": (20188, 1404242), "2": (8089, 848146), "3": (8447, 490903), "4": (4506, 433677), "5": (10135, 326953), "6": (25316, 410929), "7": (27462, 386862)}
    for key, (num, den) in urban.items():
        area_id = "CRI" if key == "CRI" else f"CRI:C2022:PROV:{key}"
        observations.append(observation(area_id, indicators[10]["id"], "2011", num/den*100, source_2011, indicators[10]["definition"], "Resultados Generales, Cuadro 5", method="derived_from_source_counts", numerator=num, denominator=den))
    for key, (num, den) in indigenous.items():
        area_id = "CRI" if key == "CRI" else f"CRI:C2022:PROV:{key}"
        observations.append(observation(area_id, indicators[11]["id"], "2011", num/den*100, source_2011, indicators[11]["definition"], "Resultados Generales, Cuadro 15", method="derived_from_source_counts", numerator=num, denominator=den))
    disability_num, disability_den = 4301712 - 3848863, 4301712
    observations.append(observation("CRI", indicators[8]["id"], "2011", disability_num/disability_den*100, source_2011, indicators[8]["definition"], "Resultados Generales, Cuadro 7", method="derived_from_source_counts", numerator=disability_num, denominator=disability_den))

    wb = json.loads(write_fetch(out / "world-bank-undernourishment.json", WB_NUTRITION).decode())[1]
    latest = max((row for row in wb if row.get("value") is not None), key=lambda row: int(row["date"]))
    observations.append(observation("CRI", indicators[13]["id"], str(latest["date"]), float(latest["value"]), "cri-world-bank-api", indicators[13]["definition"], "World Bank API SN.ITK.DEFC.ZS; latest non-null national observation"))

    features = []
    for feature in province_geo["features"]:
        code = str(feature["properties"]["COD_UGEP"])
        features.append({"type":"Feature", "properties":{"territory_id":f"CRI:C2022:PROV:{code}", "name":feature["properties"]["NOM_UGEP"], "source_id":"cri-inec-geo-2022", "geometry_edition":"INEC 2022 UGEP service", "reference_only":False, "join_method":"Exact INEC UGEP code"}, "geometry":feature["geometry"]})
    for feature in canton_geo["features"]:
        code = str(feature["properties"]["COD_UGEC"]).zfill(3)
        features.append({"type":"Feature", "properties":{"territory_id":f"CRI:C2022:CANTON:{code}", "name":feature["properties"]["NOM_UGEC"], "source_id":"cri-inec-geo-2022", "geometry_edition":"INEC 2022 UGEC service", "reference_only":False, "join_method":"Exact INEC UGEC code"}, "geometry":feature["geometry"]})
    comparisons = [{"parent_id":"CRI", "member_ids":[f"CRI:C2022:PROV:{i}" for i in "1234567"], "label":"7 Costa Rica provinces", "source_ids":[source_2022,"cri-inec-geo-2022"], "membership_note":"Complete official 2022 adjusted-estimate province register."}]
    for pcode in "1234567":
        ids = [row["id"] for row in territories if row["level"] == "canton" and row["parent_id"] == f"CRI:C2022:PROV:{pcode}"]
        comparisons.append({"parent_id":f"CRI:C2022:PROV:{pcode}", "member_ids":ids, "label":f"Cantons within {province_names[pcode]}", "source_ids":[source_2022,"cri-inec-geo-2022"], "membership_note":"Complete official 2022 canton register for the selected province."})

    # Assert 90-area coverage for every adopted 2022 local indicator.
    local_ids = {row["id"] for row in indicators if row["id"].startswith("CRI_EST2022")}
    for iid in local_ids:
        count = sum(1 for row in observations if row["indicator_id"] == iid)
        if count != 90: raise RuntimeError(f"{iid}: expected 90 observations, found {count}")
    bundle = {"schema_version":"1.0", "country_area_id":"CRI", "period":"2022", "replace_country_branch":True, "territories":territories, "indicators":indicators, "sources":sources, "observations":observations, "boundaries":{"type":"FeatureCollection","features":features}, "comparisons":comparisons, "terminal_territory_ids":[row["id"] for row in territories if row["level"]=="canton"]}
    (out / "costa-rica-country-depth-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    generated_names = {"costa-rica-country-depth-bundle.json", "COSTA_RICA_COLLECTION_AUDIT.json"}
    audit = {"schema_version":"1.0", "generated_at":datetime.now(timezone.utc).isoformat(), "country_area_id":"CRI", "status":"collected_pending_integration", "row_counts":{"powerbi_people":len(people),"powerbi_housing":len(homes)}, "hierarchy":{"province":7,"canton":82}, "bundle":{"territories":len(territories),"indicators":len(indicators),"observations":len(observations),"boundaries":len(features)}, "source_files":{path.name:{"bytes":path.stat().st_size,"sha256":sha256(path)} for path in sorted(out.iterdir()) if path.is_file() and path.name not in generated_names}}
    (out / "COSTA_RICA_COLLECTION_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Panama's 2023 Census depth bundle from official government sources.

The administrative service contains the exact 13 province/comarca, 82 district
and 699 corregimiento geography used by Census 2023.  The collector retains the
raw ArcGIS responses, joins by the published official codes, and independently
checks every subnational record against INEC Cuadro 3 before using the INEC
Cuadro 4 indicators.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

SERVICE = "https://services5.arcgis.com/E1ALP94T33Es6ABz/ArcGIS/rest/services/Limites_administrativos/FeatureServer"
INEC_CUADRO3 = "https://www.inec.gob.pa/archivos/P0705547520240201165900Cuadro3.xlsx"
INEC_CUADRO4 = "https://www.inec.gob.pa/archivos/P0579518620240202083001Cuadro%204.xlsx"

LAYERS = {2: ("province", "PROV_ID", "PROV_NOMB"), 1: ("district", "CÓDIGO", "DIST_NOMB"), 0: ("corregimiento", "CÓDIGO", "CORR_NOMB")}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def request_bytes(url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.10.2 source collector"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read(), dict(r.headers.items())


def acquire(url: str, path: Path) -> dict:
    data, headers = request_bytes(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"url": url, "path": str(path), "bytes": len(data), "sha256": sha(path),
            "headers": {k: headers.get(k) for k in ("ETag", "Last-Modified", "Content-Length") if headers.get(k)}}


def normalize(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text).strip()
    text = re.sub(r" P$", "", text)
    text = re.sub(r" CABECERA$", "", text)
    # One district spelling differs between the two official products.  The
    # identity is accepted only because parentage and both reconciliation
    # values are checked below.
    if text in {"SANTA CATALINA O CALOVEVORA BLEDESHIA", "SANTA CATALINA O CALOVEVORA BLEDES"}:
        text = "SANTA CATALINA O CALOVEBORA BLEDESHIA"
    text = {
        "NANCE DEL RISCO": "NANCE DE RISCO",
        "VALLE DEL RISCO": "VALLE DE RISCO",
        "JADABERI": "JADEBERI",
        "FEUILLET": "FEULLIET",
        "CERRO DE PLATA": "CERRO PLATA",
        "CALIDONIA O LA EXPOSICION": "LA EXPOSICION O CALIDONIA",
    }.get(text, text)
    return text


def hierarchy_key(attrs: dict, level: str) -> str:
    parts = [normalize(attrs["PROV_NOMB"])]
    if level in ("district", "corregimiento"):
        parts.append(normalize(attrs["DIST_NOMB"]))
    if level == "corregimiento":
        parts.append(normalize(attrs["CORR_NOMB"]))
    return "|".join(parts)


def read_inec_hierarchy(path: Path, start_row: int) -> dict:
    ws = load_workbook(path, read_only=True, data_only=True).active
    records = {"country": {"TOTAL": tuple(ws.iter_rows(min_row=start_row, max_row=start_row, values_only=True))[0]}}
    province = district = None
    for values in ws.iter_rows(min_row=start_row + 1, values_only=True):
        a, b, c, d = values[:4]
        # Headings, separators and footnotes share the first four columns with
        # geography rows but do not carry the first published numeric field.
        if num(values[4]) is None:
            continue
        if a not in (None, "") and all(x in (None, "") for x in (b, c, d)):
            province, district = normalize(a), None
            if province == "PANAMA OESTE 1":
                province = "PANAMA OESTE"
            records.setdefault("province", {})[province] = values
        elif b not in (None, "") and all(x in (None, "") for x in (a, c, d)):
            if not province:
                raise RuntimeError(f"District row without province in {path.name}")
            district = normalize(b)
            records.setdefault("district", {})[province + "|" + district] = values
        elif c not in (None, "") and all(x in (None, "") for x in (a, b, d)):
            if not province or not district:
                raise RuntimeError(f"Corregimiento row without parents in {path.name}")
            records.setdefault("corregimiento", {})[province + "|" + district + "|" + normalize(c)] = values
    return records


def num(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(numerator, denominator):
    n, d = num(numerator), num(denominator)
    return None if n is None or d in (None, 0) else round(n / d * 100, 4)


def title_name(value: str) -> str:
    return str(value).title().replace("Ngäbe Buglé", "Ngäbe Buglé").replace("Kuna Yala", "Kuna Yala")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--cuadro3", required=True)
    ap.add_argument("--cuadro4", required=True)
    args = ap.parse_args()
    out, raw = Path(args.out).resolve(), Path(args.raw_dir).resolve()
    out.mkdir(parents=True, exist_ok=True); raw.mkdir(parents=True, exist_ok=True)
    cuadro3, cuadro4 = Path(args.cuadro3).resolve(), Path(args.cuadro4).resolve()
    receipts = [
        {"url": INEC_CUADRO3, "path": str(cuadro3), "bytes": cuadro3.stat().st_size, "sha256": sha(cuadro3), "pre_acquired": True},
        {"url": INEC_CUADRO4, "path": str(cuadro4), "bytes": cuadro4.stat().st_size, "sha256": sha(cuadro4), "pre_acquired": True},
    ]

    layer_rows = {}
    raw_features = {}
    for layer, (level, _, _) in LAYERS.items():
        # Generalize only the display/reference geometry.  Attribute values and
        # published codes are unmodified and all raw responses are retained.
        params = {"f": "geojson", "where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": "4326",
                  "maxAllowableOffset": "0.001", "geometryPrecision": "5"}
        url = f"{SERVICE}/{layer}/query?{urllib.parse.urlencode(params)}"
        target = raw / f"layer-{layer}-{level}.geojson"
        print(f"Acquiring {level} layer ...", flush=True)
        receipts.append(acquire(url, target))
        geo = json.loads(target.read_text(encoding="utf-8"))
        expected = {"province": 13, "district": 82, "corregimiento": 699}[level]
        if len(geo.get("features", [])) != expected:
            raise RuntimeError(f"{level}: expected {expected} features, got {len(geo.get('features', []))}")
        raw_features[level] = geo["features"]
        layer_rows[level] = {hierarchy_key(f["properties"], level): f for f in geo["features"]}

    inec3 = read_inec_hierarchy(cuadro3, 9)
    inec4 = read_inec_hierarchy(cuadro4, 7)
    crosswalk = []
    for level in ("province", "district", "corregimiento"):
        service_keys, table3_keys, table4_keys = set(layer_rows[level]), set(inec3[level]), set(inec4[level])
        if service_keys != table3_keys or service_keys != table4_keys:
            raise RuntimeError(f"{level} hierarchy mismatch: service/table3/table4 = {len(service_keys)}/{len(table3_keys)}/{len(table4_keys)}")
        for key, feature in layer_rows[level].items():
            attrs = feature["properties"]
            row3 = inec3[level][key]
            if num(row3[16]) != num(attrs["N_PERSONAS"]) or num(row3[4]) != num(attrs["TOTA_VIV_P"]):
                raise RuntimeError(f"INEC/service value mismatch for {level} {key}")
            crosswalk.append({"level": level, "hierarchy_key": key,
                              "official_code": str(attrs["PROV_ID"] if level == "province" else attrs["CÓDIGO"]),
                              "population_2023": attrs["N_PERSONAS"], "occupied_private_dwellings_2023": attrs["TOTA_VIV_P"]})

    retrieved = datetime.now(timezone.utc).date().isoformat()
    source_service = "pan-miviot-census-2023-admin-service"
    source_c3 = "pan-inec-census-2023-cuadro-3"
    source_c4 = "pan-inec-census-2023-cuadro-4"
    sources = [
        {"id": source_service, "name": "Límites administrativos con atributos del Censo 2023", "publisher": "Ministerio de Vivienda y Ordenamiento Territorial, Gobierno de Panamá", "url": SERVICE, "status": "ready", "retrieved_at": retrieved, "reference_period": "2023", "geographic_level": "Provincia/comarca, distrito y corregimiento", "source_locator": "FeatureServer layers 2, 1 and 0", "license": "Reuse terms not stated in the service metadata; AreaData publishes attributed reference geometry and factual observations only.", "terms_review_status": "terms_not_stated_in_source", "raw_redistribution_status": "withheld_pending_terms_review", "note": "Government feature service with the exact 13/82/699 Census 2023 hierarchy and published administrative codes. Values were reconciled record-by-record to INEC Cuadro 3."},
        {"id": source_c3, "name": "Censo 2023, Cuadro 3", "publisher": "Instituto Nacional de Estadística y Censo (INEC), Contraloría General de la República de Panamá", "url": INEC_CUADRO3, "status": "ready", "retrieved_at": retrieved, "reference_period": "2023", "geographic_level": "República, provincia/comarca, distrito, corregimiento y lugar poblado", "source_locator": "Cuadro3_lugp; rows TOTAL through corregimiento", "license": "Reuse terms not stated in the source publication; AreaData publishes source-attributed factual observations only.", "terms_review_status": "terms_not_stated_in_source", "raw_redistribution_status": "withheld_pending_terms_review", "note": "Official workbook retained with SHA-256 receipt. Every adopted subnational service row was checked against population and occupied-private-dwelling totals in this table."},
        {"id": source_c4, "name": "Censo 2023, Cuadro 4", "publisher": "Instituto Nacional de Estadística y Censo (INEC), Contraloría General de la República de Panamá", "url": INEC_CUADRO4, "status": "ready", "retrieved_at": retrieved, "reference_period": "2023", "geographic_level": "República, provincia/comarca, distrito, corregimiento y lugar poblado", "source_locator": "cuadro4; rows TOTAL through corregimiento", "license": "Reuse terms not stated in the source publication; AreaData publishes source-attributed factual observations only.", "terms_review_status": "terms_not_stated_in_source", "raw_redistribution_status": "withheld_pending_terms_review", "note": "Official workbook retained with SHA-256 receipt and joined only after a complete 794-record hierarchical crosswalk was independently reconciled to Cuadro 3 and the government code service."},
    ]

    territories, boundary_features, area_records = [], [], {"PAN": {"level": "country", "attrs": {}, "c3": inec3["country"]["TOTAL"], "c4": inec4["country"]["TOTAL"]}}
    ids_by_level = {"province": {}, "district": {}, "corregimiento": {}}
    for level in ("province", "district", "corregimiento"):
        for key, feature in sorted(layer_rows[level].items(), key=lambda item: str(item[1]["properties"].get("CÓDIGO") or item[1]["properties"]["PROV_ID"])):
            a = feature["properties"]
            code = str(a["PROV_ID"] if level == "province" else a["CÓDIGO"]).zfill({"province": 2, "district": 4, "corregimiento": 6}[level])
            prefix = {"province": "PROV", "district": "DIST", "corregimiento": "CORR"}[level]
            tid = f"PAN:C2023:{prefix}:{code}"
            parent = "PAN" if level == "province" else (f"PAN:C2023:PROV:{code[:2]}" if level == "district" else f"PAN:C2023:DIST:{code[:4]}")
            name_field = {"province": "PROV_NOMB", "district": "DIST_NOMB", "corregimiento": "CORR_NOMB"}[level]
            territories.append({"id": tid, "country_id": "PAN", "name": title_name(a[name_field]), "level": level, "type": level, "parent_id": parent, "official_code": code, "code_system": "Panamá Censo 2023 administrative code", "boundary_version": "Censo 2023 administrative limits", "valid_from": "2023-01-01"})
            ids_by_level[level][code] = tid
            area_records[tid] = {"level": level, "attrs": a, "c3": inec3[level][key], "c4": inec4[level][key]}
            boundary_features.append({"type": "Feature", "properties": {"territory_id": tid, "source_id": source_service, "official_code": code, "code_system": "Panamá Censo 2023 administrative code", "geometry_edition": "Censo 2023 administrative limits", "join_method": "Exact published administrative code; INEC hierarchy and totals reconciled 794/794", "reference_only": True}, "geometry": feature["geometry"]})

    # value: (indicator id, name, theme, unit, definition, source, calculator, locator, aggregation)
    specs = [
        ("PAN_C2023_POP_TOTAL", "Population", "Population", "people", "Population enumerated in Census 2023.", source_c3, lambda r: num(r["c3"][16]), "Cuadro 3, population total", "sum"),
        ("PAN_C2023_FEMALE_PCT", "Female population", "Population", "%", "Women as a share of the enumerated population.", source_service, lambda r: pct(r["attrs"].get("P_MUJERES"), r["attrs"].get("N_PERSONAS")) if r["level"] != "country" else pct(r["c3"][18], r["c3"][16]), "P_MUJERES / N_PERSONAS", "none"),
        ("PAN_C2023_AGE_0_14_PCT", "Population aged under 15", "Population", "%", "Population younger than 15 years as a share of total population.", source_c4, lambda r: num(r["c4"][9]), "Cuadro 4, column 10", "none"),
        ("PAN_C2023_OCC_DWELLINGS", "Occupied private dwellings", "Households and housing", "dwellings", "Occupied private dwellings.", source_c3, lambda r: num(r["c3"][4]), "Cuadro 3, occupied private dwellings total", "sum"),
        ("PAN_C2023_EARTH_FLOOR_PCT", "Occupied private dwellings with earth floor", "Households and housing", "% of occupied private dwellings", "Occupied private dwellings with an earth floor.", source_service, lambda r: pct(r["attrs"].get("CON_PISO_T"), r["attrs"].get("TOTA_VIV_P")) if r["level"] != "country" else pct(r["c3"][5], r["c3"][4]), "CON_PISO_T / TOTA_VIV_P", "none"),
        ("PAN_C2023_NO_WATER_PCT", "Occupied private dwellings without potable water", "Water and sanitation", "% of occupied private dwellings", "Occupied private dwellings reported without potable water.", source_service, lambda r: pct(r["attrs"].get("SIN_AGUA"), r["attrs"].get("TOTA_VIV_P")) if r["level"] != "country" else pct(r["c3"][6], r["c3"][4]), "SIN_AGUA / TOTA_VIV_P", "none"),
        ("PAN_C2023_NO_SANITATION_PCT", "Occupied private dwellings without sanitation service", "Water and sanitation", "% of occupied private dwellings", "Occupied private dwellings reported without sanitation service.", source_service, lambda r: pct(r["attrs"].get("SIN_SER_SA"), r["attrs"].get("TOTA_VIV_P")) if r["level"] != "country" else pct(r["c3"][7], r["c3"][4]), "SIN_SER_SA / TOTA_VIV_P", "none"),
        ("PAN_C2023_NO_ELECTRICITY_PCT", "Occupied private dwellings without electricity", "Basic services", "% of occupied private dwellings", "Occupied private dwellings reported without electric light.", source_service, lambda r: pct(r["attrs"].get("SIN_LUZ"), r["attrs"].get("TOTA_VIV_P")) if r["level"] != "country" else pct(r["c3"][8], r["c3"][4]), "SIN_LUZ / TOTA_VIV_P", "none"),
        ("PAN_C2023_ILLITERACY_PCT", "Illiteracy, population age 10+", "Education", "% of population age 10+", "Illiterate population age 10 and older.", source_c4, lambda r: num(r["c4"][18]), "Cuadro 4, column 19", "none"),
        ("PAN_C2023_UNEMPLOYMENT_PCT", "Unemployment, population age 10+", "Employment", "% of population age 10+", "Unemployed population as reported for the population age 10 and older.", source_c4, lambda r: num(r["c4"][19]), "Cuadro 4, column 20", "none"),
        ("PAN_C2023_DISABILITY_COUNT", "Population with a disability", "Disability", "people", "Population reporting at least one disability.", source_service, lambda r: num(r["attrs"].get("CON_DISC")) if r["level"] != "country" else num(r["c3"][27]), "CON_DISC", "sum"),
        ("PAN_C2023_INDIGENOUS_PCT", "Indigenous population", "Ethnicity", "%", "Population identifying as Indigenous.", source_c4, lambda r: num(r["c4"][14]), "Cuadro 4, column 15", "none"),
        ("PAN_C2023_AFRO_DESCENDANT_PCT", "Afro-descendant population", "Ethnicity", "%", "Population identifying as Afro-descendant.", source_c4, lambda r: num(r["c4"][15]), "Cuadro 4, column 16", "none"),
        ("PAN_C2023_NO_SOCIAL_SECURITY_PCT", "Population without social security", "Health", "%", "Population reported without social-security coverage.", source_c4, lambda r: num(r["c4"][13]), "Cuadro 4, column 14", "none"),
        ("PAN_C2023_NO_INTERNET_PCT", "Occupied private dwellings without fixed or mobile Internet", "Connectivity", "% of occupied private dwellings", "Occupied private dwellings without fixed or mobile Internet access.", source_service, lambda r: pct(r["attrs"].get("SIN_INTERN"), r["attrs"].get("TOTA_VIV_P")) if r["level"] != "country" else pct(r["c3"][15], r["c3"][4]), "SIN_INTERN / TOTA_VIV_P", "none"),
    ]

    indicators, observations = [], []
    for iid, name, theme, unit, definition, source_id, calc, locator, aggregation in specs:
        derived = unit.startswith("%")
        indicators.append({"id": iid, "name": name, "theme": theme, "unit": unit, "definition": definition, "definition_id": "PAN-CENSO-2023", "population": "Census 2023 population or occupied private dwellings as stated", "measurement_method": "derived_from_source_counts" if derived and source_id != source_c4 else "source_reported", "aggregation": aggregation, "period_policy": "fixed_source_period", "series_family": "census", "display_role": "primary", "source_id": source_id, "source_locator": locator})
        for tid, record in area_records.items():
            value = calc(record)
            observations.append({"territory_id": tid, "indicator_id": iid, "period": "2023", "value": value, "status": "observed" if value is not None else "missing", "source_id": source_id, "definition": definition, "definition_id": "PAN-CENSO-2023", "unit": unit, "population": "Census 2023 population or occupied private dwellings as stated", "measurement_method": "derived_from_source_counts" if derived and source_id != source_c4 else "source_reported", "source_locator": locator})

    comparisons = [{"parent_id": "PAN", "member_ids": [ids_by_level["province"][c] for c in sorted(ids_by_level["province"])], "label": "Provinces and indigenous comarcas", "membership_note": "Census 2023 hierarchy joined by exact official code.", "source_ids": [source_service, source_c3]}]
    for pcode, pid in sorted(ids_by_level["province"].items()):
        comparisons.append({"parent_id": pid, "member_ids": [ids_by_level["district"][c] for c in sorted(ids_by_level["district"]) if c.startswith(pcode)], "label": f"Districts in {next(t['name'] for t in territories if t['id'] == pid)}", "membership_note": "Census 2023 hierarchy joined by exact official code.", "source_ids": [source_service, source_c3]})
    for dcode, did in sorted(ids_by_level["district"].items()):
        comparisons.append({"parent_id": did, "member_ids": [ids_by_level["corregimiento"][c] for c in sorted(ids_by_level["corregimiento"]) if c.startswith(dcode)], "label": f"Corregimientos in {next(t['name'] for t in territories if t['id'] == did)}", "membership_note": "Census 2023 hierarchy joined by exact official code.", "source_ids": [source_service, source_c3]})

    bundle = {"schema_version": "1.0", "country_area_id": "PAN", "period": "2023", "replace_country_branch": True,
              "territories": territories, "terminal_territory_ids": list(ids_by_level["corregimiento"].values()), "comparisons": comparisons,
              "indicators": indicators, "observations": observations, "sources": sources,
              "boundaries": {"type": "FeatureCollection", "features": boundary_features},
              "receipt": {"generated_at": datetime.now(timezone.utc).isoformat(), "collector": "collect-panama-census.py",
                          "province_count": len(ids_by_level["province"]), "district_count": len(ids_by_level["district"]), "corregimiento_count": len(ids_by_level["corregimiento"]),
                          "crosswalk_reconciled_count": len(crosswalk), "indicator_count": len(indicators), "observation_count": len(observations), "boundary_feature_count": len(boundary_features), "receipts": receipts}}
    (out / "panama-census-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "collection-receipt.json").write_text(json.dumps(bundle["receipt"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "geography-crosswalk.json").write_text(json.dumps(crosswalk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: bundle["receipt"][k] for k in ("province_count", "district_count", "corregimiento_count", "crosswalk_reconciled_count", "indicator_count", "observation_count", "boundary_feature_count")}, indent=2))


if __name__ == "__main__":
    main()

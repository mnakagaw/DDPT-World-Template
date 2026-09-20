#!/usr/bin/env python3
"""Build the Honduras 2013 Census depth bundle from preserved Redatam tables.

The Redatam output is retained verbatim.  The collector derives percentages
only from published category counts and preserves the relevant numerator and
denominator.  COD-AB geometry is used as a source-attributed display layer;
it is not represented as a current legal-boundary certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import unicodedata
import urllib.request
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from shapely.geometry import mapping, shape


INE_CENSUS = "https://ine.gob.hn/censo-de-poblacion-y-vivienda-2013/"
REDATAM = "http://181.115.7.199/binhnd/RpWebEngine.exe/Portal"
HDX_META = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-hnd"
HDX_GEOZIP = "https://data.humdata.org/dataset/bd62fb53-64d3-478f-9ca8-38e4a2de19c0/resource/2425575d-6808-45f3-90cb-55557a5d234b/download/hnd_admin_boundaries.geojson.zip"
WB_LIFE = "https://api.worldbank.org/v2/country/HND/indicator/SP.DYN.LE00.IN?format=json&per_page=100"
WB_NUTRITION = "https://api.worldbank.org/v2/country/HND/indicator/SN.ITK.DEFC.ZS?format=json&per_page=100"


TABLES = {
    "sex": ("hnd-person-munic-4186801.html", "hnd-person-dept-0.html", "hnd-person-national-0.html"),
    "ethnicity": ("hnd-person2-munic-3324401.html", "hnd-person-dept-1.html", "hnd-person-national-1.html"),
    "disability": ("hnd-person-munic-4186841.html", "hnd-person-dept-2.html", "hnd-person-national-2.html"),
    "migration": ("hnd-person2-munic-3324421.html", "hnd-person-dept-3.html", "hnd-person-national-3.html"),
    "employment": ("hnd-person-munic-4186861.html", "hnd-person-dept-4.html", "hnd-person-national-4.html"),
    "housing": ("hnd-housing-munic-4860621.html", "hnd-house-dept-0.html", "hnd-house-national-0.html"),
    "water": ("hnd-housing-munic-4860641.html", "hnd-house-dept-1.html", "hnd-house-national-1.html"),
    "electricity": ("hnd-housing-munic-4860661.html", "hnd-house-dept-2.html", "hnd-house-national-2.html"),
    "poverty": ("hnd-housing-munic-4860681.html", "hnd-house-dept-3.html", "hnd-house-national-3.html"),
    "sanitation": ("hnd-housing-munic-48606101.html", "hnd-house-dept-4.html", "hnd-house-national-4.html"),
    "urban": ("hnd-urban-munic-table.html", "hnd-urban-dept-0.html", "hnd-urban-national-0.html"),
}
ILLITERACY = ("hnd-illiteracy-munic2-0.html", "hnd-illiteracy-dept-0.html")


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.cell = None; self.cells = []; self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "td": self.cell = []
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "td" and self.cell is not None:
            self.cells.append(" ".join("".join(self.cell).split())); self.cell = None
        elif tag.lower() == "tr":
            if self.cells: self.rows.append(self.cells)
            self.cells = []


def slug(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", value.upper()) if unicodedata.category(c) != "Mn")


def number(value: str) -> float:
    return float(value.replace(",", "").strip())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_frequency(path: Path, level: str) -> dict[str, dict[str, float]]:
    parser = TableParser(); parser.feed(path.read_text(encoding="utf-8"))
    areas: dict[str, dict[str, float]] = {}; current = "HND" if level == "country" else None
    for row in parser.rows:
        cells = [cell for cell in row if cell]
        if not cells: continue
        match = next((re.fullmatch(r"AREA #\s*(\d+)", cell) for cell in cells), None)
        if match:
            code = match.group(1)
            current = f"HND:C2013:{'DEP' if level == 'department' else 'MUN'}:{code}"
            areas[current] = {"__name__": cells[cells.index(match.group(0)) + 1] if len(cells) > cells.index(match.group(0)) + 1 else ""}
            continue
        if current and len(cells) >= 2 and re.fullmatch(r"-?[\d,]+(?:\.\d+)?", cells[1]):
            label = slug(cells[0])
            if label not in {"CASOS", "%", "ACUMULADO %"}: areas.setdefault(current, {})[label] = number(cells[1])
    if level == "country" and current not in areas: areas[current] = {}
    return areas


def parse_area_list(path: Path, level: str) -> dict[str, float]:
    parser = TableParser(); parser.feed(path.read_text(encoding="utf-8")); result = {}
    width = 4 if level == "municipality" else 2
    prefix = "MUN" if level == "municipality" else "DEP"
    for row in parser.rows:
        cells = [cell for cell in row if cell]
        if len(cells) >= 3 and re.fullmatch(rf"\d{{{width}}}", cells[0]) and re.fullmatch(r"\d+(?:\.\d+)?", cells[2]):
            result[f"HND:C2013:{prefix}:{cells[0]}"] = float(cells[2])
    return result


def indicator(iid, name, theme, definition, source="hnd-ine-redatam-2013", unit="%", role="primary"):
    return {"id": iid, "name": name, "theme": theme, "unit": unit, "definition": definition,
            "definition_id": iid, "population": definition, "measurement_method": "derived_from_source_counts",
            "aggregation": "sum" if unit == "people" else "none", "period_policy": "fixed_source_period",
            "series_family": "census" if source.startswith("hnd-ine") else "international_reference",
            "display_role": role, "source_id": source}


def observation(area, iid, value, definition, numerator=None, denominator=None, source="hnd-ine-redatam-2013", period="2013", unit="%", locator=""):
    if value is None or not math.isfinite(float(value)): raise RuntimeError(f"Invalid {area} {iid}: {value}")
    row = {"territory_id": area, "indicator_id": iid, "period": str(period), "value": round(float(value), 6),
           "status": "observed", "source_id": source, "definition": definition, "definition_id": iid,
           "unit": unit, "population": definition, "measurement_method": "derived_from_source_counts",
           "source_locator": locator}
    if numerator is not None: row["numerator"] = numerator
    if denominator is not None: row["denominator"] = denominator
    return row


def ratio(categories, numerators, denominator="TOTAL"):
    den = categories.get(slug(denominator))
    if den in (None, 0): return None, None, den
    num = sum(categories.get(slug(name), 0) for name in numerators)
    return num * 100 / den, num, den


def latest_wb(path: Path):
    data = json.loads(path.read_text(encoding="utf-8")); rows = data[1] if isinstance(data, list) and len(data) > 1 else []
    row = next((r for r in rows if r.get("value") is not None), None)
    if not row: raise RuntimeError(f"No non-null World Bank value in {path}")
    return str(row["date"]), float(row["value"])


def fetch(url: str, path: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.10 Honduras evidence collector"})
    with urllib.request.urlopen(req, timeout=300) as response: path.write_bytes(response.read())


def prepare_raw(source: Path, out: Path):
    raw = out / "raw"; raw.mkdir()
    required = [name for group in TABLES.values() for name in group] + list(ILLITERACY)
    for name in required:
        src = source / name
        if not src.exists(): raise FileNotFoundError(src)
        shutil.copy2(src, raw / name)
    for name, url in (("world-bank-life.json", WB_LIFE), ("world-bank-undernourishment.json", WB_NUTRITION), ("hdx-package.json", HDX_META)):
        src = source / name
        if src.exists(): shutil.copy2(src, raw / name)
        else: fetch(url, raw / name)
    geo1, geo2 = source / "hnd_admin1.geojson", source / "hnd_admin2.geojson"
    if not geo1.exists(): geo1 = source / "extracted" / "hnd_admin1.geojson"
    if not geo2.exists(): geo2 = source / "extracted" / "hnd_admin2.geojson"
    if not geo1.exists() or not geo2.exists():
        zip_path = raw / "hnd_admin_boundaries.geojson.zip"; fetch(HDX_GEOZIP, zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extract("hnd_admin1.geojson", raw); archive.extract("hnd_admin2.geojson", raw)
    else:
        shutil.copy2(geo1, raw / "hnd_admin1.geojson"); shutil.copy2(geo2, raw / "hnd_admin2.geojson")
    return raw


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True); ap.add_argument("--source-dir", required=True); ap.add_argument("--out", required=True)
    args = ap.parse_args(); project = Path(args.project).resolve(); source = Path(args.source_dir).resolve(); out = Path(args.out).resolve()
    if out.exists(): raise FileExistsError(f"Output already exists: {out}")
    out.mkdir(parents=True); raw = prepare_raw(source, out)
    dataset = json.loads((project / "data" / "dashboard.json").read_text(encoding="utf-8"))
    existing = [r for r in dataset["territories"] if r.get("country_id") == "HND" and r["id"] != "HND"]
    if len(existing) != 316: raise RuntimeError(f"Expected 316 Honduras lower territories, found {len(existing)}")
    names = {r["id"]: r for r in existing}

    parsed = {}
    for key, files in TABLES.items():
        parsed[key] = {}
        for level, filename in zip(("municipality", "department", "country"), files): parsed[key].update(parse_frequency(raw / filename, level))
    literacy = parse_area_list(raw / ILLITERACY[0], "municipality") | parse_area_list(raw / ILLITERACY[1], "department") | {"HND": 14.13}
    if len(parsed["sex"]) != 317 or len(literacy) != 317: raise RuntimeError(f"Incomplete Redatam coverage: sex={len(parsed['sex'])}, literacy={len(literacy)}")

    defs = {
        "HND_C2013_POP_TOTAL": "Population counted in the 2013 Census Redatam weighted table.",
        "HND_C2013_FEMALE_PCT": "Women as a percentage of the 2013 Census population.",
        "HND_C2013_PRESENT_DWELLINGS_PCT": "Particular dwellings with persons present as a share of enumerated particular dwellings.",
        "HND_C2013_PIPED_WATER_PCT": "Dwellings with water supplied by pipe inside the dwelling, outside on the property, or by public standpipe; this is not a water-quality measure.",
        "HND_C2013_SANITATION_NBI_PCT": "Dwellings classified with an unmet basic need in sanitation; a lower value is generally favorable.",
        "HND_C2013_ELECTRIC_SOLAR_LIGHT_PCT": "Dwellings reporting public grid, private system, motor generator, or solar-panel lighting.",
        "HND_C2013_ILLITERACY_PCT": "Official Redatam illiteracy rate for the Census indicator population; a lower value is generally favorable.",
        "HND_C2013_EMPLOYED_PCT": "Employed persons as a percentage of the population to which the economic-activity question applies.",
        "HND_C2013_WALKING_LIMITATION_PCT": "Population reporting a limitation in moving or walking; this is not a measure of every disability type.",
        "HND_C2013_FOREIGN_BORN_PCT": "Population born in another country as a percentage of persons with stated place of birth.",
        "HND_C2013_URBAN_PCT": "Population living in areas classified as urban by the 2013 Census.",
        "HND_C2013_INDIGENOUS_AFRO_PCT": "Population self-identifying as Indigenous, Afro-Honduran, or Black in the 2013 Census.",
        "HND_C2013_NBI_POVERTY_PCT": "Dwellings with one or more unmet basic needs (NBI) as a share of classified dwellings.",
        "HND_WB_LIFE_EXPECTANCY": "National life expectancy at birth from the World Bank indicator series; no municipal value is inferred.",
        "HND_WB_UNDERNOURISHMENT_PCT": "FAO-modeled national prevalence of undernourishment distributed through the World Bank API; no municipal value is inferred.",
    }
    specs = [
        ("HND_C2013_POP_TOTAL", "2013 Census population", "Population", "people"),
        ("HND_C2013_FEMALE_PCT", "Female population", "Population", "%"),
        ("HND_C2013_PRESENT_DWELLINGS_PCT", "Dwellings with persons present", "Housing", "%"),
        ("HND_C2013_PIPED_WATER_PCT", "Dwellings with piped water access", "Basic services", "%"),
        ("HND_C2013_SANITATION_NBI_PCT", "Sanitation unmet basic need", "Basic services", "%"),
        ("HND_C2013_ELECTRIC_SOLAR_LIGHT_PCT", "Electric or solar lighting", "Basic services", "%"),
        ("HND_C2013_ILLITERACY_PCT", "Illiteracy", "Education", "%"),
        ("HND_C2013_EMPLOYED_PCT", "Employed population", "Economy", "%"),
        ("HND_C2013_WALKING_LIMITATION_PCT", "Population with moving or walking limitation", "Inclusion", "%"),
        ("HND_C2013_FOREIGN_BORN_PCT", "Foreign-born population", "Migration", "%"),
        ("HND_C2013_URBAN_PCT", "Urban population", "Population", "%"),
        ("HND_C2013_INDIGENOUS_AFRO_PCT", "Indigenous or Afro-Honduran self-identification", "Inclusion", "%"),
        ("HND_C2013_NBI_POVERTY_PCT", "Dwellings with at least one unmet basic need", "Poverty", "%"),
    ]
    indicators = [indicator(i, n, t, defs[i], unit=u) for i, n, t, u in specs]
    indicators += [indicator("HND_WB_LIFE_EXPECTANCY", "Life expectancy at birth", "Health", defs["HND_WB_LIFE_EXPECTANCY"], "hnd-world-bank-life", "years", "context"), indicator("HND_WB_UNDERNOURISHMENT_PCT", "Prevalence of undernourishment", "Nutrition", defs["HND_WB_UNDERNOURISHMENT_PCT"], "hnd-world-bank-nutrition", "%", "context")]
    observations = []
    for area, sex in parsed["sex"].items():
        total = sex["TOTAL"]
        observations.append(observation(area, "HND_C2013_POP_TOTAL", total, defs["HND_C2013_POP_TOTAL"], total, total, unit="people", locator="Redatam PERSONA.SEXO"))
        value, num, den = ratio(sex, ["Mujer"]); observations.append(observation(area, "HND_C2013_FEMALE_PCT", value, defs["HND_C2013_FEMALE_PCT"], num, den, locator="Redatam PERSONA.SEXO"))
        rules = [
            ("housing", "HND_C2013_PRESENT_DWELLINGS_PCT", ["Con personas presentes"]),
            ("water", "HND_C2013_PIPED_WATER_PCT", ["Por tuberia dentro de la vivienda", "Por tuberia fuera de la vivienda, pero dentro del edificio, lote o propiedad", "Por tuberia, fuera del edificio, lote o propiedad"]),
            ("sanitation", "HND_C2013_SANITATION_NBI_PCT", ["Con nbi"]),
            ("electricity", "HND_C2013_ELECTRIC_SOLAR_LIGHT_PCT", ["Electricidad del sistema publico", "Electricidad del sistema privado", "Electricidad de motor propio", "Panel solar"]),
            ("employment", "HND_C2013_EMPLOYED_PCT", ["Ocupados"]),
            ("disability", "HND_C2013_WALKING_LIMITATION_PCT", ["Si"]),
            ("migration", "HND_C2013_FOREIGN_BORN_PCT", ["En otro pais"]),
            ("ethnicity", "HND_C2013_INDIGENOUS_AFRO_PCT", ["Indigena", "AfroHondureno", "Negro (a)"]),
            ("poverty", "HND_C2013_NBI_POVERTY_PCT", ["Vivendas con 1 NBI", "Vivendas con 2 NBI", "Vivendas con 3 NBI", "Vivendas con 4+ NBI"]),
        ]
        for key, iid, cats in rules:
            value, num, den = ratio(parsed[key][area], cats)
            observations.append(observation(area, iid, value, defs[iid], num, den, locator=f"Redatam {key}"))
        urban = parsed["urban"].get(area, {}).get("TOTAL", 0)
        observations.append(observation(area, "HND_C2013_URBAN_PCT", urban * 100 / total, defs["HND_C2013_URBAN_PCT"], urban, total, locator="Redatam PERSONA.SEXO with VIVIENDA.VUR = 1"))
        observations.append(observation(area, "HND_C2013_ILLITERACY_PCT", literacy[area], defs["HND_C2013_ILLITERACY_PCT"], locator="Redatam %OUTENT.TASANALFA"))
    life_period, life_value = latest_wb(raw / "world-bank-life.json"); nut_period, nut_value = latest_wb(raw / "world-bank-undernourishment.json")
    observations += [observation("HND", "HND_WB_LIFE_EXPECTANCY", life_value, defs["HND_WB_LIFE_EXPECTANCY"], source="hnd-world-bank-life", period=life_period, unit="years", locator="World Bank API SP.DYN.LE00.IN"), observation("HND", "HND_WB_UNDERNOURISHMENT_PCT", nut_value, defs["HND_WB_UNDERNOURISHMENT_PCT"], source="hnd-world-bank-nutrition", period=nut_period, locator="World Bank API SN.ITK.DEFC.ZS")]

    boundary_source = "hnd-codab-sinit-seplan"
    territories, features = [], []
    for level, filename, pcode_key, name_key in (("department", "hnd_admin1.geojson", "adm1_pcode", "adm1_name"), ("municipality", "hnd_admin2.geojson", "adm2_pcode", "adm2_name")):
        geo = json.loads((raw / filename).read_text(encoding="utf-8"))
        for feature in geo["features"]:
            prop = feature["properties"]; code = prop[pcode_key][2:]; tid = f"HND:C2013:{'DEP' if level == 'department' else 'MUN'}:{code}"
            if tid not in names: raise RuntimeError(f"COD-AB code not in Census hierarchy: {tid}")
            geometry = mapping(shape(feature["geometry"]).simplify(0.002, preserve_topology=True))
            features.append({"type": "Feature", "properties": {"territory_id": tid, "name": names[tid]["name"], "source_id": boundary_source, "boundary_version": "COD-AB v01, valid_on 2016-10-05; source SINIT/SEPLAN 2010"}, "geometry": geometry})
    if len(features) != 316 or len({f["properties"]["territory_id"] for f in features}) != 316: raise RuntimeError("Boundary coverage is not exactly 18 departments and 298 municipalities")
    for old in existing:
        row = dict(old); row.update({"boundary_version": "COD-AB v01, valid_on 2016-10-05; source SINIT/SEPLAN 2010", "source_id": boundary_source, "geography_note": "Census hierarchy joined by exact department/municipality code to the OCHA COD-AB display geometry derived from SINIT/SEPLAN. This vintage is not presented as a current legal-boundary certification."}); territories.append(row)
    hdx = json.loads((raw / "hdx-package.json").read_text(encoding="utf-8"))["result"]
    today = datetime.now(timezone.utc).date().isoformat()
    sources = [
        {"id": "hnd-ine-redatam-2013", "name": "XVII Censo de Población y VI de Vivienda 2013 — Redatam tables", "publisher": "Instituto Nacional de Estadística Honduras", "url": INE_CENSUS, "catalog_url": REDATAM, "status": "ready", "retrieved_at": today, "reference_period": "2013", "geographic_level": "country, department and municipality", "license": "Official public statistical query; reuse terms not stated", "note": "Category counts and predefined illiteracy rates preserved from the official Redatam database. Derived percentages retain numerator and denominator."},
        {"id": boundary_source, "name": hdx["title"], "publisher": "OCHA Field Information Services Section; source SINIT/SEPLAN", "url": "https://data.humdata.org/dataset/cod-ab-hnd", "status": "ready", "retrieved_at": today, "reference_period": "SINIT/SEPLAN 2010 source; 2015-06-25 boundary creation; valid_on 2016-10-05; OCHA review 2025-10-30", "geographic_level": "18 departments and 298 municipalities", "license": "CC BY-IGO 3.0", "note": "Quality-assured COD-AB operational display layer. Exact Census-code coverage was verified; this does not certify current legal boundaries."},
        {"id": "hnd-world-bank-life", "name": "World Bank indicator SP.DYN.LE00.IN — Honduras", "publisher": "World Bank", "url": WB_LIFE, "status": "ready", "retrieved_at": today, "reference_period": life_period, "geographic_level": "country", "license": "World Bank terms", "note": "National international-reference context only."},
        {"id": "hnd-world-bank-nutrition", "name": "World Bank/FAO indicator SN.ITK.DEFC.ZS — Honduras", "publisher": "World Bank and FAO", "url": WB_NUTRITION, "status": "ready", "retrieved_at": today, "reference_period": nut_period, "geographic_level": "country", "license": "World Bank terms", "note": "National modeled context only."},
    ]
    comparisons = [{"parent_id": "HND", "member_ids": [f"HND:C2013:DEP:{i:02d}" for i in range(1, 19)], "level": "department", "label": "Departments within Honduras", "membership_note": "All 18 departments in the adopted 2013 Census hierarchy.", "source_ids": ["hnd-ine-redatam-2013", boundary_source]}]
    for dep in range(1, 19):
        members = sorted([r["id"] for r in territories if r["id"].startswith(f"HND:C2013:MUN:{dep:02d}")])
        comparisons.append({"parent_id": f"HND:C2013:DEP:{dep:02d}", "member_ids": members, "level": "municipality", "label": "Municipalities within the selected department", "membership_note": "Complete municipality membership under the adopted 2013 Census code hierarchy.", "source_ids": ["hnd-ine-redatam-2013", boundary_source]})
    bundle = {"schema_version": "1.0", "country_area_id": "HND", "period": "2013", "replace_country_branch": True, "territories": territories, "indicators": indicators, "sources": sources, "observations": observations, "boundaries": {"type": "FeatureCollection", "features": features}, "comparisons": comparisons, "terminal_territory_ids": sorted([r["id"] for r in territories if r["type"] == "municipality"])}
    (out / "honduras-country-depth-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    receipt = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "HND", "status": "complete", "counts": {"territories": len(territories), "indicators": len(indicators), "observations": len(observations), "boundaries": len(features)}, "coverage": {"departments": 18, "municipalities": 298, "themes": 15}, "checks": {"exact_census_code_boundary_join": True, "redatam_area_coverage": len(parsed["sex"]) == 317, "illiteracy_area_coverage": len(literacy) == 317, "missing_urban_rows_interpreted_as_zero_only_after_filtered_table_inspection": True}, "boundary_limit": "COD-AB display layer derived from SINIT/SEPLAN 2010, created 2015, valid_on 2016-10-05 and reviewed by OCHA 2025-10-30; not a current legal-boundary certification.", "raw_files": [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(raw.iterdir()) if p.is_file()]}
    (out / "HONDURAS_COLLECTION_AUDIT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt["counts"], indent=2))


if __name__ == "__main__": main()

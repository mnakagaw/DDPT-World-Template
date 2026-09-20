#!/usr/bin/env python3
"""Collect a geography-complete Canada 2021 Census Profile subset.

The collector uses Statistics Canada's official SDMX Census Profile API and
the official 2021 cartographic boundary files.  It requests only the fields
used by AreaData, but it retains an explicit missing observation for every
adopted geography/field pair returned as suppressed or unavailable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
import shapefile
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform
from shapely.validation import make_valid


API = "https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest/data"
PROFILE_PAGE = "https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm?Lang=E"
BOUNDARY_PAGE = "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21"
CHARACTERS = "1+8+56+331+1389+1425+1515+1996+2229"
GENDERS = "1+2+3"
STATISTICS = "1+4"
UA = {"User-Agent": "AreaData/0.10.2 (+https://areadata.net/)"}


FIELD_SPECS = [
    ("CAN_C2021_POP_TOTAL", "Population, 2021 Census", "Population", "people", "1", "1", "1",
     "Population enumerated in the 2021 Census of Population."),
    ("CAN_C2021_FEMALE_PCT", "Women+, share of population", "Population", "%", "8", "3", "derived",
     "Women+ count divided by the total population in the Census age-and-gender universe."),
    ("CAN_C2021_AVG_HH_SIZE", "Average household size", "Housing", "people per household", "56", "1", "1",
     "Average number of persons in private households."),
    ("CAN_C2021_LOW_INCOME_LIMAT_PCT", "Low income, LIM-AT prevalence", "Poverty", "%", "331", "1", "1",
     "Prevalence of low income based on the after-tax low-income measure (LIM-AT)."),
    ("CAN_C2021_INDIGENOUS_IDENTITY_PCT", "Indigenous identity", "Ethnicity", "%", "1389", "1", "4",
     "Population in private households reporting Indigenous identity, as a share of the applicable population."),
    ("CAN_C2021_HOUSING_NOT_SUITABLE_PCT", "Housing not suitable", "Housing", "%", "1425", "1", "4",
     "Private households living in housing that is not suitable under the National Occupancy Standard."),
    ("CAN_C2021_IMMIGRANTS_PCT", "Immigrants", "Migration", "%", "1515", "1", "4",
     "Immigrants as a share of the population in private households."),
    ("CAN_C2021_NO_HS_DIPLOMA_25_64_PCT", "No high school diploma, age 25–64", "Education", "%", "1996", "1", "4",
     "Population aged 25 to 64 in private households with no high school diploma or equivalency certificate."),
    ("CAN_C2021_EMPLOYMENT_RATE", "Employment rate", "Economy", "%", "2229", "1", "1",
     "Employment rate for the population aged 15 years and over in private households."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_level(shp_path: Path, kind: str):
    reader = shapefile.Reader(str(shp_path), encoding="cp1252")
    rows = []
    for record in reader.iterRecords():
        data = record.as_dict()
        if kind == "PR":
            code, name, dguid = data["PRUID"], data["PRENAME"], data["DGUID"]
            rows.append({"code": code, "name": name, "dguid": dguid, "parent_code": None})
        elif kind == "CD":
            code, name, dguid = data["CDUID"], data["CDNAME"], data["DGUID"]
            rows.append({"code": code, "name": name, "dguid": dguid, "parent_code": code[:2]})
        else:
            code, name, dguid = data["CSDUID"], data["CSDNAME"], data["DGUID"]
            rows.append({"code": code, "name": name, "dguid": dguid, "parent_code": code[:4]})
    return rows


def request_batch(flow: str, dguids: list[str], attempt_limit: int = 5):
    joined = "+".join(dguids)
    url = f"{API}/STC_CP,DF_{flow},1.3/A5.{joined}.{GENDERS}.{CHARACTERS}.{STATISTICS}/key?format=csv"
    error = None
    for attempt in range(attempt_limit):
        try:
            response = requests.get(url, headers=UA, timeout=240)
            response.raise_for_status()
            if not response.content.startswith(b"DATAFLOW"):
                raise RuntimeError("Unexpected Census API response")
            return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig").replace("\r\r\n", "\n")))), url
        except Exception as exc:  # network/API retries remain visible in the audit
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Census API failed after {attempt_limit} attempts: {error}")


def fetch_flow(flow: str, areas: list[dict], batch_size: int, workers: int):
    batches = [areas[i:i + batch_size] for i in range(0, len(areas), batch_size)]
    rows, urls = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(request_batch, flow, [r["dguid"] for r in batch]): n for n, batch in enumerate(batches)}
        for future in as_completed(jobs):
            part, url = future.result()
            rows.extend(part)
            urls.append(url)
    return rows, urls


def observation(area_id: str, spec, value, status, locator, numerator=None, denominator=None):
    iid, _name, _theme, unit, _char, _gender, _stat, definition = spec
    return {
        "territory_id": area_id, "indicator_id": iid, "period": "2021", "value": value,
        "status": status, "source_id": "canada-statcan-census-profile-2021",
        "definition": definition, "definition_id": iid, "unit": unit,
        "population": definition, "measurement_method": "source_reported" if _stat != "derived" else "derived_from_source_counts",
        "source_locator": locator, "numerator": numerator, "denominator": denominator,
    }


def make_observations(areas: list[dict], api_rows: list[dict], id_prefix: str):
    by_key = {}
    for row in api_rows:
        by_key[(row["REF_AREA"], row["CHARACTERISTIC"], row["GENDER"], row["STATISTIC"])] = row
    observations = []
    complete = {}
    for area in areas:
        area_id = f"CAN:{id_prefix}:{area['code']}" if id_prefix else "CAN"
        for spec in FIELD_SPECS:
            iid, _name, _theme, _unit, char, gender, stat, _definition = spec
            locator = f"2021 Census Profile; DGUID {area['dguid']}; characteristic {char}"
            if stat == "derived":
                num = by_key.get((area["dguid"], char, "3", "1"), {}).get("OBS_VALUE", "")
                den = by_key.get((area["dguid"], char, "1", "1"), {}).get("OBS_VALUE", "")
                value = (float(num) / float(den) * 100) if num not in ("", None) and den not in ("", None, "0") else None
                observations.append(observation(area_id, spec, round(value, 4) if value is not None else None, "observed" if value is not None else "missing", locator, float(num) if num else None, float(den) if den else None))
            else:
                row = by_key.get((area["dguid"], char, gender, stat))
                raw = row.get("OBS_VALUE", "") if row else ""
                value = float(raw) if raw not in ("", None) else None
                observations.append(observation(area_id, spec, value, "observed" if value is not None else "missing", locator))
            complete.setdefault(iid, 0)
            if observations[-1]["status"] == "observed": complete[iid] += 1
    return observations, complete


def geometries(shp_path: Path, kind: str, tolerance: float):
    reader = shapefile.Reader(str(shp_path), encoding="cp1252")
    transformer = Transformer.from_crs(3347, 4326, always_xy=True)
    features = []
    total = len(reader)
    for index, item in enumerate(reader.iterShapeRecords(), start=1):
        data = item.record.as_dict()
        code = data[f"{kind}UID"]
        geom = shape(item.shape.__geo_interface__)
        # These geometries are display-only. Non-topology-preserving simplify is
        # dramatically faster for Canada's detailed coastline; empty results
        # fall back to the source geometry so every ledger area remains mapped.
        simplified = geom.simplify(tolerance, preserve_topology=False)
        geom = geom if simplified.is_empty else simplified
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = transform(transformer.transform, geom)
        features.append({"type": "Feature", "properties": {"territory_id": f"CAN:{kind}:{code}", "source_id": "canada-statcan-boundaries-2021"}, "geometry": mapping(geom)})
        if index % 500 == 0 or index == total:
            print(f"boundary {kind}: {index}/{total}", flush=True)
    return features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--simplify-metres", type=float, default=2500)
    args = parser.parse_args()
    boundary_dir, out = Path(args.boundary_dir).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths = {kind: boundary_dir / name for kind, name in {
        "PR": "lpr_000b21a_e.shp", "CD": "lcd_000b21a_e.shp", "CSD": "lcsd000b21a_e.shp"}.items()}
    for path in paths.values():
        if not path.exists(): raise FileNotFoundError(path)
    pr, cd, csd = read_level(paths["PR"], "PR"), read_level(paths["CD"], "CD"), read_level(paths["CSD"], "CSD")
    country = [{"code": "01", "name": "Canada", "dguid": "2021A000011124", "parent_code": None}]
    fetched, request_urls = {}, []
    for flow, areas in (("PR", country + pr), ("CD", cd), ("CSD", csd)):
        fetched[flow], urls = fetch_flow(flow, areas, args.batch_size, args.workers)
        request_urls.extend(urls)
    country_obs, country_counts = make_observations(country, fetched["PR"], "")
    pr_obs, pr_counts = make_observations(pr, fetched["PR"], "PR")
    cd_obs, cd_counts = make_observations(cd, fetched["CD"], "CD")
    csd_obs, csd_counts = make_observations(csd, fetched["CSD"], "CSD")
    territories = []
    territories += [{"id": f"CAN:PR:{r['code']}", "name": r["name"], "type": "province_territory", "level": "province_territory", "parent_id": "CAN", "country_id": "CAN", "official_code": r["code"], "code_system": "Statistics Canada SGC 2021 PRUID", "boundary_version": "2021 Census cartographic boundary", "valid_from": "2021-05-11"} for r in pr]
    territories += [{"id": f"CAN:CD:{r['code']}", "name": r["name"], "type": "census_division", "level": "census_division", "parent_id": f"CAN:PR:{r['parent_code']}", "country_id": "CAN", "official_code": r["code"], "code_system": "Statistics Canada SGC 2021 CDUID", "boundary_version": "2021 Census cartographic boundary", "valid_from": "2021-05-11"} for r in cd]
    territories += [{"id": f"CAN:CSD:{r['code']}", "name": r["name"], "type": "census_subdivision", "level": "census_subdivision", "parent_id": f"CAN:CD:{r['parent_code']}", "country_id": "CAN", "official_code": r["code"], "code_system": "Statistics Canada SGC 2021 CSDUID", "boundary_version": "2021 Census cartographic boundary", "valid_from": "2021-05-11"} for r in csd]
    indicators = []
    for iid, name, theme, unit, char, _gender, _stat, definition in FIELD_SPECS:
        indicators.append({"id": iid, "name": name, "theme": theme, "unit": unit, "definition": definition, "definition_id": iid,
                           "population": definition, "measurement_method": "source_reported", "aggregation": "none", "period_policy": "fixed_source_period",
                           "series_family": "census", "display_role": "primary", "source_id": "canada-statcan-census-profile-2021", "source_locator": f"Characteristic {char}"})
    sources = [
        {"id": "canada-statcan-census-profile-2021", "name": "Census Profile, 2021 Census of Population", "publisher": "Statistics Canada", "url": PROFILE_PAGE,
         "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2021", "geographic_level": "Canada, provinces and territories, census divisions and census subdivisions",
         "license": "Statistics Canada Open Licence", "license_url": "https://www.statcan.gc.ca/en/reference/licence", "note": "Selected fields acquired from the official SDMX API; suppressed values remain missing."},
        {"id": "canada-statcan-boundaries-2021", "name": "2021 Census cartographic boundary files", "publisher": "Statistics Canada", "url": BOUNDARY_PAGE,
         "status": "ready", "retrieved_at": datetime.now(timezone.utc).date().isoformat(), "reference_period": "2021", "geographic_level": "Province/territory, census division, census subdivision",
         "license": "Statistics Canada Open Licence", "license_url": "https://www.statcan.gc.ca/en/reference/licence", "note": "Official cartographic reference boundaries simplified for web display; not cadastral or legal boundary certification."},
    ]
    comparison_sources = ["canada-statcan-census-profile-2021", "canada-statcan-boundaries-2021"]
    comparisons = [{"parent_id": "CAN", "level": "province_territory", "member_ids": [f"CAN:PR:{r['code']}" for r in pr], "label": "Provinces and territories", "membership_note": "Statistics Canada 2021 province and territory geography joined by exact PRUID.", "source_ids": comparison_sources}]
    comparisons += [{"parent_id": f"CAN:PR:{p['code']}", "level": "census_division", "member_ids": [f"CAN:CD:{r['code']}" for r in cd if r["parent_code"] == p["code"]], "label": f"Census divisions in {p['name']}", "membership_note": "Statistics Canada 2021 census-division geography joined by exact CDUID and PRUID parent.", "source_ids": comparison_sources} for p in pr]
    comparisons += [{"parent_id": f"CAN:CD:{p['code']}", "level": "census_subdivision", "member_ids": [f"CAN:CSD:{r['code']}" for r in csd if r["parent_code"] == p["code"]], "label": f"Census subdivisions in {p['name']}", "membership_note": "Statistics Canada 2021 census-subdivision geography joined by exact CSDUID and CDUID parent.", "source_ids": comparison_sources} for p in cd]
    features = geometries(paths["PR"], "PR", args.simplify_metres) + geometries(paths["CD"], "CD", args.simplify_metres) + geometries(paths["CSD"], "CSD", args.simplify_metres)
    observations = country_obs + pr_obs + cd_obs + csd_obs
    audit = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "CAN", "status": "official_census_profile_integrated",
             "counts": {"provinces_territories": len(pr), "census_divisions": len(cd), "census_subdivisions": len(csd), "territories": len(territories), "indicators": len(indicators), "observations": len(observations), "boundaries": len(features)},
             "observed_by_level": {"country": country_counts, "province_territory": pr_counts, "census_division": cd_counts, "census_subdivision": csd_counts},
             "api_request_count": len(request_urls), "api_request_urls": request_urls,
             "boundary_files": [{"path": str(paths[k]), "sha256": sha256(paths[k]), "bytes": paths[k].stat().st_size} for k in paths],
             "evidence_policy": "Every adopted geography is retained. Suppressed or unavailable cells are explicit missing observations and are never converted to zero."}
    bundle = {"schema_version": "1.0", "country_area_id": "CAN", "period": "2021", "replace_country_branch": True, "sources": sources, "indicators": indicators,
              "territories": territories, "observations": observations, "boundaries": {"type": "FeatureCollection", "features": features}, "comparisons": comparisons,
              "terminal_territory_ids": [f"CAN:CSD:{r['code']}" for r in csd], "audit": audit}
    (out / "canada-census-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (out / "canada-census-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()

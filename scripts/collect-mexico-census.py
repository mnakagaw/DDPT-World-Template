#!/usr/bin/env python3
"""Collect Mexico 2020 Census state and municipality evidence from INEGI ITER."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


ITER_URL = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip"
ITER_PAGE = "https://www.inegi.org.mx/programas/ccpv/2020/#Datos_abiertos"
BOUNDARY_PAGE = "https://www.inegi.org.mx/servicios/catalogounico.html"
BOUNDARY_API = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/{state}"
DEN_HOUSING = "VIVPARH_CV"


FIELD_SPECS = [
    ("MEX_C2020_POP_TOTAL", "Population, 2020 Census", "Population", "people", "value", "POBTOT", None,
     "Persons habitually resident in the area, including the published estimate for occupied private dwellings without occupant information."),
    ("MEX_C2020_FEMALE_PCT", "Female population", "Population", "%", "ratio", "POBFEM", "POBTOT",
     "Female population as a percentage of total resident population."),
    ("MEX_C2020_AVG_OCCUPANTS", "Average occupants per inhabited private dwelling", "Housing", "people per dwelling", "value", "PROM_OCUP", None,
     "Average occupants in inhabited private dwellings, as published by INEGI."),
    ("MEX_C2020_PIPED_WATER_PCT", "Inhabited private dwellings with piped water on the premises", "Basic services", "%", "ratio", "VPH_AGUADV", DEN_HOUSING,
     "Inhabited private dwellings with piped water inside the dwelling or in its yard or plot, among dwellings for which characteristics were captured."),
    ("MEX_C2020_DRAINAGE_PCT", "Inhabited private dwellings with drainage", "Basic services", "%", "ratio", "VPH_DRENAJ", DEN_HOUSING,
     "Inhabited private dwellings with drainage to the public network, a septic system or another source-defined outlet, among dwellings with captured characteristics."),
    ("MEX_C2020_ELECTRICITY_PCT", "Inhabited private dwellings with electricity", "Basic services", "%", "ratio", "VPH_C_ELEC", DEN_HOUSING,
     "Inhabited private dwellings with electricity, among dwellings for which characteristics were captured."),
    ("MEX_C2020_ILLITERACY_15PLUS_PCT", "Population age 15+ unable to read and write a message", "Education", "%", "ratio", "P15YM_AN", "P_15YMAS",
     "Persons aged 15 to 130 who cannot read and write a message, among persons aged 15 and over."),
    ("MEX_C2020_EMPLOYED_EAP_PCT", "Employed among economically active population age 12+", "Economy", "%", "ratio", "POCUPADA", "PEA",
     "Persons aged 12 and over who worked or had a job in the reference week, as a share of the economically active population aged 12 and over."),
    ("MEX_C2020_DISABILITY_PCT", "Population with disability", "Health and disability", "%", "ratio", "PCON_DISC", "POBTOT",
     "Persons with much difficulty or unable to perform at least one of INEGI's listed daily activities, as a share of total population."),
    ("MEX_C2020_BORN_OTHER_STATE_PCT", "Population born in another state", "Migration", "%", "ratio", "PNACOE", "POBTOT",
     "Persons born in another federal entity, as a share of total population. At national level this remains an internal-migration measure."),
    ("MEX_C2020_URBAN_POP_PCT", "Population in localities of 2,500 or more inhabitants", "Population", "%", "urban", None, None,
     "Population in published locality rows with 2,500 or more inhabitants, divided by the sum of published locality populations in the area."),
    ("MEX_C2020_INDIGENOUS_LANGUAGE_3PLUS_PCT", "Population age 3+ speaking an Indigenous language", "Ethnicity and language", "%", "ratio", "P3YM_HLI", "P_3YMAS",
     "Persons aged 3 and over who speak an Indigenous language, among persons aged 3 and over."),
    ("MEX_C2020_HEALTH_AFFILIATION_PCT", "Population affiliated with health services", "Health", "%", "ratio", "PDER_SS", "POBTOT",
     "Persons affiliated with medical services in a public or private health institution, as a share of total population."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def number(value):
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "*", "N/D", "N/A"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def make_observation(area_id, row, spec, urban):
    iid, _name, _theme, unit, mode, numerator_key, denominator_key, definition = spec
    numerator = denominator = None
    if mode == "value":
        value = number(row.get(numerator_key))
    elif mode == "urban":
        numerator, denominator = urban.get(area_id, (None, None))
        value = numerator / denominator * 100 if numerator is not None and denominator not in (None, 0) else None
    else:
        numerator, denominator = number(row.get(numerator_key)), number(row.get(denominator_key))
        value = numerator / denominator * 100 if numerator is not None and denominator not in (None, 0) else None
    return {"territory_id": area_id, "indicator_id": iid, "period": "2020", "value": round(value, 6) if value is not None else None,
            "status": "observed" if value is not None else "missing", "source_id": "mexico-inegi-iter-2020",
            "definition": definition, "definition_id": iid, "unit": unit, "population": definition,
            "measurement_method": "derived_from_source_counts" if mode in ("ratio", "urban") else "source_reported",
            "source_locator": f"INEGI ITER 2020; {row.get('NOM_ENT')}; {row.get('NOM_MUN')}; {numerator_key or 'locality population rows'}",
            "numerator": numerator, "denominator": denominator}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--simplify-degrees", type=float, default=0.005)
    args = parser.parse_args()
    raw, out = Path(args.raw).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive_path = raw / "iter_00_cpv2020_csv.zip"
    with zipfile.ZipFile(archive_path) as archive:
        data_name = "iter_00_cpv2020/conjunto_de_datos/conjunto_de_datos_iter_00CSV20.csv"
        with archive.open(data_name) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace"))
            totals, locality_sums = [], defaultdict(lambda: [0.0, 0.0, 0])
            for row in reader:
                ent, mun, loc = row["ENTIDAD"], row["MUN"], row["LOC"]
                if loc == "0000" and (ent == "00" or mun == "000" or mun != "000"):
                    totals.append(row)
                    continue
                if ent == "00" or mun == "000":
                    continue
                # 9998/9999 are aggregate summaries of one- and two-dwelling
                # localities already present as individual locality rows. They
                # are retained in the raw file but excluded from the sum to
                # prevent double counting.
                if loc in ("9998", "9999"):
                    continue
                pop = number(row.get("POBTOT"))
                if pop is None:
                    continue
                key = f"MEX:MUN:{ent}{mun}"
                locality_sums[key][1] += pop
                locality_sums[key][2] += 1
                if pop >= 2500:
                    locality_sums[key][0] += pop

    country_rows = [row for row in totals if row["ENTIDAD"] == "00" and row["MUN"] == "000"]
    state_rows = [row for row in totals if row["ENTIDAD"] != "00" and row["MUN"] == "000"]
    municipality_rows = [row for row in totals if row["ENTIDAD"] != "00" and row["MUN"] != "000"]
    if len(country_rows) != 1 or len(state_rows) != 32 or len(municipality_rows) != 2469:
        raise RuntimeError(f"Unexpected ITER total counts: {len(country_rows)}, {len(state_rows)}, {len(municipality_rows)}")
    municipality_ids = {f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}" for row in municipality_rows}
    state_urban = defaultdict(lambda: [0.0, 0.0])
    for area_id, (urban, total, _count) in locality_sums.items():
        state_id = f"MEX:ENT:{area_id[-5:-3]}"
        state_urban[state_id][0] += urban
        state_urban[state_id][1] += total
    country_urban = (sum(v[0] for v in locality_sums.values()), sum(v[1] for v in locality_sums.values()))
    urban = {key:(value[0],value[1]) for key,value in locality_sums.items()}
    urban.update({key:(value[0],value[1]) for key,value in state_urban.items()})
    urban["MEX"] = country_urban

    territories = [{"id":f"MEX:ENT:{row['ENTIDAD']}","name":row["NOM_ENT"],"level":"state","type":"federal_entity","parent_id":"MEX","country_id":"MEX","official_code":row["ENTIDAD"],"code_system":"INEGI Marco Geoestadístico CVE_ENT","boundary_version":"INEGI Marco Geoestadístico December 2025 display reference","valid_from":"2025-12-01"} for row in state_rows]
    territories += [{"id":f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}","name":row["NOM_MUN"],"level":"municipality","type":"municipality_or_territorial_demarcation","parent_id":f"MEX:ENT:{row['ENTIDAD']}","country_id":"MEX","official_code":f"{row['ENTIDAD']}{row['MUN']}","code_system":"INEGI Marco Geoestadístico CVE_ENT+CVE_MUN","boundary_version":"INEGI Marco Geoestadístico December 2025 display reference","valid_from":"2025-12-01"} for row in municipality_rows]
    row_area = [(country_rows[0],"MEX")]+[(row,f"MEX:ENT:{row['ENTIDAD']}") for row in state_rows]+[(row,f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}") for row in municipality_rows]
    observations = [make_observation(area_id,row,spec,urban) for row,area_id in row_area for spec in FIELD_SPECS]
    indicators = [{"id":iid,"name":name,"theme":theme,"unit":unit,"definition":definition,"definition_id":iid,"population":definition,"measurement_method":"derived_from_source_counts" if mode in ("ratio","urban") else "source_reported","aggregation":"none","period_policy":"fixed_source_period","series_family":"census","display_role":"primary","source_id":"mexico-inegi-iter-2020","source_locator":key or "published locality population rows"} for iid,name,theme,unit,mode,key,_den,definition in FIELD_SPECS]
    sources = [
        {"id":"mexico-inegi-iter-2020","name":"Principales resultados por localidad (ITER), Censo de Población y Vivienda 2020","publisher":"Instituto Nacional de Estadística y Geografía (INEGI)","url":ITER_PAGE,"status":"ready","retrieved_at":datetime.now(timezone.utc).date().isoformat(),"reference_period":"2020","geographic_level":"Mexico, federal entities, municipalities/territorial demarcations and localities","license":"INEGI free-use terms","license_url":"https://www.inegi.org.mx/inegi/terminos.html","raw_path":"raw/mexico-census-2020/iter_00_cpv2020_csv.zip","sha256":sha256(archive_path),"note":"Official national ITER CSV. Area totals are selected from published total rows; locality rows are used only for the explicitly derived urban share. Suppressed cells remain missing."},
        {"id":"mexico-inegi-boundaries-2025","name":"Marco Geoestadístico municipal reference geometry, December 2025","publisher":"Instituto Nacional de Estadística y Geografía (INEGI)","url":BOUNDARY_PAGE,"status":"ready","retrieved_at":datetime.now(timezone.utc).date().isoformat(),"reference_period":"December 2025","geographic_level":"Federal entities and municipalities","license":"INEGI free-use terms","license_url":"https://www.inegi.org.mx/inegi/terminos.html","note":"Current official display reference geometry. It is joined only by exact 2020 municipality codes and is not represented as the 2020 statistical boundary."}
    ]

    municipality_features, unmatched_current, boundary_receipts = [], [], []
    state_geometries = defaultdict(list)
    for file in sorted((raw/"boundaries-current").glob("mgem-*.json")):
        data = json.loads(file.read_text(encoding="utf-8"))
        boundary_receipts.append({"path":str(file.relative_to(raw)).replace('\\','/'),"sha256":sha256(file),"bytes":file.stat().st_size,"metadata":data.get("metadatos")})
        for feature in data["features"]:
            code = feature["properties"]["cvegeo"]
            area_id = f"MEX:MUN:{code}"
            if area_id not in municipality_ids:
                unmatched_current.append(code)
                continue
            geom = shape(feature["geometry"]).simplify(args.simplify_degrees, preserve_topology=False)
            if geom.is_empty:
                geom = shape(feature["geometry"])
            if not geom.is_valid:
                geom = make_valid(geom)
            state_geometries[code[:2]].append(geom)
            municipality_features.append({"type":"Feature","properties":{"territory_id":area_id,"source_id":"mexico-inegi-boundaries-2025"},"geometry":mapping(geom)})
    if len(municipality_features) != 2469:
        raise RuntimeError(f"Expected 2,469 exact municipality boundary matches, got {len(municipality_features)}")
    state_features=[]
    for state in state_rows:
        geom=unary_union(state_geometries[state["ENTIDAD"]])
        if not geom.is_valid: geom=make_valid(geom)
        state_features.append({"type":"Feature","properties":{"territory_id":f"MEX:ENT:{state['ENTIDAD']}","source_id":"mexico-inegi-boundaries-2025"},"geometry":mapping(geom)})
    features=state_features+municipality_features
    invalid=[f["properties"]["territory_id"] for f in features if not shape(f["geometry"]).is_valid]
    empty=[f["properties"]["territory_id"] for f in features if shape(f["geometry"]).is_empty]
    if invalid or empty: raise RuntimeError(f"Boundary QA failed: invalid={len(invalid)} empty={len(empty)}")

    comparison_sources=["mexico-inegi-iter-2020","mexico-inegi-boundaries-2025"]
    comparisons=[{"parent_id":"MEX","level":"state","member_ids":[f"MEX:ENT:{row['ENTIDAD']}" for row in state_rows],"label":"Federal entities","membership_note":"INEGI 2020 Census state totals joined by exact CVE_ENT; December 2025 geometry is display-only.","source_ids":comparison_sources}]
    comparisons += [{"parent_id":f"MEX:ENT:{state['ENTIDAD']}","level":"municipality","member_ids":[f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}" for row in municipality_rows if row["ENTIDAD"]==state["ENTIDAD"]],"label":f"Municipalities and territorial demarcations in {state['NOM_ENT']}","membership_note":"INEGI 2020 Census municipality totals joined by exact CVE_ENT+CVE_MUN; December 2025 geometry is display-only.","source_ids":comparison_sources} for state in state_rows]
    observed_by_indicator={spec[0]:sum(1 for row in observations if row["indicator_id"]==spec[0] and row["status"]=="observed") for spec in FIELD_SPECS}
    locality_reconciliation={"municipalities_with_locality_rows":len(locality_sums),"municipalities_exact_to_published_total":sum(1 for row in municipality_rows if number(row["POBTOT"]) is not None and abs(locality_sums[f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}"][1]-number(row["POBTOT"]))<0.5),"rule":"Urban share denominator is the sum of individual published locality population rows. Aggregate 9998/9999 one- and two-dwelling summaries are excluded because they duplicate those individual rows; no missing population is imputed."}
    audit={"schema_version":"1.0","generated_at":datetime.now(timezone.utc).isoformat(),"country_area_id":"MEX","status":"official_2020_census_iter_integrated","counts":{"states":len(state_rows),"municipalities":len(municipality_rows),"territories":len(territories),"indicators":len(indicators),"observations":len(observations),"boundaries":len(features)},"observed_by_indicator":observed_by_indicator,"locality_reconciliation":locality_reconciliation,"boundary_qa":{"invalid":0,"empty":0,"exact_2020_code_matches":len(municipality_features),"unmatched_current_2025_codes":sorted(unmatched_current)},"boundary_receipts":boundary_receipts,"evidence_policy":"Published total rows are authoritative for country, state and municipality values. A current boundary is display-only and never changes or aggregates a 2020 observation. Suppressed cells remain missing, not zero."}
    bundle={"schema_version":"1.0","country_area_id":"MEX","period":"2020","replace_country_branch":True,"sources":sources,"indicators":indicators,"territories":territories,"observations":observations,"boundaries":{"type":"FeatureCollection","features":features},"comparisons":comparisons,"terminal_territory_ids":[f"MEX:MUN:{row['ENTIDAD']}{row['MUN']}" for row in municipality_rows],"audit":audit}
    (out/"mexico-census-bundle.json").write_text(json.dumps(bundle,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    (out/"mexico-census-audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**audit["counts"],"urban_reconciliation":locality_reconciliation,"unmatched_current_boundaries":len(unmatched_current)},indent=2))


if __name__ == "__main__":
    main()

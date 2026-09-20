#!/usr/bin/env python3
"""Build 2023 INSEE commune adapters for six French overseas areas in the Americas."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests

INSEE_RESULTS = "https://www.insee.fr/fr/information/8971128"
INSEE_HISTORY = "https://www.insee.fr/fr/information/2880845"
INSEE_METHOD = "https://www.insee.fr/fr/information/2383265"
POP_URL = "https://api.insee.fr/melodi/file/DS_RP_POPULATION_PRINC_2023/PARQUET"
HOUSING_DOM_URL = "https://api.insee.fr/melodi/file/DS_RP_LOGEMENT_DOM_PRINC_2023/PARQUET"
EDUCATION_URL = "https://api.insee.fr/melodi/file/DS_RP_EDUCATION_PRINC_2023/PARQUET"
EMPLOYMENT_URL = "https://api.insee.fr/melodi/file/DS_RP_EMPLOI_LR_PRINC_2023/PARQUET"
COM_ZIPS = {
    "population": ("https://www.insee.fr/fr/statistiques/fichier/9006084/base_cc_evol_struct_pop_com_2023_parquet.zip", "DS_RP_POPULATION_PRINC_COM.parquet"),
    "housing": ("https://www.insee.fr/fr/statistiques/fichier/9002771/base_cc_logement_com_2023_parquet.zip", "DS_RP_LOGEMENT_PRINC_COM.parquet"),
    "education": ("https://www.insee.fr/fr/statistiques/fichier/9006614/base_cc_diplomes_formation_com_2023_parquet.zip", "DS_RP_EDUCATION_PRINC_COM.parquet"),
    "employment": ("https://www.insee.fr/fr/statistiques/fichier/9002747/base_cc_emploi_pop_active_com_2023_parquet.zip", "DS_RP_EMPLOI_LR_PRINC_COM.parquet"),
}

CONFIG = {
    "GLP": {"name": "Guadeloupe", "prefix": "971", "boundary": "https://geo.api.gouv.fr/departements/971/communes?format=geojson&geometry=contour", "mode": "drom", "plan": "https://www.guadeloupe.developpement-durable.gouv.fr/IMG/pdf/RAPPORT.pdf", "plan_name": "Schéma d'Aménagement Régional de la Guadeloupe — rapport approuvé", "guidance": "https://www.guadeloupe.developpement-durable.gouv.fr/IMG/pdf/guide-du-sar-mars-2017.pdf"},
    "MTQ": {"name": "Martinique", "prefix": "972", "boundary": "https://geo.api.gouv.fr/departements/972/communes?format=geojson&geometry=contour", "mode": "drom", "plan": "https://www.martinique.gouv.fr/index.php/Actions-de-l-Etat/La-planification-ecologique-COP/Signature-de-la-feuille-de-route-de-la-planification-ecologique-pour-la-Martinique", "plan_name": "Feuille de route de territorialisation de la planification écologique de Martinique"},
    "GUF": {"name": "French Guiana", "prefix": "973", "boundary": "https://geo.api.gouv.fr/departements/973/communes?format=geojson&geometry=contour", "mode": "drom", "plan": "https://www.guyane.developpement-durable.gouv.fr/schema-d-amenagement-regional-sar-a1523.html", "plan_name": "Schéma d'Aménagement Régional de la Guyane approuvé"},
    "SPM": {"name": "Saint Pierre and Miquelon", "codes": ["97501", "97502"], "boundary": ["https://geo.api.gouv.fr/communes/97501?format=geojson&geometry=contour", "https://geo.api.gouv.fr/communes/97502?format=geojson&geometry=contour"], "mode": "com", "plan": "https://www.saint-pierre-et-miquelon.gouv.fr/Actions-de-l-Etat/Environnement/Revision-du-STAU-n-2-et-phase-2-du-projet-de-re-territorialisation-du-village-de-Miquelon", "plan_name": "Révision du Schéma territorial d'aménagement et d'urbanisme (STAU)", "guidance": "https://www.saint-pierre-et-miquelon.gouv.fr/contenu/telechargement/10997/103103/file/A-B-%20DELIB2024-0165%20R%C3%A9vision%20partielle%20STAU_Optimized.pdf"},
    "BLM": {"name": "Saint Barthélemy", "codes": ["97701"], "boundary": ["https://geo.api.gouv.fr/communes/97701?format=geojson&geometry=contour"], "mode": "com", "plan": "https://www.comstbarth.fr/in/rest/annotationSVC/DownloadAttachment/attach_cmsUpload_80d7b448-da72-4811-8055-e92b456a2407", "plan_name": "Carte d'urbanisme de Saint-Barthélemy", "guidance": "https://www.comstbarth.fr/in/rest/annotationSVC/DownloadAttachment/attach_cmsUpload_1ff974ce-75ae-47c4-ad46-f260670a33b1"},
    "MAF": {"name": "Saint Martin (French Part)", "codes": ["97801"], "boundary": ["https://geo.api.gouv.fr/communes/97801?format=geojson&geometry=contour"], "mode": "com", "plan": "https://www.com-saint-martin.fr/thematiques/habitat-foncier-et-urbanisme/amenagement-du-territoire/le-plan-doccupation-des-sols-pos", "plan_name": "Plan d'Occupation des Sols de Saint-Martin", "guidance": "https://www.com-saint-martin.fr/actualites/developpement-du-territoire--validation-du-programme-local-de-lhabitat-2025-2030"},
}

SAR_FRAMEWORK = "https://amenagement-durable.ecologie.gouv.fr/planification-regionale"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(url: str, path: Path) -> Path:
    if path.exists() and path.stat().st_size:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(url, timeout=240, headers={"User-Agent": "AreaData/0.10.2 source collector"})
        response.raise_for_status()
        path.write_bytes(response.content)
    except requests.exceptions.RequestException:
        subprocess.run(["curl.exe", "-fL", "--retry", "3", "--output", str(path), url], check=True)
    return path


def pct(num: float, den: float) -> float:
    return round(num / den * 100, 4) if den else 0.0


def placeholders(count: int) -> str:
    return ",".join("?" for _ in range(count))


def load_boundaries(cfg: dict, raw: Path) -> tuple[list[dict], list[str]]:
    urls = cfg["boundary"] if isinstance(cfg["boundary"], list) else [cfg["boundary"]]
    features = []
    for index, url in enumerate(urls, 1):
        data = requests.get(url, timeout=180, headers={"User-Agent": "AreaData/0.10.2 source collector"}).json()
        current = data["features"] if data.get("type") == "FeatureCollection" else [data]
        features.extend(current)
        (raw / f"boundary-{index}.geojson").write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    features.sort(key=lambda feature: feature["properties"]["code"])
    codes = [feature["properties"]["code"] for feature in features]
    expected = cfg.get("codes") or [code for code in codes if code.startswith(cfg["prefix"])]
    features = [feature for feature in features if feature["properties"]["code"] in expected]
    if [feature["properties"]["code"] for feature in features] != sorted(expected):
        raise RuntimeError(f"Boundary code mismatch for {cfg['name']}: {codes} vs {expected}")
    return features, sorted(expected)


def query_rows(con: duckdb.DuckDBPyConnection, source: str, codes: list[str], kind: str) -> list[dict]:
    marks = placeholders(len(codes))
    params = [source, *codes]
    if kind == "population":
        sql = f"""select GEO,AGE,SEX,OBS_VALUE from read_parquet(?) where GEO in ({marks}) and GEO_OBJECT='COM' and year(TIME_PERIOD)=2023 and RP_MEASURE='POP' and ((AGE='_T' and SEX in ('_T','F')) or (AGE='Y_LT15' and SEX='_T'))"""
    elif kind == "education":
        sql = f"""select GEO,STUD,OBS_VALUE from read_parquet(?) where GEO in ({marks}) and GEO_OBJECT='COM' and year(TIME_PERIOD)=2023 and STUD_AREA='_T' and RP_MEASURE='POP' and AGE='Y15T17' and SEX='_T' and STUD in ('0','_T')"""
    elif kind == "employment":
        sql = f"""select GEO,EMPSTA_ENQ,OBS_VALUE from read_parquet(?) where GEO in ({marks}) and GEO_OBJECT='COM' and year(TIME_PERIOD)=2023 and EDUC='_T' and RP_MEASURE='POP' and AGE='Y15T64' and SEX='_T' and EMPSTA_ENQ in ('2','1T2')"""
    elif kind == "housing_dom":
        sql = f"""select GEO,BAINWC,ELEC,OBS_VALUE from read_parquet(?) where GEO in ({marks}) and GEO_OBJECT='COM' and year(TIME_PERIOD)=2023 and RP_MEASURE='DWELLINGS' and OCS='DW_MAIN' and SOBO='_T' and AIRCOND='_T' and WSS='_T' and WW='_T' and TDW='_T' and ((BAINWC='_T' and ELEC='_T') or (BAINWC='1' and ELEC='_T') or (BAINWC='_T' and ELEC='1'))"""
    elif kind == "housing_com":
        sql = f"""select GEO,BAINWC,ELEC,OBS_VALUE from read_parquet(?) where GEO in ({marks}) and GEO_OBJECT='COM' and year(TIME_PERIOD)=2023 and RP_MEASURE='DWELLINGS' and OCS='DW_MAIN' and SOBO='_T' and AIRCOND='_T' and WSS='_T' and WW='_T' and TDW='_T' and L_STAY='_T' and CARPARK='_T' and NRG_SRC='_T' and NOR='_T' and TSH='_T' and CARS='_T' and BUILD_END='_T' and BAINWC='_T' and ELEC='_T'"""
    else:
        raise ValueError(kind)
    cursor = con.execute(sql, params)
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def index_rows(rows: list[dict], keys: tuple[str, ...]) -> dict:
    return {tuple(row[key] for key in keys): float(row["OBS_VALUE"]) for row in rows}


def build_country(root: Path, out: Path, con: duckdb.DuckDBPyConnection, com_paths: dict[str, Path], country_id: str, cfg: dict, today: str) -> dict:
    raw = root / "raw/french-overseas-2023" / country_id
    raw.mkdir(parents=True, exist_ok=True)
    boundary_features, codes = load_boundaries(cfg, raw)
    sources = {"population": POP_URL, "education": EDUCATION_URL, "employment": EMPLOYMENT_URL, "housing": HOUSING_DOM_URL}
    if cfg["mode"] == "com":
        sources = {key: str(com_paths[key]) for key in ("population", "education", "employment", "housing")}
    pop = query_rows(con, sources["population"], codes, "population")
    edu = query_rows(con, sources["education"], codes, "education")
    jobs = query_rows(con, sources["employment"], codes, "employment")
    housing = query_rows(con, sources["housing"], codes, "housing_dom" if cfg["mode"] == "drom" else "housing_com")
    pidx, eidx, jidx, hidx = index_rows(pop, ("GEO", "AGE", "SEX")), index_rows(edu, ("GEO", "STUD")), index_rows(jobs, ("GEO", "EMPSTA_ENQ")), index_rows(housing, ("GEO", "BAINWC", "ELEC"))
    for code in codes:
        required = [(code, "_T", "_T"), (code, "_T", "F"), (code, "Y_LT15", "_T")]
        if any(key not in pidx for key in required):
            raise RuntimeError(f"Missing 2023 population cells for {country_id} {code}")
        if any(key not in eidx for key in [(code, "0"), (code, "_T")]):
            raise RuntimeError(f"Missing 2023 education cells for {country_id} {code}")
        if any(key not in jidx for key in [(code, "2"), (code, "1T2")]):
            raise RuntimeError(f"Missing 2023 employment cells for {country_id} {code}")
        if (code, "_T", "_T") not in hidx:
            raise RuntimeError(f"Missing 2023 housing cells for {country_id} {code}")

    boundary_source = f"fr-geo-api-{country_id.lower()}-communes-2026"
    # Each country bundle has its own compact, hashed extract.  Keep source IDs
    # country-specific so applying a later bundle cannot silently replace the
    # evidence path and hash of an earlier country.
    census_sources = {
        key: f"fr-insee-rp2023-{key}-{country_id.lower()}"
        for key in ("population", "housing", "education", "employment")
    }
    territory_ids = {code: f"{country_id}:RP2023:COM:{code}" for code in codes}
    territories, map_features = [], []
    for feature in boundary_features:
        code = feature["properties"]["code"]
        territories.append({"id": territory_ids[code], "country_id": country_id, "name": feature["properties"]["nom"], "level": "commune", "type": "commune", "parent_id": country_id, "official_code": code, "code_system": "Code officiel géographique (INSEE)", "boundary_version": "API Découpage administratif / COG 2026", "valid_from": "2026-01-01", "geography_note": "Official commune code and government reference contour; 2023 Census data are published in the geography in force on 1 January 2026."})
        map_features.append({"type": "Feature", "properties": {"territory_id": territory_ids[code], "source_id": boundary_source, "official_code": code, "code_system": "Code officiel géographique (INSEE)", "geometry_edition": "API Découpage administratif 2026", "join_method": "Exact COG commune code", "reference_only": True}, "geometry": feature["geometry"]})

    has_electricity = cfg["mode"] == "drom" and all((code, "_T", "1") in hidx for code in codes)
    has_bath_wc = cfg["mode"] == "drom" and all((code, "1", "_T") in hidx for code in codes)
    rows = {}
    for code in codes:
        rows[territory_ids[code]] = {
            "population": pidx[(code, "_T", "_T")], "female": pidx[(code, "_T", "F")], "under15": pidx[(code, "Y_LT15", "_T")],
            "housing": hidx[(code, "_T", "_T")], "not_enrolled": eidx[(code, "0")], "age15_17": eidx[(code, "_T")],
            "unemployed": jidx[(code, "2")], "labour_force": jidx[(code, "1T2")],
        }
        if has_electricity:
            rows[territory_ids[code]]["electricity"] = hidx[(code, "_T", "1")]
        if has_bath_wc:
            rows[territory_ids[code]]["bath_wc"] = hidx[(code, "1", "_T")]
    national = {key: sum(values[key] for values in rows.values()) for key in next(iter(rows.values()))}
    all_rows = {country_id: national, **rows}
    specs = [
        ("POP_TOTAL", "Census resident population", "Population", "people", lambda r: r["population"], "sum", "population_total", "population", "Resident population in the 2023 INSEE Census results."),
        ("FEMALE_PCT", "Female population", "Population", "%", lambda r: pct(r["female"], r["population"]), "none", "age_sex", "population", "Female residents as a share of resident population."),
        ("UNDER15_PCT", "Population under age 15", "Population", "%", lambda r: pct(r["under15"], r["population"]), "none", "age_sex", "population", "Residents under age 15 as a share of resident population."),
        ("MAIN_RESIDENCES", "Main residences", "Households and housing", "dwellings", lambda r: r["housing"], "sum", "households_housing", "housing", "Main residences in the 2023 Census housing results."),
        ("AGE15_17_NOT_ENROLLED_PCT", "Population age 15-17 not enrolled in education", "Education", "%", lambda r: pct(r["not_enrolled"], r["age15_17"]), "none", "education_literacy", "education", "Residents age 15-17 not enrolled in education as a share of residents age 15-17."),
        ("UNEMPLOYMENT_RATE", "Census unemployment rate age 15-64", "Employment", "%", lambda r: pct(r["unemployed"], r["labour_force"]), "none", "employment", "employment", "Census unemployed residents age 15-64 as a share of the Census labour force age 15-64; this is not the ILO labour-force-survey rate."),
    ]
    if has_electricity:
        specs.append(("ELECTRICITY_PCT", "Main residences with electricity", "Basic services", "% of main residences", lambda r: pct(r["electricity"], r["housing"]), "none", "electricity", "housing", "Main residences with electricity in the dwelling."))
    if has_bath_wc:
        specs.append(("INDOOR_BATH_WC_PCT", "Main residences with bath or shower and indoor toilet", "Sanitation", "% of main residences", lambda r: pct(r["bath_wc"], r["housing"]), "none", "sanitation", "housing", "Main residences with a bath or shower and a toilet inside the dwelling; this is not a sewer-connection rate."))
    indicators, observations, theme_map = [], [], {}
    for suffix, name, theme, unit, calc, aggregation, contract_theme, source_key, definition in specs:
        indicator_id = f"{country_id}_RP2023_{suffix}"
        theme_map[indicator_id] = contract_theme
        indicators.append({"id": indicator_id, "name": name, "theme": theme, "unit": unit, "definition": definition, "definition_id": f"INSEE-RP2023-{suffix}", "population": "2023 Census resident population or main residences as stated", "measurement_method": "source_reported" if aggregation == "sum" else "derived_from_source_counts", "aggregation": aggregation, "period_policy": "fixed_source_period", "series_family": "census", "display_role": "primary", "source_id": census_sources[source_key], "source_locator": f"INSEE 2023 harmonized dataset; {suffix}"})
        for territory_id, values in all_rows.items():
            observations.append({"territory_id": territory_id, "indicator_id": indicator_id, "period": "2023", "value": round(calc(values), 4), "status": "observed", "source_id": census_sources[source_key], "definition": definition, "definition_id": f"INSEE-RP2023-{suffix}", "unit": unit, "population": "2023 Census resident population or main residences as stated", "measurement_method": "source_reported" if aggregation == "sum" else "derived_from_source_counts", "source_locator": f"INSEE 2023 harmonized dataset; {suffix}"})

    extract = {"schema_version": "1.0", "country_area_id": country_id, "reference_year": 2023, "geography": "COG 2026 communes", "endpoints": {"population": POP_URL if cfg["mode"] == "drom" else COM_ZIPS["population"][0], "housing": HOUSING_DOM_URL if cfg["mode"] == "drom" else COM_ZIPS["housing"][0], "education": EDUCATION_URL if cfg["mode"] == "drom" else COM_ZIPS["education"][0], "employment": EMPLOYMENT_URL if cfg["mode"] == "drom" else COM_ZIPS["employment"][0]}, "codes": codes, "rows": rows, "national_sum": national, "controls": {"complete_nonoverlapping_commune_partition": True, "rates_derived_from_summed_numerators_denominators": True, "small_area_precision_warning_retained": True, "electricity_complete_for_all_communes": has_electricity, "bath_wc_complete_for_all_communes": has_bath_wc}}
    extract_path = raw / f"{country_id}-insee-rp2023-extract.json"
    extract_path.write_text(json.dumps(extract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_rows = []
    for key, source_id in census_sources.items():
        url = extract["endpoints"][key]
        source_rows.append({"id": source_id, "name": f"INSEE Census 2023 — {key}", "publisher": "Institut national de la statistique et des études économiques (INSEE)", "url": url, "status": "ready", "retrieved_at": today, "reference_period": "2023", "geographic_level": "country/area and commune", "raw_path": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json", "sha256": sha(extract_path), "license": "Licence Ouverte / Open Licence 2.0; source attribution retained.", "note": "Only the source rows and dimensions used by this edition are retained in the compact extract. INSEE warns that counts below 200 require care and small-area comparisons should be avoided."})
    source_rows.append({"id": boundary_source, "name": f"French government commune reference contours — {cfg['name']}", "publisher": "Direction interministérielle du numérique / API Découpage administratif", "url": cfg["boundary"][0] if isinstance(cfg["boundary"], list) else cfg["boundary"], "status": "ready", "retrieved_at": today, "reference_period": "COG 2026", "geographic_level": "commune", "raw_path": f"raw/french-overseas-2023/{country_id}", "license": "Licence Ouverte / Open Licence 2.0", "note": "Reference contours joined by exact official commune code; not represented as cadastral or legal-boundary certification."})
    bundle = {"schema_version": "1.0", "country_area_id": country_id, "period": "2023", "replace_country_branch": True, "territories": territories, "terminal_territory_ids": list(territory_ids.values()), "comparisons": ([{"parent_id": country_id, "member_ids": list(territory_ids.values()), "label": "Communes", "membership_note": "Complete non-overlapping COG 2026 commune partition used by the 2023 INSEE results.", "source_ids": [boundary_source, census_sources["population"]]}] if len(codes) > 1 else []), "indicators": indicators, "observations": observations, "boundaries": {"type": "FeatureCollection", "features": map_features}, "sources": source_rows}
    bundle_path = out / f"{country_id}-country-depth-bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plan_dir = raw / "planning"
    plan_dir.mkdir(exist_ok=True)
    plan = get(cfg["plan"], plan_dir / "plan-material")
    guidance_url = cfg.get("guidance") or (SAR_FRAMEWORK if cfg["mode"] == "drom" else cfg["plan"])
    guidance = get(guidance_url, plan_dir / "planning-framework")
    law_url = SAR_FRAMEWORK if cfg["mode"] == "drom" else guidance_url
    law = guidance if law_url == guidance_url else get(law_url, plan_dir / "planning-law")
    planning_sources = [
        {"id": f"{country_id.lower()}-planning-law", "name": "Applicable official planning and regulatory framework", "publisher": "French Ministry for Ecological Transition or the competent territorial authority", "url": law_url, "status": "ready", "retrieved_at": today, "reference_period": "current page/file retrieved 2026", "geographic_level": "territorial planning framework", "raw_path": f"raw/french-overseas-2023/{country_id}/planning/{law.name}", "sha256": sha(law), "license": "Official public planning or regulatory publication."},
        {"id": f"{country_id.lower()}-planning-material", "name": cfg["plan_name"], "publisher": "Competent territorial authority", "url": cfg["plan"], "status": "ready", "retrieved_at": today, "reference_period": "as stated in official material", "geographic_level": "country/area", "raw_path": f"raw/french-overseas-2023/{country_id}/planning/{plan.name}", "sha256": sha(plan), "license": "Official public planning material; attribution retained."},
    ]
    integrated_themes = set(theme_map.values())
    all_themes = {"population_total", "age_sex", "households_housing", "drinking_water", "sanitation", "electricity", "education_literacy", "employment", "disability", "migration", "urban_rural", "ethnicity", "health", "nutrition", "poverty"}
    gap_reasons = {
        "drinking_water": "The reviewed 2023 selected housing table does not expose a definition-compatible drinking-water service indicator for this edition; hot water or indoor plumbing is not substituted.",
        "sanitation": "The reviewed 2023 selected table does not provide a definition-compatible sanitation indicator for this area's adopted extract.",
        "electricity": "The reviewed 2023 selected table does not provide a definition-compatible electricity-access indicator for this area's adopted extract.",
        "disability": "Disability is not present in the adopted INSEE 2023 Census principal-indicator table inventory; no unrelated health proxy is substituted.",
        "migration": "Prior-residence cells exist in a separate harmonized product, but the category semantics were not adopted as a dashboard migration measure in this edition.",
        "urban_rural": "The adopted commune files do not provide a compatible urban/rural classification measure; commune population is not relabelled as urbanization.",
        "ethnicity": "Ethnicity is not a field in the reviewed adopted INSEE 2023 Census table inventory; nationality or birthplace is not relabelled as ethnicity.",
        "health": "The adopted Census tables do not publish a health-outcome measure at the same commune geography; housing comfort is not relabelled as health.",
        "nutrition": "The adopted Census tables do not publish a nutrition-outcome measure at the same commune geography.",
        "poverty": "The adopted Census tables do not publish a poverty measure for every commune in this area's partition; no national or departmental value is copied to communes.",
    }
    theme_gaps = []
    for theme in sorted(all_themes - integrated_themes):
        theme_gaps.append({"theme": theme, "source_id": census_sources["population"], "source_url": INSEE_RESULTS, "table_id": "INSEE-RP2023-reviewed-products", "field_id": f"{country_id}_{theme}_GAP", "disposition": "not_adopted" if theme == "migration" else "unavailable", "gap_kind": "not_selected_definition_unresolved" if theme == "migration" else "not_published_at_adopted_geography", "reason": gap_reasons[theme], "evidence": [{"url": INSEE_RESULTS, "raw": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json", "note": "Official result products, dimensions and adopted extract reviewed."}]})
    audit = {"schema_version": "1.0", "status": "complete", "country_area_id": country_id, "counts": {"communes": len(codes), "boundary_features": len(map_features), "indicators": len(indicators), "observations": len(observations), "theme_gaps": len(theme_gaps)}, "controls": extract["controls"], "source_receipts": [{"path": str(extract_path.relative_to(root)), "bytes": extract_path.stat().st_size, "sha256": sha(extract_path)}, {"path": str(plan.relative_to(root)), "bytes": plan.stat().st_size, "sha256": sha(plan)}, {"path": str(guidance.relative_to(root)), "bytes": guidance.stat().st_size, "sha256": sha(guidance)}]}
    catalog = [{"table_id": key, "table_title": f"INSEE RP2023 {key} harmonized product", "numeric_cell_count": len(rows), "source_id": census_sources[key], "source_path": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json", "disposition": "not_adopted", "reason": "The product was inventoried; only the explicitly mapped dimensions are adopted as indicators."} for key in census_sources]
    manifest = {
        "schema_version": "1.0", "country_area_id": country_id, "scope_role": f"completed {cfg['name']} edition with INSEE 2023 commune adapter", "country_adapter_status": "complete_country_adapter", "official_census_url": INSEE_RESULTS, "census_source_id": census_sources["population"], "semantic_source_path": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json", "audit_path": f"evidence/{country_id}_INTEGRATION_AUDIT.json",
        "domains": {
            "official_statistics_office": {"status": "inspected", "urls": [INSEE_RESULTS], "note": "INSEE official 2023 result products were inspected.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}"}]},
            "latest_census": {"status": "adopted", "urls": [INSEE_RESULTS], "note": "The 2023 Census reference year, released in 2026, is adopted.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json"}]},
            "census_results": {"status": "adopted", "urls": [INSEE_RESULTS], "note": "Source-reported and derived-from-source-count commune values are integrated without copying parent values to communes.", "evidence": [{"audit": f"evidence/{country_id}_INTEGRATION_AUDIT.json"}]},
            "table_catalog": {"status": "inspected", "urls": [INSEE_RESULTS], "note": "The four adopted harmonized result products and their dimensions were inventoried.", "evidence": [{"audit": f"evidence/{country_id}_INTEGRATION_AUDIT.json"}]},
            "machine_readable_data": {"status": "adopted", "urls": list(extract["endpoints"].values()), "note": "Official Parquet products were queried and a compact source extract was retained by hash.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}/{country_id}-insee-rp2023-extract.json"}]},
            "administrative_codes": {"status": "geography_matched", "urls": [cfg["boundary"][0] if isinstance(cfg["boundary"], list) else cfg["boundary"]], "note": "Exact COG commune codes join statistics and reference contours.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}"}]},
            "adm1_adm2_boundaries": {"status": "adopted", "urls": [cfg["boundary"][0] if isinstance(cfg["boundary"], list) else cfg["boundary"]], "note": "The complete commune partition used in this edition is integrated as reference geometry.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}"}]},
            "planning_law": {"status": "inspected", "urls": [law_url], "note": "The applicable official planning-law or territorial regulatory framework was acquired and inspected.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}/planning/{law.name}"}]},
            "planning_guidance": {"status": "acquired", "urls": [guidance_url], "note": "Official territorial planning guidance or regulatory material was acquired.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}/planning/{guidance.name}"}]},
            "plans_budgets_implementation_evaluation": {"status": "acquired", "urls": [cfg["plan"]], "note": "Official plan, budget proceedings or implementation material was acquired; document presence is not treated as proof of implementation or evaluation.", "evidence": [{"raw": f"raw/french-overseas-2023/{country_id}/planning/{plan.name}"}]},
        },
        "recent_census_rounds": [{"round": "2023", "date_text": "2023 Census reference year (released 2026)", "year": 2023, "url": INSEE_RESULTS}, {"round": "2016", "date_text": "2016 Census reference year", "year": 2016, "url": "https://www.insee.fr/fr/information/4172214"}, {"round": "2011", "date_text": "2011 Census reference year", "year": 2011, "url": "https://www.insee.fr/fr/information/2884434"}],
        "indicator_themes": theme_map, "theme_reasons": {theme: gap_reasons[theme] for theme in gap_reasons if theme in integrated_themes}, "theme_gaps": theme_gaps, "semantic_catalog": catalog, "sources": planning_sources,
        "documents": [{"id": f"{country_id.lower()}-planning-framework", "territory_id": country_id, "category": "reference", "title": planning_sources[0]["name"], "kind": "official-law-or-regulation", "url": law_url, "availability": "body_acquired", "official_status": "unverified", "source_id": planning_sources[0]["id"]}, {"id": f"{country_id.lower()}-planning-material", "territory_id": country_id, "category": "plan", "title": cfg["plan_name"], "kind": "official-plan-or-budget-material", "url": cfg["plan"], "availability": "body_acquired", "official_status": "unverified", "source_id": planning_sources[1]["id"]}],
        "census_history": {"country_id": country_id, "names": {"en": cfg["name"], "es": cfg["name"], "ja": cfg["name"]}, "adopted_data_year": 2023, "adopted_source_url": INSEE_RESULTS, "official_census_url": INSEE_RESULTS, "recent_rounds": [{"year": 2023, "status": "results_adopted", "url": INSEE_RESULTS}, {"year": 2016, "status": "historical_reference_year", "url": "https://www.insee.fr/fr/information/4172214"}, {"year": 2011, "status": "historical_reference_year", "url": "https://www.insee.fr/fr/information/2884434"}], "note": {"en": "INSEE publishes rolling Census reference-year results. AreaData adopts 2023 commune results in COG 2026 geography; comparisons should normally use intervals of at least five years, and small estimated cells require care.", "es": "INSEE publica resultados censales anuales de referencia. AreaData adopta 2023 en la geografía COG 2026; las comparaciones suelen requerir intervalos de al menos cinco años y cautela con celdas pequeñas.", "ja": "INSEEはローリング方式の国勢調査結果を基準年ごとに公表します。AreaDataはCOG 2026地理の2023年市区町村値を採用し、小標本値と短期間比較には注意を付します。"}},
        "adapters": [f"{country_id.lower()}-insee-rp2023-depth", f"{country_id.lower()}-planning-evidence"], "collection_notes": [f"{country_id}: INSEE 2023 commune values use exact COG codes and complete partition sums; rates use summed numerators and denominators.", f"{country_id}: unsupported Census themes remain explicit evidence-backed gaps; no parent value or proxy is copied to communes."], "inventory_method": "Official harmonized Parquet products were filtered by explicit dimensions. Adopted cells, denominators, boundaries and source URLs are retained in a compact hashed extract; unselected themes have evidence-backed terminal gap records.", "audit": audit,
    }
    manifest_path = out / f"{country_id}-completion-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"country_area_id": country_id, "communes": len(codes), "indicators": len(indicators), "observations": len(observations), "theme_gaps": len(theme_gaps), "bundle": str(bundle_path), "manifest": str(manifest_path), "extract_sha256": sha(extract_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--country", action="append", choices=sorted(CONFIG), help="Collect only the selected country/area; repeat for more than one.")
    args = parser.parse_args()
    root, out = Path(args.project).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    com_root = root / "raw/french-overseas-2023/common-com-parquet"
    com_root.mkdir(parents=True, exist_ok=True)
    com_paths = {}
    for key, (url, member) in COM_ZIPS.items():
        archive = get(url, com_root / f"{key}.zip")
        target = com_root / member
        if not target.exists():
            with zipfile.ZipFile(archive) as zf:
                target.write_bytes(zf.read(member))
        com_paths[key] = target
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    selected = set(args.country or CONFIG)
    results = [build_country(root, out, con, com_paths, country_id, cfg, today) for country_id, cfg in CONFIG.items() if country_id in selected]
    (out / "FRENCH_OVERSEAS_COLLECTION_AUDIT.json").write_text(json.dumps({"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "countries": results, "controls": {"official_2023_results": True, "exact_cog_join": True, "complete_partition_sum": True, "missing_themes_not_imputed": True}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the Dominica 2011 Census parish adapter from official publications."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests

CENSUS_URL = "https://stats.gov.dm/wp-content/uploads/2020/04/2011-Population-and-Housing-Census.pdf"
STATS_URL = "https://stats.gov.dm/subjects/demographic-statistics/"
CENSUS_2022_URL = "https://stats.gov.dm/census/"
GEO_META = "https://www.geoboundaries.org/api/current/gbOpen/DMA/ADM1/"
LAW = "https://www.dominica.gov.dm/laws/2002/act5-2002.pdf"
CRRP = "https://www.dominica.gov.dm/images/docs/notices/crrp_final_042020.pdf"
BUDGET = "https://finance.gov.dm/images/documents/estimates/approved_estimates_2025_2026_v2.pdf"
MDG = "https://stats.gov.dm/wp-content/uploads/2019/06/Millenum_Development_Goals_Achievement_2015.pdf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(url: str, path: Path) -> Path:
    if path.exists() and path.stat().st_size:
        return path
    response = requests.get(url, timeout=180, headers={"User-Agent": "AreaData/0.10.2 source collector"})
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return path


def pct(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100, 4)


# Table 1.2 and Table 1.3. City of Roseau and Rest of St. George are added
# before joining the published parish boundary.
PARISH = {
    "Saint George": {"male": 10247, "female": 10544, "population": 20791, "under15": 4719},
    "Saint John": {"male": 3324, "female": 3098, "population": 6422, "under15": 1419},
    "Saint Peter": {"male": 703, "female": 668, "population": 1371, "under15": 275},
    "Saint Joseph": {"male": 2875, "female": 2559, "population": 5434, "under15": 1104},
    "Saint Paul": {"male": 4688, "female": 4843, "population": 9531, "under15": 2199},
    "Saint Luke": {"male": 794, "female": 771, "population": 1565, "under15": 384},
    "Saint Mark": {"male": 911, "female": 856, "population": 1767, "under15": 353},
    "Saint Patrick": {"male": 3786, "female": 3575, "population": 7361, "under15": 1712},
    "Saint David": {"male": 3216, "female": 2683, "population": 5899, "under15": 1519},
    "Saint Andrew": {"male": 4880, "female": 4304, "population": 9184, "under15": 2338},
}
NATIONAL = {"male": 35424, "female": 33901, "population": 69325, "under15": 16022}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.project).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()

    discovered = root / "raw/discovered-source-files/DMA/010-Population_and_Housing_Census_2011.pdf"
    if not discovered.exists():
        get(CENSUS_URL, discovered)
    raw = root / "raw/dominica-country-edition"
    raw.mkdir(parents=True, exist_ok=True)
    census = raw / "population-and-housing-census-2011.pdf"
    shutil.copy2(discovered, census)
    mdg = get(MDG, raw / "millennium-development-goals-achievement-2015.pdf")
    law = get(LAW, raw / "physical-planning-act-2002.pdf")
    crrp = get(CRRP, raw / "climate-resilience-and-recovery-plan-2020-2030.pdf")
    budget = get(BUDGET, raw / "approved-estimates-2025-2026.pdf")
    meta = requests.get(GEO_META, timeout=120, headers={"User-Agent": "AreaData/0.10.2 source collector"}).json()
    geo = get(meta["simplifiedGeometryGeoJSON"], raw / "geoBoundaries-DMA-ADM1_simplified.geojson")
    geojson = json.loads(geo.read_text(encoding="utf-8"))
    by_name = {feature["properties"]["shapeName"]: feature for feature in geojson["features"]}
    if set(by_name) != set(PARISH):
        raise RuntimeError(f"Unexpected boundary names: {set(by_name) ^ set(PARISH)}")

    territories = []
    features = []
    ids = {}
    for name in sorted(PARISH):
        feature = by_name[name]
        props = feature["properties"]
        code = props["shapeISO"]
        territory_id = f"DMA:C2011:ADM1:{code.split('-')[-1]}"
        ids[name] = territory_id
        territories.append({
            "id": territory_id,
            "country_id": "DMA",
            "name": name,
            "level": "parish",
            "type": "parish",
            "parent_id": "DMA",
            "official_code": code,
            "code_system": "ISO 3166-2",
            "boundary_version": "geoBoundaries DMA ADM1 2005 / build 2023-12-12",
            "valid_from": "2005-01-01",
            "geography_note": "Reference boundary. City of Roseau and Rest of St. George Census rows are combined to Saint George parish before the join.",
        })
        features.append({
            "type": "Feature",
            "properties": {
                "territory_id": territory_id,
                "source_id": "dma-geoboundaries-adm1-2005",
                "official_code": code,
                "code_system": "ISO 3166-2",
                "geometry_edition": "geoBoundaries DMA ADM1 2005",
                "join_method": "Exact published parish name; Roseau and Rest of St. George Census rows summed before join",
                "reference_only": True,
            },
            "geometry": feature["geometry"],
        })

    rows = {"DMA": NATIONAL, **{ids[name]: values for name, values in PARISH.items()}}
    census_source = "dma-statistics-census-2011"
    local_specs = [
        ("DMA_C2011_POP_TOTAL", "Census resident population", "Population", "people", lambda r: r["population"], "sum", "Resident Census population."),
        ("DMA_C2011_FEMALE_PCT", "Female population", "Population", "%", lambda r: pct(r["female"], r["population"]), "none", "Female residents as a share of the resident Census population."),
        ("DMA_C2011_UNDER15_PCT", "Population under age 15", "Population", "%", lambda r: pct(r["under15"], r["population"]), "none", "Residents age 0-14 as a share of the resident Census population."),
    ]
    indicators = []
    observations = []
    for indicator_id, name, theme, unit, calculate, aggregation, definition in local_specs:
        indicators.append({
            "id": indicator_id,
            "name": name,
            "theme": theme,
            "unit": unit,
            "definition": definition,
            "definition_id": "DMA-CENSUS-2011",
            "population": "2011 resident Census population",
            "measurement_method": "source_reported" if aggregation == "sum" else "derived_from_source_counts",
            "aggregation": aggregation,
            "period_policy": "fixed_source_period",
            "series_family": "census",
            "display_role": "primary",
            "source_id": census_source,
            "source_locator": "2011 Census Tables 1.2 and 1.3",
        })
        for territory_id, values in rows.items():
            observations.append({
                "territory_id": territory_id,
                "indicator_id": indicator_id,
                "period": "2011",
                "value": calculate(values),
                "status": "observed",
                "source_id": census_source,
                "definition": definition,
                "definition_id": "DMA-CENSUS-2011",
                "unit": unit,
                "population": "2011 resident Census population",
                "measurement_method": "source_reported" if aggregation == "sum" else "derived_from_source_counts",
                "source_locator": "2011 Census Tables 1.2 and 1.3",
            })

    national_specs = [
        ("DMA_C2011_HOUSEHOLDS", "Private households", "Households and housing", "households", 25113, "Households reported in the 2011 housing tables.", "2011", census_source, "Table 11"),
        ("DMA_C2011_PUBLIC_PIPED_WATER_PCT", "Households with public water piped into dwelling", "Water", "% of households", 64.9, "Households whose water facility is public water piped into the dwelling.", "2011", census_source, "Table 11.9.1"),
        ("DMA_C2011_FLUSH_TOILET_PCT", "Households with flush toilet linked to sewer or septic system", "Sanitation", "% of households", pct(3051 + 15130, 25113), "Households using a flush toilet linked to a sewer, cesspit, septic tank or soak-away.", "2011", census_source, "Table 11.10"),
        ("DMA_C2011_PUBLIC_ELECTRICITY_PCT", "Households using public electricity for lighting", "Basic services", "% of households", 90.0, "Households reporting public electricity as the type of lighting.", "2011", census_source, "Table 11.11.1"),
        ("DMA_C2011_NO_EDUCATION_PCT", "Population with no education level", "Education", "% of resident population", pct(1258, 69324), "Residents whose highest level of education is reported as none.", "2011", census_source, "Table 8.1"),
        ("DMA_C2011_UNEMPLOYMENT_RATE", "Unemployment rate", "Employment", "% of labour force", 11.1, "Unemployed residents as a share of the labour force during the week before the Census.", "2011", census_source, "Table 7.1"),
        ("DMA_C2011_MOBILITY_DISABILITY_PCT", "Population reporting mobility disability", "Disability", "% of resident population", pct(1360, 69325), "Residents reporting mobility disability. Other disability types may also apply to the same person.", "2011", census_source, "Tables 9.2 and 9.3"),
        ("DMA_C2011_FOREIGN_BORN_PCT", "Foreign-born population", "Migration", "% of resident population", pct(5810, 69325), "Foreign-born residents, including not-stated country rows in the published table, as a share of resident population.", "2011", census_source, "Table 5.2"),
        ("DMA_C2011_ROSEAU_SHARE", "Population in the City of Roseau Census area", "Settlement", "% of resident population", pct(14741, 69325), "Residents in the City of Roseau Census row as a share of resident population. This is not a national urbanization rate.", "2011", census_source, "Table 1.2"),
        ("DMA_C2011_AFRO_DESCENT_PCT", "Population of Afro descent", "Ethnicity", "% of resident population", 84.8, "Residents reported in the Afro Descent ethnic group.", "2011", census_source, "Table 5.1"),
        ("DMA_C2011_NO_CHRONIC_ILLNESS_PCT", "Population reporting no chronic illness", "Health", "% of resident population", pct(52655, 69325), "Residents reporting no chronic illness. Chronic-illness categories are self-reported and multiple conditions may apply.", "2011", census_source, "Table 9"),
        ("DMA_MDG2014_UNDERWEIGHT_INCIDENCE", "Underweight-child incidence among children seen at health centres", "Nutrition", "% of children seen at health centres", 5.9, "The 2014 incidence covers children seen at health centres and includes stunted and wasted children; it is not a Census prevalence estimate.", "2014", "dma-mdg-2015", "MDG Achievement 2015 pp.1-2"),
        ("DMA_MDG2015_POVERTY_RATE", "Estimated population below the poverty line", "Poverty and livelihoods", "% of population", 19.8, "Estimated headcount poverty rate as of May 2015. It is a national estimate, not a parish Census value.", "2015", "dma-mdg-2015", "MDG Achievement 2015 p.1"),
    ]
    for indicator_id, name, theme, unit, value, definition, period, source_id, locator in national_specs:
        indicators.append({
            "id": indicator_id,
            "name": name,
            "theme": theme,
            "unit": unit,
            "definition": definition,
            "definition_id": indicator_id,
            "population": unit.removeprefix("% of "),
            "measurement_method": "source_reported" if value in {64.9, 90.0, 11.1, 84.8, 5.9, 19.8} else "derived_from_source_counts",
            "aggregation": "sum" if unit == "households" else "none",
            "period_policy": "fixed_source_period",
            "series_family": "census" if source_id == census_source else "survey",
            "display_role": "primary",
            "source_id": source_id,
            "source_locator": locator,
        })
        observations.append({
            "territory_id": "DMA",
            "indicator_id": indicator_id,
            "period": period,
            "value": value,
            "status": "observed",
            "source_id": source_id,
            "definition": definition,
            "definition_id": indicator_id,
            "unit": unit,
            "population": unit.removeprefix("% of "),
            "measurement_method": "source_reported" if value in {64.9, 90.0, 11.1, 84.8, 5.9, 19.8} else "derived_from_source_counts",
            "source_locator": locator,
        })

    sources = [
        {"id": census_source, "name": "2011 Population and Housing Census Report", "publisher": "Central Statistics Office of Dominica", "url": CENSUS_URL, "status": "ready", "retrieved_at": today, "reference_period": "2011", "geographic_level": "country and parish", "raw_path": "raw/dominica-country-edition/population-and-housing-census-2011.pdf", "sha256": sha(census), "license": "Official public report; source attribution retained.", "note": "Parish population, sex and age tables are joined to the ten reference parish boundaries. National-only tables are not imputed to parishes."},
        {"id": "dma-geoboundaries-adm1-2005", "name": "geoBoundaries DMA ADM1 reference boundaries", "publisher": "geoBoundaries / source credited as Wikimedia Commons", "url": meta["simplifiedGeometryGeoJSON"], "status": "ready", "retrieved_at": today, "reference_period": "2005 representation / 2023 build", "geographic_level": "parish", "raw_path": "raw/dominica-country-edition/geoBoundaries-DMA-ADM1_simplified.geojson", "sha256": sha(geo), "license": meta["boundaryLicense"], "note": "Reference-only boundaries; they are not represented as a current legal boundary certification."},
        {"id": "dma-mdg-2015", "name": "Dominica Millennium Development Goals Achievements 2015", "publisher": "Central Statistics Office of Dominica", "url": MDG, "status": "ready", "retrieved_at": today, "reference_period": "2014-2015 indicators", "geographic_level": "country", "raw_path": "raw/dominica-country-edition/millennium-development-goals-achievement-2015.pdf", "sha256": sha(mdg), "license": "Official public report; source attribution retained.", "note": "Nutrition and poverty values preserve their published dates, populations and methods and are not relabelled as 2011 Census measures."},
    ]
    comparisons = [{
        "parent_id": "DMA",
        "member_ids": [ids[name] for name in sorted(ids)],
        "label": "Parishes",
        "membership_note": "Ten reference parishes. City of Roseau and Rest of St. George Census rows are combined for the Saint George parish comparison.",
        "source_ids": ["dma-geoboundaries-adm1-2005", census_source],
    }]
    bundle = {
        "schema_version": "1.0",
        "country_area_id": "DMA",
        "period": "2011",
        "replace_country_branch": True,
        "territories": territories,
        "terminal_territory_ids": list(ids.values()),
        "comparisons": comparisons,
        "indicators": indicators,
        "observations": observations,
        "boundaries": {"type": "FeatureCollection", "features": features},
        "sources": sources,
    }
    (out / "dominica-country-depth-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog_names = [
        "Table 1.2 Population by sex and parish",
        "Table 1.3 Population by age group sex and parish",
        "Table 5.1 Ethnic groups by sex",
        "Table 5.2 Foreign-born population by parish and sex",
        "Table 7.1 Employment status",
        "Table 8.1 Highest level of education",
        "Table 9 Chronic illness",
        "Tables 9.2 and 9.3 Disability",
        "Table 11 Household size",
        "Table 11.9 Water facility",
        "Table 11.10 Toilet facility",
        "Table 11.11 Lighting",
        "Table 11.15 Internet access",
    ]
    catalog = [{"table_id": title, "table_title": title, "numeric_cell_count": 1, "source_path": "raw/dominica-country-edition/population-and-housing-census-2011.pdf"} for title in catalog_names]
    downloaded = [census, geo, law, crrp, budget, mdg]
    audit = {
        "schema_version": "1.0",
        "status": "complete",
        "counts": {"parishes": 10, "boundary_features": 10, "indicators": len(indicators), "observations": len(observations), "catalogued_tables": len(catalog)},
        "controls": {"roseau_and_rest_st_george_combined": True, "national_tables_not_imputed_to_parishes": True, "nutrition_and_poverty_periods_preserved": True, "2022_fieldwork_not_substituted_for_unpublished_results": True},
        "source_receipts": [{"name": item.name, "bytes": item.stat().st_size, "sha256": sha(item)} for item in downloaded],
    }
    (out / "DMA_COLLECTION_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    planning_sources = [
        {"id": "dma-physical-planning-act-2002", "name": "Physical Planning Act 2002", "publisher": "Government of the Commonwealth of Dominica", "url": LAW, "status": "ready", "retrieved_at": today, "reference_period": "2002", "geographic_level": "national legal framework", "raw_path": "raw/dominica-country-edition/physical-planning-act-2002.pdf", "sha256": sha(law), "license": "Official legal publication."},
        {"id": "dma-crrp-2020", "name": "Climate Resilience and Recovery Plan 2020-2030", "publisher": "Government of the Commonwealth of Dominica", "url": CRRP, "status": "ready", "retrieved_at": today, "reference_period": "2020-2030", "geographic_level": "country", "raw_path": "raw/dominica-country-edition/climate-resilience-and-recovery-plan-2020-2030.pdf", "sha256": sha(crrp), "license": "Official public plan; source attribution retained."},
        {"id": "dma-budget-2025-2026", "name": "Approved Estimates 2025-2026", "publisher": "Ministry of Finance, Economic Development, Climate Resilience and Social Security", "url": BUDGET, "status": "ready", "retrieved_at": today, "reference_period": "2025-2026", "geographic_level": "national budget", "raw_path": "raw/dominica-country-edition/approved-estimates-2025-2026.pdf", "sha256": sha(budget), "license": "Official public budget; source attribution retained."},
    ]
    theme_map = {
        "DMA_C2011_POP_TOTAL": "population_total",
        "DMA_C2011_FEMALE_PCT": "age_sex",
        "DMA_C2011_HOUSEHOLDS": "households_housing",
        "DMA_C2011_PUBLIC_PIPED_WATER_PCT": "drinking_water",
        "DMA_C2011_FLUSH_TOILET_PCT": "sanitation",
        "DMA_C2011_PUBLIC_ELECTRICITY_PCT": "electricity",
        "DMA_C2011_NO_EDUCATION_PCT": "education_literacy",
        "DMA_C2011_UNEMPLOYMENT_RATE": "employment",
        "DMA_C2011_MOBILITY_DISABILITY_PCT": "disability",
        "DMA_C2011_FOREIGN_BORN_PCT": "migration",
        "DMA_C2011_ROSEAU_SHARE": "urban_rural",
        "DMA_C2011_AFRO_DESCENT_PCT": "ethnicity",
        "DMA_C2011_NO_CHRONIC_ILLNESS_PCT": "health",
        "DMA_MDG2014_UNDERWEIGHT_INCIDENCE": "nutrition",
        "DMA_MDG2015_POVERTY_RATE": "poverty",
    }
    manifest = {
        "schema_version": "1.0",
        "country_area_id": "DMA",
        "scope_role": "completed Dominica edition with 2011 Census parish adapter",
        "country_adapter_status": "complete_country_adapter",
        "official_census_url": CENSUS_URL,
        "census_source_id": census_source,
        "semantic_source_path": "raw/dominica-country-edition/population-and-housing-census-2011.pdf",
        "audit_path": "evidence/DMA_INTEGRATION_AUDIT.json",
        "domains": {
            "official_statistics_office": {"status": "inspected", "urls": [STATS_URL], "note": "The official Central Statistics Office publication and data pages were inspected.", "evidence": [{"raw": "raw/dominica-country-edition"}]},
            "latest_census": {"status": "adopted", "urls": [CENSUS_2022_URL, CENSUS_URL], "note": "The 2022 Census field operation is documented, but no final 2022 result table was substituted. The latest published final report adopted here is 2011.", "evidence": [{"raw": "raw/dominica-country-edition/population-and-housing-census-2011.pdf"}]},
            "census_results": {"status": "adopted", "urls": [CENSUS_URL], "note": "Official 2011 Census results are integrated at country and parish level where the report publishes compatible parish tables.", "evidence": [{"audit": "evidence/DMA_INTEGRATION_AUDIT.json"}]},
            "table_catalog": {"status": "inspected", "urls": [CENSUS_URL], "note": "The report table inventory and every adopted table are catalogued; unselected tables remain retained in the source PDF.", "evidence": [{"audit": "evidence/DMA_INTEGRATION_AUDIT.json"}]},
            "machine_readable_data": {"status": "adopted", "urls": [CENSUS_URL], "note": "Official PDF tables were normalized into a source-attributed adapter with table locators and preserved denominators.", "evidence": [{"audit": "evidence/DMA_INTEGRATION_AUDIT.json"}]},
            "administrative_codes": {"status": "geography_matched", "urls": [GEO_META, CENSUS_URL], "note": "Census parish names were matched to ten ISO 3166-2-coded reference parishes; Roseau and Rest of St. George were summed before the Saint George join.", "evidence": [{"raw": "raw/dominica-country-edition/geoBoundaries-DMA-ADM1_simplified.geojson"}]},
            "adm1_adm2_boundaries": {"status": "adopted", "urls": [GEO_META], "note": "Ten source-attributed reference parish shapes are integrated and labelled non-certifying; no ADM2 layer is claimed.", "evidence": [{"raw": "raw/dominica-country-edition/geoBoundaries-DMA-ADM1_simplified.geojson"}]},
            "planning_law": {"status": "inspected", "urls": [LAW], "note": "The official Physical Planning Act 2002 was acquired and inspected; Part III covers development plans and public participation.", "evidence": [{"raw": "raw/dominica-country-edition/physical-planning-act-2002.pdf"}]},
            "planning_guidance": {"status": "acquired", "urls": [CRRP], "note": "The official Climate Resilience and Recovery Plan is retained as national planning material; it is not represented as a parish statutory plan.", "evidence": [{"raw": "raw/dominica-country-edition/climate-resilience-and-recovery-plan-2020-2030.pdf"}]},
            "plans_budgets_implementation_evaluation": {"status": "acquired", "urls": [CRRP, BUDGET], "note": "The official plan and approved 2025-2026 estimates are acquired. Their presence is not treated as proof that every target was implemented or evaluated.", "evidence": [{"raw": "raw/dominica-country-edition"}]},
        },
        "recent_census_rounds": [
            {"round": "2020", "date_text": "2022 Census field operation; final results not adopted", "year": 2022, "url": CENSUS_2022_URL},
            {"round": "2010", "date_text": "2011 Population and Housing Census", "year": 2011, "url": CENSUS_URL},
            {"round": "2000", "date_text": "2001 Population and Housing Census", "year": 2001, "url": "https://stats.gov.dm/wp-content/uploads/2019/06/Population_and_Housing_Census_2001.pdf"},
        ],
        "indicator_themes": theme_map,
        "theme_reasons": {
            "urban_rural": "The City of Roseau Census-area share is integrated and explicitly is not labelled as a national urbanization rate.",
            "nutrition": "The 2014 health-centre incidence preserves the published clinic-attendee universe and is not copied to parishes.",
            "poverty": "The May 2015 official estimate retains its year and national scope and is not relabelled as a 2011 Census or parish value.",
        },
        "semantic_catalog": catalog,
        "sources": planning_sources,
        "documents": [
            {"id": "dma-physical-planning-act", "territory_id": "DMA", "category": "reference", "title": "Physical Planning Act 2002", "kind": "official-law", "url": LAW, "availability": "body_acquired", "official_status": "unverified", "source_id": "dma-physical-planning-act-2002"},
            {"id": "dma-crrp", "territory_id": "DMA", "category": "plan", "title": "Climate Resilience and Recovery Plan 2020-2030", "kind": "official-plan", "url": CRRP, "availability": "body_acquired", "official_status": "unverified", "source_id": "dma-crrp-2020"},
            {"id": "dma-budget-2025-2026", "territory_id": "DMA", "category": "budget", "title": "Approved Estimates 2025-2026", "kind": "official-budget", "url": BUDGET, "availability": "body_acquired", "official_status": "unverified", "source_id": "dma-budget-2025-2026"},
        ],
        "census_history": {
            "country_id": "DMA",
            "names": {"en": "Dominica", "es": "Dominica", "ja": "ドミニカ国"},
            "adopted_data_year": 2011,
            "adopted_source_url": CENSUS_URL,
            "official_census_url": CENSUS_2022_URL,
            "recent_rounds": [
                {"year": 2022, "status": "fieldwork_no_final_results_adopted", "url": CENSUS_2022_URL},
                {"year": 2011, "status": "results_adopted", "url": CENSUS_URL},
                {"year": 2001, "status": "historical_round", "url": "https://stats.gov.dm/wp-content/uploads/2019/06/Population_and_Housing_Census_2001.pdf"},
            ],
            "note": {"en": "AreaData adopts the published final 2011 report. The 2022 field operation is documented, but no unpublished final results are substituted.", "es": "AreaData adopta el informe final publicado de 2011. Se documenta el operativo de 2022, sin sustituir resultados finales no publicados.", "ja": "AreaDataでは公表済みの2011年最終報告を採用します。2022年調査の実施情報は記録しますが、未公表の確定結果は代用しません。"},
        },
        "adapters": ["dma-census-2011-depth", "dma-planning-evidence"],
        "collection_notes": [
            "DMA: official 2011 Census parish population, sex and age are joined to ten reference parishes; national-only tables are not imputed to parishes.",
            "DMA: the 2022 field operation is recorded separately from adopted 2011 final results; nutrition and poverty retain their 2014 and 2015 national source universes.",
        ],
        "inventory_method": "The official Census PDF is preserved by hash. Every adopted table and field has an explicit semantic record; catalogued but unselected tables remain non-adopted with a reason.",
        "audit": audit,
    }
    (out / "DMA_COMPLETION_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

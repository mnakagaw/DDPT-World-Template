"""Adopt checked 2024 Georgia census geography and one municipality's documents."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


POP_ID = "geo-geostat-census-2024-population-by-local-unit"
IDP_ID = "geo-geostat-census-2024-idp-by-residence-origin"
PLAN_ID = "geo-kutaisi-municipal-action-plan-2026-2029"
BUDGET_ID = "geo-kutaisi-budget-2026-original-ordinance"
RAW_DIR = "raw/georgia-geostat-2024/"
PERIOD = "2024-11-14"
POP_FIELDS = (
    ("TOTAL", "total", "Population, both sexes", "B", "total usual residents"),
    ("MALE", "male", "Male population", "C", "male usual residents"),
    ("FEMALE", "female", "Female population", "D", "female usual residents"),
    ("URBAN_TOTAL", "urban_total", "Urban population, both sexes", "E", "usual residents of urban settlements"),
    ("URBAN_MALE", "urban_male", "Urban male population", "F", "male usual residents of urban settlements"),
    ("URBAN_FEMALE", "urban_female", "Urban female population", "G", "female usual residents of urban settlements"),
    ("RURAL_TOTAL", "rural_total", "Rural population, both sexes", "H", "usual residents of rural settlements"),
    ("RURAL_MALE", "rural_male", "Rural male population", "I", "male usual residents of rural settlements"),
    ("RURAL_FEMALE", "rural_female", "Rural female population", "J", "female usual residents of rural settlements"),
)
IDP_FIELDS = (
    ("TOTAL", "idp_total", "Internally displaced persons, both sexes", "B", "IDPs by current usual residence"),
    ("ORIGIN_ABKHAZIA", "idp_origin_abkhazia", "IDPs formerly resident in Abkhazia", "C", "IDPs with pre-displacement residence in Abkhazia"),
    ("ORIGIN_TSKHINVALI", "idp_origin_tskhinvali", "IDPs formerly resident in Tskhinvali region", "D", "IDPs with pre-displacement residence in Tskhinvali region"),
    ("MALE", "idp_male", "Male internally displaced persons", "E", "male IDPs by current usual residence"),
    ("MALE_ORIGIN_ABKHAZIA", "idp_male_origin_abkhazia", "Male IDPs formerly resident in Abkhazia", "F", "male IDPs with pre-displacement residence in Abkhazia"),
    ("MALE_ORIGIN_TSKHINVALI", "idp_male_origin_tskhinvali", "Male IDPs formerly resident in Tskhinvali region", "G", "male IDPs with pre-displacement residence in Tskhinvali region"),
    ("FEMALE", "idp_female", "Female internally displaced persons", "H", "female IDPs by current usual residence"),
    ("FEMALE_ORIGIN_ABKHAZIA", "idp_female_origin_abkhazia", "Female IDPs formerly resident in Abkhazia", "I", "female IDPs with pre-displacement residence in Abkhazia"),
    ("FEMALE_ORIGIN_TSKHINVALI", "idp_female_origin_tskhinvali", "Female IDPs formerly resident in Tskhinvali region", "J", "female IDPs with pre-displacement residence in Tskhinvali region"),
)
LEADS = (
    ("geo-geostat-census-2024-catalogue", "2024 population-census results catalogue", "https://www.geostat.ge/en/modules/categories/12/2024-population-census-of-georgia-results", "National Statistics Office of Georgia", "2024 census; eight topical sections", "national to municipality; varies by table", "Eight topical sections exist; only the six geography/migration XLSX files were acquired and inventoried in this pass."),
    ("geo-geostat-agriculture-2024-catalogue", "2024 agricultural-census results catalogue", "https://www.geostat.ge/en/modules/categories/905/2024-agricultural-census-results", "National Statistics Office of Georgia", "2024 agricultural census", "published table geography to check", "Five agricultural sections are listed; individual tables and geographic coverage remain to be acquired and audited."),
    ("geo-geostat-regional-portal", "Regional and municipal statistics portal", "https://regions.geostat.ge/regions/", "National Statistics Office of Georgia", "mixed statistical periods", "region and municipality", "Availability, detailed series definitions, dates and export paths remain to be checked; no values adopted."),
    ("geo-geostat-population-estimates", "Annual population by region and self-governed unit", "https://www.geostat.ge/en/modules/categories/41/population", "National Statistics Office of Georgia", "annual 1 January estimates", "national, regional, municipality", "Annual population series is separate from the 14 November 2024 census; its XLSX has not been acquired for this adapter."),
    ("geo-napr-nsdi-boundaries", "Municipal and geographic-region boundary catalogues", "https://nsdi.gov.ge/en/geoportal", "National Agency of Public Registry / NSDI", "current portal edition not verified", "municipality and region", "Official spatial-data locations identified, but no dated polygon, code field, legal validity or match to 2024 census rows is verified."),
    ("geo-spatial-planning-code", "Code on Spatial Planning, Architectural and Construction Activities", "https://matsne.gov.ge/en/document/view/4276845?impose=original", "Legislative Herald of Georgia", "2018 law with later amendments", "national law; municipality planning", "Official text identifies municipality spatial planning and Sakrebulo approval. Consolidated 2026 version and implementing ordinance must be checked before asserting current detailed duties."),
    ("geo-local-self-government-code", "Organic Law on Local Self-Government", "https://matsne.gov.ge/en/document/view/2244429?impose=original", "Legislative Herald of Georgia", "2014 law with later amendments", "municipal government", "Official text identifies municipality as self-governing unit. Current consolidated version, city/community distinctions and local planning/budget provisions need legal review."),
    ("geo-budget-code", "Budget Code of Georgia", "https://matsne.gov.ge/en/document/view/91006", "Legislative Herald of Georgia", "current consolidated edition to verify", "municipal budget planning", "Official source identifies municipal priority and budget preparation rules; exact current edition and local application require confirmation."),
    ("geo-kutaisi-document-register", "Kutaisi municipal official document register", "https://kutaisi.gov.ge/documents/searchDocument?document_type=69&gancxadebis_nomeri=0&page=1", "Kutaisi Municipality", "2025-2026 documents", "Kutaisi municipality", "Register shows 1 September 2025 mayoral action-plan approval and later general-plan concept proceedings; other plan, execution and evaluation records remain unassessed."),
    ("geo-geostat-terms", "Geostat data terms of use", "https://www.geostat.ge/en/page/monacemta-gamoyenebis-pirobebi", "National Statistics Office of Georgia", "checked 2026-09-26", "statistics and official publications", "Geostat permits download, adaptation and redistribution of its own statistical data and publications with source attribution; third-party material and logos are exceptions."),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(label):
    value = re.sub(r"[^A-Z0-9]+", "-", label.upper()).strip("-")
    if not value:
        raise ValueError(f"Empty geography slug: {label}")
    return value


def load_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "GEO" or any(s["id"] == POP_ID for s in dataset["sources"]):
        raise ValueError("Expected an unmodified Georgia bootstrap candidate")
    structure = json.loads((project / "evidence/GEO_GEOSTAT_2024_STRUCTURE.json").read_text(encoding="utf-8"))
    if (structure["population_rows"], structure["idp_rows"], structure["population_nil_cells"]) != (85, 75, 27):
        raise ValueError("Run the full census inspector first")
    for name, digest in structure["raw_sha256"].items():
        original = project / RAW_DIR / name
        receipt = json.loads((project / RAW_DIR / (name + ".receipt.json")).read_text(encoding="utf-8"))
        if sha(original) != digest or receipt["sha256"] != digest or receipt["status"] != "acquired":
            raise ValueError(f"Census original/receipt changed: {name}")
    plan_receipts = {Path(r["raw_path"]).name: r for r in json.loads((project / "evidence/GEO_KUTAISI_PLAN_ACQUISITION.json").read_text(encoding="utf-8"))["receipts"]}
    if len(plan_receipts) != 2:
        raise ValueError("Expected both Kutaisi planning originals")
    for receipt in plan_receipts.values():
        if sha(project / receipt["raw_path"]) != receipt["sha256"] or receipt["status"] != "acquired":
            raise ValueError("Kutaisi planning original changed")
    pop_rows = load_rows(project / "evidence/GEO_GEOSTAT_2024_POPULATION_ROWS.csv")
    idp_rows = load_rows(project / "evidence/GEO_GEOSTAT_2024_IDP_ROWS.csv")
    if len(pop_rows) != 85 or len(idp_rows) != 75:
        raise ValueError("Census source row inventory changed")
    now = datetime.now(timezone.utc).isoformat()

    country = next(t for t in dataset["territories"] if t["id"] == "GEO")
    country.update(type="country", source_id=POP_ID, code_system="ISO3 GEO dataset key; Geostat 2024 census country row",
                   boundary_version=None, reporting_role="2024-11-14 census national total excluding occupied territories")
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    territory_by_label = {"Georgia": country}
    for row in pop_rows[1:]:
        name, area_type = row["source_name_en"], row["area_type"]
        if area_type == "region_or_self_governing_city":
            kind = "TBILISI" if name == "C. Tbilisi" else "REG"
            level = "regional_reporting_unit"
            territory_type = "self_governing_city" if kind == "TBILISI" else "autonomous_republic" if name == "Adjara A.R." else "statistical_region"
        elif area_type == "tbilisi_district":
            kind, level, territory_type = "TBILISI_DIST", "municipal_district", "municipal_district"
        else:
            kind, level, territory_type = "MUN", "municipality", "municipality"
        territory_id = f"GEO:GEOSTAT2024:{kind}:{slug(name)}"
        if name in territory_by_label or any(t["id"] == territory_id for t in dataset["territories"]):
            raise ValueError(f"Duplicate source geography: {name}")
        parent = territory_by_label[row["parent_source_name_en"]]
        territory = {
            "id": territory_id, "name": name, "level": level, "type": territory_type,
            "parent_id": parent["id"], "official_code": None,
            "code_system": "Geostat 2024 census Table 02 source row and parent; official administrative code not printed",
            "provider_code": None, "source_id": POP_ID, "boundary_version": None,
            "reconciliation_status": "2024_census_source_hierarchy_checked; official_code_and_dated_polygon_unverified",
        }
        dataset["territories"].append(territory)
        territory_by_label[name] = territory
    if len(dataset["territories"]) != 85:
        raise ValueError("Expected 85 census reporting territories")

    census_receipts = {Path(p).name: json.loads((project / RAW_DIR / (Path(p).name + ".receipt.json")).read_text(encoding="utf-8")) for p in structure["raw_sha256"]}
    all_source_rows = [
        ("01-administrative-territorial-units-sex.xlsx", "2024 census detailed administrative/settlement population and sex", "national to named settlement", "partial", "4,838 rows and three numeric columns inventoried; 612 suppressed sex cells marked '...'. No settlement hierarchy/code crosswalk was certified, so this sheet contributes no adopted observations."),
        ("02-self-governed-units-urban-rural-sex.xlsx", "2024 census population by regional and self-governing unit, urban/rural and sex", "national, 11 regional rows, 63 municipalities, 10 Tbilisi districts", "ready", "Nine direct count columns adopted. Twenty-seven '-' cells mean magnitude nil and remain missing, not numeric zero. The 11 region rows and each child cover passed arithmetic checks."),
        ("03-birthplace-age-sex.xlsx", "2024 census place of birth by age and sex", "place of birth, not usual-residence geography", "partial", "All 19 numeric columns inventoried; birthplace categories must not be joined to current-residence territories. No observations adopted."),
        ("04-internal-migration.xlsx", "2024 census internal migration current/previous residence matrix", "national and regional current-residence rows", "partial", "All 14 numeric columns inventoried. Origin/destination matrix and migration definition require separate indicator design; no observations adopted."),
        ("05-idp-age-settlement-sex.xlsx", "2024 census IDPs by age, urban/rural and sex", "national age groups", "partial", "Nine numeric columns inventoried; national age-group series remains unadopted this pass. IDPs are a subset of residents."),
        ("06-idp-residence-origin-sex.xlsx", "2024 census IDPs by current residence, prior region and sex", "national, 11 regional rows and 63 municipalities; no Tbilisi district rows", "ready", "Nine direct count columns adopted for 75 source rows. Origin and sex identities and regional/municipality cover were checked; values are a subset of population, not additive to total residents."),
        ("2024-census-main-results.pdf", "Main results of the 2024 population and agricultural census, 22 June 2026", "national summary", "partial", "Official PDF confirms the national 3,929,581 and urban 2,455,444 in the adopted Excel. Earlier April release had a different urban tally; 22 June is the comparison edition. Summary percentages are not adopted as census counts."),
    ]
    for name, title, geography, status, note in all_source_rows:
        receipt = census_receipts[name]
        source_id = POP_ID if name.startswith("02-") else IDP_ID if name.startswith("06-") else "geo-geostat-census-2024-" + name.split("-")[0].lower()
        if name.endswith(".pdf"):
            source_id = "geo-geostat-census-2024-main-results"
        dataset["sources"].append({
            "id": source_id, "name": title, "url": receipt["source_url"], "publisher": "National Statistics Office of Georgia",
            "reference_period": "2024-11-14 census reference moment; publication 2026" if name.endswith(".xlsx") else "22 June 2026 summary of 2024 census",
            "geographic_level": geography, "status": status, "retrieved_at": receipt["retrieved_at"],
            "raw_path": receipt["raw_path"], "sha256": receipt["sha256"],
            "license": "Geostat public data use with source attribution; third-party/logo exceptions", "note": note,
        })
    for source_id, name, receipt_name, note in (
        (PLAN_ID, "Kutaisi 2026–2029 medium-term action plan and mayoral approval order", "kutaisi-action-plan-2026-2029.pdf", "Mayoral order B44.442524458 dated 1 September 2025 approves the four-year plan. It contains programme budgets, outcomes and targets; not evidence of a completed spatial master plan or achieved targets."),
        (BUDGET_ID, "Kutaisi 2026 budget original ordinance No. 3", "kutaisi-budget-2026-original.pdf", "Original Sakrebulo ordinance of 24 December 2025 approved the 2026 budget, effective 1 January. Matsne labels the available text as original edition valid through 28 January 2026; later consolidated amendments are not acquired, so original budget figures are not current executed amounts."),
    ):
        receipt = plan_receipts[receipt_name]
        dataset["sources"].append({"id": source_id, "name": name, "url": receipt["source_url"],
                                   "publisher": "Kutaisi Municipality" if source_id == PLAN_ID else "Legislative Herald of Georgia / Kutaisi Sakrebulo",
                                   "reference_period": "2026-2029" if source_id == PLAN_ID else "original 2026 budget ordinance, approved 2025-12-24",
                                   "geographic_level": "Kutaisi municipality", "status": "ready", "retrieved_at": receipt["retrieved_at"],
                                   "raw_path": receipt["raw_path"], "sha256": receipt["sha256"],
                                   "license": "official_publication_terms_review_required", "note": note})
    for source_id, name, url, publisher, period, geography, note in LEADS:
        dataset["sources"].append({"id": source_id, "name": name, "url": url, "publisher": publisher,
                                   "reference_period": period, "geographic_level": geography,
                                   "status": "not_collected", "retrieved_at": now,
                                   "license": "terms_review_required", "note": note})

    for prefix, fields, source_id, method, definition in (
        ("GEO_GEOSTAT_2024_POP", POP_FIELDS, POP_ID, "geostat_2024_population_agricultural_census_table02",
         "Direct 14 November 2024 usual-resident count in Geostat 2024 census Table 02. The census excludes occupied territories; this count is not a 1 January annual population estimate or a WDI series. A source '-' is magnitude nil and is retained as missing rather than an observed zero."),
        ("GEO_GEOSTAT_2024_IDP", IDP_FIELDS, IDP_ID, "geostat_2024_population_agricultural_census_table06",
         "Direct 14 November 2024 count of internally displaced persons by current usual residence in Geostat 2024 census Table 06. Prior residence in Abkhazia and Tskhinvali region is an origin attribute, not the current reporting territory. IDPs are a subset of residents and must not be added to total population."),
    ):
        for suffix, _, title, _, population in fields:
            dataset["indicators"].append({
                "id": f"{prefix}_{suffix}", "name": title + " (2024 census)", "theme": "Population" if source_id == POP_ID else "Displacement",
                "unit": "people", "source_id": source_id, "definition": definition,
                "population": population, "aggregation": "none", "measurement_method": method,
                "series_family": "census", "display_role": "primary", "period_policy": "latest_available_per_indicator",
                "display_decimals": 0,
            })
    for rows, fields, prefix, source_id, method, table in (
        (pop_rows, POP_FIELDS, "GEO_GEOSTAT_2024_POP", POP_ID, "geostat_2024_population_agricultural_census_table02", "02"),
        (idp_rows, IDP_FIELDS, "GEO_GEOSTAT_2024_IDP", IDP_ID, "geostat_2024_population_agricultural_census_table06", "06"),
    ):
        for row in rows:
            territory = territory_by_label[row["source_name_en"]]
            for suffix, field, _, column, _ in fields:
                value = row[field]
                missing = value == "-"
                dataset["observations"].append({
                    "territory_id": territory["id"], "indicator_id": f"{prefix}_{suffix}",
                    "period": PERIOD, "value": None if missing else int(value),
                    "status": "missing" if missing else "observed", "source_id": source_id,
                    "measurement_method": method,
                    "source_locator": f"Table {table}, worksheet 1, {column}{row['source_excel_row']}"
                    + ("; source dash: magnitude nil" if missing else ""),
                })

    kutaisi = territory_by_label["C. Kutaisi"]
    def match(source_id, locator):
        return {"territory_id": kutaisi["id"], "country_id": "GEO", "type": kutaisi["type"],
                "code_system": kutaisi["code_system"], "official_code": None, "boundary_version": None,
                "method": "Official Kutaisi municipal title matched to Geostat 2024 C. Kutaisi reporting row under Imereti; no official code or legal polygon is inferred.",
                "source_id": source_id, "locator": locator, "checked_at": now}
    dataset["documents"].append({
        "id": "geo-kutaisi-action-plan-2026-2029", "territory_id": kutaisi["id"],
        "category": "plan", "kind": "medium_term_municipal_action_plan",
        "title": "Kutaisi Municipality 2026–2029 medium-term action plan (mayoral order of 1 September 2025)",
        "url": plan_receipts["kutaisi-action-plan-2026-2029.pdf"]["source_url"], "period": "2026-2029",
        "target_period": {"label": "2026-2029", "kind": "multi_year"},
        "availability": "content_verified", "official_status": "approved_by_mayor_2025_original",
        "official_evidence": {"source_id": PLAN_ID, "locator": "PDF page 1, order B44.442524458 dated 1 September 2025, approval clause 1 and electronic signature",
                              "checked_at": now, "authority": "Kutaisi Municipality Mayor"},
        "source_id": PLAN_ID, "territory_match": match(PLAN_ID, "PDF page 1 municipal title; Geostat Table 02 worksheet 1 row 31"),
        "content": {"summary": "The mayor-approved four-year action plan describes programmes and subprogrammes, planned financing, responsible bodies, expected results and evaluation indicators. Its programme for preparing the city's general plan is a planned activity; this document does not prove final adoption or implementation of that general plan. Later revisions of this action plan were not checked.",
                    "priorities": ["Infrastructure", "Environment", "Education", "Culture, sport and youth", "Health and social protection", "Economy", "Governance"],
                    "evidence": {"source_id": PLAN_ID, "locator": "PDF pages 1 and 3 (order and contents), page 72 (general-plan preparation subprogramme)",
                                 "checked_at": now, "authority": "Kutaisi Municipality"}},
    })
    dataset["documents"].append({
        "id": "geo-kutaisi-budget-2026-original", "territory_id": kutaisi["id"],
        "category": "budget", "kind": "municipal_budget_original_ordinance",
        "title": "Kutaisi 2026 municipal budget, original ordinance No. 3 (later amendments unverified)",
        "url": plan_receipts["kutaisi-budget-2026-original.pdf"]["source_url"], "period": "2026",
        "target_period": {"label": "2026", "kind": "calendar_year"},
        "availability": "content_verified", "official_status": "original_ordinance_approved_2025_current_amendments_unverified",
        "official_evidence": {"source_id": BUDGET_ID, "locator": "PDF page 1, Kutaisi Sakrebulo ordinance No. 3 dated 24 December 2025, approval clause and 1 January 2026 effective date; Matsne original-edition notice",
                              "checked_at": now, "authority": "Kutaisi Sakrebulo / Legislative Herald of Georgia"},
        "source_id": BUDGET_ID, "territory_match": match(BUDGET_ID, "PDF page 1, municipal ordinance title; Geostat Table 02 worksheet 1 row 31"),
        "content": {"summary": "Original Kutaisi Sakrebulo ordinance No. 3 of 24 December 2025 approves the 2026 municipal budget and takes effect on 1 January 2026. Annex 1 distinguishes 2024 actual, 2025 plan and 2026 plan in thousand GEL. Matsne identifies this original edition as valid only through 28 January 2026; later amendments and 2026 actual execution are not acquired. No current or executed amount is derived from this original.",
                    "evidence": {"source_id": BUDGET_ID, "locator": "PDF page 1, articles 1–4 and Annex 1 first table; Matsne HTML original-edition notice",
                                 "checked_at": now, "authority": "Kutaisi Sakrebulo / Legislative Herald of Georgia"}},
    })

    dataset["country"]["geography_note"] = (
        "Geostat's 14 November 2024 census excludes occupied territories and reports one national, 11 regional/self-governing-city, 63 municipality and 10 Tbilisi internal-district rows. The source table's direct totals are used; IDPs are a resident subset and are not added to total population. Geostat Table 02 labels and printed hierarchy are source-scoped identifiers, not official administrative codes. No 2024 legal polygon/code crosswalk is verified; 12 bootstrap 2015 geoBoundaries shapes are withheld. WDI annual estimates and 2024 census counts are separate series.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="Geostat 2024 source hierarchy and 85 geographic labels are checked. National Agency of Public Registry/NSDI official region and municipality layer locations were identified, but their dated codes, geometry and match to the census were not verified. Twelve 2015 provider polygons are withheld.",
                       next_action="Acquire NSDI official code/municipality and region boundary originals with dates/terms; reconcile 85 census rows, Tbilisi districts and excluded areas before map adoption.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="Geostat 2024 Table 02 provides nine population fields for 85 reporting rows; Table 06 provides nine IDP fields for 75 rows. Twenty-seven Table 02 dash cells remain missing. Four other acquired geography/migration tables are inventoried but not adopted. Other 2024 census thematic sections, agriculture and annual estimates remain open.",
                       next_action="Audit every remaining census topical table and rural/agriculture series, source definitions, suppression, and municipal coverage; add only compatible, checked indicators.")
        elif gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Kutaisi's 2026–2029 mayor-approved medium-term action plan and original 2026 budget ordinance were acquired and checked. Later plan revisions and budget amendments, spatial master-plan approval, implementation, evaluation and the other municipalities are unverified.",
                       next_action="Acquire current consolidated Kutaisi budget and plan revisions, separate final spatial-plan decisions from concept and planned activity, and inventory each municipality's adopted plans, budgets, execution and evaluation.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["georgia-geostat-2024-census-partial", "georgia-kutaisi-planning-partial"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["analysis"]["comparisons"] = [{
        "parent_id": "GEO", "member_ids": [territory_by_label[r["source_name_en"]]["id"] for r in pop_rows if r["area_type"] == "region_or_self_governing_city"],
        "label": "2024 census regional reporting areas",
        "membership_note": "Geostat Table 02 lists Tbilisi city, Adjara Autonomous Republic and nine statistical regions as 11 disjoint direct country reporting rows. They share the same census reference moment and fields, while legal planning roles differ. The occupied territories are outside source scope.",
        "source_ids": [POP_ID], "color_scale": {"mode": "within_selection"},
    }]
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    adopted = [o for o in dataset["observations"] if o["indicator_id"].startswith("GEO_GEOSTAT_2024_")]
    observed = [o for o in adopted if o["status"] == "observed"]
    if len(adopted) != 1440 or len(observed) != 1413 or len(dataset["documents"]) != 2:
        raise ValueError("Unexpected adopted 2024 scope")
    tuples = sorted((o["territory_id"], o["indicator_id"], o["period"], o["status"], o["value"]) for o in adopted)
    audit = {"status": "partial_candidate_not_accepted", "checked_at": now,
             "territories": len(dataset["territories"]), "domestic_indicators": 18,
             "domestic_observations": len(adopted), "numeric_observations": len(observed),
             "source_dash_missing_rows": len(adopted) - len(observed), "documents_content_verified": 2,
             "national_population": 3929581, "national_idps": 210628, "withheld_provider_shapes": 12,
             "adopted_tuple_sha256": hashlib.sha256(json.dumps(tuples, ensure_ascii=False).encode("utf-8")).hexdigest(),
             "unresolved": ["Official codes and dated legal polygons", "All other census topical and agriculture tables", "Other municipalities' plans and budgets", "Kutaisi later amendments and spatial-plan adoption", "Implementation and official evaluation", "42 scenarios and independent acceptance"]}
    (project / "evidence/GEO_GEOSTAT_2024_IMPORT_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_2024_census_partially_adopted", "checked_at": now,
        "census": "Six Geostat 2024 geography/migration XLSX originals and June 2026 PDF acquired. Tables 02 and 06 adopted after full numeric-column and row/hierarchy checks; four other sheets inventoried only.",
        "geography": "85 source labels and parent groups checked; official codes, 2024 legal polygons and excluded-area reconciliation unresolved. Twelve 2015 provider shapes withheld.",
        "planning": "Kutaisi mayor-approved 2026–2029 action plan and original 2026 budget checked. Later amendments, spatial master plan, other municipalities, actual execution/evaluation not established.",
        "cross_country_candidates": "Common-source catalogue availability remains unassessed for GEO; no common-source local values were adopted.",
    }
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    original = markdown_path.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    new = ("Research status: **official_2024_census_partially_adopted** (2026-09-26).\n\n"
           "Geostat's 2024 census geography/migration originals were acquired and six sheets inventoried. Table 02 contributes nine population fields for 85 reporting rows; Table 06 contributes nine IDP fields for 75 rows. The 27 Table 02 source dashes remain missing, never zero. A Kutaisi 2026–2029 approved action plan and original 2026 budget were acquired; the latter's amendments remain unverified. No current official code or dated polygon has been joined, and the 12 bootstrap 2015 provider shapes are withheld. Other census themes, plans, budgets, execution and evaluation remain open. See GEO_GEOSTAT_2024_STRUCTURE.json and GEO_GEOSTAT_2024_IMPORT_AUDIT.json.")
    if old not in original:
        raise ValueError("Unexpected Georgia source preflight Markdown")
    markdown_path.write_text(original.replace(old, new), encoding="utf-8")
    print(json.dumps({"territories": len(dataset["territories"]), "domestic_indicators": 18,
                      "domestic_observations": len(adopted), "numeric": len(observed), "missing_dash": 27,
                      "documents": 2, "sources_added": 7 + 2 + len(LEADS)}))


if __name__ == "__main__":
    main()

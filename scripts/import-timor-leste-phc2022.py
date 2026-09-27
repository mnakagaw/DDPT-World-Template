"""Build an unpublished Timor-Leste 2022 census partial candidate from pinned PDFs.

Table 4.1/4.2 are raster tables in the official report. Their full post/suco
roster is retained as evidence only until cell-level extraction and geography
reconciliation can be independently checked.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/timor-leste-phc2022-source-manifest.json"
CENSUS = "tls-inetl-phc2022-main-report"
BOUNDARY = "INETL Population and Housing Census 2022 reporting geography; polygons pending"
AREAS = (
    "Aileu", "Ainaro", "Atauro", "Baucau", "Bobonaro", "Covalima",
    "Dili", "Ermera", "Lautém", "Liquiça", "Manatuto", "Manufahi",
    "Oecusse", "Viqueque",
)
ROSTER = ("Timor-Leste",) + AREAS
AREA_PATTERN = re.compile(r"^\s*(" + "|".join(re.escape(x) for x in ROSTER) + r")\s+(.+?)\s*$")
AGE_PATTERN = re.compile(r"^\s*((?:\d{1,2}(?:-\d{1,2})?|\d{1,2}\+))\s+(.+?)\s*$")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number_tokens(tail):
    return re.findall(r"(?<!\S)(?:[\d,]+(?:\.\d+)?|-)(?!\S)", tail)


def pinned_sources(project, manifest):
    result = {}
    for item in manifest["sources"]:
        path = project / item["raw_path"]
        require(path.is_file(), f"Missing original: {path}")
        require(path.stat().st_size == item["bytes"], f"Length changed: {path}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
                f"Hash changed: {path}")
        result[item["id"]] = path
    require(len(result) == 8, "Manifest source count changed")
    return result


def extract_rows(pdf_path, pages, columns, with_ages=False):
    summary = {}
    age_rows = defaultdict(list)
    current = None
    for page_index in pages:
        completed = subprocess.run(
            ["pdftotext", "-f", str(page_index + 1), "-l", str(page_index + 1),
             "-layout", str(pdf_path), "-"], check=True, capture_output=True)
        text = completed.stdout.decode("utf-8")
        for line in text.splitlines():
            match = AREA_PATTERN.match(line)
            if match:
                values = number_tokens(match.group(2))
                if len(values) == columns:
                    name = match.group(1)
                    require(name not in summary, f"Duplicate {name} on PDF page {page_index + 1}")
                    summary[name] = {"values": values, "pdf_page": page_index + 1,
                                     "report_page": page_index - 15}
                    current = name
                continue
            if with_ages and current:
                match = AGE_PATTERN.match(line)
                if match:
                    values = number_tokens(match.group(2))
                    if len(values) == columns:
                        age_rows[current].append((match.group(1),
                                                  [None if v == "-" else int(v.replace(",", "")) for v in values]))
    require(set(summary) == set(ROSTER), f"Expected national and 14 area rows, found {sorted(summary)}")
    if with_ages:
        require(all(len(age_rows[name]) == 17 for name in ROSTER),
                f"Age-row roster differs: {dict((k, [v[0] for v in values]) for k, values in age_rows.items())}")
    return summary, age_rows


def audit_nine_columns(rows, age_rows, label):
    failures = []
    for name, record in rows.items():
        values = [int(v.replace(",", "")) for v in record["values"]]
        total, part_a, part_b, male, male_a, male_b, female, female_a, female_b = values
        if not (total == part_a + part_b == male + female and
                male == male_a + male_b and female == female_a + female_b and
                part_a == male_a + female_a and part_b == male_b + female_b):
            failures.append({"area": name, "kind": "summary_arithmetic", "values": values})
        by_age = [None if any(age[1][i] is None for age in age_rows[name]) else
                  sum(age[1][i] for age in age_rows[name]) for i in range(9)]
        for i, age_sum in enumerate(by_age):
            if age_sum is not None and values[i] != age_sum:
                failures.append({"area": name, "kind": "age_sum", "column": i + 1,
                                 "summary": values[i], "age_sum": age_sum})
    for i in range(9):
        published = int(rows["Timor-Leste"]["values"][i].replace(",", ""))
        area_sum = sum(int(rows[name]["values"][i].replace(",", "")) for name in AREAS)
        if published != area_sum:
            failures.append({"kind": "national_sum", "column": i + 1,
                             "published": published, "area_sum": area_sum})
    return {"table": label, "summary_rows": len(rows),
            "numeric_summary_cells": len(rows) * 9,
            "age_rows": sum(len(v) for v in age_rows.values()),
            "numeric_age_cells": sum(value is not None for area in age_rows.values()
                                     for _, row in area for value in row),
            "suppressed_age_cells": sum(value is None for area in age_rows.values()
                                        for _, row in area for value in row),
            "issues": failures}


def audit_pdf(pdf_path):
    table43, _ = extract_rows(pdf_path, [102], 6)
    table411, ages411 = extract_rows(pdf_path, range(118, 124), 9, True)
    table412, ages412 = extract_rows(pdf_path, range(124, 131), 9, True)
    t43_failures = []
    for name, record in table43.items():
        total, male, female, sex_ratio, area, density = record["values"]
        total, male, female = (int(x.replace(",", "")) for x in (total, male, female))
        if total != male + female:
            t43_failures.append({"area": name, "kind": "sex_total"})
        if name == "Timor-Leste" and sex_ratio != "1,446":
            t43_failures.append({"area": name, "kind": "unexpected_national_sex_ratio"})
    for column in range(3):
        national = int(table43["Timor-Leste"]["values"][column].replace(",", ""))
        subtotal = sum(int(table43[name]["values"][column].replace(",", "")) for name in AREAS)
        if national != subtotal:
            t43_failures.append({"kind": "national_sum", "column": column + 1,
                                 "published": national, "area_sum": subtotal})
    table_audit = [
        {"table": "4.3", "summary_rows": len(table43), "numeric_columns": 6,
         "numeric_summary_cells": len(table43) * 6, "issues": t43_failures},
        audit_nine_columns(table411, ages411, "4.11"),
        audit_nine_columns(table412, ages412, "4.12"),
    ]
    return table43, table411, table412, table_audit


def region_id(name):
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return "TLS:INETL:PHC2022:ADM1:" + re.sub(r"[^A-Z0-9]+", "-", plain.upper()).strip("-")


def int_cell(record, index):
    return int(record["values"][index].replace(",", ""))


def source_record(item, retrieved_at):
    metadata = {
        "tls-inetl-phc2022-main-report": ("INETL 2022 Population and Housing Census Main Report",
            "National Institute of Statistics of Timor-Leste", "2022 census", "Nation, fourteen first-level areas; lower areas vary by table"),
        "tls-law-19-2023-territory": ("Law 19/2023 on territorial administration",
            "Ministry of Justice, Jornal da República", "2023-12-05", "National legal first-level roster"),
        "tls-suco-recognition-2023": ("Ministerial Diploma 19/2023 on suco recognition",
            "Ministry of Justice, Jornal da República", "2023-05-03", "National suco and aldeia recognition"),
        "tls-municipal-plan-procedure-2024": ("Ministerial Diploma 72/2024 on municipal plans",
            "Ministry of Justice, Jornal da República", "2024 procedure", "Municipal planning bodies"),
        "tls-atauro-plan-procedure-2025": ("Ministerial Diploma 33/2025 on Ataúro plans",
            "Ministry of Justice, Jornal da República", "2025 procedure", "Ataúro special first-level division"),
        "tls-dili-pedm-2026-2030": ("Díli municipal strategic plan 2026–2030",
            "Díli Municipal Authority", "2026–2030 plan body", "Díli municipality"),
        "tls-dili-paa-2026": ("Díli 2026 annual action plan and planned budget",
            "Díli Municipal Authority", "2026 annual plan", "Díli municipality"),
        "tls-atauro-plan-draft-2026-2030": ("Ataúro development plan 2026–2030 draft",
            "Administrative Authority of Ataúro", "2026–2030 draft", "Ataúro special first-level division"),
    }
    name, publisher, reference_period, geographic_level = metadata[item["id"]]
    return {"id": item["id"], "name": name,
            "url": item["url"], "catalogue_url": item["catalogue_url"],
            "publisher": publisher, "reference_period": reference_period,
            "geographic_level": geographic_level,
            "status": "ready", "retrieved_at": retrieved_at, "raw_path": item["raw_path"],
            "sha256": item["sha256"], "license": "Official public PDF; redistribution terms to confirm",
            "note": "Original byte length and SHA-256 pinned; selected table cells and document status are separately audited."}


def indicator(ident, name, theme, unit, population, definition, decimals=0, derived=False):
    method = "AreaData ratio of directly reported INETL counts" if derived else \
        "INETL 2022 census directly published table cell"
    return {"id": ident, "name": name, "theme": theme, "unit": unit,
            "display_decimals": decimals, "definition": definition,
            "population": population, "source_id": CENSUS,
            "aggregation": "none", "measurement_method": method}


def document_match(territory, source_id, locator):
    return {"territory_id": territory["id"], "country_id": "TLS",
            "type": territory["type"], "code_system": territory["code_system"],
            "official_code": territory["official_code"],
            "boundary_version": territory["boundary_version"],
            "method": "Source publisher and named first-level jurisdiction matched to the census reporting row; no official code or polygon equivalence asserted.",
            "source_id": source_id, "locator": locator, "checked_at": "2026-09-27"}


def build(project, manifest, table43, table411, table412, table_audit, pages):
    require(all(not table["issues"] for table in table_audit), "Selected table arithmetic mismatch")
    dashboard = project / "data/dashboard.json"
    data = json.loads(dashboard.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "TLS", "Wrong candidate country")
    data["country"]["geography_note"] = (
        "INETL 2022 census first-level reporting areas: 14 names, including Ataúro as a 2022 municipality. "
        "Law 19/2023 later made Ataúro a distinct first-level division and Oe-Cusse Ambeno a special region. "
        "No official code or 2022/2026 compatible polygon is acquired. The initial 2017 13-area "
        "geoBoundaries reference geometry is removed. Census usual residents are distinct from WDI estimates.")
    national = next(t for t in data["territories"] if t["id"] == "TLS")
    national.update({"source_id": CENSUS, "boundary_version": BOUNDARY})
    territories = [national]
    for name in AREAS:
        legal_type = ("Ataúro special first-level division" if name == "Atauro" else
                      "Oe-Cusse Ambeno special administrative region" if name == "Oecusse" else
                      "municipality")
        territories.append({"id": region_id(name), "name": name, "level": "adm1",
                            "type": legal_type, "parent_id": "TLS", "official_code": None,
                            "code_system": "INETL 2022 published reporting name; official geographic code pending",
                            "boundary_version": BOUNDARY, "source_id": CENSUS,
                            "legal_status_source_id": "tls-law-19-2023-territory",
                            "reconciliation_status": "2022 census reporting name matches the distinct first-level jurisdiction in Law 19/2023; official code, exact limits and later lower-level changes pending"})
    by_name = {"Timor-Leste": national, **{t["name"]: t for t in territories[1:]}}
    data["territories"] = territories
    data["boundaries"] = {"type": "FeatureCollection", "features": []}

    sources = {s["id"]: s for s in data["sources"]}
    for item in manifest["sources"]:
        sources[item["id"]] = source_record(item, manifest["retrieved_at"])
    data["sources"] = list(sources.values())

    spec = [
        ("POP_TOTAL", "2022 usual resident population", "Population", "people",
         "All usual residents in private and collective households at midnight 5–6 September 2022",
         "Table 4.3 published population total; different from WDI annual estimate.", 0, False),
        ("AREA", "Published reporting area", "Geography", "km²",
         "Area of INETL Table 4.3 reporting jurisdiction",
         "Published area rounded to whole km²; not an adopted legal boundary geometry.", 0, False),
        ("DENSITY", "Published population density", "Population", "people/km²",
         "Usual residents per square kilometre of the INETL Table 4.3 reported area",
         "Source-published population density, not recomputed from rounded area.", 2, False),
        ("LIT_AGE5_TOTAL", "Private-household population aged 5+", "Education", "people",
         "Usual residents aged five or above in private households",
         "Table 4.11 total; excludes collective quarters and children under five.", 0, False),
        ("LIT_AGE5_LITERATE", "Literate private-household population aged 5+", "Education", "people",
         "Usual residents aged five or above in private households",
         "Table 4.11 general literacy status, literate; source count.", 0, False),
        ("LIT_AGE5_ILLITERATE", "Illiterate private-household population aged 5+", "Education", "people",
         "Usual residents aged five or above in private households",
         "Table 4.11 general literacy status, illiterate; source count.", 0, False),
        ("LIT_AGE5_RATE", "Literate share of private-household population aged 5+", "Education", "%",
         "Usual residents aged five or above in private households",
         "AreaData: 100 × Table 4.11 literate / Table 4.11 total, same row and population.", 2, True),
        ("SCHOOL_AGE3_29_TOTAL", "Private-household population aged 3–29", "Education", "people",
         "Usual residents aged 3–29 in private households",
         "Table 4.12 total; not all residents or all school-age children.", 0, False),
        ("SCHOOL_AGE3_29_ATTENDING", "Aged 3–29 attending school", "Education", "people",
         "Usual residents aged 3–29 in private households",
         "Table 4.12 attending school; source count.", 0, False),
        ("SCHOOL_AGE3_29_NOT_ATTENDING", "Aged 3–29 not attending school", "Education", "people",
         "Usual residents aged 3–29 in private households",
         "Table 4.12 not attending school; source count.", 0, False),
        ("SCHOOL_AGE3_29_ATTEND_RATE", "School attendance share, ages 3–29 in private households", "Education", "%",
         "Usual residents aged 3–29 in private households",
         "AreaData: 100 × Table 4.12 attending / Table 4.12 total. This is not a school enrolment rate.", 2, True),
    ]
    prefix = "TLS_PHC2022_"
    data["indicators"] = [i for i in data["indicators"] if not i["id"].startswith(prefix)]
    data["observations"] = [o for o in data["observations"] if not o["indicator_id"].startswith(prefix)]
    data["indicators"].extend(indicator(prefix + key, name, theme, unit, population,
                                         definition, decimals, derived)
                              for key, name, theme, unit, population, definition,
                                  decimals, derived in spec)
    observations = []

    def add(name, key, value, source_table, column, population_scope, derived=False,
            numerator=None, denominator=None):
        row = {"territory_id": by_name[name]["id"], "indicator_id": prefix + key,
               "period": "2022", "value": value, "status": "observed",
               "source_id": CENSUS, "provenance": "derived_from_source_counts" if derived else "source_reported",
               "population_scope": population_scope,
               "measurement_method": "AreaData ratio of directly reported INETL counts" if derived else
               "INETL 2022 census directly published table cell",
               "boundary_version": BOUNDARY,
               "source_locator": f"Main Report Table {source_table}, row {name}, printed p.{ {'4.3':87,'4.11':table411.get(name,{}).get('report_page'),'4.12':table412.get(name,{}).get('report_page')}[source_table] }, {column}"}
        if derived:
            row.update({"numerator": numerator, "denominator": denominator,
                        "formula": "100 × numerator / denominator"})
        observations.append(row)

    for name in ROSTER:
        pop = int_cell(table43[name], 0)
        area = int_cell(table43[name], 4)
        density = float(table43[name]["values"][5].replace(",", ""))
        add(name, "POP_TOTAL", pop, "4.3", "column Total", "All usual residents in private and collective households")
        add(name, "AREA", area, "4.3", "column Area (Sq. km)", "2022 census published reporting area")
        add(name, "DENSITY", density, "4.3", "column Population density", "2022 census usual residents per published area")
        lit_total, literate, illiterate = (int_cell(table411[name], i) for i in range(3))
        require(lit_total == literate + illiterate and lit_total > 0, f"Literacy row mismatch {name}")
        for key, value, column in (("LIT_AGE5_TOTAL", lit_total, "column Total"),
                                   ("LIT_AGE5_LITERATE", literate, "column Literate"),
                                   ("LIT_AGE5_ILLITERATE", illiterate, "column Illiterate")):
            add(name, key, value, "4.11", column, "Private-household residents aged five or above")
        add(name, "LIT_AGE5_RATE", round(literate / lit_total * 100, 2), "4.11",
            "columns Literate / Total", "Private-household residents aged five or above",
            True, literate, lit_total)
        school_total, attending, not_attending = (int_cell(table412[name], i) for i in range(3))
        require(school_total == attending + not_attending and school_total > 0,
                f"School row mismatch {name}")
        for key, value, column in (("SCHOOL_AGE3_29_TOTAL", school_total, "column Total"),
                                   ("SCHOOL_AGE3_29_ATTENDING", attending, "column Attending school"),
                                   ("SCHOOL_AGE3_29_NOT_ATTENDING", not_attending, "column Not attending school")):
            add(name, key, value, "4.12", column, "Private-household residents aged 3–29")
        add(name, "SCHOOL_AGE3_29_ATTEND_RATE", round(attending / school_total * 100, 2),
            "4.12", "columns Attending school / Total",
            "Private-household residents aged 3–29", True, attending, school_total)
    require(len(observations) == 165, "Adopted observation count changed")
    data["observations"].extend(observations)

    data["documents"] = [d for d in data["documents"] if not d["id"].startswith("tls-")]
    data["documents"].extend([
        {"id": "tls-census2022-report", "territory_id": "TLS", "category": "reference",
         "kind": "census_report", "title": "INETL 2022 Population and Housing Census Main Report",
         "url": sources[CENSUS]["url"], "source_id": CENSUS, "period": "2022",
         "availability": "body_acquired", "official_status": "unverified",
         "note": "204-page report acquired. Tables 4.3, 4.11 and 4.12 selected; image-only post/suco Tables 4.1/4.2 and other tables remain unassessed."},
        {"id": "tls-law19-2023-first-level", "territory_id": "TLS", "category": "reference",
         "kind": "territorial_law", "title": "Law 19/2023: first-level territorial divisions",
         "url": sources["tls-law-19-2023-territory"]["url"],
         "source_id": "tls-law-19-2023-territory", "period": "2023",
         "availability": "body_acquired", "official_status": "unverified",
         "note": "Articles 1, 4 and 4-A distinguish Ataúro, 12 municipalities and Oe-Cusse Ambeno special region. This does not supply census-compatible polygons or official codes."},
        {"id": "tls-municipal-plan-procedure", "territory_id": "TLS", "category": "reference",
         "kind": "planning_guidance", "title": "Ministerial Diploma 72/2024: municipal development-plan procedure",
         "url": sources["tls-municipal-plan-procedure-2024"]["url"],
         "source_id": "tls-municipal-plan-procedure-2024", "period": "2024",
         "availability": "body_acquired", "official_status": "unverified",
         "note": "Procedure requires Council of Ministers resolution for approval. Full applicability and subsequent amendments pending."},
        {"id": "tls-dili-pedm-2026-2030-doc", "territory_id": region_id("Dili"),
         "category": "plan", "kind": "municipal_development_plan",
         "title": "Díli municipal strategic development plan 2026–2030",
         "url": sources["tls-dili-pedm-2026-2030"]["url"],
         "source_id": "tls-dili-pedm-2026-2030", "period": "2026–2030",
         "availability": "content_extracted", "official_status": "unverified",
         "note": "347-page body and executive summary acquired. Summary says approved, but the required Council of Ministers approval resolution has not been independently located. Full objectives/results are not semantically audited."},
        {"id": "tls-dili-paa-2026-doc", "territory_id": region_id("Dili"),
         "category": "budget", "kind": "annual_action_plan",
         "title": "Díli 2026 annual action plan and proposed budget",
         "url": sources["tls-dili-paa-2026"]["url"],
         "source_id": "tls-dili-paa-2026", "period": "2026",
         "target_period": {"label": "2026", "kind": "calendar_year", "start": "2026-01-01", "end": "2026-12-31"},
         "availability": "content_verified", "official_status": "unverified",
         "territory_match": document_match(by_name["Dili"], "tls-law-19-2023-territory",
             "Law 19/2023 Article 4: Município de Díli; source document header: Autoridade Municipal de Dili"),
         "content": {"summary": "Published 2026 annual action plan lists a total planned budget of US$19,502,642. It is a plan figure, not actual spending or plan achievement.",
             "evidence": {"source_id": "tls-dili-paa-2026", "locator": "PDF p.8, Total Orsamentu row", "checked_at": "2026-09-27", "authority": "Díli Municipal Authority"}},
         "findings": [{"kind": "budget", "label": "2026 total planned budget",
                       "definition": "Total Orsamentu in the published Díli annual action plan; planned allocation, not actual expenditure",
                       "scope": "Díli Municipal Authority, all listed programmes and budget categories",
                       "period": {"label": "2026", "kind": "calendar_year", "start": "2026-01-01", "end": "2026-12-31"},
                       "value": 19502642, "value_status": "observed", "unit": "USD",
                       "evidence": {"source_id": "tls-dili-paa-2026", "locator": "PDF p.8/8, Total Orsamentu = $19,502,642", "checked_at": "2026-09-27"}}],
         "note": "Full programme-by-programme meaning and formal approval record pending; do not treat this total as spending."},
        {"id": "tls-atauro-plan-procedure-doc", "territory_id": region_id("Atauro"),
         "category": "reference", "kind": "planning_guidance",
         "title": "Ministerial Diploma 33/2025: Ataúro development-plan procedure",
         "url": sources["tls-atauro-plan-procedure-2025"]["url"],
         "source_id": "tls-atauro-plan-procedure-2025", "period": "2025",
         "availability": "body_acquired", "official_status": "unverified",
         "note": "Distinct Ataúro procedure includes Council of Ministers resolution for plan approval; later approvals not inferred."},
        {"id": "tls-atauro-plan-draft-doc", "territory_id": region_id("Atauro"),
         "category": "plan", "kind": "development_plan_draft",
         "title": "Ataúro development plan 2026–2030, published draft",
         "url": sources["tls-atauro-plan-draft-2026-2030"]["url"],
         "source_id": "tls-atauro-plan-draft-2026-2030", "period": "2026–2030",
         "availability": "content_extracted", "official_status": "unverified",
         "note": "172-page published PDF filename begins Ezbosu (draft); a Council of Ministers approval resolution was not located. Do not present as an adopted plan or its estimated budget as approved."}
    ])
    data["planning"] = {"title": "Municipal and special-area plans and source evidence",
        "purpose": "Review 2022 local census baselines and the selected jurisdiction's own plan, planned budget, actual execution and evaluation separately.",
        "system": {"label": "Municipal development plans and Ataúro's distinct procedure",
            "scope": "Ministerial Diploma 72/2024 provides the municipal plan process; Diploma 33/2025 provides a separate Ataúro process. The Council of Ministers approval decision must be verified per plan.",
            "cycle": "Díli and Ataúro publish documents labelled 2026–2030; no nationwide fixed renewal period or approval state is inferred.",
            "source_ids": ["tls-municipal-plan-procedure-2024", "tls-atauro-plan-procedure-2025", "tls-law-19-2023-territory"]},
        "sections": [{"id": ident, "label": label} for ident, label in (
            ("plan", "Development plan"), ("budget", "Annual plan and budget"),
            ("implementation", "Execution and actual spending"),
            ("evaluation", "Official evaluation"), ("reference", "Census and legal references"))]}
    data["analysis"]["comparisons"] = [{
        "parent_id": "TLS", "member_ids": [region_id(name) for name in AREAS],
        "label": "14 INETL 2022 first-level reporting areas",
        "membership_note": "Complete 14-area census Table 4.3 roster, confirmed against Law 19/2023 first-level names; Ataúro and Oe-Cusse have distinct later legal types. Values are direct INETL cells or labelled ratios of same-row counts. Polygons and official codes remain pending.",
        "source_ids": [CENSUS, "tls-law-19-2023-territory"]}]
    data["analysis"]["terminal_territory_ids"] = [region_id(name) for name in AREAS]
    data["analysis"]["default_indicator_id"] = prefix + "POP_TOTAL"
    data["analysis"]["population_context"] = {"primary_indicator_id": prefix + "POP_TOTAL",
        "reference_indicator_id": "SP.POP.TOTL"}
    data["analysis"]["latest_values_only"] = True
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "inetl-phc2022-first-level-2026-09-27"]))
    data["collection"]["notes"] = [
        "Eight official PDF originals hash-pinned: INETL 2022 Census, Law 19/2023, 2023 suco recognition, municipal/Ataúro plan procedures, and Díli/Ataúro plans and annual action plan.",
        "Three census tables adopted only at national and all 14 first-level reporting areas; 2022 census values do not describe 2026 population. Table 4.1/4.2 post/suco cells are raster images and remain priority_unassessed; 2023 suco roster differs from the 2022 census roster.",
        "INETL says cells with fewer than four observations are suppressed with a dash (report p.21). The nine suppressed age cells in Table 4.11 remain hidden and are never recovered from totals.",
        "Table 4.3 national sex-ratio cell prints 1,446. Its national and Baucau male/female cells differ by ±25 from raster Table 4.1; sex counts/ratio are not adopted. Published total population, area and density are kept without fabricating a polygon.",
        "Díli's 2026 annual action plan lists a planned USD 19,502,642, not execution. Díli/Ataúro development-plan bodies are acquired; Council of Ministers approvals, actual spending and official evaluations are not confirmed."]
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "The 14 first-level names are matched to Law 19/2023, but official IDs and 2022/2026 compatible polygons are not acquired; initial 2017 13-unit geoBoundaries geometry removed. 2022 post/suco roster differs from 2023 legal recognition.",
         "next_action": "Acquire official versioned codes, geometry and 2022-to-current administrative crosswalk before showing internal post/suco maps or historical comparison."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "National and 14 first-level rows from Tables 4.3, 4.11, 4.12 are connected. Image-only Tables 4.1/4.2 and other 21 basic tables remain unassessed; published sex cells conflict in Tables 4.1/4.3. Nine literacy-age cells are privacy-suppressed.",
         "next_action": "Independently verify the post/suco tables and all remaining numeric columns without recovering suppressed cells; document official geography and resolve conflicting sex totals."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Díli 2026–2030 plan and 2026 annual action plan, Ataúro 2026–2030 draft and applicable plan procedures acquired. Other jurisdictions, formal Council of Ministers approval, actual spending, implementation and evaluation remain unverified.",
         "next_action": "Locate resolutions and local plans/budgets/execution/evaluations by responsible authority; verify document text and period separately."}
    ])
    dashboard.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog = [{"table": f"3.{i}", "disposition": "priority_unassessed",
                "numeric_columns": None} for i in range(1, 10)]
    catalog.extend({"table": f"4.{i}",
                    "disposition": "selected_first_level_columns" if i in (3, 11, 12) else
                    "priority_unassessed",
                    "numeric_columns": 6 if i == 3 else 9 if i in (11, 12) else None}
                   for i in range(1, 25))
    audit = {"country_id": "TLS", "candidate_status": "partial_unpublished",
        "retrieved_at": manifest["retrieved_at"],
        "originals": [{key: item[key] for key in ("id", "raw_path", "bytes", "sha256")}
                      for item in manifest["sources"]],
        "pdf_pages": pages, "indexed_table_catalog": catalog,
        "catalog_scope": "All 33 numbered tables in the report contents (3.1–3.9 and 4.1–4.24) are registered. Numeric-column details are confirmed only for adopted Tables 4.3, 4.11, 4.12; null means not assessed, not zero columns.",
        "selected_table_audits": table_audit,
        "selection": {"territories": 15, "indicators": len(spec),
                      "direct_observations": 15 * 9, "derived_observations": 15 * 2,
                      "total_observations": len(observations)},
        "source_conflicts": [
            {"kind": "sex_counts", "where": "national and Baucau",
             "table_4_3": {"national_male": int_cell(table43["Timor-Leste"], 1),
                           "national_female": int_cell(table43["Timor-Leste"], 2),
                           "baucau_male": int_cell(table43["Baucau"], 1),
                           "baucau_female": int_cell(table43["Baucau"], 2)},
             "table_4_1_visual_transcription": {"national_male": 681229,
                 "national_female": 660508, "baucau_male": 68117,
                 "baucau_female": 66761, "pdf_pages": [86, 87]},
             "disposition": "unadopted_pending_independent_cell_review"},
            {"kind": "national_sex_ratio", "table_4_3_printed": table43["Timor-Leste"]["values"][3],
             "disposition": "unadopted_invalid_ratio_pending_source_correction"}],
        "suppression_rule": {"source": "INETL Main Report printed p.21/PDF p.37",
            "meaning": "Cells fewer than four observations suppressed with en dash; no reconstruction"},
        "excluded_geometry": "2017 geoBoundaries 13 shapes do not represent the 14-area 2022 census roster",
        "planning_boundary": "Published bodies are not automatic proof of approval, actual spending or evaluation"}
    evidence = project / "evidence/TLS_PHC2022_AUDIT.json"
    evidence.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = pinned_sources(args.project, manifest)
    reader = PdfReader(str(paths[CENSUS]))
    require(len(reader.pages) == 204, "2022 census report page count changed")
    table43, table411, table412, audit = audit_pdf(paths[CENSUS])
    if args.audit_only:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return
    pages = {item["id"]: len(PdfReader(str(paths[item["id"]])).pages)
             for item in manifest["sources"]}
    result = build(args.project, manifest, table43, table411, table412, audit, pages)
    print(json.dumps({"country": "TLS", "status": "partial_unpublished",
                      "selection": result["selection"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

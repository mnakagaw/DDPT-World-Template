#!/usr/bin/env python3
"""Integrate checked Armenia census/2026 population and Ashtarak originals.

Replays from the saved bootstrap dataset. The 2005 geoBoundaries shapes are
withheld because they have not been matched to the 2022/2026 reporting areas.
This is an explicitly partial local candidate, not a publication gate.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
EVIDENCE = PROJECT / "evidence"
REFERENCE = PROJECT / "reference"
DATA = PROJECT / "data" / "dashboard.json"
BOOTSTRAP = REFERENCE / "dashboard-bootstrap.json"
CLASSIFIER = PROJECT / "raw" / "official-planning" / "administrative-classifier-2026.html"
BULLETIN = PROJECT / "raw" / "armstat-population-bulletin" / "population_01_01_26.pdf"
BULLETIN_TEXT = PROJECT / "raw" / "armstat-population-bulletin" / "population_01_01_26.txt"
CENSUS = EVIDENCE / "ARM_CENSUS_2022_MARZ_POPULATION_EXTRACT.json"
OFFICIAL_RECEIPTS = EVIDENCE / "ARM_OFFICIAL_PLANNING_RECEIPTS.json"
BULLETIN_RECEIPTS = EVIDENCE / "ARM_POPULATION_BULLETIN_RECEIPTS.json"
YEREVAN_RECEIPTS = EVIDENCE / "ARM_YEREVAN_PLANNING_RECEIPTS.json"
GEOPORTAL_RECEIPTS = EVIDENCE / "ARM_GEOPORTAL_RECEIPTS.json"
MARZ_THEME_RECEIPTS = EVIDENCE / "ARM_MARZ_THEME_RECEIPTS.json"
MARZ_THEME_INVENTORY = EVIDENCE / "ARM_MARZ_THEME_INVENTORY.json"
CODE_SYSTEM = "ARM HD 002-2023, 2026-02-15 classifier; nine digits including check digit"
EDITION = "ARM-HD002-2023-2026-02-15"
CENSUS_SOURCE = "armstat-census-2022-pxweb-marzes"
BULLETIN_SOURCE = "armstat-permanent-population-2026-01-01"
CLASSIFIER_SOURCE = "arm-economy-ministry-admin-classifier-2026"
LAW_SOURCE = "arm-local-self-government-law-2026"
PLAN_DECISION_SOURCE = "arm-ashtarak-plan-decision-2022-2026"
PLAN_PDF_SOURCE = "arm-ashtarak-plan-pdf-2022-2026"
BUDGET_DECISION_SOURCE = "arm-ashtarak-budget-decision-2026"
BUDGET_XLS_SOURCE = "arm-ashtarak-budget-xls-2026"
YEREVAN_LAW_SOURCE = "arm-yerevan-local-self-government-law-2026"
YEREVAN_FIVE_DECISION_SOURCE = "arm-yerevan-five-year-plan-decision-2024-2028"
YEREVAN_FIVE_PDF_SOURCE = "arm-yerevan-five-year-plan-pdf-2024-2028"
YEREVAN_ANNUAL_DECISION_SOURCE = "arm-yerevan-annual-program-decision-2026"
YEREVAN_ANNUAL_PDF_SOURCE = "arm-yerevan-annual-program-pdf-2026"
YEREVAN_REPORT_DECISION_SOURCE = "arm-yerevan-implementation-report-decision-2025"
YEREVAN_REPORT_PDF_SOURCE = "arm-yerevan-implementation-report-pdf-2025"
YEREVAN_BUDGET_SOURCE = "arm-yerevan-budget-2026-incorporated"
YEREVAN_BUDGET_AMENDMENT_SOURCE = "arm-yerevan-budget-2026-september-amendment"
YEREVAN_EXECUTION_SOURCE = "arm-yerevan-budget-execution-2025-decision"
GEOPORTAL_SOURCE = "arm-geoportal-admin-boundary-map"
POVERTY_METHOD_SOURCE = "armstat-poverty-incidence-quality-declaration"
MARZ_THEME_SPECS = {
    "schools": {"source_id": "armstat-marz-state-schools-2025", "indicator_id": "ARM_MARZ_STATE_SCHOOLS",
                "name": "State general schools", "theme": "Education", "unit": "schools", "decimals": 0,
                "definition": "Published number of state general schools in Armstat's 2025 marz table. Source time convention and institution register details require further review; not a count of all public and private schools.",
                "population": "state general school institutions", "method": "armstat_pxweb_reported_institution_count_method_detail_unverified", "family": "administrative", "additive": True},
    "hospitals": {"source_id": "armstat-marz-hospitals-2025", "indicator_id": "ARM_MARZ_HOSPITALS",
                  "name": "Hospitals reported in health system table", "theme": "Health", "unit": "hospitals", "decimals": 0,
                  "definition": "Published 'Number of hospitals' in Armstat's 2025 health-system marz table. Facility scope and ownership should be checked in the sector metadata; this is not a hospital-bed or service-access rate.",
                  "population": "hospital institutions in source table", "method": "armstat_pxweb_reported_hospital_count_method_detail_unverified", "family": "administrative", "additive": True},
    "consumer_water": {"source_id": "armstat-marz-consumer-water-2024", "indicator_id": "ARM_MARZ_CONSUMER_WATER",
                       "name": "Water delivered to consumers", "theme": "Water and housing", "unit": "thousand cubic metres", "decimals": 1,
                       "definition": "Published 'volume of water given to consumers, total' in the 2024 marz water-supply-system table, in thousand cubic metres. This is system volume, not household drinking-water access or per-person consumption.",
                       "population": "consumers served by the reported water-supply system", "method": "armstat_pxweb_reported_water_volume_method_detail_unverified", "family": "administrative", "additive": True},
    "poverty": {"source_id": "armstat-marz-poverty-2024", "indicator_id": "ARM_MARZ_POOR_POPULATION_SHARE",
                "name": "Poor population share, 2024 ILCS", "theme": "Livelihood and poverty", "unit": "percent", "decimals": 1,
                "definition": "Armstat's 2024 'Poor population' percentage. The linked quality declaration defines poor persons by per-adult consumption below the upper common poverty line; the table warns that 2024 survey weights were recalibrated against 2022-census-based population records, making 2024 rates incomparable with 2022–2023.",
                "population": "Integrated Living Conditions Survey weighted persons", "method": "armstat_ilcs_2024_recalibrated_survey", "family": "survey", "additive": False},
    "street_length": {"source_id": "armstat-marz-street-length-2024", "indicator_id": "ARM_MARZ_CITY_STREET_LENGTH",
                      "name": "Length of streets and crossings", "theme": "Infrastructure", "unit": "km", "decimals": 1,
                      "definition": "Published 2024 total length of streets and crossings by marz in Armstat's urban road-economy category. This does not represent all roads or rural access.",
                      "population": "reported streets and crossings in city/urban road economy", "method": "armstat_pxweb_reported_street_length_method_detail_unverified", "family": "administrative", "additive": True},
}
DATE = "2026-09-27"


def clean(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()


def records_classifier() -> list[dict]:
    source = CLASSIFIER.read_text(encoding="utf-8")
    rows = []
    for row in re.finditer(r"<TR\b[^>]*>(.*?)</TR>", source, re.I | re.S):
        cells = [clean(item) for item in re.findall(r"<TD\b[^>]*>(.*?)</TD>", row.group(1), re.I | re.S)]
        if not cells or not re.fullmatch(r"\d{2}\s+\d{3}\s+\d{3}", cells[0]):
            continue
        if len(cells) != 6 or not re.fullmatch(r"\d", cells[1]):
            raise ValueError(f"Unexpected official code row: {cells}")
        short_code = cells[0].replace(" ", "")
        if cells[2]:
            kind, name = "marz", cells[2]
        elif cells[3]:
            kind, name = "community", cells[3]
        else:
            kind, name = "settlement_or_yerevan_district", cells[4]
        rows.append({"official_code": short_code + cells[1], "code_without_check_digit": short_code,
                     "kind": kind, "name_hy": name, "marz_prefix": short_code[:2],
                     "community_prefix": short_code[:5], "note": cells[5]})
    if len(rows) != 1094 or Counter(item["kind"] for item in rows)["marz"] != 10:
        raise ValueError(f"Classifier shape changed: {len(rows)} rows, {Counter(item['kind'] for item in rows)}")
    return rows


def numeric(text: str) -> float | None:
    if text == "-":
        return None
    if not re.fullmatch(r"\d[\d ]*\.\d", text):
        raise ValueError(f"Unexpected bulletin numeric cell {text!r}")
    return float(text.replace(" ", ""))


def normalize_community_hy(label: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\s*համայնք.*$", "", label)).strip().casefold()


def bulletin_rows() -> tuple[list[dict], list[dict]]:
    pages = BULLETIN_TEXT.read_text(encoding="utf-8").split("\f")
    if len([p for p in pages if p.strip()]) != 11:
        raise ValueError("Expected 11 nonempty official bulletin pages")
    primary, inventory = [], []
    marz_prefix = "01"
    for page_index in range(3, 7):
        for line_number, line in enumerate(pages[page_index].splitlines(), 1):
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) != 5 or any(not re.fullmatch(r"\d[\d ]*\.\d|-", part) for part in parts[1:4]):
                continue
            label_hy, total, urban, rural, label_en = parts
            if label_en.isupper() and label_en != "C.YEREVAN":
                marz_prefix = f"{int(marz_prefix) + 1:02}"
                kind = "marz"
            elif "համայնք" in label_hy:
                kind = "community"
            elif label_en == "C.YEREVAN":
                kind = "yerevan_community"
            elif label_hy.startswith("ք.") or label_hy.startswith("ք. "):
                kind = "town_within_community"
            else:
                raise ValueError(f"Unclassified bulletin numeric row page {page_index+1}: {parts}")
            row = {"page": page_index + 1, "text_line": line_number, "kind": kind,
                   "marz_prefix": marz_prefix, "name_hy_source": label_hy, "name_en_source": label_en,
                   "total_thousand": numeric(total), "urban_thousand": numeric(urban), "rural_thousand": numeric(rural)}
            row["disposition"] = "adopted_direct" if kind in {"marz", "community", "yerevan_community"} else "withheld_internal_settlement_no_planning_area_geometry"
            inventory.append(row)
            if row["disposition"] == "adopted_direct":
                primary.append(row)
    national_line = next((line for line in pages[7].splitlines() if "3 096.9" in line), None)
    if national_line is None:
        raise ValueError("Could not locate national official row on page 8")
    parts = re.split(r"\s{2,}", national_line.strip())
    if parts[1:4] != ["3 096.9", "1 980.7", "1 116.2"]:
        raise ValueError(f"National total changed: {parts}")
    national = {"page": 8, "text_line": pages[7].splitlines().index(national_line) + 1,
                "kind": "national", "name_hy_source": parts[0], "name_en_source": "The Republic of Armenia",
                "total_thousand": numeric(parts[1]), "urban_thousand": numeric(parts[2]),
                "rural_thousand": numeric(parts[3]), "disposition": "adopted_direct"}
    primary.insert(0, national)
    inventory.append(national)
    for page_index, kind in ((7, "duplicate_national_and_marz_table"), (8, "yerevan_internal_district")):
        for line_number, line in enumerate(pages[page_index].splitlines(), 1):
            parts = re.split(r"\s{2,}", line.strip())
            if page_index == 7 and len(parts) == 5 and all(re.fullmatch(r"\d[\d ]*\.\d|-", p) for p in parts[1:4]):
                inventory.append({"page": page_index + 1, "text_line": line_number, "kind": kind, "source_cells": parts,
                                  "disposition": "duplicate_of_pages_4_to_7"})
            elif page_index == 8 and len(parts) == 3 and re.fullmatch(r"\d[\d ]*\.\d", parts[1]):
                inventory.append({"page": page_index + 1, "text_line": line_number, "kind": kind, "source_cells": parts,
                                  "disposition": "withheld_internal_yerevan_district_not_separate_community_plan_unit"})
    if Counter(row["kind"] for row in primary) != {"national": 1, "yerevan_community": 1, "marz": 10, "community": 69}:
        raise ValueError(f"Unexpected annual population coverage: {Counter(row['kind'] for row in primary)}")
    return primary, inventory


def receipt(path: Path, suffix: str) -> dict:
    records = json.loads(path.read_text(encoding="utf-8"))
    return next(row for row in records if row["path"].endswith(suffix))


def source(source_id: str, name: str, url: str, publisher: str, reference_period: str, geographic_level: str,
           receipt_record: dict, note: str) -> dict:
    return {"id": source_id, "name": name, "url": url, "publisher": publisher,
            "reference_period": reference_period, "geographic_level": geographic_level,
            "status": "ready", "retrieved_at": receipt_record.get("retrieved_at_utc", DATE),
            "sha256": receipt_record["sha256"], "raw_path": receipt_record["path"],
            "license": "official_publication_terms_review_required", "note": note}


def main() -> None:
    REFERENCE.mkdir(exist_ok=True)
    if not BOOTSTRAP.exists():
        shutil.copy2(DATA, BOOTSTRAP)
    dataset = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    if len(dataset["territories"]) != 12 or len(dataset["observations"]) != 312:
        raise ValueError("Bootstrap changed; inspect rather than overwrite")
    classifier_rows = records_classifier()
    primary, inventory = bulletin_rows()
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / "ARM_OFFICIAL_CODE_CLASSIFIER_2026.json").write_text(
        json.dumps({"source_url": "https://www.arlis.am/hy/acts/220427", "edition": EDITION,
                    "row_count": len(classifier_rows), "kind_counts": Counter(r["kind"] for r in classifier_rows),
                    "rows": classifier_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "ARM_POPULATION_2026_TABLE_INVENTORY.json").write_text(
        json.dumps({"source_url": "https://www.armstat.am/file/article/population_01_01_26.pdf",
                    "unit": "thousand persons, one decimal, source rounded", "rows": inventory}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    classifier_marzes = {row["marz_prefix"]: row for row in classifier_rows if row["kind"] == "marz"}
    classifier_communities = {(row["marz_prefix"], row["name_hy"].casefold()): row
                              for row in classifier_rows if row["kind"] == "community"}
    annual_marzes = {row["marz_prefix"]: row for row in primary if row["kind"] == "marz"}
    annual_communities = [row for row in primary if row["kind"] == "community"]
    if set(classifier_marzes) != set(annual_marzes):
        raise ValueError("Classifier and bulletin marz coverage differs")
    if len(classifier_communities) != 70 or len(annual_communities) != 69:
        raise ValueError("Unexpected official community counts")
    for row in annual_communities:
        key = (row["marz_prefix"], normalize_community_hy(row["name_hy_source"]))
        if key not in classifier_communities:
            raise ValueError(f"Unmatched community: {row}")
        row["official_code"] = classifier_communities[key]["official_code"]
    yerevan = next(row for row in classifier_rows if row["kind"] == "community" and row["marz_prefix"] == "01")
    if yerevan["name_hy"] != "Երևան":
        raise ValueError("Yerevan official community code changed")
    if {row["official_code"] for row in annual_communities} != {
        row["official_code"] for row in classifier_rows if row["kind"] == "community" and row["marz_prefix"] != "01"
    }:
        raise ValueError("2026 bulletin does not cover all classified communities")

    national = dataset["territories"][0]
    dataset["territories"] = [national]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    marz_id, community_id = {}, {}
    yid = f"ARM:community:{yerevan['official_code']}"
    dataset["territories"].append({"id": yid, "name": "Yerevan", "level": "adm1", "type": "community",
                                    "parent_id": "ARM", "official_code": yerevan["official_code"],
                                    "code_system": CODE_SYSTEM, "boundary_version": EDITION, "source_id": CLASSIFIER_SOURCE,
                                    "native_name": yerevan["name_hy"], "geometry_status": "official_polygon_not_verified"})
    community_id[("01", yerevan["name_hy"].casefold())] = yid
    for prefix in sorted(classifier_marzes):
        row = classifier_marzes[prefix]
        annual = annual_marzes[prefix]
        if row["name_hy"].casefold() != annual["name_hy_source"].casefold():
            raise ValueError(f"Marz Armenian name mismatch: {row} vs {annual}")
        mid = f"ARM:marz:{row['official_code']}"
        marz_id[prefix] = mid
        dataset["territories"].append({"id": mid, "name": annual["name_en_source"].title(),
                                        "level": "adm1", "type": "marz", "parent_id": "ARM",
                                        "official_code": row["official_code"], "code_system": CODE_SYSTEM,
                                        "boundary_version": EDITION, "source_id": CLASSIFIER_SOURCE,
                                        "native_name": row["name_hy"], "geometry_status": "official_polygon_not_verified"})
    for row in annual_communities:
        code = row["official_code"]
        cid = f"ARM:community:{code}"
        community_id[(row["marz_prefix"], normalize_community_hy(row["name_hy_source"]))] = cid
        dataset["territories"].append({"id": cid,
                                        "name": re.sub(r"^t\.", "", row["name_en_source"]).removesuffix(" community").removesuffix(" community1").strip(),
                                        "level": "community", "type": "community", "parent_id": marz_id[row["marz_prefix"]],
                                        "official_code": code, "code_system": CODE_SYSTEM, "boundary_version": EDITION,
                                        "source_id": CLASSIFIER_SOURCE, "native_name": normalize_community_hy(row["name_hy_source"]),
                                        "geometry_status": "official_polygon_not_verified"})
    if len(dataset["territories"]) != 81:
        raise ValueError("Expected national + 10 marz + 70 community records")

    census_receipts = json.loads((EVIDENCE / "ARM_CENSUS_2022_RECEIPTS.json").read_text(encoding="utf-8"))
    census_receipt = next(r for r in census_receipts if r["path"].endswith("PS-pp-1-1-2-2022-total.html"))
    pop_receipt = receipt(BULLETIN_RECEIPTS, "population_01_01_26.pdf")
    classifier_receipt = receipt(OFFICIAL_RECEIPTS, "administrative-classifier-2026.html")
    law_receipt = receipt(OFFICIAL_RECEIPTS, "local-self-government-law-2026.html")
    plan_decision_receipt = receipt(OFFICIAL_RECEIPTS, "ashtarak-plan-decision-2022-2026.html")
    plan_pdf_receipt = receipt(OFFICIAL_RECEIPTS, "ashtarak-plan-2022-2026.pdf")
    budget_decision_receipt = receipt(OFFICIAL_RECEIPTS, "ashtarak-budget-decision-2026.html")
    budget_xls_receipt = receipt(OFFICIAL_RECEIPTS, "ashtarak-budget-2026-annexes.xls")
    yr = lambda filename: receipt(YEREVAN_RECEIPTS, filename)
    geo_receipt = receipt(GEOPORTAL_RECEIPTS, "map_geoportal.html")
    sources = [
        source(CENSUS_SOURCE, "2022 population census, permanent population by marz", "https://statbank.armstat.am/pxweb/en/ArmStatBank/ArmStatBank__2%20Population%20and%20social%20processes__20%20Census/PS-pp-1-1-2.px/", "Statistical Committee of Armenia", "2022 census", "national_and_adm1", census_receipt,
               "Direct PxWeb response, all marzes total settlement/sex. Source table lists 2001 and 2011 too; these were not extracted here. Census population is distinct from WDI midyear de facto estimates."),
        source(BULLETIN_SOURCE, "Permanent population on 1 January 2026 (2022 census based)", pop_receipt["url"], "Statistical Committee of Armenia", "2026-01-01", "national_marz_community", pop_receipt,
               "Pages 4–9 in thousand persons, one decimal. Current annual count/estimate based on 2022 census plus vital and migration registers with statistical adjustment; not direct 2022 census counts. Includes 2025 Khoy merger footnote."),
        source(CLASSIFIER_SOURCE, "2026 administrative-territorial classifier, Order 143-N", classifier_receipt["url"], "Ministry of Economy of Armenia / ARLIS", "effective 2026-02-15", "marz_community_settlement", classifier_receipt,
               "Official HD 002-2023 amendment gives nine-digit code with check digit; 10 marzes, Yerevan and 69 other communities matched to 2026 bulletin by Armenian name and parent. Polygon edition not established."),
        source(LAW_SOURCE, "Local Self-Government Law, current Armenian incorporation", law_receipt["url"], "ARLIS", "as checked 2026-09-27", "national_legal", law_receipt,
               "Articles 11(5), 82, 82.1, 83, 84, 91: community plan, annual work plan, budget, participation and publication. Older English translation has obsolete four-year language."),
        source(PLAN_DECISION_SOURCE, "Ashtarak Council Decision 194-N approving 2022–2026 plan", plan_decision_receipt["url"], "Ashtarak Council / ARLIS", "2022-2026", "Ashtarak community", plan_decision_receipt,
               "Decision dated 2022-12-28, officially published 2023-01-13, recorded effective from 2023-01-14."),
        source(PLAN_PDF_SOURCE, "Ashtarak 2022–2026 five-year development plan annex", plan_pdf_receipt["url"], "Ashtarak Council / ARLIS", "2022-2026", "Ashtarak community", plan_pdf_receipt,
               "59-page PDF annex; contents and selected pages checked. Its 2026 projections are not 2026 execution."),
        source(BUDGET_DECISION_SOURCE, "Ashtarak Council Decision 170-N approving 2026 budget", budget_decision_receipt["url"], "Ashtarak Council / ARLIS", "2026", "Ashtarak community", budget_decision_receipt,
               "Decision dated 2025-12-10, published 2026-01-22, recorded effective from 2026-01-23. Approved plan amounts, not execution."),
        source(BUDGET_XLS_SOURCE, "Ashtarak approved 2026 budget annexes, original XLS", budget_xls_receipt["url"], "Ashtarak Council / ARLIS", "2026", "Ashtarak community", budget_xls_receipt,
               "Legacy XLS has 13 worksheets with detail and chart duplicates. High-level revenue/expenditure/balance cells were checked against Decision 170-N; other numeric cells remain unassessed."),
        source(YEREVAN_LAW_SOURCE, "Law on Local Self-Government in Yerevan, current incorporation", yr("yerevan-special-local-government-law.html")["url"], "ARLIS", "as checked 2026-09-27", "Yerevan legal", yr("yerevan-special-local-government-law.html"),
               "Yerevan has a distinct local-government law; current incorporation Article 70 covers development programs. Do not apply general community procedure without checking this special law."),
        source(YEREVAN_FIVE_DECISION_SOURCE, "Yerevan Council Decision 46-A approving 2024–2028 development plan", yr("yerevan-five-year-plan-2024-2028-decision.html")["url"], "Yerevan Council / ARLIS", "2024-2028", "Yerevan community", yr("yerevan-five-year-plan-2024-2028-decision.html"),
               "Decision 2023-12-26, official effective 2023-12-29; article and later modifications require separate checks."),
        source(YEREVAN_FIVE_PDF_SOURCE, "Yerevan 2024–2028 development plan annex", yr("yerevan-five-year-plan-2024-2028.pdf")["url"], "Yerevan Council / ARLIS", "2024-2028", "Yerevan community", yr("yerevan-five-year-plan-2024-2028.pdf"),
               "52-page approved annex; cover and contents checked. Numerical program targets remain unassessed."),
        source(YEREVAN_ANNUAL_DECISION_SOURCE, "Yerevan Council Decision 460-A approving 2026 annual program", yr("yerevan-annual-program-2026-decision.html")["url"], "Yerevan Council", "2026", "Yerevan community", yr("yerevan-annual-program-2026-decision.html"),
               "Council decision 2025-12-23 approves the 2026 program."),
        source(YEREVAN_ANNUAL_PDF_SOURCE, "Yerevan 2026 annual development program annex", yr("yerevan-annual-program-2026.pdf")["url"], "Yerevan Council", "2026", "Yerevan community", yr("yerevan-annual-program-2026.pdf"),
               "34-page annex; cover and narrative checked. Numeric targets remain unassessed."),
        source(YEREVAN_REPORT_DECISION_SOURCE, "Yerevan Council Decision 513-A taking note of 2025 program implementation report", yr("yerevan-program-2025-implementation-report-decision.html")["url"], "Yerevan Council", "2025", "Yerevan community", yr("yerevan-program-2025-implementation-report-decision.html"),
               "Council decision 2026-03-12 says 'take note of' the mayor's report; this is not a council finding that all targets were achieved."),
        source(YEREVAN_REPORT_PDF_SOURCE, "Yerevan 2025 development program implementation report", yr("yerevan-program-2025-implementation-report.pdf")["url"], "Yerevan Council", "2025", "Yerevan community", yr("yerevan-program-2025-implementation-report.pdf"),
               "36-page annex, cover and introduction checked; project-level quantitative claims remain unassessed."),
        source(YEREVAN_BUDGET_SOURCE, "Yerevan 2026 budget, September 2026 incorporation", yr("yerevan-budget-2026-current-decision.html")["url"], "Yerevan Council / ARLIS", "2026", "Yerevan community", yr("yerevan-budget-2026-current-decision.html"),
               "Decision 483-N in force as incorporated from 2026-09-12; annexes were amended, and current budget amounts are not adopted until annex comparison."),
        source(YEREVAN_BUDGET_AMENDMENT_SOURCE, "Yerevan Council Decision 643-N amending 2026 budget annexes", yr("yerevan-budget-2026-september-amendment.html")["url"], "Yerevan Council / ARLIS", "2026-09-12 onward", "Yerevan community", yr("yerevan-budget-2026-september-amendment.html"),
               "Amends annexes 1, 2, 3, 6, 7. Current numeric annexes not yet independently compared."),
        source(YEREVAN_EXECUTION_SOURCE, "Yerevan Council Decision 518-N approving 2025 budget execution report", yr("yerevan-budget-2025-execution-decision.html")["url"], "Yerevan Council", "2025", "Yerevan community", yr("yerevan-budget-2025-execution-decision.html"),
               "Execution decision located and acquired; annex values have not been inventoried or adopted."),
    ]
    geo_source = source(GEOPORTAL_SOURCE, "National Geoportal administrative-boundary map", geo_receipt["url"],
                        "Cadastre Committee of Armenia", "edition not verified", "marz and community boundary leads",
                        geo_receipt, "Map page/script acquired. Referenced marzer GeoJSON has 11 uncoded features in EPSG:3857; referenced community_settlement GeoJSON returned HTTP 404. No dated official code join, rights decision or polygon adoption.")
    geo_source["status"] = "partial"
    sources.append(geo_source)
    marz_theme_tables = json.loads(MARZ_THEME_INVENTORY.read_text(encoding="utf-8"))["tables"]
    if {table["slug"] for table in marz_theme_tables} != set(MARZ_THEME_SPECS):
        raise ValueError("Five-table Armstat theme inventory changed")
    for table in marz_theme_tables:
        spec = MARZ_THEME_SPECS[table["slug"]]
        response_receipt = receipt(MARZ_THEME_RECEIPTS, f"{table['slug']}-{table['selected_year']}-slice.html")
        sources.append(source(spec["source_id"], table["title"], table["source_url"], "Statistical Committee of Armenia",
                              table["selected_year"], "national_and_adm1", response_receipt,
                              f"One direct published {table['selected_year']} slice for '{table['selected_indicator']}' and all 12 first-level/national reporting rows. Other {table['other_indicator_count']} indicator options and other years remain unassessed; source geography lacks official codes and polygons."))
    poverty_method_receipt = receipt(MARZ_THEME_RECEIPTS, "poverty-quality-declaration.pdf")
    sources.append(source(POVERTY_METHOD_SOURCE, "Poverty incidence quality declaration", poverty_method_receipt["url"],
                          "Statistical Committee of Armenia", "edition/date not verified", "national survey method",
                          poverty_method_receipt,
                          "Linked from Armstat's Poverty Level table. Describes ILCS consumption-based poverty and upper common poverty line; do not carry its historical sample size forward to 2024. The table's 2024 weight-recalibration footnote controls cross-year comparability."))
    dataset["sources"].extend(sources)
    dataset["indicators"].append({"id": "ARM_CENSUS_2022_PERMANENT_POP", "name": "Permanent population, 2022 census", "theme": "Population",
                                   "unit": "people", "definition": "Direct 2022 population census permanent (de jure) population, including residents temporarily absent at census date; not the WDI midyear de facto estimate.",
                                   "population": "permanent residents, including temporarily absent", "measurement_method": "armstat_2022_population_census_direct",
                                   "source_id": CENSUS_SOURCE, "aggregation": "none", "display_decimals": 0,
                                   "series_family": "census", "display_role": "primary", "period_policy": "latest_available_per_indicator"})
    for suffix, title in (("TOTAL", "Total"), ("URBAN", "Urban"), ("RURAL", "Rural")):
        dataset["indicators"].append({"id": f"ARM_2026_PERMANENT_POP_{suffix}",
                                       "name": f"{title} permanent population, 1 January 2026",
                                       "theme": "Population", "unit": "thousand people",
                                       "definition": f"{title} permanent population as of 1 January 2026 from Armstat's census-based current population statistics, rounded to 0.1 thousand. Urban/rural reflects registration settlement status; source dash is not converted to zero.",
                                       "population": "registered permanent population with statistical adjustment",
                                       "measurement_method": "armstat_census_based_current_population_estimate",
                                       "source_id": BULLETIN_SOURCE, "aggregation": "none", "display_decimals": 1,
                                       "series_family": "administrative", "display_role": "primary", "period_policy": "latest_available_per_indicator"})
    census_rows = json.loads(CENSUS.read_text(encoding="utf-8"))["rows"]
    census_name_to_prefix = {"Yerevan": "01", "Aragatsotn Marz": "02", "Ararat Marz": "03", "Armavir Marz": "04",
                             "Gegharqunik Marz": "05", "Lori Marz": "06", "Kotayk Marz": "07", "Shirak Marz": "08",
                             "Syunik Marz": "09", "Vayots Dzor Marz": "10", "Tavush Marz": "11"}
    if len(census_rows) != 12 or {r["marz"] for r in census_rows[1:]} != set(census_name_to_prefix):
        raise ValueError("Census marz list changed")
    if int(census_rows[0]["values"][0].replace(",", "")) != sum(int(r["values"][0].replace(",", "")) for r in census_rows[1:]):
        raise ValueError("Census national vs marz sum mismatch")
    for row in census_rows:
        name = row["marz"]
        target = "ARM" if name == "RA" else yid if name == "Yerevan" else marz_id[census_name_to_prefix[name]]
        dataset["observations"].append({"territory_id": target, "indicator_id": "ARM_CENSUS_2022_PERMANENT_POP",
                                         "period": "2022", "value": int(row["values"][0].replace(",", "")),
                                         "status": "observed", "source_id": CENSUS_SOURCE,
                                         "measurement_method": "armstat_2022_population_census_direct",
                                         "boundary_version": None,
                                         "source_locator": f"PxWeb PS-pp-1-1-2; marzes={name}; settlement=Total; sex=Total; years=2022"})
    for row in primary:
        kind = row["kind"]
        target = "ARM" if kind == "national" else yid if kind == "yerevan_community" else marz_id[row["marz_prefix"]] if kind == "marz" else f"ARM:community:{row['official_code']}"
        for suffix, field in (("TOTAL", "total_thousand"), ("URBAN", "urban_thousand"), ("RURAL", "rural_thousand")):
            value = row[field]
            dataset["observations"].append({"territory_id": target, "indicator_id": f"ARM_2026_PERMANENT_POP_{suffix}",
                                             "period": "2026-01-01", "value": value,
                                             "status": "not_applicable" if value is None else "observed", "source_id": BULLETIN_SOURCE,
                                             "measurement_method": "armstat_census_based_current_population_estimate",
                                             "boundary_version": EDITION,
                                             "source_locator": f"PDF page {row['page']}, text line {row['text_line']}, {row['name_en_source']}, {suffix.lower()} column"})
    english_first_level = {row["name_en_source"].title().casefold(): marz_id[row["marz_prefix"]]
                           for row in primary if row["kind"] == "marz"}
    if len(english_first_level) != 10:
        raise ValueError("Marz English labels for thematic tables are not unique")
    adopted_theme_rows = []
    for table in marz_theme_tables:
        spec = MARZ_THEME_SPECS[table["slug"]]
        period = table["selected_year"]
        dataset["indicators"].append({"id": spec["indicator_id"], "name": spec["name"], "theme": spec["theme"],
                                       "unit": spec["unit"], "definition": spec["definition"],
                                       "population": spec["population"], "measurement_method": spec["method"],
                                       "source_id": spec["source_id"], "aggregation": "none", "display_decimals": spec["decimals"],
                                       "series_family": spec["family"], "display_role": "primary",
                                       "period_policy": "latest_available_per_indicator"})
        seen_targets = set()
        mapped = []
        for index, row in enumerate(table["rows"], 1):
            label = row["marz_label"]
            if label in ("Total RA", "National average"):
                target = "ARM"
            elif label == "Yerevan city":
                target = yid
            else:
                normalized = label.removesuffix(" Marz").casefold()
                target = english_first_level.get(normalized)
            if target is None or target in seen_targets or row["numeric_value"] is None:
                raise ValueError(f"Unmatched, duplicate or nonnumeric Armstat theme row: {table['slug']}: {row}")
            seen_targets.add(target)
            value = row["numeric_value"]
            if spec["decimals"] == 0:
                if not float(value).is_integer():
                    raise ValueError(f"Nonintegral institution count: {table['slug']}: {row}")
                value = int(value)
            mapped.append({"territory_id": target, "source_label": label, "source_value": row["raw_value"], "value": value})
            dataset["observations"].append({"territory_id": target, "indicator_id": spec["indicator_id"],
                                             "period": period, "value": value, "status": "observed",
                                             "source_id": spec["source_id"], "measurement_method": spec["method"],
                                             "boundary_version": None,
                                             "source_locator": f"PxWeb {table['slug']} {period}; indicators={table['selected_codes']['indicators'][0]}; marzes={label}; result row {index}"})
        if seen_targets != {"ARM", yid, *marz_id.values()}:
            raise ValueError(f"Armstat theme reporting cohort changed: {table['slug']}")
        national = next(row["value"] for row in mapped if row["territory_id"] == "ARM")
        child_sum = sum(row["value"] for row in mapped if row["territory_id"] != "ARM")
        if spec["additive"] and abs(national - child_sum) > 0.11:
            raise ValueError(f"Armstat national control mismatch: {table['slug']}: {national} vs {child_sum}")
        adopted_theme_rows.append({"slug": table["slug"], "source_id": spec["source_id"],
                                   "indicator_id": spec["indicator_id"], "period": period, "unit": spec["unit"],
                                   "method": spec["method"], "source_hash": table["response_sha256"],
                                   "national_value": national, "sum_of_first_level_values": child_sum if spec["additive"] else None,
                                   "additive_control": spec["additive"], "rows": mapped,
                                   "decision": "adopted_direct_selected_slice_only",
                                   "unassessed_indicator_options": table["other_indicator_count"],
                                   "geography_note": "All 12 labels crosswalk to Armstat 2026 first-level labels and official classifier IDs; source table has no code/dated polygon, so observation boundary edition remains null."})
    (EVIDENCE / "ARM_MARZ_THEME_ADOPTION.json").write_text(json.dumps({"table_count": len(adopted_theme_rows),
        "observation_count": sum(len(table["rows"]) for table in adopted_theme_rows), "tables": adopted_theme_rows,
        "caution": "Direct values are source-reported. National controls are checked but no parent value is calculated from children. Other indicators/years and community-level thematic coverage remain unassessed."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ashtarak = next(t for t in dataset["territories"] if t.get("native_name") == "աշտարակ" and t["type"] == "community")
    match = {"territory_id": ashtarak["id"], "country_id": "ARM", "type": "community",
             "code_system": CODE_SYSTEM, "official_code": ashtarak["official_code"], "boundary_version": EDITION,
             "method": "ARLIS decision title names Ashtarak community in Aragatsotn; matched exactly to the 2026 official classifier and 2026 Armstat bulletin Armenian row. Official polygon is not verified.",
             "source_id": CLASSIFIER_SOURCE, "locator": "Order 143-N, Table 1 code 02 001 000; bulletin PDF page 4 Ashtarak community", "checked_at": DATE}
    dataset["documents"].extend([
        {"id": "arm-ashtarak-five-year-plan-2022-2026", "territory_id": ashtarak["id"],
         "category": "plan", "kind": "community_five_year_development_plan",
         "title": "Ashtarak community five-year development plan, 2022–2026 (Council Decision 194-N)",
         "url": plan_pdf_receipt["url"], "period": "2022-2026", "target_period": {"label": "2022-2026", "kind": "multi_year"},
         "availability": "content_verified", "official_status": "council_approved_2022_effective_2023_original_later_revisions_unchecked",
         "official_evidence": {"source_id": PLAN_DECISION_SOURCE, "locator": "ARLIS Decision 194-N clause 1 and legal status; PDF page 1 approval heading", "checked_at": DATE, "authority": "Ashtarak Council"},
         "source_id": PLAN_PDF_SOURCE, "territory_match": dict(match),
         "content": {"summary": "The 59-page council-approved plan covers Ashtarak community for 2022–2026, including a locality description, development issues, priorities, and indicative finance. Its projected amounts are plan figures, not achieved spending or official evaluation. Later revisions and implementation reports are not yet verified.",
                     "evidence": {"source_id": PLAN_PDF_SOURCE, "locator": "PDF pages 1–2 (approval and contents), page 29 (financial projections), page 50 (priorities)", "checked_at": DATE, "authority": "Ashtarak Council"}}},
        {"id": "arm-ashtarak-budget-2026", "territory_id": ashtarak["id"],
         "category": "budget", "kind": "community_annual_budget_approved",
         "title": "Ashtarak community approved 2026 annual budget (Council Decision 170-N)",
         "url": budget_xls_receipt["url"], "period": "2026", "target_period": {"label": "2026", "kind": "calendar_year"},
         "availability": "content_verified", "official_status": "council_approved_2025_effective_2026_original_amendments_unchecked",
         "official_evidence": {"source_id": BUDGET_DECISION_SOURCE, "locator": "ARLIS Decision 170-N dated 2025-12-10, approval clause 1 and legal status effective 2026-01-23", "checked_at": DATE, "authority": "Ashtarak Council"},
         "source_id": BUDGET_XLS_SOURCE, "territory_match": dict(match),
         "content": {"summary": "The approved original 2026 budget states total revenue of 7,693,615.1 and expenditure of 8,622,091.5 thousand AMD, with a planned balance of -928,476.4 thousand AMD (deficit). Decision clause 1 and XLS Sheet1 D11, Sheet2+ F11, Sheet4+ C13 agree. These are approved budget figures, not execution; later amendments and actual spending remain unchecked.",
                     "evidence": {"source_id": BUDGET_DECISION_SOURCE, "locator": "ARLIS Decision 170-N clause 1; XLS Sheet1 D11, Sheet2+ F11, Sheet4+ C13", "checked_at": DATE, "authority": "Ashtarak Council"}}},
    ])
    ymatch = {"territory_id": yid, "country_id": "ARM", "type": "community",
              "code_system": CODE_SYSTEM, "official_code": yerevan["official_code"], "boundary_version": EDITION,
              "method": "Yerevan city-community is code 01 001 000 in the current official classifier; PDF covers and decisions identify Yerevan city. The 12 internal districts are not separate legal communities.",
              "source_id": CLASSIFIER_SOURCE, "locator": "Order 143-N, Table 1 Yerevan community; 2026 bulletin page 4", "checked_at": DATE}
    dataset["documents"].extend([
        {"id": "arm-yerevan-five-year-plan-2024-2028", "territory_id": yid, "category": "plan", "kind": "yerevan_five_year_development_plan",
         "title": "Yerevan five-year development plan, 2024–2028 (Council Decision 46-A)",
         "url": yr("yerevan-five-year-plan-2024-2028.pdf")["url"], "period": "2024-2028", "target_period": {"label": "2024-2028", "kind": "multi_year"},
         "availability": "content_verified", "official_status": "council_approved_2023_later_revisions_unchecked",
         "official_evidence": {"source_id": YEREVAN_FIVE_DECISION_SOURCE, "locator": "ARLIS Decision 46-A clause 1, legal status; annex PDF page 1 approval heading", "checked_at": DATE, "authority": "Yerevan Council"},
         "source_id": YEREVAN_FIVE_PDF_SOURCE, "territory_match": dict(ymatch),
         "content": {"summary": "The Yerevan Council approved a 2024–2028 city development plan. Its 52-page annex is acquired; quantitative goals and later changes are not yet assessed.",
                     "evidence": {"source_id": YEREVAN_FIVE_PDF_SOURCE, "locator": "PDF page 1 cover/approval and pages 2–3 contents", "checked_at": DATE, "authority": "Yerevan Council"}}},
        {"id": "arm-yerevan-annual-program-2026", "territory_id": yid, "category": "plan", "kind": "yerevan_annual_development_program",
         "title": "Yerevan 2026 annual development program (Council Decision 460-A)",
         "url": yr("yerevan-annual-program-2026.pdf")["url"], "period": "2026", "target_period": {"label": "2026", "kind": "calendar_year"},
         "availability": "content_verified", "official_status": "council_approved_2025",
         "official_evidence": {"source_id": YEREVAN_ANNUAL_DECISION_SOURCE, "locator": "Yerevan Decision 460-A clause 1, 2025-12-23; annex PDF page 1 approval heading", "checked_at": DATE, "authority": "Yerevan Council"},
         "source_id": YEREVAN_ANNUAL_PDF_SOURCE, "territory_match": dict(ymatch),
         "content": {"summary": "The council-approved 2026 annual development program is a distinct 34-page source. Targets are planned actions, not achieved 2026 results; numeric targets are not yet adopted.",
                     "evidence": {"source_id": YEREVAN_ANNUAL_PDF_SOURCE, "locator": "PDF page 1 cover and approval heading; Decision 460-A clause 1", "checked_at": DATE, "authority": "Yerevan Council"}}},
        {"id": "arm-yerevan-program-2025-implementation-report", "territory_id": yid, "category": "implementation", "kind": "yerevan_annual_program_implementation_report",
         "title": "Yerevan 2025 development program implementation report (Council Decision 513-A)",
         "url": yr("yerevan-program-2025-implementation-report.pdf")["url"], "period": "2025", "target_period": {"label": "2025", "kind": "calendar_year"},
         "availability": "content_verified", "official_status": "council_took_note_2026_not_evaluation_approval",
         "official_evidence": {"source_id": YEREVAN_REPORT_DECISION_SOURCE, "locator": "Yerevan Decision 513-A clause 1 'take note', 2026-03-12; annex PDF page 1", "checked_at": DATE, "authority": "Yerevan Council"},
         "source_id": YEREVAN_REPORT_PDF_SOURCE, "territory_match": dict(ymatch),
         "content": {"summary": "The mayor's 2025 annual program implementation report was presented and taken note of by the council. The 36-page annex describes work and outcomes; its project numbers are not adopted as verified attainment rates or budget execution.",
                     "evidence": {"source_id": YEREVAN_REPORT_PDF_SOURCE, "locator": "PDF page 1 cover and page 2 introduction; Decision 513-A clause 1", "checked_at": DATE, "authority": "Yerevan Council"}}},
    ])
    dataset["country"]["geography_note"] = (
        "Armstat 2026-01-01 bulletin reports one national, Yerevan city-community, 10 marzes and 69 other communities. "
        "Rows are matched to the 2026-02-15 official HD 002-2023 classifier by Armenian name and marz; the classifier has 70 communities including Yerevan. "
        "The 2025 Khoy community merged into Vagharshapat in 2025; the 2025 bulletin is not joined to the 2026 geography. "
        "Census 2022 and census-based 2026 current counts are distinct, as are WDI de facto midyear estimates. "
        "Five Armstat 2024/2025 marz thematic slices are direct first-level reports; their source tables do not provide official codes or dated polygons, and no community theme values are inferred. "
        "The bootstrap geoBoundaries ADM1 polygons were made for a 2005 provider edition and are withheld until official 2022/2026 geometry can be matched.")
    dataset["analysis"]["terminal_territory_ids"] = sorted(community_id.values())
    dataset["analysis"]["comparisons"] = [{"parent_id": "ARM", "member_ids": [yid] + [marz_id[p] for p in sorted(marz_id)],
                                               "label": "Armstat national reporting areas",
                                               "membership_note": "Official classifier and 2026 bulletin list Yerevan city-community and ten marzes as disjoint national reporting areas. Their legal planning roles differ; direct values are not summed to fabricate parent rates.",
                                               "source_ids": [CLASSIFIER_SOURCE, BULLETIN_SOURCE],
                                               "color_scale": {"mode": "within_selection"}}]
    for prefix in sorted(marz_id):
        members = [f"ARM:community:{r['official_code']}" for r in annual_communities if r["marz_prefix"] == prefix]
        dataset["analysis"]["comparisons"].append({"parent_id": marz_id[prefix], "member_ids": members,
                                                       "label": f"{annual_marzes[prefix]['name_en_source'].title()} communities",
                                                       "membership_note": "All 2026 official community codes in this marz match the Armstat bulletin by Armenian name and parent. No 2022 community series or verified polygon is implied.",
                                                       "source_ids": [CLASSIFIER_SOURCE, BULLETIN_SOURCE],
                                                       "color_scale": {"mode": "within_selection"}})
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["armenia-armstat-2022-census-marz-partial", "armenia-armstat-2026-annual-population", "armenia-armstat-2024-2025-marz-themes-partial", "armenia-ashtarak-planning-partial", "armenia-yerevan-planning-partial"]))
    dataset["collection"]["status"] = "partial"
    dataset["collection"]["notes"].append("Official 2026 community population, five 2024/2025 first-level Armstat theme slices, Ashtarak plan/budget, and Yerevan five-year/annual plans plus a council-noted implementation report are integrated; all 2005 provider polygons are withheld. Community thematic depth, full census cross-tabs, current budget annexes, and systematic plan/budget/implementation/evaluation coverage remain open.")
    receipt_files = [EVIDENCE / "ARM_CENSUS_2022_RECEIPTS.json", BULLETIN_RECEIPTS,
                     OFFICIAL_RECEIPTS, YEREVAN_RECEIPTS, GEOPORTAL_RECEIPTS, MARZ_THEME_RECEIPTS]
    retrieved_at = [datetime.fromisoformat(record["retrieved_at_utc"])
                    for receipt_file in receipt_files
                    for record in json.loads(receipt_file.read_text(encoding="utf-8"))
                    if record.get("retrieved_at_utc")]
    dataset["generated_at"] = max(retrieved_at).astimezone(timezone.utc).isoformat()
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="2026 official HD 002-2023 classifier matched to 2026 population bulletin for all 70 communities by Armenian name and marz. 2025 Khoy merger recorded. No official dated polygons matched; 2005 provider polygons withheld.", next_action="Acquire official national geoportal marz and community geometries with version, codes, rights and 2022/2026 validity; verify all joins and Yerevan internal districts separately.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="Direct 2022 census permanent population for 11 first-level areas and national was checked; 2026 census-based current population total/urban/rural for national, 10 marzes, Yerevan and 69 other communities was integrated in 0.1-thousand units. Five direct Armstat 2024/2025 marz slices add schools, hospitals, consumer water volume, 2024 ILCS poverty share and city street length at national/first-level only. Other source columns, 13 census tables and community-level themes remain unassessed.", next_action="Audit remaining 13 Census 2022 PxWeb tables and the other columns/years of five new marz tables; seek official community-level sector sources, 2025 boundary crosswalk and source geography codes before broad adoption.")
        elif gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Ashtarak council-approved 2022–2026 plan PDF and original approved 2026 budget XLS, plus Yerevan 2024–2028 plan, 2026 program and council-noted 2025 implementation report, were acquired and code-linked. Yerevan's current 2026 budget incorporates a September annex amendment; numeric annexes and budget execution are not adopted.", next_action="Inventory official community sites and decisions for the other 68 units; audit current annexes, actual budget execution and formal evaluations separately.")
    DATA.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    crosswalk_path = EVIDENCE / "CODE_CROSSWALK.csv"
    with crosswalk_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["territory_id", "type", "official_code", "code_system", "name_hy", "name_en", "parent_id", "source", "join_status", "geometry_status"])
        writer.writeheader()
        for t in dataset["territories"][1:]:
            writer.writerow({"territory_id": t["id"], "type": t["type"], "official_code": t["official_code"],
                             "code_system": CODE_SYSTEM, "name_hy": t["native_name"], "name_en": t["name"],
                             "parent_id": t["parent_id"], "source": CLASSIFIER_SOURCE + ";" + BULLETIN_SOURCE,
                             "join_status": "exact_armenian_name_and_parent_matched_2026",
                             "geometry_status": "official_polygon_not_verified"})
    print(json.dumps({"territories": len(dataset["territories"]), "observations": len(dataset["observations"]),
                      "new_population_observations": len(dataset["observations"]) - 312 - sum(len(table["rows"]) for table in adopted_theme_rows),
                      "new_marz_theme_observations": sum(len(table["rows"]) for table in adopted_theme_rows),
                      "community_count": len(dataset["analysis"]["terminal_territory_ids"]),
                      "documents": len(dataset["documents"]), "polygons": len(dataset["boundaries"]["features"]),
                      "dashboard_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Adopt the checked 2026 resident-age table and Astara city plan as a partial candidate."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import xlrd


RAW = "raw/azerbaijan-official/"
AGE_FILE = "2020-2026-population-age-by-area.xls"
AGE_SHEET = "01.01.2026 (Total population)"
SEX_FILE = "2026-population-sex-settlement.xls"
AGE_SOURCE = "aze-ssc-resident-age-area-2026"
SEX_SOURCE = "aze-ssc-population-sex-settlement-2026"
CODE_SOURCE = "aze-ssc-administrative-classification-2024"
APPROVAL_SOURCE = "aze-arxkom-astara-master-plan-approval-2025"
MAP_SOURCE = "aze-arxkom-astara-master-plan-map"
NEWS_SOURCE = "aze-arxkom-astara-master-plan-announcement"
PERIOD = "2026-01-01"
OFFICIAL_CODES = {
    "Baku city": "00000002",
    "Binagadi district": "00100003",
    "Astara district": "80100001",
    "Astara city": "80101014",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_receipts(project):
    acquisition = json.loads((project / "evidence/AZE_OFFICIAL_ACQUISITION.json").read_text(encoding="utf-8"))
    receipts = {Path(item["raw_path"]).name: item for item in acquisition["receipts"]}
    if len(receipts) != 11:
        raise ValueError("Expected all eleven Azerbaijan originals")
    for filename, receipt in receipts.items():
        if digest(project / receipt["raw_path"]) != receipt["sha256"] or receipt["status"] != "acquired":
            raise ValueError(f"Changed original or receipt: {filename}")
    return receipts


def integer(sheet, row, column):
    if sheet.cell_type(row, column) != xlrd.XL_CELL_NUMBER:
        raise ValueError(f"Expected numeric cell {sheet.name}!{xlrd.colname(column)}{row + 1}")
    value = sheet.cell_value(row, column)
    if not value.is_integer() or value < 0:
        raise ValueError(f"Expected nonnegative integer {sheet.name}!{xlrd.colname(column)}{row + 1}")
    return int(value)


def label(sheet, row):
    return " ".join(str(sheet.cell_value(row, 1)).split())


def source_id(filename):
    return "aze-ssc-" + re.sub(r"[^a-z0-9]+", "-", filename.lower()).strip("-").replace("-xls", "").replace("-pdf", "").replace("-zip", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "AZE" or any(s["id"] == AGE_SOURCE for s in dataset["sources"]):
        raise ValueError("Expected an unmodified Azerbaijan bootstrap")
    receipts = raw_receipts(project)
    workbook = xlrd.open_workbook(project / RAW / AGE_FILE)
    if len(workbook.sheets()) != 35:
        raise ValueError("Expected 2020–2026 five-way workbook")
    sheet = workbook.sheet_by_name(AGE_SHEET)
    if (sheet.nrows, sheet.ncols) != (138, 22):
        raise ValueError("2026 resident-age table dimensions changed")
    numeric_rows = [row for row in range(sheet.nrows) if sheet.cell_type(row, 2) == xlrd.XL_CELL_NUMBER]
    group_rows = [row for row in numeric_rows if "economic region - total" in label(sheet, row) or label(sheet, row) == "Baku city - total"]
    if len(numeric_rows) != 101 or len(group_rows) != 14 or numeric_rows[0] != 9 or integer(sheet, 9, 2) != 10262351:
        raise ValueError("2026 source geography or country total changed")
    age_labels = ["TOTAL"] + [str(sheet.cell_value(7, column)).strip() for column in range(3, 22)]
    if len(age_labels) != 20 or age_labels[1] != "0-4" or age_labels[-1] != "90+":
        raise ValueError("2026 age-band headers changed")
    for row in numeric_rows:
        if integer(sheet, row, 2) != sum(integer(sheet, row, column) for column in range(3, 22)):
            raise ValueError(f"Age bands do not sum to source total at Excel row {row + 1}")
    for row, stop in zip(group_rows, group_rows[1:] + [sheet.nrows]):
        children = [child for child in numeric_rows if row < child < stop]
        if not children:
            raise ValueError(f"Empty reporting group at row {row + 1}")
        for column in range(2, 22):
            if integer(sheet, row, column) != sum(integer(sheet, child, column) for child in children):
                raise ValueError(f"Incomplete group {row + 1} / {xlrd.colname(column)}")
    for column in range(2, 22):
        if integer(sheet, 9, column) != sum(integer(sheet, row, column) for row in group_rows):
            raise ValueError(f"Incomplete national group cover at {xlrd.colname(column)}")

    now = datetime.now(timezone.utc).isoformat()
    country = next(area for area in dataset["territories"] if area["id"] == "AZE")
    country.update(source_id=AGE_SOURCE, type="country", boundary_version=None,
                   code_system="ISO3 dataset key; State Statistical Committee 2026 source row 10")
    dataset["territories"] = [country]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    source_rows = []
    groups = []
    by_source_row = {9: country}
    for row in numeric_rows[1:]:
        name = label(sheet, row).removesuffix(" - total")
        if row in group_rows:
            parent = country
            level = "statistical_reporting_region"
            area_type = "republic_city" if name == "Baku city" else "economic_region"
        else:
            group_row = max(item for item in group_rows if item < row)
            parent = by_source_row[group_row]
            level = "administrative_unit"
            area_type = "city" if name.endswith(" city") else "urban_district" if parent["name"] == "Baku city" else "district"
        territory = {
            "id": f"AZE:SSC2026:AGE:R{row + 1}", "name": name, "level": level, "type": area_type,
            "parent_id": parent["id"], "official_code": OFFICIAL_CODES.get(name),
            "code_system": "SSC 2024 administrative division classification" if name in OFFICIAL_CODES else "SSC 2026 age table row and printed parent; official code unresolved",
            "provider_code": None, "source_id": AGE_SOURCE, "boundary_version": None,
            "reconciliation_status": "2026_source_hierarchy_and_parent_sums_checked; official_polygon_unverified" if name in OFFICIAL_CODES else "2026_source_hierarchy_checked; official_code_and_polygon_unverified",
        }
        dataset["territories"].append(territory)
        by_source_row[row] = territory
    if len(dataset["territories"]) != 101:
        raise ValueError("Unexpected source geography count")
    astara_district = by_source_row[90]
    if astara_district["name"] != "Astara district" or astara_district["official_code"] != "80100001":
        raise ValueError("Astara district source row changed")
    sex_sheet = xlrd.open_workbook(project / RAW / SEX_FILE).sheet_by_index(0)
    if (sex_sheet.nrows, sex_sheet.ncols) != (474, 11) or label(sex_sheet, 323) != "Astara district" or label(sex_sheet, 324) != "Astara city":
        raise ValueError("Astara settlement source hierarchy changed")
    city = {
        "id": "AZE:SSC2026:SETTLEMENT:R325", "name": "Astara city", "level": "settlement", "type": "city",
        "parent_id": astara_district["id"], "official_code": "80101014",
        "code_system": "SSC 2024 administrative division classification, 8-digit code",
        "provider_code": None, "source_id": SEX_SOURCE, "boundary_version": None,
        "reconciliation_status": "2024_official_code_and_2026_source_parent_checked; 2026_code_validity_and_polygon_unverified",
    }
    dataset["territories"].append(city)
    for row in numeric_rows:
        area = by_source_row[row]
        source_rows.append({"excel_row": row + 1, "source_name": label(sheet, row), "territory_id": area["id"],
                            "parent_id": area.get("parent_id"), "type": area["type"], "official_code": area.get("official_code"),
                            "total": integer(sheet, row, 2)})
    with (project / "evidence/AZE_2026_AGE_SOURCE_ROWS.csv").open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(source_rows)

    acquired = (
        (AGE_FILE, AGE_SOURCE, "2020–2026 population by age and area; 2026 total-population sheet", "ready", "2026-01-01 resident estimate; 2020–2025 and four sex/settlement variants inventoried, not adopted"),
        (SEX_FILE, SEX_SOURCE, "2026 population by sex, area and settlement", "partial", "Only Astara city C–E rounded thousand-person cells adopted; remaining source rows/columns unadopted"),
        ("2026-resident-population-by-area.xls", "aze-ssc-historical-census-population-by-area", "Historical 1979–2019 census population by area", "partial", "The title is on a 2026 page, but all five numeric columns are historical census years, not 2026 estimates; not adopted"),
        ("2025-area-population-density.xls", source_id("2025-area-population-density.xls"), "2025 area, 2019 census and 2026 population/density", "partial", "Four numeric fields inventoried; 2019 census and 2026 annual estimate columns kept separate; no values adopted"),
        ("2025-administrative-division.xls", source_id("2025-administrative-division.xls"), "2025 administrative unit counts", "partial", "Nine numeric unit-count columns inventoried; not mistaken for population or legal code table"),
        ("2019-census-volume-a.zip", source_id("2019-census-volume-a.zip"), "2019 population census Volume A", "partial", "Official 470-page PDF in ZIP; table contents identified, full numeric-column and geographic audit outstanding; no values adopted"),
        ("2019-census-volume-b.zip", source_id("2019-census-volume-b.zip"), "2019 population census Volume B", "partial", "Official 584-page PDF in ZIP; household and housing table contents identified, full numeric-column audit outstanding; no values adopted"),
        ("2024-administrative-classification.pdf", CODE_SOURCE, "2024 administrative division classification with eight-digit codes", "partial", "PDF pages 9 and 34 verify Baku/Binagadi and Astara district/city codes. Remaining code crosswalk and 2026 validity are unverified"),
        ("astara-master-plan-approval-291-2025.pdf", APPROVAL_SOURCE, "Cabinet decision No. 291 approving Astara city master plan", "ready", "Official one-page decision of 7 October 2025; city scope, to 2039; attached plan text not in this PDF"),
        ("astara-master-plan-map.pdf", MAP_SOURCE, "Astara city master-plan drawing", "partial", "One-page drawing dated 2022 and published in 2026; not treated as legal boundary data or proof of final annex identity"),
        ("astara-master-plan-announcement.html", NEWS_SOURCE, "ARXKOM Astara city master-plan announcement", "ready", "Official 7 October 2025 article reports decision No. 291 and describes intended priorities and projections, not achieved outcomes"),
    )
    for filename, item_id, title, status, note in acquired:
        receipt = receipts[filename]
        dataset["sources"].append({
            "id": item_id, "name": title, "publisher": "State Statistical Committee of the Republic of Azerbaijan" if filename.startswith(("2019", "2020", "2024", "2025", "2026")) else "State Committee on Urban Planning and Architecture / Cabinet of Ministers of Azerbaijan",
            "url": receipt["source_url"], "status": status, "reference_period": "1979–2019 historical censuses" if filename == "2026-resident-population-by-area.xls" else "2019 census" if filename.startswith("2019") else "2024 classification" if filename.startswith("2024") else "2025–2039 planning" if filename.startswith("astara") else "2020–2026 statistical editions",
            "geographic_level": "country, reporting region and administrative unit" if filename.endswith(".xls") else "official document",
            "retrieved_at": receipt["retrieved_at"], "raw_path": receipt["raw_path"], "sha256": receipt["sha256"],
            "license": "Public official material; cite source; redistribution terms require review", "note": note,
        })
    for item_id, title, url, note in (
        ("aze-ssc-population-methodology", "Population-estimate methodology", "https://stat.gov.az/source/demoqraphy/ap/?lang=en", "Official bulletin explains post-census births, deaths and permanent migration adjustment; exact 2026 applicability and revision history remain to check"),
        ("aze-arxkom-master-plan-catalogue", "ARXKOM master-plan catalogue", "https://arxkom.gov.az/en/sehersalma/bas-planlar", "Catalogue contains both drafts and approved documents; approval must be checked case by case"),
        ("aze-urban-planning-code", "Urban Planning and Construction Code", "https://frameworks.e-qanun.az/24/c_f_24201.html", "Legal planning units, amendments and current applicability require separate review"),
    ):
        dataset["sources"].append({"id": item_id, "name": title, "publisher": "Official Azerbaijan source", "url": url,
                                   "reference_period": "edition to verify", "geographic_level": "country and local planning",
                                   "status": "not_collected", "retrieved_at": now, "license": "terms_review_required", "note": note})

    method = "ssc_2026_annual_resident_population_estimate_age_area"
    definition = ("State Statistical Committee estimated resident population on 1 January 2026 by reporting area and five-year age band, "
                  "in persons. The annual estimate is based on the 2019 census with demographic/migration adjustments; "
                  "it is not a 2019 census count or a World Bank midyear series. Economic regions are statistical groupings, "
                  "not asserted legal planning units. No unverified occupied-area allocation or provider polygon is inferred.")
    fields = []
    for column, band in enumerate(age_labels, start=2):
        suffix = "TOTAL" if column == 2 else "AGE_" + band.replace("-", "_").replace("+", "_PLUS")
        indicator_id = "AZE_SSC_2026_" + suffix
        fields.append((column, indicator_id, band))
        dataset["indicators"].append({
            "id": indicator_id, "name": "Resident population, total (1 Jan 2026 estimate)" if column == 2 else f"Resident population age {band} (1 Jan 2026 estimate)",
            "theme": "Population", "unit": "people", "source_id": AGE_SOURCE, "definition": definition,
            "population": "usual residents, both sexes" if column == 2 else f"usual residents aged {band}, both sexes",
            "aggregation": "none", "measurement_method": method,
            "display_role": "primary", "period_policy": "latest_available_per_indicator", "display_decimals": 0,
        })
    for row in numeric_rows:
        for column, indicator_id, _ in fields:
            dataset["observations"].append({
                "territory_id": by_source_row[row]["id"], "indicator_id": indicator_id, "period": PERIOD,
                "value": integer(sheet, row, column), "status": "observed", "source_id": AGE_SOURCE,
                "measurement_method": method, "source_locator": f"{AGE_SHEET}!{xlrd.colname(column)}{row + 1}",
            })
    for column, suffix, title in ((2, "TOTAL", "Population"), (3, "MALE", "Male population"), (4, "FEMALE", "Female population")):
        value = sex_sheet.cell_value(324, column)
        if sex_sheet.cell_type(324, column) != xlrd.XL_CELL_NUMBER or value < 0:
            raise ValueError("Astara city source cell missing")
        indicator_id = "AZE_SSC_2026_SETTLEMENT_" + suffix
        dataset["indicators"].append({
            "id": indicator_id, "name": f"{title}, Astara city (1 Jan 2026 rounded estimate)",
            "theme": "Population", "unit": "thousand people", "source_id": SEX_SOURCE,
            "definition": "Source-reported 1 January 2026 resident estimate in thousand persons, rounded to one decimal. Astara city is nested under Astara district; the city figure is not the district total.",
            "population": "Astara city usual residents" if column == 2 else f"Astara city {'men' if column == 3 else 'women'} usual residents",
            "aggregation": "none", "measurement_method": "ssc_2026_rounded_resident_population_by_settlement",
            "display_role": "primary", "period_policy": "latest_available_per_indicator", "display_decimals": 1,
        })
        dataset["observations"].append({
            "territory_id": city["id"], "indicator_id": indicator_id, "period": PERIOD,
            "value": round(value, 1), "status": "observed", "source_id": SEX_SOURCE,
            "measurement_method": "ssc_2026_rounded_resident_population_by_settlement",
            "source_locator": f"1.19.!{xlrd.colname(column)}325; city below Astara district at row 324",
        })
    if round(sex_sheet.cell_value(324, 3) + sex_sheet.cell_value(324, 4), 1) != round(sex_sheet.cell_value(324, 2), 1):
        raise ValueError("Astara city rounded sex components differ")

    def territory_match(source, locator):
        return {"territory_id": city["id"], "country_id": "AZE", "type": city["type"],
                "code_system": city["code_system"], "official_code": city["official_code"],
                "boundary_version": None,
                "method": "Cabinet and ARXKOM documents identify Astara city, not Astara district. The SSC 2024 classification gives city code 80101014 under district 80100001; SSC 2026 table 1.19 row 325 separately reports that city. Current legal boundary is unverified.",
                "source_id": source, "locator": locator, "checked_at": now}

    dataset["documents"].append({
        "id": "aze-astara-city-master-plan-2039-approved-2025", "territory_id": city["id"],
        "category": "plan", "kind": "city_master_plan_approval",
        "title": "Astara city master plan through 2039 — Cabinet approval No. 291 (7 October 2025)",
        "url": receipts["astara-master-plan-approval-291-2025.pdf"]["source_url"], "period": "2025–2039",
        "target_period": {"label": "2025–2039", "kind": "multi_year"},
        "availability": "content_verified", "official_status": "cabinet_approved_2025",
        "official_evidence": {"source_id": APPROVAL_SOURCE, "locator": "PDF page 1, Cabinet decision No. 291 dated 7 October 2025, approval clause and city title",
                              "checked_at": now, "authority": "Cabinet of Ministers of the Republic of Azerbaijan"},
        "source_id": APPROVAL_SOURCE,
        "territory_match": territory_match(CODE_SOURCE, "SSC administrative classification PDF page 34, 80100001/80101014; 2026 table 1.19 rows 324–325"),
        "content": {"summary": "The Cabinet approved Astara city's master plan through 2039. ARXKOM's announcement describes proposed settlement, services, roads, green space and tourism priorities; these are plans and forecasts, not achieved results. A published 2022 plan drawing is available, but the one-page decision does not itself establish that drawing as the legal annex. No Astara district-wide plan, local budget, implementation result or evaluation is inferred.",
                    "evidence": {"source_id": NEWS_SOURCE, "locator": "ARXKOM announcement dated 7 October 2025, paragraphs on approval and proposed priorities; drawing title block dated 2022",
                                 "checked_at": now, "authority": "State Committee on Urban Planning and Architecture"}},
    })

    dataset["country"]["geography_note"] = (
        "SSC table 1.23.6 directly reports 1 January 2026 resident estimates for the country, Baku city, 13 statistical economic regions and their 86 administrative city/district rows. The 20 count columns and parent sums are exact in the source; this is not the 2019 census. SSC table 1.19 separately reports Astara city's rounded settlement values. Baku, Binagadi and Astara district/city 2024 official codes are provisionally matched by type and printed parent; the rest remain source-row IDs without official-code or dated-polygon verification. Two bootstrap provider shapes are withheld. Economic regions are not legal planning units, and Astara city approval is not a district-wide plan.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="SSC 2024 code PDF verifies four sampled identifiers, and 2026 source rows establish reporting parents. Remaining official codes, post-2024 changes and dated legal polygons are unverified. Two provider reference polygons are withheld.",
                       next_action="Reconcile every 2026 reporting row to current official classification and valid polygon edition, including changes in recovered areas and city/district distinctions.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="2026 table 1.23.6 contributes 20 exact both-sex age/count fields for 101 source rows (2,020 observations); table 1.19 contributes three rounded Astara city values. Other 34 age/sex/settlement sheets, the remainder of table 1.19, historical 1.17, and both 2019 census volumes are acquired or inventoried but not adopted.",
                       next_action="Audit and map the remaining 727 numeric XLS column contexts and the 2019 census A/B tables; keep 2019 census, annual resident estimates, occupied-area scope and rounding distinct.")
        elif gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Cabinet decision No. 291 approves the Astara city master plan through 2039; ARXKOM publishes an announcement and 2022 drawing. This is a city document, not an Astara district or economic-region plan. Local budgets, execution, evaluation and plans elsewhere are not collected.",
                       next_action="Verify the legal annex/current revisions, legal planning roles, other city/district plans, budgets, implementation and official evaluations.")
    dataset["analysis"]["latest_values_only"] = True
    comparisons = []
    for parent in [country] + [by_source_row[row] for row in group_rows]:
        members = [area for area in dataset["territories"] if area.get("parent_id") == parent["id"] and area["id"] != city["id"]]
        if not members:
            raise ValueError(f"Missing comparison members for {parent['id']}")
        comparisons.append({
            "parent_id": parent["id"], "member_ids": [area["id"] for area in members],
            "label": "2026 resident-age table reporting areas",
            "membership_note": "SSC table 1.23.6 prints these disjoint direct child rows; all 20 numeric count columns sum to this parent's separately reported value. Baku city and economic regions have different legal types; the set is only a statistical comparison, never a planning-authority classification.",
            "source_ids": [AGE_SOURCE], "color_scale": {"mode": "within_selection"},
        })
    dataset["analysis"]["comparisons"] = comparisons
    dataset["analysis"]["terminal_territory_ids"] = [area["id"] for area in dataset["territories"] if area["level"] in ("administrative_unit", "settlement") and area["id"] != astara_district["id"]]
    dataset["analysis"]["incomplete_child_cover_ids"] = [astara_district["id"]]
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] + ["azerbaijan-ssc-2026-resident-age-partial", "azerbaijan-astara-master-plan-partial"]))
    dataset["generated_at"] = now
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (project / "evidence/AZE_XLS_NUMERIC_COLUMNS.csv").open("r", encoding="utf-8-sig", newline="") as source:
        inventory = list(csv.DictReader(source))
    if len(inventory) != 727:
        raise ValueError("All acquired XLS numeric columns must be inventoried before import")
    for item in inventory:
        if item["file"] == AGE_FILE and item["sheet"] == AGE_SHEET and item["column"] in [xlrd.colname(column) for column in range(2, 22)]:
            item["disposition"] = "adopted_all_101_source_rows_2026_both_sexes"
        elif item["file"] == SEX_FILE and item["column"] in ("C", "D", "E"):
            item["disposition"] = "adopted_astara_city_row_325_only_remaining_rows_unassessed"
    with (project / "evidence/AZE_XLS_NUMERIC_COLUMNS.csv").open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)
    audit = {
        "status": "partial_candidate_not_accepted", "checked_at": now,
        "territories": len(dataset["territories"]), "age_source_rows": 101, "age_numeric_columns": 20,
        "age_observations": 2020, "astara_city_rounded_observations": 3,
        "full_xls_numeric_column_register": len(inventory), "comparison_groups_parent_sums_checked": 14,
        "national_population_exact": 10262351, "astara_city_population_thousand_rounded": round(sex_sheet.cell_value(324, 2), 1),
        "documents_content_verified": 1, "official_polygons_adopted": 0,
        "unresolved": ["All other official codes and dated polygons", "2019 census A/B full tables", "Other annual age/sex sheets", "Current master-plan annex and revisions", "Local budgets, actual execution and evaluation", "42 scenarios and independent acceptance"],
    }
    (project / "evidence/AZE_2026_IMPORT_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_file = project / "evidence/SOURCE_PREFLIGHT.json"
    preflight = json.loads(preflight_file.read_text(encoding="utf-8"))
    preflight["country_research"] = {
        "status": "official_2026_resident_estimate_partially_adopted", "checked_at": now,
        "census": "Official 2019 census Volumes A/B acquired but no census observations adopted; 2026 annual resident estimates are a separate adjusted series.",
        "geography": "SSC source-row hierarchy, 2024 code PDF for Baku/Binagadi/Astara and all 20 field parent sums checked; remaining official codes/dates and polygons pending.",
        "planning": "Astara city Cabinet-approved master plan through 2039 and ARXKOM drawing/announcement acquired; city and district separated; other local planning and finances pending.",
        "cross_country_candidates": "Common-source availability not assessed for AZE; no cross-country local values adopted.",
    }
    preflight_file.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_file = project / "evidence/SOURCE_PREFLIGHT.md"
    original = markdown_file.read_text(encoding="utf-8")
    old = "Research status: **source_locations_not_pre_researched**\n\nNo country-specific source locations are pre-researched yet. Complete the first required action below."
    replacement = ("Research status: **official_2026_resident_estimate_partially_adopted** (2026-09-26).\n\n"
                   "SSC's 2019 census Volumes A/B, 2024 official code classification and 2026 population workbooks were acquired. Table 1.23.6 contributes 20 exact both-sex age/count columns for 101 source rows; table 1.19 contributes three rounded Astara city values. These are 2026 annual estimates, not 2019 census values. Astara city's Cabinet-approved plan through 2039 was verified, but district-wide planning/finance, current plan annex, official polygons, most codes and remaining source columns are unresolved. See AZE_2026_IMPORT_AUDIT.json and AZE_XLS_NUMERIC_COLUMNS.csv.")
    if old not in original:
        raise ValueError("Unexpected bootstrap source preflight Markdown")
    markdown_file.write_text(original.replace(old, replacement), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()

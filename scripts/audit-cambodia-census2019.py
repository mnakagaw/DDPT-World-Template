"""Inventory the NIS 2019 final report's province/district/commune tables.

Requires Poppler pdftotext. PDF page numbers below are one-based file pages, not
the printed page numbers. The P tables count normal/regular-household residents,
which must never be substituted for the separate final all-person census count.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P_TITLE = re.compile(r"Table P-(\d{2})\. Total Population (.*?) 2019")
P_ROW = re.compile(
    r"^\s*(\d{2,6})\s+(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)\s*$"
)
P_SUBTOTAL = re.compile(
    r"^\s*(Total|Toatl|Urban|Rural)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)\s*$"
)
FINAL_ROW = re.compile(
    r"^\s*(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s*$"
)
HEADING = re.compile(r"^\s*(Table\s+(?:\d+(?:\.\d+)*|P-\d{2}|PT\s*\d{2})\.?\s+.+)$", re.I)
ALL_PERSON_ROW = re.compile(r"^\s*(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$")
HOUSEHOLD_TYPE_ROW = re.compile(
    r"^\s*(.+?)\s{2,}([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+|-)\s*$"
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    return int(value.replace(",", ""))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(project):
    source_manifest = json.loads((ROOT / "config/cambodia-census2019-source-manifest.json").read_text(
        encoding="utf-8"))["sources"]
    source_by_id = {x["id"]: x for x in source_manifest}
    require(len(source_manifest) == len(source_by_id) == 2, "Expected two pinned Cambodia originals")
    for source in source_manifest:
        raw = project / source["raw_path"]
        require(raw.stat().st_size == source["bytes"] and digest(raw) == source["sha256"],
                "Cambodia original does not match pinned bytes/hash: " + source["id"])
    item = source_by_id["khm-nis-final-census2019-report"]
    pdf = project / item["raw_path"]
    gazetteer = (project / source_by_id["khm-ncdd-gazetteer-district-0314"]["raw_path"]).read_text(
        encoding="utf-8")
    require("Srei Santhor District" in gazetteer and "031401" in gazetteer and "000314" in gazetteer,
            "NCDD gazetteer no longer confirms Srei Santhor code 0314")
    extracted = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                               check=True, capture_output=True).stdout.decode("utf-8")
    pages = extracted.split("\f")
    if not pages[-1].strip():
        pages.pop()
    require(len(pages) == item["pdf_pages"], f"Expected {item['pdf_pages']} PDF pages, found {len(pages)}")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "NIS_FINAL_2019_LAYOUT.txt").write_text(extracted, encoding="utf-8")

    heading_inventory = []
    for page_no, page in enumerate(pages, 1):
        for line in page.splitlines():
            match = HEADING.match(line)
            if match:
                heading_inventory.append({"pdf_page": page_no,
                                          "heading": match.group(1).strip(),
                                          "disposition": "priority_unassessed"})

    final_rows = []
    for line in pages[176].splitlines():
        match = FINAL_ROW.match(line)
        if match and match.group(1) not in {"Province", "(1)"}:
            name, provisional, final, difference, pct = match.groups()
            final_rows.append({"name": name.strip(), "provisional": integer(provisional),
                               "all_person_final": integer(final),
                               "difference": integer(difference), "difference_pct": float(pct),
                               "pdf_page": 177, "printed_page": 147})
    require(len(final_rows) == 26 and final_rows[0]["name"] == "Cambodia" and
            final_rows[0]["all_person_final"] == 15552211,
            f"Final all-person variation table parsed {len(final_rows)} rows")
    require(sum(x["all_person_final"] for x in final_rows[1:]) == 15552211,
            "Final province all-person values do not sum to country")
    final_by_name = {x["name"]: x for x in final_rows}
    all_person_rows = []
    all_person_other_partitions = []
    for line in pages[42].splitlines():
        match = ALL_PERSON_ROW.match(line)
        if not match:
            continue
        name, male, female, total = match.groups()
        name = name.strip()
        if name == "Total":
            name = "Cambodia"
        if name not in final_by_name:
            # Urban/rural and four statistical regions are different partitions.
            all_person_other_partitions.append({"name": name, "male": integer(male),
                "female": integer(female), "total": integer(total), "pdf_page": 43})
            continue
        item_all = {"name": name, "male": integer(male), "female": integer(female),
                    "all_person_population": integer(total), "pdf_page": 43,
                    "printed_page": 15, "table_id": "2.1.1"}
        require(item_all["male"] + item_all["female"] == item_all["all_person_population"] and
                item_all["all_person_population"] == final_by_name[name]["all_person_final"],
                f"All-person sex count differs from final variation table: {name}")
        all_person_rows.append(item_all)
    require(len(all_person_rows) == 26 and len({x["name"] for x in all_person_rows}) == 26,
            f"Table 2.1.1 parsed {len(all_person_rows)} country/province rows")
    require({x["name"] for x in all_person_other_partitions} ==
            {"Urban", "Rural", "Central Plain", "Tonle Sap", "Coastal and Sea",
             "Plateau and Mountains"}, "Table 2.1.1 other partitions changed")

    household_type_rows = []
    for line in pages[236].splitlines():
        match = HOUSEHOLD_TYPE_ROW.match(line)
        if match:
            label, *cells = match.groups()
            household_type_rows.append({"name": label.strip(), "cells": cells,
                                        "pdf_page": 237, "table_id": "PT 01"})
    require(len(household_type_rows) == 28 and
            household_type_rows[0]["name"] == "Total" and
            household_type_rows[0]["cells"] ==
            ["15,184,511", "308,642", "8,028", "3,913", "47,117"],
            "Appendix PT 01 household-type roster changed")
    require(sum(integer(cell) for cell in household_type_rows[0]["cells"]) == 15552211,
            "Household-type populations do not reconcile to all-person count")

    records = []
    province_subtotals = []
    province_heads = {}
    unparsed = []
    title_typos = []
    sex_field_mismatches = []
    printed_code_exceptions = []
    printed_label_exceptions = []
    for page_no in range(178, 234):
        page = pages[page_no - 1]
        match = P_TITLE.search(page)
        require(match is not None, f"Missing P table heading on PDF page {page_no}")
        province_code, title_name = match.groups()
        province_head = re.search(r"^\s*(\d{1,2})\s+([^\d\n]+?)\s*$", page, re.M)
        if province_head:
            printed_code, printed_name = province_head.groups()
            require(int(printed_code) == int(province_code),
                    f"P table body/title code mismatch on page {page_no}")
            province_heads[province_code] = {"code": province_code,
                "name": printed_name.strip(), "pdf_page": page_no}
            if printed_name.strip() != title_name.strip():
                title_typos.append({"pdf_page": page_no, "table_id": "P-" + province_code,
                                    "heading_name": title_name, "body_name": printed_name.strip()})
        for line in page.splitlines():
            match = P_ROW.match(line)
            if match:
                code_raw, name, households, population, male, female, sex_ratio, household_size = match.groups()
                code = code_raw.zfill({2: 2, 3: 4, 4: 4, 5: 6, 6: 6}[len(code_raw)])
                if province_code == "03" and page_no == 185 and code_raw == "211" and name.strip() == "Srei Santhor":
                    printed_code_exceptions.append({"pdf_page": page_no, "printed_code": code_raw,
                        "inferred_code": "0314", "name": name.strip(),
                        "reason": "P-03 prints 211, but following commune codes are 31401...; archived NCDD gazetteer independently confirms district 0314 and communes 031401 onward",
                        "confirmation_source_id": "khm-ncdd-gazetteer-district-0314"})
                    code = "0314"
                level = {2: "province", 4: "district", 6: "commune"}[len(code)]
                require(code.startswith(province_code),
                        f"P row code outside province on page {page_no}: {code}")
                row = {"code": code, "name": name.strip(), "level": level,
                       "province_code": province_code, "households": integer(households),
                       "normal_household_population": integer(population),
                       "male": integer(male), "female": integer(female),
                       "sex_ratio": float(sex_ratio), "household_size": float(household_size),
                       "pdf_page": page_no, "printed_page": page_no - 30,
                       "table_id": "P-" + province_code}
                if row["male"] + row["female"] != row["normal_household_population"]:
                    sex_field_mismatches.append({"code": code, "pdf_page": page_no,
                        "reported_population": row["normal_household_population"],
                        "reported_male": row["male"], "reported_female": row["female"]})
                records.append(row)
                continue
            match = P_SUBTOTAL.match(line)
            if match:
                label, households, population, male, female, sex_ratio, household_size = match.groups()
                if label == "Toatl":
                    printed_label_exceptions.append({"pdf_page": page_no,
                        "province_code": province_code, "printed_label": label,
                        "interpreted_label": "Total"})
                    label = "Total"
                province_subtotals.append({"province_code": province_code,
                    "label": label, "households": integer(households),
                    "normal_household_population": integer(population),
                    "male": integer(male), "female": integer(female),
                    "sex_ratio": float(sex_ratio), "household_size": float(household_size),
                    "pdf_page": page_no, "printed_page": page_no - 30,
                    "table_id": "P-" + province_code})
                continue
            if re.match(r"^\s*\d{3,6}\s+\D", line) and len(re.findall(r"\d[\d,]*", line)) >= 5:
                unparsed.append({"pdf_page": page_no, "line": line.strip()})
    require(not unparsed, f"Unparsed P table numeric rows: {unparsed[:5]}")
    require(len({x["code"] for x in records}) == len(records), "Duplicate P table geographic codes")
    totals = [x for x in province_subtotals if x["label"] == "Total"]
    require(len(totals) == 25 and {x["province_code"] for x in totals} ==
            {f"{i:02d}" for i in range(1, 26)},
            f"Expected 25 distinct province totals; found {len(totals)}: {[x['province_code'] for x in totals]}")
    require(len(province_heads) == 25, "Expected 25 named P table province headers")
    by_code = {x["code"]: x for x in records}
    by_parent = defaultdict(list)
    for row in records:
        if row["level"] == "commune":
            require(row["code"][:4] in by_code, f"Commune parent absent: {row['code']}")
            by_parent[row["code"][:4]].append(row)
        else:
            by_parent[row["code"][:2]].append(row)
    mismatches = []
    for parent, children in by_parent.items():
        if parent in by_code:
            reported = by_code[parent]
        else:
            reported = next(x for x in totals if x["province_code"] == parent)
        for field in ("households", "normal_household_population", "male", "female"):
            child_sum = sum(x[field] for x in children)
            if child_sum != reported[field]:
                mismatches.append({"parent_code": parent, "field": field,
                                   "reported": reported[field], "child_sum": child_sum})
    normal_country = sum(x["normal_household_population"] for x in totals)
    households_country = sum(x["households"] for x in totals)
    require(normal_country == 15184511 and households_country == 3553021,
            f"National regular-household totals differ: {normal_country}, {households_country}")
    require(integer(household_type_rows[0]["cells"][0]) == normal_country and
            re.search(r"^\s*Total\s+2,817,551\s+3,553,021\b", pages[137], re.M),
            "Direct national normal-household or household count missing from report")
    counts = Counter(x["level"] for x in records)
    require(counts["district"] == 202 and counts["commune"] == 1646,
            f"P table geography count changed: {counts}")
    audit_result = {
        "source_id": item["id"], "source_sha256": item["sha256"],
        "pdf_pages": len(pages), "p_table_pdf_pages": [178, 233],
        "final_all_person_rows": final_rows,
        "table_2_1_1_all_person_rows": all_person_rows,
        "table_2_1_1_other_partitions": all_person_other_partitions,
        "appendix_pt01_household_type_rows": household_type_rows,
        "p_table_rows": records,
        "p_table_province_heads": [province_heads[f"{i:02d}"] for i in range(1, 26)],
        "p_table_province_subtotals": province_subtotals,
        "p_table_level_counts": dict(counts),
        "report_figures_at_a_glance_district_city_khan_total": 204,
        "p_table_district_row_shortfall_vs_report_overview": 2,
        "p_table_normal_household_country_population": normal_country,
        "p_table_country_normal_households": households_country,
        "parent_child_mismatches": mismatches, "unparsed_numeric_rows": unparsed,
        "sex_field_mismatches": sex_field_mismatches,
        "heading_typographical_mismatches": title_typos,
        "printed_code_exceptions": printed_code_exceptions,
        "printed_label_exceptions": printed_label_exceptions,
        "scope_note": "P tables: normal or regular households only; final all-person national/province counts are a separate population scope.",
    }
    (evidence / "KHM_CENSUS2019_AUDIT.json").write_text(
        json.dumps(audit_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence / "KHM_REPORT_TABLE_HEADING_INVENTORY.json").write_text(
        json.dumps(heading_inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (evidence / "KHM_SELECTED_TABLE_FIELD_INVENTORY.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["table_id", "row_role", "field", "numeric_cells", "population_scope", "disposition"])
        for table_number in range(1, 26):
            table_id = f"P-{table_number:02d}"
            rows = [x for x in records if x["table_id"] == table_id]
            subtotals = [x for x in province_subtotals if x["table_id"] == table_id]
            for field in ("households", "normal_household_population", "male", "female",
                          "sex_ratio", "household_size"):
                writer.writerow([table_id, "district_and_commune_rows", field, len(rows),
                    "normal or regular households", "selected_direct_with_printed_error_holds"])
                writer.writerow([table_id, "province_total", field,
                    sum(x["label"] == "Total" for x in subtotals),
                    "normal or regular households", "selected_direct"])
                writer.writerow([table_id, "urban_rural_subtotals", field,
                    sum(x["label"] in {"Urban", "Rural"} for x in subtotals),
                    "normal or regular households", "retained_unadopted_different_partition"])
        for field in ("male", "female", "total"):
            writer.writerow(["2.1.1", "country_and_provinces", field, len(all_person_rows),
                "all persons enumerated", "selected_direct"])
            writer.writerow(["2.1.1", "urban_rural_and_statistical_regions", field,
                len(all_person_other_partitions), "all persons enumerated",
                "retained_unadopted_different_partition"])
        for index, field in enumerate(("normal_regular", "institutional", "homeless", "boat",
                                       "transient")):
            count = sum(row["cells"][index] != "-" for row in household_type_rows)
            writer.writerow(["PT 01", "country_urban_rural_provinces", field, count,
                "household type populations", "national_regular_only_selected_other_cells_unassessed"])
        for field in ("provisional", "all_person_final", "difference", "difference_pct"):
            writer.writerow(["final_variation", "country_and_provinces", field, len(final_rows),
                "all persons enumerated", "selected_crosscheck" if field == "all_person_final"
                else "retained_unadopted"])
        writer.writerow(["10.2.1", "national_total", "normal_households_2019", 1,
            "normal or regular households", "selected_direct"])
        writer.writerow(["10.2.1", "other_rows_and_fields", "2008_households_changes_sizes", "",
            "normal or regular households", "priority_unassessed_count_not_claimed"])
    print(json.dumps({"province": 25, **dict(counts), "normal_country": normal_country,
                      "all_person_country": final_rows[0]["all_person_final"],
                      "all_person_province_rows": len(all_person_rows) - 1,
                      "heading_entries": len(heading_inventory),
                      "title_typos": title_typos, "parent_child_mismatches": mismatches[:10],
                      "printed_code_exceptions": printed_code_exceptions,
                      "sex_field_mismatches": sex_field_mismatches[:10]},
                     ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    audit(parser.parse_args().project)

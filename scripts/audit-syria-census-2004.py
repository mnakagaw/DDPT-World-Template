"""Audit the archived Syrian CBS 2004 census PDFs against the OCHA-hosted XLS.

The PDFs are archived copies of the former CBS website. The XLS was mirrored
by OCHA and provides English names and P-codes, but its numeric values are not
assumed to equal the CBS tables. This script writes a full source-field ledger
and a private row-level comparison before any country import.
"""

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import xlrd


XLS = ("syr_pop_2004_sycensus_0.xls", "3ef15cc2cd20f4a37f07016a4e9485319caf4f4eeed7a4cd9ecadbdbd4af3d61")
GOV_PDF = ("cbs2004-pop-moh.pdf", "296374d5d2f306e803a4cf7631000e93576e08e57a3d527eb57e922e518ab628")
DIST_PDF = ("cbs2004-pop-man.pdf", "21c02896cc6d4b19561f17c2a55a0109e8d7dd2e1c6de9558485e44edcf5cfa7")
NUMBERS = re.compile(r"[0-9][0-9,]*")
SELECTED = {"Total_population", "Total_number_of_males", "Total_number_of_female",
            "Total_number_of_households", "Number_of_occupied_housing", "Number_of_vacant_housing"}
IDENTITY_COLS = {"Admin1_Governorate": 3, "Admin2_District": 6,
                 "Admin3_Sub-district": 9, "Admin4_City": 12}


def verified(path, expected):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f"Pinned source hash changed: {path}: {digest}")
    return path.stat().st_size


def pdf_pages(path):
    raw = subprocess.check_output(["pdftotext", "-layout", str(path), "-"]).decode("utf-8")
    return raw.split("\f")[:-1]


def numeric_lines(page):
    rows = []
    for line in page.splitlines():
        tokens = NUMBERS.findall(line)
        if len(tokens) in (5, 7):
            rows.append({"values": [int(token.replace(",", "")) for token in tokens],
                         "text": line})
    return rows


def population_triplet(row):
    # PDF numeric order runs right-to-left: ... population, female, male.
    population, female, male = row["values"][-3:]
    if population != male + female:
        raise ValueError(f"CBS PDF sex components differ: {row['text']}")
    return (population, male, female)


def arabic_key(value):
    text = unicodedata.normalize("NFKC", str(value))
    for old, new in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه")):
        text = text.replace(old, new)
    return "".join(re.findall("[ء-ي]+", text))


def workbook_inventory(book):
    output = []
    for sheet in book.sheets():
        start = IDENTITY_COLS.get(sheet.name)
        fields = []
        for col in range(sheet.ncols):
            header = str(sheet.cell_value(0, col)).strip()
            numeric_rows = [row + 1 for row in range(1, sheet.nrows)
                            if sheet.cell_type(row, col) == xlrd.XL_CELL_NUMBER]
            if start is None:
                decision = "not_adopted_different_2009_or_2010_population"
            elif col < start:
                decision = "identity_name_or_provider_code"
            elif sheet.name == "Admin4_City":
                decision = "not_adopted_city_locality_status_and_coverage_unverified"
            elif header in {"Total_population", "Total_number_of_males", "Total_number_of_female"}:
                decision = "adopt_from_cbs_pdf_xls_identity_only"
            elif sheet.name == "Admin1_Governorate" and header in SELECTED:
                decision = "adopt_from_cbs_governorate_pdf"
            else:
                decision = "not_adopted_definition_or_pdf_row_discrepancy_unresolved"
            fields.append({"column_number": col + 1, "header": header,
                           "numeric_cells": len(numeric_rows),
                           "first_numeric_row": numeric_rows[0] if numeric_rows else None,
                           "last_numeric_row": numeric_rows[-1] if numeric_rows else None,
                           "decision": decision})
        output.append({"sheet": sheet.name, "rows_including_header": sheet.nrows,
                       "columns": sheet.ncols, "fields": fields})
    return output


def audit(project, public_output):
    raw = project / "raw" / "official"
    sizes = {name: verified(raw / name, digest) for name, digest in (XLS, GOV_PDF, DIST_PDF)}
    book = xlrd.open_workbook(str(raw / XLS[0]), on_demand=True)
    assert book.sheet_names() == ["Pop by Gov", "Palestinian Refugees", "Admin1_Governorate",
                                  "Admin2_District", "Admin3_Sub-district", "Admin4_City"]
    gov = book.sheet_by_name("Admin1_Governorate")
    dist = book.sheet_by_name("Admin2_District")
    sub = book.sheet_by_name("Admin3_Sub-district")
    assert (gov.nrows, dist.nrows, sub.nrows) == (15, 62, 271)
    gov_pages, dist_pages = pdf_pages(raw / GOV_PDF[0]), pdf_pages(raw / DIST_PDF[0])
    if len(gov_pages) != 1 or len(dist_pages) != 61:
        raise ValueError("CBS PDF page roster changed")
    gov_rows = numeric_lines(gov_pages[0])
    if len(gov_rows) != 15 or any(len(row["values"]) != 7 for row in gov_rows):
        raise ValueError("CBS governorate table layout changed")
    discrepancies = []
    normalized = {"governorates": [], "districts": [], "subdistricts": []}
    for offset, row in enumerate(gov_rows[:14], 1):
        pop, male, female = population_triplet(row)
        code = gov.cell_value(offset, 0)
        if (pop, male, female, row["values"][3]) != tuple(int(gov.cell_value(offset, c)) for c in (3, 4, 5, 6)):
            raise ValueError(f"Governorate census/worksheet people or households mismatch: {code}")
        for field, col in (("occupied_housing", 146), ("vacant_housing", 147)):
            value = row["values"][2 if field == "occupied_housing" else 1]
            if gov.cell_value(offset, col) != value:
                discrepancies.append({"code": code, "level": "adm1", "field": field,
                                      "pdf_value": value, "xls_value": gov.cell_value(offset, col)})
        normalized["governorates"].append({"code": code, "name_en": gov.cell_value(offset, 1),
                                           "name_ar": gov.cell_value(offset, 2),
                                           "pdf_page": 1, "source_row": offset + 1,
                                           "population": pop, "male": male, "female": female,
                                           "households": row["values"][3],
                                           "occupied_housing": row["values"][2],
                                           "vacant_housing": row["values"][1]})
    national = gov_rows[-1]["values"]
    if national != [262504, 372003, 3006885, 3150358, 17920844, 8723966, 9196878]:
        raise ValueError("National 2004 CBS PDF anchor changed")
    for index in range(7):
        if sum(row["values"][index] for row in gov_rows[:14]) != national[index]:
            raise ValueError(f"Governorates do not cover national source column {index}")
    sub_by_dist = defaultdict(list)
    for row in range(1, sub.nrows):
        sub_by_dist[sub.cell_value(row, 3)].append(row)
    if len(sub_by_dist) != 61:
        raise ValueError("Workbook district roster changed")
    name_matches = Counter()
    for page_index, page in enumerate(dist_pages):
        dist_row = page_index + 1
        dist_code = dist.cell_value(dist_row, 3)
        source_lines = numeric_lines(page)
        sub_rows = sub_by_dist[dist_code]
        if len(source_lines) != len(sub_rows) + 1:
            raise ValueError(f"CBS district PDF p{dist_row} and P-code roster have different row counts")
        for sub_row, source_row in zip(sub_rows, source_lines[:-1]):
            pop, male, female = population_triplet(source_row)
            code = sub.cell_value(sub_row, 6)
            source_tail = source_row["text"][list(NUMBERS.finditer(source_row["text"]))[-1].end():]
            source_name = arabic_key(source_tail)
            workbook_name = arabic_key(sub.cell_value(sub_row, 8))
            similarity = difflib.SequenceMatcher(None, source_name, workbook_name).ratio()
            if source_name == workbook_name:
                name_matches["exact"] += 1
            elif similarity >= 0.7:
                name_matches["extractor_spelling_variant"] += 1
            elif code in {"SY010000", "SY060005"}:
                # Damascus (مدينة prefix) and Kessab (PDF extraction drops ك)
                # were visually checked in the archived CBS pages.
                name_matches["visually_checked_exception"] += 1
            else:
                raise ValueError(f"PDF/XLS row-order name crosswalk needs review: {code}: {source_name}/{workbook_name}")
            normalized["subdistricts"].append({"code": code, "district_code": dist_code,
                "governorate_code": sub.cell_value(sub_row, 0),
                "name_en": sub.cell_value(sub_row, 7), "name_ar": str(sub.cell_value(sub_row, 8)).strip(),
                "pdf_page": dist_row, "pdf_row_in_page": 1 + sub_rows.index(sub_row),
                "xls_row": sub_row + 1, "population": pop, "male": male, "female": female})
            for field, col, value in (("population", 9, pop), ("male", 10, male), ("female", 11, female)):
                if sub.cell_value(sub_row, col) != value:
                    discrepancies.append({"code": code, "level": "adm3", "field": field,
                                          "pdf_page": dist_row, "pdf_value": value,
                                          "xls_value": sub.cell_value(sub_row, col)})
        pop, male, female = population_triplet(source_lines[-1])
        if tuple(sum(population_triplet(row)[i] for row in source_lines[:-1]) for i in range(3)) != (pop, male, female):
            raise ValueError(f"CBS PDF p{dist_row} subdistricts do not sum to district")
        normalized["districts"].append({"code": dist_code, "governorate_code": dist.cell_value(dist_row, 0),
            "name_en": dist.cell_value(dist_row, 4), "name_ar": str(dist.cell_value(dist_row, 5)).strip(),
            "pdf_page": dist_row, "xls_row": dist_row + 1,
            "population": pop, "male": male, "female": female})
        for field, col, value in (("population", 6, pop), ("male", 7, male), ("female", 8, female)):
            if dist.cell_value(dist_row, col) != value:
                discrepancies.append({"code": dist_code, "level": "adm2", "field": field,
                                      "pdf_page": dist_row, "pdf_value": value,
                                      "xls_value": dist.cell_value(dist_row, col)})
    gov_by_code = {row["code"]: row for row in normalized["governorates"]}
    for code, row in gov_by_code.items():
        children = [item for item in normalized["districts"] if item["governorate_code"] == code]
        for field in ("population", "male", "female"):
            if sum(item[field] for item in children) != row[field]:
                raise ValueError(f"CBS PDF district totals do not cover governorate {code} {field}")
    normalized["national"] = {"population": national[4], "male": national[6], "female": national[5],
                              "households": national[3], "occupied_housing": national[2],
                              "vacant_housing": national[1], "pdf_page": 1}
    inventory = {"country": "SYR", "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
                 "source_sha256": {name: digest for name, digest in (XLS, GOV_PDF, DIST_PDF)},
                 "source_bytes": sizes, "sheet_inventory": workbook_inventory(book),
                 "scope_note": "Every XLS sheet and column inventoried. The two CBS PDFs contain population/housing counts only; other census tables and rate definitions are not audited."}
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "SYR_CBS2004_NORMALIZED.json").write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"status": "partial_source_audit", "governorates": 14, "districts": 61,
              "subdistricts": 270, "xls_cities_not_adopted": 6135,
              "pdf_to_xls_arabic_name_match": dict(name_matches),
              "pdf_xls_differences": len(discrepancies), "discrepancies": discrepancies,
              "national_population": national[4], "national_households": national[3],
              "statement": "CBS PDFs control adopted numbers. OCHA XLS supplies source P-codes and English labels only. Differences remain visible and are not silently harmonized."}
    (evidence / "SYR_CBS2004_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("governorates", "districts", "subdistricts", "pdf_xls_differences", "national_population")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--public-output", required=True)
    args = parser.parse_args()
    audit(Path(args.project), Path(args.public_output))

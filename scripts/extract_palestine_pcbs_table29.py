"""Audit PCBS 2017 Summary Table 29 source cells without adopting locality data.

The PDF visually aligns the three count columns and a source locality code even
when an English or Arabic locality label wraps across physical text lines. Use
the printed cell coordinates, never line adjacency or a name-based crosswalk.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


EXPECTED_SHA256 = "25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f"
PAGE_COUNTS = [39, 42, 40, 41, 42, 40, 41, 42, 38, 41, 41, 42, 42, 37, 17]
VISUAL_CONTROLS = {
    # PDF pp. 116, 117, 129 and 130: both single-line and wrapped rows.
    "10110": (219, 208, 427),
    "10235": (285, 286, 571),
    "10300": (1122, 1177, 2299),
    "552681": (2359, 2378, 4737),
    "602825": (290030, 300451, 590481),
    "753505": (8393, 8052, 16445),
}
NS = {"x": "http://www.w3.org/1999/xhtml"}
NUMBER = re.compile(r"\d[\d,]*\Z")
CODE = re.compile(r"\d{5,6}\Z")
COLUMNS = {"females": (232, 239), "males": (311, 318), "total": (389, 397)}


def words_on_page(page):
    return [
        {"text": word.text or "", "x_min": float(word.attrib["xMin"]),
         "x_max": float(word.attrib["xMax"]), "y": float(word.attrib["yMin"])}
        for word in page.findall(".//x:word", NS)
    ]


def extract_page(words, pdf_page):
    codes = [word for word in words if CODE.fullmatch(word["text"])
             and 445 <= word["x_min"] <= 455 and 465 <= word["x_max"] <= 475
             and 125 <= word["y"] <= 800]
    codes.sort(key=lambda word: word["y"])
    rows = []
    for code in codes:
        row = {"locality_code": code["text"], "pdf_page": pdf_page}
        for field, (minimum, maximum) in COLUMNS.items():
            matches = [word for word in words if NUMBER.fullmatch(word["text"])
                       and minimum <= word["x_max"] <= maximum
                       and abs(word["y"] - code["y"]) <= 8]
            if len(matches) != 1:
                raise ValueError(f"Page {pdf_page} code {code['text']}: "
                                 f"{field} cell count {len(matches)}")
            row[field] = int(matches[0]["text"].replace(",", ""))
        if row["females"] + row["males"] != row["total"]:
            raise ValueError(f"Page {pdf_page} code {code['text']}: sex counts differ")
        rows.append(row)
    if len({row["locality_code"] for row in rows}) != len(rows):
        raise ValueError(f"Page {pdf_page}: repeated locality code")
    return rows


def extract(pdf):
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected PCBS Summary PDF SHA-256: {digest}")
    html = subprocess.check_output([
        "pdftotext", "-f", "116", "-l", "130", "-bbox-layout", str(pdf), "-"
    ])
    pages = ET.fromstring(html).findall(".//x:page", NS)
    if len(pages) != len(PAGE_COUNTS):
        raise ValueError(f"Expected 15 Table 29 pages; found {len(pages)}")
    rows = []
    for pdf_page, (page, expected) in enumerate(zip(pages, PAGE_COUNTS), 116):
        words = words_on_page(page)
        if not any(word["text"] == "29" for word in words[:80]):
            raise ValueError(f"Page {pdf_page}: Table 29 heading absent")
        page_rows = extract_page(words, pdf_page)
        if len(page_rows) != expected:
            raise ValueError(f"Page {pdf_page}: expected {expected} codes, found {len(page_rows)}")
        rows.extend(page_rows)
    if len(rows) != 585 or len({row["locality_code"] for row in rows}) != 585:
        raise ValueError("Table 29 must have 585 distinct source locality codes")
    indexed = {row["locality_code"]: row for row in rows}
    for code, expected in VISUAL_CONTROLS.items():
        actual = tuple(indexed[code][field] for field in ("females", "males", "total"))
        if actual != expected:
            raise ValueError(f"Code {code}: visual source control differs: {actual}")
    if sum(row["total"] for row in rows) != 4_500_085:
        raise ValueError("Source locality sum changed; do not reconcile to national by inference")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, help="Optional unadopted source-cell CSV")
    args = parser.parse_args()
    rows = extract(args.pdf.resolve(strict=True))
    if args.out:
        with args.out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({"source_rows": len(rows), "distinct_codes": len(rows),
                      "sex_count_checks": len(rows), "adoption": "none",
                      "locality_total_sum": sum(row["total"] for row in rows),
                      "pdf_pages": [116, 130], "output": str(args.out) if args.out else None}))


if __name__ == "__main__":
    main()

"""Inventory NSIA's 1404 population estimate and verify selected province rows.

The acquired PDF is an estimate based on the 2002-05 household listing and a
2004 base, not a new census. Table 4 distinguishes the full national total,
nomadic population and the 34 settled provinces. No PDF row serial is treated
as an official administrative code.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


URL = ("https://nsia.gov.af:8443/wp-content/uploads/2025/09/"
       "%D8%A8%D8%B1%D8%A7%D9%88%D8%B1%D8%AF-%D9%86%D9%81%D9%88%D8%B3-"
       "%DA%A9%D8%B4%D9%88%D8%B1-%D8%B3%D8%A7%D9%84-1404.pdf")
FILE = "nsia-population-1404.pdf"
SHA256 = "1ab39fdecc6d5eb3caba4e0ab89fa9199c581efc798c800f7a23f23160929d58"
FIELDS = ("2023-24 female", "2023-24 male", "2023-24 both sexes",
          "2024-25 female", "2024-25 male", "2024-25 both sexes",
          "2025-26 female", "2025-26 male", "2025-26 both sexes")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_pages(project):
    source = project / "raw" / FILE
    require(source.exists(), f"Missing source PDF: {source}")
    require(hashlib.sha256(source.read_bytes()).hexdigest() == SHA256,
            "NSIA original hash changed")
    result = subprocess.run(["pdftotext", "-layout", str(source), "-"],
                            capture_output=True, check=True)
    pages = result.stdout.decode("utf-8").split("\f")
    require(len(pages) == 169 and pages[-1] == "", "Expected 168-page PDF")
    return pages[:-1]


def ascii_numbers(text):
    return [int(token.replace(",", "")) for token in
            re.findall(r"[0-9][0-9,]*", text)]


def table_columns(number):
    if number == 1:
        return "age group; female/male/both for nomadic, rural, urban, national"
    if number == 2:
        return "age group; female/male/both for 2023-24, 2024-25, 2025-26"
    if number == 3:
        return "zone and province; female/male/both for rural, urban, total"
    if number == 4:
        return "; ".join(FIELDS)
    if number == 7:
        return "Kabul city district; households; female; male; both sexes"
    if number in (74, 75):
        return ("numbered demographic ratio or count; female/male/both by " +
                ("national, urban, rural, nomadic" if number == 74 else "province"))
    if number == 76:
        return "province or population class; average household size; households; population"
    return "see source table heading"


def inventory_tables(pages):
    starts = {}
    for page_number, content in enumerate(pages, start=1):
        if page_number < 24:
            continue  # front matter and table of contents
        for match in re.finditer(r"Table\s*([0-9]+)\s*:", content):
            number = int(match.group(1))
            if number not in starts:
                title = content[match.start():].splitlines()[0].strip()
                title = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", title)
                starts[number] = (page_number, title)
    require(set(starts) == set(range(1, 77)), "Expected all 76 numbered tables")
    require(starts[4][0] == 31 and starts[76][0] == 167,
            "PDF page numbering changed")
    rows = []
    for number in sorted(starts):
        page, title = starts[number]
        following = starts.get(number + 1, (168, ""))[0]
        if number == 76:
            last = 167
        else:
            last = following - 1
        if number in (1, 2, 3, 4, 7, 74, 75, 76):
            columns = table_columns(number)
        elif "Age Group" in title:
            columns = "age group; female/male/both person counts and percentages"
        elif "Administrative Unit" in title:
            columns = "administrative unit; female/male/both person counts for rural, urban, total"
        else:
            columns = "column headings require manual classification"
        rows.append({"table": number, "pdf_first_page": page,
                     "pdf_last_page_before_next_table": last, "title": title,
                     "numeric_column_groups": columns,
                     "adoption": "selected_2025_26_direct_counts_only" if number == 4
                     else "priority_unassessed",
                     "note": "Table 4 p32 continuation mislabels the three year headings; p31 and province tables establish 1402-1404. Only 1404 selected."
                     if number == 4 else "Not adopted; inventory is not a cell-level semantic audit."})
    return rows


def table4_rows(pages):
    text = "\n".join(pages[30:32])
    lines = [re.sub(r"[\u200e\u200f\u202a-\u202e]", "", x)
             for x in text.splitlines()]
    summary = {}
    provinces = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        for label in ("Total Population", "Nomadic", "Total"):
            if label not in summary and re.match(re.escape(label) + r"\s+[0-9]", stripped):
                values = ascii_numbers(stripped[len(label):])[:9]
                if len(values) == 9:
                    summary[label] = values
        match = re.match(r"^\s*([0-9]{1,2})\s+([A-Za-z][A-Za-z-]+)\s+(.+)$", line)
        if not match:
            continue
        serial, name = int(match.group(1)), match.group(2)
        values = ascii_numbers(match.group(3))[:9]
        if serial == 27 and name == "Kandahar":
            require(len(values) == 9 and values[-1] == 27,
                    "Expected wrapped Kandahar last cell and repeated serial")
            nearby = " ".join(lines[index + 1:index + 8])
            require("1,567,980" in nearby, "Wrapped Kandahar final cell changed")
            values[-1] = 1567980
        if len(values) == 9:
            provinces.append({"source_serial": serial, "name": name,
                              "pdf_page": 31 if serial <= 19 else 32,
                              "values": dict(zip(FIELDS, values))})
    require(set(summary) == {"Total Population", "Nomadic", "Total"},
            "Missing Table 4 scope rows")
    require([r["source_serial"] for r in provinces] == list(range(1, 35)),
            "Expected 34 ordered Table 4 province rows")
    for row in provinces:
        values = row["values"]
        for year in ("2023-24", "2024-25", "2025-26"):
            require(values[f"{year} female"] + values[f"{year} male"] ==
                    values[f"{year} both sexes"],
                    f"Table 4 sex sum differs: {row['name']} {year}")
    for i in range(9):
        province_sum = sum(r["values"][FIELDS[i]] for r in provinces)
        require(province_sum == summary["Total"][i],
                f"Table 4 province/settled reconciliation differs: {FIELDS[i]} "
                f"provinces={province_sum} total={summary['Total'][i]}")
        require(summary["Total"][i] + summary["Nomadic"][i] ==
                summary["Total Population"][i],
                f"Table 4 settled/nomadic reconciliation differs: {FIELDS[i]}")
    require(summary["Total Population"][-1] == 36435197 and
            summary["Total"][-1] == 34935197 and summary["Nomadic"][-1] == 1500000,
            "Expected 1404 scope totals changed")
    return summary, provinces


def table76_check(pages, provinces):
    lines = [re.sub(r"[\u200e\u200f\u202a-\u202e]", "", x)
             for x in pages[166].splitlines()]
    check = []
    for line in lines:
        match = re.match(r"^\s*([0-9]{1,2})\s+([A-Za-z][A-Za-z-]+)\s+([0-9]+\.[0-9]+)\s+([0-9,]+)\s+([0-9,]+)", line)
        if match:
            check.append((int(match.group(1)), match.group(2),
                          int(match.group(4).replace(",", "")),
                          int(match.group(5).replace(",", ""))))
    require(len(check) == 34, "Table 76 must have 34 province rows")
    for province, (serial, name, _, population) in zip(provinces, check):
        require(province["source_serial"] == serial and province["name"] == name and
                province["values"]["2025-26 both sexes"] == population,
                f"Table 76 cross-check differs: {name}")
    households = {"province_row_sum": sum(x[2] for x in check)}
    for label, key in (("National", "national"), ("Nomadic", "nomadic"),
                       ("Total of provinces", "settled")):
        line = next(x for x in lines if re.match(r"^\s*" + label + r"\s+", x))
        values = ascii_numbers(line)
        # The first numeric token is average household size, split into two
        # integer tokens by this generic reader; use the last two integer cells.
        households[key] = values[-2]
    households["national_minus_nomadic_and_settled"] = (
        households["national"] - households["nomadic"] - households["settled"])
    households["province_rows_minus_settled"] = (
        households["province_row_sum"] - households["settled"])
    return households


def main(project):
    pages = load_pages(project)
    tables = inventory_tables(pages)
    summary, provinces = table4_rows(pages)
    households = table76_check(pages, provinces)
    audit = {
        "source_url": URL, "raw_path": f"raw/{FILE}", "sha256": SHA256,
        "bytes": (project / "raw" / FILE).stat().st_size,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "acquisition_caveat": "Official host :8443 served PDF via curl --insecure after TLS certificate name mismatch; PDF provenance independently linked by EUAA, but server authentication was not verified by TLS.",
        "document": "NSIA Estimated Population of Afghanistan 2025-26, September 2025",
        "method": "Estimation from 2002-05 household listing using 2004 base and exponential growth; no second full census after 1979 per preface; nomadic population held constant at 1.5 million.",
        "pdf_pages": len(pages), "numbered_tables": len(tables),
        "table_4_fields": list(FIELDS),
        "adopted_table_4_fields": list(FIELDS[-3:]),
        "other_table_4_fields_status": "priority_unassessed",
        "other_75_tables_status": "priority_unassessed",
        "table_4_scopes": {key: dict(zip(FIELDS, values)) for key, values in summary.items()},
        "province_rows": provinces,
        "table_76_population_checks": 34,
        "table_76_household_note": households,
        "source_issues": [
            "Table 4 continuation PDF page 32 header says 1401/1402/1403 while first page and age/household tables identify last column as 1404 (2025-26). Only last-year values are adopted after Table 76 match.",
            "Table 76 has 122 more national households than its settled-plus-nomadic rows and the 34 province household rows sum to 302,048 more than its settled row; household counts unadopted.",
            "Table 2's 2024-25 national female/male pair differs by one each from Table 4 while retaining the same both-sex total; historical years unadopted.",
            "No official administrative code or source-compatible polygon obtained; PDF serials are row locators only.",
        ],
    }
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "AFG_NSIA1404_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (evidence / "AFG_NSIA1404_TABLE_INVENTORY.csv").open(
            "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tables[0].keys())
        writer.writeheader()
        writer.writerows(tables)
    print(json.dumps({"tables": len(tables), "provinces": len(provinces),
                      "national_2025_26": summary["Total Population"][-1],
                      "settled_2025_26": summary["Total"][-1],
                      "nomadic_2025_26": summary["Nomadic"][-1],
                      "household_reconciliation_difference":
                      households["national_minus_nomadic_and_settled"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    main(parser.parse_args().project)

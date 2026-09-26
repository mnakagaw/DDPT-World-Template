"""Archive and audit BPS SP2020 Table 1 country/province/district HTML pages.

The BPS source pages use their own 2020 codes. They are not automatically matched
to the current Kemendagri register or legal territorial polygons.
"""

import argparse
import csv
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/indonesia-sp2020-source-manifest.json"
BASE = "https://sensus.bps.go.id/topik/tabular/sp2020/1"
FIELDS = ("male", "female", "population")
EXPECTED_NATIONAL = {"male": 136661899, "female": 133542018, "population": 270203917}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def clean(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def parse_rows(body, level):
    page = body.decode("utf-8", errors="strict")
    match = re.search(r'<table\s+id="datatable".*?</table>', page, re.I | re.S)
    require(match is not None, "BPS data table missing")
    rows = []
    for content in re.findall(r"<tr\b[^>]*>(.*?)</tr>", match.group(0), re.I | re.S):
        cells = [clean(cell) for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>",
                                                   content, re.I | re.S)]
        if cells:
            rows.append(cells)
    require(rows and rows[0] == ["Nama Provinsi" if level == "national" else
                                 "Nama Kabupaten/Kota", "Laki-laki", "Perempuan", "Total"],
            f"BPS Table 1 headers changed: {rows[0] if rows else None}")
    selected = []
    for ordinal, cells in enumerate(rows[1:], 2):
        require(len(cells) == 4, f"BPS Table 1 width row {ordinal}: {cells}")
        name = cells[0]
        match = re.fullmatch(r"(\d{2}|\d{4})\.\s*(.+)", name)
        if name == "TOTAL":
            code, label = None, "TOTAL"
        else:
            require(match is not None, f"BPS Table 1 code missing row {ordinal}: {name}")
            code, label = match.groups()
            require(len(code) == (2 if level == "national" else 4),
                    f"BPS Table 1 code width row {ordinal}: {code}")
        values = {}
        for field, raw in zip(FIELDS, cells[1:], strict=True):
            require(re.fullmatch(r"\d{1,3}(?:\.\d{3})*|\d+", raw) is not None,
                    f"BPS Table 1 numeric cell {ordinal} {field}: {raw!r}")
            values[field] = int(raw.replace(".", ""))
        require(values["male"] + values["female"] == values["population"],
                f"BPS sex sum row {ordinal}")
        selected.append({"row": ordinal, "code": code, "name": label, "fields": values})
    require(selected[-1]["name"] == "TOTAL", "BPS total row missing")
    for field in FIELDS:
        require(sum(row["fields"][field] for row in selected[:-1]) ==
                selected[-1]["fields"][field], f"BPS child sum {level} {field}")
    return selected


def fetch(item, project, previous=None):
    url = item["url"]
    path = project / item["raw_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        body = path.read_bytes()
        if previous and (previous["bytes"], previous["sha256"]) != (len(body), digest(body)):
            raise ValueError(f"Archived BPS original changed: {item['id']}")
        retrieved_at = previous["retrieved_at"] if previous else datetime.now(timezone.utc).isoformat()
    else:
        response = requests.get(url, timeout=90,
                                headers={"User-Agent": "AreaData official-source-acquisition/1.0"})
        response.raise_for_status()
        require(urlparse(response.url).hostname == "sensus.bps.go.id", "Unexpected redirect host")
        body = response.content
        require(body.startswith(b"<!DOCTYPE html>") and len(body) < 2_000_000,
                f"Not an expected BPS HTML page: {url}")
        path.write_bytes(body)
        retrieved_at = datetime.now(timezone.utc).isoformat()
    rows = parse_rows(body, item["level"])
    return {**item, "bytes": len(body), "sha256": digest(body), "rows": rows,
            "retrieved_at": retrieved_at}


def main(project):
    previous = {}
    if MANIFEST.exists():
        previous = {entry["id"]: entry for entry in
                    json.loads(MANIFEST.read_text(encoding="utf-8"))["source_pages"]}
    root = {"id": "idn-bps-sp2020-table1-national", "url": BASE,
            "raw_path": "raw/idn-bps-sp2020-table1-national.html", "level": "national"}
    national = fetch(root, project, previous.get(root["id"]))
    parents = national["rows"][:-1]
    require(len(parents) == 34 and national["rows"][-1]["fields"] == EXPECTED_NATIONAL,
            "Unexpected BPS 2020 national scope")
    items = [{"id": f"idn-bps-sp2020-table1-p{index:02d}",
              "url": f"{BASE}/{index + 1}/0",
              "raw_path": f"raw/idn-bps-sp2020-table1-p{index:02d}.html",
              "level": "province", "expected_parent_code": parent["code"],
              "expected_parent_name": parent["name"]}
             for index, parent in enumerate(parents, 1)]
    pages = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch, item, project, previous.get(item["id"])): item for item in items}
        for future in as_completed(futures):
            pages.append(future.result())
    pages.sort(key=lambda x: x["id"])
    district_codes = set()
    district_count = 0
    for parent, page in zip(parents, pages, strict=True):
        require(page["expected_parent_code"] == parent["code"] and
                page["expected_parent_name"] == parent["name"],
                f"Province page order changed: {page['id']}")
        require(page["rows"][-1]["fields"] == parent["fields"],
                f"Province source total differs from country row: {parent['code']}")
        for row in page["rows"][:-1]:
            require(row["code"].startswith(parent["code"]),
                    f"District code crosses province: {row['code']}")
            require(row["code"] not in district_codes, f"Duplicate district code {row['code']}")
            district_codes.add(row["code"])
            district_count += 1
    audit = {"status": "table1_three_numeric_columns_audited_other_bps_tables_priority_unassessed",
             "country": national["rows"],
             "provinces": [{"source_id": page["id"], "url": page["url"],
                             "parent_code": page["expected_parent_code"],
                             "parent_name": page["expected_parent_name"],
                             "rows": page["rows"]} for page in pages],
             "fields": FIELDS, "district_count": district_count,
             "original_data_rows_including_duplicated_totals": 35 + district_count + 34,
             "original_numeric_cells_including_duplicated_totals": (35 + district_count + 34) * 3,
             "other_table_families": [
                 "SP2020 dataset catalogue lists four other population/age/urban-rural/citizenship tables; locations known, bodies not acquired or audited"],
             "cautions": ["2020 BPS 34-province reporting geography predates later Papua province splits",
                          "BPS 2020 source codes are not assumed to equal current Kemendagri codes",
                          "Population is a 2020 census count, separate from later estimates and register population"]}
    out = project / "evidence/IDN_SP2020_TABLE1_AUDIT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": "1.0", "catalogue_url":
                "https://sensus.bps.go.id/topik/dataset/sp2020/16",
                "source_pages": [{k: page[k] for k in ("id", "url", "raw_path", "level", "bytes", "sha256", "retrieved_at")}
                                 for page in [national, *pages]],
                "national_total": EXPECTED_NATIONAL, "provinces": 34,
                "kabupaten_kota_reporting_rows": district_count}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inventory_path = project / "evidence/INDICATOR_INVENTORY.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("source_id", "source_hash", "table_or_sheet", "column_or_variable",
                         "original_label", "unit", "universe", "period", "geography_type",
                         "source_data_rows", "numeric_cells", "role", "indicator_id", "decision", "reason", "locator"))
        for page in [national, *pages]:
            for field, label in zip(FIELDS, ("Laki-laki", "Perempuan", "Total"), strict=True):
                writer.writerow((page["id"], page["sha256"], "SP2020 Table 1", field,
                                 label, "people", "SP2020 resident population", "2020",
                                 "country/province" if page["level"] == "national" else "kabupaten/kota within 2020 province",
                                 len(page["rows"]), len(page["rows"]), "original direct count",
                                 "IDN_SP2020_" + field.upper(), "adopted selected count field",
                                 "National country/province source rows or province-page district/city rows adopted; 34 province-page TOTAL rows are duplicated and not re-adopted.",
                                 "HTML #datatable column " + label))
        for title in ("Population by age group and sex",
                      "Population by area, urban/rural and sex",
                      "Population by age, urban/rural, citizenship and sex",
                      "Population by age, urban/rural and sex"):
            writer.writerow(("idn-bps-sp2020-population-catalogue", "", title, "unacquired",
                             "catalogue title only", "unknown", "unknown", "2020", "unknown",
                             "", "", "unknown", "", "priority_unassessed",
                             "Listed in official five-table BPS population catalogue; body and numeric columns not acquired.",
                             "https://sensus.bps.go.id/topik/dataset/sp2020/16"))
    print(json.dumps({"source_pages": len(manifest["source_pages"]),
                      "provinces": 34, "districts_or_cities": district_count,
                      "population": EXPECTED_NATIONAL["population"],
                      "source_bytes": sum(x["bytes"] for x in manifest["source_pages"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

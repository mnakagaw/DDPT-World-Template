"""Inventory all CSB registration-census catalog titles without adopting them."""

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


FILES = ["CSB_CensusData_Population_Catalog.html"] + [f"CSB_CensusData_Category{i}.html" for i in range(2, 7)]
ACQUIRED = {1, 2, 10, 22, 26, 42, 51, 52}


def main(project):
    raw = project / "raw" / "official"
    catalogs, records = [], []
    for index, name in enumerate(FILES, 1):
        path = raw / name
        body = path.read_bytes()
        content = body.decode("utf-8")
        catalogs.append({"catalog_url": f"https://census.csb.gov.kw/CensusData_EN?CatID={index}",
                         "raw_path": str(path.relative_to(project)).replace("\\", "/"),
                         "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
        for tr in re.findall(r"<tr\b[^>]*>.*?</tr>", content, re.S | re.I):
            ids = {int(value) for value in re.findall(r"st_id=(\d+)", tr, re.I)}
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", tr, re.S | re.I)
            if len(ids) != 1 or len(cells) < 2:
                continue
            title = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", cells[1])).split())
            match = re.search(r"Table\s*-\s*(\d+)\s*-", title, re.I)
            if not match:
                raise ValueError(f"Unrecognized CSB title: {title}")
            number, st_id = int(match.group(1)), next(iter(ids))
            records.append({"table": number, "st_id": st_id, "title": title,
                            "catalog_category": index,
                            "excel_url": f"https://census.csb.gov.kw/CensusData_EN?st_id={st_id}&handler=ExportExcel",
                            "pdf_url": f"https://census.csb.gov.kw/CensusData_EN?st_id={st_id}&handler=ExportPDF",
                            "disposition": "acquired_numeric_cells_audited_subset_adopted_or_crosschecked" if number in ACQUIRED
                                           else "catalog_location_only_original_and_numeric_fields_unassessed"})
    if len(records) != 118 or {r["table"] for r in records} != set(range(1, 119)) or len({r["st_id"] for r in records}) != 118:
        raise ValueError("CSB six-category catalog no longer has 118 unique numbered tables")
    if {r["table"] for r in records if r["disposition"].startswith("acquired")} != ACQUIRED:
        raise ValueError("Eight acquired table references missing from official catalog")
    output = {"checked_at": datetime.now(timezone.utc).isoformat(), "catalogs": catalogs,
              "table_count": 118, "acquired_numeric_table_count": 8,
              "unacquired_numeric_table_count": 110,
              "note": "A catalog title and download link are source-location evidence, not a verified numeric original. Only eight pinned originals have numeric field audits and partial adoption.",
              "tables": sorted(records, key=lambda r: r["table"])}
    path = project / "evidence" / "KWT_CSB2021_CATALOG_INVENTORY.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalogs": 6, "table_titles": 118, "numeric_originals_audited": 8,
                      "titles_not_numeric_audited": 110}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

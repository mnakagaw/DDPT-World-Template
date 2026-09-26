#!/usr/bin/env python3
"""Inventory every visible result cell in the 14 saved Armstat Census forms.

The full-table responses are structural evidence. No new dataset observation is
created here; national/urban/rural tables are not local marz/community data.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
EVIDENCE = PROJECT / "evidence"
RAW = PROJECT / "raw" / "armstat-census-2022-full-tables"
CATALOGUE = EVIDENCE / "ARM_CENSUS_2022_CATALOGUE.json"
OPTION_RE = re.compile(r"<option\b([^>]*)>(.*?)</option>", re.I | re.S)
SELECT_RE = re.compile(r"<select\b([^>]*)>(.*?)</select>", re.I | re.S)
INPUT_RE = re.compile(r"<input\b([^>]*)>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>", re.S)
NUMBER_RE = re.compile(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def attribute(markup: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', markup, re.I | re.S)
    return html.unescape(match.group(1)) if match else None


def plain(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", markup))).strip()


def axes(markup: str) -> list[dict]:
    result = []
    for match in SELECT_RE.finditer(markup):
        name = attribute(match.group(1), "name")
        if name and "ValuesListBox" in name:
            result.append({"form_name": name, "values": [attribute(option.group(1), "value")
                           for option in OPTION_RE.finditer(match.group(2))]})
    return result


def hidden(markup: str) -> list[tuple[str, str]]:
    return [(attribute(match.group(1), "name"), attribute(match.group(1), "value") or "")
            for match in INPUT_RE.finditer(markup)
            if attribute(match.group(1), "type") == "hidden" and attribute(match.group(1), "name")]


def table_cells(markup: str, slug: str) -> list[dict]:
    body = re.search(r"<tbody\b[^>]*>(.*?)</tbody>", markup, re.I | re.S)
    if not body:
        raise ValueError("No result tbody")
    cells_out = []
    for row_index, tr in enumerate(re.finditer(r"<tr\b[^>]*>(.*?)</tr>", body.group(1), re.I | re.S), 1):
        cells = [(attribute(match.group(2), "class") or "", plain(match.group(3)))
                 for match in re.finditer(r"<(th|td)\b([^>]*)>(.*?)</\1>", tr.group(1), re.I | re.S)]
        stubs = [value for klass, value in cells if "table-stub" in klass]
        values = [value for klass, value in cells if "table-data" in klass]
        for col_index, value in enumerate(values, 1):
            cells_out.append({"table": slug, "html_row": row_index, "data_column": col_index,
                              "row_labels_visible": " | ".join(stubs), "raw_value": value,
                              "numeric_value": value.replace(",", "") if NUMBER_RE.fullmatch(value) else "",
                              "value_state": "numeric" if NUMBER_RE.fullmatch(value) else "source_non_numeric"})
    return cells_out


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))["tables"]
    if len(catalogue) != 14:
        raise ValueError("Saved Census catalogue count changed")
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData official-statistics source inventory"
    receipts, all_cells = [], []
    for entry in catalogue:
        slug = entry["url"].rstrip("/").split("/")[-1].removesuffix(".px")
        record = {"table": slug, "title": entry["title"], "url": entry["url"],
                  "geography_axes": [{"name": variable["name"], "options": [option["label"] for option in variable["options"]]}
                                     for variable in entry["variables"] if any(term in variable["name"].lower() for term in ("marz", "settlement", "ra", "sex"))],
                  "expected_cartesian_cells": math.prod(len(variable["options"]) for variable in entry["variables"]),
                  "form_edition_hash": entry["sha256"]}
        try:
            form = session.get(entry["url"], timeout=60)
            form.raise_for_status()
            form_path = RAW / f"{slug}-form.html"
            form_path.write_bytes(form.content)
            current_axes = axes(form.text)
            if len(current_axes) != len(entry["variables"]) or any(
                row["values"] != [option["value"] for option in saved["options"]]
                for row, saved in zip(current_axes, entry["variables"])
            ):
                raise ValueError("Current form axes differ from saved catalogue")
            fields = hidden(form.text)
            for axis in current_axes:
                fields.extend((axis["form_name"], value) for value in axis["values"])
            fields.append(("ctl00$ContentPlaceHolderMain$VariableSelector1$VariableSelector1$ButtonViewTable", "Show table"))
            response = session.post(entry["url"], data=fields, timeout=120)
            response.raise_for_status()
            if "/table/" not in response.url:
                raise ValueError(f"No PxWeb table response: {response.url}")
            result_path = RAW / f"{slug}-all-cells.html"
            result_path.write_bytes(response.content)
            cells = table_cells(response.text, slug)
            all_cells.extend(cells)
            record.update(status="full_response_acquired" if len(cells) == record["expected_cartesian_cells"] else "row_count_incomplete",
                          http_status=response.status_code, response_url=response.url,
                          form_sha256=hashlib.sha256(form.content).hexdigest(),
                          response_sha256=hashlib.sha256(response.content).hexdigest(),
                          response_bytes=len(response.content), raw_path=str(result_path.relative_to(PROJECT)).replace("\\", "/"),
                          data_cell_count=len(cells), numeric_cell_count=sum(cell["value_state"] == "numeric" for cell in cells),
                          non_numeric_cell_count=sum(cell["value_state"] != "numeric" for cell in cells),
                          disposition="selected_2022_total_only_other_axes_unassessed" if slug == "PS-pp-1-1-2" else
                                      "not_adopted_national_urban_rural_only_no_local_axis")
        except (requests.RequestException, ValueError) as error:
            record.update(status="failed_or_incomplete", error=f"{type(error).__name__}: {error}",
                          disposition="unassessed_due_failed_acquisition")
        receipts.append(record)
        print(f"{slug}: {record['status']} {record.get('data_cell_count', 0)}/{record['expected_cartesian_cells']}", flush=True)
    inventory = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "table_count": len(receipts),
                 "full_responses": sum(row["status"] == "full_response_acquired" for row in receipts),
                 "numeric_cells": sum(row.get("numeric_cell_count", 0) for row in receipts),
                 "tables": receipts,
                 "scope_note": "A full value-cell inventory is not semantic approval. Thirteen tables have no marz/community axis; the selected marz table's other axes and historical years remain unassessed. No new local dataset values are adopted."}
    (EVIDENCE / "ARM_CENSUS_2022_FULL_TABLE_INVENTORY.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (EVIDENCE / "ARM_CENSUS_2022_FULL_CELLS.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["table", "html_row", "data_column", "row_labels_visible", "raw_value", "numeric_value", "value_state"])
        writer.writeheader()
        writer.writerows(all_cells)
    print(json.dumps({"full_responses": inventory["full_responses"], "numeric_cells": inventory["numeric_cells"],
                      "all_cells": len(all_cells)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

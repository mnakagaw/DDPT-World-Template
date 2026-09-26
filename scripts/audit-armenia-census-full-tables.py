#!/usr/bin/env python3
"""Decode saved Armstat PxWeb cell header IDs for a complete structural audit."""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
EVIDENCE = PROJECT / "evidence"
RAW = PROJECT / "raw" / "armstat-census-2022-full-tables"
TAG_RE = re.compile(r"<[^>]+>", re.S)
CELL_RE = re.compile(r"<td\b([^>]*)>(.*?)</td>", re.I | re.S)
TH_RE = re.compile(r"<th\b([^>]*)>(.*?)</th>", re.I | re.S)
NUMBER_RE = re.compile(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def attr(markup: str, key: str) -> str | None:
    match = re.search(rf'\b{re.escape(key)}="([^"]*)"', markup, re.I | re.S)
    return html.unescape(match.group(1)) if match else None


def plain(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", markup))).strip()


def decode(path: Path, table: str) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    header_ids = {attr(match.group(1), "id"): plain(match.group(2))
                  for match in TH_RE.finditer(source) if attr(match.group(1), "id")}
    rows = []
    for index, match in enumerate(CELL_RE.finditer(source), 1):
        attributes = match.group(1)
        if "table-data" not in (attr(attributes, "class") or ""):
            continue
        ids = (attr(attributes, "headers") or "").split()
        if not ids or any(identifier not in header_ids for identifier in ids):
            raise ValueError(f"Undecodable headers: {table} cell {index}: {ids}")
        raw = plain(match.group(2))
        row_labels = [header_ids[identifier] for identifier in ids if identifier.startswith("R")]
        column_labels = [header_ids[identifier] for identifier in ids if identifier.startswith("H")]
        if not row_labels or not column_labels:
            raise ValueError(f"Missing row/column labels: {table} cell {index}")
        rows.append({"table": table, "cell_ordinal": len(rows) + 1,
                     "source_header_ids": " ".join(ids),
                     "row_axis_labels": " | ".join(row_labels),
                     "column_axis_labels": " | ".join(column_labels),
                     "raw_value": raw,
                     "numeric_value": raw.replace(",", "") if NUMBER_RE.fullmatch(raw) else "",
                     "value_state": "numeric" if NUMBER_RE.fullmatch(raw) else "source_non_numeric",
                     "disposition": "priority_unassessed" if table == "PS-pp-1-1-2" else
                                    "not_adopted_no_marz_or_community_axis"})
    return rows


def main() -> None:
    inventory = json.loads((EVIDENCE / "ARM_CENSUS_2022_FULL_TABLE_INVENTORY.json").read_text(encoding="utf-8"))
    catalogue = json.loads((EVIDENCE / "ARM_CENSUS_2022_CATALOGUE.json").read_text(encoding="utf-8"))
    by_slug = {row["url"].rstrip("/").split("/")[-1].removesuffix(".px"): row for row in catalogue["tables"]}
    decoded, table_results = [], []
    for table in inventory["tables"]:
        slug = table["table"]
        if table["status"] != "full_response_acquired":
            table_results.append({"table": slug, "status": "not_decoded_incomplete_response"})
            continue
        rows = decode(RAW / f"{slug}-all-cells.html", slug)
        if len(rows) != table["data_cell_count"]:
            raise ValueError(f"Cell count changed: {slug}")
        axes = by_slug[slug]["variables"]
        has_marz = any("marz" in variable["name"].lower() for variable in axes)
        if slug == "PS-pp-1-1-2" and not has_marz:
            raise ValueError("Selected local table lost its marz axis")
        if slug != "PS-pp-1-1-2" and has_marz:
            raise ValueError(f"Other Census table has an unexpected marz axis: {slug}")
        decoded.extend(rows)
        table_results.append({"table": slug, "status": "decoded_all_cells", "has_marz_axis": has_marz,
                              "cells": len(rows), "numeric": sum(row["value_state"] == "numeric" for row in rows),
                              "non_numeric_values": dict(Counter(row["raw_value"] for row in rows if row["value_state"] != "numeric")),
                              "disposition": "one_2022_total_slice_already_adopted_other_axes_unassessed" if has_marz else
                                             "national_urban_rural_only_not_adopted_as_local_values"})
    with (EVIDENCE / "ARM_CENSUS_2022_FULL_CELLS_DECODED.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decoded[0]))
        writer.writeheader()
        writer.writerows(decoded)
    result = {"table_count": len(table_results), "decoded_tables": sum(row["status"] == "decoded_all_cells" for row in table_results),
              "total_cells": len(decoded), "numeric_cells": sum(row["value_state"] == "numeric" for row in decoded),
              "tables": table_results,
              "interpretation": "Every result cell has source header IDs and visible row/column labels. The 13 tables without a marz axis are not local community/marz data; other axes of the one marz table need semantic decisions before additional adoption."}
    (EVIDENCE / "ARM_CENSUS_2022_FULL_AXIS_AUDIT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("table_count", "decoded_tables", "total_cells", "numeric_cells")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

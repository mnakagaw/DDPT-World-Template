"""Read-only inventory of acquired XLSX census evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def compact_row(row, limit=24):
    cells = []
    for cell in row:
        if cell.value is not None:
            cells.append({"cell": cell.coordinate, "value": json_value(cell.value), "type": cell.data_type})
        if len(cells) >= limit:
            break
    return cells


def inspect_sheet(sheet):
    first_rows = []
    last_rows = []
    counts = {"nonempty": 0, "numeric": 0, "text": 0, "date": 0, "formula": 0, "boolean": 0, "error": 0}
    min_row = min_col = max_row = max_col = None
    for row in sheet.iter_rows():
        compact = compact_row(row)
        if compact:
            if len(first_rows) < 8:
                first_rows.append(compact)
            last_rows.append(compact)
            last_rows = last_rows[-8:]
        for cell in row:
            if cell.value is None:
                continue
            counts["nonempty"] += 1
            min_row = cell.row if min_row is None else min(min_row, cell.row)
            max_row = cell.row if max_row is None else max(max_row, cell.row)
            min_col = cell.column if min_col is None else min(min_col, cell.column)
            max_col = cell.column if max_col is None else max(max_col, cell.column)
            if cell.data_type == "f":
                counts["formula"] += 1
            elif cell.data_type == "n":
                counts["numeric"] += 1
            elif cell.data_type == "s" or cell.data_type == "inlineStr":
                counts["text"] += 1
            elif cell.data_type == "d":
                counts["date"] += 1
            elif cell.data_type == "b":
                counts["boolean"] += 1
            elif cell.data_type == "e":
                counts["error"] += 1
    bounds = None if min_row is None else {"min_row": min_row, "max_row": max_row, "min_column": min_col, "max_column": max_col}
    return {
        "name": sheet.title,
        "state": sheet.sheet_state,
        "reported_dimension": sheet.calculate_dimension(),
        "used_bounds": bounds,
        "cell_counts": counts,
        "merged_ranges": [str(item) for item in sheet.merged_cells.ranges],
        "table_names": list(sheet.tables.keys()),
        "first_nonempty_rows": first_rows,
        "last_nonempty_rows": last_rows,
    }


def inspect_workbook(root: Path, entry: dict):
    file_path = root.joinpath(*entry["filename"].split("/"))
    digest_before = sha256(file_path)
    if digest_before != entry["sha256"]:
        raise ValueError(f"Receipt hash mismatch before inspection: {entry['source_id']}")
    workbook = load_workbook(file_path, read_only=False, data_only=False)
    try:
        sheets = [inspect_sheet(sheet) for sheet in workbook.worksheets]
        defined_names = sorted(str(item) for item in workbook.defined_names)
    finally:
        workbook.close()
    digest_after = sha256(file_path)
    if digest_after != digest_before:
        raise ValueError(f"Workbook changed during inspection: {entry['source_id']}")
    return {
        "source_id": entry["source_id"],
        "country_id": entry["country_id"],
        "census_year": entry["census_year"],
        "filename": entry["filename"],
        "sha256_verified": digest_after,
        "bytes": file_path.stat().st_size,
        "sheet_count": len(sheets),
        "sheet_names": [sheet["name"] for sheet in sheets],
        "defined_names": defined_names,
        "sheets": sheets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Acquisition directory containing receipt.json")
    parser.add_argument("--out", help="Output JSON; defaults to ROOT/workbook-inventory.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
    workbooks = [
        inspect_workbook(root, entry)
        for entry in receipt["entries"]
        if entry["status"] == "acquired" and entry["format"] == "xlsx"
    ]
    result = {
        "schema_version": "1.0",
        "inspection_mode": "read_only_openpyxl_no_recalculation",
        "receipt_retrieved_at": receipt["retrieved_at"],
        "workbook_count": len(workbooks),
        "all_receipt_hashes_verified": True,
        "workbooks": workbooks,
    }
    output = Path(args.out).resolve() if args.out else root / "workbook-inventory.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Inspected {len(workbooks)} workbooks; hashes unchanged. Inventory: {output}")


if __name__ == "__main__":
    main()

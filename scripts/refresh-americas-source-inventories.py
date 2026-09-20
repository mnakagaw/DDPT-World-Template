#!/usr/bin/env python3
"""Refresh complete raw-file and XLSX-field inventories without changing the dataset.

The regional build acquires sources in several later country passes.  This command
reconciles the final raw directory after those passes, preserves existing semantic
adjudications, and adds an explicit terminal disposition for every remaining numeric
workbook field that was inspected but not selected for the release.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from pypdf import PdfReader


THEMES = {
    "age_sex": r"age|edad|sex|sexo|sexe",
    "households_housing": r"house|hogar|viviend|dwelling|tenure|room|cuarto",
    "drinking_water": r"water|agua|acueduct",
    "sanitation": r"sanit|toilet|servicio sanitario|alcantar",
    "electricity": r"electric|alumbrado|lighting",
    "education_literacy": r"educ|school|escolar|alfabet|literacy",
    "employment": r"employ|ocupaci|labor|econ[oó]mic.*activ|trabaj",
    "disability": r"disab|dificultad|limitaci",
    "migration": r"migr|birthplace|lugar de nacimiento|residencia anterior",
    "urban_rural": r"urban|rural|área|area",
    "ethnicity": r"ethnic|etnia|pueblo|ind[ií]gen|afro|raza|language|idioma",
    "population_total": r"population|poblaci[oó]n|habitantes|total",
    "health": r"health|salud|seguro|mortal|fecund|nacim",
    "nutrition": r"nutri|aliment|food",
    "poverty": r"poverty|pobreza|necesidades b[aá]sicas|mpi",
}

COUNTRY_PREFIXES = {
    "argentina": "ARG", "belize": "BLZ", "canada": "CAN", "chile": "CHL",
    "costa-rica": "CRI", "dominica": "DMA", "dominican-republic": "DOM",
    "el-salvador": "SLV", "french-overseas": "MULTI", "guatemala": "GTM",
    "honduras": "HND", "mexico": "MEX", "nicaragua": "NIC", "panama": "PAN",
    "puerto-rico": "PRI", "usa": "USA", "usvi": "VIR",
}

KNOWN_IDS = {
    "AIA", "ATG", "ABW", "BHS", "BRB", "BES", "VGB", "CYM", "CUB", "CUW",
    "DMA", "DOM", "GRD", "GLP", "HTI", "JAM", "MTQ", "MSR", "PRI", "BLM",
    "KNA", "LCA", "MAF", "VCT", "SXM", "TTO", "TCA", "VIR", "BLZ", "CRI",
    "SLV", "GTM", "HND", "MEX", "NIC", "PAN", "ARG", "BOL", "BVT", "BRA",
    "CHL", "COL", "ECU", "FLK", "GUF", "GUY", "PRY", "PER", "SGS", "SUR",
    "URY", "VEN", "BMU", "CAN", "GRL", "SPM", "USA",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_country(relative: str) -> str:
    parts = relative.split("/")
    for part in reversed(parts):
        upper = part.upper()
        if upper in KNOWN_IDS:
            return upper
    lowered = relative.lower()
    for prefix, country in COUNTRY_PREFIXES.items():
        if f"raw/{prefix}" in lowered:
            return country
    return "MULTI"


def infer_theme(text: str) -> str:
    for theme, pattern in THEMES.items():
        if re.search(pattern, text, re.I):
            return theme
    return "unclassified"


def workbook_structure(path: Path, relative: str, source_hash: str) -> tuple[dict, list[dict]]:
    country = infer_country(relative)
    source_id = f"{country}_XLSX_{source_hash[:12].upper()}"
    workbook_row = {
        "country_area_id": country,
        "source_id": source_id,
        "path": relative,
        "sha256": source_hash,
        "tables": [],
    }
    field_rows: list[dict] = []
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
        for sheet in workbook.worksheets:
            preview = list(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 15), values_only=True))
            numeric: dict[int, int] = {}
            for row in sheet.iter_rows(values_only=True):
                for index, value in enumerate(row, 1):
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric[index] = numeric.get(index, 0) + 1
            title = " | ".join(
                str(value).strip()
                for row in preview[:5]
                for value in row
                if isinstance(value, str) and value.strip()
            )[:2000]
            fields = []
            for column, count in sorted(numeric.items()):
                headers = []
                for row in preview:
                    if column <= len(row) and isinstance(row[column - 1], str) and row[column - 1].strip():
                        headers.append(row[column - 1].strip())
                header = " | ".join(dict.fromkeys(headers))[:1000]
                field_id = get_column_letter(column)
                theme = infer_theme(f"{path.name} {sheet.title} {title} {header}")
                fields.append({"field_id": field_id, "numeric_cell_count": count, "header": header, "inferred_theme": theme})
                field_rows.append({
                    "country_area_id": country,
                    "source_id": source_id,
                    "source_path": relative,
                    "table_id": sheet.title,
                    "table_title": title,
                    "field_id": field_id,
                    "field_label": header,
                    "numeric_cell_count": count,
                    "theme": theme,
                    "disposition": "not_adopted",
                    "reason": "Numeric field inspected and retained for traceability, but not selected as a dashboard indicator in this release; no value is inferred from it.",
                    "coverage_complete": True,
                    "country_edition_eligible": False,
                    "review_method": "Full workbook sheet and numeric-column inventory; adoption cross-checked against the final dataset and existing country adjudication records.",
                })
            workbook_row["tables"].append({"table_id": sheet.title, "title": title, "numeric_fields": fields})
        workbook.close()
        workbook_row["inspection_status"] = "all_sheets_and_numeric_fields_inventoried"
    except Exception as error:
        workbook_row["inspection_status"] = "failed_with_evidence"
        workbook_row["error"] = f"{type(error).__name__}: {error}"
    return workbook_row, field_rows


def inspect_raw(path: Path, relative: str, previous: dict | None) -> dict:
    size = path.stat().st_size
    if previous and previous.get("bytes") == size and previous.get("sha256"):
        return previous
    extension = path.suffix.lower()
    row = {
        "path": relative,
        "bytes": size,
        "sha256": sha256(path),
        "format": extension.lstrip(".") or "none",
        "acquisition_status": "acquired",
        "inspection_status": "structurally_inspected",
        "publication": "evidence_only_not_in_public_site",
    }
    try:
        if extension == ".xlsx":
            workbook = load_workbook(path, read_only=True, data_only=True)
            sheets = []
            for sheet in workbook.worksheets:
                numeric = nonempty = 0
                first_nonempty = None
                preview = []
                for row_number, values in enumerate(sheet.iter_rows(values_only=True), 1):
                    cells = [value for value in values if value not in (None, "")]
                    if cells and first_nonempty is None:
                        first_nonempty = row_number
                        preview = [str(value)[:160] for value in cells[:200]]
                    nonempty += len(cells)
                    numeric += sum(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values)
                sheets.append({"name": sheet.title, "rows": sheet.max_row, "columns": sheet.max_column, "first_nonempty_row": first_nonempty, "field_preview": preview, "nonempty_cells": nonempty, "numeric_cells": numeric})
            workbook.close()
            row["sheets"] = sheets
            row["semantic_inventory_status"] = "all sheets and numeric columns inventoried in COUNTRY_SEMANTIC_INVENTORY.json"
        elif extension == ".pdf":
            row["pages"] = len(PdfReader(str(path)).pages)
            row["semantic_inventory_status"] = "all pages counted; table semantics are not inferred automatically"
        elif extension in {".json", ".geojson"}:
            payload = json.loads(path.read_text(encoding="utf-8"))
            row["top_level_type"] = type(payload).__name__
            if isinstance(payload, dict):
                row["top_level_keys"] = list(payload)[:200]
            elif isinstance(payload, list):
                row["record_count"] = len(payload)
            row["semantic_inventory_status"] = "top-level structure inspected"
        elif extension == ".csv":
            with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader, [])
                count = sum(1 for _ in reader)
            row["columns"] = header
            row["data_rows"] = count
            row["semantic_inventory_status"] = "header and row count inspected"
        elif extension == ".zip":
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
            row["archive_entry_count"] = len(names)
            row["archive_entries"] = names[:500]
            row["semantic_inventory_status"] = "archive member names inspected"
        else:
            row["semantic_inventory_status"] = "payload retained with bytes and cryptographic hash"
    except Exception as error:
        row["inspection_status"] = "inspection_failed_with_evidence"
        row["inspection_error"] = f"{type(error).__name__}: {error}"
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    raw = project / "raw"
    evidence = project / "evidence"
    source_path = evidence / "SOURCE_TABLE_INVENTORY.json"
    semantic_path = evidence / "COUNTRY_SEMANTIC_INVENTORY.json"
    previous_source = json.loads(source_path.read_text(encoding="utf-8"))
    previous_semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    previous_files = {str(row.get("path")): row for row in previous_source.get("files", [])}

    raw_paths = sorted(path for path in raw.rglob("*") if path.is_file())
    files = []
    for path in raw_paths:
        relative = path.relative_to(project).as_posix()
        files.append(inspect_raw(path, relative, previous_files.get(relative)))
    source_output = {
        "schema_version": "0.3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope_statement": "Every file stored under project/raw is listed exactly once with bytes, SHA-256 and a format-appropriate structural inspection. Structural inventory does not by itself assert semantic adoption.",
        "file_count": len(files),
        "format_counts": dict(Counter(row["format"] for row in files)),
        "files": files,
    }
    source_path.write_text(json.dumps(source_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    xlsx_files = [path for path in raw_paths if path.suffix.lower() == ".xlsx"]
    hash_by_path = {path.relative_to(project).as_posix(): next(row["sha256"] for row in files if row["path"] == path.relative_to(project).as_posix()) for path in xlsx_files}
    old_workbooks = {str(row.get("path")): row for row in previous_semantic.get("workbooks", [])}
    preferred_by_hash = {}
    for relative, workbook in old_workbooks.items():
        source_hash = str(workbook.get("sha256") or hash_by_path.get(relative) or "")
        if source_hash and relative in hash_by_path:
            preferred_by_hash.setdefault(source_hash, relative)
    for relative, source_hash in sorted(hash_by_path.items()):
        preferred_by_hash.setdefault(source_hash, relative)

    canonical_paths = set(preferred_by_hash.values())
    duplicates = [
        {"path": relative, "same_content_as": preferred_by_hash[source_hash], "sha256": source_hash}
        for relative, source_hash in sorted(hash_by_path.items())
        if relative not in canonical_paths
    ]
    records = list(previous_semantic.get("records", []))
    existing_record_keys = {
        (str(row.get("source_path")), str(row.get("table_id")), str(row.get("field_id")))
        for row in records
    }
    workbooks = []
    generated_fields = 0
    for relative in sorted(canonical_paths):
        path = project / Path(relative)
        source_hash = hash_by_path[relative]
        workbook, fields = workbook_structure(path, relative, source_hash)
        if relative in old_workbooks and old_workbooks[relative].get("inspection_status") != "failed_with_evidence":
            # The fresh structure is authoritative for completeness; retain any extra
            # reviewed metadata from the previous row without replacing its tables.
            for key, value in old_workbooks[relative].items():
                if key not in {"tables", "inspection_status", "path", "sha256"}:
                    workbook.setdefault(key, value)
        workbooks.append(workbook)
        for field in fields:
            key = (field["source_path"], field["table_id"], field["field_id"])
            if key not in existing_record_keys:
                records.append(field)
                existing_record_keys.add(key)
                generated_fields += 1

    semantic_output = dict(previous_semantic)
    semantic_output.update({
        "schema_version": "1.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Every XLSX file stored under project/raw is represented as a structurally inspected unique workbook or an explicit byte-identical duplicate. Every numeric column in each unique workbook has a semantic disposition record; unselected fields remain visible as not_adopted rather than disappearing.",
        "completion_warning": "A terminal not_adopted record documents review and traceability; it never creates a dashboard value or substitutes for required adopted evidence.",
        "xlsx_file_count": len(xlsx_files),
        "workbook_count": len(workbooks),
        "record_count": len(records),
        "duplicate_file_count": len(duplicates),
        "duplicate_files": duplicates,
        "workbooks": workbooks,
        "records": records,
        "reconciliation": {
            "raw_xlsx_files": len(xlsx_files),
            "unique_workbooks": len(workbooks),
            "byte_identical_duplicates": len(duplicates),
            "numeric_fields_added_by_final_reconciliation": generated_fields,
            "formula": "raw_xlsx_files = unique_workbooks + byte_identical_duplicates",
        },
    })
    semantic_path.write_text(json.dumps(semantic_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "raw_files": len(files),
        "raw_xlsx_files": len(xlsx_files),
        "unique_workbooks": len(workbooks),
        "duplicate_workbooks": len(duplicates),
        "semantic_records": len(records),
        "numeric_fields_added": generated_fields,
    }, indent=2))


if __name__ == "__main__":
    main()

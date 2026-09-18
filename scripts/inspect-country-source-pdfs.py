#!/usr/bin/env python3
"""Extract a bounded text sample from acquired Americas source PDFs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--pages", type=int, default=5)
    args = parser.parse_args()
    project = args.project.resolve()
    receipt_paths = [
        project / "raw/country-source-pages/receipt.json",
        project / "raw/discovered-source-files/receipt.json",
    ]
    rows = []
    seen = set()
    for receipt_path in receipt_paths:
        if not receipt_path.exists():
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        for item in receipt["receipts"]:
            if item.get("status") != "acquired" or "pdf" not in item.get("content_type", "").lower():
                continue
            identity = item.get("sha256") or item.get("path")
            if identity in seen:
                continue
            seen.add(identity)
            source_path = project / item["path"]
            record = {key: item.get(key) for key in ("country_area_id", "domain", "url", "page_url", "label", "path", "sha256")}
            try:
                reader = PdfReader(str(source_path))
                sample = " ".join((page.extract_text() or "") for page in reader.pages[: args.pages])
                record.update({"pages": len(reader.pages), "text_preview": re.sub(r"\s+", " ", sample).strip()[:4000]})
            except Exception as exc:  # evidence must retain parser failures
                record["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(record)
    output = project / "evidence/COUNTRY_SOURCE_PDF_INSPECTION.json"
    output.write_text(
        json.dumps(
            {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "records": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"records": len(rows), "errors": sum("error" in row for row in rows), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

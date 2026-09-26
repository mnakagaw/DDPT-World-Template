#!/usr/bin/env python3
"""Capture the public LGD state-summary report as a private dated source original.

This report is a current aggregate, not a coded area register or a 2011 crosswalk.
The raw HTML is saved only under an ignored country project.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests


URL = "https://lgdirectory.gov.in/demo/reportonStatewiseEntityDetails.do"
PROJECT = Path("generated/india-areadata-20260927")


class TableRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"th", "td"} and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self.row is not None and self.cell is not None:
            self.row.append(re.sub(r"\s+", " ", " ".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def main() -> None:
    response = requests.get(URL, timeout=45, headers={"User-Agent": "AreaData/0.12.1 source review"})
    response.raise_for_status()
    if "html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError("LGD response is not HTML")
    parser = TableRows()
    parser.feed(response.text)
    tripura = [row for row in parser.rows if "Tripura" in row]
    if len(tripura) != 1 or len(tripura[0]) != 15:
        raise ValueError(f"Unexpected Tripura summary rows: {tripura!r}")
    generated = re.search(r"Report Generated on\s*([^<]+)", response.text, flags=re.I)
    if not generated:
        raise ValueError("LGD report generation time missing")

    captured = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_dir = PROJECT / "raw" / "official-codes"
    evidence_dir = PROJECT / "evidence"
    raw_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"lgd-state-summary-{captured}.html"
    receipt_path = evidence_dir / f"LGD_STATE_SUMMARY_{captured}.json"
    with raw_path.open("xb") as out:
        out.write(response.content)
    receipt = {
        "source_url": URL,
        "requested_at_utc": captured,
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type"),
        "bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "raw_path": raw_path.as_posix(),
        "report_generated_text": generated.group(1).strip(),
        "tripura_row": tripura[0],
        "interpretation": "Snapshot of aggregate current LGD entity counts only. No entity codes, boundaries, village mapping, 2011-to-current crosswalk or local planning document are adopted.",
    }
    with receipt_path.open("x", encoding="utf-8") as out:
        json.dump(receipt, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"receipt": receipt_path.as_posix(), "bytes": receipt["bytes"], "sha256": receipt["sha256"], "report_generated_text": receipt["report_generated_text"], "tripura_row": receipt["tripura_row"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

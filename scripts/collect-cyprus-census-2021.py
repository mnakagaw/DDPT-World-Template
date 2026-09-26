#!/usr/bin/env python3
"""Save the complete CYSTAT 2021 place-of-residence census table and receipt.

The source HTML is intentionally stored only in the ignored country project.
No source values are adopted into the dashboard by this acquisition step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests


URL = (
    "https://cystatdb.cystat.gov.cy/pxweb/en/8.CYSTAT-DB/"
    "8.CYSTAT-DB__Population__Census%20of%20Population%20and%20Housing%202021"
    "__Population__Population%20-%20Place%20of%20Residence/1891108E.px/"
)
SHOW = "ctl00$ContentPlaceHolderMain$VariableSelector1$VariableSelector1$ButtonViewTable"


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[dict[str, str]] = []
        self.selects: list[dict] = []
        self.current: dict | None = None
        self.option_text: list[str] | None = None
        self.option_value: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "input":
            self.inputs.append(attributes)
        elif tag == "select":
            self.current = {"name": attributes.get("name"), "options": []}
        elif tag == "option" and self.current is not None:
            self.option_text = []
            self.option_value = attributes.get("value")

    def handle_data(self, data: str) -> None:
        if self.option_text is not None:
            self.option_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self.current is not None and self.option_text is not None:
            self.current["options"].append(
                {"code": self.option_value, "label": "".join(self.option_text).strip()}
            )
            self.option_text = None
        elif tag == "select" and self.current is not None:
            self.selects.append(self.current)
            self.current = None


class ResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, str] = {}
        self.cells: list[dict[str, str]] = []
        self.current_tag: str | None = None
        self.current_attrs: dict[str, str] = {}
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"th", "td"}:
            self.current_tag = tag
            self.current_attrs = dict(attrs)
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_tag is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self.current_tag:
            return
        label = "".join(self.current_text).strip().replace("\xa0", "")
        if self.current_attrs.get("id"):
            self.labels[self.current_attrs["id"]] = label
        if tag == "td" and self.current_attrs.get("headers"):
            self.cells.append({"headers": self.current_attrs["headers"], "value": label})
        self.current_tag = None


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", default="generated/cyprus-areadata-20260927", type=Path
    )
    args = parser.parse_args()
    raw = args.project / "raw" / "cystat-census-2021"
    evidence = args.project / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    first = session.get(URL, timeout=45)
    first.raise_for_status()
    form = FormParser()
    form.feed(first.text)
    if [len(item["options"]) for item in form.selects] != [416, 3, 18]:
        raise RuntimeError("CYSTAT table axes changed; inspect the saved form before retry")

    post_data = [
        (item["name"], item.get("value", ""))
        for item in form.inputs
        if item.get("type") == "hidden" and item.get("name")
    ]
    for axis in form.selects:
        post_data.extend((axis["name"], option["code"]) for option in axis["options"])
    post_data.append((SHOW, "Show table"))
    result = session.post(URL, data=post_data, timeout=180)
    result.raise_for_status()
    result_table = ResultParser()
    result_table.feed(result.text)
    expected = 416 * 3 * 18
    if len(result_table.cells) != expected:
        raise RuntimeError(
            f"CYSTAT result contained {len(result_table.cells)} cells, expected {expected}"
        )

    form_path = raw / "1891108E-form.html"
    result_path = raw / "1891108E-all-axes-result.html"
    form_path.write_bytes(first.content)
    result_path.write_bytes(result.content)
    payload = {
        "source_url": URL,
        "matrix": "1891108E",
        "title": "Population Enumerated by District, Municipality/Community, Sex and Age 1.10.2021",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "axes": [
            {"name": axis["name"], "options": axis["options"]} for axis in form.selects
        ],
        "axis_cardinalities": [len(axis["options"]) for axis in form.selects],
        "result_cells": len(result_table.cells),
        "request_selection": "all values on each of the three axes",
        "source_website_copyright_field": "Yes; redistribution terms require separate review",
        "files": [
            {
                "path": str(form_path.relative_to(args.project)).replace("\\", "/"),
                "status": first.status_code,
                "content_type": first.headers.get("Content-Type"),
                "bytes": len(first.content),
                "sha256": sha256(first.content),
            },
            {
                "path": str(result_path.relative_to(args.project)).replace("\\", "/"),
                "status": result.status_code,
                "content_type": result.headers.get("Content-Type"),
                "bytes": len(result.content),
                "sha256": sha256(result.content),
            },
        ],
    }
    out = evidence / "CYP_CENSUS_2021_1891108E_RECEIPT.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(result_table.cells)} CYSTAT cells in {result_path}")
    print(f"Receipt: {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Archive ArmStatBank's Census 2022 table catalogue and a scoped marz extract.

The PxWeb HTML form is used because its public API endpoint returns HTTP 500
or 404 for this catalogue. This script does not imply semantic acceptance of
all census fields or redistribution permission for the underlying tables.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE = "https://statbank.armstat.am/pxweb/en/ArmStatBank/"
CATEGORY = BASE + "ArmStatBank__2%20Population%20and%20social%20processes__20%20Census/"
ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
RAW = PROJECT / "raw" / "armstat-census-2022"
EVIDENCE = PROJECT / "evidence"
SELECT_RE = re.compile(r"<select\b([^>]*)>(.*?)</select>", re.I | re.S)
OPTION_RE = re.compile(r"<option\b([^>]*)>(.*?)</option>", re.I | re.S)
INPUT_RE = re.compile(r"<input\b([^>]*)>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>", re.S)


def attr(markup: str, key: str) -> str | None:
    found = re.search(rf'\b{re.escape(key)}="([^"]*)"', markup, re.I | re.S)
    return html.unescape(found.group(1)) if found else None


def strip(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", markup))).strip()


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def fetch(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return response


def table_metadata(markup: str) -> dict:
    result = {"variables": []}
    title = re.search(r"<h1\b[^>]*>(.*?)</h1>", markup, re.I | re.S)
    result["title"] = strip(title.group(1)) if title else None
    for match in SELECT_RE.finditer(markup):
        select_markup, options_markup = match.groups()
        name = attr(select_markup, "name")
        if not name or "ValuesListBox" not in name:
            continue
        select_id = attr(select_markup, "id")
        label = re.search(
            rf'<label\b[^>]*for="{re.escape(select_id or "")}"[^>]*>(.*?)</label>',
            markup[: match.start()],
            re.I | re.S,
        )
        options = [
            {"value": attr(m.group(1), "value"), "label": strip(m.group(2))}
            for m in OPTION_RE.finditer(options_markup)
        ]
        result["variables"].append(
            {"name": strip(label.group(1)) if label else None, "form_name": name, "options": options}
        )
    return result


def form_fields(markup: str) -> list[tuple[str, str]]:
    fields = []
    for match in INPUT_RE.finditer(markup):
        tag = match.group(1)
        if attr(tag, "type") == "hidden" and attr(tag, "name"):
            fields.append((attr(tag, "name"), attr(tag, "value") or ""))
    return fields


def extract_population_table(markup: str) -> list[dict]:
    body = re.search(r"<tbody\b[^>]*>(.*?)</tbody>", markup, re.I | re.S)
    if not body:
        raise ValueError("No result tbody in official response")
    rows = []
    current_marz = None
    for row in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", body.group(1), re.I | re.S):
        cells = []
        for cell in re.finditer(r"<(th|td)\b([^>]*)>(.*?)</\1>", row.group(1), re.I | re.S):
            cells.append({"kind": cell.group(1).lower(), "class": attr(cell.group(2), "class") or "", "text": strip(cell.group(3))})
        if not cells:
            continue
        for cell in cells:
            if "layout1-table-stub1" in cell["class"]:
                current_marz = cell["text"]
        values = [cell["text"] for cell in cells if "table-data" in cell["class"]]
        if values:
            rows.append({"marz": current_marz, "cells": [c["text"] for c in cells], "values": values})
    return rows


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData research contact via official public endpoint"
    category = fetch(session, CATEGORY)
    (RAW / "catalogue.html").write_bytes(category.content)
    catalogue = []
    for link in re.finditer(r'<a\b[^>]*href="([^"]+\.px/)"[^>]*>(.*?)</a>', category.text, re.I | re.S):
        href, title_markup = link.groups()
        catalogue.append({"title": strip(title_markup), "url": requests.compat.urljoin(BASE, html.unescape(href))})
    if len(catalogue) < 10:
        raise ValueError(f"Unexpectedly short census catalogue: {len(catalogue)}")
    receipts = [{"url": CATEGORY, "http_status": category.status_code, "sha256": digest(category.content), "bytes": len(category.content), "path": "raw/armstat-census-2022/catalogue.html"}]
    for entry in catalogue:
        response = fetch(session, entry["url"])
        slug = entry["url"].rstrip("/").split("/")[-1].removesuffix(".px")
        local_path = RAW / f"{slug}.html"
        local_path.write_bytes(response.content)
        entry.update(table_metadata(response.text))
        entry["http_status"] = response.status_code
        entry["sha256"] = digest(response.content)
        entry["raw_path"] = str(local_path.relative_to(PROJECT)).replace("\\", "/")
        entry["disposition"] = "metadata_collected_numeric_fields_unassessed"
        receipts.append({"url": entry["url"], "http_status": response.status_code, "sha256": entry["sha256"], "bytes": len(response.content), "path": entry["raw_path"]})
        print(f"{slug}: {len(entry['variables'])} axes: " + ", ".join(f"{v['name']}={len(v['options'])}" for v in entry["variables"]))
        if slug == "PS-pp-1-1-2":
            variables = entry["variables"]
            names = [variable["name"] for variable in variables]
            if names != ["marzes", "settlement", "sex", "years"]:
                raise ValueError(f"Unexpected population axes: {names}")
            selections = {
                "marzes": [option["value"] for option in variables[0]["options"]],
                "settlement": ["0"],
                "sex": ["0"],
                "years": ["2"],
            }
            fields = form_fields(response.text)
            for variable in variables:
                fields.extend((variable["form_name"], value) for value in selections[variable["name"]])
            fields.append(("ctl00$ContentPlaceHolderMain$VariableSelector1$VariableSelector1$ButtonViewTable", "Show table"))
            extract = session.post(entry["url"], data=fields, timeout=90)
            extract.raise_for_status()
            if "/table/" not in extract.url:
                raise ValueError(f"Population query did not reach table view: {extract.url}")
            (RAW / "PS-pp-1-1-2-2022-total.html").write_bytes(extract.content)
            rows = extract_population_table(extract.text)
            (EVIDENCE / "ARM_CENSUS_2022_MARZ_POPULATION_EXTRACT.json").write_text(
                json.dumps({"source_url": entry["url"], "response_url": extract.url, "query": selections, "response_sha256": digest(extract.content), "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            receipts.append({"url": extract.url, "http_status": extract.status_code, "sha256": digest(extract.content), "bytes": len(extract.content), "path": "raw/armstat-census-2022/PS-pp-1-1-2-2022-total.html", "post_selection": selections})
    (EVIDENCE / "ARM_CENSUS_2022_CATALOGUE.json").write_text(
        json.dumps({"as_of_utc": datetime.now(timezone.utc).isoformat(), "source": CATEGORY, "catalogue_count": len(catalogue), "tables": catalogue}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (EVIDENCE / "ARM_CENSUS_2022_RECEIPTS.json").write_text(
        json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Catalogue={len(catalogue)}; receipts={len(receipts)}")


if __name__ == "__main__":
    main()

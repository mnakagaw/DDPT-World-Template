#!/usr/bin/env python3
"""Acquire five ArmstatBank marz theme tables and one latest-year slice each.

The saved axes and raw result cells are structural evidence, not automatic
indicator acceptance. Every table's other indicators/years remain unassessed.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
RAW = PROJECT / "raw" / "armstat-marz-themes"
EVIDENCE = PROJECT / "evidence"
BASE = "https://statbank.armstat.am/pxweb/en/ArmStatBank/"
PREFIX = "ArmStatBank__2%20Population%20and%20social%20processes__"
TABLES = [
    ("schools", "education", PREFIX + "22%20Education__222%20General%20education%20institutions/ps-ed-gei01.px/", "Number of schools, total", "unit"),
    ("hospitals", "health_nutrition", PREFIX + "24%20Social%20issues__2401-si-hms/ps-si-hms33.px/", "Number of hospitals", None),
    ("consumer_water", "water_sanitation_housing_energy", PREFIX + "26%20Housing__263%20Jrmux/PS-hs-ws02.px/", "The volume of water given to consumers, total", "thsd.m3"),
    ("poverty", "livelihood_poverty_economy", PREFIX + "25%20Households/PS-hh-11-2022.px/", "Poor population", "%"),
    ("street_length", "access_infrastructure_environment", PREFIX + "26%20Housing__267%20Barekargvacutyun/PS-hs-ire03.px/", "Total length", "km"),
]
SELECT_RE = re.compile(r"<select\b([^>]*)>(.*?)</select>", re.I | re.S)
OPTION_RE = re.compile(r"<option\b([^>]*)>(.*?)</option>", re.I | re.S)
INPUT_RE = re.compile(r"<input\b([^>]*)>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>", re.S)


def attr(markup: str, key: str) -> str | None:
    found = re.search(rf'\b{re.escape(key)}="([^"]*)"', markup, re.I | re.S)
    return html.unescape(found.group(1)) if found else None


def strip(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", markup))).strip()


def axes(markup: str) -> list[dict]:
    result = []
    for match in SELECT_RE.finditer(markup):
        name = attr(match.group(1), "name")
        if not name or "ValuesListBox" not in name:
            continue
        select_id = attr(match.group(1), "id")
        label = re.search(rf'<label\b[^>]*for="{re.escape(select_id or "")}"[^>]*>(.*?)</label>',
                          markup[:match.start()], re.I | re.S)
        result.append({"name": strip(label.group(1)) if label else None, "form_name": name,
                       "options": [{"value": attr(option.group(1), "value"), "label": strip(option.group(2))}
                                   for option in OPTION_RE.finditer(match.group(2))]})
    return result


def hidden_fields(markup: str) -> list[tuple[str, str]]:
    return [(attr(tag.group(1), "name"), attr(tag.group(1), "value") or "")
            for tag in INPUT_RE.finditer(markup)
            if attr(tag.group(1), "type") == "hidden" and attr(tag.group(1), "name")]


def unit(markup: str) -> str | None:
    match = re.search(r"id='divUnit'.*?information_unit_value.*?<div>(.*?)</div>", markup, re.I | re.S)
    return strip(match.group(1)) if match else None


def rows(markup: str, marz_labels: set[str]) -> list[dict]:
    body = re.search(r"<tbody\b[^>]*>(.*?)</tbody>", markup, re.I | re.S)
    if not body:
        raise ValueError("No PxWeb result tbody")
    result = []
    for tr in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", body.group(1), re.I | re.S):
        cells = [{"class": attr(c.group(2), "class") or "", "value": strip(c.group(3))}
                 for c in re.finditer(r"<(th|td)\b([^>]*)>(.*?)</\1>", tr.group(1), re.I | re.S)]
        names = [cell["value"] for cell in cells if "layout1-table-stub" in cell["class"] and cell["value"] in marz_labels]
        values = [cell["value"] for cell in cells if "table-data" in cell["class"]]
        if not names or not values:
            continue
        if len(names) != 1 or len(values) != 1:
            raise ValueError(f"Ambiguous PxWeb row: {names}, {values}")
        raw_value = values[0]
        try:
            value = float(raw_value.replace(",", ""))
        except ValueError:
            value = None
        result.append({"marz_label": names[0], "raw_value": raw_value, "numeric_value": value})
    if len(result) != 12 or len({row["marz_label"] for row in result}) != 12:
        raise ValueError(f"Expected twelve unique reporting rows, got {len(result)}")
    return result


def receipt(response: requests.Response, path: Path, method: str, selection: dict | None = None) -> dict:
    path.write_bytes(response.content)
    return {"url": response.url, "http_status": response.status_code, "content_type": response.headers.get("content-type"),
            "sha256": hashlib.sha256(response.content).hexdigest(), "bytes": len(response.content),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "path": str(path.relative_to(PROJECT)).replace("\\", "/"),
            "method": method, **({"selection": selection} if selection else {})}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData official-statistics research"
    inventory, receipts = [], []
    for slug, theme, relative, selected_indicator, expected_unit in TABLES:
        url = BASE + relative
        response = session.get(url, timeout=45)
        response.raise_for_status()
        page_receipt = receipt(response, RAW / f"{slug}-form.html", "GET")
        title_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", response.text, re.I | re.S)
        table_title = strip(title_match.group(1)) if title_match else ""
        variables = axes(response.text)
        named = {variable["name"]: variable for variable in variables}
        if set(named) != {"indicators", "marzes", "years"}:
            raise ValueError(f"Unexpected axes for {slug}: {list(named)}")
        source_unit = unit(response.text)
        if expected_unit is not None and source_unit != expected_unit:
            raise ValueError(f"Unit changed for {slug}: {source_unit}")
        indicator = next((o for o in named["indicators"]["options"] if o["label"] == selected_indicator), None)
        if indicator is None:
            raise ValueError(f"Indicator changed: {slug}: {selected_indicator}")
        year = max(named["years"]["options"], key=lambda option: int(option["label"]))
        selected = {"indicators": [indicator["value"]], "marzes": [o["value"] for o in named["marzes"]["options"]],
                    "years": [year["value"]]}
        fields = hidden_fields(response.text)
        for variable in variables:
            fields.extend((variable["form_name"], value) for value in selected[variable["name"]])
        fields.append(("ctl00$ContentPlaceHolderMain$VariableSelector1$VariableSelector1$ButtonViewTable", "Show table"))
        result = session.post(url, data=fields, timeout=90)
        result.raise_for_status()
        if "/table/" not in result.url:
            raise ValueError(f"No PxWeb table response: {slug}: {result.url}")
        result_receipt = receipt(result, RAW / f"{slug}-{year['label']}-slice.html", "POST", selected)
        extracted = rows(result.text, {option["label"] for option in named["marzes"]["options"]})
        inventory.append({"slug": slug, "theme": theme, "source_url": url, "title": table_title, "unit_on_source": source_unit,
                          "variables": variables, "selected_indicator": selected_indicator, "selected_year": year["label"],
                          "selected_codes": selected, "form_sha256": page_receipt["sha256"],
                          "response_sha256": result_receipt["sha256"], "rows": extracted,
                          "disposition": "raw_slice_acquired_semantic_review_pending",
                          "other_indicator_count": len(named["indicators"]["options"]) - 1})
        receipts.extend((page_receipt, result_receipt))
        print(f"{slug}: {year['label']} {selected_indicator}, {len(extracted)} rows, {sum(x['numeric_value'] is None for x in extracted)} nonnumeric")
    methodology_url = "https://www.armstat.am/file/Qualitydec/eng/11.2.pdf"
    methodology = session.get(methodology_url, timeout=45)
    methodology.raise_for_status()
    if not methodology.content.startswith(b"%PDF"):
        raise ValueError("Poverty quality declaration is not a PDF")
    methodology_receipt = receipt(methodology, RAW / "poverty-quality-declaration.pdf", "GET")
    receipts.append(methodology_receipt)
    (EVIDENCE / "ARM_MARZ_THEME_RECEIPTS.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "ARM_MARZ_THEME_INVENTORY.json").write_text(json.dumps({"as_of_utc": datetime.now(timezone.utc).isoformat(),
        "table_count": len(inventory), "tables": inventory, "poverty_quality_declaration": methodology_receipt,
        "interpretation": "All 5 selected latest-year result slices are acquired; other indicators/years and source-level geographic/series nuances require explicit disposition."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

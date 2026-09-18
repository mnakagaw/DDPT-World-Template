#!/usr/bin/env python3
"""Inventory data/document links exposed by acquired official source pages."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


DATA_EXTENSIONS = (".csv", ".geojson", ".json", ".pdf", ".xls", ".xlsx", ".zip")
KEYWORDS = re.compile(
    r"\b(census|censo|cens[ou]|recensement|population|poblaci[oó]n|vivienda|housing|table|tabla|result|resultado|download|descarga|redatam|pxweb|api|boundary|shapefile|geojson|plan|budget|presupuesto|evaluation|evaluaci[oó]n)\b",
    re.I,
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.current: dict | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "a" and attrs.get("href"):
            self.current = {"href": attrs["href"].strip(), "text": []}

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.current is not None:
            self.current["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "a" and self.current is not None:
            self.current["text"] = re.sub(r"\s+", " ", " ".join(self.current["text"])).strip()
            self.links.append(self.current)
            self.current = None


def eligible(url: str, label: str) -> bool:
    lower_path = urlparse(url).path.lower()
    return lower_path.endswith(DATA_EXTENSIONS) or bool(KEYWORDS.search(f"{url} {label}"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    receipt = json.loads((project / "raw/country-source-pages/receipt.json").read_text(encoding="utf-8-sig"))
    records = []
    for item in receipt["receipts"]:
        if item.get("status") != "acquired" or "html" not in item.get("content_type", "").lower():
            continue
        source_url = item.get("url", "")
        if source_url.rstrip("/") in {
            "https://unstats.un.org/home/nso_sites",
            "https://unstats.un.org/unsd/demographic-social/census/censusdates",
            "https://observatorioplanificacion.cepal.org/en",
        }:
            continue
        source_path = project / item["path"]
        text = source_path.read_text(encoding="utf-8", errors="replace")
        page = LinkParser()
        try:
            page.feed(text)
        except Exception:
            pass
        seen = set()
        links = []
        for link in page.links:
            absolute = urljoin(item.get("final_url") or item["url"], link["href"])
            if not absolute.startswith(("http://", "https://")) or absolute in seen:
                continue
            seen.add(absolute)
            if eligible(absolute, link["text"]):
                links.append({"url": absolute, "label": link["text"][:500]})
        records.append(
            {
                "country_area_id": item["country_area_id"],
                "domain": item["domain"],
                "source_url": item["url"],
                "final_url": item.get("final_url"),
                "page_title": re.sub(r"\s+", " ", " ".join(page.title_parts)).strip()[:500],
                "eligible_link_count": len(links),
                "eligible_links": links,
            }
        )
    output = project / "evidence/COUNTRY_SOURCE_LINK_CATALOG.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "selection_rule": "Direct data/document extensions or census, population, housing, planning, budget and geography keywords. Discovery is not acquisition or adoption.",
                "page_count": len(records),
                "eligible_link_count": sum(row["eligible_link_count"] for row in records),
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"pages": len(records), "eligible_links": sum(row["eligible_link_count"] for row in records), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

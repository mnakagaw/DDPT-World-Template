#!/usr/bin/env python3
"""Inspect pinned Qatar R3 official-page receipts without adopting a plan."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []
        self.current_link = None
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip_depth += 1
        if tag == "a":
            self.current_link = {"href": dict(attrs).get("href", ""), "text": []}

    def handle_data(self, data):
        if self.skip_depth:
            return
        self.text.append(data)
        if self.current_link is not None:
            self.current_link["text"].append(data)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "a" and self.current_link is not None:
            self.links.append({"href": self.current_link["href"], "text": " ".join(" ".join(self.current_link["text"]).split())})
            self.current_link = None


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--manifest", required=True)
args = parser.parse_args()
project = Path(args.project).resolve()
manifest_path = Path(args.manifest).resolve()
if not manifest_path.is_relative_to(project):
    raise SystemExit("Manifest must be inside the selected project")
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
entries = []
for receipt in manifest["receipts"]:
    if receipt["status"] != "acquired":
        entries.append({"file": receipt["file"], "status": receipt["status"], "error": receipt.get("error", "")})
        continue
    raw = (manifest_path.parent / receipt["file"]).read_bytes()
    if len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        raise SystemExit(f"Receipt mismatch: {receipt['file']}")
    item = {"file": receipt["file"], "url": receipt["url"], "sha256": receipt["sha256"]}
    if receipt["file"].startswith("msdp-"):
        page = PageText()
        page.feed(raw.decode("utf-8-sig", errors="replace"))
        item["pdf_links"] = [
            {"url": urljoin(receipt["url"], link["href"]), "label": link["text"]}
            for link in page.links if ".pdf" in link["href"].lower()
        ]
        item["panel_terms"] = [
            " ".join(text.split())[:240] for text in page.text
            if re.search(r"vision|strategy|zoning map|centre plan|center plan|municipality", text, re.I)
        ][:20]
    elif receipt["file"] == "npc-terms.html":
        page = PageText()
        page.feed(raw.decode("utf-8-sig", errors="replace"))
        plain = " ".join(" ".join(page.text).split())
        copyright_start = plain.find("Copyrights Intellectual Property Rights")
        disclaimer_start = plain.find("Disclaimer", copyright_start) if copyright_start >= 0 else -1
        item["copyright_section"] = plain[copyright_start:disclaimer_start if disclaimer_start > copyright_start else copyright_start + 2400] if copyright_start >= 0 else ""
        item["relevant_excerpts"] = [
            plain[max(0, match.start() - 130): match.end() + 260]
            for match in list(re.finditer(r"terms of use|copyright|citation|reproduc|permission|official statistical data|statistical purposes|download", plain, re.I))[:35]
        ]
    elif receipt["file"] == "municipality-current-layer.json":
        layer = json.loads(raw)
        item.update({"layer_name": layer.get("name"), "layer_id": layer.get("id"), "geometry_type": layer.get("geometryType"),
                     "fields": [field["name"] for field in layer.get("fields", [])], "copyright_text": layer.get("copyrightText")})
    elif receipt["file"] == "municipality-current-polygons.geojson":
        features = json.loads(raw)["features"]
        item["feature_count"] = len(features)
        item["municipalities"] = [
            {"code": feature["properties"].get("MNCP_NO"), "name": feature["properties"].get("ENAME"),
             "startdate_utc": datetime.fromtimestamp(feature["properties"]["STARTDATE"] / 1000, timezone.utc).isoformat() if feature["properties"].get("STARTDATE") else None,
             "enddate": feature["properties"].get("ENDDATE"), "geometry_type": feature.get("geometry", {}).get("type")}
            for feature in features
        ]
    entries.append(item)

out = project / "evidence/QAT_R3_OFFICIAL_PAGE_INSPECTION.json"
out.write_text(json.dumps({"manifest": str(manifest_path.relative_to(project)).replace("\\", "/"), "entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"entries": len(entries), "panel_pdf_links": sum(len(item.get("pdf_links", [])) for item in entries),
                  "current_polygons": next((item["feature_count"] for item in entries if "feature_count" in item), None)}, ensure_ascii=False))

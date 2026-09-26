"""Inventory Geostat's 2024 census catalog and retain selected originals privately.

Run from the template root. The output project is ignored by Git. A saved file
is never overwritten: refreshes need a new project or a deliberate new name.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests


CATEGORIES = {
    909: "geographical_distribution_and_internal_migration",
    910: "demographic_and_social_characteristics",
    912: "education",
    913: "economic_characteristics",
    914: "international_migration",
    915: "households",
    918: "living_conditions",
    920: "disability",
}
BASE = "https://www.geostat.ge/en/modules/categories/"
OVERVIEW_URL = "https://www.geostat.ge/media/78282/2024-Population-and-Agricultural-Census-of-Georgia-Finalized-results.pdf"
TITLE = re.compile(r"<button[^>]*>\s*<span>(.*?)</span>", re.I | re.S)
LINK = re.compile(r"<a\s+href=['\"]([^'\"]+\.(?:xlsx|xls)(?:\?[^'\"]*)?)['\"]", re.I)
TAGS = re.compile(r"<[^>]+>")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_bytes(session: requests.Session, url: str) -> tuple[bytes, str]:
    response = session.get(url, timeout=90)
    response.raise_for_status()
    return response.content, response.url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="Fetch every cataloged XLS/XLSX original")
    args = parser.parse_args()
    raw = args.project / "raw" / "geostat-2024-census"
    raw.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "AreaData-source-audit/1.0 (public statistics research)"})
    result = {
        "schema_version": "1.0",
        "source": "Geostat 2024 Population Census result catalogs",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "catalogs": [],
        "tables": [],
    }
    for category_id, key in CATEGORIES.items():
        url = BASE + str(category_id)
        body, resolved = get_bytes(session, url)
        catalog_path = raw / f"catalog-{category_id}.html"
        if catalog_path.exists() and catalog_path.read_bytes() != body:
            raise RuntimeError(f"Catalog changed; retain old bytes and use a new project: {catalog_path}")
        catalog_path.write_bytes(body)
        result["catalogs"].append({
            "id": category_id, "section": key, "url": url, "resolved_url": resolved,
            "path": str(catalog_path.relative_to(args.project)).replace("\\", "/"),
            "sha256": sha256(body),
        })
        chunks = re.split(r"<div class=['\"]mistake m-collapse['\"]>", body.decode("utf-8"))
        for position, chunk in enumerate(chunks[1:], 1):
            match = TITLE.search(chunk)
            if not match:
                continue
            title = html.unescape(TAGS.sub("", match.group(1))).strip()
            links = list(dict.fromkeys(urljoin(resolved, html.unescape(link)) for link in LINK.findall(chunk)))
            if not links:
                result["tables"].append({"id": f"{category_id}-{position:02d}", "section": key, "title": title,
                                         "status": "listed_without_xls_link"})
                continue
            for link_index, link in enumerate(links, 1):
                table_id = f"{category_id}-{position:02d}" + (f"-{link_index}" if len(links) > 1 else "")
                item = {"id": table_id, "section": key, "title": title, "url": link,
                        "status": "cataloged_not_acquired"}
                if args.download:
                    suffix = ".xlsx" if ".xlsx" in link.lower() else ".xls"
                    output = raw / f"{table_id}{suffix}"
                    if output.exists():
                        data = output.read_bytes()
                        acquired_url = "retained_existing_original"
                    else:
                        data, acquired_url = get_bytes(session, link)
                        if suffix == ".xlsx" and not data.startswith(b"PK\x03\x04"):
                            raise RuntimeError(f"Unexpected XLSX signature: {table_id} {link}")
                        if suffix == ".xls" and not data.startswith(bytes.fromhex("D0CF11E0")):
                            raise RuntimeError(f"Unexpected XLS signature: {table_id} {link}")
                        output.write_bytes(data)
                    item.update({"status": "acquired_field_audit_pending", "path": str(output.relative_to(args.project)).replace("\\", "/"),
                                 "sha256": sha256(data), "bytes": len(data), "resolved_url": acquired_url})
                result["tables"].append(item)
        print(f"{category_id}: {sum(t['section'] == key for t in result['tables'])} listed tables")
    if args.download:
        overview_path = raw / "finalized-results-2024.pdf"
        if overview_path.exists():
            overview, overview_resolved = overview_path.read_bytes(), "retained_existing_original"
        else:
            overview, overview_resolved = get_bytes(session, OVERVIEW_URL)
            if not overview.startswith(b"%PDF-"):
                raise RuntimeError("Unexpected Geostat final-results PDF signature")
            overview_path.write_bytes(overview)
        result["overview"] = {"url": OVERVIEW_URL, "resolved_url": overview_resolved,
                              "path": str(overview_path.relative_to(args.project)).replace("\\", "/"),
                              "sha256": sha256(overview), "bytes": len(overview),
                              "status": "acquired_scope_and_national_totals_reviewed"}
    evidence = args.project / "evidence" / "GEO_GEOSTAT2024_CATALOG_INVENTORY.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['tables'])} table entries; {sum(t['status'] == 'acquired_field_audit_pending' for t in result['tables'])} originals retained")


if __name__ == "__main__":
    main()

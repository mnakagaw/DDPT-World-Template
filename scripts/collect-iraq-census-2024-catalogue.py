"""Capture COSIT's public 2024 census table catalogue and selected source PDFs.

The output is private project evidence. It does not imply that a listed table has
been semantically checked or adopted into a country edition.
"""

import argparse
import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests


CATALOGUE_URL = "https://cosit.gov.iq/ar/1234-2019-09-05-07-53-20"
MAX_PDF_BYTES = 200_000_000


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            if "/images/census2024/" in self.href:
                self.links.append((self.href, html.unescape(" ".join(self.parts)).strip()))
            self.href = None
            self.parts = []


def fetch(session, url):
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return response


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--match", action="append", default=[],
                        help="Substring of decoded PDF filename to acquire; repeatable")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "cosit-census-2024-catalogue.json"
    previous = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    previously_acquired = {item["url"]: item for item in previous.get("entries", [])
                           if item.get("acquisition") == "success"}
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData source audit/0.1 (public COSIT catalogue)"
    checked_at = datetime.now(timezone.utc).isoformat()
    response = fetch(session, CATALOGUE_URL)
    source_bytes = response.content
    (out / "cosit-census-2024-catalogue.html").write_bytes(source_bytes)
    parser = Links()
    parser.feed(response.text)
    seen = set()
    entries = []
    for href, title in parser.links:
        url = urljoin(CATALOGUE_URL, href)
        parsed = urlparse(url)
        if parsed.hostname not in {"cosit.gov.iq", "www.cosit.gov.iq"}:
            raise ValueError(f"Unexpected source host: {url}")
        if url in seen:
            continue
        seen.add(url)
        filename = unquote(Path(parsed.path).name)
        entry = {"index": len(entries) + 1, "title": title, "filename": filename,
                 "url": url, "process_state": "identified", "acquisition": "not_requested"}
        path = out / f"cosit-2024-table-{entry['index']:02d}.pdf"
        earlier = previously_acquired.get(url)
        if earlier and path.exists() and earlier.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest():
            entry.update({key: value for key, value in earlier.items()
                          if key not in {"index", "title", "filename", "url"}})
        elif any(term in filename for term in args.match):
            try:
                document = fetch(session, url)
                body = document.content
                if len(body) > MAX_PDF_BYTES or not body.startswith(b"%PDF-"):
                    raise ValueError("Response is oversized or lacks PDF signature")
                path.write_bytes(body)
                entry.update(process_state="acquired", acquisition="success",
                             object_path=path.name, bytes=len(body),
                             sha256=hashlib.sha256(body).hexdigest(),
                             response_status=document.status_code,
                             content_type=document.headers.get("Content-Type"),
                             final_url=document.url)
            except (requests.RequestException, ValueError) as exc:
                entry.update(acquisition="failed", error=str(exc))
        entries.append(entry)
    if len(entries) < 15:
        raise ValueError(f"Catalogue unexpectedly has only {len(entries)} census table links")
    receipt = {"catalogue_url": CATALOGUE_URL, "checked_at": checked_at,
               "catalogue_status": response.status_code,
               "catalogue_sha256": hashlib.sha256(source_bytes).hexdigest(),
               "catalogue_bytes": len(source_bytes), "entries": entries}
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"entries": len(entries), "acquired": sum(
        e["acquisition"] == "success" for e in entries), "failed": sum(
        e["acquisition"] == "failed" for e in entries), "out": str(out)}, ensure_ascii=False))
    for entry in entries:
        print(f"{entry['index']:02d} {entry['acquisition']:14s} {entry['filename']}")


if __name__ == "__main__":
    main()

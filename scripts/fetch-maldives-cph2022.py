"""Archive Maldives Bureau of Statistics 2022 census XLSX catalogue files.

The catalogue snapshot and each original are immutable in the ignored country
project. Acquisition is separate from table-field adoption and legal geography.
"""

import argparse
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = "https://statisticsmaldives.gov.mv/census-2022-results-summary/"
INDICATORS = "https://statisticsmaldives.gov.mv/census-2022-island-and-atoll-level-indicator-sheets/"
SUPPLEMENTAL = {
    "Definitions-Population": "population-indicator-definitions",
    "Atoll-Level-Indicator-Sheet-Population": "population-atoll-indicators",
    "Island-Level-Indicator-Sheet-Population": "population-island-indicators",
    "Definitions-Employment": "employment-indicator-definitions",
    "Atoll-Level-Indicator-Sheet-Emp": "employment-atoll-indicators",
    "Island-Level-Indicator-Sheet-Emp": "employment-island-indicators",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def request(url):
    response = requests.get(url, timeout=90,
                            headers={"User-Agent": "AreaData official-source-acquisition/1.0"})
    response.raise_for_status()
    if urlparse(response.url).hostname not in {"statisticsmaldives.gov.mv", "www.statisticsmaldives.gov.mv"}:
        raise ValueError(f"Unexpected redirect host: {response.url}")
    if len(response.content) > 50_000_000:
        raise ValueError(f"Oversize original: {url}")
    return response


def archive(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f"Original changed; refusing overwrite: {path}")
        return "verified_existing"
    path.write_bytes(body)
    return "acquired"


def catalogue(path, url):
    if path.exists():
        return path.read_bytes(), "reused_saved_snapshot"
    body = request(url).content
    return body, archive(path, body)


def table_entries(body):
    entries = []
    for segment in re.findall(r"<li\b[^>]*>(.*?)</li>", body.decode("utf-8", errors="replace"), re.I | re.S):
        title = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", segment)).split())
        match = re.search(r"Table\s+([A-Z]+\d+)\s*:", title)
        urls = re.findall(r'href="([^"]+\.xlsx?)"', segment, re.I)
        if match and urls:
            code = match.group(1)
            entries.append({"id": f"mdv-cph2022-{code.lower()}", "code": code,
                            "title": title.rsplit(" XLS", 1)[0], "url": urls[0],
                            "catalogue": "summary"})
    if len(entries) != 52 or len({entry["code"] for entry in entries}) != 52:
        raise ValueError(f"Expected 52 unique official numbered tables, got {len(entries)}")
    return entries


def supplemental_entries(body):
    found = []
    for segment in re.findall(r"<li\b[^>]*>(.*?)</li>", body.decode("utf-8", errors="replace"), re.I | re.S):
        urls = re.findall(r'href="([^"]+\.xlsx?)"', segment, re.I)
        for url in urls:
            stem = urlparse(url).path.rsplit("/", 1)[-1].removesuffix(".xlsx")
            if stem in SUPPLEMENTAL:
                found.append({"id": f"mdv-cph2022-{SUPPLEMENTAL[stem]}",
                              "code": SUPPLEMENTAL[stem], "title": stem.replace("-", " "),
                              "url": url, "catalogue": "indicator_sheets"})
    if len(found) != 6 or len({entry["id"] for entry in found}) != 6:
        raise ValueError(f"Expected six indicator/definition XLSX files, got {len(found)}")
    return found


def main(project):
    raw, evidence = project / "raw", project / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    summary_body, summary_state = catalogue(raw / "mdv-cph2022-results-summary.html", SUMMARY)
    indicator_body, indicator_state = catalogue(raw / "mdv-cph2022-indicator-sheets.html", INDICATORS)
    entries = table_entries(summary_body) + supplemental_entries(indicator_body)

    def one(entry):
        response = request(entry["url"])
        body = response.content
        if not body.startswith(b"PK\x03\x04") or len(body) < 1500:
            raise ValueError(f"Not a substantive XLSX: {entry['id']}")
        relative = f"raw/{entry['id']}.xlsx"
        state = archive(project / relative, body)
        return {**entry, "resolved_url": response.url, "raw_path": relative,
                "bytes": len(body), "sha256": sha(body), "status": state,
                "http_status": response.status_code}

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(one, entry): entry for entry in entries}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as error:
                entry = futures[future]
                failures.append({**entry, "status": "failed",
                                 "reason": f"{type(error).__name__}: {error}"})
    results.sort(key=lambda entry: entry["id"])
    failures.sort(key=lambda entry: entry["id"])
    receipt = {"checked_at": datetime.now(timezone.utc).isoformat(),
               "catalogues": [{"url": SUMMARY, "status": summary_state,
                               "sha256": sha(summary_body), "bytes": len(summary_body)},
                              {"url": INDICATORS, "status": indicator_state,
                               "sha256": sha(indicator_body), "bytes": len(indicator_body)}],
               "expected_resources": entries, "sources": results,
               "failed_sources": failures, "acquisition_is_not_adoption": True}
    (evidence / "MDV_CPH2022_ACQUISITION.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": "1.0", "catalogues": receipt["catalogues"],
                "source_files": [{key: value for key, value in row.items() if key in
                    {"id", "code", "title", "url", "catalogue", "raw_path", "bytes", "sha256"}}
                    for row in results], "failed_sources": failures}
    (ROOT / "config/maldives-cph2022-source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"expected": len(entries), "acquired": len(results),
                      "failed": len(failures), "bytes": sum(row["bytes"] for row in results),
                      "failure_ids": [row["id"] for row in failures]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

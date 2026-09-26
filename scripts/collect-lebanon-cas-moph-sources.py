"""Acquire Lebanon CAS district-survey originals and MOPH reference geography."""

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests


CATALOGUE = ("https://www.cas.gov.lb/Publications/"
             "district-statistical-profiles-2018-2019-"
             "%D8%A5%D8%AD%D8%B5%D8%A7%D8%A1%D8%A7%D8%AA-"
             "%D8%A7%D9%84%D8%A3%D9%82%D8%B6%D9%8A%D8%A9-2018-2019/")
DEMOGRAPHY = "https://www.cas.gov.lb/wp-content/uploads/2026/06/LFHLCS_2018_2019_Demography.xls"
FULL_REPORT = "https://www.cas.gov.lb/wp-content/uploads/2025/07/Labour-Force-and-Household-Living-Conditions-Survey-2018-2019.pdf"
MAP_BASE = "https://maps.moph.gov.lb/server/rest/services/Administrative_Zones/MapServer"


def acquire(project, relative, url, signature, expected_media=None):
    target = project / relative
    receipt_path = project / (relative + ".receipt.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (receipt.get("url") != url or receipt.get("status") != "acquired"
                or receipt.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest()):
            raise ValueError(f"Stored body/receipt mismatch: {relative}")
        return receipt
    if target.exists() or receipt_path.exists():
        raise ValueError(f"Incomplete immutable pair: {relative}")
    response = requests.get(url, timeout=90)
    record = {"url": url, "final_url": response.url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
              "http_status": response.status_code, "content_type": response.headers.get("content-type"),
              "bytes": len(response.content), "path": relative}
    response.raise_for_status()
    if not (response.content.lstrip() if signature == b"<!" else response.content).startswith(signature):
        raise ValueError(f"Unexpected body signature: {relative}")
    if expected_media and expected_media not in response.headers.get("content-type", ""):
        raise ValueError(f"Unexpected media type: {relative}")
    target.write_bytes(response.content)
    record.update(status="acquired", sha256=hashlib.sha256(response.content).hexdigest(),
                  redistribution_terms="review_required")
    receipt_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset = json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "LBN":
        raise ValueError("Expected Lebanon candidate")
    raw = "raw/lebanon-cas-moph/"
    catalogue = acquire(project, raw + "cas-district-catalogue.html", CATALOGUE, b"<!", "text/html")
    html = (project / catalogue["path"]).read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" class="cas-map-data">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError("CAS district catalogue data array not found")
    entries = json.loads(match.group(1))
    english = [item for item in entries if item.get("language") == "English"]
    arabic = [item for item in entries if item.get("language") == "Arabic"]
    if len(entries) != 52 or len(english) != 26 or len(arabic) != 26 or \
            len({item["districtKey"] for item in english}) != 26 or \
            {item["districtKey"] for item in english} != {item["districtKey"] for item in arabic}:
        raise ValueError("CAS expected 26 English/Arabic district pairs changed")
    results = {}

    def get_profile(item):
        relative = raw + "profiles-en/" + item["districtKey"] + ".pdf"
        try:
            return item["districtKey"], acquire(project, relative, item["url"], b"%PDF", "pdf")
        except (requests.RequestException, ValueError) as error:
            return item["districtKey"], {"status": "failed_with_evidence", "url": item["url"],
                                          "error": f"{type(error).__name__}: {error}", "path": relative}

    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(get_profile, item) for item in english]):
            district, result = future.result()
            results[district] = result
    for item in entries:
        item["disposition"] = (results[item["districtKey"]]["status"]
                               if item["language"] == "English" else "duplicate_alternate_language_not_acquired")
        if item["language"] == "English":
            item["receipt_path"] = results[item["districtKey"]]["path"] + ".receipt.json"
    evidence = project / "evidence/LBN_CAS_DISTRICT_PROFILE_CATALOG.json"
    evidence.write_text(json.dumps({"catalogue_url": CATALOGUE, "catalogue_sha256": catalogue["sha256"],
                                    "expected_files": 52, "districts": 26, "entries": entries},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    extras = []
    for relative, url, signature, media in [
        (raw + "lfhlcs-2018-19-demography.xls", DEMOGRAPHY, b"\xd0\xcf\x11\xe0", "excel"),
        (raw + "lfhlcs-2018-19-full-report.pdf", FULL_REPORT, b"%PDF", "pdf"),
        *[(raw + f"moph-adm{level}.geojson",
           MAP_BASE + f"/{layer}/query?where=1%3D1&outFields=NAME%2CNAME_AR%2CPCODE%2CSTATUS&returnGeometry=true&outSR=4326&f=geojson",
           b"{", "json") for level, layer in ((1, 2), (2, 3))],
    ]:
        try:
            extras.append(acquire(project, relative, url, signature, media))
        except (requests.RequestException, ValueError) as error:
            extras.append({"status": "failed_with_evidence", "url": url,
                           "error": f"{type(error).__name__}: {error}", "path": relative})
    for item in extras:
        if item["status"] == "acquired" and item["path"].endswith(".geojson"):
            body = json.loads((project / item["path"]).read_text(encoding="utf-8"))
            item["features"] = len(body.get("features", []))
    failures = [item for item in [*results.values(), *extras] if item["status"] != "acquired"]
    (project / "evidence/LBN_ACQUISITION_SUMMARY.json").write_text(json.dumps({
        "checked_at": datetime.now(timezone.utc).isoformat(), "catalogue": catalogue,
        "profile_count_acquired": sum(item["status"] == "acquired" for item in results.values()),
        "profile_count_expected_english": 26, "alternate_arabic_not_acquired": 26,
        "extras": extras, "failures": failures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"english_profile_acquired": 26 - len([item for item in results.values() if item["status"] != "acquired"]),
                      "extra_status": [(item["path"], item["status"], item.get("features")) for item in extras],
                      "failures": len(failures)}))


if __name__ == "__main__":
    main()

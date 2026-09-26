"""Record initial official Yemen leads without promoting the bootstrap to a local edition."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LAW_HASH = "1f40479d81ad54ec220a849c07daf34dd90f12c75cb8df1a0ccc67a89be1d509"
YEARBOOK_URL = "https://cso-ye.org/%D8%A7%D9%84%D9%83%D8%AA%D8%A7%D8%A8-%D8%A7%D9%84%D8%A7%D8%AD%D8%B5%D8%A7%D8%A1-%D8%A7%D9%84%D8%B3%D9%86%D9%88%D9%8A-%D8%B9%D9%84%D9%89-%D9%85%D8%B3%D8%AA%D9%88%D9%89-%D8%A7%D9%84%D9%85%D8%AD%D8%A7/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    dataset_path = project / "data/dashboard.json"
    preflight_path = project / "evidence/SOURCE_PREFLIGHT.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "YEM" or preflight["country"]["iso3"] != "YEM":
        raise ValueError("Expected Yemen project")
    raw = project / "raw/official-yemen"
    receipt = {item["name"]: item for item in json.loads((raw / "acquisition.json").read_text(encoding="utf-8"))}
    law = receipt["parliament-local-authority-law-2000.pdf"]
    census = receipt["cso-2004-main-report.pdf"]
    law_bytes = (raw / law["name"]).read_bytes()
    if law["acquisition"] != "success" or law["sha256"] != LAW_HASH or hashlib.sha256(law_bytes).hexdigest() != LAW_HASH:
        raise ValueError("Parliament law original does not match acquisition receipt")
    if census["acquisition"] != "failed" or census["status"] != 200:
        raise ValueError("Recheck census acquisition state before recording the lead")
    stamp = datetime.now(timezone.utc).isoformat()
    sources = [
        {"id": "yem-cso-2004-census-main-report-location", "name": "CSO 2004 census main report location",
         "publisher": "Yemen Central Statistical Organization", "url": census["url"],
         "reference_period": "2004", "geographic_level": "national; local tables require inspection",
         "status": "failed", "retrieved_at": census["checked_at"], "license": "terms_review_required",
         "note": "Official PDF URL identified; automated acquisition returned HTTP 200 with non-PDF content. Census results were not adopted. The 2004 geography must not be equated to the 2017 reference ADM1 layer."},
        {"id": "yem-cso-governorate-yearbook-catalogue", "name": "CSO governorate statistical yearbook catalogue",
         "publisher": "Yemen Central Statistical Organization", "url": YEARBOOK_URL,
         "reference_period": "2021-2024 listings", "geographic_level": "governorate; exact volume coverage unreviewed",
         "status": "not_collected", "retrieved_at": stamp, "license": "terms_review_required",
         "note": "Official page lists a 2024 volume and several historical governorate volumes. Individual report files, tables and local identifiers remain unacquired and unreviewed."},
        {"id": "yem-parliament-local-authority-law-2000", "name": "Yemen Local Authority Law No. 4 of 2000",
         "publisher": "Yemen Parliament", "url": law["url"],
         "reference_period": "2000 original enactment", "geographic_level": "governorate, district",
         "status": "partial", "retrieved_at": law["checked_at"], "sha256": LAW_HASH,
         "raw_path": "raw/official-yemen/parliament-local-authority-law-2000.pdf",
         "license": "terms_review_required",
         "note": "Forty-page parliamentary PDF acquired. The current consolidated text, amendment history, implementation and actual local plan documents remain unverified; do not infer current plan status."},
    ]
    chosen = {item["id"] for item in sources}
    dataset["sources"] = [item for item in dataset["sources"] if item["id"] not in chosen] + sources
    dataset["generated_at"] = stamp
    preflight["country_research"] = {
        "status": "initial_official_locations_identified", "checked_at": stamp,
        "origin_registry": "AreaData 2026-09-26 Middle East research pass",
        "census": {"url": census["url"], "reference_period": "2004", "acquisition": "failed_non_pdf_response"},
        "planning": {"url": law["url"], "law_year": 2000, "acquisition": "success", "current_applicability": "unverified"},
        "sources": [{"id": item["id"], "url": item["url"], "site_status": item["status"]} for item in sources],
    }
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = project / "evidence/SOURCE_PREFLIGHT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    heading = "## 2026-09-26 official source location pass"
    markdown = markdown.split(heading)[0].rstrip() + "\n\n"
    markdown_path.write_text(markdown + heading + "\n\n"
        "2026-09-26: CSO census main report URL located, acquisition returned non-PDF content; no census values adopted. "
        "The CSO governorate yearbook catalogue lists 2024 and older volumes, whose files and fields remain unreviewed. "
        "The parliamentary Local Authority Law No. 4 (2000) PDF was acquired (40 pages); current consolidated status and local plan application are unverified. "
        "The 22 ADM1 reference shapes are 2017 geoBoundaries units without an official code or epoch crosswalk. "
        "The 268 WDI observations are national only. This is a research bootstrap, not a domestic edition.\n",
        encoding="utf-8")
    print(json.dumps({"source_leads": len(sources), "acquired_law_sha256": LAW_HASH,
                      "census_acquisition": census["acquisition"], "domestic_observations_added": 0}))


if __name__ == "__main__":
    main()

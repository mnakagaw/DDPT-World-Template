"""Archive the NSB catalogue's 2017 PHCB reports and bounded planning leads.

Acquisition is not a semantic audit or a claim that current code/legal geography
matches 2017 census rows. Existing raw bytes are verified, never overwritten.
"""

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "https://nsb.gov.bt/phcb/"
CODE_PAGE = "https://nsb.gov.bt/bhutan-standard-statistical-geograpgic-codes-2/"
EXTRAS = [
    ("local-government-rules-2012", "https://www.dlgdm.gov.bt/storage/upload-documents/2021/12/16/umXB6iM4gC.pdf"),
    ("national-plan-13fyp", "https://www.pmo.gov.bt/api/uploads/plans/document-1751451996345.pdf"),
]


def sha(body):
    return hashlib.sha256(body).hexdigest()


def get(url):
    response = requests.get(url, timeout=90, headers={"User-Agent": "AreaData official-source-acquisition/1.0"})
    response.raise_for_status()
    if urlparse(response.url).hostname not in {"nsb.gov.bt", "www.nsb.gov.bt", "www.dlgdm.gov.bt", "www.pmo.gov.bt", "pmo.gov.bt"}:
        raise ValueError(f"Unexpected redirect host: {response.url}")
    return response


def archive(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f"Existing original differs; refusing overwrite: {path}")
        return "verified_existing"
    path.write_bytes(body)
    return "acquired"


def main(project):
    raw = project / "raw"
    evidence = project / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    cat_path = raw / "nsb-phcb-catalogue.html"
    if cat_path.exists():
        catalogue = cat_path.read_bytes()
        catalogue_state = "reused_saved_snapshot"
    else:
        catalogue = get(CATALOGUE).content
        catalogue_state = archive(cat_path, catalogue)
    html = catalogue.decode("utf-8", errors="replace")
    urls = re.findall(r'data-wdlib-file-url="([^"]+)"', html)
    reports = [url for url in urls if re.search(r"/(?:PHCB2017_[^/]+|2017-PHCB-report-_national)\.pdf$", url, re.I)]
    if len(reports) != 21 or len(set(reports)) != 21:
        raise ValueError(f"Expected 2017 national and 20 district reports, got {len(reports)} unique {len(set(reports))}")
    code_path = raw / "nsb-geographic-code-catalogue.html"
    if code_path.exists():
        code_html = code_path.read_bytes()
    else:
        code_html = get(CODE_PAGE).content
        archive(code_path, code_html)
    code_urls = re.findall(r'data-wdlib-file-url="([^"]+)"', code_html.decode("utf-8", errors="replace"))
    if len(code_urls) != 1:
        raise ValueError(f"Expected one official geographic-code file, got {len(code_urls)}")
    entries = []
    for url in reports:
        stem = urlparse(url).path.rsplit("/", 1)[-1].removesuffix(".pdf")
        district = stem.removeprefix("PHCB2017_")
        key = "national-2017" if stem.startswith("2017-PHCB") else "district-" + re.sub(r"[^a-z0-9]+", "-", district.lower()).strip("-")
        entries.append((key, url))
    entries += [("geographic-codes", code_urls[0]), *EXTRAS]
    if len({key for key, _ in entries}) != 24:
        raise ValueError("Duplicate source identifiers")

    def one(item):
        key, url = item
        response = get(url)
        body = response.content
        if not body.startswith(b"%PDF-") or len(body) < 20_000:
            raise ValueError(f"Not a substantive PDF: {key} {url}")
        relative = f"raw/btn-phcb2017-{key}.pdf"
        state = archive(project / relative, body)
        pages = len(PdfReader(project / relative).pages)
        return {"id": f"btn-phcb2017-{key}", "url": url, "resolved_url": response.url,
                "raw_path": relative, "bytes": len(body), "sha256": sha(body),
                "pages": pages, "status": state, "http_status": response.status_code}

    results = []
    failures = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(one, item): item[0] for item in entries}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as error:
                failures.append({"id": f"btn-phcb2017-{futures[future]}",
                                 "url": dict(entries)[futures[future]],
                                 "status": "failed", "reason": f"{type(error).__name__}: {error}"})
    results.sort(key=lambda x: x["id"])
    failures.sort(key=lambda x: x["id"])
    if sum(x["id"] == "btn-phcb2017-national-2017" or
           x["id"].startswith("btn-phcb2017-district-") for x in results) != 21:
        raise ValueError(f"Some census reports failed; see {failures}")
    receipt = {"checked_at": datetime.now(timezone.utc).isoformat(),
               "catalogue_url": CATALOGUE, "catalogue_state": catalogue_state,
               "catalogue_sha256": sha(catalogue), "catalogue_bytes": len(catalogue),
               "geographic_code_catalogue_url": CODE_PAGE,
               "geographic_code_catalogue_sha256": sha(code_html),
               "sources": results, "failed_sources": failures,
               "acquisition_is_not_adoption": True}
    (evidence / "BTN_PHCB2017_ACQUISITION.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": "1.0", "catalogue_url": CATALOGUE,
                "catalogue_sha256": sha(catalogue),
                "geographic_code_catalogue_url": CODE_PAGE,
                "geographic_code_catalogue_sha256": sha(code_html),
                "scope": "2017 PHCB national and 20 Dzongkhag reports, current code publication and two planning references; adoption separate",
                "source_files": [{key: value for key, value in x.items() if key in
                    {"id", "url", "raw_path", "bytes", "sha256", "pages"}} for x in results],
                "failed_sources": failures}
    (ROOT / "config/bhutan-phcb2017-source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalogue_state": catalogue_state, "census_reports": len(reports),
                      "archived_pdfs": len(results), "total_bytes": sum(x["bytes"] for x in results),
                      "failed": failures,
                      "manifest": "config/bhutan-phcb2017-source-manifest.json"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

"""Acquire the bounded official DCS CPH-2024 table catalogue and originals.

This captures source bytes and locations only. Provisional GN files and final
tables are separate publications and must not be joined without an audit.
"""

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


CATALOGUE = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/"
ROOT = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/"
ADDITIONAL = {
    "gn-population-provisional": (ROOT + "GN_population_excel", "xlsx"),
    "gn-housing-provisional": (ROOT + "GN_housing_excel", "xlsx"),
    "gn-occupied-housing": (ROOT + "OHU_GN_excel", "xlsx"),
    "gn-households": (ROOT + "HH_GND_excel", "xlsx"),
    "gn-ethnicity": (ROOT + "GNLevel/GN_Level_Population_by_Ethnic_Group", "xlsx"),
    "gn-five-year-age": (ROOT + "GNLevel/GN_Level_Population_by_Five_Year_Age_Group", "xlsx"),
    "gn-local-government-area": (ROOT + "GNLevel/GN_Level_Population_by_Local_Government_Area", "xlsx"),
    "gn-religion": (ROOT + "GNLevel/GN_Level_Population_by_Religion", "xlsx"),
    "gn-sector": (ROOT + "GNLevel/GN_Level_Population_by_Sector", "xlsx"),
    "admin-codes": ("https://www.statistics.gov.lk/qlink/AdminDivCodes_Excel", "xlsx"),
    "final-report-en": ("https://www.statistics.gov.lk/Resource/en/Population/CPH_2024/CPH2024_Final_Eng.pdf", "pdf"),
}


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def acquire(url, destination, kind, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(limit + 1)
        final_url = response.url
        status = response.status
        content_type = response.headers.get("Content-Type")
    if urlsplit(final_url).hostname != "www.statistics.gov.lk":
        raise ValueError(f"Unexpected redirect target: {final_url}")
    if len(body) > limit or not body.startswith(b"PK\x03\x04" if kind == "xlsx" else b"%PDF-"):
        raise ValueError(f"Oversized or invalid {kind} response: {url}")
    digest = sha256(body)
    if destination.exists():
        if sha256(destination.read_bytes()) != digest:
            raise ValueError(f"Immutable original changed: {destination}")
        state = "identical_existing"
    else:
        destination.write_bytes(body)
        state = "acquired"
    return {"url": url, "response_url": final_url, "http_status": status,
            "content_type": content_type, "bytes": len(body), "sha256": digest,
            "raw_path": f"raw/{destination.name}", "state": state}


def main(project):
    raw = project / "raw"
    evidence = project / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    page_path = raw / "dcs-cph2024-catalogue.html"
    if page_path.exists():
        page = page_path.read_bytes()
        catalogue_state = "saved_official_snapshot_reused"
    else:
        request = urllib.request.Request(CATALOGUE, headers={"User-Agent": "AreaData-source-audit/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            page = response.read(2_000_001)
        page_path.write_bytes(page)
        catalogue_state = "acquired"
    if len(page) > 2_000_000 or b"HousingA/A16" not in page or b"PopulationA/A7" not in page:
        raise ValueError("Official 2024 catalogue changed or is oversized")
    paths = sorted({x.decode("ascii") for x in re.findall(
        rb"(?:PopulationA|HousingA)/A[0-9]+", page)},
        key=lambda s: (s.split("/")[0], int(s.split("A")[-1])))
    if len(paths) != 23:
        raise ValueError(f"Expected 23 numbered tables, found {len(paths)}")
    sources = {x.replace("/", "-").lower(): (ROOT + x, "xlsx") for x in paths}
    sources.update(ADDITIONAL)
    prior_path = evidence / "LKA_CPH2024_ACQUISITION.json"
    prior = {x["id"]: x for x in json.loads(prior_path.read_text(encoding="utf-8"))["records"]} if prior_path.exists() else {}
    records = []
    for key, (url, kind) in sources.items():
        destination = raw / f"dcs-cph2024-{key}.{kind}"
        # Keep legacy pilot names as immutable originals rather than overwriting.
        if key == "populationa-a5":
            destination = raw / "cph2024-population-ds-A5.xlsx"
        elif key == "gn-population-provisional":
            destination = raw / "dcs-gn-population-2024.xlsx"
        elif key == "admin-codes":
            destination = raw / "dcs-admin-codes.xlsx"
        record = {"id": key, "url": url, "kind": kind,
                  "requested_at_utc": datetime.now(timezone.utc).isoformat()}
        try:
            old = prior.get(key)
            if old and old.get("sha256") and destination.exists():
                body = destination.read_bytes()
                if len(body) != old["bytes"] or sha256(body) != old["sha256"]:
                    raise ValueError(f"Prior original hash mismatch: {destination}")
                record.update(old)
                record["state"] = "verified_existing_prior_receipt"
                record["rechecked_at_utc"] = datetime.now(timezone.utc).isoformat()
            else:
                record.update(acquire(url, destination, kind, 45_000_000))
        except (OSError, ValueError) as error:
            record.update({"state": "failed", "error": str(error)})
        records.append(record)
        print(f"{key}: {record['state']}", flush=True)
    receipt = {"schema_version": "1.0", "catalogue_url": CATALOGUE,
               "catalogue_state": catalogue_state,
               "catalogue_raw_path": f"raw/{page_path.name}",
               "catalogue_bytes": len(page), "catalogue_sha256": sha256(page),
               "checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "selection": "All 23 numbered A tables plus nine GN workbooks, administrative codes and final English report; other catalogue entries remain to inventory",
               "records": records}
    (evidence / "LKA_CPH2024_ACQUISITION.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if any(x["state"] == "failed" for x in records):
        raise SystemExit("One or more official originals failed; see acquisition receipt")
    print(json.dumps({"acquired_or_identical": len(records),
                      "catalogue_numbered_tables": len(paths)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

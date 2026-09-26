"""Acquire a bounded set of public NSO Nepal 2021 province XLSX originals.

The filenames come from the archived official Next.js provincial download page
module. Existing originals are immutable: changed remote bytes stop acquisition.
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = "https://censusresults.nsonepal.gov.np/files/province"
FILES = {
    "Indv01": "Indv01-PopulationBySex.xlsx",
    "Hhld06": "Hhld06_SourceOfDrinkingWater.xlsx",
    "Hhld09": "Hhld09_TypeOfToiletUsed.xlsx",
    "Indv17": "Indv17-PopulationByLiteracyStatus.xlsx",
}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def main(project):
    raw = project / "raw"
    evidence = project / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = []
    for province in range(1, 8):
        for key, filename in FILES.items():
            url = f"{BASE}/P{province}/{filename}"
            destination = raw / f"NPL-P{province}-{key}.xlsx"
            row = {"province_directory": f"P{province}", "table": key, "filename": filename,
                   "url": url, "raw_path": f"raw/{destination.name}",
                   "requested_at_utc": datetime.now(timezone.utc).isoformat()}
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-audit/1.0"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    body = response.read(20_000_001)
                    row["http_status"] = response.status
                    row["content_type"] = response.headers.get("Content-Type")
                if len(body) > 20_000_000 or not body.startswith(b"PK\x03\x04"):
                    raise ValueError("Response is oversized or not an XLSX ZIP")
                row["bytes"], row["sha256"] = len(body), sha256(body)
                if destination.exists():
                    if sha256(destination.read_bytes()) != row["sha256"]:
                        raise ValueError("Existing immutable original differs from current download")
                    row["state"] = "identical_existing"
                else:
                    destination.write_bytes(body)
                    row["state"] = "acquired"
            except (OSError, urllib.error.URLError, ValueError) as error:
                row["state"] = "failed"
                row["error"] = str(error)
            manifest.append(row)
            print(f"{row['province_directory']} {key}: {row['state']}", flush=True)
            time.sleep(0.1)
    receipt = evidence / "NPL_NSO2021_ACQUISITION.json"
    receipt.write_text(json.dumps({
        "catalogue_url": "https://censusresults.nsonepal.gov.np/downloads/provincial/1?type=data",
        "catalogue_page_sha256": "788ce352056323754558a288b319c7347b5135d31eab4217353c49bfff479f8a",
        "catalogue_script_sha256": sha256((raw / "nso-provincial-page.js").read_bytes())
        if (raw / "nso-provincial-page.js").exists() else None,
        "selected_filenames_source": "official Next.js provincial download module, 91 catalogue entries (2 reports and 89 XLSX tables)",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": manifest,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if any(row["state"] == "failed" for row in manifest):
        raise SystemExit("One or more official XLSX originals failed; see receipt")
    print(json.dumps({"downloaded_or_identical": len(manifest), "tables": list(FILES)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

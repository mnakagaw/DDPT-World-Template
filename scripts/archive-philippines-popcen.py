"""Archive the PSA browser downloads with their official source URLs and hashes.

PSA's public attachments can require a browser challenge. Download them from
the two official release pages first, then pass that download directory here.
The originals remain in the ignored country project's raw directory.
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


POPCEN_PAGE = "https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president"
PSGC_JUNE_PAGE = "https://psa.gov.ph/content/second-quarter-2024-psgc-updates-creation-negros-island-region-and-correction-names-two"
PSGC_DEC_PAGE = "https://psa.gov.ph/content/fourth-quarter-2024-psgc-updates-correction-names-three-barangays"
PREFIX = "https://psa.gov.ph/system/files/"


def source(source_id, download_name, remote_name, parent, category="popcen"):
    return {"id": source_id, "download_name": download_name,
            "url": PREFIX + parent + quote(remote_name, safe="-_."),
            "release_page": {"popcen": POPCEN_PAGE, "psgc_june": PSGC_JUNE_PAGE,
                             "psgc_dec": PSGC_DEC_PAGE}[category], "category": category}


SOURCES = [
    source("phl-popcen-release-pdf", "1_2024%20POPCEN%20Press%20Release_Declaration%20of%20Count_Revised_ONS-signed_0.pdf",
           "1_2024 POPCEN Press Release_Declaration of Count_Revised_ONS-signed_0.pdf", "phcd/"),
    source("phl-popcen-proclamation", "20250711-PROC-973-FRM_0.pdf", "20250711-PROC-973-FRM_0.pdf", "phcd/"),
    source("phl-popcen-table-a", "2_Table A - Population and Annual PGR for the Philippines and its Regions, Provinces, and HUCs_0.xlsx",
           "2_Table A - Population and Annual PGR for the Philippines and its Regions, Provinces, and HUCs_0.xlsx", "phcd/"),
    source("phl-popcen-table-b", "3_Table B - Population and Annual PGR by Province, City, and Municipality - By Region - rev_0.xlsx",
           "3_Table B - Population and Annual PGR by Province, City, and Municipality - By Region - rev_0.xlsx", "phcd/"),
]

TABLE_C = [
    ("ncr", "NCR_2.xlsx"), ("car", "CAR_0.xlsx"),
    ("region-i", "Region I_1.xlsx"), ("region-ii", "Region II_1.xlsx"),
    ("region-iii", "Region III_1.xlsx"), ("calabarzon", "CALABARZON_0.xlsx"),
    ("mimaropa", "MIMAROPA_1.xlsx"), ("region-v", "Region V_1.xlsx"),
    ("region-vi", "Region VI_1.xlsx"), ("region-vii", "Region VII_1.xlsx"),
    ("nir", "NIR_0.xlsx"), ("region-viii", "Region VIII_0.xlsx"),
    ("region-ix", "Region IX_1.xlsx"), ("region-x", "Region X_0.xlsx"),
    ("region-xi", "Region XI_1.xlsx"), ("region-xii", "Region XII_1.xlsx"),
    ("caraga", "Caraga_0.xlsx"), ("barmm", "BARMM_1.xlsx"),
]
SOURCES += [source("phl-popcen-table-c-" + key, filename, filename, "phcd/")
            for key, filename in TABLE_C]
SOURCES += [
    source("phl-psgc-2024q2-datafile", "PSGC-2Q-2024-Publication-Datafile-rev.xlsx",
           "PSGC-2Q-2024-Publication-Datafile-rev.xlsx", "scd/", "psgc_june"),
    source("phl-psgc-2024q2-summary", "PSGC-2Q%202024-National%20and%20Provincial%20Summary.xlsx",
           "PSGC-2Q 2024-National and Provincial Summary.xlsx", "scd/", "psgc_june"),
    source("phl-psgc-2024q2-changes", "PSGC-2Q-2024-Summary-of-Changes.xlsx",
           "PSGC-2Q-2024-Summary-of-Changes.xlsx", "scd/", "psgc_june"),
    source("phl-psgc-2024q2-release", "Press-Release-June2024PSGC.pdf",
           "Press-Release-June2024PSGC.pdf", "scd/", "psgc_june"),
    source("phl-psgc-2024q4-datafile", "PSGC-4Q-2024-Publication-Datafile.xlsx",
           "PSGC-4Q-2024-Publication-Datafile.xlsx", "scd/", "psgc_dec"),
    source("phl-psgc-2024q4-summary", "PSGC-4Q-2024-National-and-Provincial-Summary.xlsx",
           "PSGC-4Q-2024-National-and-Provincial-Summary.xlsx", "scd/", "psgc_dec"),
    source("phl-psgc-2024q4-changes", "PSGC-4Q-2024-Summary-of-Changes.xlsx",
           "PSGC-4Q-2024-Summary-of-Changes.xlsx", "scd/", "psgc_dec"),
    source("phl-psgc-2024q4-release", "Press%20Release%204Q%20PSGC%20Updates.pdf",
           "Press Release 4Q PSGC Updates.pdf", "scd/", "psgc_dec"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads-dir", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    raw = args.project / "raw" / "psa-2024"
    raw.mkdir(parents=True, exist_ok=True)
    archived = []
    for item in SOURCES:
        origin = args.downloads_dir / item["download_name"]
        if not origin.is_file():
            raise FileNotFoundError(origin)
        suffix = origin.suffix.lower()
        body = origin.read_bytes()
        if suffix == ".xlsx" and not body.startswith(b"PK\x03\x04"):
            raise ValueError(f"Not XLSX: {origin}")
        if suffix == ".pdf" and not body.startswith(b"%PDF-"):
            raise ValueError(f"Not PDF: {origin}")
        target = raw / (item["id"] + suffix)
        shutil.copyfile(origin, target)
        archived.append({**item, "raw_path": str(target.relative_to(args.project)).replace("\\", "/"),
                         "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                         "retrieved_at": datetime.now(timezone.utc).isoformat(),
                         "retrieval_method": "Official release link in Codex in-app browser; copied from browser download"})
    result = {"schema_version": "1.0", "sources": archived,
              "source_count": len(archived), "total_bytes": sum(x["bytes"] for x in archived)}
    out = args.project / "evidence" / "PHL_SOURCE_MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(archived), "bytes": result["total_bytes"], "manifest": str(out)}))


if __name__ == "__main__":
    main()

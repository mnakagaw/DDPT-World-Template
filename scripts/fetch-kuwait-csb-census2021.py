"""Fetch pinned CSB 2021 registration-census originals into a private project.

The eight tables are a selected source subset. Changed upstream bytes require
an explicit source review and new hash rather than an implicit replacement.
"""

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = "https://census.csb.gov.kw/CensusData_EN"
TABLES = {
    1: (4, "1ef400667d1cd91b68aba1c446fb63861a65cd45d269b4090707b27893f89bd7", "368bbce7a09929686fb9777ad36e6ab3a8f99dd2d48987bd02a61611130a96b3"),
    2: (5, "28c39aedda3179a3e06a97bcc6ac27d31cd2fb54d0057636f5fe422740c47cec", "4384b607c5f9a995dc67cafb15c55c9e71b482846560ccf5354cb9d1c512e1bb"),
    10: (30, "b13c2c835a2a743328f42982513e0c819f23b01593066b525d27b14585749621", "3be5dc51f027cb9d937907c9916c81d6ce3f526fcd49bc42f27ae2c787019cf8"),
    22: (42, "ebc95bd42e6d0de7527f50171dc76e9242777cb919e37061e9ad5fcfeededa10", "c3c35cf364c32bfb427afb3525db7034e4073878dff1613f81a4bd37f634ee3d"),
    26: (46, "1b6e1a9e92928839a2432c1e5a678427719b05f8ccdcd9fa7cbc230d364e9df8", "7ff00ad934e5c782534316444081c9fcaf00893f1d096df2b14bb25151304cb9"),
    42: (62, "736f3e50675a370a503ff44822214150e7e01955eb6a302f8305a87f086db128", "dd2abc0ea7115a11f332c72ca0674fbef7f3daa6a2d0129ba2954ca78eba3d76"),
    51: (71, "1b3f865e3ec52558a1a516176fc53b73436b27659c2579bf9c1a1fc4468daa51", "23292eaaaa4e70bef182b11bfb082e6eb589e45a00fa0b4b1382628c4dd8a18a"),
    52: (72, "30833b3d503571b4a4a08a7b0b1856d44396ee66e9ca45ee4f9b3aefdef1e6f2", "a2d8e2249bc4c2850b8d124bdd46f8c16bcc1a3b73bac18c3cfdd963780794be"),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_url(st_id, ext):
    return f"{BASE}?st_id={st_id}&handler=Export{'Excel' if ext == 'xlsx' else 'PDF'}"


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for table, (st_id, xlsx_sha, pdf_sha) in TABLES.items():
        for ext, expected in (("xlsx", xlsx_sha), ("pdf", pdf_sha)):
            path = raw / f"CSB_2021_Census_Table{table}.{ext}"
            url = source_url(st_id, ext)
            if not path.exists():
                request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AreaData source audit)"})
                with urllib.request.urlopen(request, timeout=90) as response:
                    content = response.read()
                path.write_bytes(content)
            actual = digest(path)
            if actual != expected:
                raise ValueError(f"Changed or incorrect CSB original: Table {table} {ext}: {actual}")
            receipt = {"table": table, "source_url": url, "raw_path": str(path.relative_to(project)).replace("\\", "/"),
                       "sha256": actual, "bytes": path.stat().st_size,
                       "checked_at": datetime.now(timezone.utc).isoformat(), "status": "hash_verified"}
            receipts.append(receipt)
    (raw / "CSB_2021_SELECTED_TABLE_RECEIPTS.json").write_text(
        json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"original_files": len(receipts), "tables": list(TABLES), "hashes_verified": len(receipts)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

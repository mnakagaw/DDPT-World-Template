"""Fetch pinned archived CBS originals and the OCHA census mirror.

These are historical source copies, not evidence of current Syrian population.
Raw files and receipts stay in the ignored country project. A changed body stops
the replay until its identity and numeric tables have been audited again.
"""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "cbs2004-pop-moh.pdf": (
        "https://web.archive.org/web/20140124131814id_/http://cbssyr.sy/General%20census/census%202004/pop-moh.pdf",
        "296374d5d2f306e803a4cf7631000e93576e08e57a3d527eb57e922e518ab628",
        b"%PDF",
        "Archived original Central Bureau of Statistics governorate table",
    ),
    "cbs2004-pop-man.pdf": (
        "https://web.archive.org/web/20130310211017/http://www.cbssyr.org/General%20census/census%202004/pop-man.pdf",
        "21c02896cc6d4b19561f17c2a55a0109e8d7dd2e1c6de9558485e44edcf5cfa7",
        b"%PDF",
        "Archived original Central Bureau of Statistics district/sub-district table",
    ),
    "syr_pop_2004_sycensus_0.xls": (
        "https://web.archive.org/web/20160307093758/https://www.humanitarianresponse.info/files/syr_pop_2004_sycensus_0.xls",
        "3ef15cc2cd20f4a37f07016a4e9485319caf4f4eeed7a4cd9ecadbdbd4af3d61",
        bytes.fromhex("d0cf11e0"),
        "Archived OCHA distribution; names and P-codes only, never controlling numeric source",
    ),
}


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    results = []
    for filename, (url, expected, signature, scope) in SOURCES.items():
        path = raw / filename
        if path.exists():
            actual = digest(path)
            if actual != expected:
                raise ValueError(f"Existing source changed: {filename}: {actual}")
            status = "reused_verified"
            retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-acquisition/1.0"})
            temporary = None
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=filename + ".", suffix=".part", delete=False) as sink:
                        temporary = Path(sink.name)
                        for chunk in iter(lambda: response.read(1024 * 1024), b""):
                            sink.write(chunk)
                actual = digest(temporary)
                if actual != expected:
                    raise ValueError(f"Retrieved source changed: {filename}: {actual}")
                if temporary.read_bytes()[:4] != signature:
                    raise ValueError(f"Unexpected file format: {filename}")
                temporary.replace(path)
                status = "downloaded_verified"
                retrieved = datetime.now(timezone.utc).isoformat()
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        if path.read_bytes()[:4] != signature:
            raise ValueError(f"Existing source format invalid: {filename}")
        receipt = {"url": url, "original_scope": scope, "retrieved_at_utc": retrieved,
                   "size_bytes": path.stat().st_size, "sha256": expected, "status": status,
                   "redistribution_terms": "review_required"}
        (raw / f"{filename}.receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append({"file": filename, "status": status, "bytes": receipt["size_bytes"], "sha256": expected})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

"""Fetch two pinned UAE official population sources into an ignored project.

Stop on changed content. An updated FCSC PDF or SCAD page needs a new audit.
"""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "fcsc-uae-numbers-2009.pdf": (
        "https://fcsc.gov.ae/wp-content/uploads/2025/04/%D8%A7%D9%84%D8%A5%D9%85%D8%A7%D8%B1%D8%A7%D8%AA-%D8%A8%D8%A7%D9%84%D8%A3%D8%B1%D9%82%D8%A7%D9%85-2009.pdf",
        "7f23a54f8cae8857238db82539f5275adbe6dc362315267e2d2a9980083225db", b"%PDF"),
    "scad-census-population-2024.html": (
        "https://census.scad.gov.ae/home/population?fid=0&lang=en&tab=webreport",
        "887d84414ee37445ab5499f6315587b2d52662d42da959c8cfd903ee65560a70", b"<htm"),
}


def sha256(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    result = []
    for name, (url, expected, signature) in SOURCES.items():
        path = raw / name
        if path.exists():
            actual = sha256(path)
            if actual != expected: raise ValueError(f"Existing source changed: {name}: {actual}")
            status = "reused_verified"
            retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-acquisition/1.0"})
            temporary = None
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=name + ".", suffix=".part", delete=False) as out:
                        temporary = Path(out.name)
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            out.write(block)
                actual = sha256(temporary)
                if actual != expected: raise ValueError(f"Upstream source changed: {name}: {actual}")
                if temporary.read_bytes()[:4] != signature: raise ValueError(f"Wrong source format: {name}")
                temporary.replace(path)
                status = "downloaded_verified"
                retrieved = datetime.now(timezone.utc).isoformat()
            finally:
                if temporary is not None: temporary.unlink(missing_ok=True)
        if path.read_bytes()[:4] != signature: raise ValueError(f"Wrong existing format: {name}")
        receipt = {"url": url, "retrieved_at_utc": retrieved, "size_bytes": path.stat().st_size,
                   "sha256": expected, "status": status, "redistribution_terms": "review_required"}
        (raw / (name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        result.append({"file": name, "status": status, "bytes": receipt["size_bytes"]})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

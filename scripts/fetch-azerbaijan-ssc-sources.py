"""Fetch the pinned SSC Azerbaijan originals for the partial country adapter.

The hashes are intentionally fixed: a changed official file requires a new field audit.
Large census ZIPs remain in the ignored country project, outside Git.
"""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "ssc-area-population-density.xls": (
        "https://www.stat.gov.az/source/demoqraphy/en/001_15en.xls",
        "de9bc5a8caa091383712cfacfbc591836e5dad28f8023c5b4b276f063e25b56c", b"\xd0\xcf\x11\xe0"),
    "ssc-resident-population-regions.xls": (
        "https://www.stat.gov.az/source/demoqraphy/en/001_17en.xls",
        "34057c449d9114277d5608b99c44e29a8d3dc9fc8ec5f9fce02a4911f2e35162", b"\xd0\xcf\x11\xe0"),
    "ssc-population-sex-2026.xls": (
        "https://www.stat.gov.az/source/demoqraphy/en/001_19en.xls",
        "fa66767c497fb1dd48f70762b26a0269519828ca26dccd087f6adbcc4c808b89", b"\xd0\xcf\x11\xe0"),
    "ssc-admin-classification-2024.pdf": (
        "https://www.stat.gov.az/menu/5/classifications/source/Inzibati-1.05.2024.pdf",
        "2445d60a6d7294d47ab7886eada3b27d86c8cdf9794da1962e3ba233952ef6b9", b"%PDF"),
    "ssc-census-2019-volume-a.zip": (
        "https://www.stat.gov.az/menu/6/statistical_yearbooks/source/Siyahiyaalinma-2019%2C%20Cild%20A.zip",
        "503b379af477e7022255cd02936dbb3cb3b777632a00b023f6d56e61d5028f05", b"PK\x03\x04"),
    "ssc-census-2019-volume-b.zip": (
        "https://www.stat.gov.az/menu/6/statistical_yearbooks/source/Siyahiyaalinma-2019%2C%20Cild%20B.zip",
        "be113eb342a218429a9d1e5112f7a232fa099e0ed270cf18ee1aa77a4de3e080", b"PK\x03\x04"),
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    result = []
    for name, (url, expected, signature) in SOURCES.items():
        path = raw / name
        if path.exists():
            status = "reused_verified"
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-acquisition/1.0"})
            temporary = None
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=name + ".", suffix=".part", delete=False) as out:
                        temporary = Path(out.name)
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            out.write(block)
                if sha256(temporary) != expected or temporary.read_bytes()[:4] != signature:
                    raise ValueError(f"Unreviewed upstream version or format: {name}")
                temporary.replace(path)
                status = "downloaded_verified"
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        if sha256(path) != expected or path.read_bytes()[:4] != signature:
            raise ValueError(f"Unreviewed local version or format: {name}")
        receipt = {
            "url": url, "retrieved_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "size_bytes": path.stat().st_size, "sha256": expected, "status": status,
            "redistribution_terms": "review_required",
        }
        (raw / (name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        result.append({"file": name, "status": status, "bytes": receipt["size_bytes"]})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

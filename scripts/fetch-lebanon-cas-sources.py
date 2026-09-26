"""Fetch three official CAS originals for a partial Lebanon source audit."""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


FILES = {
    "LFHLCS_2018_2019_Demography.xls": {
        "url": "https://www.cas.gov.lb/wp-content/uploads/2026/06/LFHLCS_2018_2019_Demography.xls",
        "sha256": "780f52f78949de142593717cde07cda03256d5759b534096443cf77a4e315486",
        "magic": bytes.fromhex("D0CF11E0"),
    },
    "LFHLCS_2018_2019_Report.pdf": {
        "url": "https://www.cas.gov.lb/wp-content/uploads/2025/07/Labour-Force-and-Household-Living-Conditions-Survey-2018-2019.pdf",
        "sha256": "589b164265045769ae5bf646e86fc2e4f05bbdbd47e07743c7f7b2583d457990",
        "magic": b"%PDF-",
    },
    "MICS6_Ch11_EQ_2023.xlsx": {
        "url": "https://www.cas.gov.lb/wp-content/uploads/2025/05/MICS6-Ch11-EQ-Equitable-chance-in-life-LB_EN.xlsx",
        "sha256": "f8ac41800587bf5f011b235da0487962df45dac8883335d0e4f4623dffcb1b60",
        "magic": b"PK\x03\x04",
    },
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, spec in FILES.items():
        path = raw / name
        if not path.exists():
            temporary = None
            try:
                req = urllib.request.Request(spec["url"], headers={"User-Agent": "AreaData-source-audit/1.0"})
                with urllib.request.urlopen(req, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=name + ".", suffix=".part", delete=False) as out:
                        temporary = Path(out.name)
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            out.write(block)
                if not temporary.read_bytes().startswith(spec["magic"]):
                    raise ValueError(f"Invalid source signature: {name}")
                temporary.replace(path)
                status = "downloaded"
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        else:
            status = "reused"
        with path.open("rb") as stream:
            if stream.read(len(spec["magic"])) != spec["magic"]:
                raise ValueError(f"Invalid source signature: {name}")
        actual = digest(path)
        if actual != spec["sha256"]:
            raise ValueError(f"Unreviewed source edition: {name} {actual}")
        receipt = {"url": spec["url"], "retrieved_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                   "size_bytes": path.stat().st_size, "sha256": actual, "status": status,
                   "reuse_terms": "review_required"}
        (raw / (name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        rows.append({"name": name, "bytes": path.stat().st_size, "sha256": actual, "status": status})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

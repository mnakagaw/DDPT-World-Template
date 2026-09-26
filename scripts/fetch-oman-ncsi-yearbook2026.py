"""Fetch the pinned official NCSI Statistical Year Book 2026 PDF privately."""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


NAME = "NCSI_Statistical_Yearbook_2026_Issue54.pdf"
URL = "https://api.ncsi.gov.om/uploads/pdfs/statistical_year_book_2026___issue_54_1777963604.pdf"
SHA256 = "93a4fc2ba4b508ab5b01a7ec5de041529ff284d8ba1b3eab6fe1b0463196f9df"
SIZE = 17012041


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / NAME
    if not path.exists():
        temporary = None
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "AreaData-official-source-audit/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response:
                with tempfile.NamedTemporaryFile(dir=raw, prefix=NAME + ".", suffix=".part", delete=False) as output:
                    temporary = Path(output.name)
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        output.write(block)
            temporary.replace(path)
            status = "downloaded"
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    else:
        status = "reused"
    if path.stat().st_size != SIZE or digest(path) != SHA256 or path.open("rb").read(5) != b"%PDF-":
        raise ValueError("NCSI yearbook bytes differ from the audited original")
    receipt = {"url": URL, "retrieved_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
               "size_bytes": SIZE, "sha256": SHA256, "status": status, "reuse_terms": "review_required"}
    (raw / (NAME + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

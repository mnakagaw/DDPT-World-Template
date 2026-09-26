"""Acquire four public PCBS 2017 originals for a partial Palestine census audit."""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


FILES = {
    "PCBS_2017_Final_Summary_book2383.pdf": {
        "url": "https://www.pcbs.gov.ps/Downloads/book2383.pdf",
        "sha256": "25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f",
        "size": 4663974,
    },
    "PCBS_2017_Detailed_Population_book2425.pdf": {
        "url": "https://www.pcbs.gov.ps/Downloads/book2425.pdf",
        "sha256": "0ab9b57187f3924a128069a685a83295a23d80ab7d706dc8e690b8df2e9d0520",
        "size": 6256624,
    },
    "PCBS_2017_Locality_Classification.pdf": {
        "url": "https://www.pcbs.gov.ps/Portals/_PCBS/Class/Arabic/Geography/localities-2017-class.pdf",
        "sha256": "4eafedbec01401f5a8fc7e9f4537ef97d2e5e435dc4dee3445a98f977380023b",
        "size": 2052149,
    },
    "PCBS_2017_Older_Summary_book2369.pdf": {
        "url": "https://www.pcbs.gov.ps/Downloads/book2369.pdf",
        "sha256": "49438e35b6e2f36a4cad7038411c8be43db12e753adf45fec74f31186d47d0e5",
        "size": 4634598,
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
                request = urllib.request.Request(spec["url"], headers={"User-Agent": "AreaData-source-audit/1.0"})
                with urllib.request.urlopen(request, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=name + ".", suffix=".part", delete=False) as output:
                        temporary = Path(output.name)
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            output.write(block)
                with temporary.open("rb") as stream:
                    signature = stream.read(5)
                if temporary.stat().st_size != spec["size"] or signature != b"%PDF-":
                    raise ValueError("Invalid PCBS original: " + name)
                temporary.replace(path)
                status = "downloaded"
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        else:
            status = "reused"
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("Invalid PDF signature: " + name)
        actual = digest(path)
        if path.stat().st_size != spec["size"] or actual != spec["sha256"]:
            raise ValueError("Unreviewed PCBS edition: " + name + " " + actual)
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

"""Fetch pinned public Jordan DoS and planning originals into a country project.

Existing hash-matching files are reused. Raw files stay in ignored generated/;
only public URLs, hashes, code and evidence summaries belong in Git.
"""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DOS_BASE = "https://dosweb.dos.gov.jo/databank/Population/Population_Estimares/"
FILES = {
    "PopulationEstimates.xlsx": (DOS_BASE + "PopulationEstimates.xlsx", "0917681306aa728e501464a8a42c0ec31ed81e66cf16245862ede53f007f7002"),
    "PopulationEstimatesbyLocality.xlsx": (DOS_BASE + "PopulationEstimatesbyLocality.xlsx", "ebf49f985570c25de141a26c75fc70790a0f7225fb351b3ecd04b68402bd0ef8"),
    "Municipalities.xlsx": (DOS_BASE + "Municipalities.xlsx", "3f880201fd685830e5c77f6505797a2bc91086412f72a758399dd4f92dda4b97"),
    "YearBook_2024_Population.pdf": ("https://dosweb.dos.gov.jo/databank/yearbook/YearBook_2024/Population.pdf", "4ebf27354c51d95776b4b51cbd27a9b34a7cdb021ab31de55c8e56f981b90dea"),
    "GovernoratePlanningGuide.pdf": ("https://www.mola.gov.jo/ebv4.0/root_storage/ar/eb_list_page/guide_for_the_preparation_of_governorate_strategic_development_and_implementation_plans.pdf", "ebb981db5b5afd468e3662461a0f84445732ab916b512d57f65ddd526efab85a"),
    "LocalAdministrationLaw2021.pdf": ("https://mola.gov.jo/EBV4.0/Root_Storage/AR/EB_Info_Page/%D9%82%D8%A7%D9%86%D9%88%D9%86_%D8%A7%D9%84%D8%A7%D8%AF%D8%A7%D8%B1%D8%A9_%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%D8%A92021.pdf", "715f73dc331e62764ee2ec7433ba06e402953ec706ac683df8f4e1f46d8569ac"),
}


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    raw = Path(args.project) / "raw" / "official-jordan"
    raw.mkdir(parents=True, exist_ok=True)
    result = []
    for filename, (url, expected) in FILES.items():
        path = raw / filename
        if path.exists():
            actual = file_hash(path)
            if actual != expected:
                raise ValueError(f"Existing raw file has changed: {filename} SHA-256 {actual}")
            status = "reused_verified"
            retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-acquisition/1.0"})
            temporary = None
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=filename + ".", suffix=".part", delete=False) as sink:
                        temporary = Path(sink.name)
                        while chunk := response.read(1024 * 1024):
                            sink.write(chunk)
                actual = file_hash(temporary)
                if actual != expected:
                    raise ValueError(f"Official source content changed: {filename} SHA-256 {actual}")
                with temporary.open("rb") as source:
                    signature = source.read(4)
                if signature != (b"%PDF" if filename.endswith(".pdf") else b"PK\x03\x04"):
                    raise ValueError(f"Unexpected source format: {filename}: {signature!r}")
                temporary.replace(path)
                status = "downloaded_verified"
                retrieved = datetime.now(timezone.utc).isoformat()
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        receipt = {"url": url, "retrieved_at_utc": retrieved, "size_bytes": path.stat().st_size,
                   "sha256": expected, "status": status, "redistribution_terms": "review_required"}
        (raw / f"{filename}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        result.append({"file": filename, "bytes": receipt["size_bytes"], "sha256": expected, "status": status})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

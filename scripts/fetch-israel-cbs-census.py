"""Acquire official Israel CBS 2022 census workbooks for a source audit.

URLs come from the CBS Population Census page. Hashes are pinned after the
first acquisition and must be reviewed before source import.
"""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = "https://www.cbs.gov.il/he/publications/LochutTlushim/2025/"
FILES = {
    "selected-data-localities-statistical-areas.xlsx": "Selected%20data%2C%20by%20localities%20and%20statistical%20areas%20-%20the%202022%20Census.xlsx",
    "population-group-religion-age-sex.xlsx": "Population%20by%20population%20group%2C%20religion%2C%20age%2C%20and%20sex%20-%202022%20Census%20estimate.xlsx",
    "population-households-locality.xlsx": "Population%20and%20households%20by%20locality%20-%202022%20Census%20estimate.xlsx",
    "population-selected-characteristics.xlsx": "Population%20by%20selected%20characteristics%20-%202022%20Census%20estimate%2C%20end%20of%202021%20population%20estimate%20and%202008%20Census%20estimate.xlsx",
    "households-selected-characteristics.xlsx": "Households%20by%20selected%20characteristics%20-%202022%20Census%20estimate%20and%202008%20Census%20estimate.xlsx",
    "broad-geographical-units.xlsx": "Summarized%20file%20of%20broad%20geographical%20units%20-%20census%202022.xlsx",
}
EXPECTED_SHA256 = {
    "selected-data-localities-statistical-areas.xlsx": "881f2c0625652b347f48f7058000b02e6977be8d19aeb3af25aeafbd4111a102",
    "population-group-religion-age-sex.xlsx": "71b963fd0be725a37d581aa7007c38ef3baf608463cadd916bf083e6e05f6694",
    "population-households-locality.xlsx": "bbdb08ef7ef152f05cc6d85f70fad26d34b7daed41d871bc145018e1dc97a949",
    "population-selected-characteristics.xlsx": "b3e77a362a710f99d053e31d788dd0cf4801d3c662ef0b4bcbebaae975bae09f",
    "households-selected-characteristics.xlsx": "2da9e0d9ad9f7214734bdf39d50c292edd57ec10c2c571707dbebcfe8f2b2c82",
    "broad-geographical-units.xlsx": "79a967d1e72127e4ea01296d77a32c2bd7d6e9fca132ac2b2029b1ac7c7d866d",
}


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(project):
    raw = project / "raw" / "official"
    raw.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, tail in FILES.items():
        url = BASE + tail
        path = raw / name
        if not path.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "AreaData-source-audit/1.0"})
            temporary = None
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    with tempfile.NamedTemporaryFile(dir=raw, prefix=name + ".", suffix=".part", delete=False) as out:
                        temporary = Path(out.name)
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            out.write(block)
                with temporary.open("rb") as stream:
                    signature = stream.read(4)
                if signature != b"PK\x03\x04":
                    raise ValueError(f"Not an XLSX ZIP: {name}")
                temporary.replace(path)
                status = "downloaded"
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        else:
            status = "reused"
        actual = hash_file(path)
        if actual != EXPECTED_SHA256[name]:
            raise ValueError(f"Unreviewed source edition: {name} {actual}")
        receipt = {"url": url, "retrieved_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                   "size_bytes": path.stat().st_size, "sha256": actual, "status": status,
                   "reuse_terms": "review_required"}
        (raw / (name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        rows.append({"name": name, "bytes": path.stat().st_size, "sha256": actual, "status": status})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

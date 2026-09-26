"""Fetch two official Yemen leads, preserving response bytes and distinct failures."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


SOURCES = [
    ("cso-2004-main-report.pdf",
     "https://cso-ye.org/wp-content/uploads/2023/11/%D8%A7%D9%84%D9%86%D8%AA%D8%A7%D8%A6%D8%AC-%D8%A7%D9%84%D9%86%D9%87%D8%A7%D8%A6%D9%8A%D8%A9-%D9%84%D8%AA%D8%B9%D8%AF%D8%A7%D8%AF-%D8%A7%D9%84%D8%B9%D8%A7%D9%85-%D9%84%D9%84%D8%B3%D9%83%D8%A7%D9%86-%D9%88%D8%A7%D9%84%D9%85%D8%B3%D8%A7%D9%83%D9%86-%D9%88%D8%A7%D9%84%D9%85%D9%86%D8%B4%D8%A3%D8%AA-2004-%D9%85-%D8%A7%D9%84%D8%AA%D9%82%D8%B1%D9%8A%D8%B1-%D8%A7%D9%84%D8%A6%D9%8A%D8%B3-1.pdf"),
    ("parliament-local-authority-law-2000.pdf",
     "https://yemenparliament.gov.ye/uploads/posts/documents/2018/12/1219201894218116.pdf"),
]
MAX_BYTES = 100_000_000


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    if json.loads((project / "data/dashboard.json").read_text(encoding="utf-8"))["country"]["id"] != "YEM":
        raise ValueError("Expected Yemen project")
    out = project / "raw/official-yemen"
    out.mkdir(parents=True, exist_ok=True)
    receipts = []
    session = requests.Session()
    session.headers["User-Agent"] = "AreaData official source audit/0.1"
    for filename, url in SOURCES:
        stamp = datetime.now(timezone.utc).isoformat()
        receipt = {"name": filename, "url": url, "checked_at": stamp}
        try:
            response = session.get(url, stream=True, timeout=90)
            chunks = []
            size = 0
            for chunk in response.iter_content(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Response exceeds the collection cap")
                chunks.append(chunk)
            body = b"".join(chunks)
            digest = hashlib.sha256(body).hexdigest()
            receipt.update(status=response.status_code, content_type=response.headers.get("Content-Type"),
                           bytes=size, final_url=response.url, response_sha256=digest)
            if response.ok and body.startswith(b"%PDF-"):
                target = out / filename
                if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise ValueError("New PDF differs from retained original; inspect both editions")
                if not target.exists():
                    target.write_bytes(body)
                receipt.update(acquisition="success", sha256=digest, object_path=filename)
            else:
                failed_name = f"{filename}.response-{digest[:12]}.bin"
                failed_path = out / failed_name
                if not failed_path.exists():
                    failed_path.write_bytes(body)
                receipt.update(acquisition="failed", reason="HTTP failure or response is not a PDF",
                               response_path=failed_name)
        except (requests.RequestException, ValueError) as error:
            receipt.update(acquisition="failed", reason=str(error))
        receipts.append(receipt)
        print(json.dumps({"name": filename, "acquisition": receipt["acquisition"],
                          "status": receipt.get("status"), "bytes": receipt.get("bytes")}, ensure_ascii=False))
    (out / "acquisition.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

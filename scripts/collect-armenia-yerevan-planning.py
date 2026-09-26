#!/usr/bin/env python3
"""Archive a second Armenian community's official planning and reporting sources."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
RAW = PROJECT / "raw" / "yerevan-planning"
EVIDENCE = PROJECT / "evidence"
HTML = {
    "yerevan-special-local-government-law": "https://www.arlis.am/hy/acts/229984",
    "yerevan-five-year-plan-2024-2028-decision": "https://www.arlis.am/hy/acts/188571",
    "yerevan-annual-program-2026-decision": "https://yerevan.am/hy/elders-decisions/460-a-1/",
    "yerevan-program-2025-implementation-report-decision": "https://www.yerevan.am/hy/elders-decisions/513-a-2/",
    "yerevan-budget-2026-current-decision": "https://www.arlis.am/hy/acts/230905",
    "yerevan-budget-2026-september-amendment": "https://www.arlis.am/hy/acts/230892",
    "yerevan-budget-2025-execution-decision": "https://www.yerevan.am/hy/elders-decisions/518-n-2/",
    "yerevan-development-program-index": "https://www.yerevan.am/hy/development-programs/",
}
PDF = {
    "yerevan-five-year-plan-2024-2028.pdf": "https://www.arlis.am/acts/files/317164/dfa5b491d742f44ffb556c93277e6e8f36d844761495489f38a770fc317f1c77",
    "yerevan-annual-program-2026.pdf": "https://www.yerevan.am/uploads/media/default/0002/59/68370808c18ed14ec88559eaf3c69464a06a163f.pdf",
    "yerevan-program-2025-implementation-report.pdf": "https://www.yerevan.am/uploads/media/default/0002/60/8527e7d3beb28446f2ae3adb669dc11f4caf723a.pdf",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    session = requests.Session()
    receipts = []
    for name, url in [*HTML.items(), *PDF.items()]:
        response = session.get(url, timeout=90)
        response.raise_for_status()
        if name.endswith(".pdf") and not response.content.startswith(b"%PDF-"):
            raise ValueError(f"Expected PDF source: {url}, got {response.headers.get('Content-Type')}")
        if not name.endswith(".pdf") and b"<html" not in response.content[:500].lower():
            raise ValueError(f"Expected HTML source: {url}")
        filename = name if name.endswith(".pdf") else name + ".html"
        path = RAW / filename
        path.write_bytes(response.content)
        receipts.append({"url": url, "http_status": response.status_code,
                         "content_type": response.headers.get("Content-Type"),
                         "bytes": len(response.content),
                         "sha256": hashlib.sha256(response.content).hexdigest(),
                         "path": str(path.relative_to(PROJECT)).replace("\\", "/"),
                         "retrieved_at_utc": datetime.now(timezone.utc).isoformat()})
        print(filename, response.status_code, len(response.content))
    (EVIDENCE / "ARM_YEREVAN_PLANNING_RECEIPTS.json").write_text(
        json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

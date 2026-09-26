#!/usr/bin/env python3
"""Archive selected Armenian official law, code and Ashtarak plan/budget originals."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "armenia-areadata-20260927"
RAW = PROJECT / "raw" / "official-planning"
EVIDENCE = PROJECT / "evidence"
SOURCES = {
    "local-self-government-law-2026": "https://www.arlis.am/hy/acts/231070",
    "administrative-classifier-2026": "https://www.arlis.am/hy/acts/220427",
    "ashtarak-plan-decision-2022-2026": "https://www.arlis.am/hy/acts/173115",
    "ashtarak-budget-decision-2026": "https://www.arlis.am/hy/acts/219910",
}
ATTACHMENTS = {
    "ashtarak-plan-2022-2026.pdf": "https://www.arlis.am/acts/files/293865/aa26f34ad91883936526b149e1bda0f3da3ab5655d74f99a9c573ae79a6b354c",
    "ashtarak-budget-2026-annexes.xls": "https://www.arlis.am/acts/files/358896/a5d4e573b80ed069ff7a7aa6e5d8f625139add90c0b727b36da0994a8a6458d0",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    receipts = []
    for stem, url in SOURCES.items():
        response = session.get(url, timeout=60)
        response.raise_for_status()
        path = RAW / f"{stem}.html"
        path.write_bytes(response.content)
        receipts.append({"url": url, "http_status": response.status_code, "content_type": response.headers.get("Content-Type"), "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(), "path": str(path.relative_to(PROJECT)).replace("\\", "/"), "retrieved_at_utc": datetime.now(timezone.utc).isoformat()})
        print(path.name, response.status_code, len(response.content))
        if stem.startswith("ashtarak"):
            expected = ATTACHMENTS["ashtarak-plan-2022-2026.pdf" if "plan" in stem else "ashtarak-budget-2026-annexes.xls"]
            if expected.split("www.arlis.am", 1)[1] not in response.text:
                raise ValueError(f"Expected attachment link absent from {url}")
    for filename, url in ATTACHMENTS.items():
        response = session.get(url, timeout=90)
        response.raise_for_status()
        if filename.endswith(".pdf") and not response.content.startswith(b"%PDF-"):
            raise ValueError(f"Expected PDF bytes at {url}; got {response.headers.get('Content-Type')}")
        if filename.endswith(".xls") and not response.content.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
            raise ValueError(f"Expected legacy Excel bytes at {url}; got {response.headers.get('Content-Type')}")
        path = RAW / filename
        path.write_bytes(response.content)
        receipts.append({"url": url, "http_status": response.status_code, "content_type": response.headers.get("Content-Type"), "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(), "path": str(path.relative_to(PROJECT)).replace("\\", "/"), "retrieved_at_utc": datetime.now(timezone.utc).isoformat()})
        print(path.name, response.status_code, len(response.content))
    (EVIDENCE / "ARM_OFFICIAL_PLANNING_RECEIPTS.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

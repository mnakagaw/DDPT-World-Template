#!/usr/bin/env python3
"""Acquire the official Nicaragua planning, budget and execution evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


SOURCES = [
    ("law-40-consolidated.html", "https://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?action=openDocument&documentId=67CC56A8B80761DA0625886F006DCDBC", "law"),
    ("law-475-participation.html", "https://legislacion.asamblea.gob.ni/Normaweb.nsf/%28%24All%29/F78CA467F5C96D0306257257005FBADC", "law"),
    ("law-792-municipal-reform.pdf", "https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/c9a0faf9d8c5e28f062572c70052cde2/7ebe8ba4e242fa7b062579eb0064e3b6/%24FILE/Ley%20No.%20792%20reforma%20Ley%20de%20municipios.pdf", "law"),
    ("law-828-budget-reform.pdf", "https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/0/362c8026f915756806257ac6007facc6/%24FILE/Ley%20No.%20828%20Ley%20de%20Reforma%20a%20la%20Ley%20R%C3%A9gimen%20Presupuestario%20Municipal.pdf", "law"),
    ("budget-2026.html", "https://www.hacienda.gob.ni/presupuesto2026/", "budget"),
    ("budget-execution-2026-q1.pdf", "https://www.hacienda.gob.ni/wp-content/uploads/2026/05/INFORME-DE-EJECUCION-PRESUPUESTARIA-ENERO-MARZO-2026.pdf", "implementation"),
    ("public-investment-program.html", "https://www.hacienda.gob.ni/programa-de-inversion-publica/", "implementation"),
    ("public-investment-reports.html", "https://www.hacienda.gob.ni/reportes-del-programa-de-inversion-publica/", "evaluation"),
    ("national-poverty-development-plan.html", "https://www.hacienda.gob.ni/plan-nacional-de-lucha-contra-la-pobreza-2022-2026/", "plan"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")
    out.mkdir(parents=True)
    entries = []
    for filename, url, category in SOURCES:
        target = out / filename
        request = Request(url, headers={"User-Agent": "AreaData/0.10 Nicaragua planning evidence collector"})
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                target.write_bytes(body)
                entries.append({
                    "file": filename,
                    "url": url,
                    "final_url": response.geturl(),
                    "category": category,
                    "status": "acquired",
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": digest(target),
                })
        except (URLError, TimeoutError, OSError) as error:
            entries.append({
                "file": filename,
                "url": url,
                "category": category,
                "status": "retrieval_failed_with_evidence",
                "bytes": 0,
                "error_type": type(error).__name__,
                "error": str(error),
            })
    receipt = {
        "schema_version": "1.0",
        "country_area_id": "NIC",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
        "scope_limit": "National legal, budget and execution evidence does not prove that every municipality has a current approved development plan or that every planned activity was implemented.",
    }
    (out / "planning-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(row["status"] == "acquired" for row in entries),
                      "failed": sum(row["status"] != "acquired" for row in entries),
                      "bytes": sum(row["bytes"] for row in entries)}, indent=2))


if __name__ == "__main__":
    main()

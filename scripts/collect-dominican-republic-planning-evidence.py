#!/usr/bin/env python3
"""Acquire official Dominican Republic planning, budget and implementation evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SOURCES = [
    ("law-176-07.pdf", "https://consultoria.gov.do/Consulta/Home/FileManagement?documentId=3345180&managementType=1", "law"),
    ("law-498-06.pdf", "https://mepyd.gob.do/wp-content/uploads/drive/DIGEDES/Monitoreo%20y%20Evaluaci%C3%B3n/Publicaciones/Normativa/Ley-498-06%20Planificaci%C3%B3n%20e%20Inversi%C3%B3n%20P%C3%BAblica.pdf", "law"),
    ("municipal-development-plan-guide.html", "https://mepyd.gob.do/publicaciones/guia-para-la-formulacion-de-planes-de-desarrollo-municipales", "guidance"),
    ("municipal-development-plan-guide.pdf", "https://mepyd.gob.do/wp-content/uploads/drive/VIOTDR/Publicaciones/Gu%C3%ADa%20metodol%C3%B3gica%20-%20C%C3%B3mo%20elaborar%20un%20plan%20municipal%20de%20desarrollo.pdf", "guidance"),
    ("comendador-pdm-2025-2029.pdf", "https://ayuntamientocomendador.gob.do/transparencia/wp-content/uploads/2026/01/PDM-Comendador-2025-2029.pdf", "plan"),
    ("local-government-budgets.html", "https://hist.digepres.gob.do/presupuesto/gobiernos-locales/?print=print", "budget"),
    ("local-government-budget-dashboard.html", "https://www.digepres.gob.do/digepres-presenta-nueva-herramienta-para-transparentar-ejecucion-presupuestaria-de-gobiernos-locales/?print=pdf", "implementation"),
    ("municipal-planning-assistance.html", "https://mepyd.gob.do/asistencia-tecnica-en-temas-de-desarrollo-municipales/", "evaluation"),
]


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
        request = Request(url, headers={"User-Agent": "AreaData/0.10 Dominican Republic planning evidence collector"})
        target = out / filename
        try:
            with urlopen(request, timeout=90) as response:
                body = response.read()
                target.write_bytes(body)
                entries.append({"file": filename, "url": url, "final_url": response.geturl(), "category": category, "status": "acquired", "content_type": response.headers.get("Content-Type", ""), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            entries.append({"file": filename, "url": url, "category": category, "status": "retrieval_failed_with_evidence", "bytes": 0, "error_type": type(error).__name__, "error": str(error)})
    receipt = {"schema_version": "1.0", "country_area_id": "DOM", "retrieved_at": datetime.now(timezone.utc).isoformat(), "entries": entries, "scope_limit": "The legal framework and national catalogs do not prove that every municipality has a current approved plan, complete budget execution, or an official outcome evaluation. Each document retains its own territorial and temporal scope."}
    (out / "planning-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": sum(row["status"] == "acquired" for row in entries), "failed": sum(row["status"] != "acquired" for row in entries), "bytes": sum(row["bytes"] for row in entries)}, indent=2))


if __name__ == "__main__":
    main()

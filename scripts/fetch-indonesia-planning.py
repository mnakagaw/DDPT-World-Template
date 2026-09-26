"""Archive accessible Indonesian official catalogue and planning-law originals.

Jawa Barat's RPJMD body and the later Kemendagri code register are source leads;
their inaccessible bodies are deliberately not represented as acquired here.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/indonesia-planning-source-manifest.json"
SOURCES = [
    ("idn-bps-sp2020-population-catalogue", "https://sensus.bps.go.id/topik/dataset/sp2020/16",
     "raw/idn-bps-sp2020-population-catalogue.html", "text/html", b"Jumlah dan Distribusi Penduduk"),
    ("idn-surabaya-jdih-permendagri-86-2017-page", "https://jdih.surabaya.go.id/others/3803",
     "raw/idn-surabaya-jdih-permendagri-86-2017-page.html", "text/html", b"Nomor 86 Tahun 2017"),
    ("idn-permendagri-86-2017-surabaya-copy", "https://jdih.surabaya.go.id/peraturan/download/3803",
     "raw/idn-permendagri-86-2017-surabaya-copy.pdf", "application/pdf", b"%PDF"),
    ("idn-jabar-official-plan-catalogue", "https://jabarprov.go.id/arsip-dan-dokumen?kategori=dokumen+perencanaan&tahun=2025",
     "raw/idn-jabar-official-plan-catalogue.html", "text/html", b"RPJMD"),
]


def digest(body):
    return hashlib.sha256(body).hexdigest()


def acquire(project):
    previous = {}
    if MANIFEST.exists():
        previous = {entry["id"]: entry for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]}
    result = []
    for sid, url, relative, mime, marker in SOURCES:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        old = previous.get(sid)
        if target.exists():
            body = target.read_bytes()
            if old and (len(body), digest(body)) != (old["bytes"], old["sha256"]):
                raise ValueError(f"Archived original changed: {sid}")
            retrieved_at = old["retrieved_at"] if old else datetime.now(timezone.utc).isoformat()
        else:
            response = requests.get(url, timeout=90, headers={"User-Agent": "AreaData official-source-acquisition/1.0"})
            response.raise_for_status()
            if urlparse(response.url).hostname not in {"sensus.bps.go.id", "jdih.surabaya.go.id", "jabarprov.go.id"}:
                raise ValueError(f"Unexpected source redirect: {response.url}")
            body = response.content
            retrieved_at = datetime.now(timezone.utc).isoformat()
            target.write_bytes(body)
        if marker not in body or len(body) < 1000:
            raise ValueError(f"Official original signature not found: {sid}")
        item = {"id": sid, "url": url, "raw_path": relative, "mime_type": mime,
                "bytes": len(body), "sha256": digest(body), "retrieved_at": retrieved_at}
        if mime == "application/pdf":
            reader = PdfReader(target)
            first = reader.pages[0].extract_text() or ""
            if "NOMOR 86 TAHUN 2017" not in first or "MENTERI DALAM NEGERI" not in first:
                raise ValueError("Law PDF identity mismatch")
            item["pages"] = len(reader.pages)
            item["inspected_pdf_pages"] = [1, 5, 6, 7, 15, 16]
        result.append(item)
    manifest = {"schema_version": "1.0", "sources": result,
                "unacquired_leads": [
                    {"id": "idn-jabar-rpjmd-2025-2029", "url": "https://jdih.jabarprov.go.id/page/info/produk/53538?tentang=peraturan-daerah-provinsi-jawa-barat-nomor-7-tahun-2025-tentang-rencana-pembangunan-jangka-menengah-daerah-tahun-2025-2029",
                     "status": "official_location_identified_pdf_get_403", "body_acquired": False},
                    {"id": "idn-kemendagri-2025-code-register", "url": "https://ppid.kemendagri.go.id/storage/dokumen/QBPTW8gxbngpCGprIS5ybgC1puZYD1b8S0F0Uyes.pdf",
                     "status": "official_location_identified_connect_timeout", "body_acquired": False},
                ]}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquired_originals": len(result), "law_pages": next(x["pages"] for x in result if x["mime_type"] == "application/pdf"),
                      "unacquired_leads": len(manifest["unacquired_leads"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    acquire(parser.parse_args().project)

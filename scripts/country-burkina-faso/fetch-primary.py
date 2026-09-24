"""Fetch the fixed INSD RGPH 2019 source set; never silently accept an HTML error page."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "insd-rgph-2019"
RAW.mkdir(parents=True, exist_ok=True)
SOURCES = {
    "statistical_tables.pdf": "https://web2.insd.bf/sites/default/files/2024-06/Volume%20des%20tableaux%20statistiques_%205e%20RGPH.pdf",
    "localities.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/270",
    "questionnaire.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/268",
    "key_figures.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/269",
    "results_leaflet.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/271",
    "final_report.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/273",
    "communal_disparities.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/272",
    "poverty_map.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/275",
    "households_and_population.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/274",
    "demographic_projections.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/276",
    "quality_population.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/277",
    "documentation.pdf": "https://microdata.insd.bf/index.php/catalog/69/download/278",
}

receipts = []
for filename, url in SOURCES.items():
    target = RAW / filename
    if target.exists() and target.read_bytes().startswith(b"%PDF-"):
        data = target.read_bytes()
        status = "cached_pdf"
        final_url = url
    else:
        request = Request(url, headers={"User-Agent": "AreaDataSourceResearch/1.0"})
        try:
            with urlopen(request, timeout=70) as response:
                data = response.read()
                final_url = response.url
            if not data.startswith(b"%PDF-"):
                raise ValueError("response is not a PDF")
            target.write_bytes(data)
            status = "acquired_pdf"
        except Exception as error:
            receipts.append({"name": filename, "url": url, "status": "failed", "error": str(error)})
            continue
    receipts.append({
        "name": filename, "url": url, "final_url": final_url, "status": status,
        "bytes": len(data), "sha256": sha256(data).hexdigest(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })
    print(f"{filename}: {status} {len(data)} bytes", flush=True)

(RAW / "receipts.json").write_text(json.dumps(receipts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if any(item["status"] == "failed" for item in receipts):
    raise SystemExit(1)

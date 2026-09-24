"""Acquire local planning references and separate 2017 boundary audit files."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
SOURCES = {
    "planning/pcd-guide.pdf": "https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/GMPL_PCD_Version_definitive_1.pdf",
    "planning/prd-guide.pdf": "https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/GMPL_PRD_Version_definitive_1.pdf",
    "planning/collectivities-code-2025.pdf": "https://www.academiedepolice.bf/index.php/telechargement/category/25-deconcentration-et-decentralisation?download=226:code-general-des-colectivite",
    "planning/pld-monitoring-2024.pdf": "https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/MEF_RAPPORT_NATIONAL_2024_SUIVI_PLD_FINAL.pdf",
    "geoboundaries-adm2.geojson": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BFA/ADM2/geoBoundaries-BFA-ADM2_simplified.geojson",
    "geoboundaries-adm3.geojson": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BFA/ADM3/geoBoundaries-BFA-ADM3_simplified.geojson",
}
receipts = []
for name, url in SOURCES.items():
    target = RAW / name
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        if target.exists():
            payload = target.read_bytes()
            status = "cached"
        else:
            with urlopen(Request(url, headers={"User-Agent": "AreaDataSourceResearch/1.0"}), timeout=90) as response:
                payload = response.read()
            status = "acquired"
        if name.endswith(".pdf"):
            assert payload.startswith(b"%PDF-"), name
        else:
            features = json.loads(payload)["features"]
            expected = 351 if "adm3" in name else 45
            assert len(features) == expected, (name, len(features))
        if status == "acquired":
            target.write_bytes(payload)
        receipts.append({
            "name": name, "url": url, "status": status,
            "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as error:
        receipts.append({"name": name, "url": url, "status": "failed", "error": str(error)})
(RAW / "supplementary-receipts.json").write_text(json.dumps(receipts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for receipt in receipts:
    print(receipt["name"], receipt["status"])
if any(receipt["status"] == "failed" for receipt in receipts):
    raise SystemExit(1)

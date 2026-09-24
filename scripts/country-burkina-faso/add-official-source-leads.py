"""Record newly located official sources without promoting them to data adoption."""
from argparse import ArgumentParser
from pathlib import Path
import json


ap = ArgumentParser()
ap.add_argument("--project", required=True)
args = ap.parse_args()
path = Path(args.project) / "data/dashboard.json"
data = json.loads(path.read_text(encoding="utf-8"))
assert data["country"]["id"] == "BFA"
leads = [
    {
        "id": "bfa-insd-regional-yearbook-catalogue-2026",
        "name": "INSD regional statistical yearbooks catalogue, including 2024 editions",
        "url": "https://www.insd.bf/fr/statistiques/autres-statitiques/annuaires-statistiques-regionaux?combine=&items_per_page=10&page=1",
        "publisher": "Institut national de la statistique et de la démographie (INSD)",
        "reference_period": "2023 and 2024 regional yearbook listings; individual coverage varies",
        "status": "partial", "retrieved_at": "2026-09-24",
        "note": "Official HTML listing identified. Individual PDFs, tables, geography, denominators, contents and terms are not acquired or adopted; listings use historical region names and must be reconciled with the 2025 reform.",
    },
    {
        "id": "bfa-government-transfer-decrees-notice-2026",
        "name": "Government notice on 30 July 2026 territorial competence-transfer decrees",
        "url": "https://gouvernement.gov.bf/conseil-des-ministres/conseil-des-ministres-n25-du-30-juillet-2026/",
        "publisher": "Service d’information du Gouvernement du Burkina Faso",
        "reference_period": "30 July 2026 council adoption notice",
        "status": "partial", "retrieved_at": "2026-09-24",
        "note": "Official notice reports decrees applying law 024-2025/ALT across sectoral powers and resources. Decree numbers and signed full texts were not acquired; the notice does not establish a local plan, budget or 2019-to-current territorial crosswalk.",
    },
]
existing = {source["id"] for source in data["sources"]}
for lead in leads:
    if lead["id"] not in existing:
        data["sources"].append(lead)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source_count": len(data["sources"]), "new_leads": [lead["id"] for lead in leads]}))

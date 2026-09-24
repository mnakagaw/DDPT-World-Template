"""Close generator-only statements after the Burkina Faso source adapters run."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
path = root / "data/dashboard.json"
d = json.loads(path.read_text(encoding="utf-8"))
population = next(x for x in d["indicators"] if x["id"] == "BFA_RGPH2019_POP_TOTAL")
population["name"] = "Census population, total (2019)"
for indicator in d["indicators"]:
    if indicator["source_id"].startswith("wb-"):
        indicator["theme"] = "National context"
d["country"]["geography_note"] = (
    "The INSD 2019 census uses 13 regions, 45 provinces and 351 communes. "
    "The 2025 reform established 17 regions and 47 provinces; 2019 statistical areas are "
    "not silently relabelled as today's legal administrative units. ADM1/ADM2 map shapes are "
    "2017 geoBoundaries references, not certified legal boundaries. Communes have no verified joined polygons."
)
d["collection"]["notes"] = [
    note for note in d["collection"]["notes"]
    if not note.startswith("Initial national-data site inputs only")
    and not note.startswith("Country edition integrates INSD 2019 census locality totals")
]
d["collection"]["notes"].insert(0,
    "Country edition integrates INSD 2019 census locality totals, regional tables, poverty atlas annexes and a separately labelled 2015 modeled contraceptive indicator. WDI is national context only; source geography and periods remain distinct."
)
for feature in d["boundaries"]["features"]:
    if feature.get("properties", {}).get("territory_id", "").startswith("BFA:gbOpen:ADM1:"):
        feature["properties"]["source_id"] = "geoboundaries-adm1"
for gap in d["gaps"]:
    if gap["category"] == "subnational_statistics":
        gap.update({
            "status": "partial",
            "detail": "INSD RGPH 2019 provides extensive local population and nonmonetary indicators. The 12 WDI series are national context only; some source tables and commune/urban subdivisions remain outside the adopted dashboard scope.",
            "next_action": "Review the source table inventory for unadopted fields and collect current post-2025 local series before comparing them with 2019 census geography."
        })
    elif gap["category"] == "planning_documents":
        gap.update({
            "status": "partial",
            "detail": "National PCD/PRD methodology, the 2025 territorial code and the 2024 PLD monitoring report were acquired. Area-specific plan, budget, implementation and evaluation records have not yet been joined to historic census areas.",
            "next_action": "Inventory the 2024 monitoring annex and each current municipality's official plan and budget. Reconcile 2025 administrative reforms before area-specific status claims."
        })
path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

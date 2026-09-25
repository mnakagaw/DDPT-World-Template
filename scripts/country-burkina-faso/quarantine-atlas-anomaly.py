"""Quarantine the confirmed impossible percentage in an existing BFA build.

Fresh builds are protected in add-poverty-atlas.py. This narrow repair makes an
already-built country dataset match that rule without rerunning source downloads.
"""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import re


parser = ArgumentParser()
parser.add_argument("--project", required=True)
args = parser.parse_args()
project = Path(args.project).resolve()
dataset_path = project / "data/dashboard.json"
text_path = project / "raw/insd-rgph-2019/poverty_map.txt"
evidence_path = project / "evidence/POVERTY_ATLAS_IMPORT.json"

source_text = text_path.read_text(encoding="utf-8")
assert re.search(r"Zoungou\s+52,6\s+70800\s+14,5\s+54,4\s+74,7", source_text)
data = json.loads(dataset_path.read_text(encoding="utf-8"))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
territory_id = "BFA:RGPH2019:ADM3:GANZOURGOU:ZOUNGOU"
indicator_id = "BFA_INSD_LITERACY_15_64"
match = [row for row in data["observations"] if row["territory_id"] == territory_id
         and row["indicator_id"] == indicator_id and row["period"] == "2019"]
assert len(match) <= 1
if match:
    assert match[0]["value"] == 70800 and match[0]["status"] == "observed"
    assert match[0]["source_id"] == "bfa-insd-poverty-atlas-2019"
    data["observations"].remove(match[0])

anomaly = {
    "annex": 8, "code": "11 07 08 00", "name": "Zoungou",
    "territory_id": territory_id, "indicator_id": indicator_id,
    "published_text": "70800", "pdf_page": 272, "printed_page": 252,
    "reason": "The source PDF itself prints 70800 for a percentage; the value is withheld without inferring a correction.",
}
evidence.setdefault("source_anomalies", [])
if not any(item.get("territory_id") == territory_id and item.get("indicator_id") == indicator_id
           for item in evidence["source_anomalies"]):
    evidence["source_anomalies"].append(anomaly)
    evidence["observations_added"] -= 1
evidence["method"] = (
    "Exact Annex 4 parent/order/name/population crosswalk; Annexes 5-9 aligned "
    "by published row sequence and normalized label. Incomplete numeric rows "
    "and impossible percentages are withheld, with raw source text retained in evidence."
)
if not any(gap.get("category") == "source_value_anomaly" and "Zoungou" in gap.get("detail", "")
           for gap in data["gaps"]):
    data["gaps"].append({
        "category": "source_value_anomaly", "status": "pending",
        "detail": "INSD RGPH 2019 poverty atlas Annex 8 prints 70800 for Zoungou literacy age 15-64 (PDF page 272, printed page 252); this impossible percentage is withheld, not converted to zero or silently corrected.",
        "next_action": "Check an official erratum or corrected source table before adopting a replacement value.",
    })

dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"removed_observations": len(match), "dataset_sha256": sha256(dataset_path.read_bytes()).hexdigest(),
                  "anomalies": len(evidence["source_anomalies"])}))

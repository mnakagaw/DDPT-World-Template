"""Withhold Annex 8 dependency values whose printed definition conflicts with counts.

The PDF defines the measure as (<18 plus >64) / (18-64), yet prints 48.5%
nationally. The census age totals alone imply a strict lower bound above 94%.
This script corrects an existing country build; fresh builds skip the column in
add-poverty-atlas.py.
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
assert re.search(r"\[24\] Taux de dépendance démographique\s*:\s*rapport entre la population totale de moins de 18 ans et\s*de plus de 64 ans et la population totale de 18-64 ans", source_text)
assert re.search(r"BURKINA FASO\s+45,1\s+30,9\s+48,5\s+27,6\s+84,7", source_text)
data = json.loads(dataset_path.read_text(encoding="utf-8"))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
indicator_id = "BFA_INSD_DEMOGRAPHIC_DEPENDENCY"


def national_value(indicator: str) -> int:
    matches = [row for row in data["observations"] if row["territory_id"] == "BFA"
               and row["indicator_id"] == indicator and row["period"] == "2019"]
    assert len(matches) == 1 and matches[0]["status"] == "observed"
    return matches[0]["value"]


population = national_value("BFA_RGPH2019_POP_TOTAL")
known_dependents = sum(national_value(indicator) for indicator in (
    "BFA_RGPH2019_AGE_0_4", "BFA_RGPH2019_AGE_5_14", "BFA_RGPH2019_AGE_65_PLUS"))
lower_bound = 100 * known_dependents / (population - known_dependents)
assert population == 20505155 and 94 < lower_bound < 96, lower_bound

indicators = [item for item in data["indicators"] if item["id"] == indicator_id]
observations = [item for item in data["observations"] if item["indicator_id"] == indicator_id]
assert len(indicators) <= 1
if indicators:
    assert len(observations) == 408
    assert all(item["source_id"] == "bfa-insd-poverty-atlas-2019" and item["period"] == "2019"
               for item in observations)
    assert next(item["value"] for item in observations if item["territory_id"] == "BFA") == 48.5
    data["indicators"].remove(indicators[0])
    data["observations"] = [item for item in data["observations"] if item["indicator_id"] != indicator_id]
    data["analysis"].get("default_period_by_indicator", {}).pop(indicator_id, None)
    evidence["indicator_count"] -= 1
    evidence["observations_added"] -= len(observations)

for index, note in enumerate(data["collection"]["notes"]):
    if "Annexes 4-9 add 29 distinct indicators" in note:
        data["collection"]["notes"][index] = note.replace(
            "Annexes 4-9 add 29 distinct indicators",
            "Annexes 4-9 add 28 distinct indicators; the conflicting Annex 8 dependency column is withheld")

if not any(gap.get("category") == "source_definition_conflict" and indicator_id in gap.get("detail", "")
           for gap in data["gaps"]):
    data["gaps"].append({
        "category": "source_definition_conflict", "status": "pending",
        "detail": (f"INSD RGPH 2019 poverty atlas Annex 8 prints 48.5% nationally for {indicator_id} "
                   f"(PDF page 241), but the definition on PDF page 94 and the 2019 census age "
                   f"counts imply a strict lower bound of {lower_bound:.1f}%. The 408 source "
                   "values are withheld without inferring a different denominator."),
        "next_action": "Obtain an INSD erratum or documented definition/denominator before adopting the column.",
    })

conflict = {
    "annex": 8, "indicator_id": indicator_id,
    "published_national_value": 48.5, "strict_lower_bound_from_census_counts": round(lower_bound, 3),
    "definition_pdf_page": 94, "table_pdf_page": 241,
    "withheld_observations": 408,
    "reason": "Printed source definition and values conflict; no replacement denominator is inferred.",
}
evidence.setdefault("withheld_source_columns", [])
if not any(item.get("indicator_id") == indicator_id for item in evidence["withheld_source_columns"]):
    evidence["withheld_source_columns"].append(conflict)
evidence["method"] = (
    "Exact Annex 4 geographic crosswalk. Incomplete rows, impossible bounded "
    "percentages, and the definition-conflicted Annex 8 dependency column are withheld."
)

dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"removed_indicators": len(indicators), "removed_observations": len(observations),
                  "strict_lower_bound": round(lower_bound, 3),
                  "dataset_sha256": sha256(dataset_path.read_bytes()).hexdigest()}))

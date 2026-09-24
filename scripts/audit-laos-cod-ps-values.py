"""Read-only replay of all adopted Lao 2024 COD-PS population observations."""

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "laos-areadata-20260924"
FILES = [
    ("lao_admpop_adm0_2024.csv", "ADM0_PCODE"),
    ("hdx-cod-ps-lao-lao_admpop_adm1_2024.csv", "ADM1_PCODE"),
    ("hdx-cod-ps-lao-lao_admpop_adm2_2024.csv", "ADM2_PCODE"),
]


def expected(row):
    total = int(row["T_TL"])
    ages = {key: int(value) for key, value in row.items() if key.startswith("T_") and key != "T_TL"}
    under15 = sum(ages[f"T_{group}"] for group in ("00_04", "05_09", "10_14"))
    over65 = sum(ages[f"T_{group}"] for group in ("65_69", "70_74", "75_79", "80Plus"))
    return {
        "POP_TOTAL_2024": total,
        "POP_FEMALE_2024": int(row["F_TL"]),
        "POP_MALE_2024": int(row["M_TL"]),
        "SHARE_AGE_0_14_2024": under15 / total * 100,
        "SHARE_AGE_15_64_2024": (total - under15 - over65) / total * 100,
        "SHARE_AGE_65_PLUS_2024": over65 / total * 100,
    }


def main():
    lookup = {}
    for filename, code_field in FILES:
        with (PROJECT / "raw" / filename).open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                code = "LAO" if code_field == "ADM0_PCODE" and row[code_field] == "LA" else row[code_field]
                if code in lookup:
                    raise ValueError(f"duplicate P-code: {code}")
                lookup[code] = expected(row)
    data = json.loads((PROJECT / "data/dashboard.json").read_text(encoding="utf-8"))
    observations = [item for item in data["observations"] if item["source_id"] == "lao-cod-ps"]
    issues = []
    checked = 0
    for item in observations:
        expected_value = lookup.get(item["territory_id"], {}).get(item["indicator_id"])
        if expected_value is None or item["status"] != "observed" or abs(item["value"] - expected_value) > 0.000001:
            issues.append(f"{item['territory_id']}/{item['indicator_id']}: expected {expected_value}, got {item.get('value')}")
        else:
            checked += 1
    report = {"csv_geographies": len(lookup), "observations_checked": checked,
              "observation_count": len(observations), "issue_count": len(issues),
              "issue_examples": issues[:30], "verdict": "PASS_COD_PS_VALUES_ONLY" if not issues else "FAIL"}
    print(json.dumps(report, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())

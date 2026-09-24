"""Cross-check printed RGPH 2019 Tables I.5-I.7 against adopted 2019 counts.

This verifies row arithmetic and existing observations. It does not adopt new
urban/rural indicators or establish a current administrative correspondence.
"""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "raw/insd-rgph-2019/statistical_tables.txt").read_text(encoding="utf-8").splitlines()
data = json.loads((ROOT / "data/dashboard.json").read_text(encoding="utf-8"))
regions = {area["name"]: area["id"] for area in data["territories"] if area["level"] == "adm1"}
regions["Burkina Faso"] = "BFA"
assert len(regions) == 14
observed = {(row["territory_id"], row["indicator_id"], row["period"]): row["value"]
            for row in data["observations"] if row["status"] == "observed"}


def table_rows(table_id, count):
    pattern = re.compile(rf"^\s*Tableau\s+I\.{table_id}\s*:")
    start = next(i for i, line in enumerate(lines) if i > 900 and pattern.search(line))
    end = next(i for i in range(start + 1, len(lines)) if re.match(r"^\s*Tableau\s+I\.\d+\s*:", lines[i]))
    found = {}
    for line in lines[start + 1:end]:
        cells = re.split(r"\s{2,}", line.strip())
        if len(cells) != count + 1 or cells[0] not in regions:
            continue
        assert cells[0] not in found, (table_id, cells[0])
        found[cells[0]] = cells[1:]
    assert set(found) == set(regions), (table_id, sorted(set(regions) - set(found)))
    return found


pop = table_rows(5, 2)  # Count and population weight; weight is decimal.
residence = table_rows(6, 6)
sex = table_rows(7, 3)


def integer(value):
    return int(value.replace(" ", ""))


rows = []
for name, area_id in regions.items():
    i5_total = integer(pop[name][0])
    urban_male, urban_female, urban_total, rural_male, rural_female, rural_total = map(integer, residence[name])
    male, female, i7_total = map(integer, sex[name])
    adopted_total = observed[(area_id, "BFA_RGPH2019_POP_TOTAL", "2019")]
    adopted_male = observed[(area_id, "BFA_RGPH2019_POP_MALE", "2019")]
    adopted_female = observed[(area_id, "BFA_RGPH2019_POP_FEMALE", "2019")]
    assert urban_male + urban_female == urban_total, name
    assert rural_male + rural_female == rural_total, name
    assert urban_total + rural_total == i5_total, name
    assert male + female == i7_total == i5_total == adopted_total, name
    assert urban_male + rural_male == male == adopted_male, name
    assert urban_female + rural_female == female == adopted_female, name
    rows.append({
        "territory_id": area_id, "name_2019": name,
        "I.5_pdf_page": 28, "I.5_population": i5_total,
        "I.6_pdf_page": 29, "I.6_urban_male": urban_male,
        "I.6_urban_female": urban_female, "I.6_urban_total": urban_total,
        "I.6_rural_male": rural_male, "I.6_rural_female": rural_female,
        "I.6_rural_total": rural_total,
        "I.7_pdf_page": 29, "I.7_male": male, "I.7_female": female,
        "I.7_total": i7_total, "adopted_population": adopted_total,
        "adopted_male": adopted_male, "adopted_female": adopted_female,
        "arithmetic_and_adopted_match": "yes",
        "new_urban_rural_indicator_adopted": "no",
    })

out = ROOT / "evidence/FIRST_CENSUS_TABLES_CROSSCHECK.csv"
with out.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps({"rows": len(rows), "tables": ["I.5", "I.6", "I.7"],
                  "new_indicators_adopted": 0, "output": str(out)}, ensure_ascii=False))

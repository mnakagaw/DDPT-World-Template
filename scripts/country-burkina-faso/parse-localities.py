"""Extract RGPH 2019 region/province/commune totals from the INSD locality volume.

The printed tables are authoritative. This parser only accepts rows whose male,
female and total columns satisfy male + female = total; unmatched rows are
retained in the audit, never converted to zero.
"""
from collections import defaultdict
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "raw/insd-rgph-2019/localities.txt").read_text(encoding="utf-8")
REGION_ORDER = [
    ("Boucle du Mouhoun", 6), ("Cascades", 2), ("Centre", 1),
    ("Centre-Est", 3), ("Centre-Nord", 3), ("Centre-Ouest", 4),
    ("Centre-Sud", 3), ("Est", 5), ("Hauts-Bassins", 3),
    ("Nord", 4), ("Plateau Central", 3), ("Sahel", 4),
    ("Sud-Ouest", 4),
]


def key(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def numbers(line):
    cells = re.split(r"\s{2,}", line.strip())
    if len(cells) < 4:
        return None
    try:
        male, female, total = (int(cells[n].replace(" ", "")) for n in (1, 2, 3))
    except ValueError:
        return None
    if male + female != total:
        return None
    return male, female, total


regions = []
provinces = []
commune_rows = []
unparsed = []
special_rows = {}
arrondissements = defaultdict(list)
province = None
for line_no, line in enumerate(TEXT.split("\n"), 1):
    if line_no < 160:
        continue
    stripped = line.strip()
    if line_no in (5585, 6468):
        # In the printed table KINDI and GAO are unprefixed commune totals.
        expected = {5585: ("BOULKIEMDE", "KINDI"), 6468: ("ZIRO", "GAO")}[line_no]
        assert stripped.startswith(expected[1] + " "), (line_no, stripped[:80])
        value = numbers(line)
        assert value
        special_rows[line_no] = {"province": province, "name": expected[1],
                                  "part": None, "male": value[0], "female": value[1],
                                  "total": value[2], "estimated_marker": False,
                                  "line": line_no, "source_label_unprefixed": True}
    if (2451 <= line_no <= 2554 or 8863 <= line_no <= 8961) and re.match(r"^ARRONDISSEMENT\s+\d+\s", stripped):
        value = numbers(line)
        assert value
        city = "OUAGADOUGOU" if line_no < 5000 else "BOBO-DIOULASSO"
        arrondissements[city].append({"line": line_no, "male": value[0],
                                      "female": value[1], "total": value[2]})
    if re.match(r"^REGION\s*:\s*", stripped):
        value = numbers(line)
        if value:
            name = re.split(r"\s{2,}", stripped)[0].split(":", 1)[1].strip()
            regions.append({"name": name, "male": value[0], "female": value[1], "total": value[2], "line": line_no})
    if re.match(r"^PROVINCE\s*:\s*", stripped):
        value = numbers(line)
        if value:
            name = re.split(r"\s{2,}", stripped)[0].split(":", 1)[1].strip()
            province = name
            provinces.append({"name": name, "male": value[0], "female": value[1], "total": value[2], "line": line_no})
        elif "......" not in stripped:
            # The volume repeats a province title before the detailed table.
            # It changes the parent even though that title has no values.
            province = stripped.split(":", 1)[1].strip()
    if "COMMUNE" in stripped and ":" in stripped and not stripped.startswith("PROVINCE"):
        match = re.search(r"COMMUNE\s*:\s*([^\"]+)", line, re.I)
        if not match:
            continue
        value = numbers(line)
        if value is None:
            unparsed.append({"line": line_no, "text": stripped[:160], "kind": "commune"})
            continue
        name_raw = match.group(1).strip().strip('"')
        name_raw = re.split(r"\s{2,}", name_raw)[0].strip()
        name = re.sub(r"\*+", "", name_raw).strip()
        part = None
        part_match = re.search(r"\s*-\s*(rural|urbain)\s*$", name, re.I)
        if part_match:
            part = part_match.group(1).lower()
            name = name[:part_match.start()].strip()
        commune_rows.append({"province": province, "name": name, "part": part,
                             "male": value[0], "female": value[1], "total": value[2],
                             "estimated_marker": "*" in name_raw, "line": line_no})

assert len(provinces) == 45, len(provinces)
assert sum(count for _, count in REGION_ORDER) == 45
for item, region in zip(provinces, [name for name, count in REGION_ORDER for _ in range(count)]):
    item["region"] = region

groups = defaultdict(list)
for row in commune_rows:
    groups[(row["province"], key(row["name"]))].append(row)
for row in special_rows.values():
    groups[(row["province"], key(row["name"]))].append(row)
for city, pname, expected_count in (("OUAGADOUGOU", "KADIOGO", 12),
                                     ("BOBO-DIOULASSO", "HOUET", 7)):
    rows = arrondissements[city]
    assert len(rows) == expected_count, (city, len(rows))
    city_row = {"province": pname, "name": city.title(), "part": None,
                "male": sum(x["male"] for x in rows),
                "female": sum(x["female"] for x in rows),
                "total": sum(x["total"] for x in rows),
                "estimated_marker": False,
                "derived_from_arrondissement_lines": [x["line"] for x in rows],
                "line": rows[0]["line"]}
    groups[(pname, key(city))].append(city_row)
communes = []
ambiguous = []
for (pname, _), rows in groups.items():
    whole = [row for row in rows if row["part"] is None]
    if len(whole) == 1:
        chosen = whole[0].copy()
    elif len(whole) == 0 and len(rows) == 1:
        chosen = rows[0].copy()
    elif len(whole) == 0 and {r["part"] for r in rows} == {"rural", "urbain"}:
        chosen = rows[0].copy()
        for col in ("male", "female", "total"):
            chosen[col] = sum(r[col] for r in rows)
        chosen["estimated_marker"] = any(r["estimated_marker"] for r in rows)
        chosen["derived_from_parts"] = [r["line"] for r in rows]
    else:
        ambiguous.append({"province": pname, "rows": rows})
        continue
    chosen.pop("part", None)
    communes.append(chosen)

province_check = []
for p in provinces:
    children = [c for c in communes if c["province"] == p["name"]]
    province_check.append({"province": p["name"], "expected": p["total"],
                           "sum_communes": sum(c["total"] for c in children), "communes": len(children)})
output = {"source": "Fichier des localités du 5e RGPH 2019, INSD, June 2022",
          "national_total": 20505155, "regions": regions, "provinces": provinces,
          "communes": communes, "raw_commune_rows": len(commune_rows),
          "ambiguous": ambiguous, "unparsed": unparsed,
          "province_check": province_check,
          "province_sum": sum(p["total"] for p in provinces)}
assert output["province_sum"] == output["national_total"]
assert len(communes) == 351, len(communes)
assert all(x["expected"] == x["sum_communes"] for x in province_check), province_check
(ROOT / "raw/parsed-localities.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"regions": len(regions), "provinces": len(provinces), "communes": len(communes),
                  "raw_commune_rows": len(commune_rows), "province_sum": output["province_sum"],
                  "ambiguous": len(ambiguous), "unparsed": len(unparsed),
                  "province_mismatch": [x for x in province_check if x["expected"] != x["sum_communes"]]}, ensure_ascii=False))

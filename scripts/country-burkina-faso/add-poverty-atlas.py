"""Import the INSD RGPH volume 3 published annexes with a strict 2019 geography join.

Run after build-dashboard.py. No value is inferred for absent city aggregates or
partially extracted PDF rows. Annex 4 is a small-area poverty model, not a
direct census poverty observation; Annexes 5-9 are reported census indicators.
"""
from collections import Counter
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
import csv
import json
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/dashboard.json"
PDF = ROOT / "raw/insd-rgph-2019/poverty_map.pdf"
TXT = ROOT / "raw/insd-rgph-2019/poverty_map.txt"
URL = "https://microdata.insd.bf/index.php/catalog/69/download/275"

if not TXT.exists():
    subprocess.run(["pdftotext", "-layout", str(PDF), str(TXT)], check=True)
content = TXT.read_text(encoding="utf-8")
starts = [content.index(f"Annexe {n} :", 100000) for n in range(4, 11)]
data = json.loads(DATA.read_text(encoding="utf-8"))
assert not any(s["id"] == "bfa-insd-poverty-atlas-2019" for s in data["sources"])
observation_count_before = len(data["observations"])


def key(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.upper()) if c.isalnum())


def number(value):
    return float(value.replace(" ", "").replace(",", "."))


def source_observation(territory_id, indicator_id, value, period, origin, locator):
    data["observations"].append({
        "territory_id": territory_id, "indicator_id": indicator_id,
        "period": period, "value": value, "status": "observed",
        "source_id": "bfa-insd-poverty-atlas-2019",
        "value_origin": origin, "source_locator": locator,
    })


annex4 = [["", "BURKINA FASO", "20 505 155", "3 908 847", "39,3", "11,6", "8 065 679"]]
for line in content[starts[0]:starts[1]].splitlines():
    if re.match(r"^\s*\d{1,2} \d\d \d\d \d\d ", line):
        parts = re.split(r"\s{2,}", line.strip())
        assert len(parts) == 7, parts
        annex4.append(parts)
assert len(annex4) == 882

territories = data["territories"]
population = {
    row["territory_id"]: row["value"]
    for row in data["observations"]
    if row["indicator_id"] == "BFA_RGPH2019_POP_TOTAL"
}
match = {0: "BFA"}
region = province = None
unmatched = []
for index, (code, label, population_text, *_rest) in enumerate(annex4[1:], 1):
    c = code.split()
    level = ("adm1" if c[1:] == ["00", "00", "00"] else
             "adm2" if c[2:] == ["00", "00"] else
             "adm3" if c[3] == "00" else "lower")
    if level == "lower":
        continue
    parent = {"adm1": "BFA", "adm2": region, "adm3": province}[level]
    alias = {"BALE": "BALES", "NIAOGO": "NIAOGHO"}.get(key(label), key(label))
    if parent == "BFA:RGPH2019:ADM2:SANMATENGA" and alias == "BOUSSOUMA":
        alias = "BOUSSOUMACN"
    candidates = [t for t in territories if t["level"] == level and
                  t["parent_id"] == parent and key(t["name"]) == alias and
                  population.get(t["id"]) == int(population_text.replace(" ", ""))]
    if len(candidates) != 1:
        unmatched.append({"code": code, "label": label, "level": level,
                          "parent": parent, "population": population_text})
        continue
    territory = candidates[0]
    match[index] = territory["id"]
    if level == "adm1":
        region = territory["id"]
    elif level == "adm2":
        province = territory["id"]

assert len(match) == 408, (len(match), unmatched[:20])
assert len(unmatched) == 20 and all(" Arr " in x["label"] or x["label"] == "Bobo rural" for x in unmatched), unmatched
assert len(set(match.values())) == 408

with (ROOT / "evidence/POVERTY_ATLAS_CODE_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["INSD_RGPH2019_annex4_code", "INSD_label", "INSD_population", "AreaData_territory_id", "match_method"])
    for index, tid in match.items():
        row = annex4[index]
        writer.writerow([row[0] or "NATIONAL", row[1], row[2], tid, "2019 parent/name/population exact match"])

data["sources"].append({
    "id": "bfa-insd-poverty-atlas-2019",
    "name": "RGPH 2019 Volume 3: Mesure et cartographie de la pauvreté",
    "url": URL,
    "publisher": "Institut national de la statistique et de la démographie (INSD)",
    "reference_period": "2018 household survey with 2019 census frame; Annexes 5-9 use RGPH 2019",
    "status": "ready", "retrieved_at": "2026-09-24",
    "sha256": sha256(PDF.read_bytes()).hexdigest(),
    "raw_path": "raw/insd-rgph-2019/poverty_map.pdf",
    "note": "Annex 4 poverty estimates use small-area modelling, not direct census poverty counts. Annexes 5-9 report census-derived nonmonetary measures. Source terms prohibit raw redistribution without written permission; raw PDF is retained only in the local research project.",
})


def indicator(id_suffix, name, theme, unit, definition, annex, column, family="census"):
    iid = "BFA_INSD_" + id_suffix
    data["indicators"].append({
        "id": iid, "name": name, "theme": theme, "unit": unit,
        "definition": definition, "source_id": "bfa-insd-poverty-atlas-2019",
        "aggregation": "none", "series_family": family,
        "display_role": "primary" if family == "census" else "supplementary",
        "period_policy": "source_year", "upstream_table": f"Annex {annex}",
        "upstream_column": column,
        "measurement_method": ("INSD small-area model based on 2018 household survey and RGPH 2019 census"
                               if family == "survey" else "INSD RGPH 2019 published census indicator"),
    })
    return iid


poverty_specs = [
    (indicator("POVERTY_INCIDENCE_MODEL", "Estimated population below the monetary poverty line", "Livelihoods, poverty and economy", "%", "INSD small-area estimate of the population below the monetary poverty line, based on the 2018 household survey and 2019 census geography.", 4, "Incidence", "survey"), 4),
    (indicator("POVERTY_GAP_MODEL", "Estimated monetary poverty gap", "Livelihoods, poverty and economy", "%", "INSD small-area poverty gap (P1), based on the 2018 household survey and 2019 census geography; not a direct census count.", 4, "Profondeur", "survey"), 5),
    (indicator("POOR_PEOPLE_MODEL", "Estimated people below the monetary poverty line", "Livelihoods, poverty and economy", "people", "INSD modeled count of people below the poverty line using the 2018 survey and 2019 census population frame.", 4, "Nombre de pauvres", "survey"), 6),
    (indicator("HOUSEHOLDS_2019", "Households in the 2019 census geography", "Population and demography", "households", "Number of households published by INSD in the RGPH 2019 poverty atlas; not a modeled poverty measure.", 4, "Nombre de ménages"), 3),
]
for index, tid in match.items():
    row = annex4[index]
    for iid, col in poverty_specs:
        value = number(row[col])
        if iid.endswith("HOUSEHOLDS_2019") or iid.endswith("POOR_PEOPLE_MODEL"):
            value = int(value)
        source_observation(tid, iid, value, "2019" if iid.endswith("HOUSEHOLDS_2019") else "2018", "source_reported_model" if not iid.endswith("HOUSEHOLDS_2019") else "source_reported", f"Annex 4, geographic code {row[0] or 'national'}")


definitions = {
    5: [
        ("CHILD_EMPLOYMENT_7_14", "Children ages 7-14 in paid work", "Livelihoods, poverty and economy", "%", "Share of all children aged 7-14 in paid work according to the source definition."),
        ("YOUTH_EMPLOYMENT_15_24", "Employment among persons ages 15-24", "Livelihoods, poverty and economy", "%", "Employed persons as a share of all persons aged 15-24; not the employment-to-labor-force rate."),
        ("ADULT_EMPLOYMENT_25_64", "Employment among persons ages 25-64", "Livelihoods, poverty and economy", "%", "Employed persons as a share of all persons aged 25-64."),
        ("YOUTH_UNEMPLOYMENT_15_24", "Unemployment among active persons ages 15-24", "Livelihoods, poverty and economy", "%", "Unemployed persons as a share of the labor force aged 15-24."),
        ("ADULT_UNEMPLOYMENT_25_64", "Unemployment among active persons ages 25-64", "Livelihoods, poverty and economy", "%", "Unemployed persons as a share of the labor force aged 25-64."),
    ],
    6: [
        ("YOUTH_SELF_EMPLOYED_15_24", "Non-salaried employment among working youth", "Livelihoods, poverty and economy", "%", "Share of employed persons aged 15-24 in non-salaried work."),
        ("ADULT_SELF_EMPLOYED_25_64", "Non-salaried employment among working adults", "Livelihoods, poverty and economy", "%", "Share of employed persons aged 25-64 in non-salaried work."),
        ("POST_PRIMARY_NET_ATTENDANCE", "Net post-primary school attendance", "Education", "%", "Children aged 12-15 attending post-primary school as a share of all children aged 12-15."),
        ("SECONDARY_NET_ATTENDANCE", "Net secondary school attendance", "Education", "%", "Children aged 16-18 attending secondary school as a share of all children aged 16-18."),
        ("PRIMARY_GIRL_BOY_RATIO", "Girls-to-boys ratio in primary school", "Education", "girls per boy", "Number of girls in primary school divided by the number of boys; a ratio, not a percentage."),
    ],
    7: [
        ("POST_PRIMARY_GIRL_BOY_RATIO", "Girls-to-boys ratio in post-primary school", "Education", "girls per boy", "Number of girls in post-primary school divided by boys; a ratio, not a percentage."),
        ("SECONDARY_GIRL_BOY_RATIO", "Girls-to-boys ratio in secondary school", "Education", "girls per boy", "Number of girls in secondary school divided by boys; a ratio, not a percentage."),
        ("OUT_OF_SCHOOL_6_11", "Children ages 6-11 not attending school", "Education", "%", "Children aged 6-11 not attending school as a share of all children aged 6-11."),
        ("OUT_OF_SCHOOL_12_15", "Children ages 12-15 not attending school", "Education", "%", "Children aged 12-15 not attending school as a share of all children aged 12-15."),
        ("OUT_OF_SCHOOL_16_18", "Children ages 16-18 not attending school", "Education", "%", "Children aged 16-18 not attending school as a share of all children aged 16-18."),
    ],
    8: [
        ("YOUTH_NOT_SCHOOL_OR_WORK", "Persons ages 15-24 neither in school nor work", "Education", "%", "Persons aged 15-24 neither attending school nor working as a share of all persons aged 15-24."),
        ("LITERACY_15_64", "Literacy among persons ages 15-64", "Education", "%", "Persons aged 15-64 able to read and write in any language as a share of all persons aged 15-64."),
        ("DEMOGRAPHIC_DEPENDENCY", "Demographic dependency ratio", "Population and demography", "%", "Persons below 18 or over 64 divided by persons aged 18-64, multiplied by 100; source-defined ratio."),
        ("GIRLS_17_MARRIED", "Girls age 17 living in a marital union", "Health and nutrition", "%", "Girls who had reached age 17 and lived in a union as a share of all girls of that age; not the child-marriage rate across all ages."),
        ("BIRTH_REGISTRATION", "People registered in civil records", "Population and demography", "%", "Persons registered in civil records as a share of the resident population; not limited to recent births."),
    ],
    9: [
        ("HOUSEHOLD_SANITATION_ADEQUATE", "Households using source-defined adequate sanitation", "Housing, water, sanitation and energy", "%", "Households using flush toilets or private/shared simple or ventilated latrines divided by all households; not the SDG safely managed sanitation measure."),
        ("HOUSEHOLD_WATER_IMPROVED", "Households using source-defined potable-water sources", "Housing, water, sanitation and energy", "%", "Households using boreholes, public fountains, or specified taps divided by all households; not the SDG safely managed drinking-water measure."),
        ("HOUSEHOLD_ELECTRIC_LIGHT", "Households using electricity as main lighting source", "Housing, water, sanitation and energy", "%", "Households mainly using grid, solar, platform, generator or battery electricity for lighting divided by all households; not a measure of continuous electricity service."),
        ("HOUSEHOLD_CLEAN_COOKING", "Households using gas or electricity as main cooking fuel", "Housing, water, sanitation and energy", "%", "Households whose principal cooking fuel is gas or electricity divided by all households; not the full SDG clean cooking measure."),
        ("HOUSEHOLD_PHONE", "Households possessing a working telephone", "Access, infrastructure and environment", "%", "Households with at least one working mobile or fixed telephone divided by all households."),
    ],
}

annex_rows = {}
source_labels = [key(row[1]) for row in annex4]
for annex in range(5, 10):
    section = content[starts[annex - 4]:starts[annex - 3]]
    rows = []
    for line in section.splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 4 and re.fullmatch(r"\d+(?:,\d+)?|\.\.", parts[-1]) and parts[0] not in ("Label", "label"):
            rows.append(parts)
    sequence = SequenceMatcher(a=source_labels, b=[key(row[0]) for row in rows], autojunk=False)
    aligned = {a1 + i: b1 + i for op, a1, a2, b1, b2 in sequence.get_opcodes()
               if op == "equal" for i in range(a2-a1)}
    assert set(match).issubset(aligned), (annex, sorted(set(match)-set(aligned)))
    annex_rows[annex] = (rows, aligned)

incomplete = []
source_anomalies = []
for annex, specs in definitions.items():
    indicator_ids = [indicator(*spec, annex, spec[1]) for spec in specs]
    bounded_rates = {iid for iid, spec in zip(indicator_ids, specs)
                     if spec[3] == "%" and spec[0] != "DEMOGRAPHIC_DEPENDENCY"}
    rows, aligned = annex_rows[annex]
    for index, tid in match.items():
        values = rows[aligned[index]]
        if len(values) != 6 or any(not re.fullmatch(r"\d+(?:,\d+)?", value) for value in values[1:]):
            incomplete.append({"annex": annex, "code": annex4[index][0],
                               "name": annex4[index][1], "values": values[1:]})
            continue
        for iid, value in zip(indicator_ids, values[1:]):
            numeric_value = number(value)
            if iid in bounded_rates and not 0 <= numeric_value <= 100:
                source_anomalies.append({
                    "annex": annex, "code": annex4[index][0],
                    "name": annex4[index][1], "territory_id": tid,
                    "indicator_id": iid, "published_text": value,
                    "reason": "Source-published percentage is outside the possible 0-100 range; withheld without correction.",
                })
                continue
            source_observation(tid, iid, numeric_value, "2019", "source_reported", f"Annex {annex}, geographic code {annex4[index][0] or 'national'}")

for anomaly in source_anomalies:
    data["gaps"].append({
        "category": "source_value_anomaly", "status": "pending",
        "detail": (f"INSD RGPH 2019 poverty atlas Annex {anomaly['annex']} prints "
                   f"{anomaly['published_text']} for {anomaly['name']} / {anomaly['indicator_id']}; "
                   "this impossible percentage is withheld, not converted to zero or silently corrected."),
        "next_action": "Check an official erratum or corrected source table before adopting a replacement value.",
    })

data["collection"]["adapters"].append("insd-rgph2019-poverty-atlas-annexes-4-9")
data["collection"]["notes"].append("INSD Volume 3 Annexes 4-9 add 29 distinct indicators with geography matched to published Annex 4 codes and census population. The 2018-based monetary-poverty model is separate from 2019 census measures.")
data["collection"]["notes"].append("Twenty Ouagadougou/Bobo subdivision rows were not assigned to the two city-wide commune records; 2019 city aggregate values are left missing rather than averaged. Partial PDF rows for three communes were withheld for the affected annex.")
data["gaps"].append({"category": "poverty_atlas_city_aggregation", "status": "not_collected",
                     "detail": "Annexes 4-9 report 20 Ouagadougou/Bobo subdivision rows but not the two whole-city commune values in this dataset. No rate is inferred by averaging.",
                     "next_action": "Verify complete constituent denominators and official city totals before any aggregation."})

DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
evidence = {
    "source_url": URL, "source_sha256": sha256(PDF.read_bytes()).hexdigest(),
    "annex4_rows": len(annex4), "matched_geographies_including_national": len(match),
    "unmatched_subcity_rows": unmatched, "incomplete_extracted_rows": incomplete,
    "source_anomalies": source_anomalies,
    "indicator_count": len(poverty_specs)+sum(len(x) for x in definitions.values()),
    "observations_added": len(data["observations"]) - observation_count_before,
    "method": "Exact Annex 4 parent/order/name/population crosswalk; Annexes 5-9 aligned by published row sequence and normalized label. Incomplete numeric rows and impossible percentages are withheld, with raw source text retained in evidence.",
}
(ROOT / "evidence/POVERTY_ATLAS_IMPORT.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
print(json.dumps({k:v for k,v in evidence.items() if k not in ("unmatched_subcity_rows", "incomplete_extracted_rows")}, indent=2))

"""Import selected, directly reported PCBS 2017 updated-census tables.

The updated summary Table 2/29 includes post-enumeration estimates. The
separate detailed-report counted population and older summary are not merged.
Neither census locality codes nor source names certify a legal planning unit
or a current boundary polygon.
"""

import argparse
import json
import re
import runpy
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


fetch = runpy.run_path(str(Path(__file__).with_name("fetch-palestine-pcbs2017-sources.py")))
FILES, digest = fetch["FILES"], fetch["digest"]
SUMMARY = "pse-pcbs2017-updated-final-summary"
DETAIL = "pse-pcbs2017-detailed-counted-population"
GUIDE = "pse-pcbs2017-locality-classification"
OLDER = "pse-pcbs2017-older-summary"

# Key, source Table 2 label, source Table 29 label, region, female, male, total,
# households. Source anchors are kept separate from the extraction algorithm.
PARENTS = [
    ("Palestine", "Palestine", "Palestine", None, 2348052, 2433196, 4781248, 929221),
    ("West Bank", "West Bank", "West Bank", None, 1411664, 1470293, 2881957, 594511),
    ("Gaza Strip", "Gaza Strip", "Gaza Strip", None, 936388, 962903, 1899291, 334710),
    ("Jenin", "Jenin", "Jenin Gov.", "West Bank", 154635, 160231, 314866, 65495),
    ("Tubas & Northern Valleys", "Tubas & Northern Valleys", "Tubas & Northern Valleys", "West Bank", 29758, 31169, 60927, 12411),
    ("Tulkarm", "Tulkarm", "Tulkarm Gov.", "West Bank", 91743, 95017, 186760, 39360),
    ("Nablus", "Nablus", "Nablus Gov.", "West Bank", 191460, 196861, 388321, 82235),
    ("Qalqiliya", "Qalqiliya", "Qalqiliya Gov.", "West Bank", 54814, 57586, 112400, 22507),
    ("Salfit", "Salfit", "Salfit Gov.", "West Bank", 36967, 38477, 75444, 15677),
    ("Ramallah & Al-Bireh", "Ramallah & Al-Bireh", "Ramallah & Al-Bireh Gov.", "West Bank", 162664, 166197, 328861, 70188),
    ("Jericho & Al-Aghwar", "Jericho & Al Aghwar", "Jericho & Al-Aghwar Gov.", "West Bank", 24901, 25101, 50002, 10234),
    ("Jerusalem", "Jerusalem", "Jerusalem Gov.", "West Bank", 209844, 225909, 435753, 95234),
    ("Bethlehem", "Bethlehem", "Bethlehem Gov.", "West Bank", 106630, 110770, 217400, 45556),
    ("Hebron", "Hebron", "Hebron Gov.", "West Bank", 348248, 362975, 711223, 135614),
    ("North Gaza", "North Gaza", "North Gaza Gov.", "Gaza Strip", 181215, 187763, 368978, 64012),
    ("Gaza", "Gaza", "Gaza Gov.", "Gaza Strip", 320612, 331985, 652597, 113238),
    ("Dier Al-Balah", "Dier al Balah", "Dier Al-Balah Gov.", "Gaza Strip", 135860, 137340, 273200, 49202),
    ("Khan Yunis", "Khan Yunis", "Khan Yunis Gov.", "Gaza Strip", 182674, 187964, 370638, 66510),
    ("Rafah", "Rafah", "Rafah Gov.", "Gaza Strip", 116027, 117851, 233878, 41748),
]
PARENT_BY_KEY = {row[0]: row for row in PARENTS}
JERUSALEM_ZONES = {
    "Jerusalem (J1)**": (136361, 144802, 281163),
    "Jerusalem (J2)": (73483, 81107, 154590),
}
UNMATCHED_GUIDE_CODES = ["010287", "010325", "251355", "301835", "502855", "503211", "503305", "503325"]


def slug(label):
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]+", "-", label.upper())).strip("-")


def area_id(name, kind):
    if kind == "national":
        return "PSE"
    if kind == "region":
        return "PSE:PCBS17:REGION:" + slug(name)
    if kind == "governorate":
        return "PSE:PCBS17:GOV:" + slug(name)
    if kind == "zone":
        return "PSE:PCBS17:JERUSALEM:" + name
    return "PSE:PCBS17:LOCALITY:" + name


def extract(path, output):
    result = subprocess.run(["pdftotext", "-layout", str(path), str(output)],
                            capture_output=True, text=True, timeout=120, check=False)
    if result.returncode or not output.exists():
        raise RuntimeError("Poppler pdftotext failed: " + path.name + " " + result.stderr[:350])
    return output.read_text(encoding="utf-8")


def parse_table29(text):
    pages = [(i + 1, page) for i, page in enumerate(text.split("\f"))
             if "Table 29" in page[:1500] and "Population* in Palestine by Locality" in page[:1500]]
    if [page for page, _ in pages] != list(range(116, 131)):
        raise ValueError("Updated Table 29 page range changed")
    number = r"\d[\d,]*"
    three = re.compile(rf"(?P<f>{number})\s+(?P<m>{number})\s+(?P<t>{number})(?:\s+(?P<code>\d{{5,6}}))?(?!\d)")
    code = re.compile(r"(?<!\d)(\d{5,6})(?!\d)")
    parents, localities, unresolved = [], [], []
    governorate, region, pending_name, pending_code = None, None, "", ""
    for page, body in pages:
        for line in body.splitlines():
            left = re.split(r"[\u0600-\u06ff\u202a-\u202e]", line, maxsplit=1)[0].strip()
            # A closing bracket in the far-right Arabic column can precede
            # the first Arabic letter and survive the column split.
            left = re.sub(r"\s{3,}\)$", "", left).strip()
            if not left or left.startswith(("Table 29", "PCBS:", "Locality", "Females", "* ", "**", "results.", "Tuba.")):
                continue
            match = three.search(left)
            if match:
                inline = left[:match.start()].strip()
                continuation = inline.startswith("(") or pending_name.endswith(" Al") and inline.endswith(")")
                name = (pending_name + " " + inline).strip() if continuation and pending_name else inline or pending_name
                source_code = match.group("code") or pending_code
                female, male, total = [int(match.group(key).replace(",", "")) for key in ("f", "m", "t")]
                if female + male != total:
                    raise ValueError("Sex components differ at Table 29 page " + str(page) + ": " + name)
                if name in ("Palestine", "West Bank", "Gaza Strip", "Tubas & Northern Valleys", *JERUSALEM_ZONES) or name.endswith("Gov."):
                    if name in ("West Bank", "Gaza Strip"):
                        region = name
                    if name.endswith("Gov.") or name == "Tubas & Northern Valleys":
                        governorate = name[:-5].strip() if name.endswith("Gov.") else name
                    parents.append({"page": page, "name": name, "female": female, "male": male, "total": total})
                elif source_code:
                    localities.append({"page": page, "name": name, "female": female, "male": male,
                                       "total": total, "code": source_code.zfill(6), "governorate": governorate,
                                       "region": region})
                else:
                    unresolved.append((page, name, female, male, total))
                pending_name, pending_code = "", ""
            elif code.search(left) and not re.search(r"[A-Za-z]", left):
                pending_code = code.search(left).group(1)
            elif re.search(r"[A-Za-z]", left) and not left.startswith(("Note", "Population", "Governorate", "Both Sexes", "Page")):
                found = code.search(left)
                fragment = (left[:found.start()] + left[found.end():]).strip() if found else left
                # In the printed bilingual table a long English label can wrap
                # before or after its numeric row. A code can also be printed on
                # a name-only line. Keep all three pieces without the code.
                if pending_name and pending_name.count("(") > pending_name.count(")"):
                    pending_name += " " + fragment
                elif not found and localities and localities[-1]["name"].count("(") > localities[-1]["name"].count(")") and fragment.endswith(")"):
                    localities[-1]["name"] += " " + fragment
                else:
                    pending_name = fragment
                if found:
                    pending_code = found.group(1)
    if unresolved or len(parents) != 21 or len(localities) != 585 or len({r["code"] for r in localities}) != 585:
        raise ValueError(f"Incomplete Table 29: parents={len(parents)}, localities={len(localities)}, unresolved={unresolved}")
    parent_map = {row["name"]: row for row in parents}
    if len(parent_map) != 21:
        raise ValueError("Duplicate Table 29 parent")
    for key, _, source_name, _, female, male, total, _ in PARENTS:
        actual = parent_map.get(source_name)
        if not actual or (actual["female"], actual["male"], actual["total"]) != (female, male, total):
            raise ValueError("Updated Table 29 parent changed: " + key)
    for name, expected in JERUSALEM_ZONES.items():
        actual = parent_map.get(name)
        if not actual or (actual["female"], actual["male"], actual["total"]) != expected:
            raise ValueError("Jerusalem reporting zone changed: " + name)
    for key, _, _, region, female, male, total, _ in PARENTS[3:]:
        children = [x for x in localities if x["governorate"] == key]
        expected = JERUSALEM_ZONES["Jerusalem (J2)"] if key == "Jerusalem" else (female, male, total)
        if tuple(sum(x[field] for x in children) for field in ("female", "male", "total")) != expected:
            raise ValueError("Locality cover incomplete for " + key)
    if tuple(sum(parent_map[name][field] for name in JERUSALEM_ZONES) for field in ("female", "male", "total")) != (209844, 225909, 435753):
        raise ValueError("Jerusalem J1/J2 cover changed")
    for region in ("West Bank", "Gaza Strip"):
        members = [x for x in PARENTS[3:] if x[3] == region]
        for position, field in ((4, "female"), (5, "male"), (6, "total")):
            if sum(x[position] for x in members) != parent_map[region][field]:
                raise ValueError("Governorates do not cover " + region)
    if sum(parent_map[name]["total"] for name in ("West Bank", "Gaza Strip")) != 4781248:
        raise ValueError("Regions do not cover national population")
    return parents, localities


def main(project):
    raw = project / "raw" / "official"
    evidence = project / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    for name, spec in FILES.items():
        if not (raw / name).exists() or digest(raw / name) != spec["sha256"]:
            raise ValueError("Changed or missing official PCBS original: " + name)
    texts = {name: extract(raw / name, evidence / (name + ".txt")) for name in FILES}
    summary = texts["PCBS_2017_Final_Summary_book2383.pdf"]
    detail = texts["PCBS_2017_Detailed_Population_book2425.pdf"]
    guide = texts["PCBS_2017_Locality_Classification.pdf"]
    older = texts["PCBS_2017_Older_Summary_book2369.pdf"]
    if "4,705,855" not in detail or "4,780,978" not in older or "4,781,248" not in summary:
        raise ValueError("PCBS counted/older/updated editions are not distinguishable")
    table2 = summary.split("\f")[70]
    if "Table 2: Population in Palestine by Governorate and Sex, 2017" not in table2:
        raise ValueError("Updated Table 2 page changed")
    for _, label, _, _, female, male, total, households in PARENTS:
        if not any(line.lstrip().startswith(label + " ") and all(f"{value:,}" in line for value in (female, male, total, households))
                   for line in table2.splitlines()):
            raise ValueError("Updated Table 2 source anchor changed: " + label)
    parents, localities = parse_table29(summary)
    guide_missing = sorted(x["code"] for x in localities if x["code"] not in guide)
    if guide_missing != UNMATCHED_GUIDE_CODES:
        raise ValueError("Classification crosswalk changed: " + repr(guide_missing))
    path = project / "data" / "dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "PSE":
        raise ValueError("Expected PSE project")
    source_ids = {SUMMARY, DETAIL, GUIDE, OLDER, "pse-pcbs-midyear-projection-catalog",
                  "pse-molg-law-catalog", "pse-molg-planning-guides", "pse-molg-icud-projects",
                  "pse-molg-budget-portal", "pse-molg-geomolg-2017-boundary-note"}
    indicator_ids = {"PSE_PCBS17_ADJ_POP", "PSE_PCBS17_ADJ_WOMEN", "PSE_PCBS17_ADJ_MEN", "PSE_PCBS17_HOUSEHOLDS"}
    data["sources"] = [row for row in data["sources"] if row["id"] not in source_ids]
    data["indicators"] = [row for row in data["indicators"] if row["id"] not in indicator_ids]
    data["observations"] = [row for row in data["observations"] if row["indicator_id"] not in indicator_ids]
    data["territories"] = [row for row in data["territories"] if row["id"] == "PSE"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["country"].update({
        "name": "State of Palestine", "requested_name": "PSE (State of Palestine)",
        "geography_note": "PCBS 2017 updated census summary reports the State of Palestine as West Bank including Jerusalem J1 and J2 plus Gaza Strip. Table 29 supplies 585 coded locality rows; Jerusalem J1 is aggregate-only, while 29 locality rows cover J2. Census counts include post-enumeration estimates and are historical, not present population. The World Bank labels its separate international PSE series West Bank and Gaza. No 2021 geoBoundaries region shape is joined to official 2017 source rows; current legal/administrative boundaries and planning units require verification."
    })
    data["territories"][0]["name"] = "State of Palestine"
    data["territories"][0]["source_id"] = SUMMARY
    data["territories"][0]["code_system"] = "PCBS 2017 updated census reporting scope; no national boundary certification"
    data["territories"][0]["reconciliation_status"] = "PCBS national 2017 census scope; WDI PSE is a separate international series"
    for region in ("West Bank", "Gaza Strip"):
        data["territories"].append({"id": area_id(region, "region"), "name": region, "level": "pcbs17_region",
            "type": "PCBS census region", "parent_id": "PSE", "official_code": None,
            "code_system": "PCBS 2017 source row; region code not adopted", "boundary_version": None,
            "source_id": SUMMARY, "reconciliation_status": "direct census reporting region; 2021 provider reference polygon not joined"})
    for key, _, _, region, _, _, _, _ in PARENTS[3:]:
        data["territories"].append({"id": area_id(key, "governorate"), "name": key,
            "level": "pcbs17_governorate", "type": "PCBS census governorate",
            "parent_id": area_id(region, "region"), "official_code": None,
            "code_system": "PCBS 2017 governorate source row; governorate code not adopted", "boundary_version": None,
            "source_id": SUMMARY, "reconciliation_status": "2017 updated census row; current official polygon and code unverified"})
    for zone, (female, male, total) in JERUSALEM_ZONES.items():
        short = "J1" if "J1" in zone else "J2"
        data["territories"].append({"id": area_id(short, "zone"), "name": "Jerusalem " + short,
            "level": "pcbs17_jerusalem_zone", "type": "PCBS census reporting zone",
            "parent_id": area_id("Jerusalem", "governorate"), "official_code": None,
            "code_system": "PCBS Table 29 J1/J2 reporting zone; not a legal locality code", "boundary_version": None,
            "source_id": SUMMARY,
            "reconciliation_status": "J1 aggregate has no individually coded locality values in Table 29" if short == "J1" else "J2 has 29 coded source localities; no verified polygon"})
    for row in localities:
        guide_match = row["code"] in guide
        data["territories"].append({"id": area_id(row["code"], "locality"), "name": row["name"],
            "level": "pcbs17_locality", "type": "PCBS census locality",
            "parent_id": area_id("J2", "zone") if row["governorate"] == "Jerusalem" else area_id(row["governorate"], "governorate"),
            "official_code": row["code"], "code_system": "PCBS PHC 2017 updated Table 29 locality code",
            "boundary_version": None, "source_id": SUMMARY,
            "reconciliation_status": "Code also located in May 2017 PCBS locality classification; no polygon joined" if guide_match else
                "Code printed in updated Table 29 but not found in May 2017 classification; code-edition crosswalk held; no polygon joined"})
    indicator_specs = [
        ("PSE_PCBS17_ADJ_POP", "2017 census final population incl. post-enumeration estimate", "Population", "people", "Both Sexes",
         "PCBS 2017 updated final census count at midnight 30 November–1 December 2017, including the post-enumeration estimate. Historical source scope; not a current population projection."),
        ("PSE_PCBS17_ADJ_WOMEN", "2017 census final female population incl. post-enumeration estimate", "Demography", "people", "Females",
         "PCBS 2017 updated final census female population, including the post-enumeration estimate; historical source scope."),
        ("PSE_PCBS17_ADJ_MEN", "2017 census final male population incl. post-enumeration estimate", "Demography", "people", "Males",
         "PCBS 2017 updated final census male population, including the post-enumeration estimate; historical source scope."),
        ("PSE_PCBS17_HOUSEHOLDS", "2017 census published households", "Households", "households", "Households",
         "Household number directly published in PCBS updated final census summary Table 2 for national, region and governorate rows only; no locality household value is inferred."),
    ]
    for ident, title, theme, unit, _, definition in indicator_specs:
        data["indicators"].append({"id": ident, "name": title, "theme": theme, "unit": unit,
            "definition": definition, "population": "PCBS PHC 2017 reported census scope",
            "source_id": SUMMARY, "aggregation": "none", "measurement_method": "source_reported", "display_decimals": 0})
    def observe(aid, values, locator):
        for ident, _, _, _, column, _ in indicator_specs:
            if column not in values:
                continue
            data["observations"].append({"territory_id": aid, "indicator_id": ident, "period": "2017",
                "value": values[column], "status": "observed", "measurement_method": "source_reported",
                "source_id": SUMMARY, "source_locator": locator + ", column " + column})
    for key, _, _, region, female, male, total, households in PARENTS:
        kind = "national" if key == "Palestine" else "region" if region is None else "governorate"
        ident = area_id(key, kind)
        observe(ident, {"Both Sexes": total, "Females": female, "Males": male, "Households": households},
                f"PCBS updated 2017 Final Summary Table 2, printed/PDF page 71, {key}")
    for name, (female, male, total) in JERUSALEM_ZONES.items():
        short = "J1" if "J1" in name else "J2"
        parent = next(row for row in parents if row["name"] == name)
        observe(area_id(short, "zone"), {"Both Sexes": total, "Females": female, "Males": male},
                f"PCBS updated 2017 Final Summary Table 29, printed/PDF page {parent['page']}, {name}; aggregate zone, no locality code")
    for row in localities:
        observe(area_id(row["code"], "locality"), {"Both Sexes": row["total"], "Females": row["female"], "Males": row["male"]},
                f"PCBS updated 2017 Final Summary Table 29, printed/PDF page {row['page']}, locality code {row['code']}, {row['name']}")
    comparisons = [{"parent_id": "PSE", "member_ids": [area_id(x, "region") for x in ("West Bank", "Gaza Strip")],
        "label": "PCBS 2017 census reporting regions", "source_ids": [SUMMARY],
        "membership_note": "Two complete, non-overlapping source regions; direct final census values including post-enumeration estimates. Not current population."}]
    for region in ("West Bank", "Gaza Strip"):
        comparisons.append({"parent_id": area_id(region, "region"),
            "member_ids": [area_id(row[0], "governorate") for row in PARENTS[3:] if row[3] == region],
            "label": f"PCBS 2017 governorates in {region}", "source_ids": [SUMMARY],
            "membership_note": "Direct 2017 updated-census governorate rows, complete within this reporting region; no 2021 provider polygon is substituted."})
    for key, _, _, _, _, _, _, _ in PARENTS[3:]:
        member_ids = [area_id(x, "zone") for x in ("J1", "J2")] if key == "Jerusalem" else \
                     [area_id(x["code"], "locality") for x in localities if x["governorate"] == key]
        comparisons.append({"parent_id": area_id(key, "governorate"), "member_ids": member_ids,
            "label": "PCBS 2017 Jerusalem J1/J2 reporting zones" if key == "Jerusalem" else f"PCBS 2017 coded localities in {key}",
            "source_ids": [SUMMARY],
            "membership_note": "Jerusalem J1 is aggregate-only; J2 is its separate non-overlapping reporting zone." if key == "Jerusalem" else
                "All coded Table 29 localities sum exactly to the directly published governorate line; locality is a census type, not a verified legal planning unit."})
    comparisons.append({"parent_id": area_id("J2", "zone"),
        "member_ids": [area_id(x["code"], "locality") for x in localities if x["governorate"] == "Jerusalem"],
        "label": "PCBS 2017 coded Jerusalem J2 localities", "source_ids": [SUMMARY],
        "membership_note": "The 29 coded locality rows fully cover Jerusalem J2 only. J1 is a separate aggregate with no individual locality counts in Table 29."})
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = sorted([area_id(x["code"], "locality") for x in localities] + [area_id("J1", "zone")])
    data["analysis"]["default_indicator_id"] = "PSE_PCBS17_ADJ_POP"
    data["analysis"]["latest_values_only"] = True
    data["analysis"].pop("population_context", None)
    for name, ident, title, period, geography, note in [
        ("PCBS_2017_Final_Summary_book2383.pdf", SUMMARY, "PCBS 2017 final census summary, updated version", "2017-12-01", "national, 2 regions, 16 governorates, 2 Jerusalem zones, 585 localities", "Only Table 2/29 selected fields are adopted. Other 27 summary tables unassessed. Updated total 4,781,248 includes 75,393 post-enumeration estimate."),
        ("PCBS_2017_Detailed_Population_book2425.pdf", DETAIL, "PCBS 2017 final detailed population report", "2017-12-01", "national to governorate; other tables unassessed", "Table 1 counted population 4,705,855 is distinct from updated adjusted summary. Its 44 tables are not adopted; most fields unassessed."),
        ("PCBS_2017_Locality_Classification.pdf", GUIDE, "PCBS Palestinian localities classification 2017", "May 2017", "locality code catalogue", "577 of 585 updated Table 29 locality codes were found; eight updated-report codes were not located in this earlier guide. No polygon or local-government type is inferred."),
        ("PCBS_2017_Older_Summary_book2369.pdf", OLDER, "PCBS 2017 older final summary edition", "earlier 2018 edition", "national to locality; held edition", "Older published national count 4,780,978 differs from updated book2383 count 4,781,248 by 270; no older field is adopted or mixed."),
    ]:
        spec = FILES[name]
        data["sources"].append({"id": ident, "name": title, "url": spec["url"],
            "publisher": "Palestinian Central Bureau of Statistics", "reference_period": period,
            "geographic_level": geography, "status": "partial", "license": "terms_review_required",
            "raw_path": "raw/official/" + name, "sha256": spec["sha256"],
            "retrieved_at": datetime.fromtimestamp((raw / name).stat().st_mtime, timezone.utc).isoformat(), "note": note})
    for ident, name, url, publisher, period, geography, note in [
        ("pse-pcbs-midyear-projection-catalog", "PCBS 1997–2026 governorate midyear population projection table", "https://microdata.pcbs.gov.ps/statisticsIndicatorsTables.aspx?lang=en&table_id=676", "Palestinian Central Bureau of Statistics", "table published 2021; includes projected 2026", "national/region/governorate", "Projection location only. A pre-2023 forecast is not observed 2026 population and is not merged with the 2017 census."),
        ("pse-molg-law-catalog", "MoLG local authorities and planning law catalogue", "https://www.molg.pna.ps/ar/categories/74/", "Palestinian Ministry of Local Government", "catalog checked 2026-09-26", "national law catalogue", "1997 local-authorities law and 1966 town/village planning law amendments are listed; consolidated legal text, current applicability and planning duties not yet audited."),
        ("pse-molg-planning-guides", "MoLG planning and local-development manuals catalogue", "https://molg.pna.ps/ar/categories/2080/%D8%A7%D9%84%D8%A7%D8%AF%D9%84%D8%A9/3", "Palestinian Ministry of Local Government", "catalog checked 2026-09-26", "local government planning guides", "Catalogue lead only; edition, lawful planning unit, form and binding status unassessed."),
        ("pse-molg-icud-projects", "MoLG Integrated Cities and Urban Development project catalogue", "https://www.molg.pna.ps/AR/categories/2119/ICUD", "Palestinian Ministry of Local Government", "catalog checked 2026-09-26", "selected cities/project documents", "Location only. No selected-area approved plan, decision, budget or performance record is adopted."),
        ("pse-molg-budget-portal", "MoLG local government budget submission portal", "https://budgets.molg.pna.ps/", "Palestinian Ministry of Local Government", "portal checked 2026-09-26", "local government budget process", "Portal announces 2027 budget intake but supplies no verified selected-area public budget/approval; login and publication scope unassessed."),
        ("pse-molg-geomolg-2017-boundary-note", "PCBS/MoLG 2017 census boundary revision note", "https://www.pcbs.gov.ps/Portals/_Rainbow/Documents/Land-use-table%201E-2019.html", "Palestinian Central Bureau of Statistics; Ministry of Local Government", "2017 census geography; page checked 2026-09-26", "governorate boundary revision note; no shapes", "Official note describes 2017 locality-based governorate boundary revision. No GeoMOLG polygon files or official spatial codes were acquired."),
    ]:
        data["sources"].append({"id": ident, "name": name, "url": url, "publisher": publisher,
            "reference_period": period, "geographic_level": geography, "status": "not_collected",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "license": "terms_review_required", "note": note})
    data["gaps"] = [row for row in data["gaps"] if row["category"] not in ("subnational_statistics", "boundary_reconciliation", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Updated 2017 PCBS census Table 2/29 selected fields supply direct national, two-region, 16-governorate, two Jerusalem-zone and 585 coded-locality observations. Includes post-enumeration estimates; not present population. Other 27 summary and 44 detailed tables, older edition and 2021-published 2026 projections remain unadopted.",
         "next_action": "Audit every source table/number column and nonpopulation themes, denominators, source edition, present availability and 2023-onward comparability without using pre-conflict projections as observations."},
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "585 locality codes are printed in updated Table 29; 577 also occur in the May 2017 code guide, eight do not. Governorate codes, locality-government typing and 2017 official polygons are not reconciled. Two 2021 provider region shapes are unjoined.",
         "next_action": "Obtain official GeoMOLG 2017/current code and polygon editions, resolve eight code-guide gaps and administrative histories, especially Jerusalem J1/J2."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "MoLG law/manual/project and budget portal locations identified. No current legal plan-making unit, applicable format, selected-area plan/decision, public budget, implementation or evaluation body verified.",
         "next_action": "Acquire current consolidated law, manuals, actual plan/decision and fiscal/performance evidence for contrasting municipalities/camps/Jerusalem and Gaza; separate institutional status from document acquisition."},
    ]
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] + ["palestine-pcbs2017-updated-table2-table29-partial-v1"]))
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_tables = sorted(set(map(int, re.findall(r"Table\s+(\d+)\s*:", summary))))
    detailed_tables = sorted(set(map(int, re.findall(r"Table\s+(\d+)\s*:", detail))))
    audit = {"source_hashes": {name: spec["sha256"] for name, spec in FILES.items()},
        "summary_tables": [{"table": i, "decision": "selected_fields_adopted" if i in (2, 29) else "unassessed_not_adopted"} for i in summary_tables],
        "detailed_tables": [{"table": i, "decision": "counted_population_scope_inspected_not_adopted" if i == 1 else "unassessed_not_adopted"} for i in detailed_tables],
        "updated_national": 4781248, "older_national": 4780978, "counted_national": 4705855,
        "post_enumeration_estimate": 75393, "parent_rows": parents,
        "coded_locality_count": len(localities), "guide_matched_count": len(localities) - len(guide_missing),
        "guide_unmatched_codes": guide_missing,
        "governorate_locality_counts": dict(Counter(row["governorate"] for row in localities)),
        "jerusalem_j1": {"population": 281163, "decision": "aggregate_only_no_locality_population_rows"},
        "jerusalem_j2": {"population": 154590, "coded_localities": 29},
        "unjoined_reference_shapes": 2,
        "next_review": "Only Table 2/29 selected numeric fields are semantically audited; the inventory does not close other source tables, local legal types or current data."}
    (evidence / "PSE_PCBS2017_FIELD_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": len(data["territories"]), "coded_localities": len(localities),
        "guide_matched": len(localities) - len(guide_missing), "guide_unmatched": guide_missing,
        "indicators": 4, "direct_observations": len(PARENTS)*4 + 2*3 + len(localities)*3,
        "summary_tables": len(summary_tables), "detailed_tables": len(detailed_tables)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

"""Import audited Maldives CPH 2022 reporting units and selected direct counts.

The 2022 statistical atoll partition is not the 2026 atoll-council system.
No geography is joined without a dated official polygon and code crosswalk.
"""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/maldives-cph2022-source-manifest.json"
PLANNING = ROOT / "config/maldives-planning-source-manifest.json"
PREFIX = "MDV_CPH2022_"
BOUNDARY = "MBS CPH 2022 census reporting partition; official polygons and 2026 council crosswalk unverified"
PERIOD = "2022"
POP = ("population", "female", "male", "maldivian_population", "maldivian_female",
       "maldivian_male", "foreign_population", "foreign_female", "foreign_male")
WATER = ("safe_source_reported", "unsafe_source_reported", "rain_treated", "rain_untreated",
         "desalinated", "bottled")
EMP = ("population_15_plus", "labour_force", "employed", "unemployed", "outside_labour_force")
LIT = ("maldivian_population_10_plus", "maldivian_literate_mother_tongue")
NAMES = {
    "population": "Resident population, total", "female": "Resident population, female",
    "male": "Resident population, male", "maldivian_population": "Resident Maldivian population, total",
    "maldivian_female": "Resident Maldivian population, female",
    "maldivian_male": "Resident Maldivian population, male",
    "foreign_population": "Resident foreign population, total",
    "foreign_female": "Resident foreign population, female",
    "foreign_male": "Resident foreign population, male",
    "households": "Households, census count",
    "safe_source_reported": "Households using census-reported safe water source",
    "unsafe_source_reported": "Households using census-reported unsafe water source",
    "rain_treated": "Households using treated rainwater",
    "rain_untreated": "Households using untreated rainwater",
    "desalinated": "Households using desalinated water",
    "bottled": "Households using bottled water",
    "population_15_plus": "Resident population aged 15 and over, EC3 scope",
    "labour_force": "Labour force aged 15 and over",
    "employed": "Employed population aged 15 and over",
    "unemployed": "Unemployed population aged 15 and over, seeking and available",
    "outside_labour_force": "Population aged 15 and over outside the labour force",
    "maldivian_population_10_plus": "Resident Maldivian population aged 10 and over, ED16 scope",
    "maldivian_literate_mother_tongue": "Literate Maldivian population aged 10 and over, mother tongue",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def iid(field):
    return PREFIX + field.upper()


def atoll_id(code):
    return f"MDV:CPH2022:A:{code}"


def island_id(row):
    return f"{atoll_id(row['code'])}:I{row['row']:03d}"


def obs(data, territory_id, field, value, source, locator, scope, method):
    if value is None:
        return
    require(isinstance(value, int) and value >= 0, f"Invalid observed count {field} {territory_id}")
    data["observations"].append({
        "territory_id": territory_id, "indicator_id": iid(field), "period": PERIOD,
        "value": value, "status": "observed", "source_id": source,
        "measurement_method": method, "provenance": "source_reported",
        "source_locator": locator, "population_scope": scope,
        "boundary_version": BOUNDARY,
    })


def add_row(data, territory_id, row, fields, source, scope, method):
    for field in fields:
        obs(data, territory_id, field, row["fields"][field], source,
            f"Table {source.rsplit('-', 1)[-1].upper()} row {row['row']}, {row['name']}; "
            f"selected {field} count column", scope, method)


def main(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    planning_manifest = json.loads(PLANNING.read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/MDV_CPH2022_SELECTED_AUDIT.json").read_text(encoding="utf-8"))
    require(audit["manifest_sha256"] == digest(MANIFEST.read_bytes()), "Rerun workbook inventory and audit")
    require(len(manifest["source_files"]) == 58 and len(audit["population"]["islands"]) == 186,
            "Source scope changed")
    for entry in [*manifest["source_files"], *planning_manifest["sources"]]:
        body = (project / entry["raw_path"]).read_bytes()
        require(len(body) == entry["bytes"] and digest(body) == entry["sha256"],
                f"Source original changed: {entry['id']}")

    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "MDV", "Expected Maldives candidate")
    data["territories"] = [x for x in data["territories"] if x["id"] == "MDV"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "2022 census country scope; dated official subnational polygons unacquired"
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith(("mdv-cph2022-", "mdv-presidency-", "mdv-fonadhoo-"))]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("mdv-fonadhoo-")]
    data["country"]["geography_note"] = (
        "MBS 2022 Census of Population and Housing reporting areas include Maale, 20 atoll/city "
        "statistical rows, 186 administrative-island rows, nine Maale subareas and one non-administrative-island "
        "aggregate. The 2026 abolition of atoll councils means these 2022 rows are not current council jurisdictions. "
        "Official 2022 island codes, dated matching polygons and 2026 council crosswalk remain unverified. "
        "2022 direct census counts and World Bank annual estimates remain separate indicators.")

    p = audit["population"]
    h = audit["households"]
    w = audit["water"]
    e = audit["employment"]
    l = audit["literacy"]
    aid_to_islands = {}
    island_by_key = {}
    atoll_by_code = {row["code"]: row for row in p["atolls"]}
    for code, row in atoll_by_code.items():
        data["territories"].append({"id": atoll_id(code), "name": f"{code} — {row['name']}",
            "level": "census_atoll_reporting_2022", "type": "census_statistical_atoll_or_city_2022",
            "parent_id": "MDV", "official_code": code,
            "code_system": "MBS CPH 2022 atoll abbreviation, not 2026 council code",
            "boundary_version": BOUNDARY, "source_id": "mdv-cph2022-p4",
            "reconciliation_status": "2022 census reporting row; current council jurisdiction and polygon unverified"})
        aid_to_islands[code] = []
    maale = "MDV:CPH2022:MAALE"
    nonadmin = "MDV:CPH2022:NONADMIN"
    data["territories"].append({"id": maale, "name": "Maale, 2022 census scope",
        "level": "census_city_2022", "type": "census_city_reporting_2022", "parent_id": "MDV",
        "official_code": None, "code_system": "MBS CPH 2022 Maale reporting row; no current council code matched",
        "boundary_version": BOUNDARY, "source_id": "mdv-cph2022-p5",
        "reconciliation_status": "2022 census reporting scope; current city jurisdiction unverified"})
    maale_parts = []
    for row in p["maale_parts"]:
        tid = f"{maale}:P{row['row']:02d}"
        maale_parts.append(tid)
        data["territories"].append({"id": tid, "name": row["name"],
            "level": "census_city_subarea_2022", "type": "census_city_subarea_or_harbour_2022",
            "parent_id": maale, "official_code": None,
            "code_system": "Internal P5 row number; not an official geographic code",
            "boundary_version": BOUNDARY, "source_id": "mdv-cph2022-p5",
            "reconciliation_status": "Census reporting subarea, not proven council ward"})
    for row in p["islands"]:
        tid = island_id(row)
        key = (row["code"], row["name"])
        island_by_key[key] = tid
        aid_to_islands[row["code"]].append(tid)
        data["territories"].append({"id": tid, "name": row["name"],
            "level": "census_administrative_island_2022", "type": "census_administrative_island_2022",
            "parent_id": atoll_id(row["code"]), "official_code": None,
            "code_system": "Internal P5 row number with MBS atoll abbreviation; official island code unverified",
            "boundary_version": BOUNDARY, "source_id": "mdv-cph2022-p5",
            "reconciliation_status": "2022 census island row; current island-council extent/polygon unverified"})
    data["territories"].append({"id": nonadmin, "name": "Non-administrative islands, 2022 aggregate",
        "level": "census_nonadministrative_aggregate_2022", "type": "census_nonadministrative_aggregate",
        "parent_id": "MDV", "official_code": None,
        "code_system": "MBS CPH 2022 non-administrative-island aggregate; not a legal planning unit",
        "boundary_version": BOUNDARY, "source_id": "mdv-cph2022-p5",
        "reconciliation_status": "Census aggregate without individual island geography"})
    require(len(data["territories"]) == 218 and len(island_by_key) == 186, "Unexpected territory count")

    pop_scope = "CPH 2022 usual resident population, Maldivian and foreign residents; visitors excluded"
    household_scope = "CPH 2022 households; MBS H2/H7 source categories and scope"
    emp_scope = "CPH 2022 resident population aged 15 and over; EC3 labour-force definitions"
    lit_scope = "CPH 2022 resident Maldivian population aged 10 and over; ED16 mother-tongue literacy"
    pop_method = "MBS CPH 2022 direct census count by census place of enumeration"
    for tid, row in (("MDV", p["country"]), (maale, p["maale"]), (nonadmin, p["nonadmin"])):
        add_row(data, tid, row, POP, "mdv-cph2022-p5", pop_scope, pop_method)
    for row, tid in zip(p["maale_parts"], maale_parts, strict=True):
        add_row(data, tid, row, POP, "mdv-cph2022-p5", pop_scope, pop_method)
    for code, row in atoll_by_code.items():
        add_row(data, atoll_id(code), row, POP, "mdv-cph2022-p4", pop_scope, pop_method)
    for row in p["islands"]:
        add_row(data, island_by_key[(row["code"], row["name"])], row, POP,
                "mdv-cph2022-p5", pop_scope, pop_method)

    for tid, row in (("MDV", h["country"]), (maale, h["maale"]), (nonadmin, h["nonadmin"])):
        add_row(data, tid, row, ("households",), "mdv-cph2022-h2", household_scope,
                "MBS CPH 2022 direct household count")
    for row, tid in zip(h["maale_parts"], maale_parts, strict=True):
        add_row(data, tid, row, ("households",), "mdv-cph2022-h2", household_scope,
                "MBS CPH 2022 direct household count")
    for row in h["islands"]:
        add_row(data, island_by_key[(row["code"], row["name"])], row, ("households",),
                "mdv-cph2022-h2", household_scope, "MBS CPH 2022 direct household count")
    for row in w["atolls"]:
        add_row(data, atoll_id(row["code"]), row, ("households",), "mdv-cph2022-h7",
                household_scope, "MBS CPH 2022 direct household count")
    for tid, row in (("MDV", w["country"]), (maale, w["maale"]), (nonadmin, w["nonadmin"])):
        add_row(data, tid, row, WATER, "mdv-cph2022-h7", household_scope,
                "MBS CPH 2022 H7 water-source household category count, source wording retained")
    for row in w["atolls"]:
        add_row(data, atoll_id(row["code"]), row, WATER, "mdv-cph2022-h7",
                household_scope, "MBS CPH 2022 H7 water-source household category count, source wording retained")
    for key, fields, scope, source, segment in (("employment", EMP, emp_scope, "mdv-cph2022-ec3", e),
                                                ("literacy", LIT, lit_scope, "mdv-cph2022-ed16", l)):
        for tid, row in (("MDV", segment["country"]), (maale, segment["maale"]),
                         (nonadmin, segment["nonadmin"])):
            add_row(data, tid, row, fields, source, scope,
                    f"MBS CPH 2022 {key} direct source count")
        for row in segment["islands"]:
            add_row(data, island_by_key[(row["code"], row["name"])], row, fields, source,
                    scope, f"MBS CPH 2022 {key} direct source count; exact P5 island name matched")

    field_to_source = {**dict.fromkeys(POP, "mdv-cph2022-p5"), "households": "mdv-cph2022-h2",
                       **dict.fromkeys(WATER, "mdv-cph2022-h7"),
                       **dict.fromkeys(EMP, "mdv-cph2022-ec3"),
                       **dict.fromkeys(LIT, "mdv-cph2022-ed16")}
    for field, source in field_to_source.items():
        is_water = field in WATER
        is_emp = field in EMP
        is_lit = field in LIT
        data["indicators"].append({"id": iid(field), "name": NAMES[field],
            "theme": "Water" if is_water else "Employment" if is_emp else "Education" if is_lit
                     else "Households" if field == "households" else "Population",
            "unit": "households" if is_water or field == "households" else "people",
            "definition": ("MBS H7 original safe/unsafe and water-source category. Not a WHO/JMP service tier."
                           if is_water else "MBS CPH 2022 direct count. " +
                           (lit_scope if is_lit else emp_scope if is_emp else household_scope
                            if field == "households" else pop_scope)),
            "population": lit_scope if is_lit else emp_scope if is_emp else household_scope
                          if is_water or field == "households" else pop_scope,
            "source_id": source, "aggregation": "none", "display_decimals": 0,
            "measurement_method": ("MBS CPH 2022 H7 water-source household category count, source wording retained"
                                   if is_water else "MBS CPH 2022 direct household count"
                                   if field == "households" else
                                   "MBS CPH 2022 employment direct source count" if is_emp else
                                   "MBS CPH 2022 literacy direct source count" if is_lit else pop_method)})

    now = datetime.now(timezone.utc).isoformat()
    selected_codes = set(audit["selected_source_codes"])
    for item in manifest["source_files"]:
        selected = item["code"].upper() in selected_codes
        data["sources"].append({"id": item["id"], "name": item["title"],
            "url": item["url"], "publisher": "Maldives Bureau of Statistics",
            "reference_period": "2022 CPH", "geographic_level": "national, 2022 atoll/city reporting scope or island, depending on table",
            "status": "ready" if selected else "partial", "raw_path": item["raw_path"],
            "sha256": item["sha256"], "retrieved_at": now,
            "license": "Official public workbook; raw redistribution terms unverified",
            "note": "Selected original count columns audited and adopted; other columns held for semantic audit."
                    if selected else "Original acquired and numeric columns inventoried; no values adopted pending semantic audit."})
    for item in planning_manifest["sources"]:
        data["sources"].append({"id": item["id"], "name": item["title"],
            "url": item["url"], "publisher": item["publisher"],
            "reference_period": item.get("period", "2026 legal context or publication page"),
            "geographic_level": "L. Fonadhoo" if item["id"].startswith("mdv-fonadhoo-") else "national",
            "status": "partial", "raw_path": item["raw_path"], "sha256": item["sha256"],
            "retrieved_at": now, "license": "Official public document; raw redistribution terms unverified",
            "note": item.get("content_note", "Official page body acquired; legal detail requires review.")})
    fonadhoo = next(tid for (code, name), tid in island_by_key.items()
                    if code == "L" and name == "Fonadhoo")
    plan = planning_manifest["sources"][0]
    data["documents"].append({"id": plan["id"], "territory_id": fonadhoo,
        "category": "plan", "kind": "council_development_plan", "title": plan["title"],
        "url": plan["url"], "source_id": plan["id"], "period": plan["period"],
        "availability": "body_acquired", "official_status": "unverified",
        "note": "Official council site PDF, 114 pages. Cover and contents inspected. Council approval, complete Dhivehi text, implementation and relationship to 2026 amendments remain unverified. Census island and council area polygon equivalence unverified.",
        "territory_match": {"territory_id": fonadhoo, "country_id": "MDV",
            "type": "census_administrative_island_2022", "official_code": None,
            "code_system": "Internal P5 row number with MBS atoll abbreviation; official island code unverified",
            "boundary_version": BOUNDARY, "method": "Official publisher L. Fonadhoo Council and P5 L Fonadhoo census row name; exact legal polygon match unverified",
            "source_id": plan["id"], "locator": "PDF cover p1; P5 row 171",
            "checked_at": now[:10]}})

    data["analysis"]["comparisons"] = [{
        "parent_id": "MDV", "member_ids": [maale, *[atoll_id(c) for c in atoll_by_code], nonadmin],
        "label": "2022 census national statistical partition",
        "membership_note": "Maale plus 20 atoll/city administrative-island groups plus non-administrative aggregate are nonoverlapping for P5 census population. Atoll councils were abolished in 2026; no legal authority is implied.",
        "source_ids": ["mdv-cph2022-p4", "mdv-cph2022-p5"]},
        {"parent_id": maale, "member_ids": maale_parts,
         "label": "Maale 2022 census subareas",
         "membership_note": "Nine P5 subareas include a harbour reporting row; no council ward status is implied.",
         "source_ids": ["mdv-cph2022-p5"]},
        *[{"parent_id": atoll_id(code), "member_ids": ids,
           "label": "2022 administrative-island census rows",
           "membership_note": "Direct P5 island counts reconcile with P4 atoll reporting row. Current council jurisdiction and island polygons are unverified.",
           "source_ids": ["mdv-cph2022-p4", "mdv-cph2022-p5"]}
          for code, ids in aid_to_islands.items()]]
    data["analysis"]["terminal_territory_ids"] = [*maale_parts, *island_by_key.values(), nonadmin]
    data["analysis"]["default_indicator_id"] = iid("population")
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {"title": "Local council plans and census evidence",
        "purpose": "Use selected 2022 census counts for a reporting area, then verify the current council jurisdiction and obtain its actual plan, budget, implementation and evaluation.",
        "system": {"label": "Maldives local councils; 2026 institutional changes under review",
            "scope": "The 2022 census atoll/city rows are statistical reporting groups. Atoll councils and secretariats ceased in May 2026; island/city council jurisdiction requires current crosswalk.",
            "cycle": "Current statutory plan cycle and approval conditions require article-level review after 2026 amendments",
            "source_ids": ["mdv-presidency-atoll-councils-ended-2026",
                           "mdv-presidency-local-governance-amendment-2026"]},
        "sections": [{"id": k, "label": v} for k, v in (
            ("plan", "Area-specific development plan"), ("budget", "Budget and allocations"),
            ("implementation", "Expenditure and implementation"),
            ("evaluation", "Official evaluation"), ("reference", "Census and legal references"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "mbs-cph2022-selected-direct-counts"]))
    data["collection"]["notes"] = [
        "58 MBS CPH 2022 workbooks acquired. Six selected tables/fields semantically audited; 52 other workbooks and unselected columns priority_unassessed.",
        "Two island-name mismatches each in EC3 and ED16 held; P5 G17 Maldivian female blank retained as missing, not inferred zero.",
        "2022 census statistical atolls are not 2026 atoll councils; Fonadhoo plan PDF is an issuer-specific body with approval and full content unverified.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith((
            "Initial national-data site inputs only", "58 MBS CPH 2022 workbooks acquired.",
            "Two island-name mismatches each", "2022 census statistical atolls are"))]]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "MBS 2022 atoll abbreviations and 186 P5 island rows reconcile internally. Official dated island codes/polygons and 2026 council jurisdiction crosswalk are unverified. Atoll councils were abolished in May 2026.",
         "next_action": "Obtain dated official island register and polygons, 2026 council boundaries and legal amendment text; audit row-by-row code correspondence."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Selected fields from P4/P5/H2/H7/EC3/ED16 adopted. The other 52 acquired workbooks and unselected fields remain priority_unassessed; two EC3/ED16 island spellings held.",
         "next_action": "Audit remaining tables by original numeric column/definition and resolve two name crosswalks from official identifiers."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Fonadhoo Council 114-page development plan body acquired for its island only; contents/approval not fully audited. Other island/city council plans, budgets, spending and evaluations not acquired.",
         "next_action": "Review current law and Fonadhoo plan contents, then acquire council-specific budget, spending and evaluation bodies for representative islands."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    direct = [o for o in data["observations"] if o["indicator_id"].startswith(PREFIX)]
    require(len(field_to_source) == 23 and len(direct) == 3626,
            f"Unexpected adopted counts {len(field_to_source)} {len(direct)}")
    result = {"source_workbooks": 58, "selected_tables": list(audit["selected_source_codes"]),
              "territories": len(data["territories"]), "atolls": 20, "islands": 186,
              "maale_parts": 9, "indicators": len(field_to_source),
              "direct_observations": len(direct), "population": p["country"]["fields"]["population"],
              "households": h["country"]["fields"]["households"],
              "fonadhoo_plan_pdf_pages": plan["pages"], "official_compatible_polygons": 0,
              "independent_acceptance": False, "dataset_sha256": digest(data_path.read_bytes())}
    (project / "evidence/MDV_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

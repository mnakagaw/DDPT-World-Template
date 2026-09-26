"""Import audited NSO 2021 census counts without inferring boundary joins or rates.

The national, province and district rows are direct source observations. Local
level rows and separate institutional rows partition each district population.
Water and toilet tables cover private households, not institutional households.
"""

import argparse
import hashlib
import json
import runpy
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


inventory = runpy.run_path(str(Path(__file__).with_name("inventory-nepal-nso2021.py")))
FIELDS = inventory["FIELDS"]
require = inventory["require"]
MANIFEST = Path(__file__).resolve().parents[1] / "config/nepal-nso2021-source-manifest.json"
PLANNING_MANIFEST = Path(__file__).resolve().parents[1] / "config/nepal-planning-source-manifest.json"
PREFIX = "NPL_NSO2021_"
PERIOD = "2021"
BOUNDARY = "NSO 2021 census reporting units; 2023 code register partly reconciled; official compatible polygons unacquired"
KMC = "NPL:NSO2021:P3:D06:L08"
PROVINCES = ("Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpaschim")
NAMES = {
    "households_all": "All households, including institutional households",
    "population": "Census population, all persons",
    "male": "Census population, male",
    "female": "Census population, female",
    "households_private": "Private households",
    "piped_inside": "Private households: piped drinking water inside premises",
    "piped_outside": "Private households: piped drinking water outside premises",
    "tube_well": "Private households: tube well or hand pump drinking water",
    "covered_well": "Private households: covered well drinking water",
    "uncovered_well": "Private households: uncovered well drinking water",
    "spout": "Private households: spout drinking water",
    "river_stream": "Private households: river or stream drinking water",
    "jar_bottle": "Private households: jar or bottled drinking water",
    "other_water": "Private households: other drinking water source",
    "flush_sewer": "Private households: flush toilet to sewerage",
    "flush_septic": "Private households: flush toilet to septic tank",
    "pit_toilet": "Private households: pit toilet",
    "public_toilet": "Private households: public toilet",
    "no_toilet": "Private households: no toilet facility",
}
REFERENCES = (
    ("npl-npc-local-planning-guide-2078", "NPC local-level plan formulation guidance, 2078",
     "https://npc.gov.np/content/5107/5107-%25E0%25A4%25B8%25E0%25A4%25A5%25E0%25A4%25A8%25E0%25A4%25AF-%25E0%25A4%25A4%25E0%25A4%25B9%25E0%25A4%2595-%25E0%25A4%25AF%25E0%25A4%259C%25E0%25A4%25A8-%25E0%25A4%25A4%25E0%25A4%25B0%25E0%25A4%259C%25E0%25A4%25AE-%25E0%25A4%25A6%25E0%25A4%2597/",
     "https://giwmscdnone.gov.np/media/app/public/56/posts/1684598335_57.pdf",
     "raw/npc-local-planning-guide-2078.pdf", "National Planning Commission", "reference", "2078",
     "244-page guidance body acquired. It concerns local-level plan formulation, not an adopted plan for every palika."),
    ("npl-local-government-operation-act-2074", "Local Government Operation Act 2074",
     "https://daokailali.moha.gov.np/en/post/local-government-operation-act-2074",
     None, None, "District Administration Office Kailali", "reference", "2074",
     "Official act location identified; consolidated current force and article-level requirements not yet audited."),
    ("npl-kmc-action-plan-2083-84", "Kathmandu Metropolitan City Annual Action Plan 2083/84",
     "https://kathmandu.gov.np/en/notices/annual-action-plan-2083-84",
     "https://files.kathmandu.gov.np/uploads/medias/19f1df22cc154bf2b521460124e25fc6.pdf",
     "raw/kmc-action-2083-84.pdf", "Kathmandu Metropolitan City", "plan", "2083/84",
     "187-page city action-plan body acquired; opening pages inspected. This is for Kathmandu Metropolitan City, not Kathmandu District or Bagmati Province. Approval and full contents not yet independently audited."),
    ("npl-kmc-budget-2083-84", "Kathmandu Metropolitan City Annual Budget and Program 2083/84",
     "https://kathmandu.gov.np/en/notices/kathmandu-metropolitan-city-annual-budget-and-program-for-fiscal-year-2083-84",
     "https://files.kathmandu.gov.np/uploads/medias/027510d56b07404bb7c73cf4ff1c039a.pdf",
     "raw/kmc-budget-2083-84.pdf", "Kathmandu Metropolitan City", "budget", "2083/84",
     "116-page city budget body acquired; opening income table inspected. Reported budget amounts are allocations/estimates, not expenditure or outcome."),
    ("npl-kmc-progress-2082-83", "Kathmandu Metropolitan City Annual Progress Report 2082/83",
     "https://kathmandu.gov.np/en/notices/kathmandu-metropolitan-city-annual-progress-report-for-the-fiscal-year-2082-83",
     "https://files.kathmandu.gov.np/uploads/medias/766f1bd16e224e5c9748c98a8b50f6f3.pdf",
     "raw/kmc-progress-2082-83.pdf", "Kathmandu Metropolitan City", "implementation", "2082/83",
     "Five-page city annual-progress body acquired; first page inspected. It describes prior-year implementation; specific outcome and financial values not adopted."),
)


def tid(province, order=None, serial=None, institutional=False):
    result = f"NPL:NSO2021:P{province}"
    if order is not None:
        result += f":D{order:02d}"
    if serial is not None:
        result += ":I" if institutional else f":L{serial:02d}"
    return result


def iid(table, field):
    return PREFIX + table.upper() + "_" + field.upper()


def source_id(province, table):
    return f"npl-nso2021-{table.lower()}-p{province}"


def add_obs(data, territory, table, field, value, source, sheet, row, col, scope):
    data["observations"].append({
        "territory_id": territory, "indicator_id": iid(table, field), "period": PERIOD,
        "value": value, "status": "observed", "source_id": source,
        "measurement_method": "NSO 2021 census direct count",
        "provenance": "source_reported", "source_locator": f"{sheet}!{col}{row}",
        "population_scope": scope, "boundary_version": BOUNDARY,
    })


def main(project):
    audit_path = project / "evidence/NPL_NSO2021_AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(audit["manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
            "Rerun inventory after manifest change")
    recon = audit["reconciliation"]
    require(recon["population_row_types"] == {"district": 77, "local": 753,
                                               "institutional": 77}, "Unexpected hierarchy")
    require(recon["local_code_matches"] == {"exact_normalized": 749,
            "minor_transliteration": 2, "name_conflict_unresolved": 2},
            "Unexpected code matching state")
    require(audit["national"]["Indv01"]["population"] == 29164578 and
            audit["national"]["Hhld06"]["households_private"] == 6660841,
            "Source totals changed")
    planning_manifest = json.loads(PLANNING_MANIFEST.read_text(encoding="utf-8"))
    planning_map = {x["source_id"]: x for x in planning_manifest["files"]}
    require(len(planning_map) == 4, "Expected four pinned planning PDFs")
    planning = {}
    for source, _, _, _, raw, _, _, _, _ in REFERENCES:
        if raw:
            body = project / raw
            entry = planning_map[source]
            require(body.exists() and body.read_bytes().startswith(b"%PDF-") and
                    body.stat().st_size == entry["bytes"] and
                    hashlib.sha256(body.read_bytes()).hexdigest() == entry["sha256"],
                    f"Missing official planning PDF {raw}")
            page = project / entry["page_raw_path"]
            require(page.exists() and page.stat().st_size == entry["page_bytes"] and
                    hashlib.sha256(page.read_bytes()).hexdigest() == entry["page_sha256"],
                    f"Official publication page changed {source}")
            planning[source] = {"raw_path": raw, "bytes": entry["bytes"],
                                "sha256": entry["sha256"], "pages": entry["pages"],
                                "reviewed_pages": entry["reviewed_pages"]}
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "NPL", "Expected Nepal project")
    data["territories"] = [x for x in data["territories"] if x["id"] == "NPL"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("npl-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("npl-")]
    now = datetime.now(timezone.utc).isoformat()
    data["country"]["geography_note"] = (
        "NSO 2021 census direct counts for 7 provinces, 77 districts and 753 local levels. "
        "The 2023 NSO code register matches 749 local names exactly after normalization and "
        "two minor transliterations; two name conflicts retain census row IDs but no adopted "
        "official code. Institutional population is a separate nonterritorial row in each "
        "district. Private-household amenity tables exclude those institutional households. "
        "No official same-edition boundary polygons are joined; WDI midyear estimates are separate.")
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "NSO 2021 census geography; 2023 code and polygon match incomplete"
    tables = audit["adopted_tables"]
    for p, name in enumerate(PROVINCES, 1):
        data["territories"].append({"id": tid(p), "name": name, "level": "province_2021",
            "type": "census_province", "parent_id": "NPL", "official_code": str(p),
            "code_system": "NSO 2023 pradesh_code ordinal; register uses State 1-7 rather than the 2021 province names",
            "boundary_version": BOUNDARY, "source_id": source_id(p,"Indv01")})
        for row in tables[f"P{p}-Indv01"]["rows"]:
            kind = row["kind"]
            if kind == "district":
                area = tid(p, row["district_order"])
                parent = tid(p)
                code = row["official_code"]
                level, type_ = "district_2021", "census_district"
            elif kind == "institutional":
                area = tid(p, row["district_order"], 99, True)
                parent = tid(p, row["district_order"])
                code = None
                level, type_ = "institutional_2021", "nonterritorial_statistical_population"
            else:
                area = tid(p, row["district_order"], row["source_serial"])
                parent = tid(p, row["district_order"])
                code = row["official_code"]
                level, type_ = "local_level_2021", "census_local_level"
            territory = {"id": area, "name": row["name"], "level": level,
                "type": type_, "parent_id": parent, "official_code": code,
                "code_system": "NSO 2023 code register; held where 2021/2023 names conflict"
                               if kind != "institutional" else "NSO 2021 institutional row; no geographic code",
                "boundary_version": BOUNDARY, "source_id": row["source_id"],
                "reconciliation_status": row.get("code_name_status", "2021 census district name matches 2023 code register")}
            if kind == "local":
                territory["code_candidate"] = row["code_candidate"]
                territory["code_register_name"] = row["code_register_name"]
            if kind == "institutional":
                territory["reconciliation_status"] = "Institutional residents and households are separate statistical counts; no mapped local-level jurisdiction"
            data["territories"].append(territory)
    require(len(data["territories"]) == 915, "Unexpected territory count")
    manifest_map = {(int(x["province_directory"][1:]), x["table"]): x
                    for x in manifest["source_files"]}
    for p in range(1, 8):
        for table in FIELDS:
            source = tables[f"P{p}-{table}"]
            for field_index, field in enumerate(FIELDS[table], 2):
                col = chr(65 + field_index)
                scope = "all_people_including_institutional" if table == "Indv01" else "private_households_only"
                if p == 1:
                    add_obs(data, "NPL", table, field, source["national"][field],
                            source_id(p, table), source["sheet"], 6, col, scope)
                add_obs(data, tid(p), table, field, source["province_value"][field],
                        source_id(p, table), source["sheet"], 8, col, scope)
                for row in source["rows"]:
                    kind = row["kind"]
                    area = tid(p, row["district_order"], row["source_serial"], kind == "institutional") if kind != "district" else tid(p, row["district_order"])
                    add_obs(data, area, table, field, row["values"][field],
                            source_id(p, table), source["sheet"], row["source_cell_row"], col, scope)
    for table, fields in FIELDS.items():
        selected = fields if table != "Hhld09" else fields[1:]
        for field in selected:
            is_pop = table == "Indv01"
            data["indicators"].append({"id": iid(table,field), "name": NAMES[field],
                "theme": "Population" if is_pop else "Living conditions",
                "unit": "people" if field in ("population","male","female") else "households",
                "definition": f"NSO NPHC 2021 {table} direct count; " +
                   ("all-person or all-household census universe with institutional rows separate."
                    if is_pop else "private households only; categories are source labels, not WHO/JMP service tiers."),
                "population": "all census residents and households including institutional"
                              if is_pop else "private households, excluding institutional",
                "source_id": source_id(1,table), "aggregation": "none",
                "measurement_method": "NSO 2021 census direct count",
                "display_decimals": 0})
    # Hhld09 repeats the private-household denominator already taken from Hhld06.
    data["observations"] = [x for x in data["observations"]
        if x["indicator_id"] != iid("Hhld09", "households_private")]
    for territory in data["territories"]:
        if territory["level"] != "institutional_2021":
            continue
        p = int(territory["id"].split(":P")[1].split(":")[0])
        for table in ("Hhld06", "Hhld09"):
            for field in FIELDS[table] if table == "Hhld06" else FIELDS[table][1:]:
                data["observations"].append({
                    "territory_id": territory["id"], "indicator_id": iid(table,field),
                    "period": PERIOD, "value": None, "status": "not_applicable",
                    "source_id": source_id(p,table),
                    "source_locator": "Household Table 6/9 covers private households; the institutional row exists only in Individual Table 1",
                    "population_scope": "institutional_households_outside_private_household_table",
                    "boundary_version": BOUNDARY})
    for entry in manifest["source_files"]:
        p = int(entry["province_directory"][1:])
        adopted = entry["table"] in FIELDS
        data["sources"].append({"id": source_id(p, entry["table"]),
            "name": f"NSO NPHC 2021 P{p} {entry['table']} original workbook",
            "url": entry["url"], "publisher": "National Statistics Office, Nepal",
            "reference_period": PERIOD, "geographic_level": "national, province, district, local level; institutional rows in Indv01",
            "status": "ready" if adopted else "partial",
            "raw_path": entry["raw_path"], "sha256": entry["sha256"],
            "retrieved_at": now, "license": "Official public workbook; redistribution terms unverified",
            "note": "Original hash pinned. All count columns reconciled across hierarchy."
                    if adopted else "Age/sex literacy hierarchy inventoried only; no values adopted."})
    data["sources"].append({"id": "npl-nso-2023-codes", "name": "NSO 2023 geographical code register",
        "url": manifest["administrative_code_source_url"], "publisher": "National Statistics Office, Nepal",
        "reference_period": "2023 code release", "geographic_level": "7 provinces, 77 districts, 753 local levels",
        "status": "partial", "raw_path": manifest["administrative_code_raw_path"],
        "sha256": manifest["administrative_code_sha256"], "retrieved_at": now,
        "license": "Official public XLS; redistribution terms unverified",
        "note": "2021 census rows cross-checked to 2023 codes. Two local name conflicts unresolved; official_code withheld on those 2021 rows."})
    for source, title, page_url, pdf_url, raw, publisher, category, period, note in REFERENCES:
        item = {"id": source, "name": title, "url": pdf_url or page_url,
            "publisher": publisher, "reference_period": period,
            "geographic_level": "Kathmandu Metropolitan City" if source.startswith("npl-kmc") else "national local-planning reference",
            "status": "partial" if raw else "not_collected",
            "retrieved_at": now, "license": "Official public PDF; redistribution terms unverified" if raw else "Location only",
            "note": note + f" Catalogue: {page_url}"}
        if raw:
            item.update(planning[source])
        data["sources"].append(item)
        territory = KMC if source.startswith("npl-kmc") else "NPL"
        area = next(x for x in data["territories"] if x["id"] == territory)
        document = {"id": source + "-document", "territory_id": territory,
            "category": category, "kind": "city_annual_action_plan" if category == "plan" else
                                      "city_annual_budget" if category == "budget" else
                                      "city_annual_progress" if category == "implementation" else "planning_reference",
            "title": title, "url": pdf_url or page_url, "source_id": source,
            "period": period, "availability": "body_acquired" if raw else "link_verified",
            "official_status": "unverified", "note": note}
        if raw:
            document["territory_match"] = {"territory_id": territory, "country_id": "NPL",
                "type": area["type"], "official_code": area.get("official_code"),
                "code_system": area["code_system"], "boundary_version": area.get("boundary_version"),
                "method": "City issuer and title matched to NSO local-level name/code; no current polygon or ward match"
                          if territory == KMC else "National source reference only",
                "source_id": source, "locator": "Official city publication page and PDF opening pages" if territory == KMC else "NPC guidance cover page",
                "checked_at": now}
        data["documents"].append(document)
    for p in range(1, 8):
        data["documents"].append({"id": f"npl-nso2021-census-p{p}-reference",
            "territory_id": tid(p), "category": "reference", "kind": "official_census_originals",
            "title": f"NSO 2021 province {p} census population, water and toilet originals",
            "url": manifest["catalogue_url"], "source_id": source_id(p,"Indv01"),
            "period": PERIOD, "availability": "body_acquired", "official_status": "official_statistical_release",
            "official_evidence": {"source_id": source_id(p,"Indv01"),
                "locator": f"{tables[f'P{p}-Indv01']['sheet']}!A1:F8 official census table heading and province row",
                "checked_at": now},
            "territory_match": {"territory_id": tid(p), "country_id": "NPL",
                "type": "census_province", "official_code": str(p),
                "code_system": "NSO 2023 pradesh_code ordinal; register uses State 1-7 rather than the 2021 province names",
                "boundary_version": BOUNDARY,
                "method": "Same census province directory and workbook province row; code ordinal cross-checked to NSO 2023 register, polygons not joined",
                "source_id": source_id(p,"Indv01"), "locator": f"{tables[f'P{p}-Indv01']['sheet']}!A8:F8",
                "checked_at": now},
            "note": "Three adopted XLSX table bodies pinned in acquisition receipt; 2021 census counts, not a plan."})
    comparisons = []
    for parent in ["NPL"] + [tid(p) for p in range(1,8)] + [tid(p, d)
            for p in range(1,8) for d in range(1, 1 + len([r for r in tables[f"P{p}-Indv01"]["rows"] if r["kind"] == "district"]))]:
        members = [x["id"] for x in data["territories"] if x.get("parent_id") == parent]
        require(members, f"Comparison missing children {parent}")
        p = int(parent.split(":P")[1].split(":")[0]) if ":P" in parent else 1
        comparisons.append({"parent_id": parent, "member_ids": members,
            "label": "NSO 2021 census reporting units",
            "membership_note": "Direct source rows. District population contains a separate nonterritorial institutional row; private-household amenities exclude that row. Parent direct observations take precedence. No rate is averaged or estimated from incomplete children.",
            "source_ids": [source_id(p,"Indv01"), source_id(p,"Hhld06"), source_id(p,"Hhld09")]})
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = [x["id"] for x in data["territories"]
        if x["level"] in ("local_level_2021", "institutional_2021")]
    data["analysis"]["default_indicator_id"] = iid("Indv01","population")
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {"title": "Local plans and census evidence",
        "purpose": "Use 2021 census counts to diagnose the selected palika; obtain and distinguish its own adopted plan, budget, implementation and evaluation for the relevant period.",
        "system": {"label": "Nepal local-level planning under the Local Government Operation Act and NPC guidance",
            "scope": "Kathmandu city documents apply only to Kathmandu Metropolitan City. Province and district census units are diagnostic and do not inherit its city plan.",
            "cycle": "Planning and fiscal periods must be verified for each local government",
            "source_ids": ["npl-local-government-operation-act-2074", "npl-npc-local-planning-guide-2078"]},
        "sections": [{"id": k, "label": v} for k,v in (
            ("plan","Area-specific adopted plan"),("budget","Budget and allocations"),
            ("implementation","Expenditure and implementation"),("evaluation","Official evaluation"),
            ("reference","Census originals and planning guidance"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "nso-2021-selected-domestic-census-tables"]))
    data["collection"]["notes"] = [
        "21 selected NSO census workbooks adopted as direct counts; 7 literacy originals inventoried but unassessed. All 89 catalogue XLSX families per province have not been audited.",
        *[x for x in data["collection"].get("notes", [])
          if not x.startswith("Initial national-data site inputs only")]]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "2021 census names mapped to 2023 NSO codes except two unresolved local name conflicts. Provider 2020 ADM1 shapes removed; no matched official polygons.",
         "next_action": "Resolve code history for 30304 and 70905 and acquire dated official province/district/local polygons."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Population, sex, private-household drinking-water and toilet category counts adopted from 21 original XLSX. 7 literacy workbooks inventoried only; 85 other XLSX families per province remain unacquired. Institutional households excluded from amenities.",
         "next_action": "Audit source definitions and remaining priority census/sector tables, including literacy age/sex hierarchy and ward-level data where available."},
        {"category": "planning_documents", "status": "partial",
         "detail": "NPC local-planning guidance and Kathmandu city action plan, budget and prior-year progress PDFs acquired. Current law provisions, full bodies, adoption, expenditures and evaluation have not been assessed for each palika.",
         "next_action": "Review applicable act and guide provisions, verify approval and figures in Kathmandu documents, then survey other palikas and provinces."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    nobs = sum(x["indicator_id"].startswith(PREFIX) and x["status"] == "observed"
               for x in data["observations"])
    nna = sum(x["indicator_id"].startswith(PREFIX) and x["status"] == "not_applicable"
              for x in data["observations"])
    require(len(data["indicators"]) >= 19 and nobs == 16230,
            f"Unexpected adopted observation count {nobs}")
    require(nna == 1155, f"Unexpected institutional non-applicable count {nna}")
    result = {"adopted_originals": 21, "unassessed_originals": 7,
        "territories": len(data["territories"]), "census_indicators": 19,
        "census_observations": nobs, "institutional_amenity_not_applicable": nna,
        "official_compatible_polygons": 0,
        "unresolved_local_codes": 2, "comparison_sets": len(comparisons),
        "planning_pdf_receipts": planning, "independent_acceptance": False,
        "dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest()}
    (project/"evidence/NPL_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "planning_pdf_receipts"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

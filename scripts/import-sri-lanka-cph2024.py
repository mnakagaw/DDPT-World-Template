"""Import selected final DCS 2024 census counts at country/district/DS level.

The 2024 GN population file is labeled provisional and its age counts differ
from eight final DS rows. It is retained as original evidence, not merged into
this final statistical series. DS areas are not local-government councils.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/sri-lanka-cph2024-source-manifest.json"
PREFIX = "LKA_DCS2024_"
PERIOD = "2024"
BOUNDARY = "DCS 2024 census districts and Divisional Secretary reporting units; official same-edition polygons unacquired"
FIELDS = {
    "populationa-a5": ["population", "male", "female", "under_15", "age_15_59", "age_60_64", "age_65_plus"],
    "housinga-a14": ["households", "protected_well", "semi_protected_well", "unprotected_well",
                     "tube_well", "spring", "water_board_piped", "local_authority_piped",
                     "community_piped", "private_piped", "tank_river_stream", "rainwater",
                     "bottled_water", "reverse_osmosis", "bowser", "other_water"],
    "housinga-a16": ["households", "within_unit_exclusive", "within_unit_shared",
                     "outside_unit_exclusive", "outside_unit_shared", "other_unit_shared",
                     "public_toilet", "no_toilet"],
}
PROVINCES = (
    (1, "Western", 6117341), (2, "Central", 2714045), (3, "Southern", 2606679),
    (4, "Northern", 1150148), (5, "Eastern", 1783214), (6, "North Western", 2586972),
    (7, "North Central", 1407610), (8, "Uva", 1399892), (9, "Sabaragamuwa", 2015899),
)
LABELS = {
    "population": "Usual resident population", "male": "Usual resident population: male",
    "female": "Usual resident population: female", "under_15": "Population under 15 years",
    "age_15_59": "Population aged 15–59 years", "age_60_64": "Population aged 60–64 years",
    "age_65_plus": "Population aged 65 years and over",
    "households": "Households", "protected_well": "Households: protected well drinking water",
    "semi_protected_well": "Households: semi-protected well drinking water",
    "unprotected_well": "Households: unprotected well drinking water",
    "tube_well": "Households: tube well drinking water",
    "spring": "Households: spring or fountain drinking water",
    "water_board_piped": "Households: national water board piped water",
    "local_authority_piped": "Households: local-authority piped water",
    "community_piped": "Households: community-based piped water",
    "private_piped": "Households: private piped water project",
    "tank_river_stream": "Households: tank, river or stream drinking water",
    "rainwater": "Households: rainwater as main drinking source",
    "bottled_water": "Households: bottled drinking water",
    "reverse_osmosis": "Households: reverse-osmosis filtered drinking water",
    "bowser": "Households: bowser drinking water",
    "other_water": "Households: other main drinking water source",
    "within_unit_exclusive": "Households: toilet in unit, exclusive use",
    "within_unit_shared": "Households: toilet in unit, shared",
    "outside_unit_exclusive": "Households: toilet outside unit, exclusive use",
    "outside_unit_shared": "Households: toilet outside unit, shared",
    "other_unit_shared": "Households: no own toilet, shares another unit",
    "public_toilet": "Households: common or public toilet",
    "no_toilet": "Households: not using a toilet",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def source_id(key):
    return "lka-dcs2024-" + key


def indicator_id(key, field):
    return PREFIX + key.replace("-", "_").upper() + "_" + field.upper()


def province_id(p):
    return f"LKA:DCS2024:P{p}"


def district_id(p, d):
    return f"{province_id(p)}:D{d}"


def division_id(p, d, ds):
    return f"{district_id(p, d)}:DS{ds:02d}"


def add_observation(data, territory, key, field, value, row, col, method="source_reported"):
    item = {"territory_id": territory, "indicator_id": indicator_id(key, field),
            "period": PERIOD, "value": value, "status": "observed", "source_id": source_id(key),
            "measurement_method": "DCS CPH 2024 final census direct count",
            "provenance": method, "source_locator": f"{key.split('-')[-1].upper()}!{col}{row}",
            "population_scope": "usual_residents" if key == "populationa-a5" else "households",
            "boundary_version": BOUNDARY}
    data["observations"].append(item)


def main(project):
    audit = json.loads((project / "evidence/LKA_CPH2024_AUDIT.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(audit["manifest_sha256"] == digest(MANIFEST.read_bytes()),
            "Rerun inventory after manifest change")
    require(audit["gn_code_reconciliation"]["exact_code_keys"] == 14008 and
            len(audit["gn_age_differences_from_final_a5"]) == 8,
            "GN/final distinction changed")
    entries = {x["id"]: x for x in manifest["source_files"]}
    require(len(entries) == 34, "Unexpected source manifest")
    for x in entries.values():
        file = project / x["raw_path"]
        require(file.exists() and file.stat().st_size == x["bytes"] and
                digest(file.read_bytes()) == x["sha256"], f"Original changed {x['id']}")
    report = PdfReader(project / entries["final-report-en"]["raw_path"])
    require(len(report.pages) == 266, "Final report page count changed")
    table_text = report.pages[67].extract_text() or ""
    for _, name, value in PROVINCES:
        require(name + " Province" in table_text and f"{value:,}" in table_text,
                f"Province Table 3.2 value missing: {name}")

    path = project / "data/dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "LKA", "Expected Sri Lanka project")
    data["territories"] = [x for x in data["territories"] if x["id"] == "LKA"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("lka-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("lka-")]
    now = datetime.now(timezone.utc).isoformat()
    data["country"]["geography_note"] = (
        "DCS CPH 2024 final counts for 25 districts and 340 Divisional Secretary Divisions; "
        "nine final province population totals from Table 3.2. The DCS code register and GN workbook "
        "align by 14,008 source keys, but GN age counts differ from final DS counts in eight divisions. "
        "The GN workbook is labeled provisional and is not merged into final indicators. "
        "DS census units are not local-government authorities; no official compatible polygon is joined. "
        "WDI midyear national estimates remain a separate series.")
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "DCS 2024 final census geography; official polygon and local-authority crosswalk pending"

    crosswalk = {x["final_row"]: x for x in audit["division_code_crosswalk"]}
    a5 = audit["selected"]["populationa-a5"]["records"]
    division_codes_by_district = {}
    for x in crosswalk.values():
        division_codes_by_district.setdefault(x["district"], set()).add(
            (x["official_province_code"], x["official_district_code"]))
    require(all(len(x) == 1 for x in division_codes_by_district.values()) and
            len(division_codes_by_district) == 25, "District code hierarchy is ambiguous")
    territory_by_a5_index = []
    for index, row in enumerate(a5):
        if row["kind"] == "country":
            territory_by_a5_index.append("LKA")
            continue
        if row["kind"] == "district":
            p, d = next(iter(division_codes_by_district[row["district"]]))
            aid = district_id(p, d)
            data["territories"].append({"id": aid, "name": row["district"],
                "level": "district_2024", "type": "census_district",
                "parent_id": province_id(p), "official_code": f"{p}/{d}",
                "code_system": "DCS administrative code workbook Province_Code/District_Code components; GN table also labels district with two-digit province+district",
                "boundary_version": BOUNDARY, "source_id": source_id("populationa-a5"),
                "reconciliation_status": "District name and all population fields reconciled to final report and 2024 GN hierarchy"})
        else:
            link = crosswalk[row["row"]]
            p, d, ds = (link["official_province_code"], link["official_district_code"],
                        link["official_ds_code"])
            aid = division_id(p, d, ds)
            data["territories"].append({"id": aid, "name": row["name"],
                "level": "divisional_secretary_2024", "type": "census_divisional_secretary_division",
                "parent_id": district_id(p, d), "official_code": f"{p}/{d}/{ds:02d}",
                "code_system": "DCS administrative code workbook component tuple; not a local-government authority code",
                "boundary_version": BOUNDARY, "source_id": source_id("populationa-a5"),
                "reconciliation_status": link["match_method"],
                "code_register_name": link["code_register_name"]})
        territory_by_a5_index.append(aid)
    for p, name, value in PROVINCES:
        aid = province_id(p)
        data["territories"].append({"id": aid, "name": name, "level": "province_2024",
            "type": "census_province", "parent_id": "LKA", "official_code": str(p),
            "code_system": "DCS Province_Code in official administrative code workbook",
            "boundary_version": BOUNDARY, "source_id": source_id("final-report-en")})
        data["observations"].append({"territory_id": aid,
            "indicator_id": indicator_id("populationa-a5", "population"), "period": PERIOD,
            "value": value, "status": "observed", "source_id": source_id("final-report-en"),
            "measurement_method": "DCS CPH 2024 final census direct count",
            "provenance": "source_reported",
            "source_locator": f"Final Report PDF page 68 (printed page 51), Table 3.2, {name} Province",
            "population_scope": "usual_residents", "boundary_version": BOUNDARY})
    require(len(data["territories"]) == 375 and len(set(x["id"] for x in data["territories"])) == 375,
            "Expected country + 9 provinces + 25 districts + 340 DS divisions")

    for key, fields in FIELDS.items():
        records = audit["selected"][key]["records"]
        require(len(records) == len(territory_by_a5_index), "Selected table row alignment changed")
        for idx, row in enumerate(records):
            aid = territory_by_a5_index[idx]
            for offset, field in enumerate(fields):
                if key == "housinga-a16" and field == "households":
                    continue  # Same source-reported household denominator as A14.
                col = chr(ord("A") + (2 if key == "populationa-a5" else 1) + offset)
                add_observation(data, aid, key, field, row["values"][field], row["row"], col)
    for key, fields in FIELDS.items():
        for field in fields:
            if key == "housinga-a16" and field == "households":
                continue
            people = key == "populationa-a5"
            data["indicators"].append({"id": indicator_id(key, field), "name": LABELS[field],
                "theme": "Population" if people else "Living conditions",
                "unit": "people" if people else "households",
                "definition": "DCS CPH 2024 final direct count. " + (
                    "Usual resident population at the census moment; four age groups are mutually exclusive."
                    if people else "Source household category, not a WHO/JMP service tier or calculated rate."),
                "population": "usual residents" if people else "households",
                "source_id": source_id(key), "aggregation": "none",
                "measurement_method": "DCS CPH 2024 final census direct count",
                "display_decimals": 0})
    for entry in manifest["source_files"]:
        key = entry["id"]
        selected = key in FIELDS
        if selected:
            note = "Selected final count columns and all 366 hierarchy rows audited."
        elif key == "final-report-en":
            note = "Original acquired; Table 3.2 province population adopted, remaining report tables unassessed."
        elif key == "admin-codes":
            note = "Official code workbook acquired; 14,008 GN source keys matched, but current legal boundary edition and polygons unverified."
        elif key == "gn-population-provisional":
            note = "GN workbook labels itself provisional. Population and sex match final DS rows, but age groups differ in eight DS; no GN cells adopted here."
        else:
            note = "Original acquired and sheet dimensions inventoried; numeric meaning and adoption unassessed."
        data["sources"].append({"id": source_id(key),
            "name": f"DCS CPH 2024 {key} official original",
            "url": entry["url"], "publisher": "Department of Census and Statistics, Sri Lanka",
            "reference_period": "2024 census" if key != "admin-codes" else "official code register, edition not yet confirmed",
            "geographic_level": "country, province, district, DS or GN as identified in original",
            "status": "ready" if selected else "partial", "raw_path": entry["raw_path"],
            "sha256": entry["sha256"], "retrieved_at": now,
            "license": "Official public download; redistribution terms unverified",
            "note": note})
    data["sources"].append({"id": "lka-municipal-budget-rules-2020",
        "name": "Sri Lanka Gazette Extraordinary 2199/15 municipal budget and development-plan rules",
        "url": "https://documents.gov.lk/view/extra-gazettes/2020/10/2199-15_E.pdf",
        "publisher": "Department of Government Printing, Sri Lanka",
        "reference_period": "2020 publication; current applicability unverified",
        "geographic_level": "municipal councils, not census DS reporting units",
        "status": "not_collected", "retrieved_at": now,
        "license": "Official public Gazette; terms unverified",
        "note": "Retrieved-at is the online location-check time only: PDF body not archived or adopted. Present legal force, detailed provisions and application to any selected local authority remain under review."})
    data["analysis"]["comparisons"] = []
    for parent in ["LKA"] + [province_id(p) for p, _, _ in PROVINCES] + [x["id"] for x in data["territories"] if x["level"] == "district_2024"]:
        members = [x["id"] for x in data["territories"] if x.get("parent_id") == parent]
        require(members, f"Missing comparison children {parent}")
        data["analysis"]["comparisons"].append({"parent_id": parent, "member_ids": members,
            "label": "DCS 2024 census reporting units",
            "membership_note": "Direct source counts; province population from final report Table 3.2. Province household and age values are missing unless separately acquired or explicitly calculated from complete coverage. No provisional GN age counts enter this comparison.",
            "source_ids": [source_id("populationa-a5"), source_id("housinga-a14"),
                           source_id("housinga-a16"), source_id("final-report-en")]})
    data["analysis"]["terminal_territory_ids"] = [x["id"] for x in data["territories"]
        if x["level"] == "divisional_secretary_2024"]
    data["analysis"]["default_indicator_id"] = indicator_id("populationa-a5", "population")
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {"title": "Local plans and census evidence",
        "purpose": "Use official census counts to diagnose the selected area, then obtain the competent local authority's adopted plan, budget, implementation and evaluation for its actual jurisdiction.",
        "system": {"label": "Sri Lankan local-authority and provincial planning context under review",
            "scope": "A Divisional Secretary census area is not automatically a municipal council, urban council or Pradeshiya Sabha. City plans and budgets must be matched to their own legal jurisdiction.",
            "cycle": "Applicable planning and fiscal periods require authority-specific verification",
            "source_ids": ["lka-municipal-budget-rules-2020"]},
        "sections": [{"id": k, "label": v} for k, v in (
            ("plan", "Area-specific adopted plan"), ("budget", "Budget and allocations"),
            ("implementation", "Expenditure and implementation"),
            ("evaluation", "Official evaluation"), ("reference", "Census and planning references"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "dcs-cph2024-selected-final-ds-counts"]))
    data["collection"]["notes"] = [
        "Final DCS 2024 tables A5, A14 and A16 adopted at country/district/DS level; final report Table 3.2 supplies nine direct province population counts.",
        "Thirty-four official originals acquired. Other numbered/GN tables have not been semantically adopted; the provisional GN age series differs from final DS age in eight DS areas.",
        *[x for x in data["collection"].get("notes", [])
          if not x.startswith("Initial national-data site inputs only")]]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "DCS administrative code components match 340 final DS rows by name/population/sex, including 16 spelling variants; 14,008 GN source keys match code register. Compatible official 2024 polygons and local-authority geographic crosswalk are unacquired.",
         "next_action": "Acquire dated official district, DS, GN and local-government polygons; check legal boundary changes and the 16 spelling variants."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Final A5 population/sex/age and A14/A16 household water/toilet categories adopted for 25 districts and 340 DS. Other acquired tables await numeric-field semantic decisions. Provisional GN age differs in eight DS rows and is not merged.",
         "next_action": "Review remaining 20 numbered A tables, nine GN workbooks and final report; reconcile provisional/final and legal planning geography before any GN adoption."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "No area-specific local-authority plan, budget body, implementation or official evaluation has been adopted. DS statistical areas are not equivalent to councils.",
         "next_action": "Review current Municipal Councils/Urban Councils/Pradeshiya Sabha laws and planning rules, then obtain matching local-authority documents and fiscal evidence."},
    ])
    data["generated_at"] = now
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    direct = sum(x["indicator_id"].startswith(PREFIX) and
                 x.get("provenance") == "source_reported" for x in data["observations"])
    require(len(data["indicators"]) >= 30 and direct == 10989,
            f"Unexpected selected indicator/observation count: {direct}")
    result = {"selected_count_workbooks": 3, "final_province_report_table": "3.2",
        "territories": len(data["territories"]), "selected_indicators": 30,
        "direct_observations": direct, "gn_age_conflict_divisions": 8,
        "official_compatible_polygons": 0, "independent_acceptance": False,
        "dataset_sha256": digest(path.read_bytes())}
    (project / "evidence/LKA_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

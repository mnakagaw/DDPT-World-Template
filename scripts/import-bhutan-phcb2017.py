"""Import the audited Bhutan PHCB 2017 Table A2.1 statistical partition.

The rural Gewog row is a census rural part, not proof of complete legal Gewog
population. Urban towns and local-government Thromdes also require a crosswalk.
"""

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/bhutan-phcb2017-source-manifest.json"
PREFIX = "BTN_PHCB2017_"
BOUNDARY = "PHCB 2017 census Dzongkhag and urban/rural reporting partitions; compatible official polygons unacquired"
PERIOD = "2017"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def district_id(slug):
    return "BTN:PHCB2017:D:" + slug


def indicator_id(field):
    return PREFIX + field.upper()


def add_observation(data, aid, field, value, source, locator):
    data["observations"].append({"territory_id": aid, "indicator_id": indicator_id(field),
        "period": PERIOD, "value": value, "status": "observed", "source_id": source,
        "measurement_method": "NSB PHCB 2017 de facto direct census count, excluding hotel visitors without detailed data",
        "provenance": "source_reported", "source_locator": locator,
        "population_scope": "2017 PHCB detailed-analysis population; excludes 8,408 hotel visitors from national found count",
        "boundary_version": BOUNDARY})


def main(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/BTN_PHCB2017_AUDIT.json").read_text(encoding="utf-8"))
    require(audit["manifest_sha256"] == digest(MANIFEST.read_bytes()), "Rerun inventory after manifest change")
    require(len(audit["districts"]) == 20 and audit["district_population_sum"] == 727145,
            "District source totals changed")
    for source in manifest["source_files"]:
        body = (project / source["raw_path"]).read_bytes()
        require(len(body) == source["bytes"] and digest(body) == source["sha256"],
                f"Original changed: {source['id']}")
    national = next(x for x in manifest["source_files"] if x["id"] == "btn-phcb2017-national-2017")
    national_text = subprocess.run(["pdftotext", "-layout", str(project / national["raw_path"]), "-"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
    heading = "Table 2.1 Distribution of Population by Sex and Dzongkhag/Thromde, Bhutan 2017"
    start = national_text.rfind(heading)
    require(start >= 0, "National Table 2.1 not found")
    national_table = national_text[start:start + 8000]
    require(re.search(r"Bhutan\s+380,453\s+52\.3\s+346,692\s+47\.7\s+727,145", national_table),
            "National detailed-analysis count changed")
    require("735,553" in national_text and "8,408" in national_text,
            "National found-population distinction changed")
    national_pdf_page = national_text[:start].count("\f") + 1

    dataset_path = project / "data/dashboard.json"
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "BTN", "Expected Bhutan candidate")
    data["territories"] = [x for x in data["territories"] if x["id"] == "BTN"]
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "NSB PHCB 2017 district reporting scope; official 2017 polygon/code correspondence pending"
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("btn-phcb2017-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("btn-phcb2017-")]
    now = datetime.now(timezone.utc).isoformat()
    data["country"]["geography_note"] = (
        "NSB PHCB 2017 detailed analysis uses 727,145 persons (20 Dzongkhags), excluding "
        "8,408 tourists/non-Bhutanese found in hotels. Its all-found national count is 735,553, "
        "a separate indicator. Town/Thromde and rural Gewog census rows form a nonoverlapping "
        "statistical partition; rural Gewog rows need not be whole legal Gewogs. The 2020 "
        "statistical-geographic code publication is not assumed to match 2017, and no "
        "compatible official polygons are joined. WDI estimates remain separate.")

    national_source = national["id"]
    national_locator = f"National Report Table 2.1, printed p10, PDF p{national_pdf_page}, Bhutan row"
    for field, value in (("population", 727145), ("male", 380453), ("female", 346692)):
        add_observation(data, "BTN", field, value, national_source, national_locator)
    data["observations"].append({"territory_id": "BTN",
        "indicator_id": indicator_id("all_found_including_hotel_visitors"),
        "period": PERIOD, "value": 735553, "status": "observed", "source_id": national_source,
        "measurement_method": "NSB PHCB 2017 all persons found on census reference day, including hotel visitors",
        "provenance": "source_reported",
        "source_locator": f"National Report text preceding Table 2.1, PDF p{national_pdf_page}; 735,553 = 727,145 + 8,408",
        "population_scope": "all found on census reference day including 8,408 tourists/non-Bhutanese found in hotels",
        "boundary_version": BOUNDARY})

    ids_by_source = {}
    local_ids = []
    for district in audit["districts"]:
        source = district["source_id"]
        did = district_id(district["slug"])
        ids_by_source[source] = did
        data["territories"].append({"id": did, "name": district["name"].title(),
            "level": "dzongkhag_2017", "type": "census_dzongkhag",
            "parent_id": "BTN", "official_code": None,
            "code_system": "Internal 2017 PHCB report slug; NSB BSSGC 2020 not historically matched",
            "boundary_version": BOUNDARY, "source_id": source,
            "reconciliation_status": "Direct district report row; official 2017 code/polygon pending"})
    counters = {}
    for row in audit["selected_rows"]:
        source = row["source_id"]
        did = ids_by_source[source]
        kind = row["kind"]
        if kind == "subtotal":
            continue  # Urban/rural subtotal retained in audit, not doubled as a territory.
        if kind == "dzongkhag":
            aid = did
        else:
            counters[(source, kind)] = counters.get((source, kind), 0) + 1
            aid = f"{did}:{'T' if kind == 'town' else 'G'}{counters[(source, kind)]:02d}"
            data["territories"].append({"id": aid, "name": row["name"],
                "level": "census_urban_place_2017" if kind == "town" else "census_rural_gewog_part_2017",
                "type": "census_urban_town_or_thromde" if kind == "town" else "census_rural_gewog_part",
                "parent_id": did, "official_code": None,
                "code_system": "Internal Table A2.1 row ordinal, not an official geographic code",
                "boundary_version": BOUNDARY, "source_id": source,
                "reconciliation_status": "Direct 2017 census urban/rural row; legal LG extent and code unverified"})
            local_ids.append(aid)
        locator = f"District Report Table A2.1, PDF p{row['source_page_text_position']}, {row['name']} row"
        for field in ("population", "male", "female"):
            add_observation(data, aid, field, row[field], source, locator)
    require(len(data["territories"]) == 290 and len(local_ids) == 269,
            f"Unexpected reporting unit count {len(data['territories'])} {len(local_ids)}")
    for field, name in (("population", "2017 census detailed-analysis population"),
                        ("male", "2017 census detailed-analysis population: male"),
                        ("female", "2017 census detailed-analysis population: female"),
                        ("all_found_including_hotel_visitors", "2017 all persons found, including hotel visitors")):
        data["indicators"].append({"id": indicator_id(field), "name": name,
            "theme": "Population", "unit": "people",
            "definition": "NSB 2017 de facto census direct count. " + (
                "All persons found, including 8,408 tourists/non-Bhutanese in hotels; not comparable to local detailed-analysis rows."
                if field == "all_found_including_hotel_visitors" else
                "Excludes 8,408 tourists/non-Bhutanese in hotels without detailed data. Rural Gewog rows are census rural parts, not necessarily complete legal Gewogs."),
            "population": "all found including hotel visitors" if field == "all_found_including_hotel_visitors"
                          else "PHCB detailed-analysis population excluding hotel visitors",
            "source_id": national_source, "aggregation": "none",
            "measurement_method": (
                "NSB PHCB 2017 all persons found on census reference day, including hotel visitors"
                if field == "all_found_including_hotel_visitors" else
                "NSB PHCB 2017 de facto direct census count, excluding hotel visitors without detailed data"),
            "display_decimals": 0})

    for source in manifest["source_files"]:
        key = source["id"]
        selected = key == national_source or key.startswith("btn-phcb2017-district-")
        data["sources"].append({"id": key,
            "name": ("NSB PHCB 2017 " + key.removeprefix("btn-phcb2017-").replace("-", " ")).title(),
            "url": source["url"], "publisher": "National Statistics Bureau, Royal Government of Bhutan"
            if selected or key.endswith("geographic-codes") else
            "Department of Local Governance and Disaster Management, Bhutan",
            "reference_period": "2017 census" if selected else "2020 code edition" if key.endswith("geographic-codes") else "2012 rules, present force unverified",
            "geographic_level": "national, Dzongkhag, town/Thromde or rural Gewog part" if selected else "Bhutan administrative codes or local-government rules",
            "status": "ready" if selected else "partial", "raw_path": source["raw_path"],
            "sha256": source["sha256"], "retrieved_at": now,
            "license": "Official public PDF; raw redistribution terms unverified",
            "note": "Only Table A2.1 direct counts adopted; all other report tables remain priority_unassessed."
                    if selected else "Original acquired; current legal/2017 geography correspondence and detailed content pending."})
    for failure in manifest["failed_sources"]:
        data["sources"].append({"id": failure["id"], "name": "Bhutan 13th Five Year Plan official PDF",
            "url": failure["url"], "publisher": "Prime Minister's Office, Royal Government of Bhutan",
            "reference_period": "2024–2029 national plan, body not acquired",
            "geographic_level": "national framework; local-plan sections not inspected",
            "status": "failed", "retrieved_at": now,
            "license": "Official PDF location; terms unverified",
            "note": "Acquisition failed TLS peer verification. No certificate bypass and no plan body or number adopted."})
    data["analysis"]["comparisons"] = []
    for parent in ["BTN", *ids_by_source.values()]:
        children = [x["id"] for x in data["territories"] if x.get("parent_id") == parent]
        require(children, f"Missing comparison children {parent}")
        data["analysis"]["comparisons"].append({"parent_id": parent, "member_ids": children,
            "label": "PHCB 2017 nonoverlapping reporting rows",
            "membership_note": "District comparison uses town/Thromde urban rows and rural Gewog parts, excluding overlapping Urban/Rural subtotal rows. Local legal-government boundaries/codes are unverified.",
            "source_ids": [national_source, *[x["source_id"] for x in audit["districts"]]]})
    data["analysis"]["terminal_territory_ids"] = local_ids
    data["analysis"]["default_indicator_id"] = indicator_id("population")
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {"title": "Local plans and census evidence",
        "purpose": "Use selected census counts to diagnose a reporting area and then obtain the competent Dzongkhag, Gewog or Thromde's actual plan, budget, implementation and evaluation for its legal jurisdiction.",
        "system": {"label": "Bhutan local-government planning framework under current-edition review",
            "scope": "2017 census rural Gewog part and town rows are not proven to equal complete legal Gewog or Thromde boundaries.",
            "cycle": "2012 rules discuss Five Year and Annual Plans; present applicability and 13th FYP requirements require review",
            "source_ids": ["btn-phcb2017-local-government-rules-2012"]},
        "sections": [{"id": k, "label": v} for k, v in (
            ("plan", "Area-specific adopted plan"), ("budget", "Budget and allocations"),
            ("implementation", "Expenditure and implementation"),
            ("evaluation", "Official evaluation"), ("reference", "Census and planning references"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([
        *data["collection"].get("adapters", []), "nsb-phcb2017-table-a2-1-selected-counts"]))
    data["collection"]["notes"] = [
        "2017 PHCB district Table A2.1 selected direct population/sex counts; 20 district reports and national report acquired, other tables unassessed.",
        "Detailed-analysis national 727,145 excludes 8,408 hotel visitors from the all-found 735,553; the two are separate indicators.",
        *[x for x in data["collection"].get("notes", [])
          if not x.startswith(("Initial national-data site inputs only",
                               "2017 PHCB district Table A2.1 selected direct",
                               "Detailed-analysis national 727,145 excludes"))]]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "Twenty 2017 Dzongkhag reports and 269 town/rural Gewog-part rows are internally reconciled. The NSB BSSGC is December 2020 edition; 2017 code history and compatible official polygons are unverified.",
         "next_action": "Obtain 2017 codebook and dated official Dzongkhag, Gewog and Thromde polygons; match every source row and test cross-boundary towns."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Table A2.1 population and sex is adopted; 661 distinct numbered table headings across 20 district reports are inventoried, but other numeric fields remain priority_unassessed.",
         "next_action": "Audit the remaining tables' numeric fields, definitions and denominators, plus national annex and newer official local statistics."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "2012 local-government rules body is acquired, current force and requirements unreviewed; 13th FYP PDF failed TLS verification. No jurisdiction-specific adopted plan, budget, expenditure or evaluation is connected.",
         "next_action": "Reacquire the 13th FYP through a verifiable official channel, review current rules and obtain matching local plan/fiscal bodies."},
    ])
    data["generated_at"] = now
    dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    direct = [x for x in data["observations"] if x["indicator_id"].startswith(PREFIX)]
    require(len(direct) == 871 and len(data["territories"]) == 290,
            f"Unexpected direct counts {len(direct)}")
    result = {"selected_table": "A2.1", "territories": 290, "districts": 20,
        "towns": 64, "rural_gewog_parts": 205, "selected_indicators": 4,
        "direct_observations": len(direct), "other_numbered_table_headings": 661 - 20,
        "detailed_analysis_population": 727145, "all_found_population": 735553,
        "hotel_visitor_difference": 8408, "official_compatible_polygons": 0,
        "independent_acceptance": False, "dataset_sha256": digest(dataset_path.read_bytes())}
    (project / "evidence/BTN_IMPORT_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

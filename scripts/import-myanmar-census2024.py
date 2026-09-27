"""Adopt DOP 2024 Table A-1 state/region breakdown with explicit estimation status."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("conventional_both", "conventional_male", "conventional_female",
          "institution_both", "institution_male", "institution_female",
          "estimated_both", "estimated_male", "estimated_female",
          "total_both", "total_male", "total_female")


def require(condition, message):
    if not condition:
        raise ValueError(message)


PREFIX = "MMR_DOP24_"
SOURCE_XLSX = "mmr-dop-census2024-demographic-appendix"
SOURCE_PDF = "mmr-dop-census2024-union-report"
SOURCE_PLAN = "mmr-moi-plan-coordination-2026-27"
ROSTER = "DOP 2024 census Table A-1 state/region reporting rows; official code/polygon not verified"
STATE_NAMES = {"Kachin", "Kayah", "Kayin", "Chin", "Mon", "Rakhine", "Shan"}
REGION_NAMES = {"Sagaing", "Tanintharyi", "Bago", "Magway", "Mandalay", "Yangon", "Ayeyawady"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(project):
    manifest = json.loads((ROOT / "config/myanmar-census2024-source-manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/MMR_CENSUS2024_AUDIT.json").read_text(encoding="utf-8"))
    require(audit["source_sha256"] == manifest["sources"][0]["sha256"] and
            audit["report_sha256"] == manifest["sources"][1]["sha256"] and
            audit["adopted_observations"] == 240 and len(audit["areas"]) == 16,
            "Pinned DOP 2024 audit changed")
    path = project / "data/dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "MMR", "Expected Myanmar candidate")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data["territories"] = [t for t in data["territories"] if t["id"] == "MMR"]
    data["territories"][0].update({"boundary_version": ROSTER, "source_id": SOURCE_XLSX})
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["country"]["geography_note"] = (
        "DOP 2024 census reports 15 state/region-equivalent areas, including Nay Pyi Taw. "
        "Table A-1 does not publish the official administrative code for these reporting rows. "
        "The initial 2019 geoBoundaries set had only 14 shapes and an unresolved naming/edition mismatch; "
        "it is removed rather than joined by name. 2024 totals combine enumerated and statistically "
        "estimated people; 2024 census and WDI estimates are separate series.")
    data["sources"] = [s for s in data["sources"] if not s["id"].startswith("mmr-")]
    names = {SOURCE_XLSX: "2024 Census Appendix Tables, Demographic Characteristics (Excel)",
             SOURCE_PDF: "The 2024 Myanmar Population and Housing Census, Union Report",
             "mmr-dop-census2024-provisional": "2024 Population and Housing Census Provisional Results",
             SOURCE_PLAN: "Coordination meeting on national and local plans for FY2026-27"}
    for source in manifest["sources"]:
        item = {"id": source["id"], "name": names[source["id"]],
                "url": source["url"], "publisher": "Department of Population, Myanmar"
                if source["id"] != SOURCE_PLAN else "Ministry of Information, Myanmar",
                "reference_period": "2024 census, 30 September 2024 reference time"
                if source["id"] != SOURCE_PLAN else "FY2026-27 planning coordination; published 2025-09-12",
                "geographic_level": "Union, state/region; other levels in unassessed tables"
                if source["id"] != SOURCE_PLAN else "national and Region/State discussion only",
                "status": "ready", "retrieved_at": manifest["retrieved_at"],
                "sha256": source["sha256"], "raw_path": source["raw_path"],
                "license": "Official public source; reuse terms not yet verified",
                "note": source["scope"]}
        if source.get("catalogue_url"):
            item["catalogue_url"] = source["catalogue_url"]
        data["sources"].append(item)
    data["sources"].append({"id": "mmr-cso-2023-admin-units-location",
        "name": "Statistical Yearbook 2023 Part 1, Table 1.11 Administrative Units",
        "url": "https://www.csostat.gov.mm/FileUpload/cso/FileDownload/SYB%202023%20%28Part-1%29.pdf",
        "publisher": "Central Statistical Organization, Myanmar; General Administration Department table source",
        "reference_period": "31 March 2023 administrative count",
        "geographic_level": "Union and 15 state/region-level units, district/township counts",
        "status": "partial", "retrieved_at": manifest["retrieved_at"],
        "license": "Official public location; raw PDF and terms unverified",
        "note": "Official indexed Table 1.11 locates GAD administrative-unit counts, not the 2024 code register or an exact census boundary crosswalk. Body not acquired for this candidate."})
    for source_id, title, url, period, note in [
        ("mmr-dop-census2024-main-excel-catalogue", "DOP 2024 Main Report Excel catalogue",
         "https://www.dop.gov.mm/en/data-and-maps-category/2024-main-report-excel",
         "2024 census, English Union appendices released March 2026",
         "Official catalogue lists demographic, housing, education, migration, labour and disability Excel appendices. Only the demographic body is acquired/audited here."),
        ("mmr-dop-census2024-state-excel-catalogue", "DOP 2024 State/Region Reports Excel catalogue",
         "https://www.dop.gov.mm/en/data-and-maps-category/2024-stateregion-reports-excel",
         "2024 census, some English state/region appendices released June 2026",
         "Official catalogue location for state/region workbooks; individual geographic and indicator coverage, files and terms are not acquired in this candidate."),
        ("mmr-dop-census2014-data-catalogue", "DOP 2014 Census Excel Data catalogue",
         "https://www.dop.gov.mm/en/data-and-maps-category/2014-census-data",
         "2014 census data catalogue",
         "Official older census table catalogue; no historical code/definition crosswalk or 2014 value is adopted into the 2024 DOP series."),
    ]:
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": "Department of Population, Myanmar", "reference_period": period,
            "geographic_level": "Union and source-specific subnational tables",
            "status": "partial", "retrieved_at": manifest["retrieved_at"],
            "license": "Official public location; item terms unverified", "note": note})
    data["indicators"] = [i for i in data["indicators"] if not i["id"].startswith(PREFIX)]
    data["observations"] = [o for o in data["observations"]
                            if not o["indicator_id"].startswith(PREFIX)]
    labels = {"conventional": "enumerated conventional-household population",
              "institution": "enumerated institutional population",
              "estimated": "statistically estimated population for un-enumerated areas",
              "total": "combined enumerated and estimated population"}
    sex_labels = {"both": "both sexes", "male": "male", "female": "female"}
    for field in FIELDS:
        group, sex = field.split("_", 1)
        data["indicators"].append({"id": PREFIX + field.upper(),
            "name": f"2024 census {labels[group]}, {sex_labels[sex]}",
            "theme": "Population", "unit": "people", "display_decimals": 0,
            "definition": "DOP Table A-1, 30 September 2024 reference time. "
                "The 2024 census combines field enumeration in accessible areas with statistical "
                "estimation in areas not canvassed; these components are kept separate. "
                "See the enumerated and estimated percentages before comparing areas. "
                "Not harmonised with WDI, 2014 census or administrative registration.",
            "population": "People present in Myanmar at the 2024 census reference time; "
                + labels[group], "source_id": SOURCE_XLSX, "aggregation": "none",
            "measurement_method": ("2024_census_statistical_estimate" if group == "estimated" else
                                   "2024_census_enumerated_plus_estimated" if group == "total" else
                                   "2024_census_field_enumeration")})
    for key, name, unit, definition in [
        ("ENUMERATED_BOTH", "2024 census directly enumerated population", "people",
         "DOP Union Report Tables 2.2 and 3.1; conventional-household plus institutional enumeration."),
        ("ENUMERATED_PCT", "2024 census directly enumerated share", "percent",
         "Published one-decimal DOP Table 2.2 share of directly enumerated persons in the combined 2024 population."),
        ("ESTIMATED_PCT", "2024 census statistically estimated share", "percent",
         "Published one-decimal DOP Table 2.2 share estimated for areas not canvassed. This is not an uncertainty interval."),
    ]:
        data["indicators"].append({"id": PREFIX + key, "name": name,
            "theme": "Population", "unit": unit, "display_decimals": 1 if unit == "percent" else 0,
            "definition": definition + " Coverage differs sharply across states/regions; "
                "do not read the combined total as a uniform direct count.",
            "population": "2024 DOP census Union or state/region reporting area",
            "source_id": SOURCE_PDF, "aggregation": "none",
            "measurement_method": "source_reported_2024_census_coverage"})

    member_ids = []
    for area in audit["areas"]:
        country = area["name"] == "Myanmar"
        tid = "MMR" if country else f"MMR:DOP2024:A1:R{area['source_row']}"
        if not country:
            kind = ("State" if area["name"] in STATE_NAMES else "Region"
                    if area["name"] in REGION_NAMES else "Union Territory")
            data["territories"].append({"id": tid, "name": area["name"],
                "level": "adm1", "type": kind, "parent_id": "MMR",
                "official_code": None,
                "code_system": "DOP 2024 Table A-1 source row ID; official administrative code not published in this table",
                "provider_code": f"A1:R{area['source_row']}",
                "boundary_version": ROSTER, "source_id": SOURCE_XLSX,
                "reconciliation_status": "DOP reporting row verified; official code, polygon and legal planning jurisdiction unjoined"})
            member_ids.append(tid)
        for col, field in enumerate(FIELDS, 2):
            group = field.split("_", 1)[0]
            dash = group == "estimated" and area["source_dash_is_zero"]
            data["observations"].append({"territory_id": tid,
                "indicator_id": PREFIX + field.upper(), "period": "2024",
                "value": area["fields"][field], "status": "observed",
                "source_id": SOURCE_XLSX,
                "measurement_method": ("2024_census_statistical_estimate" if group == "estimated" else
                                       "2024_census_enumerated_plus_estimated" if group == "total" else
                                       "2024_census_field_enumeration"),
                "population_scope": labels[group],
                "provenance": "calculated" if dash else "source_reported",
                "boundary_version": ROSTER,
                "source_locator": f"Table A-1!{chr(64 + col)}{area['source_row']}" +
                    (" (source dash; zero reconciled with Union Report Table 2.2 p.15)" if dash else "")})
        for key, value, locator in [
            ("ENUMERATED_BOTH", area["enumerated_both"], "Tables 2.2 p.15 and 3.1 p.18"),
            ("ENUMERATED_PCT", area["enumerated_pct"], "Table 2.2 p.15"),
            ("ESTIMATED_PCT", area["estimated_pct"], "Table 2.2 p.15"),
        ]:
            data["observations"].append({"territory_id": tid,
                "indicator_id": PREFIX + key, "period": "2024", "value": value,
                "status": "observed", "source_id": SOURCE_PDF,
                "measurement_method": "source_reported_2024_census_coverage",
                "population_scope": "DOP 2024 combined census population",
                "provenance": "source_reported", "boundary_version": ROSTER,
                "source_locator": f"Union Report {locator}, {area['name']} row"})
    require(len(data["territories"]) == 16 and len(member_ids) == 15 and
            sum(o["indicator_id"].startswith(PREFIX) for o in data["observations"]) == 240,
            "Expected country plus 15 areas and 240 observations")
    data["documents"] = [d for d in data["documents"] if not d["id"].startswith("mmr-")]
    data["documents"].extend([
        {"id": SOURCE_PLAN, "territory_id": "MMR", "category": "reference",
         "kind": "planning_reference", "title": "FY2026-27 national/local plan coordination report",
         "url": next(s["url"] for s in data["sources"] if s["id"] == SOURCE_PLAN),
         "source_id": SOURCE_PLAN, "period": "FY2026-27", "availability": "body_acquired",
         "official_status": "unverified",
         "note": "Official coordination news body acquired. It is not a plan, legal competence instrument, approved budget, implementation record or official evaluation."},
        {"id": SOURCE_PDF, "territory_id": "MMR", "category": "reference",
         "kind": "census_reference", "title": "2024 Population and Housing Census Union Report",
         "url": next(s["url"] for s in data["sources"] if s["id"] == SOURCE_PDF),
         "source_id": SOURCE_PDF, "period": "2024", "availability": "body_acquired",
         "official_status": "unverified",
         "note": "Census evidence only. Section 2.8 warns state/region confidence varies with direct enumeration share."},
    ])
    data["planning"] = {"title": "Local planning evidence",
        "purpose": "Use the selected area census breakdown as a baseline while obtaining the responsible authority's actual plan, budget, implementation and evaluation documents.",
        "system": {"label": "Myanmar national and local plan coordination",
            "scope": "The acquired FY2026-27 official coordination report names Union ministries and Region/State governments. Formal planning competence, township role and current legal requirements remain unverified.",
            "cycle": "FY2026-27 coordination was reported; a binding local plan cycle and approved forms have not been established.",
            "source_ids": [SOURCE_PLAN]},
        "sections": [{"id": key, "label": label} for key, label in (
            ("plan", "Local plans"), ("budget", "Approved budgets"),
            ("implementation", "Implementation and actual expenditure"),
            ("evaluation", "Official evaluation"), ("reference", "Census and planning references"))]}
    data["analysis"]["comparisons"] = [{"parent_id": "MMR", "member_ids": member_ids,
        "label": "DOP 2024 census state/region reporting rows",
        "membership_note": "All 15 Table A-1 reporting rows are non-overlapping and each count component sums to the Union. Published state/region enumeration shares vary greatly and must not be averaged into the Union share. Source row IDs are not official administrative codes or approved planning jurisdictions; no 2019 provider polygon is joined.",
        "source_ids": [SOURCE_XLSX, SOURCE_PDF]}]
    data["analysis"]["terminal_territory_ids"] = []
    data["analysis"]["default_indicator_id"] = PREFIX + "TOTAL_BOTH"
    data["analysis"]["population_context"] = {
        "primary_indicator_id": PREFIX + "TOTAL_BOTH",
        "reference_indicator_id": "SP.POP.TOTL",
    }
    data["analysis"]["latest_values_only"] = True
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
        "dop-census-2024-table-a1-state-region"]))
    data["collection"]["notes"] = [
        "DOP 2024 Union Report and demographic workbook acquired and hash-pinned. Table A-1 12 fields plus Union Report three coverage fields yield 15 indicators and 240 observations across Union and 15 state/region-equivalent rows.",
        "Field enumeration covered 152 of 330 townships fully, 120 partially and 58 not at all; 32,183,599 people enumerated and 19,191,728 statistically estimated. State/region coverage differs substantially. A source dash is converted to zero only where total and Table 2.2 0.0% reconcile.",
        "The other 17 demographic appendix tables, including district/township Table A-2 and detailed characteristics, remain priority_unassessed. The separate provisional PDF is acquired but its different edition is not adopted.",
        "No 2024 official administrative code or matching polygon was acquired. The 2019 geoBoundaries set had 14 shapes, while the DOP table has 15 areas; its geometry is withheld. GAD 2023 unit counts are a location lead, not a code crosswalk.",
        "FY2026-27 national/local plan coordination article acquired. Local law, actual approved plans, budget, expenditure, evaluation and representative township-level records remain unacquired.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith((
            "Initial national-data site inputs only", "DOP 2024 Union Report",
            "Field enumeration covered", "The other 17 demographic appendix",
            "No 2024 official administrative code", "FY2026-27 national/local plan coordination"))],
    ]
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "DOP Table A-1 gives fifteen reporting names but no official area codes. The initial 2019 geoBoundaries set has fourteen shapes and is withheld; no exact 2024 polygon crosswalk is established.",
         "next_action": "Obtain dated DOP/GAD administrative code and boundary editions, then join all 15 reporting areas by verified code and version."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Fifteen Table A-1 coverage and population fields are adopted for Union plus 15 state/region-equivalent areas. The other 17 appendix tables, including district/township and demographic detail, remain priority_unassessed; the 2024 provisional edition is separate.",
         "next_action": "Audit Table A-2 district/township identities, all remaining numerical columns and subject tables, with code/coverage/definition checks before any finer-grained adoption."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Official FY2026-27 coordination news is acquired, but legal planning competence, actual current plan, budgets, implementation and evaluation are not verified for any selected area.",
         "next_action": "Acquire current legal instruments and representative Region/State plus township plan/budget/actual/evaluation bodies; verify publisher, period, territory and official status."},
    ])
    failed_wdi = {g["source_id"]: g for g in data["gaps"]
                  if g["category"] == "source_collection" and g["status"] == "failed"
                  and g.get("source_id", "").startswith("wb-")}
    for gap in data["gaps"]:
        if gap["category"] == "indicator_coverage" and gap.get("source_id") in failed_wdi:
            gap["status"] = "failed"
            gap["detail"] = "WDI fetch failed; values and country availability remain unknown, not zero or absent."
            gap["next_action"] = failed_wdi[gap["source_id"]]["next_action"]
    data["generated_at"] = now
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]), "indicators_added": 15,
              "observations_added": 240, "official_compatible_polygons": 0,
              "independent_acceptance": False,
              "observations_by_indicator": dict(Counter(o["indicator_id"] for o in data["observations"]
                                                        if o["indicator_id"].startswith(PREFIX))),
              "dataset_sha256": sha(path)}
    (project / "evidence/MMR_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

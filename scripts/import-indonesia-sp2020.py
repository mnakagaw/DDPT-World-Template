"""Import BPS SP2020 Table 1 direct population counts without a current-code join."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BPS_MANIFEST = ROOT / "config/indonesia-sp2020-source-manifest.json"
PLANNING_MANIFEST = ROOT / "config/indonesia-planning-source-manifest.json"
PREFIX = "IDN_SP2020_"
PERIOD = "2020"
BOUNDARY = "BPS SP2020 Table 1 2020 reporting codes; dated official polygons and current Kemendagri crosswalk unverified"
SCOPE = "SP2020 residents: domicile in Indonesia for at least one year, or less than one year with intent to remain at least one year"
METHOD = "BPS SP2020 Table 1 direct census count by 2020 reporting area and sex"
FIELDS = {"population": "Resident population, 2020 census count",
          "male": "Male resident population, 2020 census count",
          "female": "Female resident population, 2020 census count"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def tid(code):
    return "IDN:SP2020:" + code


def iid(field):
    return PREFIX + field.upper()


def add_observations(data, territory_id, row, source_id, locator):
    for field in FIELDS:
        value = row["fields"][field]
        require(isinstance(value, int) and value >= 0, f"Invalid Table 1 count {territory_id} {field}")
        data["observations"].append({"territory_id": territory_id, "indicator_id": iid(field),
            "period": PERIOD, "value": value, "status": "observed", "source_id": source_id,
            "measurement_method": METHOD, "population_scope": SCOPE,
            "provenance": "source_reported", "boundary_version": BOUNDARY,
            "source_locator": f"BPS Table 1 {locator}, HTML table row {row['row']}, {field} original count column"})


def main(project):
    bps = json.loads(BPS_MANIFEST.read_text(encoding="utf-8"))
    planning = json.loads(PLANNING_MANIFEST.read_text(encoding="utf-8"))
    audit = json.loads((project / "evidence/IDN_SP2020_TABLE1_AUDIT.json").read_text(encoding="utf-8"))
    require(len(bps["source_pages"]) == 35 and len(audit["provinces"]) == 34 and
            audit["district_count"] == 514 and
            audit["original_numeric_cells_including_duplicated_totals"] == 1749,
            "Unexpected BPS source scope")
    require(set(audit["fields"]) == set(FIELDS), "Unexpected BPS Table 1 fields")
    for item in [*bps["source_pages"], *planning["sources"]]:
        body = (project / item["raw_path"]).read_bytes()
        require(len(body) == item["bytes"] and digest(body) == item["sha256"],
                f"Original changed: {item['id']}")
    data_path = project / "data/dashboard.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "IDN", "Expected Indonesia candidate")
    data["territories"] = [x for x in data["territories"] if x["id"] == "IDN"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["territories"][0]["boundary_version"] = BOUNDARY
    data["territories"][0]["reconciliation_status"] = "SP2020 country scope; current administrative register and compatible polygons unverified"
    data["country"]["geography_note"] = (
        "BPS 2020 census Table 1 has 34 province reporting rows and 514 kabupaten/kota reporting rows. "
        "Its historical two/four-digit source codes and 2020 population counts are distinct from the later Kemendagri register, "
        "current legal planning jurisdictions, the 2017 geoBoundaries shapes and World Bank annual estimates. "
        "No official dated subnational polygons are joined.")
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("idn-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("idn-")]

    national = audit["country"][-1]
    require(national["name"] == "TOTAL" and national["fields"] == bps["national_total"],
            "National BPS source total changed")
    add_observations(data, "IDN", national, "idn-bps-sp2020-table1-national", "national TOTAL")
    provinces = audit["country"][:-1]
    province_by_code = {x["code"]: x for x in provinces}
    require(len(province_by_code) == 34 and len(audit["provinces"]) == 34,
            "Province inventory changed")
    comparisons = [{"parent_id": "IDN", "member_ids": [tid(row["code"]) for row in provinces],
        "label": "BPS SP2020 34-province statistical reporting partition",
        "membership_note": "All 34 direct BPS Table 1 province rows reconcile with the 2020 country total in each of three count columns. This is not a present-day legal province register.",
        "source_ids": ["idn-bps-sp2020-table1-national"]}]
    district_count = 0
    for source in audit["provinces"]:
        code = source["parent_code"]
        prow = province_by_code[code]
        require(source["parent_name"] == prow["name"] and
                source["rows"][-1]["fields"] == prow["fields"],
                f"BPS province page disagrees with national Table 1 row {code}")
        pid = tid(code)
        data["territories"].append({"id": pid, "name": prow["name"],
            "level": "census_province_2020", "type": "BPS SP2020 province reporting row",
            "parent_id": "IDN", "official_code": code,
            "code_system": "BPS SP2020 Table 1 two-digit source code; current Kemendagri equivalence unverified",
            "boundary_version": BOUNDARY, "source_id": "idn-bps-sp2020-table1-national",
            "reconciliation_status": "2020 BPS census code, not a confirmed current province polygon or legal register entry"})
        add_observations(data, pid, prow, "idn-bps-sp2020-table1-national", f"province {code}")
        members = []
        for row in source["rows"][:-1]:
            dcode = row["code"]
            require(dcode.startswith(code), f"District outside province {dcode}")
            did = tid(dcode)
            members.append(did)
            district_count += 1
            data["territories"].append({"id": did, "name": row["name"],
                "level": "census_kabupaten_kota_2020", "type": "BPS SP2020 kabupaten/kota reporting row; legal subtype unverified",
                "parent_id": pid, "official_code": dcode,
                "code_system": "BPS SP2020 Table 1 four-digit source code; current Kemendagri equivalence unverified",
                "boundary_version": BOUNDARY, "source_id": source["source_id"],
                "reconciliation_status": "2020 BPS reporting area; kabupaten versus kota legal subtype and current polygon unverified"})
            add_observations(data, did, row, source["source_id"], f"province {code} district/city {dcode}")
        for field in FIELDS:
            require(sum(row["fields"][field] for row in source["rows"][:-1]) == prow["fields"][field],
                    f"BPS province child coverage mismatch {code} {field}")
        comparisons.append({"parent_id": pid, "member_ids": members,
            "label": f"BPS SP2020 kabupaten/kota reporting rows within {prow['name']}",
            "membership_note": "All direct BPS Table 1 child counts reconcile to this 2020 province row for male, female and total. Current legal type and official polygon crosswalk are unverified.",
            "source_ids": [source["source_id"], "idn-bps-sp2020-table1-national"]})
    require(district_count == 514 and len(data["territories"]) == 549,
            "Unexpected imported reporting area count")

    for field, name in FIELDS.items():
        data["indicators"].append({"id": iid(field), "name": name, "theme": "Population",
            "unit": "people", "definition": f"BPS 2020 Census Table 1 direct count. {SCOPE}. Census reference year 2020; distinct from WDI midyear estimates and later administrative population registers.",
            "population": SCOPE, "source_id": "idn-bps-sp2020-table1-national",
            "aggregation": "none", "display_decimals": 0, "measurement_method": METHOD})
    for item in bps["source_pages"]:
        data["sources"].append({"id": item["id"],
            "name": "BPS SP2020 Table 1 country" if item["level"] == "national" else
                    f"BPS SP2020 Table 1 province {item['id'][-2:]}",
            "url": item["url"], "publisher": "Badan Pusat Statistik (BPS)",
            "reference_period": "2020 census", "geographic_level":
                "country and province" if item["level"] == "national" else "kabupaten/kota within one 2020 province",
            "status": "ready", "raw_path": item["raw_path"], "sha256": item["sha256"],
            "retrieved_at": item["retrieved_at"], "license": "Official public HTML; reuse terms unverified",
            "note": "Table 1 original male, female and total numeric columns inspected and adopted; other SP2020 table families remain priority_unassessed."})
    for item in planning["sources"]:
        data["sources"].append({"id": item["id"],
            "name": {"idn-bps-sp2020-population-catalogue": "BPS SP2020 population dataset catalogue",
                     "idn-surabaya-jdih-permendagri-86-2017-page": "Surabaya JDIH Permendagri 86/2017 record",
                     "idn-permendagri-86-2017-surabaya-copy": "Permendagri 86/2017 PDF, Surabaya JDIH copy",
                     "idn-jabar-official-plan-catalogue": "Jawa Barat official 2025 plan catalogue"}[item["id"]],
            "url": item["url"], "publisher": "BPS" if "bps" in item["id"] else
                         "Pemerintah Provinsi Jawa Barat" if "jabar" in item["id"] else
                         "JDIH Pemerintah Kota Surabaya (hosted copy of Ministry of Home Affairs regulation)",
            "reference_period": "2020 census catalogue" if "bps" in item["id"] else
                                "2025 plan catalogue" if "jabar" in item["id"] else "2017 regulation",
            "geographic_level": "national" if "bps" in item["id"] or "permendagri" in item["id"] else "Jawa Barat province",
            "status": "partial", "raw_path": item["raw_path"], "sha256": item["sha256"],
            "retrieved_at": item["retrieved_at"], "license": "Official public material; reuse terms unverified",
            "note": "Original body acquired; selected provisions inspected, current amended law and full guidance not yet audited." if "permendagri" in item["id"] else
                    "Catalogue body acquired; other SP2020 datasets unassessed." if "bps" in item["id"] else
                    "Official archive listing acquired; linked RPJMD PDF body not acquired."})
    for item in planning["unacquired_leads"]:
        data["sources"].append({"id": item["id"],
            "name": "Jawa Barat RPJMD 2025–2029 JDIH record" if "jabar" in item["id"] else "Kemendagri 2025 administrative-code decision PDF",
            "url": item["url"], "publisher": "JDIH Pemerintah Provinsi Jawa Barat" if "jabar" in item["id"] else "Kementerian Dalam Negeri",
            "reference_period": "2025–2029" if "jabar" in item["id"] else "2025 code edition",
            "geographic_level": "Jawa Barat province" if "jabar" in item["id"] else "national administrative register",
            "status": "partial", "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "license": "Official location only; source body not acquired",
            "note": item["status"] + "; retrieved_at is the source-location metadata check, not a body retrieval; source body and full meaning unverified."})
    now = datetime.now(timezone.utc).isoformat()
    law = next(x for x in planning["sources"] if x["id"] == "idn-permendagri-86-2017-surabaya-copy")
    data["documents"].append({"id": law["id"], "territory_id": "IDN", "category": "reference",
        "kind": "planning_regulation", "title": "Permendagri 86/2017 — regional development planning, control and evaluation",
        "url": law["url"], "source_id": law["id"], "period": "2017 regulation",
        "availability": "body_acquired", "official_status": "unverified",
        "note": "644-page Surabaya JDIH copy of a Ministry of Home Affairs regulation. Cover and selected definitions/provisions inspected (PDF pages 1, 5–7, 15–16). Current amendment status, all forms and province/kabupaten/kota application remain to be audited; not a local approved plan.",
        "territory_match": {"territory_id": "IDN", "country_id": "IDN", "type": "country",
            "official_code": None, "code_system": "World Bank economy code", "boundary_version": BOUNDARY,
            "method": "National regulation reference; applies as legal research context without asserting a subnational plan",
            "source_id": law["id"], "locator": "PDF cover and selected pages 5–7, 15–16",
            "checked_at": now[:10]}})
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = [tid(row["code"]) for source in audit["provinces"] for row in source["rows"][:-1]]
    data["analysis"]["default_indicator_id"] = iid("population")
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {"title": "Regional development planning and source evidence",
        "purpose": "Use 2020 census reporting counts as a historical baseline while verifying current province and kabupaten/kota planning jurisdictions, their plans, budgets, implementation and evaluation.",
        "system": {"label": "Indonesia RPJPD, RPJMD and RKPD under Permendagri 86/2017",
            "scope": "The 2017 regulation discusses province and kabupaten/kota regional planning, with BAPPEDA coordination. BPS 2020 statistical codes are not yet confirmed against current legal planning units.",
            "cycle": "2017 rule defines RPJPD as 20 years, RPJMD as five years and RKPD as one year; current amendments and local implementing documents remain under review.",
            "source_ids": ["idn-permendagri-86-2017-surabaya-copy"]},
        "sections": [{"id": key, "label": label} for key, label in (
            ("plan", "Area-specific RPJPD/RPJMD"), ("budget", "RKPD and budget"),
            ("implementation", "Expenditure and implementation"),
            ("evaluation", "Official evaluation"), ("reference", "Census and legal references"))]}
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []),
                                                             "bps-sp2020-table1-selected-direct-counts"]))
    data["collection"]["notes"] = [
        "BPS SP2020 Table 1: 35 official HTML originals, 34 province and 514 kabupaten/kota reporting rows; three count columns adopted. Four other listed population table families priority_unassessed.",
        "All three selected numeric columns reconcile district→province→country; no 2020-compatible official polygons or current Kemendagri code crosswalk acquired.",
        "Permendagri 86/2017 body archived from Surabaya JDIH; Jawa Barat RPJMD 2025–2029 official location found but PDF body not acquired and is not attached as a verified local plan.",
        *[x for x in data["collection"].get("notes", []) if not x.startswith((
            "Initial national-data site inputs only", "BPS SP2020 Table 1:",
            "All three selected numeric columns reconcile", "Permendagri 86/2017 body archived"))]]
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "BPS 2020 two/four-digit source codes and internal parent coverage checked. Current Kemendagri code decision body timed out; dated official census-compatible polygons and legal subtype crosswalk unverified.",
         "next_action": "Acquire historical and current official code/polygon editions, reconcile province and kabupaten/kota types, and inspect Papua splits before any shape or legal-unit join."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "Three direct Table 1 count fields adopted for 2020 country, 34 provinces and 514 kabupaten/kota rows. Four other population catalogue tables and other SP2020 themes remain priority_unassessed.",
         "next_action": "Inventory all national and territorial SP2020 table families, then review original numeric columns, definitions, denominators and geography before adoption."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Permendagri 86/2017 PDF body acquired and selected provisions inspected. Jawa Barat 2025–2029 RPJMD legal metadata and plan catalogue located but PDF body unavailable locally; no matching budget, expenditure or evaluation bodies acquired.",
         "next_action": "Obtain current amendments and Jawa Barat RPJMD body, then region-specific RPJMD/RKPD/APBD, expenditure and evaluation originals; confirm each plan's legal jurisdiction and code before attaching."},
    ])
    data["generated_at"] = now
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"territories": len(data["territories"]), "provinces": 34, "kabupaten_kota_reporting_rows": district_count,
              "indicators": len(FIELDS), "direct_observations": 3 * len(data["territories"]),
              "census_population": national["fields"]["population"], "official_compatible_polygons": 0,
              "law_pdf_pages": law["pages"], "independent_acceptance": False,
              "dataset_sha256": digest(data_path.read_bytes())}
    (project / "evidence/IDN_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

"""Import selected direct counts from the pinned official 2011 India PCA workbook.

The source's 2011 state/UT and district codes are a historical statistical
hierarchy. They are intentionally not joined to current LGD units or polygons.
"""

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


_inventory = runpy.run_path(str(Path(__file__).with_name("inventory-india-census2011.py")))
EXPECTED_HASH = _inventory["EXPECTED_HASH"]
SELECTED_TOTAL_FIELDS = _inventory["SELECTED_TOTAL_FIELDS"]
audit = _inventory["audit"]
load = _inventory["load"]
require = _inventory["require"]


PREFIX = "IND_CENSUS2011_"
SOURCE_ID = "ind-orgi-pca2011-state-district"
METHOD = "ORGI_2011_primary_census_abstract_direct_count"
PERIOD = "2011"
BOOK_URL = "https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/DDW_PCA0000_2011_Indiastatedist.xlsx"
BOOK_CATALOGUE = "https://censusindia.gov.in/nada/index.php/catalog/6191"
DOCS = [
    ("ind-mopr-pdp-2026-27", "Preparation of Panchayat Development Plan booklet 2026-27",
     "https://cdnbbsr.s3waas.gov.in/s316026d60ff9b54410b3435b403afd226/uploads/2026/05/202607211776250416.pdf",
     "raw/mopr-panchayat-development-plan-2026-27.pdf", "1fead200a14afc2c68b8aeddf3548f1f03eab4b36dbf44e105016309cc4bc b61".replace(" ", ""),
     "88-page rural Panchayat planning guidance; chapters 3-4 address GPDP, Block and District Panchayat plans. It does not identify the legal plan and coverage for each 2011 census district."),
    ("ind-mopr-egramswaraj-2026-27", "Panchayat planning FY 2026-27: eGramSwaraj prerequisites and updates",
     "https://cdnbbsr.s3waas.gov.in/s316026d60ff9b54410b3435b403afd226/uploads/2026/07/20260702740329884.pdf",
     "raw/mopr-egramswaraj-prerequisites-2026-27.pdf", "dce9dd23a817e60b0f360f280155058a0f6940c54b24050ca42141be7c1895db",
     "Three-page guidance lists plan preparation, Panchayat profile validation, resource envelope and budget allocation; it proves no particular area's plan or expenditure."),
    ("ind-census2027-notification", "Gazette notification for Census of India 2027",
     "https://censusindia.gov.in/nada/index.php/catalog/45572/download/49769/GAZ_NOTIFICATION_07.pdf",
     "raw/census2027-gazette-notification.pdf", "2310d16519452ef20ccdf e6224e2a64a69bcb9f998c2eb87ec6832f51c14d61e".replace(" ", ""),
     "Gazette dated 16 June 2025 sets future census reference dates; it provides no 2027 census results."),
    ("ind-constitution-2025", "Constitution of India, Articles 243G and 243W",
     "https://www.legislative.gov.in/static/uploads/2025/07/359f70a69695affb9d72f8393102bd2e.pdf",
     "raw/constitution-of-india-2025.pdf", "485d637c268bd079cf07a81e7a1df05ea785e3effda167a4f19699e97279ee50",
     "Legislative Department text: printed pp. 122 (Article 243G, Panchayats) and 130 (Article 243W, Municipalities); PDF pp. 301 and 317. State legislation may endow planning powers; this national text alone does not establish each state/local body's actual powers, plan status or geography."),
]


def tid(level, state, district):
    if level == "India":
        return "IND"
    if level == "STATE":
        return f"IND:ORGI2011:STATE:{state}"
    return f"IND:ORGI2011:DIST:{state}:{district}"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field_meta(field, tru):
    if field == "No_HH":
        return "2011 census households", "Households", "households", "Source No_HH count of households."
    if field == "TOT_P" and tru == "Rural":
        return "2011 rural population", "Population", "people", "Source TOT_P in the Rural reporting row."
    if field == "TOT_P" and tru == "Urban":
        return "2011 urban population", "Population", "people", "Source TOT_P in the Urban reporting row."
    labels = {
        "TOT_P": ("total population", "Population"), "TOT_M": ("male population", "Population"),
        "TOT_F": ("female population", "Population"),
        "P_06": ("population age 0–6", "Population"), "M_06": ("male population age 0–6", "Population"),
        "F_06": ("female population age 0–6", "Population"),
        "P_SC": ("Scheduled Caste population", "Population"),
        "M_SC": ("male Scheduled Caste population", "Population"),
        "F_SC": ("female Scheduled Caste population", "Population"),
        "P_ST": ("Scheduled Tribe population", "Population"),
        "M_ST": ("male Scheduled Tribe population", "Population"),
        "F_ST": ("female Scheduled Tribe population", "Population"),
        "P_LIT": ("literate persons", "Literacy"),
        "M_LIT": ("literate males", "Literacy"),
        "F_LIT": ("literate females", "Literacy"),
        "TOT_WORK_P": ("total workers", "Work"),
        "TOT_WORK_M": ("male workers", "Work"),
        "TOT_WORK_F": ("female workers", "Work"),
        "MAINWORK_P": ("main workers", "Work"),
        "MARGWORK_P": ("marginal workers", "Work"),
        "NON_WORK_P": ("non-workers", "Work"),
    }
    label, theme = labels[field]
    return f"2011 census {label}", theme, "people", f"Direct count in official PCA field {field}, Total reporting row; not a rate or current estimate."


def run(project):
    fields, entries, workbook_hash = load(project)
    grouped, checks, _ = audit(fields, entries)
    require(workbook_hash == EXPECTED_HASH, "PCA source hash differs")
    audit_file = project / "evidence/IND_ORGI_PCA2011_AUDIT.json"
    require(audit_file.exists(), "Run the full field inventory before import")
    inventory = json.loads(audit_file.read_text(encoding="utf-8"))
    require(inventory["source_sha256"] == workbook_hash and inventory["numeric_cells"] == 172380,
            "Full source inventory differs")
    for _, _, _, path, expected, _ in DOCS:
        require(sha256(project / path) == expected, f"Official PDF changed: {path}")
    now = datetime.now(timezone.utc).isoformat()
    receipts = []
    for url, relative, expected in [(BOOK_URL, "raw/DDW_PCA0000_2011_Indiastatedist.xlsx", workbook_hash),
                                    *[(item[2], item[3], item[4]) for item in DOCS]]:
        raw_file = project / relative
        receipts.append({"source_url": url, "raw_path": relative, "sha256": expected,
                         "bytes": raw_file.stat().st_size,
                         "saved_at_utc": datetime.fromtimestamp(raw_file.stat().st_mtime, timezone.utc).isoformat(),
                         "transfer_status": "downloaded_with_curl_fail_on_http_error",
                         "note": "Saved timestamp is local file metadata; server Last-Modified/ETag not captured."})
    catalog = project / "raw/censusindia-catalog-6191.html"
    if catalog.exists():
        receipts.append({"source_url": BOOK_CATALOGUE, "raw_path": str(catalog.relative_to(project)).replace('\\','/'),
                         "sha256": sha256(catalog), "bytes": catalog.stat().st_size,
                         "saved_at_utc": datetime.fromtimestamp(catalog.stat().st_mtime, timezone.utc).isoformat(),
                         "transfer_status": "saved_catalogue_html"})
    (project / "evidence/SOURCE_RECEIPTS.json").write_text(
        json.dumps({"recorded_at_utc": now, "receipts": receipts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    data_file = project / "data/dashboard.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "IND", "Expected an India candidate")
    data["territories"] = [x for x in data["territories"] if x["id"] == "IND"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["indicators"] = [x for x in data["indicators"] if not x["id"].startswith(PREFIX)]
    data["observations"] = [x for x in data["observations"] if not x["indicator_id"].startswith(PREFIX)]
    data["sources"] = [x for x in data["sources"] if not x["id"].startswith("ind-")]
    data["documents"] = [x for x in data["documents"] if not x["id"].startswith("ind-")]
    data["country"]["geography_note"] = (
        "Official 2011 Primary Census Abstract uses the 2011 state/UT and district hierarchy: 35 state/UT rows "
        "and 640 district rows. The 2027 census has been notified but has not supplied these results. "
        "Current LGD units, split states, Gram/Block/District Panchayats and census 2011 districts are not "
        "crosswalked. No source-compatible official polygon is joined. WDI estimates remain a separate series.")
    state_keys = sorted(key for key in grouped if key[0] == "STATE")
    dist_keys = sorted(key for key in grouped if key[0] == "DISTRICT")
    require(len(state_keys) == 35 and len(dist_keys) == 640, "2011 area ledger changed")
    for level, state, district in [*state_keys, *dist_keys]:
        source_row = grouped[(level, state, district)]["Total"]
        code = state if level == "STATE" else district
        data["territories"].append({
            "id": tid(level, state, district), "name": source_row["name"] + " (2011 census)",
            "level": "state_ut_2011" if level == "STATE" else "district_2011",
            "type": "census_state_or_ut" if level == "STATE" else "census_district",
            "parent_id": "IND" if level == "STATE" else tid("STATE", state, "000"),
            "official_code": code, "code_system": "ORGI Census 2011 State" if level == "STATE" else "ORGI Census 2011 District within State",
            "boundary_version": "Census 2011 statistical geography; polygons not acquired", "source_id": SOURCE_ID,
            "reconciliation_status": "Official 2011 code and parent in PCA; current LGD/legal boundary not matched",
        })
    data["sources"].append({
        "id": SOURCE_ID, "name": "ORGI Census 2011 Primary Census Abstract, India/state/district",
        "url": BOOK_URL, "publisher": "Office of the Registrar General & Census Commissioner, India",
        "reference_period": PERIOD, "geographic_level": "India, 35 state/UT and 640 district census 2011 units",
        "status": "partial", "raw_path": "raw/DDW_PCA0000_2011_Indiastatedist.xlsx",
        "sha256": workbook_hash, "retrieved_at": now,
        "license": "Government census download; redistribution terms for original workbook need review",
        "note": f"Catalogue {BOOK_CATALOGUE}. All 85 numeric columns and 2028 data rows inventoried; 24 field/reporting-row combinations adopted, 231 unassessed. State and district codes are official for 2011, not current geography.",
    })
    for source_id, title, url, path, expected, note in DOCS:
        data["sources"].append({
            "id": source_id, "name": title, "url": url,
            "publisher": "Ministry of Panchayati Raj, India" if "mopr" in source_id else (
                "Legislative Department, Government of India" if source_id == "ind-constitution-2025"
                else "Office of the Registrar General & Census Commissioner, India"),
            "reference_period": "2026-27" if "mopr" in source_id else (
                "2025 source edition" if source_id == "ind-constitution-2025"
                else "2027 census notification (2025)"),
            "geographic_level": "rural Panchayat guidance" if "mopr" in source_id else "national",
            "status": "partial", "raw_path": path, "sha256": expected,
            "retrieved_at": now, "license": "Official government PDF; redistribution terms need review",
            "note": note,
        })
    for source_id, title, url, scope in (
        ("ind-orgi-census2011-administrative-atlas", "Census 2011 administrative atlas",
         "https://censusindia.gov.in/census.website/data/atlas", "2011 state/UT and district reference maps; body not acquired"),
        ("ind-orgi-population-finder", "Census Population Finder / Basic Population Figures catalogue",
         "https://censusindia.gov.in/census.website/en/data/population-finder", "district, subdistrict, village, town and ward indicator locations; bodies not acquired"),
        ("ind-lgd-download", "Local Government Directory download catalogue",
         "https://lgdirectory.gov.in/demo/downloadDirectory.do", "current administrative and Panchayat code files; current-to-2011 crosswalk not acquired"),
        ("ind-mopr-egramswaraj", "eGramSwaraj official planning portal information",
         "https://panchayat.gov.in/en/e-gramswaraj/", "plan, progress and accounting location only; no area plan body acquired"),
    ):
        data["sources"].append({"id": source_id, "name": title, "url": url,
            "publisher": "Ministry of Panchayati Raj, India" if "mopr" in source_id or "lgd" in source_id else "Office of the Registrar General & Census Commissioner, India",
            "reference_period": "2026 location check", "geographic_level": scope,
            "status": "not_collected", "retrieved_at": now,
            "license": "Catalogue location only; terms of exact body need review",
            "note": "Location identified; no source body or geographic mapping adopted."})
    adopted = [(field, "Total") for field in SELECTED_TOTAL_FIELDS] + [("TOT_P", "Rural"), ("TOT_P", "Urban")]
    for field, tru in adopted:
        name, theme, unit, definition = field_meta(field, tru)
        iid = PREFIX + field + ("_" + tru.upper() if tru != "Total" else "")
        data["indicators"].append({
            "id": iid, "name": name, "theme": theme, "unit": unit,
            "definition": definition, "population": "2011 Indian census PCA reporting population / households",
            "source_id": SOURCE_ID, "aggregation": "none", "measurement_method": METHOD,
            "series_family": "census", "display_decimals": 0,
        })
        col = fields.index(field) + 1
        for level, state, district in [("India", "00", "000"), *state_keys, *dist_keys]:
            row = grouped[(level, state, district)][tru]
            observation = {
                "territory_id": tid(level, state, district), "indicator_id": iid,
                "period": PERIOD, "value": row["values"][field], "status": "observed",
                "source_id": SOURCE_ID, "measurement_method": METHOD,
                "source_locator": f"Sheet1!R{row['row']}C{col}; Level={level}; State={state}; District={district}; TRU={tru}; field={field}",
                "provenance": "source_reported",
            }
            if level != "India":
                observation["boundary_version"] = "Census 2011 statistical geography; polygons not acquired"
            data["observations"].append(observation)
    comparisons = [{
        "parent_id": "IND", "member_ids": [tid(*key) for key in state_keys],
        "label": "35 states and Union Territories in Census 2011",
        "membership_note": "Complete nonoverlapping 2011 PCA state/UT reporting ledger. Do not equate with current states or LGD units.",
        "source_ids": [SOURCE_ID],
    }]
    for _, state, _ in state_keys:
        children = [key for key in dist_keys if key[1] == state]
        comparisons.append({
            "parent_id": tid("STATE", state, "000"), "member_ids": [tid(*key) for key in children],
            "label": f"Census 2011 districts of state/UT {state}",
            "membership_note": "Complete nonoverlapping 2011 PCA district reporting ledger for this state/UT. These are statistical units, not confirmed current District Panchayats.",
            "source_ids": [SOURCE_ID],
        })
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = [tid(*key) for key in dist_keys]
    data["analysis"]["default_indicator_id"] = PREFIX + "TOT_P"
    data["analysis"]["latest_values_only"] = True
    data["planning"] = {
        "title": "Panchayat planning source and census evidence",
        "purpose": "Use the selected 2011 census area for a historical diagnosis, then locate the competent current rural planning unit and its actual approved plan, budget, implementation and evaluation evidence.",
        "system": {
            "label": "Ministry of Panchayati Raj Panchayat Development Plan guidance and eGramSwaraj",
            "scope": "Gram, Block and District Panchayats in rural planning; state-specific and urban systems require separate verification. A 2011 census district is not automatically a District Panchayat.",
            "cycle": "FY 2026-27 guidance verified; area-specific plan period and status unverified",
            "source_ids": ["ind-constitution-2025", "ind-mopr-pdp-2026-27", "ind-mopr-egramswaraj-2026-27", "ind-mopr-egramswaraj"],
        },
        "sections": [
            {"id": "plan", "label": "Panchayat and applicable local plans"},
            {"id": "budget", "label": "Resource envelope and budgets"},
            {"id": "implementation", "label": "Implementation and expenditure"},
            {"id": "evaluation", "label": "Official evaluation"},
            {"id": "reference", "label": "Census, guidance and official source locations"},
        ],
    }
    for source_id, title, url, period in (
        ("ind-mopr-pdp-2026-27", DOCS[0][1], DOCS[0][2], "FY 2026-27"),
        ("ind-mopr-egramswaraj-2026-27", DOCS[1][1], DOCS[1][2], "FY 2026-27"),
        (SOURCE_ID, "Census 2011 PCA state/district historical reference", BOOK_CATALOGUE, PERIOD),
        ("ind-constitution-2025", DOCS[3][1], DOCS[3][2], "2025 source edition"),
    ):
        data["documents"].append({
            "id": source_id + "-reference", "territory_id": "IND", "category": "reference",
            "kind": "source_reference", "title": title, "url": url, "source_id": source_id,
            "period": period, "availability": "body_acquired", "official_status": "unverified",
            "note": "National guidance or historical statistics only; no area-specific plan, approval, budget or implementation status is inferred.",
        })
    data["documents"].append({
        "id": "ind-mopr-egramswaraj-location", "territory_id": "IND", "category": "reference",
        "kind": "plan_portal_location", "title": "eGramSwaraj: locate current Panchayat plans and progress",
        "url": "https://panchayat.gov.in/en/e-gramswaraj/", "source_id": "ind-mopr-egramswaraj",
        "period": "current portal location; exact plan period unverified", "availability": "link_verified",
        "official_status": "unverified", "note": "Area-specific plan bodies, approved status, fiscal evidence and geographic linkage have not been acquired.",
    })
    data["collection"]["status"] = "partial"
    data["collection"]["adapters"] = list(dict.fromkeys([*data["collection"].get("adapters", []), "orgi-pca2011-state-district-selected-counts"]))
    data["collection"]["notes"] = [
        "Official 2011 PCA state/district counts partially integrated; no current-code or boundary crosswalk, area plans or independent acceptance.",
        *[n for n in data["collection"].get("notes", []) if not n.startswith("Initial national-data site inputs only")],
    ]
    data["gaps"] = [g for g in data["gaps"] if g["category"] not in
                    {"boundary_reconciliation", "subnational_statistics", "planning_documents"}]
    data["gaps"].extend([
        {"category": "boundary_reconciliation", "status": "pending",
         "detail": "2011 ORGI state and district codes and complete source hierarchy are verified. No source-compatible official polygons or current LGD/2026 Panchayat crosswalk acquired. Historic Jammu & Kashmir and Andhra Pradesh units must not be merged with current units by name.",
         "next_action": "Acquire ORGI 2011 coded polygons and current LGD administrative/Panchayat codes, then audit split/merged units with time-specific correspondence."},
        {"category": "subnational_statistics", "status": "partial",
         "detail": "One official 2011 PCA workbook: 85 numeric fields × 2028 Total/Rural/Urban rows audited; 24 field/reporting-row combinations adopted for India, 35 states/UT and 640 districts. Other official village/subdistrict/ward source bodies and 231 field/reporting-row combinations remain unassessed; no 2027 result adopted.",
         "next_action": "Inventory the other official PCA and 2027 result releases as available; review definitions and source terms before adoption. Do not fill current areas with 2011 values."},
        {"category": "planning_documents", "status": "partial",
         "detail": "Constitution Articles 243G/243W and two national Ministry of Panchayati Raj FY 2026-27 guidance PDFs acquired; eGramSwaraj location verified. State-specific rural/urban laws and exact district, Block and Gram Panchayat plans, budgets, expenditure and evaluation bodies are unacquired.",
         "next_action": "Identify competent current rural or urban planning bodies by state and local unit; acquire exact approved plans, budgets, execution and evaluation with area/date/status and crosswalk evidence."},
    ])
    data["generated_at"] = now
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"source_sha256": workbook_hash, "audit_checks": checks,
              "territories": len(data["territories"]), "domestic_indicators": len(adopted),
              "domestic_observations": sum(o["indicator_id"].startswith(PREFIX) for o in data["observations"]),
              "comparison_sets": len(comparisons), "planning_guidance_pdfs": 2,
              "current_compatible_polygons": 0, "independent_acceptance": False}
    (project / "evidence/IND_IMPORT_RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    run(parser.parse_args().project)

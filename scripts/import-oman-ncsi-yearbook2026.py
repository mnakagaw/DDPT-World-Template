"""Import selected 2023-25 registered-population columns of NCSI Year Book 2026.

Table 7-2 is a registered-population series, not the 2020 eCensus. The PDF
has bilingual cells and wrapped English labels; every expected group and
six source numeric columns are checked before writing the country dataset.
"""

import argparse
import json
import re
import runpy
import subprocess
from datetime import datetime, timezone
from pathlib import Path


fetch = runpy.run_path(str(Path(__file__).with_name("fetch-oman-ncsi-yearbook2026.py")))
PDF_NAME, PDF_URL, PDF_SHA, digest = fetch["NAME"], fetch["URL"], fetch["SHA256"], fetch["digest"]
SOURCE = "omn-ncsi-yearbook2026-table7-2"
PREFIX = "OMN_NCSI_REG_"
YEARS = ("2025", "2024", "2023")
GOVS = [
    ("Muscat", 6), ("Dhofar", 10), ("Musandam", 4), ("Al Buraymi", 3),
    ("Ad Dakhliyah", 9), ("Al Batinah North", 6), ("Al Batinah South", 6),
    ("Ash Sharqiyah South", 5), ("Ash Sharqiyah North", 7),
    ("Adh Dhahirah", 3), ("Al Wusta", 4),
]
# Independent published Table 6-2 total-population columns, ordered 2025/24/23.
PUBLISHED_TOTALS = {
    "Muscat": (1532486, 1498521, 1455680),
    "Dhofar": (532897, 529574, 521266),
    "Musandam": (56002, 55150, 56800),
    "Al Buraymi": (135509, 135821, 130576),
    "Ad Dakhliyah": (570269, 560483, 555250),
    "Al Batinah North": (939746, 925163, 917546),
    "Al Batinah South": (585794, 566771, 545449),
    "Ash Sharqiyah South": (374962, 369528, 366501),
    "Ash Sharqiyah North": (321045, 321462, 315592),
    "Adh Dhahirah": (246823, 244373, 240529),
    "Al Wusta": (64024, 61226, 60413),
    "Sultanate Total": (5359557, 5268072, 5165602),
}
NAME_FIXES = {
    "AL Jabal Alakhdar": "Al Jabal Alakhdar",
    "Shalim wa juzor al Hallniyat": "Shalim wa Juzur al Hallniyat",
    "BidBid": "Bidbid",
    "Al khaburah": "Al Khaburah",
    "Wadi Al maawil": "Wadi Al Maawil",
    "Al qabil": "Al Qabil",
    "Wadi bani Khalid": "Wadi Bani Khalid",
    "Jaalan bani bu Hasan": "Jaalan Bani Bu Hasan",
    "Jaalan bani bu Ali": "Jaalan Bani Bu Ali",
}


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("governorate", ""))


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]+", "-", name.upper())).strip("-")


def area_id(gov, wilayat=None):
    return "OMN:NCSI25:GOV:" + slug(gov) + (":WILAYAT:" + slug(wilayat) if wilayat else "")


def read_pdf(path, output):
    result = subprocess.run(["pdftotext", "-layout", str(path), str(output)],
                            capture_output=True, text=True, timeout=180, check=False)
    if result.returncode or not output.exists():
        raise RuntimeError("Poppler pdftotext failed for pinned NCSI PDF: " + result.stderr[:300])
    return output.read_text(encoding="utf-8")


def parse_table72(pages):
    number = re.compile(r"(?<![\d,])\d{1,3}(?:,\d{3})*(?![\d,])")
    rows = []
    for page, first_label in ((36, "Muscat :-"), (37, "Al Batinah North")):
        body = pages[page - 1]
        if ("7-2" not in body[:700] and "7-2" not in body[:1200]) or "2025" not in body[:1200]:
            raise ValueError("NCSI Table 7-2 page anchor changed: " + str(page))
        started = False
        pending = ""
        partial = None
        for raw in body.splitlines():
            left = re.split(r"[\u0600-\u06ff\u202a-\u202e]", raw, maxsplit=1)[0].strip()
            if not started:
                if left.startswith(first_label):
                    started = True
                else:
                    continue
            if left == "Population" or left.startswith("Population "):
                break
            if not left:
                continue
            matches = list(number.finditer(left))
            nums = [int(match.group().replace(",", "")) for match in matches]
            fragment = left[:matches[0].start()].strip() if matches else left
            if len(nums) == 6:
                if partial:
                    raise ValueError("Unexpected numeric row after partial Table 7-2 row")
                rows.append({"page": page, "name": (pending + " " + fragment).strip(), "values": nums})
                pending = ""
            elif len(nums) == 2:
                if partial:
                    raise ValueError("Two adjacent partial Table 7-2 rows")
                partial = {"page": page, "name": (pending + " " + fragment).strip(), "values": nums}
                pending = ""
            elif len(nums) == 4 and partial:
                if fragment:
                    partial["name"] += " " + fragment
                partial["values"] += nums
                rows.append(partial)
                partial = None
            elif not nums:
                if rows and (rows[-1]["name"].startswith("Ash Sharqiyah") or rows[-1]["name"] == "Al Wusta") and fragment in ("South", "North", "Governorate :-"):
                    rows[-1]["name"] += " " + fragment
                else:
                    pending = (pending + " " + fragment).strip()
            else:
                raise ValueError(f"Unexpected numeric layout on PDF page {page}: {left}")
        if not started or pending or partial:
            raise ValueError(f"Incomplete Table 7-2 PDF page {page}: {pending}, {partial}")
    if len(rows) != 75 or norm(rows[-1]["name"]) != norm("Sultanate Total"):
        raise ValueError("Table 7-2 did not yield 11 governorates, 63 Wilayats and national")
    index = 0
    groups = []
    for gov, child_count in GOVS:
        parent = rows[index]
        if norm(parent["name"]) != norm(gov):
            raise ValueError("Governorate order/name changed at source row " + str(index) + ": " + parent["name"])
        children = rows[index + 1:index + 1 + child_count]
        if len(children) != child_count or any("Governorate" in child["name"] for child in children):
            raise ValueError("Wilayat membership changed: " + gov)
        for column in range(6):
            if sum(child["values"][column] for child in children) != parent["values"][column]:
                raise ValueError(f"Wilayat cover differs from {gov} in column {column}")
        groups.append((gov, parent, children))
        index += child_count + 1
    if index != len(rows) - 1:
        raise ValueError("Orphan or overlapping source row in Table 7-2")
    national = rows[-1]
    for column in range(6):
        if sum(parent["values"][column] for _, parent, _ in groups) != national["values"][column]:
            raise ValueError("Governorate cover differs from national in column " + str(column))
    for gov, parent, _ in groups + [("Sultanate Total", national, [])]:
        for offset, year in enumerate(YEARS):
            if sum(parent["values"][offset*2:offset*2+2]) != PUBLISHED_TOTALS[gov][offset]:
                raise ValueError("Table 6-2 independent total differs: " + gov + "/" + year)
    return groups, national


def main(project):
    raw = project / "raw" / "official" / PDF_NAME
    if not raw.exists() or digest(raw) != PDF_SHA:
        raise ValueError("Missing or changed official NCSI yearbook")
    evidence = project / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    text = read_pdf(raw, evidence / (PDF_NAME + ".txt"))
    pages = text.split("\f")
    if len(pages) < 346 or "5,359,557" not in pages[37]:
        raise ValueError("NCSI PDF page inventory or independent Table 8-2 2025 total changed")
    groups, national = parse_table72(pages)
    dataset_path = project / "data" / "dashboard.json"
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "OMN":
        raise ValueError("Expected Oman project")
    source_ids = {SOURCE, "omn-ecensus2020-portal", "omn-mjla-urban-planning-law2026",
                  "omn-mjla-governorates-system2022", "omn-mohup-onss",
                  "omn-mohup-structural-plan-catalog"}
    data["sources"] = [row for row in data["sources"] if row["id"] not in source_ids]
    data["indicators"] = [row for row in data["indicators"] if not row["id"].startswith(PREFIX)]
    data["observations"] = [row for row in data["observations"] if not row["indicator_id"].startswith(PREFIX)]
    data["territories"] = [row for row in data["territories"] if row["id"] == "OMN"]
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    data["country"]["geography_note"] = ("NCSI Statistical Year Book 2026 Table 7-2 reports registered population by nationality "
        "for 2023–2025 at year end: 11 governorates and 63 Wilayats. This administrative-registration series is "
        "not the 2020 eCensus or a midyear population projection. Wilayat rows fully cover their published "
        "governorate parent in each year/category. The seven 2023 geoBoundaries reference ADM1 shapes are "
        "unjoined; official code/boundary editions and lawful planning units need verification.")
    data["territories"][0]["source_id"] = SOURCE
    data["territories"][0]["reconciliation_status"] = "NCSI Table 7-2 national registration scope; WDI midyear series is separate"
    all_rows = [("OMN", "Sultanate Total", national, None)]
    comparisons = [{"parent_id": "OMN", "member_ids": [area_id(gov) for gov, _, _ in groups],
        "label": "NCSI 2023–2025 registered-population governorates", "source_ids": [SOURCE],
        "membership_note": "Eleven complete, non-overlapping yearbook governorate rows; same year-end registration definition. No provider boundary is substituted."}]
    for gov, parent, children in groups:
        gid = area_id(gov)
        data["territories"].append({"id": gid, "name": gov, "level": "ncsi_governorate",
            "type": "NCSI registered-population governorate", "parent_id": "OMN",
            "official_code": None, "code_system": "NCSI Year Book 2026 Table 7-2 source name; official code unverified",
            "boundary_version": None, "source_id": SOURCE,
            "reconciliation_status": "2023–2025 registration reporting row; current official polygon unverified"})
        all_rows.append((gid, gov, parent, None))
        member_ids = []
        for child in children:
            display = NAME_FIXES.get(child["name"], child["name"])
            wid = area_id(gov, display)
            data["territories"].append({"id": wid, "name": display, "level": "ncsi_wilayat",
                "type": "NCSI registered-population Wilayat", "parent_id": gid,
                "official_code": None, "code_system": "NCSI Year Book 2026 Table 7-2 source name; official code unverified",
                "boundary_version": None, "source_id": SOURCE,
                "reconciliation_status": "Direct 2023–2025 Wilayat nationality counts; 2020 eCensus/codes and current polygon not joined"})
            member_ids.append(wid)
            all_rows.append((wid, display, child, gov))
        comparisons.append({"parent_id": gid, "member_ids": member_ids,
            "label": f"NCSI registered-population Wilayats in {gov}", "source_ids": [SOURCE],
            "membership_note": "All Table 7-2 Wilayats sum exactly to this governorate by year and nationality. Statistical Wilayat is not asserted to be a legal plan maker."})
    indicator_specs = (
        ("OMANI", "Registered Omani population at year end", "Omani", "source_reported"),
        ("EXPATRIATE", "Registered expatriate population at year end", "Expatriate", "source_reported"),
        ("TOTAL", "Registered total population at year end", "Omani + Expatriate", "areadata_calculated"),
    )
    for suffix, title, category, method in indicator_specs:
        data["indicators"].append({"id": PREFIX + suffix, "name": title, "theme": "Population",
            "unit": "people", "definition": "NCSI year-end registered population by nationality in Table 7-2, not the 2020 eCensus or a midyear estimate. " +
                ("AreaData adds the mutually exclusive Omani and expatriate counts for the same source area and year; parent totals independently match published Table 6-2." if suffix == "TOTAL" else "Direct source category count."),
            "population": "People registered in the Sultanate of Oman in the selected NCSI year-end series",
            "source_id": SOURCE, "aggregation": "none", "measurement_method": method,
            "display_decimals": 0})
    for aid, display, row, gov in all_rows:
        for offset, year in enumerate(YEARS):
            expatriate, omani = row["values"][offset*2:offset*2+2]
            for suffix, value, category, method in (("OMANI", omani, "Omani", "source_reported"),
                                                    ("EXPATRIATE", expatriate, "Expatriate", "source_reported"),
                                                    ("TOTAL", omani + expatriate, "Omani + Expatriate", "areadata_calculated")):
                observation = {"territory_id": aid, "indicator_id": PREFIX + suffix,
                    "period": year, "value": value, "status": "observed", "source_id": SOURCE,
                    "measurement_method": method,
                    "source_locator": f"NCSI Statistical Year Book 2026, Table 7-2, PDF page {row['page']}, {row['name']}, {year} {category}"}
                if suffix == "TOTAL":
                    observation.update({"provenance": "calculated", "footnote":
                        f"AreaData: {omani:,} registered Omani + {expatriate:,} registered expatriate, same Table 7-2 row/year. "
                        "National/governorate result cross-checked with published Table 6-2."})
                data["observations"].append(observation)
    imported_observations = [row for row in data["observations"] if row["indicator_id"].startswith(PREFIX)]
    if len(data["territories"]) != 75 or len({row["id"] for row in data["territories"]}) != 75 or len(imported_observations) != 675:
        raise ValueError("NCSI territory or observation count changed")
    data["analysis"]["comparisons"] = comparisons
    data["analysis"]["terminal_territory_ids"] = sorted([aid for aid, _, _, gov in all_rows if gov])
    data["analysis"]["default_indicator_id"] = PREFIX + "TOTAL"
    data["analysis"]["latest_values_only"] = True
    data["analysis"].pop("population_context", None)
    data["sources"].append({"id": SOURCE, "name": "NCSI Statistical Year Book 2026, population Tables 6-2, 7-2 and 8-2",
        "url": PDF_URL, "publisher": "National Centre for Statistics and Information, Sultanate of Oman",
        "reference_period": "year-end 2023–2025", "geographic_level": "national, 11 governorates, 63 Wilayats",
        "status": "partial", "license": "terms_review_required", "raw_path": "raw/official/" + PDF_NAME,
        "sha256": PDF_SHA, "retrieved_at": datetime.fromtimestamp(raw.stat().st_mtime, timezone.utc).isoformat(),
        "note": "Selected Table 7-2 nationality counts adopted; Table 6-2 parent totals and Table 8-2 2025 national total cross-check. Other yearbook tables/fields unassessed. Statistical map limits are explicitly not official legal boundaries."})
    for ident, name, url, publisher, geography, note in [
        ("omn-ecensus2020-portal", "Oman eCensus 2020 portal", "https://www.ecensus.gov.om/", "National Centre for Statistics and Information", "2020 census; detailed dataset availability unassessed", "Location only. No 2020 population count or code edition imported; keep census distinct from annual registrations."),
        ("omn-mjla-urban-planning-law2026", "Royal Decree issuing the Urban Planning Law, 2026", "https://mjla.gov.om/decrees/ar/1/show/1453", "Ministry of Justice and Legal Affairs, Oman", "national law; local applicability to verify", "Official law location only. Consolidated text, commencement, plan maker, statutory duties and form not yet audited."),
        ("omn-mjla-governorates-system2022", "Royal Decree 36/2022 on Governorates System", "https://mjla.gov.om/laws/ar/1/show/186", "Ministry of Justice and Legal Affairs, Oman", "governorate governance", "Official legal location only. Do not infer Wilayat planning authority or approval from source title."),
        ("omn-mohup-onss", "Oman National Spatial Strategy overview", "https://oman.housing.gov.om/onss", "Ministry of Housing and Urban Planning, Oman", "national and governorate strategy", "Official overview only. Full approved plans, periods, implementation, investment and area decisions unacquired."),
        ("omn-mohup-structural-plan-catalog", "MoHUP structural-plans catalogue", "https://mohup.gov.om/en/projects", "Ministry of Housing and Urban Planning, Oman", "selected city plans; geographic matching to verify", "Official plan-location catalogue only. No selected-area plan text, status, budget, implementation or evaluation adopted."),
    ]:
        data["sources"].append({"id": ident, "name": name, "url": url, "publisher": publisher,
            "reference_period": "catalog checked 2026-09-26", "geographic_level": geography,
            "status": "not_collected", "license": "terms_review_required",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "note": note})
    data["gaps"] = [row for row in data["gaps"] if row["category"] not in ("subnational_statistics", "boundary_reconciliation", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial",
         "detail": "NCSI Year Book 2026 Table 7-2 has 2023–2025 year-end registration counts for all 11 governorates and 63 Wilayats by Omani/expatriate nationality. Selected fields are adopted; other yearbook fields, 2020 eCensus, current sector data and changing registration methods need review.",
         "next_action": "Inventory all yearbook numeric tables and eCensus datasets, inspect definitions and add compatible nonpopulation themes with denominators and source-period checks."},
        {"category": "boundary_reconciliation", "status": "partial",
         "detail": "No official code or year-compatible polygon has been reconciled to Table 7-2. Seven 2023 geoBoundaries ADM1 reference shapes cannot cover the 11 reported governorates and are unjoined. The NCSI yearbook itself cautions that its statistical map limits are not legal boundaries.",
         "next_action": "Obtain NCSI/official geographic codes and current boundary editions for 11 governorates and 63 Wilayats; review changes including Sinaw and Al Jabal Alakhdar."},
        {"category": "planning_documents", "status": "not_collected",
         "detail": "Urban Planning Law, Governorates System, national spatial strategy and selected structural-plan locations identified. Current applicable plan-making unit, full plan text, decisions, area budget, execution and evaluation remain unverified.",
         "next_action": "Audit current law and actual plan/decision/fiscal/performance bodies for contrasting governorates and Wilayats; do not equate registered-statistics geography with legal planning authority."},
    ]
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] + ["oman-ncsi-yearbook2026-table7-2-partial-v1"]))
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {"source_hash": PDF_SHA, "table72_pdf_pages": [36, 37], "table62_pdf_page": 34,
        "table82_pdf_page": 38, "source_numeric_fields": ["2025/2024/2023 expatriate", "2025/2024/2023 Omani"],
        "adopted_source_fields": 6, "published_parent_totals": PUBLISHED_TOTALS,
        "governorate_count": len(groups), "wilayat_count": sum(len(children) for _, _, children in groups),
        "source_rows": [{"page": row["page"], "name": row["name"], "values": row["values"]} for _, _, row, _ in all_rows],
        "national_2025": 5359557, "direct_category_observations": 450,
        "calculated_total_observations": 225,
        "remaining_yearbook_tables": "unassessed_not_adopted; no all-tables-checked claim",
        "eCensus2020": "location_only_not_imported"}
    (evidence / "OMN_NCSI_YEARBOOK_FIELD_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"territories": len(data["territories"]), "governorates": len(groups),
        "wilayats": audit["wilayat_count"], "indicators": 3,
        "direct_category_observations": 450, "calculated_total_observations": 225,
        "total_observations": 675, "national_2025": 5359557}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    main(Path(parser.parse_args().project))

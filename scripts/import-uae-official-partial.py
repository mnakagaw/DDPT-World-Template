"""Import audited UAE historical emirate counts and scoped 2024/plan records.

The 2005 publication supplies five census years; its 2017 provider polygons
remain navigation references. SCAD's 2024 register series is Abu Dhabi only.
"""

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


RAW = "raw/uae-official/"
FILES = {
    "figures": ("fcsc-uae-in-figures-2005.pdf", "a002de0ff995e521547b4b1e44c24787a307fd7745e1f1271fa47185df38b935"),
    # Presentation HTML changes between requests. The receipt pins the actual
    # downloaded body; the report's displayed values are checked below.
    "scad": ("scad-abu-dhabi-census-population-2024.html", None),
    "plan": ("dubai-2040-structure-plan-executive-summary.pdf", "a7b07b7e5529a79d50f4a0d0040149ab337125b90643dbfd6c9c0f713edd2b27"),
    "law": ("dubai-urban-planning-law-16-2023.pdf", "d012df3d4b11bdd2876eba9c0196e8817258b312bcb2e7580de7299a3df83859"),
}
NAMES = ("Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al-Quwain", "Ras Al-Khaimah", "Fujairah")
SOURCE_TO_PROVIDER = {name: name for name in NAMES}
SOURCE_TO_PROVIDER.update({"Umm Al-Quwain": "Umm al-Quwain", "Ras Al-Khaimah": "Ras al-Khaimah"})
YEARS = (2005, 1995, 1985, 1980, 1975)
TABLES = {
    "population": (4, "POPULATION BY EMIRATE", "ARE_FCSC_CENSUS_POP", "Census population by emirate", "people"),
    "urban": (5, "POPULATION IN URBAN", "ARE_FCSC_CENSUS_URBAN", "Census urban population by emirate", "people"),
    "rural": (6, "POPULATION IN RURAL", "ARE_FCSC_CENSUS_RURAL", "Census rural population by emirate", "people"),
    "buildings": (16, "BUILDINGS BY EMIRATE", "ARE_FCSC_CENSUS_BUILDINGS", "Census buildings by emirate", "buildings"),
}
SCAD_COUNTS = {"population": 4_135_985, "male": 2_767_060, "female": 1_368_925}
SCAD_REGIONS = {"Abu Dhabi": 2_823_340, "Al Ain": 986_910, "Al Dhafra": 325_735}


def pdf_page(path, page):
    return subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", "-enc", "UTF-8", str(path), "-"],
                          check=True, capture_output=True).stdout.decode("utf-8")


def checked_original(project, key):
    filename, expected_hash = FILES[key]
    relative = RAW + filename
    target = project / relative
    receipt = json.loads((project / (relative + ".receipt.json")).read_text(encoding="utf-8"))
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if (expected_hash is not None and actual != expected_hash) or receipt["sha256"] != actual or receipt["path"] != relative:
        raise ValueError(f"Source edition/receipt changed: {filename}")
    if key == "scad" and receipt["source_url"] != "https://census.scad.gov.ae/home/population?fid=0&lang=en&tab=webreport":
        raise ValueError("SCAD receipt URL changed")
    return target, receipt


def parse_census_table(path, page, heading):
    content = pdf_page(path, page)
    if heading not in content or "2005" not in content or "1995" not in content or "*CensusData" not in content.replace(" ", ""):
        raise ValueError(f"Expected census heading/year/footnote absent on PDF page {page}")
    content = "".join(ch for ch in content if unicodedata.category(ch) != "Cf")
    rows = []
    name_pattern = "|".join(re.escape(x) for x in NAMES)
    pattern = re.compile(r"^\s*(" + name_pattern + r"|TOTAL|Total)\s+((?:\d[\d,]*\s+){4}\d[\d,]*)")
    for line in content.splitlines():
        match = pattern.match(line)
        if match:
            values = tuple(int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", match.group(2)))
            rows.append((match.group(1), values))
        if len(rows) == 8:
            break
    if tuple(name for name, _ in rows[:7]) != NAMES or len(rows) != 8 or rows[7][0].lower() != "total":
        raise ValueError(f"Census region order or coverage changed on PDF page {page}")
    for index, year in enumerate(YEARS):
        if sum(values[index] for _, values in rows[:7]) != rows[7][1][index]:
            raise ValueError(f"Printed national sum mismatch on page {page}, {year}")
    return {name.upper() if name.lower() == "total" else name: values for name, values in rows}


def flat_html(path):
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", content, flags=re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", content)).split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "ARE" or any(source["id"] == "are-fcsc-census-figures-2005" for source in dataset["sources"]):
        raise ValueError("Expected unimproved UAE candidate")
    originals = {key: checked_original(project, key) for key in FILES}

    figures_path, figures_receipt = originals["figures"]
    census = {field: parse_census_table(figures_path, spec[0], spec[1]) for field, spec in TABLES.items()}
    if census["population"]["TOTAL"][0] != 4_106_427 or census["buildings"]["TOTAL"][0] != 336_815:
        raise ValueError("2005 census control totals changed")
    for name in (*NAMES, "TOTAL"):
        for index, year in enumerate(YEARS):
            if census["urban"][name][index] + census["rural"][name][index] != census["population"][name][index]:
                raise ValueError(f"Urban/rural decomposition differs: {name}, {year}")

    scad_text = flat_html(originals["scad"][0])
    for phrase in ("4,135,985 Abu Dhabi Emirate Population 2024", "Male 2,767,060", "Female 1,368,925",
                   "Abu Dhabi 2,595,390 2,823,340", "Al Ain 945,600 986,910", "Al Dhafra 306,595 325,735"):
        if phrase not in scad_text:
            raise ValueError(f"SCAD page content changed: {phrase}")
    if SCAD_COUNTS["male"] + SCAD_COUNTS["female"] != SCAD_COUNTS["population"] or \
            sum(SCAD_REGIONS.values()) != SCAD_COUNTS["population"]:
        raise ValueError("SCAD 2024 sex/region totals differ")

    plan_path, plan_receipt = originals["plan"]
    cover, plan_body, monitoring = (pdf_page(plan_path, page) for page in (1, 4, 30))
    if "Structure Plan" not in cover or "Executive Summary" not in cover or \
            "both Metropolitan Dubai and Hatta" not in plan_body or \
            "The Plan outlines quantitative key performance indicators" not in monitoring:
        raise ValueError("Dubai 2040 plan's checked pages changed")
    law_path, law_receipt = originals["law"]
    law_title, law_scope, law_end = (pdf_page(law_path, page) for page in (1, 6, 17))
    if "Law No. (16) of 2023" not in law_title or "all areas within the Emirate" not in law_scope or \
            "ninety (90) days" not in law_end:
        raise ValueError("Dubai law's checked pages changed")

    regions = {area["name"]: area for area in dataset["territories"] if area["parent_id"] == "ARE"}
    if set(regions) != set(SOURCE_TO_PROVIDER.values()) or len(dataset["boundaries"]["features"]) != 7:
        raise ValueError("Reference emirate coverage changed")
    now = datetime.now(timezone.utc).isoformat()
    source_specs = (
        ("are-fcsc-census-figures-2005", "U.A.E. in Figures 2005: census-by-emirate tables", "figures", "Federal Competitiveness and Statistics Centre", "1975, 1980, 1985, 1995, 2005", "country and seven emirates", "Four count tables are adopted; 2005 is historical and not comparable to WDI midyear estimates or SCAD 2024."),
        ("are-scad-abu-dhabi-census-2024", "Abu Dhabi Census 2024 population web report", "scad", "Statistics Centre - Abu Dhabi", "2024", "Abu Dhabi emirate; three named regions unadopted", "Register-based 2024 residents and sex counts are scoped to Abu Dhabi. Region values are audited but lack a matched official region boundary/code in this candidate."),
        ("are-dubai-2040-structure-plan", "Dubai 2040 Structure Plan executive summary", "plan", "Dubai Municipality", "2021-2040; PDF prepared June 2022", "Emirate of Dubai", "Selected pages reviewed: cover, PDF page 4 scope, PDF page 30 future implementation and monitoring. No completed performance result or budget execution adopted."),
        ("are-dubai-urban-planning-law-16-2023", "Dubai Law No. 16 of 2023 concerning urban planning", "law", "Dubai Legislation Portal", "2023 law; current amendment status unverified", "Emirate of Dubai", "Selected pages reviewed: title, Article 3 scope, Article 24 commencement. Gazette publication date and later amendments require follow-up."),
    )
    source_by_key = {}
    for source_id, title, key, publisher, period, level, note in source_specs:
        _, receipt = originals[key]
        source_by_key[key] = source_id
        dataset["sources"].append({"id": source_id, "name": title, "url": receipt["source_url"],
            "publisher": publisher, "reference_period": period, "geographic_level": level,
            "status": "ready", "retrieved_at": receipt["retrieved_at"], "sha256": receipt["sha256"],
            "raw_path": receipt["path"], "license": "terms_review_required", "note": note})

    crosswalk = []
    for name in NAMES:
        area = regions[SOURCE_TO_PROVIDER[name]]
        area["source_name_en"] = name
        area["reconciliation_status"] = "name_correspondence_only_2017_reference_boundary_unverified"
        crosswalk.append((name, area["name"], area["id"], area["provider_code"],
                          "name_correspondence_only; official_code_and_historical_boundary_unverified"))
    for field, (page, heading, indicator_id, label, unit) in TABLES.items():
        dataset["indicators"].append({"id": indicator_id, "name": label + " (1975-2005)",
            "theme": "Historical census population" if field != "buildings" else "Historical census buildings",
            "unit": unit, "definition": f"Printed {heading} count, 1975/1980/1985/1995/2005 census columns. This historical series is distinct from 2024 SCAD register statistics and WDI midyear estimates.",
            "population": "UAE census population by emirate" if field != "buildings" else "Buildings counted by UAE census",
            "source_id": source_by_key["figures"], "aggregation": "sum", "measurement_method": "source_reported",
            "series_family": "census", "display_role": "primary", "period_policy": "latest_available_per_indicator",
            "display_decimals": 0})
        for source_name in (*NAMES, "TOTAL"):
            area_id = "ARE" if source_name == "TOTAL" else regions[SOURCE_TO_PROVIDER[source_name]]["id"]
            for index, year in enumerate(YEARS):
                dataset["observations"].append({"territory_id": area_id, "indicator_id": indicator_id,
                    "period": str(year), "value": census[field][source_name][index], "status": "observed",
                    "measurement_method": "source_reported", "source_id": source_by_key["figures"],
                    "source_locator": f"PDF page {page}, {heading}, {source_name} row, {year} column"})
    for sex, number in SCAD_COUNTS.items():
        indicator_id = "ARE_SCAD_AD_CENSUS_2024_" + sex.upper()
        dataset["indicators"].append({"id": indicator_id, "name": f"Abu Dhabi register census 2024: {sex}",
            "theme": "Abu Dhabi census 2024", "unit": "people",
            "definition": f"SCAD 2024 register-based count of {sex} residents in Abu Dhabi emirate; differs in period and method from the historical federal census and WDI midyear estimates. Other emirates have no observation in this series.",
            "population": "Residents of Abu Dhabi emirate in the 2024 integrated administrative registers",
            "source_id": source_by_key["scad"], "aggregation": "none", "measurement_method": "source_reported",
            "series_family": "administrative", "display_role": "primary", "period_policy": "latest_available_per_indicator",
            "display_decimals": 0})
        dataset["observations"].append({"territory_id": regions["Abu Dhabi"]["id"],
            "indicator_id": indicator_id, "period": "2024", "value": number,
            "status": "observed", "measurement_method": "source_reported", "source_id": source_by_key["scad"],
            "source_locator": f"2024 Population web report, Abu Dhabi Emirate, {sex.title()}"})

    dubai = regions["Dubai"]
    for key, document_id, title, category, period, summary, locator in (
        ("plan", "are-dubai-2040-plan-summary", "Dubai 2040 Structure Plan — executive summary", "plan", "2021-2040",
         "Dubai Municipality's structure plan covers Metropolitan Dubai and Hatta. The checked monitoring page names preliminary KPIs and future implementation actions; it is not an implementation result or an expenditure report.",
         "PDF pages 1, 4 and 30 (printed pages 1, 6 and 56)"),
        ("law", "are-dubai-urban-planning-law-16-2023", "Dubai urban planning Law No. 16 of 2023", "reference", "2023",
         "The law applies to all areas within the Emirate of Dubai and describes the structure-plan governance. Its latest amendment and Gazette commencement record were not independently audited.",
         "PDF pages 1, 6 (Article 3) and 17 (Article 24)"),
    ):
        _, receipt = originals[key]
        record = {"id": document_id, "territory_id": dubai["id"], "category": category,
            "kind": "plan" if category == "plan" else "official-law-or-regulation", "title": title,
            "url": receipt["source_url"], "period": period,
            "availability": "content_verified", "official_status": "unverified", "source_id": source_by_key[key],
            "territory_match": {"territory_id": dubai["id"], "country_id": "ARE",
                "type": dubai["type"], "code_system": dubai["code_system"],
                "official_code": dubai["official_code"], "boundary_version": dubai["boundary_version"],
                "method": "The official document explicitly identifies the Emirate of Dubai; provider polygon remains a navigation reference without confirmed legal-boundary equivalence.",
                "source_id": source_by_key[key], "locator": locator, "checked_at": now},
            "content": {"summary": summary,
                        "evidence": {"source_id": source_by_key[key], "locator": locator,
                                     "checked_at": now, "authority": "Dubai Municipality" if key == "plan" else "Dubai Legislation Portal"}}}
        if category == "plan":
            record["target_period"] = {"label": period, "kind": "multi_year"}
        dataset["documents"].append(record)
    dataset["country"]["geography_note"] = (
        "Seven emirates are shown with 2017 geoBoundaries provider reference shapes. The federal 1975-2005 census counts were matched by name only; official codes and historical/current legal boundary equivalence are unverified. SCAD 2024 register counts cover Abu Dhabi only. Country WDI estimates are a separate midyear series.")
    for gap in dataset["gaps"]:
        if gap["category"] == "boundary_reconciliation":
            gap.update(status="partial", detail="Seven historical census emirate names correspond one-to-one to 2017 provider reference shapes. Official codes and boundary editions are not yet reconciled.",
                       next_action="Acquire official emirate and lower-area codes/dated boundaries, check historical changes, and verify SCAD region geography.")
        elif gap["category"] == "subnational_statistics":
            gap.update(status="partial", detail="Four 1975-2005 federal census count series cover seven emirates and nation; three register-based 2024 SCAD counts cover Abu Dhabi only. Other source tables and current figures for six emirates are unadopted.",
                       next_action="Audit current federal by-emirate vital/sector tables and six emirate statistics; verify source definitions and official region codes.")
        elif gap["category"] == "planning_documents":
            gap.update(status="partial", detail="Dubai 2040 plan executive summary and Dubai 2023 planning law have verified selected pages. No other emirate plan, budget, execution report or official evaluation is adopted.",
                       next_action="Review the whole Dubai plan, later law amendments, and other emirates' current plans, budget/execution and evaluation records.")
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
        ["uae-fcsc-1975-2005-census-emirates", "uae-scad-abu-dhabi-register-2024", "uae-dubai-planning-materials"]))
    dataset["analysis"]["latest_values_only"] = True
    dataset["generated_at"] = now
    evidence_dir = project / "evidence"
    with (evidence_dir / "ARE_SOURCE_NAME_CROSSWALK.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("official_table_name", "provider_name", "territory_id", "provider_shape_id", "status"))
        writer.writerows(crosswalk)
    (evidence_dir / "ARE_OFFICIAL_IMPORT_AUDIT.json").write_text(json.dumps({
        "status": "partial_candidate_not_accepted", "checked_at": now,
        "raw_sha256": {key: receipt["sha256"] for key, (_, receipt) in originals.items()},
        "adopted": {"federal_census_tables": list(TABLES), "years": YEARS, "emirates": len(NAMES),
                    "historical_observations": len(TABLES) * len(YEARS) * (len(NAMES) + 1),
                    "abu_dhabi_register_2024_observations": len(SCAD_COUNTS),
                    "dubai_documents": 2},
        "checks": ["Each census page's seven rows sum to its printed national total for every year",
                   "Every emirate/year's urban and rural counts sum to census total",
                   "SCAD male/female and three unadopted regions each sum to Abu Dhabi's 2024 total"],
        "unresolved": ["Official emirate codes and 2005/2017/current boundary correspondence",
                       "Six other emirates' recent comparable population counts", "SCAD region codes/boundaries",
                       "Full plan and law amendment audit", "Other emirate planning/budget/execution/evaluation",
                       "Source reuse terms and independent acceptance"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"historical_observations": 160, "scad_observations": 3,
                      "sources_added": 4, "documents_added": 2, "total_observations": len(dataset["observations"])}))


if __name__ == "__main__":
    main()

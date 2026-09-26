"""Import explicitly scoped UAE census 2005 and Abu Dhabi register 2023/24 values.

The federal 2005 census and SCAD administrative-register series are distinct;
the latter is not extrapolated to the other six emirates or the national total.
"""

import argparse
import hashlib
import html
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


PDF_NAME = "fcsc-uae-numbers-2009.pdf"
PDF_HASH = "7f23a54f8cae8857238db82539f5275adbe6dc362315267e2d2a9980083225db"
PDF_URL = "https://fcsc.gov.ae/wp-content/uploads/2025/04/%D8%A7%D9%84%D8%A5%D9%85%D8%A7%D8%B1%D8%A7%D8%AA-%D8%A8%D8%A7%D9%84%D8%A3%D8%B1%D9%82%D8%A7%D9%85-2009.pdf"
HTML_NAME = "scad-census-population-2024.html"
HTML_HASH = "887d84414ee37445ab5499f6315587b2d52662d42da959c8cfd903ee65560a70"
HTML_URL = "https://census.scad.gov.ae/home/population?fid=0&lang=en&tab=webreport"
SOURCE_PDF = "are-fcsc-2009-report-census-by-emirate"
SOURCE_SCAD = "are-scad-abu-dhabi-register-2024"
SOURCE_GOV = "are-government-local-governments"
SOURCE_PLAN = "are-government-dubai-2040-plan"
SOURCE_STAT = "are-fcsc-uaestat-population-explorer"
IND_2005 = "ARE_FCSC_CENSUS_2005_POP"
IND_SCAD = "ARE_SCAD_REGISTER_POP"
ROWS = ("Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al-Quwain", "Ras Al-Khaimah", "Fujairah")
CROSSWALK = {"Umm Al-Quwain": "Umm al-Quwain", "Ras Al-Khaimah": "Ras al-Khaimah"}


class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.table, self.row, self.cell = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table": self.table = []
        elif tag == "tr" and self.table is not None: self.row = []
        elif tag in ("th", "td") and self.row is not None: self.cell = ""

    def handle_data(self, data):
        if self.cell is not None: self.cell += data

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join(html.unescape(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def source(path, expected):
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    if value != expected: raise ValueError(f"Source hash changed: {path.name}: {value}")
    return path.stat().st_size


def census_page(path):
    text = subprocess.check_output(["pdftotext", "-f", "9", "-l", "9", "-layout", str(path), "-"]).decode("utf-8")
    text = "".join(ch for ch in unicodedata.normalize("NFKC", text) if unicodedata.category(ch) != "Cf")
    table = text.split("Population by Emirate", 1)[1].split("Percentage Distribution of Population by Emirate", 1)[0]
    result = {}
    for name in (*ROWS, "Total"):
        match = re.search(re.escape(name) + r"\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)", table)
        if not match: raise ValueError(f"FCSC table row missing: {name}")
        result[name] = dict(zip(("2005", "1995", "1985", "1975"), map(int, match.groups())))
    for year in ("2005", "1995", "1985", "1975"):
        if sum(result[name][year] for name in ROWS) != result["Total"][year]:
            raise ValueError(f"FCSC page 9 emirate census sum differs in {year}")
    if result["Total"]["2005"] != 4106427: raise ValueError("FCSC census anchor changed")
    return result


def scad_page(path):
    text = path.read_text(encoding="utf-8")
    parser = TableReader()
    parser.feed(text)
    candidates = [table for table in parser.tables if table and "2023 R1*" in table[0] and "2024" in table[0]]
    if len(candidates) != 1: raise ValueError("SCAD region table changed")
    table = candidates[0]
    rows = {}
    for row in table[1:]:
        if not row or row[0] not in ("Abu Dhabi", "Al Ain", "Al Dhafra"): continue
        rows[row[0]] = {"2023": int(row[1].replace(",", "")),
                        "2024": int(row[2].replace(",", "")),
                        "reported_change_pct": row[3], "reported_share_2024": row[4]}
    if set(rows) != {"Abu Dhabi", "Al Ain", "Al Dhafra"}: raise ValueError("SCAD region roster changed")
    total = 4135985
    if "4,135,985" not in text or sum(row["2024"] for row in rows.values()) != total:
        raise ValueError("SCAD 2024 emirate population mismatch")
    if any(row[year] % 5 for row in rows.values() for year in ("2023", "2024")):
        raise ValueError("SCAD rounded table identity changed")
    return {"emirate_2024": total, "regions": rows,
            "note": "SCAD 2024 integrated administrative registers; 2023 R1 revised. Region table rounded to multiples of five; percentages not adopted."}


def observation(territory, indicator, period, value, source_id, locator):
    return {"territory_id": territory, "indicator_id": indicator, "period": period,
            "value": value, "status": "observed", "measurement_method": "source_reported",
            "source_id": source_id, "source_locator": locator}


def main(project):
    raw = project / "raw" / "official"
    sizes = {PDF_NAME: source(raw / PDF_NAME, PDF_HASH), HTML_NAME: source(raw / HTML_NAME, HTML_HASH)}
    census, scad = census_page(raw / PDF_NAME), scad_page(raw / HTML_NAME)
    evidence = project / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "ARE_SOURCE_TABLE_AUDIT.json").write_text(json.dumps({
        "source_sizes": sizes, "source_sha256": {PDF_NAME: PDF_HASH, HTML_NAME: HTML_HASH},
        "fcsc_pdf_page_9": census, "scad_region_table": scad,
        "adopted": "FCSC 2005 count, SCAD 2023 R1 and 2024 region/emirate counts",
        "not_adopted": "FCSC 1975, 1985, 1995 numeric fields and other report pages; SCAD percentages, growth and other page tables remain unassessed"
    }, indent=2) + "\n", encoding="utf-8")
    path = project / "data" / "dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["country"]["id"] != "ARE": raise ValueError("Expected UAE project")
    data["territories"] = [x for x in data["territories"] if not x["id"].startswith("ARE:SCAD:")]
    data["indicators"] = [x for x in data["indicators"] if x["id"] not in (IND_2005, IND_SCAD)]
    data["observations"] = [x for x in data["observations"] if x["indicator_id"] not in (IND_2005, IND_SCAD)]
    data["sources"] = [x for x in data["sources"] if x["id"] not in (SOURCE_PDF, SOURCE_SCAD, SOURCE_GOV, SOURCE_PLAN, SOURCE_STAT)]
    emirates = {x["name"]: x for x in data["territories"] if x["parent_id"] == "ARE"}
    if len(emirates) != 7: raise ValueError("Reference emirate roster changed")
    obs = [observation("ARE", IND_2005, "2005", census["Total"]["2005"], SOURCE_PDF,
                       "FCSC UAE Numbers 2009 PDF p.9 / printed p.6, Population by Emirate, Total 2005")]
    for name in ROWS:
        area = emirates[CROSSWALK.get(name, name)]
        area["census_2005_source_name"] = name
        area["census_2005_match"] = "Name match to 2017 geoBoundaries reference only; no official 2005/current boundary certification"
        obs.append(observation(area["id"], IND_2005, "2005", census[name]["2005"], SOURCE_PDF,
                               f"FCSC UAE Numbers 2009 PDF p.9 / printed p.6, Population by Emirate, {name} 2005"))
    abu_id = emirates["Abu Dhabi"]["id"]
    obs.append(observation(abu_id, IND_SCAD, "2024", scad["emirate_2024"], SOURCE_SCAD,
                           "SCAD Abu Dhabi Census population page, 2024 emirate headline"))
    for name, row in scad["regions"].items():
        id_ = f"ARE:SCAD:REGION:{name.upper().replace(' ', '_')}"
        data["territories"].append({"id": id_, "country_id": "ARE", "parent_id": abu_id,
            "level": "statistical_region", "type": "SCAD statistical region", "name": name + " Region",
            "source_name": name, "official_code": None, "boundary_version": None,
            "source_id": SOURCE_SCAD, "reconciliation_status": "SCAD region label; official geographic code and boundary unverified"})
        for year in ("2023", "2024"):
            obs.append(observation(id_, IND_SCAD, year, row[year], SOURCE_SCAD,
                       f"SCAD Abu Dhabi Census population page, Population Distribution by Region 2024, {name}, {year + (' R1 revised' if year == '2023' else '')}"))
    data["indicators"] += [
        {"id": IND_2005, "name": "Population, 2005 federal census", "theme": "FCSC historical census",
         "unit": "people", "definition": "Persons in December 2005 federal census by emirate, as republished in FCSC UAE Numbers 2009. Historical, not current resident population.",
         "population": "Persons in the UAE 2005 census", "source_id": SOURCE_PDF,
         "aggregation": "sum", "measurement_method": "source_reported", "period_policy": "latest_available_per_indicator", "display_decimals": 0},
        {"id": IND_SCAD, "name": "Abu Dhabi register population, 2023 R1–2024", "theme": "SCAD administrative registers",
         "unit": "people", "definition": "SCAD Abu Dhabi emirate/three-region population from integrated administrative registers. 2023 R1 is revised; 2024 region values are disclosure-rounded to multiples of five. Not comparable as a UAE-wide emirate series.",
         "population": "Residents in Abu Dhabi's integrated administrative registers", "source_id": SOURCE_SCAD,
         "aggregation": "sum", "measurement_method": "source_reported", "period_policy": "latest_available_per_indicator", "display_decimals": 0}
    ]
    data["observations"] += obs
    stamp = datetime.now(timezone.utc).isoformat()
    def retrieved(filename): return datetime.fromtimestamp((raw / filename).stat().st_mtime, timezone.utc).isoformat()
    data["sources"] += [
        {"id": SOURCE_PDF, "name": "FCSC UAE Numbers 2009, Population by Emirate census table",
         "url": PDF_URL, "publisher": "Federal Competitiveness and Statistics Centre",
         "reference_period": "2005 federal census (report edition 2009)", "geographic_level": "national, emirate",
         "status": "ready", "retrieved_at": retrieved(PDF_NAME), "sha256": PDF_HASH,
         "raw_path": "raw/official/" + PDF_NAME, "license": "terms_review_required",
         "note": "Original 48-page official report; only the population-by-emirate table on PDF p.9/printed p.6 and its four year columns inspected. Only 2005 adopted; other pages not semantically audited."},
        {"id": SOURCE_SCAD, "name": "SCAD Abu Dhabi Census 2024 population and three-region table",
         "url": HTML_URL, "publisher": "Statistics Centre - Abu Dhabi",
         "reference_period": "2023 R1 revised; 2024 integrated administrative registers", "geographic_level": "Abu Dhabi emirate and three SCAD regions",
         "status": "partial", "retrieved_at": retrieved(HTML_NAME), "sha256": HTML_HASH,
         "raw_path": "raw/official/" + HTML_NAME, "license": "terms_review_required",
         "note": "Emirate headline and three-region population table inspected. Region counts rounded to multiples of five; no current cross-emirate equivalence or legal region code/boundary established."},
        {"id": SOURCE_GOV, "name": "UAE government description of seven emirates' local governments",
         "url": "https://u.ae/en/about-the-uae/the-uae-government/the-local-governments-of-the-seven-emirates",
         "publisher": "Official Portal of the UAE Government", "reference_period": "portal page, checked 2026-09-26",
         "geographic_level": "seven emirates; local structures differ", "status": "not_collected", "retrieved_at": stamp,
         "license": "terms_review_required", "note": "Source-location lead for emirate-specific executive councils and municipalities. It does not establish a uniform federal local-planning duty or selected-area plan status."},
        {"id": SOURCE_PLAN, "name": "UAE government overview of Dubai 2040 Urban Master Plan",
         "url": "https://u.ae/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/transport-and-infrastructure/dubai-2040-urban-master-plan",
         "publisher": "Official Portal of the UAE Government", "reference_period": "Dubai 2040 overview",
         "geographic_level": "Dubai emirate, urban planning areas", "status": "not_collected", "retrieved_at": stamp,
         "license": "terms_review_required", "note": "Overview lead, not the full plan, current implementation report, municipality budget or approval instrument. Obtain actual source documents before use."},
        {"id": SOURCE_STAT, "name": "FCSC UAE.Stat official population-estimate explorer",
         "url": "https://uaestat.fcsc.gov.ae/en", "publisher": "Federal Competitiveness and Statistics Centre",
         "reference_period": "national population series shown through 2024; emirate scope unverified",
         "geographic_level": "national in checked catalogue; subnational availability unverified",
         "status": "not_collected", "retrieved_at": stamp, "license": "terms_review_required",
         "note": "Official data-explorer lead. Its national population series is not automatically an all-emirate series; inspect dataflow, definitions, download format and subnational coverage before adoption."},
    ]
    data["country"]["geography_note"] = (
        "The seven emirate polygons are 2017 geoBoundaries navigation references; their source codes and borders are not certified as the 2005 census or current legal geography. Three Abu Dhabi regions are SCAD 2024 statistical labels without joined shapes or verified official codes. Federal 2005 census, Abu Dhabi 2024 administrative registers and WDI national estimates are separate series.")
    data["gaps"] = [x for x in data["gaps"] if x["category"] not in ("subnational_statistics", "planning_documents")]
    data["gaps"] += [
        {"category": "subnational_statistics", "status": "partial", "detail": "Federal 2005 census by seven emirates and SCAD 2024/2023 R1 Abu Dhabi three-region administrative register counts are available as separate non-comparable series. Current same-method statistics for all seven emirates, district-level data, official codes/boundaries and other source fields remain unadopted.",
         "next_action": "Inspect UAE.Stat and all emirate statistical centres, source methods and full tables; obtain current compatible emirate series and official territorial crosswalks."},
        {"category": "planning_documents", "status": "not_collected", "detail": "Government portal provides local-government structure and Dubai 2040 plan overview leads. No selected-area plan, budget, implementation or evaluation document has been content-verified.",
         "next_action": "For each emirate, verify relevant planning law, responsible body, actual plan and local budget/implementation/evaluation sources."}
    ]
    data["collection"]["adapters"] = sorted(set(data["collection"]["adapters"] + ["uae-fcsc-2005-scad-2024-partial"]));
    data["analysis"]["latest_values_only"] = True
    data["analysis"]["default_indicator_id"] = IND_2005
    data["analysis"]["population_context"] = {
        "primary_indicator_id": IND_2005, "reference_indicator_id": "SP.POP.TOTL",
        "reference_period": "2005",
        "note": "The December 2005 federal census (4,106,427) and World Bank's 2005 midyear estimate use different methods and reference dates. Their gap is not a source error or a local growth rate. SCAD 2024 uses a separate Abu Dhabi administrative-register method."
    }
    data["generated_at"] = stamp
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"federal_census_2005": len([x for x in obs if x["indicator_id"] == IND_2005]),
                      "scad_register": len([x for x in obs if x["indicator_id"] == IND_SCAD]),
                      "total_adopted_observations": len(obs), "scad_regions": len(scad["regions"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    main(Path(args.project))

"""Inventory NSB district-report tables and audit Table A2.1 direct counts.

The remaining numbered tables receive headings only and remain unassessed.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/bhutan-phcb2017-source-manifest.json"
ROW = re.compile(r"^\s*(\S.*?)\s{2,}([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")
TITLE = re.compile(r"(?m)^\s*Table A2\.1 Population by Sex and Gewog/Town[^\n]*2017\s*$")
NEXT = re.compile(r"(?m)^\s*Table A2\.2 Population by Age")
HEADINGS = re.compile(r"(?m)^\s*Table (A\d+\.\d+)\s+([^\n]+)")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def integer(value):
    return int(value.replace(",", ""))


def main(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = [x for x in manifest["source_files"] if x["id"].startswith("btn-phcb2017-district-")]
    require(len(files) == 20, "Expected twenty district reports")
    tables = []
    district_audits = []
    all_rows = []
    for source in files:
        path = project / source["raw_path"]
        require(path.exists() and path.stat().st_size == source["bytes"] and
                digest(path.read_bytes()) == source["sha256"], f"Original changed: {source['id']}")
        completed = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        text = completed.stdout
        starts = list(TITLE.finditer(text))
        require(starts, f"A2.1 not found: {source['id']}")
        start = starts[-1]
        after = NEXT.search(text, start.end())
        require(after, f"A2.2 not found after A2.1: {source['id']}")
        section = text[start.end():after.start()]
        label = source["id"].removeprefix("btn-phcb2017-district-")
        seen_tables = set()
        for heading in HEADINGS.finditer(text):
            if heading.group(1) in seen_tables:
                continue
            seen_tables.add(heading.group(1))
            tables.append({"source_id": source["id"], "table": heading.group(1),
                           "heading": heading.group(2).strip(),
                           "decision": "selected_numeric_audit" if heading.group(1) == "A2.1" else "priority_unassessed"})
        rows = []
        group = None
        first_page = text[:start.end()].count("\f") + 1
        for page_delta, page_text in enumerate(section.split("\f")):
            for line in page_text.splitlines():
                match = ROW.match(line)
                if not match:
                    continue
                name = match.group(1).strip()
                male, female, total = map(integer, match.group(2, 3, 4))
                require(male + female == total, f"Sex sum mismatch {source['id']} {name}")
                kind = "dzongkhag" if not rows else "subtotal" if name in {"Urban", "Rural"} else "town" if group == "Urban" else "gewog" if group == "Rural" else "unclassified"
                if name in {"Urban", "Rural"}:
                    group = name
                rows.append({"name": name, "kind": kind, "male": male, "female": female,
                             "population": total, "source_table": "A2.1",
                             "source_page_text_position": first_page + page_delta,
                             "source_line": line.rstrip(), "source_id": source["id"]})
        require(rows and rows[0]["kind"] == "dzongkhag", f"No district value: {source['id']}")
        require(sum(x["kind"] == "subtotal" for x in rows) == 2 and
                all(x["kind"] != "unclassified" for x in rows),
                f"Incomplete geography in {source['id']}: {[(x['name'],x['kind']) for x in rows]}")
        district = rows[0]
        urban, rural = (next(x for x in rows if x["name"] == kind) for kind in ("Urban", "Rural"))
        for field in ("male", "female", "population"):
            require(urban[field] + rural[field] == district[field], f"Urban/rural total {source['id']} {field}")
            require(sum(x[field] for x in rows if x["kind"] == "town") == urban[field],
                    f"Town total {source['id']} {field}")
            require(sum(x[field] for x in rows if x["kind"] == "gewog") == rural[field],
                    f"Gewog total {source['id']} {field}")
        district_audits.append({"source_id": source["id"], "slug": label,
                                "name": district["name"], "population": district["population"],
                                "towns": sum(x["kind"] == "town" for x in rows),
                                "gewogs": sum(x["kind"] == "gewog" for x in rows),
                                "table_headings": sum(x["source_id"] == source["id"] for x in tables)})
        all_rows += rows
    report = {"status": "table_a2_1_audited_other_tables_headings_only",
              "manifest_sha256": digest(MANIFEST.read_bytes()),
              "district_reports": len(files), "districts": district_audits,
              "table_headings": tables, "selected_rows": all_rows,
              "district_population_sum": sum(x["population"] for x in district_audits),
              "cautions": ["2017 census de facto population excludes tourists/non-Bhutanese found in hotels on census reference day per report table notes",
                           "Town, Thromde and Gewog source rows remain distinct; legal planning identity and 2017 official codes not yet matched",
                           "All A2.2 onward numeric fields remain priority_unassessed; headings are not field audit"]}
    target = project / "evidence/BTN_PHCB2017_AUDIT.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"districts": len(district_audits),
                      "selected_rows": len(all_rows),
                      "towns": sum(x["towns"] for x in district_audits),
                      "gewogs": sum(x["gewogs"] for x in district_audits),
                      "table_headings": len(tables),
                      "district_population_sum": report["district_population_sum"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    main(parser.parse_args().project)

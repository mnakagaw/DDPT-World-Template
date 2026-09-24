"""Screen every INSD statistical table for a reproducible numeric-column review.

This is a locator/triage inventory, not indicator adoption. A parsed number is
not comparable evidence until denominator, geography, period and meaning are
checked against the PDF page and a selected column is explicitly adopted.
"""
from collections import Counter
from pathlib import Path
import csv
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / "raw/insd-rgph-2019/statistical_tables.txt"
INVENTORY = ROOT / "evidence/SOURCE_TABLE_INVENTORY.csv"
OUT = ROOT / "evidence/TABLE_COLUMN_SCREEN.csv"
COL_OUT = ROOT / "evidence/TABLE_NUMERIC_COLUMN_CANDIDATES.csv"
DATA = json.loads((ROOT / "data/dashboard.json").read_text(encoding="utf-8"))
PRINTED_PAGE_DECISIONS = {
    "I.1": "reviewed_crosscheck_only",
    "I.2": "reviewed_deferred_collective_household_definition",
    "I.3": "reviewed_deferred_historical_comparability",
    "I.4": "reviewed_crosscheck_only",
    "I.5": "reviewed_crosscheck_only",
    "I.6": "reviewed_candidate_not_adopted_urban_rural_definition",
    "I.7": "reviewed_crosscheck_only",
    "V.23": "reviewed_deferred_migration_type_definition",
    "VI.5": "reviewed_crosscheck_only",
    "IX.23": "reviewed_deferred_unemployed_count_not_rate",
}


def key(value):
    return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", value)
                  .encode("ascii", "ignore").decode().upper())


regions = {key(area["name"]) for area in DATA["territories"] if area["level"] == "adm1"}
assert len(regions) == 13
with INVENTORY.open(encoding="utf-8-sig", newline="") as stream:
    inventory = list(csv.DictReader(stream))
assert len(inventory) == 581
raw_text = TEXT.read_text(encoding="utf-8")
lines = raw_text.splitlines()
page_by_line = []
page = 1
for line in raw_text.splitlines(keepends=True):
    page_by_line.append(page)
    page += line.count("\f")
assert len(page_by_line) == len(lines)
heading = re.compile(r"^\s*Tableau\s+([IVX]+\.\d+[A-Za-z]?)\s*:", re.I)
numeric = re.compile(r"(?<![A-Za-z])(?:\d{1,3}(?:[ .]\d{3})*|\d+)(?:,\d+)?(?![A-Za-z])")
anchors = [(i, match.group(1).upper()) for i, line in enumerate(lines)
           if page_by_line[i] >= 27 and (match := heading.match(line))]
by_id = {}
for index, table_id in anchors:
    by_id.setdefault(table_id, []).append(index)
all_ids = {row["table_id"].upper() for row in inventory}
assert all_ids <= set(by_id), sorted(all_ids - set(by_id))[:20]
assert set(PRINTED_PAGE_DECISIONS) <= all_ids

rows = []
column_rows = []
for item in inventory:
    table_id = item["table_id"].upper()
    starts = by_id[table_id]
    blocks = []
    for start in starts:
        end = next((i for i, other in anchors if i > start and other != table_id), len(lines))
        blocks.extend(lines[start + 1:end])
    sample = []
    region_hits = set()
    national_hits = 0
    numeric_rows = 0
    max_tokens = 0
    candidate_lines = []
    for line in blocks:
        tokens = numeric.findall(line)
        if len(tokens) >= 2:
            numeric_rows += 1
            max_tokens = max(max_tokens, len(tokens))
            candidate_lines.append((" ".join(line.strip().split()), tokens))
            if len(sample) < 2:
                sample.append(" ".join(line.strip().split())[:180])
        before = numeric.search(line)
        label = key(line[:before.start()] if before else line)
        if label in regions:
            region_hits.add(label)
        if label == "BURKINAFASO":
            national_hits += 1
    headers = [" ".join(line.strip().split()) for line in blocks[:14]
               if line.strip() and not numeric.search(line)]
    counts = Counter(len(tokens) for _, tokens in candidate_lines)
    modal_count = counts.most_common(1)[0][0] if counts else 0
    modal_lines = [(label, tokens) for label, tokens in candidate_lines if len(tokens) == modal_count]
    for position in range(modal_count):
        column_rows.append({
            "table_id": table_id,
            "first_pdf_page": page_by_line[starts[0]],
            "numeric_position_1_based": position + 1,
            "modal_numeric_tokens_in_line": modal_count,
            "matching_candidate_lines": len(modal_lines),
            "sample_values": " | ".join(tokens[position] for _, tokens in modal_lines[:3]),
            "sample_source_line": modal_lines[0][0][:200],
            "header_excerpt": " | ".join(headers[:3])[:250],
            "semantic_column_name": "unverified",
            "denominator": "unverified",
            "period_and_geography": "unverified",
            "adoption_decision": "see_printed_page_review; no_new_indicator_adopted" if table_id in PRINTED_PAGE_DECISIONS
                                 else "pending_printed_page_and_semantic_review",
        })
    rows.append({
        "table_id": table_id,
        "adoption_status": item["adoption_status"],
        "first_pdf_page": page_by_line[starts[0]],
        "body_occurrences": len(starts),
        "first_text_line": starts[0] + 1,
        "numeric_candidate_lines": numeric_rows,
        "maximum_numeric_tokens_in_line": max_tokens,
        "modal_numeric_tokens_in_line": modal_count,
        "historical_region_name_hits": len(region_hits),
        "national_label_hits": national_hits,
        "header_excerpt": " | ".join(headers[:3])[:250],
        "numeric_row_examples": " | ".join(sample)[:370],
        "review_disposition": "selected_column_adopted" if item["adoption_status"] == "adopted_selected_columns"
                             else PRINTED_PAGE_DECISIONS.get(table_id, "pending_semantic_and_pdf_page_review"),
        "required_next_check": "See Burkina Faso printed-page review evidence under docs/evidence/; no new indicator was adopted."
                               if table_id in PRINTED_PAGE_DECISIONS else
                               "Inspect printed page, full numeric column names, population/denominator, geography, period, units and source method; decide adopt, incompatible, or out of scope with reason.",
    })

with OUT.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
with COL_OUT.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=column_rows[0].keys())
    writer.writeheader()
    writer.writerows(column_rows)
print(json.dumps({"tables": len(rows), "status": dict(Counter(row["review_disposition"] for row in rows)),
                  "with_all_13_region_names": sum(row["historical_region_name_hits"] == 13 for row in rows),
                  "with_national_label": sum(row["national_label_hits"] > 0 for row in rows),
                  "numeric_position_candidates": len(column_rows), "output": str(OUT)}, ensure_ascii=False))

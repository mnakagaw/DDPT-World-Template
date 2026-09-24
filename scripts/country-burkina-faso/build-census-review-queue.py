"""Order unreviewed RGPH tables for printed-page review, without adopting data.

The OCR/text match is a triage signal only. No detected historical-region name
must never be interpreted as proof that a table lacks local observations.
"""
from collections import Counter
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "evidence/TABLE_COLUMN_SCREEN.csv"
INVENTORY = ROOT / "evidence/SOURCE_TABLE_INVENTORY.csv"
OUT = ROOT / "evidence/TABLE_REVIEW_QUEUE.csv"
SUMMARY = ROOT / "evidence/TABLE_REVIEW_QUEUE_SUMMARY.json"

with SCREEN.open(encoding="utf-8-sig", newline="") as stream:
    screened = list(csv.DictReader(stream))
with INVENTORY.open(encoding="utf-8-sig", newline="") as stream:
    headings = {row["table_id"]: row["heading_first_line"] for row in csv.DictReader(stream)}
assert len(screened) == len(headings) == 581
pending = [row for row in screened if row["review_disposition"] == "pending_semantic_and_pdf_page_review"]
if not pending:
    raise SystemExit("No pending table decisions remain; review queue not written")


def group(row):
    hits = int(row["historical_region_name_hits"])
    if hits == 13:
        return "13_historical_region_names_detected"
    if hits > 0:
        return "some_historical_region_names_detected"
    return "no_historical_region_name_detected"


order = {name: index for index, name in enumerate((
    "13_historical_region_names_detected",
    "some_historical_region_names_detected",
    "no_historical_region_name_detected",
))}
pending.sort(key=lambda row: (order[group(row)], int(row["first_pdf_page"]), row["table_id"]))
rows = []
for rank, row in enumerate(pending, 1):
    rows.append({
        "review_order": rank,
        "triage_group_not_a_geography_decision": group(row),
        "table_id": row["table_id"],
        "first_physical_pdf_page": row["first_pdf_page"],
        "heading_from_inventory": headings[row["table_id"]],
        "historical_region_name_hits": row["historical_region_name_hits"],
        "national_label_hits": row["national_label_hits"],
        "numeric_candidate_lines": row["numeric_candidate_lines"],
        "header_excerpt_unverified": row["header_excerpt"],
        "numeric_row_examples_unverified": row["numeric_row_examples"],
        "review_instruction": "Inspect full printed table, columns, notes, geography, period, population/denominator, unit and source method; record an explicit adoption/exclusion/defer reason.",
    })
with OUT.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
summary = {
    "source_tables": len(screened),
    "previously_selected_adopted": sum(row["review_disposition"] == "selected_column_adopted" for row in screened),
    "printed_page_decisions_without_new_adoption": sum(row["review_disposition"].startswith("reviewed_") for row in screened),
    "pending": len(rows),
    "pending_groups": dict(Counter(row["triage_group_not_a_geography_decision"] for row in rows)),
    "pending_without_numeric_candidate_lines": sum(int(row["numeric_candidate_lines"]) == 0 for row in pending),
    "caution": "Textual region-name detection is only a review-order hint. Absence of a match does not establish absence of local data. No new indicator or source stage is adopted by this queue.",
}
assert sum(summary["pending_groups"].values()) == len(rows)
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

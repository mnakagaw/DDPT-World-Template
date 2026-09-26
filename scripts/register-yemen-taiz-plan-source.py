"""Register the verified Taiz 2024-2026 plan as a source, not a territory document."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PLAN_SHA256 = "09e33d2a39a0747370cac63c974ae4fe63703e17512cfff3878257d726a3c5cb"
PLAN_NAME = "raw/taiz-planning-2024/taiz-economic-and-social-development-plan-2024-2026.pdf"
SOURCE_ID = "yem-taiz-mopic-economic-social-plan-2024-2026"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    pdf = project / PLAN_NAME
    receipt = json.loads((project / f"{PLAN_NAME}.receipt.json").read_text(encoding="utf-8"))
    if (hashlib.sha256(pdf.read_bytes()).hexdigest() != PLAN_SHA256 or
            receipt["sha256"] != PLAN_SHA256 or receipt["status"] != "acquired"):
        raise ValueError("Taiz plan original/receipt differs from pinned source")
    dataset_path = project / "data/dashboard.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset["country"]["id"] != "YEM" or SOURCE_ID in {s["id"] for s in dataset["sources"]}:
        raise ValueError("Expected Yemen candidate without the plan source")
    dataset["sources"].append({
        "id": SOURCE_ID,
        "name": "Taiz Economic and Social Development Plan 2024-2026, English PDF",
        "url": receipt["source_url"],
        "publisher": "Taiz Governorate Planning and International Cooperation Office",
        "reference_period": "2024-2026",
        "geographic_level": "17 named Taiz districts within the plan's own scope",
        "status": "ready", "retrieved_at": receipt["retrieved_at"],
        "sha256": PLAN_SHA256, "raw_path": receipt["path"],
        "license": "terms_review_required",
        "note": "Publisher's 42-page English plan PDF. Its page 4 limits coverage to 17 named liberated districts, whereas the 2024 CSO Taiz yearbook lists 23 districts. Plan approval and exact 2017-reference territorial equivalence are unverified. Do not present it as a whole-governorate plan, approved budget, actual expenditure or evaluation."})
    dataset["collection"]["adapters"] = sorted(set(dataset["collection"]["adapters"] +
                                                    ["yemen-taiz-2024-plan-source-audit"]))
    for gap in dataset["gaps"]:
        if gap["category"] == "planning_documents":
            gap["status"] = "partial"
            gap["detail"] = ("The publisher's 42-page 2024-2026 plan PDF was acquired and its cover, methodology, "
                             "scope, project matrices and appendix were visually checked. Its own geographic scope is "
                             "17 named districts, while the 2024 Taiz statistical yearbook reports 23. Approval, legal "
                             "status, budget, expenditure and official evaluation remain unverified. No territory "
                             "document is adopted against the 2017 reference polygons.")
            gap["next_action"] = ("Verify the plan's 17-district roster and legal/official codes against a dated boundary, "
                                  "confirm approval/status with the issuer and audit the other planning, budget, "
                                  "implementation and evaluation originals by their distinct scopes.")
    dataset["generated_at"] = datetime.now(timezone.utc).isoformat()
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources_added": 1, "observations_added": 0, "documents_added": 0,
                      "plan_named_districts": 17}))


if __name__ == "__main__":
    main()

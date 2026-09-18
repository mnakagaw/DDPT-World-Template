#!/usr/bin/env python3
"""Create terminal, evidence-backed baseline dispositions for every Americas area.

This baseline never turns a failed acquisition into an observed value.  It records
what the regional release actually integrates and makes every remaining theme or
domain an explicit not-adopted/unavailable/failed state.  Country-specific
adjudicators may then replace the baseline with deeper evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


THEMES = [
    "population_total", "age_sex", "households_housing", "drinking_water", "sanitation", "electricity",
    "education_literacy", "employment", "disability", "migration", "urban_rural", "ethnicity",
    "health", "nutrition", "poverty",
]
DEEP_COUNTRIES = {"BLZ", "GTM"}
UNINHABITED = {"BVT", "SGS"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def set_complete(record, *, status, urls, note, evidence):
    record.update({
        "status": status,
        "identified": True,
        "accessed": status not in {"unavailable"},
        "acquired": status in {"inspected", "geography_matched", "adopted"},
        "inspected": status in {"inspected", "geography_matched", "adopted"},
        "geography_matched": status in {"geography_matched", "adopted"},
        "adopted": status == "adopted",
        "unavailable": status == "unavailable",
        "restricted": status == "restricted",
        "failed_with_evidence": status == "failed_with_evidence",
        "completion_verified": True,
        "urls": list(dict.fromkeys(urls)),
        "note": note,
        "evidence": evidence,
    })


def ext(receipt):
    path = receipt.get("path") or urlparse(receipt.get("url", "")).path
    return Path(path).suffix.lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    evidence = project / "evidence"
    preflight_path = evidence / "SOURCE_PREFLIGHT.json"
    semantic_path = evidence / "COUNTRY_SEMANTIC_INVENTORY.json"
    dashboard_path = project / "data/dashboard.json"
    preflight, semantic, dashboard = read(preflight_path), read(semantic_path), read(dashboard_path)
    page_receipts = read(project / "raw/country-source-pages/receipt.json").get("receipts", [])
    file_receipts = read(project / "raw/discovered-source-files/receipt.json").get("receipts", [])
    link_catalog = read(evidence / "COUNTRY_SOURCE_LINK_CATALOG.json")
    pdf_inspection = read(evidence / "COUNTRY_SOURCE_PDF_INSPECTION.json")

    pages_by_country, files_by_country, links_by_country, pdfs_by_country = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for row in page_receipts: pages_by_country[row.get("country_area_id")].append(row)
    for row in file_receipts: files_by_country[row.get("country_area_id")].append(row)
    for row in link_catalog.get("links", []): links_by_country[row.get("country_area_id")].append(row)
    for row in pdf_inspection.get("records", []): pdfs_by_country[row.get("country_area_id")].append(row)

    observations = defaultdict(list)
    for row in dashboard.get("observations", []):
        observations[row.get("territory_id")].append(row)
    source_by_id = {row.get("id"): row for row in dashboard.get("sources", [])}

    # Rebuild only the synthetic baseline.  Preserve real workbook field rows and deep-country adjudication rows.
    semantic["records"] = [row for row in semantic.get("records", []) if row.get("table_id") != "americas-baseline-release-disposition"]
    adjudicated = []
    for country in preflight.get("countries", []):
        cid, name = country["country_area_id"], country["name"]
        if cid in DEEP_COUNTRIES:
            continue
        country_pages = pages_by_country[cid]
        country_files = files_by_country[cid]
        acquired_pages = [row for row in country_pages if row.get("status") == "acquired"]
        failed_pages = [row for row in country_pages if row.get("status") != "acquired"]
        acquired_files = [row for row in country_files if row.get("status") == "acquired"]
        failed_files = [row for row in country_files if row.get("status") != "acquired"]
        machine_files = [row for row in acquired_files if ext(row) in {".xlsx", ".xls", ".csv", ".json", ".geojson", ".zip"}]
        country_links = links_by_country[cid]
        country_pdfs = pdfs_by_country[cid]
        all_urls = [row.get("url") for row in country_pages + country_files if row.get("url")]
        receipt_evidence = [{"receipt": "raw/country-source-pages/receipt.json", "acquired": len(acquired_pages), "failed_with_evidence": len(failed_pages)}, {"receipt": "raw/discovered-source-files/receipt.json", "acquired": len(acquired_files), "failed_with_evidence": len(failed_files)}]

        office_pages = [row for row in country_pages if row.get("domain") == "official_statistics_office"]
        office_acquired = [row for row in office_pages if row.get("status") == "acquired"]
        set_complete(country["official_statistics_office"], status="inspected" if office_acquired else "failed_with_evidence", urls=[row.get("url") for row in office_pages if row.get("url")], note=(f"The official statistics-office entry page for {name} was acquired and retained with a hashed receipt." if office_acquired else f"The official statistics-office URL for {name} was attempted but could not be acquired; the failure status and response evidence are retained."), evidence=receipt_evidence)

        census_pages = [row for row in country_pages if row.get("domain") in {"latest_census", "recent_census_round"}]
        census_acquired = [row for row in census_pages if row.get("status") == "acquired"]
        if cid in UNINHABITED:
            census_status = "unavailable"
            census_note = f"{name} is treated as an uninhabited special area in this release; no resident-population census result is represented as applicable. Registry membership and source attempts remain visible."
        else:
            census_status = "inspected" if census_acquired else "failed_with_evidence"
            census_note = (f"At least one official or UNSD census-round page for {name} was acquired. This confirms the source location or round, not a complete machine-readable table set." if census_acquired else f"The identified census result locations for {name} were attempted but could not be acquired; no census value is fabricated from the failed requests.")
        future_rounds = []
        for round_value in country.get("recent_census_rounds", []):
            try:
                round_year = int(round_value.get("year")) if isinstance(round_value, dict) else int(str(round_value)[:4])
            except (TypeError, ValueError):
                continue
            if round_year > datetime.now(timezone.utc).year:
                future_rounds.append(str(round_value.get("round") or round_year) if isinstance(round_value, dict) else str(round_value))
        if future_rounds:
            census_note += (
                " Scheduled/future census round(s): " + ", ".join(future_rounds)
                + ". Results are not acquired or usable."
            )
        set_complete(country["latest_census"], status=census_status, urls=[row.get("url") for row in census_pages if row.get("url")] or country["latest_census"].get("urls", []), note=census_note, evidence=receipt_evidence)

        if cid in UNINHABITED:
            result_status, result_note = "unavailable", "No resident-population Census result is treated as applicable for this uninhabited special area."
        elif acquired_files or country_pdfs:
            result_status, result_note = "inspected", f"{len(acquired_files)} direct official files and {len(country_pdfs)} PDF inspection records were retained for {name}; adopted observations remain separately identified."
        elif census_acquired:
            result_status, result_note = "inspected", "The official Census result location was acquired, but no direct result file was adopted in the regional baseline."
        else:
            result_status, result_note = "failed_with_evidence", "No direct Census result file was acquired after the recorded official-source attempts; international reference values remain labelled separately."
        set_complete(country["census_results"], status=result_status, urls=all_urls or country["census_results"].get("urls", []), note=result_note, evidence=receipt_evidence + [{"inspection": "evidence/COUNTRY_SOURCE_PDF_INSPECTION.json", "records": len(country_pdfs)}])

        if cid in UNINHABITED:
            catalog_status, catalog_note = "unavailable", "A resident Census table catalog is not treated as applicable for this uninhabited special area."
        elif country_links:
            catalog_status, catalog_note = "inspected", f"The acquired official pages exposed {len(country_links)} eligible source links; the link catalog preserves labels, source pages and URLs."
        elif census_acquired:
            catalog_status, catalog_note = "inspected", "The official Census entry page was inspected, but it exposed no directly collectable table link in this release."
        else:
            catalog_status, catalog_note = "failed_with_evidence", "No inspectable Census table catalog was acquired; attempted URLs and errors are retained."
        set_complete(country["table_catalog"], status=catalog_status, urls=all_urls or country["table_catalog"].get("urls", []), note=catalog_note, evidence=receipt_evidence + [{"catalog": "evidence/COUNTRY_SOURCE_LINK_CATALOG.json", "eligible_links": len(country_links)}])

        if cid in UNINHABITED:
            machine_status, machine_note = "unavailable", "Resident Census machine-readable data are not treated as applicable for this uninhabited special area."
        elif machine_files:
            machine_status, machine_note = "inspected", f"{len(machine_files)} directly linked machine-readable files were acquired. Only explicitly adopted, definition-compatible observations enter the dashboard."
        elif acquired_files:
            machine_status, machine_note = "unavailable", f"Direct official files were acquired, but none had an adopted machine-readable tabular format in this release; PDF evidence remains source-linked."
        else:
            machine_status, machine_note = "failed_with_evidence", "No machine-readable Census file was acquired after the recorded attempts; no PDF number was silently parsed into a regional indicator."
        set_complete(country["machine_readable_data"], status=machine_status, urls=all_urls or country["machine_readable_data"].get("urls", []), note=machine_note, evidence=receipt_evidence)

        # The regional baseline does not pretend that a country outline is an official ADM1/ADM2 code system.
        if cid in UNINHABITED:
            code_status, code_note = "unavailable", "No resident statistical ADM1/ADM2 hierarchy is treated as applicable for this uninhabited special area."
            bound_status, bound_note = "unavailable", "No resident statistical ADM1/ADM2 boundary layer is treated as applicable; registry membership remains."
        else:
            code_status, code_note = "failed_with_evidence", "Official domestic administrative/statistical codes were not adopted by this regional baseline. Country-level UN M49 identity is preserved and is not substituted for ADM1/ADM2 codes."
            bound_status, bound_note = "failed_with_evidence", "No official domestic ADM1/ADM2 boundary bundle was adopted for this country adapter. Any Natural Earth country outline is display-only and is not represented as a legal or statistical boundary."
        set_complete(country["administrative_codes"], status=code_status, urls=country["administrative_codes"].get("urls", []), note=code_note, evidence=receipt_evidence + [{"crosswalk": "evidence/GEOGRAPHY_CROSSWALK.csv"}])
        set_complete(country["adm1_adm2_boundaries"], status=bound_status, urls=country["adm1_adm2_boundaries"].get("urls", []), note=bound_note, evidence=[{"crosswalk": "evidence/GEOGRAPHY_CROSSWALK.csv"}, {"boundary_policy": "docs/WORLD_ADAPTER.md"}])

        planning_pages = [row for row in country_pages if row.get("domain") == "planning_law"]
        planning_acquired = [row for row in planning_pages if row.get("status") == "acquired"]
        planning_status = "failed_with_evidence"
        planning_note = ("The official government/planning start pages were acquired, but this baseline did not verify a country-specific legal planning obligation. No law, legal unit or planning cycle is inferred from a government home page." if planning_acquired else "Country-specific planning-law locations were attempted but not acquired; no legal obligation or planning unit is inferred.")
        set_complete(country["planning_law"], status=planning_status, urls=[row.get("url") for row in planning_pages if row.get("url")] or country["planning_law"].get("urls", []), note=planning_note, evidence=receipt_evidence + [{"inventory": "evidence/PLANNING_LEGAL_INVENTORY.csv"}])
        set_complete(country["planning_guidance"], status="failed_with_evidence", urls=country["planning_guidance"].get("urls", []), note="No country-specific official planning manual or verified drafting guidance was adopted in the regional baseline. The recorded start URLs remain available for the country adapter.", evidence=receipt_evidence + [{"inventory": "evidence/PLANNING_LEGAL_INVENTORY.csv"}])
        set_complete(country["plans_budgets_implementation_evaluation"], status="failed_with_evidence", urls=country["plans_budgets_implementation_evaluation"].get("urls", []), note="No mutually linked current plan, budget, implementation report and evaluation set was adopted for this country in the regional baseline. Missing components are not converted into a claim that planning does not exist.", evidence=receipt_evidence + [{"inventory": "evidence/PLANNING_LEGAL_INVENTORY.csv"}])

        # Close every real numeric workbook field with a terminal decision.
        for row in semantic["records"]:
            if row.get("country_area_id") != cid:
                continue
            if row.get("disposition") not in {"integrated", "not_adopted", "unavailable", "restricted", "failed_with_evidence"}:
                row.update({"disposition": "not_adopted", "reason": "The numeric field is retained in the source inventory but was not adopted in the Americas regional baseline because its category, denominator, geographic level, period or definition has not been harmonized to a dashboard indicator.", "coverage_complete": False})

        country_observations = observations.get(cid, [])
        by_indicator = {row.get("indicator_id"): row for row in country_observations}
        integrated_theme = {
            "population_total": next((iid for iid in ("CENSUS_POP_TOTAL", "UN_WPP_POP_TOTAL", "SP.POP.TOTL") if iid in by_indicator), None),
            "electricity": "EG.ELC.ACCS.ZS" if "EG.ELC.ACCS.ZS" in by_indicator else None,
            "health": "SP.DYN.LE00.IN" if "SP.DYN.LE00.IN" in by_indicator else None,
        }
        for theme in THEMES:
            iid = integrated_theme.get(theme)
            if iid:
                disposition = "integrated"
                src = by_indicator[iid].get("source_id") or "dashboard-observation"
                reason = f"{iid} is integrated at country/area level with its own period, unit, definition and source. It is not copied to subnational areas."
            elif cid in UNINHABITED:
                disposition, src = "unavailable", "area-applicability-review"
                reason = "No resident-population value is treated as applicable for this uninhabited special area; missing is not zero."
            elif acquired_pages or acquired_files:
                disposition, src = "not_adopted", "country-source-screening"
                reason = "Official source locations were screened, but no definition-compatible, geography-matched observation for this theme was adopted in the regional baseline. This is a release-scope disposition, not a claim that the country has no data."
            else:
                disposition, src = "failed_with_evidence", "country-source-screening"
                reason = "The official-source attempts did not yield an inspectable, definition-compatible observation for this theme. Acquisition failures are retained and no value is fabricated."
            semantic["records"].append({
                "country_area_id": cid,
                "source_id": src,
                "source_path": "evidence/SOURCE_PREFLIGHT.json",
                "source_url": all_urls[0] if all_urls else (country.get("latest_census", {}).get("urls") or ["https://unstats.un.org/unsd/demographic-social/census/censusdates"])[0],
                "table_id": "americas-baseline-release-disposition",
                "table_title": f"{name} Americas baseline evidence disposition",
                "field_id": theme,
                "field_label": f"Terminal release disposition for {theme}",
                "numeric_cell_count": 1 if iid else 0,
                "theme": theme,
                "disposition": disposition,
                "reason": reason,
                "indicator_id": iid,
                "coverage_complete": True,
            })
        country["country_adapter_status"] = "regional_baseline_terminal_evidence_review"
        adjudicated.append({"country_area_id": cid, "acquired_pages": len(acquired_pages), "failed_pages": len(failed_pages), "acquired_files": len(acquired_files), "failed_files": len(failed_files), "machine_files": len(machine_files), "pdf_records": len(country_pdfs), "eligible_links": len(country_links)})

    # Shared international workbooks do not belong to one country row, but all
    # acquired numeric fields still require a terminal release decision.
    for row in semantic["records"]:
        if row.get("country_area_id") != "MULTI":
            continue
        if row.get("disposition") in {"integrated", "not_adopted", "unavailable", "restricted", "failed_with_evidence"}:
            continue
        row.update({
            "disposition": "not_adopted",
            "reason": "This numeric field belongs to the shared UN WPP workbook and is not adopted through the country semantic inventory. The adopted total-population series is separately extracted by exact WPP location code, period and measure and audited in UN_WPP_AMERICAS_ADOPTION_AUDIT.json; all other workbook measures remain excluded from this release.",
            "coverage_complete": False,
        })

    semantic.setdefault("adjudication", {})["AMERICAS_BASELINE"] = {
        "country_area_count": len(adjudicated),
        "excluded_for_deep_adjudication": sorted(DEEP_COUNTRIES),
        "method": "Terminal evidence screening of acquired official pages/files, failed requests and adopted regional observations. A complete disposition does not imply equal data depth or source availability.",
    }
    semantic.setdefault("adjudication", {})["MULTI"] = {
        "source": "UN World Population Prospects 2024 shared workbook",
        "method": "Every inventoried numeric column is terminally excluded from the country semantic inventory. Adopted population rows are governed by the separate WPP extraction and 57-row adoption audit.",
        "adoption_audit": "evidence/UN_WPP_AMERICAS_ADOPTION_AUDIT.json",
    }
    semantic["generated_at"] = datetime.now(timezone.utc).isoformat()
    semantic["record_count"] = len(semantic["records"])
    semantic_path.write_text(json.dumps(semantic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight["generated_at"] = datetime.now(timezone.utc).isoformat()
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Public dataset states the release-wide audit result without hiding unequal depth.
    dashboard["gaps"] = [row for row in dashboard.get("gaps", []) if row.get("category") != "country_source_evidence_audit"]
    audit_source_id = "areadata-country-completion-matrix"
    dashboard["sources"] = [row for row in dashboard.get("sources", []) if row.get("id") != audit_source_id]
    dashboard["sources"].append({
        "id": audit_source_id,
        "name": "AreaData Americas country completion matrix",
        "publisher": "AreaData",
        "url": "https://areadata.net/",
        "status": "ready",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "reference_period": "Release 0.10.1 evidence audit",
        "license": "AreaData audit metadata",
        "geographic_level": "57 UN M49 Americas countries/areas",
        "note": "Release evidence distinguishes integrated, not-adopted, unavailable, restricted and failed-with-evidence states; completion does not imply equal data depth.",
    })
    dashboard["gaps"].append({
        "category": "country_source_evidence_audit",
        "status": "complete_with_explicit_gaps",
        "detail": "All 57 UN M49 Americas countries/areas have a terminal source-evidence review. Each required domain and theme is recorded as integrated, not adopted, unavailable, restricted or failed with evidence. Data depth is intentionally unequal and no missing value is converted to zero.",
        "next_action": "Use each country adapter's source links and dispositions to add compatible local tables and official boundaries without changing existing missing-value meanings.",
        "source_id": audit_source_id,
    })
    dashboard["generated_at"] = datetime.now(timezone.utc).isoformat()
    dashboard_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "countries": adjudicated, "counts": {"countries": len(adjudicated), "acquired_pages": sum(x["acquired_pages"] for x in adjudicated), "failed_pages": sum(x["failed_pages"] for x in adjudicated), "acquired_files": sum(x["acquired_files"] for x in adjudicated), "failed_files": sum(x["failed_files"] for x in adjudicated), "machine_files": sum(x["machine_files"] for x in adjudicated), "pdf_records": sum(x["pdf_records"] for x in adjudicated)}}
    (evidence / "AMERICAS_BASELINE_ADJUDICATION.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()

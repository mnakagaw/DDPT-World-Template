"""Graft the validated BFA country shard onto the deployed AreaData site.

This preserves all previously published country shards and the supranational
edition. The fully regenerated world candidate is used only for BFA additions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--integrated", type=Path, required=True)
    parser.add_argument("--country", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    base, integrated, country, out = (p.resolve() for p in (args.base, args.integrated, args.country, args.out))
    if out.exists():
        raise RuntimeError(f"Output already exists: {out}")
    old = json.loads((base / "data/dashboard.json").read_text(encoding="utf-8"))
    new = json.loads((integrated / "data/dashboard.json").read_text(encoding="utf-8"))
    manifest = json.loads((country / "evidence/WORD_REPORT_MANIFEST.json").read_text(encoding="utf-8"))
    if old["country"]["id"] != "WLD" or new["country"]["id"] != "WLD":
        raise RuntimeError("Expected world datasets")
    if "BFA" in old["data_shards"]["countries"] or "BFA" not in new["data_shards"]["countries"]:
        raise RuntimeError("BFA branch already present or not generated")
    if len(manifest["files"]) != 410:
        raise RuntimeError("Expected 410 BFA Word reports")
    bfa_shard = integrated / "data/countries/BFA.json"
    shard = json.loads(bfa_shard.read_text(encoding="utf-8"))
    if shard["country_area_id"] != "BFA" or len(shard["territories"]) != 409:
        raise RuntimeError("BFA shard content mismatch")
    for entry in manifest["files"]:
        word = country / "site" / entry["path"]
        if not word.is_file() or digest(word) != entry["sha256"]:
            raise RuntimeError(f"Word source mismatch: {entry['territory_id']}")

    shutil.copytree(base, out)
    out_countries = out / "data/countries"
    for name in ("BFA.json", "BFA.boundaries.0.json", "BFA.boundaries.1.json"):
        shutil.copy2(integrated / "data/countries" / name, out_countries / name)
    for key in ("indicators", "sources"):
        ids = {row["id"] for row in old[key]}
        old[key].extend(row for row in new[key] if row["id"] not in ids)
    old["analysis"]["default_period_by_indicator"].update(
        {k: v for k, v in new["analysis"]["default_period_by_indicator"].items()
         if k not in old["analysis"]["default_period_by_indicator"]}
    )
    old["analysis"]["terminal_territory_ids"] = [
        item for item in old["analysis"]["terminal_territory_ids"] if item != "BFA"
    ]
    old["analysis"]["census_population_pyramids"] = new["analysis"].get("census_population_pyramids", {})
    old["analysis"]["coverage"]["census_integrated_country_ids"] = new["analysis"]["coverage"]["census_integrated_country_ids"]
    for gap in old["gaps"]:
        if gap.get("category") == "country_adapters":
            gap["status"] = "partial"
            gap["detail"] = (
                "Domestic country data are integrated for 48 Americas countries/areas and Burkina Faso. "
                "Other countries still need separate official census, administrative and planning research; "
                "the world collector does not invent local boundaries, values or legal planning status."
            )
        elif gap.get("category") == "domestic_census_coverage":
            gap["detail"] = (
                "Domestic data branches cover 48 Americas countries/areas and Burkina Faso. "
                "The Burkina Faso branch uses historical 2019 census geography; its current-law crosswalk "
                "and remaining source tables are still under review. Other domestic Census editions are pending."
            )
    for key in ("adapters", "notes"):
        old["collection"][key].extend(x for x in new["collection"][key] if x not in old["collection"][key])
    old["data_shards"]["countries"]["BFA"] = new["data_shards"]["countries"]["BFA"]
    old_integrity, new_integrity = old["data_shards"]["integrity"], new["data_shards"]["integrity"]
    old_integrity["countries"]["BFA"] = new_integrity["countries"]["BFA"]
    for key in ("territory_count", "observation_count", "boundary_count", "document_count", "comparison_count"):
        old_integrity[key] = new_integrity[key]
    old_integrity["canonical_sha256"] = new_integrity["canonical_sha256"]
    old_integrity["full_sha256"] = new_integrity["full_sha256"]
    (out / "data/dashboard.json").write_text(json.dumps(old, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    # The common app uses this country-independent area ID map only for BFA.
    word_map = {entry["territory_id"]: Path(entry["path"]).name for entry in manifest["files"]}
    words_dir = out / "exports/bfa/diagnostic"
    words_dir.mkdir(parents=True)
    for entry in manifest["files"]:
        shutil.copy2(country / "site" / entry["path"], words_dir / Path(entry["path"]).name)
    app_path = out / "assets/app.mjs"
    app = app_path.read_text(encoding="utf-8")
    hook = "function territorial() {"
    button = "${button('diagnostic-csv','Full diagnostic data CSV')}</div>"
    if hook not in app or button not in app:
        raise RuntimeError("Common app Word-link insertion points changed")
    helper = (
        "const bfaWordFiles=" + json.dumps(word_map, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "function bfaWordLink(){const filename=bfaWordFiles[state.selected];"
        "if(!filename)return '';return '<a class=\"button\" href=\"../exports/bfa/diagnostic/'"
        "+filename+'\" download=\"Territorial Development Diagnostic - '+safeFilename(currentArea().name)"
        "+'.docx\">Territorial Development Diagnostic Word</a>'; }\n"
    )
    app = app.replace(hook, helper + hook, 1)
    app = app.replace(button, "${button('diagnostic-csv','Full diagnostic data CSV')}${bfaWordLink()}</div>", 1)
    app_changes = {
        "const nationalDocuments=state.selected===dataset.country.national_territory_id?[]:planningDocuments(dataset,dataset.country.national_territory_id);":
            "const referenceCountryId=(currentArea().id==='BFA'||currentArea().country_id==='BFA')?'BFA':dataset.country.national_territory_id;\n"
            "  const nationalDocuments=state.selected===referenceCountryId?[]:planningDocuments(dataset,referenceCountryId);",
        "const local=dataset.territories.filter(area=>area.level!=='national');":
            "const local=dataset.territories.filter(area=>area.level!=='national' && (referenceCountryId!=='BFA'||(area.country_id==='BFA'&&area.id!=='BFA')));",
        "if(worldMode()&&currentArea().type!=='country'){":
            "if(worldMode()&&currentArea().type!=='country'&&currentArea().country_id!=='BFA'){",
        "<h2>National reference materials — '+e(dataset.country.name)+'</h2>":
            "<h2>National reference materials — '+e(areaFor(referenceCountryId)?.name||dataset.country.name)+'</h2>",
        "'<div class=\"end-actions\">'+pageLink('territorial','Review territorial evidence')":
            "'<div class=\"end-actions\">'+bfaWordLink()+pageLink('territorial','Review territorial evidence')",
    }
    planning_start = app.index("function planning() {")
    planning_end = app.index("function home() {", planning_start)
    planning_app = app[planning_start:planning_end]
    for original, replacement in app_changes.items():
        if planning_app.count(original) != 1:
            raise RuntimeError(f"Planning insertion point changed: {original[:70]}")
        planning_app = planning_app.replace(original, replacement, 1)
    app = app[:planning_start] + planning_app + app[planning_end:]
    root_fetch = "new URL('data/dashboard.json',base)"
    if app.count(root_fetch) != 1:
        raise RuntimeError("Root data load hook changed")
    app = app.replace(root_fetch, "new URL('data/dashboard.json?v=0.12.2-bfa',base)", 1)
    app_path.write_text(app, encoding="utf-8")
    for page in ("index.html", "territorial/index.html", "thematic/index.html", "planning/index.html", "database/index.html"):
        html_path = out / page
        html = html_path.read_text(encoding="utf-8")
        old_version = "app.mjs?v=0.12.1"
        if html.count(old_version) != 1:
            raise RuntimeError(f"App version hook changed: {page}")
        html_path.write_text(html.replace(old_version, "app.mjs?v=0.12.2-bfa"), encoding="utf-8")

    # Verify that no previously published area value is removed by the graft.
    preserved = json.loads((out / "data/dashboard.json").read_text(encoding="utf-8"))
    assert preserved["observations"] == json.loads((base / "data/dashboard.json").read_text(encoding="utf-8"))["observations"]
    evidence = {
        "base_root_sha256": digest(base / "data/dashboard.json"),
        "release_root_sha256": digest(out / "data/dashboard.json"),
        "bfa_shard_sha256": digest(out_countries / "BFA.json"),
        "bfa_territories": len(shard["territories"]) + 1,
        "bfa_word_files": len(word_map),
        "previous_root_observations_preserved": True,
        "source_limitations": "2019 historical geography and partial source-table review; 2025 legal/current locality crosswalk is unresolved.",
    }
    (out / "BFA_RELEASE_EVIDENCE.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()

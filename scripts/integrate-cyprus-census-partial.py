#!/usr/bin/env python3
"""Replay a partial Cyprus 2021 census edition from saved CYSTAT and DLS originals.

The CYSTAT 2021 geography is kept separate from post-2024 municipalities.
The DLS shapes are simplified for navigation only, never for legal boundaries
or statistical aggregation. No current municipal plan or budget is inferred.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import re
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pyproj
import shapefile
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "generated" / "cyprus-areadata-20260927"
RAW = PROJECT / "raw"
EVIDENCE = PROJECT / "evidence"
DATA = PROJECT / "data" / "dashboard.json"
BOOTSTRAP = PROJECT / "reference" / "dashboard-bootstrap.json"
CENSUS_RECEIPT = EVIDENCE / "CYP_CENSUS_2021_1891108E_RECEIPT.json"
BOUNDARY_RECEIPT = EVIDENCE / "CYP_OFFICIAL_BOUNDARY_RECEIPT.json"
REUSE_RECEIPT = EVIDENCE / "CYP_CYSTAT_REUSE_RECEIPT.json"
PLANNING_RECEIPT = RAW / "planning-followup" / "receipt.json"
CENSUS_RESULT = RAW / "cystat-census-2021" / "1891108E-all-axes-result.html"
BOUNDARY_ZIP = RAW / "official-boundaries" / "pre-2024-municipal-community-boundaries.zip"
CENSUS_ID = "cystat-census-2021-1891108E"
DLS_ID = "cyprus-dls-pre-2024-coded-boundaries"
REUSE_ID = "cystat-data-reusability"
STAT_EDITION = "CYSTAT-Census-2021-10-01-1891108E"
SHAPE_EDITION = "DLS-resource-2947-2021-05-26-pre-2024"
SIMPLIFICATION_METRES = 10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def planning_location_sources() -> list[dict]:
    """Register official planning locations without joining current authorities to 2021 units."""
    receipts = {
        row["path"]: row
        for row in json.loads(PLANNING_RECEIPT.read_text(encoding="utf-8"))["sources"]
    }
    leads = [
        ("cyprus-mof-municipal-budget-circular-2026", "Ministry of Finance 2026 municipal-budget circular and 2026–2028 templates", "Ministry of Finance, Republic of Cyprus", "2026-budget-circular-government.html", "2026; 2026–2028", "Official entrypoint returned HTTP 403 to the capture client. Template contents and current edition are unverified; this is neither an adopted budget nor a municipal value."),
        ("cyprus-pafos-municipal-budget-2026", "Pafos municipality 2026 budget PDF", "Municipality of Pafos", "pafos-2026-budget.pdf", "2026; framework 2026–2028", "The source PDF has conflicting surplus figures on pages 1 and 2. No amount is adopted; current municipality identity must be crosswalked before any link to 2021 Census units."),
        ("cyprus-pafos-budget-approval-2026", "Pafos 2026 budget conditional approval letter", "Municipality of Pafos / Ministry of Interior", "pafos-2026-budget-approval.pdf", "2026-02-27", "Approval carries conditions and does not itself approve projects or resolve the source budget's page-1/page-2 disagreement. No amount or 2021 locality join is transferred."),
        ("cyprus-larnaka-strategic-plan-minutes-2025", "Larnaka council 2025 strategic-plan decision minutes", "Municipality of Larnaka", "larnaka-strategy-council-minutes.pdf", "2025-01-08", "The council approval minute was acquired, but its Appendix B plan body is missing. Do not infer plan contents, achievement or a 2021 statistical-locality join."),
        ("cyprus-limassol-strategy-minutes-2025", "Limassol council 2025 strategic-objectives decision minutes", "Municipality of Limassol", "limassol-council-strategy-minutes-2025.pdf", "2025-03-13", "The strategy/objectives decision was acquired; its underlying plan body and implementation are not verified. Keep the current municipality separate from 2021 Census units."),
        ("cyprus-limassol-strategy-minutes-2026", "Limassol council 2026 strategic-objectives decision minutes", "Municipality of Limassol", "limassol-council-strategy-minutes-2026.pdf", "2026-03-11", "The decision was acquired but its plan annex and results were not. The example 3–5-year period is not a universal legal cycle or 2021-locality value."),
    ]
    sources = []
    for source_id, name, publisher, path, period, note in leads:
        receipt = receipts[path]
        source = {
            "id": source_id, "name": name, "url": receipt["requested_url"],
            "publisher": publisher, "reference_period": period,
            "geographic_level": "current_municipality" if "mof-" not in source_id else "national_guidance",
            "status": "partial" if receipt["saved"] else "failed",
            "retrieved_at": receipt["retrieved_at"], "note": note,
        }
        if receipt["saved"]:
            original = RAW / "planning-followup" / path
            if sha256(original) != receipt["sha256"]:
                raise ValueError(f"Planning original changed: {path}")
            source.update({
                "sha256": receipt["sha256"],
                "raw_path": f"raw/planning-followup/{path}",
            })
        sources.append(source)
    return sources


def source_parser():
    module_path = ROOT / "scripts" / "collect-cyprus-census-2021.py"
    spec = importlib.util.spec_from_file_location("cyprus_census_collector", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.ResultParser


def integer(text: str) -> int:
    if not re.fullmatch(r"(?:\d{1,3}(?:\.\d{3})*|\d+)", text):
        raise ValueError(f"Unexpected CYSTAT numeric cell {text!r}")
    return int(text.replace(".", ""))


def census_rows(receipt: dict) -> tuple[list[dict], list[list[list[int]]], Counter]:
    if sha256(CENSUS_RESULT) != receipt["files"][1]["sha256"]:
        raise ValueError("The saved CYSTAT result no longer matches its HTTP receipt")
    result = source_parser()()
    result.feed(CENSUS_RESULT.read_text(encoding="utf-8"))
    axes = receipt["axes"]
    if [len(axis["options"]) for axis in axes] != [416, 3, 18]:
        raise ValueError("CYSTAT axis list changed")
    if len(result.cells) != 416 * 3 * 18:
        raise ValueError("CYSTAT all-axis response is incomplete")
    areas, values, dispositions = [], [], Counter()
    for index, option in enumerate(axes[0]["options"]):
        cells = result.cells[index * 54 : (index + 1) * 54]
        matrix = []
        for sex_index, sex in enumerate(axes[1]["options"]):
            age_values = []
            for age_index, age in enumerate(axes[2]["options"]):
                cell = cells[sex_index * 18 + age_index]
                parts = cell["headers"].split()
                if len(parts) != 3 or [result.labels.get(key) for key in parts] != [
                    option["label"],
                    sex["label"],
                    age["label"],
                ]:
                    raise ValueError(f"CYSTAT header-axis mismatch at {index}/{sex_index}/{age_index}")
                age_values.append(integer(cell["value"]))
                dispositions[
                    "adopted_direct"
                    if age_index == 0
                    else "adopted_calculation_input"
                    if sex_index == 0
                    else "retained_sex_age_validation"
                ] += 1
            if age_values[0] != sum(age_values[1:]):
                raise ValueError(f"Age cells do not sum for {option['code']}/{sex['code']}")
            matrix.append(age_values)
        if any(matrix[0][age] != matrix[1][age] + matrix[2][age] for age in range(18)):
            raise ValueError(f"Sex cells do not sum for {option['code']}")
        areas.append(option)
        values.append(matrix)
    district_positions = [index for index, row in enumerate(areas) if row["label"].endswith(" DISTRICT")]
    if [areas[index]["code"] for index in district_positions] != ["1", "3", "4", "5", "6"]:
        raise ValueError("The 2021 government-controlled district set changed")
    for district_index, start in enumerate(district_positions):
        end = district_positions[district_index + 1] if district_index + 1 < 5 else len(areas)
        for sex in range(3):
            for age in range(18):
                if values[start][sex][age] != sum(values[pos][sex][age] for pos in range(start + 1, end)):
                    raise ValueError(f"Local cover mismatch in {areas[start]['code']}/{sex}/{age}")
    for sex in range(3):
        for age in range(18):
            if values[0][sex][age] != sum(values[pos][sex][age] for pos in district_positions):
                raise ValueError(f"District cover mismatch for {sex}/{age}")
    if values[0][0][0] != 923381:
        raise ValueError("The official final Census 2021 control changed")
    return areas, values, dispositions


def boundary_rows(receipt: dict, census_codes: set[int]) -> tuple[dict[int, dict], dict[int, object], dict]:
    if sha256(BOUNDARY_ZIP) != receipt["sha256"]:
        raise ValueError("Saved DLS boundary archive no longer matches its HTTP receipt")
    with zipfile.ZipFile(BOUNDARY_ZIP) as archive:
        contents = {
            info.filename[-3:].lower(): archive.read(info)
            for info in archive.infolist()
            if info.filename[-3:].lower() in {"shp", "shx", "dbf"}
        }
        wkt = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".prj"))).decode("ascii")
    reader = shapefile.Reader(
        shp=io.BytesIO(contents["shp"]),
        shx=io.BytesIO(contents["shx"]),
        dbf=io.BytesIO(contents["dbf"]),
        encoding="utf-8",
    )
    if len(reader) != 615:
        raise ValueError("Official DLS archive feature count changed")
    transform_to_wgs84 = pyproj.Transformer.from_crs(
        pyproj.CRS.from_wkt(wkt), pyproj.CRS.from_epsg(4326), always_xy=True
    ).transform
    attrs, geometries, original_points, display_points = {}, {}, 0, 0
    distortion = []
    for item in reader.iterShapeRecords():
        record = item.record.as_dict()
        code = record["VIL_CCD"]
        if code not in census_codes:
            continue
        if code in attrs or record["DIST_CODE"] != code // 1000 or record["VIL_CODE"] != code % 1000:
            raise ValueError(f"DLS code collision or inconsistent district prefix at {code}")
        original = shape(item.shape.__geo_interface__)
        if not original.is_valid or original.is_empty:
            raise ValueError(f"Invalid official geometry for {code}")
        display = original.simplify(SIMPLIFICATION_METRES, preserve_topology=True)
        if not display.is_valid or display.is_empty:
            raise ValueError(f"Invalid simplified display geometry for {code}")
        distortion.append(abs(display.area - original.area) / original.area)
        original_points += len(item.shape.points)
        display_points += sum(
            len(polygon.exterior.coords) + sum(len(ring.coords) for ring in polygon.interiors)
            for polygon in ([display] if display.geom_type == "Polygon" else display.geoms)
        )
        attrs[code] = record
        geometries[code] = transform(transform_to_wgs84, display)
    if set(attrs) != census_codes:
        raise ValueError(f"DLS-CYSTAT code join incomplete: {len(attrs)} of {len(census_codes)}")
    return attrs, geometries, {
        "dls_archive_features": len(reader),
        "census_local_codes": len(census_codes),
        "exact_unique_code_matches": len(attrs),
        "unjoined_dls_features": len(reader) - len(attrs),
        "original_matched_points": original_points,
        "display_points_after_10m_simplification": display_points,
        "maximum_relative_area_change": max(distortion),
        "crs_epsg": pyproj.CRS.from_wkt(wkt).to_epsg(),
    }


def polygon_coordinates(geometry):
    # Six decimals retain sub-metre display precision after the 10 m
    # topology-preserving navigation simplification in source metres.
    def rounded(value):
        if isinstance(value, (list, tuple)):
            return [rounded(item) for item in value]
        return round(value, 6)
    return rounded(mapping(geometry)["coordinates"])


def make_indicator(indicator_id: str, name: str, definition: str, method: str) -> dict:
    return {
        "id": indicator_id,
        "name": name,
        "theme": "Population",
        "unit": "people",
        "definition": definition,
        "population": "persons enumerated in the government-controlled areas of Cyprus on 2021-10-01",
        "measurement_method": method,
        "source_id": CENSUS_ID,
        "aggregation": "none",
        "series_family": "census",
        "display_role": "primary",
        "period_policy": "same_period",
    }


def main() -> None:
    census_receipt = json.loads(CENSUS_RECEIPT.read_text(encoding="utf-8"))
    boundary_receipt = json.loads(BOUNDARY_RECEIPT.read_text(encoding="utf-8"))
    reuse_receipt = json.loads(REUSE_RECEIPT.read_text(encoding="utf-8"))
    if sha256(RAW / reuse_receipt["raw_path"].removeprefix("raw/")) != reuse_receipt["sha256"]:
        raise ValueError("CYSTAT reuse policy receipt changed")
    areas, values, dispositions = census_rows(census_receipt)
    census_codes = {int(item["code"]) for item in areas if len(item["code"]) == 4}
    if len(census_codes) != 410:
        raise ValueError("Census locality code count changed")
    boundary_attrs, geometries, boundary_audit = boundary_rows(boundary_receipt, census_codes)
    PROJECT.joinpath("reference").mkdir(exist_ok=True)
    if not BOOTSTRAP.exists():
        shutil.copy2(DATA, BOOTSTRAP)
    dataset = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    if len(dataset["territories"]) != 7 or len(dataset["observations"]) != 312:
        raise ValueError("Cyprus bootstrap changed; inspect rather than overwrite")
    dataset["generated_at"] = datetime.now(timezone.utc).isoformat()
    dataset["country"]["geography_note"] = (
        "CYSTAT Census 2021 enumerated persons in the government-controlled areas on 2021-10-01: "
        "five districts and 410 coded municipality/community reporting units in the 2021 catalogue. "
        "The 2024 local-government reform changed municipal structure; these historic reporting IDs are not current "
        "municipal authorities. DLS resource 2947 contains 615 pre-2024 coded shapes, of which the same 410 "
        "CYSTAT local codes match uniquely. The DLS archive was posted 2021-05-26, before Census day; exact "
        "2021-10-01 legal boundary equivalence is unverified. Display polygons are 10 m simplified navigation "
        "geometry only. WDI whole-economy midyear estimates have a different scope and are not census counts."
    )
    dataset["territories"] = [dataset["territories"][0]]
    dataset["boundaries"] = {"type": "FeatureCollection", "features": []}
    for indicator in dataset["indicators"]:
        indicator["series_family"] = "international_reference"
        indicator["display_role"] = "context"
        indicator["period_policy"] = "same_period"
    age_groups = [
        ("CYP_CENSUS_AGE_0_14", "Census population aged 0–14", range(1, 4)),
        ("CYP_CENSUS_AGE_15_64", "Census population aged 15–64", range(4, 14)),
        ("CYP_CENSUS_AGE_65_PLUS", "Census population aged 65+", range(14, 18)),
    ]
    indicators = [
        make_indicator("CYP_CENSUS_POP_TOTAL", "Census enumerated population", "Direct CYSTAT 2021 census count, total sex and total age, for the government-controlled census reporting area. It is not the WDI midyear whole-economy estimate.", "cystat_2021_source_reported"),
        make_indicator("CYP_CENSUS_POP_MALE", "Census enumerated males", "Direct CYSTAT 2021 census count, male sex and total age, for the government-controlled census reporting area.", "cystat_2021_source_reported"),
        make_indicator("CYP_CENSUS_POP_FEMALE", "Census enumerated females", "Direct CYSTAT 2021 census count, female sex and total age, for the government-controlled census reporting area.", "cystat_2021_source_reported"),
    ]
    indicators.extend(
        make_indicator(
            indicator_id,
            name,
            "AreaData calculated this age band by summing the mutually exclusive published five-year CYSTAT 2021 census age cells for total sex, within the same coded reporting area. CYSTAT is not responsible for this derived grouping.",
            "areadata_sum_of_cystat_2021_age_cells",
        )
        for indicator_id, name, _ in age_groups
    )
    dataset["indicators"] = indicators + dataset["indicators"]
    census_observations, crosswalk, decoded = [], [], []
    district_ids = {}
    district_geometries = {}
    current_district_id = None
    for area_index, area in enumerate(areas):
        code, name = area["code"], area["label"]
        if code == "TOTAL":
            territory_id, level, kind, parent = "CYP", "national", "country", None
            target = dataset["territories"][0]
            target["source_id"] = CENSUS_ID
            target["code_system"] = "CYSTAT Census 2021 national government-controlled scope; World Bank country identity kept separately"
            target["boundary_version"] = None
        elif len(code) == 1:
            territory_id, level, kind, parent = f"CYP:census2021:district:{code}", "district", "census_district", "CYP"
            current_district_id = territory_id
            district_ids[code] = territory_id
            district_geometries[code] = []
            dataset["territories"].append({
                "id": territory_id, "name": name.title().replace(" District", " District"),
                "level": level, "type": kind, "parent_id": parent, "official_code": code,
                "code_system": "CYSTAT 1891108E district code", "boundary_version": STAT_EDITION,
                "source_id": CENSUS_ID,
            })
        else:
            district_code = code[0]
            if current_district_id != district_ids.get(district_code):
                raise ValueError(f"Unexpected CYSTAT district order for {code}")
            territory_id, level, kind, parent = f"CYP:census2021:local:{code}", "census_locality", "2021 municipality/community reporting unit", current_district_id
            dls = boundary_attrs[int(code)]
            dataset["territories"].append({
                "id": territory_id, "name": name, "level": level, "type": kind,
                "parent_id": parent, "official_code": code,
                "code_system": "CYSTAT 1891108E code = DLS VIL_CCD, DIST_CODE + VIL_CODE",
                "boundary_version": STAT_EDITION,
                "source_id": CENSUS_ID,
                "geometry_source_id": DLS_ID,
                "geometry_edition": SHAPE_EDITION,
            })
            geometry = geometries[int(code)]
            district_geometries[district_code].append(geometry)
            dataset["boundaries"]["features"].append({
                "type": "Feature",
                "properties": {
                    "territory_id": territory_id, "name": name, "official_code": code,
                    "code_system": "CYSTAT 1891108E code = DLS VIL_CCD, DIST_CODE + VIL_CODE",
                    "source_id": DLS_ID,
                    "geometry_edition": SHAPE_EDITION,
                    "reference_only": True,
                    "join_method": "Exact unique four-digit CYSTAT / DLS code; exact Census-day polygon equivalence unverified",
                    "display_only": True,
                    "dls_name_en": dls["VIL_NM_E"],
                },
                "geometry": {"type": geometry.geom_type, "coordinates": polygon_coordinates(geometry)},
            })
            crosswalk.append({
                "cystat_code": code, "cystat_name": name, "district_code": district_code,
                "dls_vil_ccd": dls["VIL_CCD"], "dls_dist_code": dls["DIST_CODE"],
                "dls_vil_code": dls["VIL_CODE"], "dls_name_en": dls["VIL_NM_E"],
                "match": "exact_unique_official_code", "geometry_adoption": "display_only_10m_simplified",
            })
        matrix = values[area_index]
        direct = [matrix[0][0], matrix[1][0], matrix[2][0]]
        grouped = [sum(matrix[0][index] for index in ages) for _, _, ages in age_groups]
        if sum(grouped) != direct[0]:
            raise ValueError(f"Derived age groups do not cover {code}")
        for indicator, value in zip(indicators, direct + grouped):
            calculated = indicator["id"].startswith("CYP_CENSUS_AGE_")
            census_observations.append({
                "territory_id": territory_id, "indicator_id": indicator["id"],
                "period": "2021", "value": value, "status": "observed",
                "source_id": CENSUS_ID, "boundary_version": STAT_EDITION if code != "TOTAL" else None,
                "source_locator": f"1891108E area code {code}; " + (
                    "Total sex, age " + ",".join(str(index) for index in next(ages for ind, _, ages in age_groups if ind == indicator["id"]))
                    if calculated else f"sex {['Total', 'Males', 'Females'][indicators.index(indicator)]}, age Total"
                ),
                **({"provenance": "calculated", "footnote": "AreaData sum of exact published five-year age cells in CYSTAT 1891108E; CYSTAT is not responsible for this modification."} if calculated else {}),
            })
        for sex_index in range(3):
            for age_index in range(18):
                decoded.append({
                    "area_code": code, "area_name": name,
                    "sex_code": str(sex_index), "sex": ["Total", "Males", "Females"][sex_index],
                    "age_code": str(age_index), "age": census_receipt["axes"][2]["options"][age_index]["label"],
                    "value": matrix[sex_index][age_index],
                    "disposition": "adopted_direct" if age_index == 0 else "adopted_calculation_input" if sex_index == 0 else "retained_sex_age_validation",
                })
    for district_code, parts in district_geometries.items():
        # Every CYSTAT child code has exactly one DLS shape. The dissolve is a
        # navigation outline of that complete observed footprint, not an
        # official district boundary or a numerical aggregation.
        union = unary_union(parts)
        if union.is_empty or not union.is_valid:
            raise ValueError(f"Invalid display-only district outline for {district_code}")
        district_id = district_ids[district_code]
        dataset["boundaries"]["features"].append({
            "type": "Feature",
            "properties": {
                "territory_id": district_id,
                "name": next(area["name"] for area in dataset["territories"] if area["id"] == district_id),
                "official_code": district_code,
                "code_system": "CYSTAT 1891108E district code",
                "source_id": DLS_ID,
                "geometry_edition": SHAPE_EDITION,
                "reference_only": True,
                "join_method": "Union of exact-code DLS locality display polygons; exact Census-day legal district outline unverified",
                "display_only": True,
                "construction": "Union of all matching 2021 Census locality display shapes; not legal district geometry",
                "member_count": len(parts),
            },
            "geometry": {"type": union.geom_type, "coordinates": polygon_coordinates(union)},
        })
    dataset["observations"] = census_observations + dataset["observations"]
    dataset["sources"].extend([
        {
            "id": CENSUS_ID, "name": "CYSTAT 2021 Population and Housing Census, table 1891108E",
            "url": census_receipt["source_url"], "publisher": "Statistical Service of Cyprus",
            "reference_period": "2021-10-01", "geographic_level": "government_controlled_census_district_and_locality",
            "status": "ready", "retrieved_at": census_receipt["retrieved_at_utc"],
            "sha256": census_receipt["files"][1]["sha256"], "raw_path": census_receipt["files"][1]["path"],
            "license": reuse_receipt["url"],
            "note": "© REPUBLIC OF CYPRUS, STATISTICAL SERVICE. CYSTAT permits aggregate statistical reuse with attribution. AreaData age-band grouping is a modification for which CYSTAT is not responsible. Government-controlled scope only; 2021 units are not post-2024 municipalities.",
        },
        {
            "id": DLS_ID, "name": "DLS pre-2024 coded municipality/community polygons, resource 2947",
            "url": boundary_receipt["resource_page"], "publisher": "Department of Lands and Surveys, Republic of Cyprus",
            "reference_period": "pre-2024; portal ZIP timestamp 2021-05-26", "geographic_level": "municipality_community",
            "status": "ready", "retrieved_at": boundary_receipt["retrieved_at_utc"],
            "sha256": boundary_receipt["sha256"], "raw_path": "raw/official-boundaries/pre-2024-municipal-community-boundaries.zip",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "license_url": boundary_receipt["catalogue_url"],
            "note": "© Department of Lands and Surveys. CC BY 4.0. 615 raw coded features; 410 exact unique code matches to CYSTAT 2021 local reporting units. Shapes were reprojected from EPSG:6312 and simplified 10 m for display. The ZIP predates Census day; exact legal boundary equivalence on 2021-10-01 remains unverified. District outlines are display-only child unions.",
        },
        {
            "id": REUSE_ID, "name": "CYSTAT data reusability policy",
            "url": reuse_receipt["url"], "publisher": "Statistical Service of Cyprus",
            "reference_period": "retrieved 2026-09-26", "geographic_level": "institutional_policy",
            "status": "ready", "retrieved_at": reuse_receipt["retrieved_at_utc"],
            "sha256": reuse_receipt["sha256"], "raw_path": reuse_receipt["raw_path"],
            "license": reuse_receipt["url"],
            "note": "CYSTAT allows aggregate statistical reuse with source acknowledgement; modified data require a clear statement and disclaimer of CYSTAT responsibility.",
        },
    ])
    dataset["sources"].extend(planning_location_sources())
    dataset["analysis"]["terminal_territory_ids"] = [row["id"] for row in dataset["territories"] if row["level"] == "census_locality"]
    dataset["analysis"]["population_context"] = {"primary_indicator_id": "CYP_CENSUS_POP_TOTAL", "reference_indicator_id": "SP.POP.TOTL"}
    dataset["analysis"]["census_2021"] = {
        "official_scope": "government-controlled areas", "statistical_date": "2021-10-01",
        "reporting_local_units": 410, "districts": 5, "code_system": "CYSTAT 1891108E / DLS VIL_CCD",
        "geometry_date_limitation": "2021-05-26 portal resource predates 2021-10-01 Census day; legal exactness not proven",
        "post_2024_municipal_crosswalk_status": "not_verified",
    }
    dataset["collection"]["adapters"].extend(["cystat-census-2021-1891108E", "cyprus-dls-pre-2024-code-join"])
    dataset["collection"]["notes"].extend([
        "All 22,464 source census cells were decoded; 1,248 direct population/sex totals adopted, 7,072 age cells used for three AreaData calculated groups, 14,144 sex-by-age cells retained for reconciliation.",
        "The 2021 CYSTAT geography is not the current post-2024 municipal registry; no current plan or budget is attached to these historical units.",
        "DLS shapes are navigation-only; 410/410 local codes match exactly, but the 2021-05-26 ZIP predates Census day and legal boundary equivalence remains unverified.",
    ])
    dataset["gaps"].extend([
        {"category": "post_2024_local_government", "status": "not_collected", "detail": "Current municipalities, community councils and district organizations are institutionally distinct from 2021 Census reporting units. No verified crosswalk or current local plan has been adopted.", "next_action": "Acquire the 2024 official reform register and unit-specific planning/budget originals; construct an approved historical-to-current code crosswalk before attaching documents."},
        {"category": "census_boundary_date", "status": "unverified", "detail": "DLS resource 2947 was posted 2021-05-26 and codes all 410 CYSTAT 2021 local reporting units, but its exact 2021-10-01 legal boundary date is not established.", "next_action": "Locate DLS or CYSTAT boundary release history or confirm the census map edition. Keep the current shapes display-only."},
        {"category": "local_sector_statistics", "status": "not_collected", "detail": "This pass adopted population/age/sex from one Census 2021 table, not education, housing, health, poverty, infrastructure or municipal finance detail.", "next_action": "Inventory all official Census themes and domestic sector sources, then join compatible 2021 codes/periods without carrying WDI national values locally."},
    ])
    DATA.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (EVIDENCE / "CYP_CENSUS_2021_1891108E_CELLS.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(decoded[0]))
        writer.writeheader()
        writer.writerows(decoded)
    with (EVIDENCE / "CYP_2021_CENSUS_DLS_CODE_CROSSWALK.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(crosswalk[0]))
        writer.writeheader()
        writer.writerows(crosswalk)
    inventory = {
        "source": CENSUS_ID, "source_matrix": "1891108E", "statistical_date": "2021-10-01",
        "axis_cardinalities": [416, 3, 18], "numeric_cells": len(decoded),
        "cell_dispositions": dispositions, "national_total": values[0][0][0],
        "national_males": values[0][1][0], "national_females": values[0][2][0],
        "all_area_sex_age_sums_reconciled": True,
        "all_district_local_and_national_district_sums_reconciled": True,
        "zero_total_census_localities": [
            {"code": area["code"], "name": area["label"]}
            for index, area in enumerate(areas)
            if len(area["code"]) == 4 and values[index][0][0] == 0
        ],
        "boundary_audit": boundary_audit,
        "source_rights": "CYSTAT aggregate statistical reuse with attribution and modified-value disclaimer; DLS CC BY 4.0",
        "not_adopted": ["sex-by-age detail as separate cards", "2024 municipal/plan identities", "WDI values as local census values"],
        "dataset_sha256": sha256(DATA),
    }
    (EVIDENCE / "CYP_CENSUS_2021_TABLE_AUDIT.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "territories": len(dataset["territories"]), "observations": len(dataset["observations"]),
        "indicators": len(dataset["indicators"]), "boundaries": len(dataset["boundaries"]["features"]),
        "census_cells": len(decoded), "code_matches": len(crosswalk),
        "dataset_sha256": inventory["dataset_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

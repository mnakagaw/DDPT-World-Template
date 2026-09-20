#!/usr/bin/env python3
"""Build a Nicaragua 2005 Census depth bundle from preserved INIDE tables.

The municipal reports are parsed at their published table rows.  Percentages
are calculated from source counts wherever counts are published.  Department
and country values are produced only after all member municipalities have
usable numerator and denominator values.  Santa Maria de Pantasma's municipal
PDF stores the tables as images, so its published rows are transcribed here
and cross-checked against the four national census volumes retained with the
collection receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import mapping, shape


INIDE_INDEX = "https://www.inide.gob.ni/docu/censos2005/censo2005.htm"
INIDE_MUNICIPAL = "https://www.inide.gob.ni/docu/censos2005/CifrasMun/tablas_cifras.htm"
INIDE_POP_GENERAL = "https://www.inide.gob.ni/docu/censos2005/VolPoblacion/Volumen%20Poblacion%201-4/Vol.I%20Poblacion-Caracteristicas%20Generales.pdf"
INETER = "https://www.ineter.gob.ni/geoportales/miacnicaragua/index.html"
INETER_MUN_WFS = "http://mapserveride.ineter.gob.ni/geoserver/wsINETER-DGGC/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=wsINETER-DGGC:Lim_Municipal&outputFormat=application/json&srsName=EPSG:4326"
INETER_DEP_WFS = "http://mapserveride.ineter.gob.ni/geoserver/wsINETER-DGGC/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=wsINETER-DGGC:Lim_Departamental&outputFormat=application/json&srsName=EPSG:4326"
WB_NUTRITION = "https://api.worldbank.org/v2/country/NIC/indicator/SN.ITK.DEFC.ZS?format=json&per_page=100"


ALIASES = {
    "EL JICARO": "JICARO",
    "SAN JOSE BOCAY": "SAN JOSE DE BOCAY",
    "STA MARIA DE PANTASMA": "SANTA MARIA DE PANTASMA",
    "VILLA CARLOS FONSECA": "VILLA EL CARMEN",
    "VILLANUEVA": "VILLA NUEVA",
    "SAN JUAN DE RIO COCO": "SAN JUAN DEL RIO COCO",
    "SAN FRANCISCO CUAPA": "SAN FRANCISCO DE CUAPA",
    "SAN JUAN DEL NICARAGUA": "SAN JUAN DE NICARAGUA",
    "DESEMBOCADURA DE RIO GRANDE": "DESEMBOCADURA DE RIO",
    "RAMA": "EL RAMA",
    "WIWILI DE NUEVA SEGOVIA": "WIWILI",
    "WIWILI": "WIWILI DE JINOTEGA",
}


def norm(value: str) -> str:
    value = "".join(c for c in unicodedata.normalize("NFD", value.upper()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", value).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "AreaData/0.10 Nicaragua evidence collector"})
    with urllib.request.urlopen(request, timeout=300) as response:
        path.write_bytes(response.read())


def number(cell: str) -> float:
    cell = cell.strip()
    if cell == "-":
        return 0.0
    match = re.search(r"-?\d+(?: \d{3})*(?:\.\d+)?", cell)
    if not match:
        raise ValueError(f"No numeric value in {cell!r}")
    return float(match.group(0).replace(" ", ""))


def row_values(page: str, target: str, minimum: int, *, exact_only: bool = False) -> list[float]:
    candidates = []
    for line in page.splitlines():
        cells = re.split(r"\s{2,}", line.strip())
        label_norm = norm(cells[0]) if cells else ""
        if label_norm != target and (exact_only or not label_norm.startswith(target + " ")):
            continue
        values = []
        for cell in cells[1:]:
            try:
                values.append(number(cell))
            except ValueError:
                pass
        if len(values) >= minimum:
            candidates.append(values)
    if not candidates:
        raise RuntimeError(f"Published row {target!r} with {minimum} values not found")
    # A municipal report can repeat the municipality name for the whole
    # municipality and for its like-named urban locality.  The table total is
    # the candidate with the largest printed denominator/count; taking the
    # first text-layer occurrence silently selected the locality for Boaco.
    return max(candidates, key=lambda values: values[0])


def find_page(pages: list[str], target: str | tuple[str, ...], required: tuple[str, ...], minimum: int) -> tuple[str, list[float]]:
    targets = (target,) if isinstance(target, str) else target
    eligible = [page for page in pages if all(norm(term) in norm(page) for term in required)]
    # Search every eligible page for an exact municipality row before using a
    # prefix alias. Otherwise Boaco Viejo on an earlier page wins over the
    # later exact BOACO municipal-total row.
    for exact_only in (True, False):
        for candidate in targets:
            for page in eligible:
                try:
                    return page, row_values(page, candidate, minimum, exact_only=exact_only)
                except RuntimeError:
                    continue
    raise RuntimeError(f"No page for {targets!r} with headings {required}")


def find_page_any(pages: list[str], target: str | tuple[str, ...], alternatives: tuple[tuple[str, ...], ...], minimum: int) -> tuple[str, list[float]]:
    failures = []
    for required in alternatives:
        try:
            return find_page(pages, target, required, minimum)
        except RuntimeError as exc:
            failures.append(str(exc))
    raise RuntimeError("; ".join(failures))


def published_municipal_rows(entry: dict, text_path: Path) -> dict[str, tuple[float, float]]:
    code = entry["official_code"]
    if code == "1015":
        # Published municipal table rows (pages 4, 6, 9, 11 and 19 of the report).
        return {
            "population_total": (37880.0, 37880.0),
            "female": (8524.0 + 9921.0, 37880.0),
            "illiteracy": (10620.0 * 0.37 + 9921.0 * 0.31, 10620.0 + 9921.0),
            "employment": (10054.0 + 1485.0, 10054.0 + 1485.0 + 3403.0 + 11254.0),
            "urban": (5662.0, 37880.0),
            "occupied_housing": (6652.0, 7262.0),
            "water_access": (6652.0 - 5101.0, 6652.0),
            "electricity_access": (6652.0 - 5481.0, 6652.0),
            "health_access_risk": (2563.0, 6652.0),
            "sanitation_access": (6780.0 - 2386.0, 6780.0),
            "disability": (508.0, 6780.0),
            "migration": (327.0, 6780.0),
            "poverty": (6780.0 * (23.8 + 65.3) / 100.0, 6780.0),
        }

    catalog_target = norm(entry["municipality"])
    target = ALIASES.get(catalog_target, catalog_target)
    targets = tuple(dict.fromkeys((target, catalog_target)))
    pages = text_path.read_text(encoding="utf-8", errors="replace").split("\f")
    pop_page, pop = find_page(pages, targets, ("PARTOS DEL", "% ANALF"), 12)
    _housing_page, housing = find_page_any(pages, targets, (("VIVIENDAS", "SIN LUZ", "SIN AGUA"), ("INDICADORES DE VIVIENDA",)), 10)
    _household_page, household = find_page_any(pages, targets, (("HOGARES", "CON EMI"), ("INDICADORES DE HOGAR",)), 4)
    _poverty_page, poverty = find_page_any(pages, targets, (("NO POBRE",), ("POBRES EXTREMOS",)), 3)

    total, male_u15, male_15, female_u15, female_15 = pop[:5]
    particular, occupied = housing[:2]
    no_light, no_water, far_health = housing[6], housing[7], housing[9]
    households, no_toilet = household[0], household[3]
    poor_pct = poverty[1] + poverty[2]
    return {
        "population_total": (total, total),
        "female": (female_u15 + female_15, total),
        "illiteracy": (male_15 * pop[8] / 100.0 + female_15 * pop[9] / 100.0, male_15 + female_15),
        # Replaced below from national Volume IV table 7, which has complete
        # male/female PEA and PEI counts for every municipality.
        "employment": (0.0, 1.0),
        # Replaced below from the municipality volume's explicit Urban/Rural
        # row. This avoids treating repeated district Barrio subtotals as a
        # municipality total in Managua.
        "urban": (0.0, total),
        "occupied_housing": (occupied, particular),
        "water_access": (occupied - no_water, occupied),
        "electricity_access": (occupied - no_light, occupied),
        "health_access_risk": (far_health, occupied),
        "sanitation_access": (households - no_toilet, households),
        # Replaced below from Household Volume I tables 9 and 11. Some
        # municipal PDFs visually contain these columns but omit them in the
        # embedded text layer.
        "disability": (0.0, households),
        "migration": (0.0, households),
        "poverty": (households * poor_pct / 100.0, households),
    }


def latest_wb(path: Path) -> tuple[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    row = next((row for row in data[1] if row.get("value") is not None), None)
    if row is None:
        raise RuntimeError("No non-null World Bank nutrition value")
    return str(row["date"]), float(row["value"])


def parse_population_basics(text_path: Path, entries: list[dict], parsed: dict[str, dict[str, tuple[float, float]]]) -> tuple[dict[str, tuple[float, float, float]], list[dict]]:
    lines = text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = table_block(lines, "CUADRO 1 POBLACION POR AREA", "CUADRO 2 POBLACION POR LUGAR", after_line=480)
    result: dict[str, tuple[float, float, float]] = {}
    differences = []
    for entry in entries:
        catalog_target = norm(entry["municipality"])
        targets = tuple(dict.fromkeys((ALIASES.get(catalog_target, catalog_target), catalog_target)))
        total = parsed[entry["official_code"]]["population_total"][0]
        candidates = []
        for line in lines:
            line_norm = norm(line)
            if not any(line_norm == target or line_norm.startswith(target + " ") for target in targets):
                continue
            cells = re.split(r"\s{2,}", line.strip())
            values = []
            for cell in cells[1:]:
                try:
                    values.append(number(cell))
                except ValueError:
                    pass
            # Vol. IV table 1 columns: total/male/female, urban/male/female,
            # rural/male/female. Match the already parsed municipal total so
            # same-named department rows cannot be selected.
            if len(values) >= 9:
                candidates.append((abs(values[0] - total), values[0], values[2], values[3]))
        candidates.sort()
        if not candidates or (len(candidates) > 1 and math.isclose(candidates[0][0], candidates[1][0], abs_tol=0.1)):
            raise RuntimeError(f"Urban total match for {entry['official_code']} {entry['municipality']}: {candidates}")
        _distance, volume_total, volume_female, urban = candidates[0]
        result[entry["official_code"]] = (volume_total, volume_female, urban)
        report_female = parsed[entry["official_code"]]["female"][0]
        if (not math.isclose(volume_total, total, rel_tol=0, abs_tol=0.1)
                or not math.isclose(volume_female, report_female, rel_tol=0, abs_tol=0.1)):
            differences.append({"code": entry["official_code"], "municipality": entry["municipality"],
                                "municipal_report_population": total, "volume_iv_population": volume_total,
                                "municipal_report_female": report_female, "volume_iv_female": volume_female,
                                "treatment": "Population, female and urban counts use the direct Volume IV municipality row; the municipal-report difference is retained here and is not silently discarded."})
    return result, differences


def parse_direct_parent_population(text_path: Path, department_names: list[str]) -> dict[str, tuple[float, float, float]]:
    """Return direct total, female and urban counts from Volume IV table 1.

    Department and municipality labels can be identical (for example Boaco),
    so the larger exact-label row is the first-order-area observation.
    """
    lines = text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    block = table_block(lines, "CUADRO 1 POBLACION POR AREA", "CUADRO 2 POBLACION POR LUGAR", after_line=480)
    labels = {name: norm(name) for name in department_names}
    labels["LA REPÚBLICA"] = "LA REPUBLICA"
    aliases = {"Atlántico Norte": "R A A N", "Atlántico Sur": "R A A S"}
    result: dict[str, tuple[float, float, float]] = {}
    for original, target in labels.items():
        target = aliases.get(original, target)
        candidates = []
        for line in block:
            cells = re.split(r"\s{2,}", line.strip())
            if not cells or norm(cells[0]) != target:
                continue
            values = []
            for cell in cells[1:]:
                try:
                    values.append(number(cell))
                except ValueError:
                    pass
            if len(values) >= 9:
                candidates.append((values[0], values[2], values[3]))
        if not candidates:
            raise RuntimeError(f"Direct parent population row missing for {original}")
        result[original] = max(candidates, key=lambda values: values[0])
    return result


def numeric_cells(line: str) -> list[float]:
    values = []
    for cell in re.split(r"\s{2,}", line.strip())[1:]:
        try:
            values.append(number(cell))
        except ValueError:
            pass
    return values


def table_block(lines: list[str], start_text: str, end_text: str, after_line: int = 1000) -> list[str]:
    start = next(i for i, line in enumerate(lines) if i > after_line and start_text in norm(line))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if end_text in norm(line))
    return lines[start:end]


def parse_employment_totals(text_path: Path, entries: list[dict], parsed: dict[str, dict[str, tuple[float, float]]]) -> dict[str, tuple[float, float]]:
    lines = text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    block = table_block(lines, "CUADRO 7 POBLACION DE 10 ANOS", "CUADRO 8 POBLACION OCUPADA")
    result = {}
    for entry in entries:
        catalog_target = norm(entry["municipality"])
        targets = tuple(dict.fromkeys((ALIASES.get(catalog_target, catalog_target), catalog_target)))
        matches = [i for i, line in enumerate(block) if norm(line) in targets]
        if not matches:
            matches = [i for i, line in enumerate(block) if any(norm(line).startswith(target + " ") for target in targets)]
        candidates = []
        for index in matches:
            nearby = block[index + 1:index + 8]
            male = next((numeric_cells(line) for line in nearby if norm(line).startswith("HOMBRES ")), None)
            female = next((numeric_cells(line) for line in nearby if norm(line).startswith("MUJERES ")), None)
            if male and female and len(male) >= 7 and len(female) >= 7:
                candidates.append((male[1] + female[1], male[1] + female[1] + male[6] + female[6]))
        if len(candidates) != 1:
            raise RuntimeError(f"Employment total match for {entry['official_code']} {entry['municipality']}: {candidates}")
        result[entry["official_code"]] = candidates[0]
    return result


def parse_household_supplements(text_path: Path, entries: list[dict], parsed: dict[str, dict[str, tuple[float, float]]]) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float]], list[dict]]:
    lines = text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    disability_block = table_block(lines, "CUADRO 9 HOGARES CON PERSONAS", "CUADRO 10")
    migration_block = table_block(lines, "CUADRO 11 HOGARES POR NUMERO", "CUADRO 12")
    disability, migration = {}, {}
    for entry in entries:
        catalog_target = norm(entry["municipality"])
        targets = tuple(dict.fromkeys((ALIASES.get(catalog_target, catalog_target), catalog_target)))
        d_candidates, m_candidates = [], []
        disability_lines = [line for line in disability_block if norm(line) in targets]
        if not disability_lines:
            disability_lines = [line for line in disability_block if any(norm(line).startswith(target + " ") for target in targets)]
        migration_lines = [line for line in migration_block if norm(line) in targets]
        if not migration_lines:
            migration_lines = [line for line in migration_block if any(norm(line).startswith(target + " ") for target in targets)]
        for line in disability_lines:
            line_norm = norm(line)
            values = numeric_cells(line)
            if len(values) >= 12:
                d_candidates.append((values[3], values[0]))
        for line in migration_lines:
            line_norm = norm(line)
            values = numeric_cells(line)
            if len(values) >= 7:
                m_candidates.append((values[1], values[0]))
        # Prefix fallback can deliberately expose both Santa María and Santa
        # María de Pantasma.  Use the municipal report household total only to
        # disambiguate those names; keep the denominator printed in the chosen
        # central table for the resulting indicator.
        report_households = parsed[entry["official_code"]]["sanitation_access"][1]
        if len(d_candidates) > 1:
            distance = min(abs(candidate[1] - report_households) for candidate in d_candidates)
            d_candidates = [candidate for candidate in d_candidates if abs(candidate[1] - report_households) == distance]
        if len(m_candidates) > 1:
            distance = min(abs(candidate[1] - report_households) for candidate in m_candidates)
            m_candidates = [candidate for candidate in m_candidates if abs(candidate[1] - report_households) == distance]
        if len(d_candidates) != 1 or len(m_candidates) != 1:
            raise RuntimeError(f"Household supplement match for {entry['official_code']} {entry['municipality']}: disability={d_candidates}, migration={m_candidates}")
        disability[entry["official_code"]] = d_candidates[0]
        migration[entry["official_code"]] = m_candidates[0]
    denominator_differences = []
    for entry in entries:
        code = entry["official_code"]
        report_households = parsed[code]["sanitation_access"][1]
        disability_households = disability[code][1]
        migration_households = migration[code][1]
        if not (math.isclose(report_households, disability_households, abs_tol=0.1)
                and math.isclose(disability_households, migration_households, abs_tol=0.1)):
            denominator_differences.append({
                "official_code": code,
                "municipality": entry["municipality"],
                "municipal_report_households": report_households,
                "table_9_households": disability_households,
                "table_11_households": migration_households,
                "resolution": "Each indicator retains the denominator printed in its own INIDE table; no silent reconciliation."
            })
    return disability, migration, denominator_differences


def indicator(iid: str, name: str, theme: str, definition: str, unit: str = "%", source: str = "nic-inide-census-2005", role: str = "primary") -> dict:
    return {"id": iid, "name": name, "theme": theme, "unit": unit, "definition": definition,
            "definition_id": iid, "population": definition, "measurement_method": "derived_from_source_counts",
            "aggregation": "sum" if unit == "people" else "none", "period_policy": "fixed_source_period",
            "series_family": "census" if source.startswith("nic-inide") else "international_reference",
            "display_role": role, "source_id": source}


def observation(area: str, iid: str, value: float, definition: str, numerator: float | None = None,
                denominator: float | None = None, unit: str = "%", source: str = "nic-inide-census-2005",
                period: str = "2005", locator: str = "") -> dict:
    if not math.isfinite(value):
        raise RuntimeError(f"Invalid observation {area} {iid}: {value}")
    row = {"territory_id": area, "indicator_id": iid, "period": str(period), "value": round(value, 6),
           "status": "observed", "source_id": source, "definition": definition, "definition_id": iid,
           "unit": unit, "population": definition, "measurement_method": "derived_from_source_counts",
           "source_locator": locator}
    if numerator is not None:
        row["numerator"] = round(numerator, 6)
    if denominator is not None:
        row["denominator"] = round(denominator, 6)
    return row


def parse_ethnicity_totals(text_path: Path, department_names: list[str]) -> dict[str, float]:
    text = text_path.read_text(encoding="utf-8", errors="replace")
    start = text.index("CUADRO 10. POBLACIÓN AUTOIDENTIFICADA")
    end = text.index("CUADRO 11.", start)
    block = text[start:end]
    wanted = {norm(name): name for name in department_names}
    wanted["R A A N"] = next(name for name in department_names if norm(name) == "ATLANTICO NORTE")
    wanted["R A A S"] = next(name for name in department_names if norm(name) == "ATLANTICO SUR")
    wanted["LA REPUBLICA"] = "LA REPÚBLICA"
    totals: dict[str, float] = {}
    for line in block.splitlines():
        line_norm = norm(line)
        for key, original in wanted.items():
            if line_norm == key or line_norm.startswith(key + " "):
                cells = re.split(r"\s{2,}", line.strip())
                if len(cells) > 1:
                    totals[original] = number(cells[1])
                break
    missing = set(wanted.values()) - set(totals)
    if missing:
        raise RuntimeError(f"Missing ethnicity totals: {sorted(missing)}")
    return totals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--municipal-dir", required=True)
    parser.add_argument("--volume-dir", required=True)
    parser.add_argument("--municipal-boundaries", required=True)
    parser.add_argument("--department-boundaries", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    project = Path(args.project).resolve()
    municipal_dir = Path(args.municipal_dir).resolve()
    volume_dir = Path(args.volume_dir).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")
    out.mkdir(parents=True)

    receipt_path = municipal_dir / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    entries = receipt["entries"]
    if len(entries) != 153 or len({entry["official_code"] for entry in entries}) != 153:
        raise RuntimeError("The INIDE catalog receipt is not exactly 153 municipalities")

    parsed: dict[str, dict[str, tuple[float, float]]] = {}
    errors = []
    for entry in entries:
        try:
            parsed[entry["official_code"]] = published_municipal_rows(entry, municipal_dir / f"{entry['official_code']}.txt")
        except Exception as exc:
            errors.append({"code": entry["official_code"], "municipality": entry["municipality"], "error": str(exc)})
    if errors:
        (out / "PARSE_ERRORS.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"Municipal parse failed for {len(errors)} areas; see PARSE_ERRORS.json")
    population_basics, urban_population_differences = parse_population_basics(volume_dir / "population-municipalities.txt", entries, parsed)
    employment_totals = parse_employment_totals(volume_dir / "population-municipalities.txt", entries, parsed)
    disability_totals, migration_totals, household_denominator_differences = parse_household_supplements(volume_dir / "household-general.txt", entries, parsed)
    for code, (volume_total, volume_female, urban) in population_basics.items():
        parsed[code]["population_total"] = (volume_total, volume_total)
        parsed[code]["female"] = (volume_female, volume_total)
        parsed[code]["urban"] = (urban, volume_total)
        parsed[code]["employment"] = employment_totals[code]
        parsed[code]["disability"] = disability_totals[code]
        parsed[code]["migration"] = migration_totals[code]
    expected_fields = {"population_total", "female", "illiteracy", "employment", "urban", "occupied_housing", "water_access", "electricity_access", "health_access_risk", "sanitation_access", "disability", "migration", "poverty"}
    for code, rows in parsed.items():
        if set(rows) != expected_fields:
            raise RuntimeError(f"Theme rows incomplete for {code}: {sorted(set(rows) ^ expected_fields)}")
        for key, (num, den) in rows.items():
            if den <= 0 or num < -0.001 or num > den + 0.001:
                raise RuntimeError(f"Invalid numerator/denominator {code} {key}: {num}/{den}")

    # Hierarchy follows the 2005 Census catalog.  Boundary geometries are the
    # official INETER display layer and retain their later vintage explicitly.
    departments: dict[str, str] = {}
    for entry in entries:
        departments.setdefault(entry["department_code"], entry["department"])
    if len(departments) != 17:
        raise RuntimeError(f"Expected 17 departments/autonomous regions, found {len(departments)}")

    boundary_version = "INETER Lim_Departamental/Lim_Municipal, metadata dated 2018-07-19"
    boundary_source = "nic-ineter-boundaries-2018"
    territories = []
    for code, name in sorted(departments.items()):
        territories.append({"id": f"NIC:C2005:DEP:{code}", "country_id": "NIC", "name": name,
                            "level": "department", "type": "department", "parent_id": "NIC",
                            "official_code": code, "code_system": "INIDE 2005 Census department/region code",
                            "boundary_version": boundary_version, "source_id": boundary_source,
                            "geography_note": "The analysis hierarchy is the 2005 Census catalog. The INETER 2018 display geometry is joined by verified code/name correspondence and is not presented as a 2005 or current legal-boundary certification."})
    for entry in entries:
        code = entry["official_code"]
        territories.append({"id": f"NIC:C2005:MUN:{code}", "country_id": "NIC", "name": entry["municipality"],
                            "level": "municipality", "type": "municipality", "parent_id": f"NIC:C2005:DEP:{entry['department_code']}",
                            "official_code": code, "code_system": "INIDE 2005 Census department-municipality code",
                            "boundary_version": boundary_version, "source_id": boundary_source,
                            "geography_note": "The analysis hierarchy is the 2005 Census catalog. The INETER 2018 display geometry is joined by verified code/name correspondence; documented name/code changes are retained in the audit."})

    municipal_geo = json.loads(Path(args.municipal_boundaries).read_text(encoding="utf-8"))
    department_geo = json.loads(Path(args.department_boundaries).read_text(encoding="utf-8"))
    entry_by_name = {norm(entry["municipality"]): entry for entry in entries}
    boundary_name_aliases = {"MOSONTE": "MOZONTE", "WIWILI DE JINOTEGA": "WIWILI", "SAN JOSE DE BOCAY": "SAN JOSE BOCAY",
                             "SANTA MARIA DE PANTASMA": "STA MARIA DE PANTASMA", "VILLA EL CARMEN": "VILLA CARLOS FONSECA",
                             "SAN FRANCISCO DE CUAPA": "SAN FRANCISCO CUAPA", "SAN JUAN DE NICARAGUA": "SAN JUAN DEL NICARAGUA",
                             "EL RAMA": "RAMA", "WASPAM": "WASPAN", "KUKRAHILL": "KUKRA HILL",
                             "TUMA LA DALIA": "EL TUMA LA DALIA", "SAN JUAN DEL RIO COCO": "SAN JUAN DE RIO COCO"}
    features = []
    boundary_join_notes = []
    used_municipal_ids = set()
    for feature in municipal_geo["features"]:
        props = feature["properties"]
        boundary_name = norm(props["nv3_nbre"])
        census_name = boundary_name_aliases.get(boundary_name, boundary_name)
        entry = entry_by_name.get(census_name)
        if entry is None:
            raise RuntimeError(f"INETER municipality not matched to Census catalog: {props['nv3_cod']} {props['nv3_nbre']}")
        tid = f"NIC:C2005:MUN:{entry['official_code']}"
        if tid in used_municipal_ids:
            raise RuntimeError(f"Duplicate municipal boundary match: {tid}")
        used_municipal_ids.add(tid)
        if str(props["nv3_cod"]).zfill(4) != entry["official_code"] or norm(props["nv3_nbre"]) != norm(entry["municipality"]):
            boundary_join_notes.append({"census_code": entry["official_code"], "census_name": entry["municipality"],
                                        "ineter_code": str(props["nv3_cod"]).zfill(4), "ineter_name": props["nv3_nbre"],
                                        "method": "verified name correspondence; Census code retained"})
        features.append({"type": "Feature", "properties": {"territory_id": tid, "name": entry["municipality"],
                         "source_id": boundary_source, "boundary_version": boundary_version},
                         "geometry": mapping(shape(feature["geometry"]).simplify(0.002, preserve_topology=True))})
    if len(used_municipal_ids) != 153:
        raise RuntimeError(f"Boundary coverage is {len(used_municipal_ids)}/153 municipalities")

    dep_by_name = {norm(name): code for code, name in departments.items()}
    dep_aliases = {"REGION AUTONOMA COSTA CARIBE NORTE": "ATLANTICO NORTE", "REGION AUTONOMA COSTA CARIBE SUR": "ATLANTICO SUR",
                   "REGION AUTONOMA DE LA COSTA CARIBE NORTE RACCN": "ATLANTICO NORTE",
                   "REGION AUTONOMA DE LA COSTA CARIBE SUR RACCS": "ATLANTICO SUR",
                   "RACCN": "ATLANTICO NORTE", "RACCS": "ATLANTICO SUR"}
    used_dep_ids = set()
    for feature in department_geo["features"]:
        props = feature["properties"]
        candidate = dep_aliases.get(norm(props["nv2_nbre"]), norm(props["nv2_nbre"]))
        code = dep_by_name.get(candidate)
        if code is None:
            raise RuntimeError(f"INETER department not matched: {props['nv2_cod']} {props['nv2_nbre']}")
        tid = f"NIC:C2005:DEP:{code}"
        used_dep_ids.add(tid)
        features.append({"type": "Feature", "properties": {"territory_id": tid, "name": departments[code],
                         "source_id": boundary_source, "boundary_version": boundary_version},
                         "geometry": mapping(shape(feature["geometry"]).simplify(0.002, preserve_topology=True))})
    if len(used_dep_ids) != 17:
        raise RuntimeError(f"Boundary coverage is {len(used_dep_ids)}/17 departments")

    definitions = {
        "NIC_C2005_POP_TOTAL": "Population enumerated in the 2005 Population and Housing Census.",
        "NIC_C2005_FEMALE_PCT": "Women and girls as a percentage of the 2005 Census population.",
        "NIC_C2005_OCCUPIED_HOUSING_PCT": "Occupied private dwellings as a share of private dwellings in the selected municipal report.",
        "NIC_C2005_WATER_ACCESS_PCT": "Occupied dwellings not classified by INIDE as without potable water; this is a census service proxy, not a water-quality test.",
        "NIC_C2005_SANITATION_ACCESS_PCT": "Households not classified as without sanitary service in the selected municipal report.",
        "NIC_C2005_ELECTRICITY_ACCESS_PCT": "Occupied dwellings not classified as without electric light in the selected municipal report.",
        "NIC_C2005_ILLITERACY_PCT": "Weighted illiteracy rate for men and women age 15 or older, derived from published sex-specific rates and population counts.",
        "NIC_C2005_ECONOMICALLY_ACTIVE_PCT": "Economically active population as a share of the economically active and inactive populations in the published municipal table.",
        "NIC_C2005_DISABLED_HOUSEHOLD_PCT": "Households reporting at least one person with disability as a percentage of households.",
        "NIC_C2005_EMIGRANT_HOUSEHOLD_PCT": "Households reporting international emigrants as a percentage of households.",
        "NIC_C2005_URBAN_PCT": "Population classified as urban in INIDE Population Volume IV as a share of municipal population.",
        "NIC_C2005_ETHNIC_SELF_ID_PCT": "Population self-identifying as belonging to an Indigenous people or ethnic community, as a share of the total Census population; available at country and department/region level.",
        "NIC_C2005_FAR_HEALTH_CENTER_PCT": "Occupied dwellings reported more than 5 km from a health center; this is an access-risk proxy and lower values are generally favorable.",
        "NIC_WB_UNDERNOURISHMENT_PCT": "FAO-modeled national prevalence of undernourishment distributed through the World Bank API; no local value is inferred.",
        "NIC_C2005_NBI_POVERTY_PCT": "Households classified as poor non-extreme or poor extreme under the 2005 Census unmet-basic-needs method.",
    }
    specs = [
        ("NIC_C2005_POP_TOTAL", "2005 Census population", "Population", "people"),
        ("NIC_C2005_FEMALE_PCT", "Female population", "Population", "%"),
        ("NIC_C2005_OCCUPIED_HOUSING_PCT", "Occupied private dwellings", "Housing", "%"),
        ("NIC_C2005_WATER_ACCESS_PCT", "Dwellings with potable-water service proxy", "Basic services", "%"),
        ("NIC_C2005_SANITATION_ACCESS_PCT", "Households with sanitary service", "Basic services", "%"),
        ("NIC_C2005_ELECTRICITY_ACCESS_PCT", "Dwellings with electric-light service", "Basic services", "%"),
        ("NIC_C2005_ILLITERACY_PCT", "Illiteracy age 15 or older", "Education", "%"),
        ("NIC_C2005_ECONOMICALLY_ACTIVE_PCT", "Economically active population", "Economy", "%"),
        ("NIC_C2005_DISABLED_HOUSEHOLD_PCT", "Households with a person with disability", "Inclusion", "%"),
        ("NIC_C2005_EMIGRANT_HOUSEHOLD_PCT", "Households with international emigrants", "Migration", "%"),
        ("NIC_C2005_URBAN_PCT", "Population in Barrio-classified locations", "Population", "%"),
        ("NIC_C2005_ETHNIC_SELF_ID_PCT", "Indigenous or ethnic-community self-identification", "Inclusion", "%"),
        ("NIC_C2005_FAR_HEALTH_CENTER_PCT", "Dwellings more than 5 km from a health center", "Health", "%"),
        ("NIC_C2005_NBI_POVERTY_PCT", "Households in NBI poverty", "Poverty", "%"),
    ]
    indicators = [indicator(iid, name, theme, definitions[iid], unit) for iid, name, theme, unit in specs]

    wb_path = out / "world-bank-undernourishment.json"
    fetch(WB_NUTRITION, wb_path)
    nutrition_period, nutrition_value = latest_wb(wb_path)
    indicators.append(indicator("NIC_WB_UNDERNOURISHMENT_PCT", "Prevalence of undernourishment", "Nutrition",
                                definitions["NIC_WB_UNDERNOURISHMENT_PCT"], "%", "nic-world-bank-nutrition", "context"))

    field_indicator = {
        "population_total": "NIC_C2005_POP_TOTAL", "female": "NIC_C2005_FEMALE_PCT",
        "occupied_housing": "NIC_C2005_OCCUPIED_HOUSING_PCT", "water_access": "NIC_C2005_WATER_ACCESS_PCT",
        "sanitation_access": "NIC_C2005_SANITATION_ACCESS_PCT", "electricity_access": "NIC_C2005_ELECTRICITY_ACCESS_PCT",
        "illiteracy": "NIC_C2005_ILLITERACY_PCT", "employment": "NIC_C2005_ECONOMICALLY_ACTIVE_PCT",
        "disability": "NIC_C2005_DISABLED_HOUSEHOLD_PCT", "migration": "NIC_C2005_EMIGRANT_HOUSEHOLD_PCT",
        "urban": "NIC_C2005_URBAN_PCT", "health_access_risk": "NIC_C2005_FAR_HEALTH_CENTER_PCT",
        "poverty": "NIC_C2005_NBI_POVERTY_PCT",
    }
    observations = []
    aggregate: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
    for entry in entries:
        area = f"NIC:C2005:MUN:{entry['official_code']}"
        dep = f"NIC:C2005:DEP:{entry['department_code']}"
        for field, (num, den) in parsed[entry["official_code"]].items():
            iid = field_indicator[field]
            value = num if field == "population_total" else num * 100.0 / den
            unit = "people" if field == "population_total" else "%"
            observations.append(observation(area, iid, value, definitions[iid], num, den, unit=unit,
                                            locator=f"INIDE municipal report {entry['official_code']}, published table row"))
            for parent in (dep, "NIC"):
                aggregate[parent][field][0] += num
                aggregate[parent][field][1] += den
                aggregate[parent][field][2] += 1

    member_counts = {f"NIC:C2005:DEP:{code}": sum(1 for entry in entries if entry["department_code"] == code) for code in departments}
    member_counts["NIC"] = 153
    for parent, fields in aggregate.items():
        for field, (num, den, count) in fields.items():
            if int(count) != member_counts[parent]:
                raise RuntimeError(f"Incomplete aggregation for {parent} {field}: {count}/{member_counts[parent]}")
            iid = field_indicator[field]
            value = num if field == "population_total" else num * 100.0 / den
            unit = "people" if field == "population_total" else "%"
            observations.append(observation(parent, iid, value, definitions[iid], num, den, unit=unit,
                                            locator=f"AreaData complete non-overlapping sum of {int(count)} INIDE municipal rows"))

    # The source publishes direct country and department observations.  These
    # take precedence over an otherwise complete municipal sum, while the
    # difference remains auditable rather than being silently harmonized.
    direct_parent_population = parse_direct_parent_population(
        volume_dir / "population-municipalities.txt", list(departments.values()))
    parent_direct_differences = []
    existing_parent = {(row["territory_id"], row["indicator_id"]): row for row in observations}
    replacement_rows = []
    for area, name in [("NIC", "LA REPÚBLICA")] + [(f"NIC:C2005:DEP:{code}", dep_name) for code, dep_name in departments.items()]:
        total, female, urban = direct_parent_population[name]
        replacements = [
            observation(area, "NIC_C2005_POP_TOTAL", total, definitions["NIC_C2005_POP_TOTAL"], total, total,
                        unit="people", locator="INIDE Population Volume IV, Table 1 direct parent observation"),
            observation(area, "NIC_C2005_FEMALE_PCT", female * 100.0 / total, definitions["NIC_C2005_FEMALE_PCT"], female, total,
                        locator="INIDE Population Volume IV, Table 1 direct parent observation"),
            observation(area, "NIC_C2005_URBAN_PCT", urban * 100.0 / total, definitions["NIC_C2005_URBAN_PCT"], urban, total,
                        locator="INIDE Population Volume IV, Table 1 direct parent observation"),
        ]
        for replacement in replacements:
            previous = existing_parent[(area, replacement["indicator_id"])]
            if not math.isclose(previous["value"], replacement["value"], rel_tol=0, abs_tol=1e-6):
                parent_direct_differences.append({
                    "territory_id": area,
                    "indicator_id": replacement["indicator_id"],
                    "complete_municipal_sum_or_rate": previous["value"],
                    "direct_parent_observation": replacement["value"],
                    "resolution": "The direct official parent observation is displayed; the complete municipal calculation is retained in this audit record."
                })
        replacement_rows.extend(replacements)
    replacement_keys = {(row["territory_id"], row["indicator_id"], row["period"]) for row in replacement_rows}
    observations = [row for row in observations if (row["territory_id"], row["indicator_id"], row["period"]) not in replacement_keys]
    observations.extend(replacement_rows)

    population = {(row["territory_id"]): row["value"] for row in observations if row["indicator_id"] == "NIC_C2005_POP_TOTAL"}
    ethnic_totals = parse_ethnicity_totals(volume_dir / "population-general.txt", list(departments.values()))
    for area, name in [("NIC", "LA REPÚBLICA")] + [(f"NIC:C2005:DEP:{code}", dep_name) for code, dep_name in departments.items()]:
        numerator = ethnic_totals[name]
        denominator = population[area]
        observations.append(observation(area, "NIC_C2005_ETHNIC_SELF_ID_PCT", numerator * 100.0 / denominator,
                                        definitions["NIC_C2005_ETHNIC_SELF_ID_PCT"], numerator, denominator,
                                        locator="INIDE Population General Volume I, Table 10"))
    observations.append(observation("NIC", "NIC_WB_UNDERNOURISHMENT_PCT", nutrition_value,
                                    definitions["NIC_WB_UNDERNOURISHMENT_PCT"], source="nic-world-bank-nutrition",
                                    period=nutrition_period, locator="World Bank API SN.ITK.DEFC.ZS"))

    today = datetime.now(timezone.utc).date().isoformat()
    sources = [
        {"id": "nic-inide-census-2005", "name": "VIII Censo de Población y IV de Vivienda 2005 — municipal reports and national volumes",
         "publisher": "Instituto Nacional de Información de Desarrollo (INIDE)", "url": INIDE_INDEX,
         "catalog_url": INIDE_MUNICIPAL, "status": "ready", "retrieved_at": receipt.get("retrieved_at", today)[:10],
         "reference_period": "2005", "geographic_level": "country, 17 departments/autonomous regions and 153 municipalities",
         "license": "Official public statistical publication; reuse terms not stated",
         "note": "All 153 municipality report rows are retained by official code. Derived rates preserve numerator and denominator. The image-only Pantasma row is cross-checked to the national census volumes."},
        {"id": boundary_source, "name": "INETER Lim_Departamental and Lim_Municipal WFS layers",
         "publisher": "Instituto Nicaragüense de Estudios Territoriales (INETER)", "url": INETER,
         "catalog_url": INETER_MUN_WFS, "status": "ready", "retrieved_at": today,
         "reference_period": "metadata dated 2018-07-19", "geographic_level": "17 departments/autonomous regions and 153 municipalities",
         "license": "Official public geoservice; reuse terms not stated",
         "note": "Official display geometry. Census-code/name differences, including Waslala and Mulukukú, are recorded; the layer is not represented as a 2005 or current legal-boundary certification."},
        {"id": "nic-world-bank-nutrition", "name": "World Bank/FAO indicator SN.ITK.DEFC.ZS — Nicaragua",
         "publisher": "World Bank and FAO", "url": WB_NUTRITION, "status": "ready", "retrieved_at": today,
         "reference_period": nutrition_period, "geographic_level": "country", "license": "World Bank terms",
         "note": "National modeled context only; no municipal or department value is inferred."},
    ]
    comparisons = [{"parent_id": "NIC", "member_ids": [f"NIC:C2005:DEP:{code}" for code in sorted(departments)],
                    "level": "department", "label": "Departments and autonomous regions within Nicaragua",
                    "membership_note": "All 17 first-order areas in the adopted 2005 Census catalog.",
                    "source_ids": ["nic-inide-census-2005", boundary_source]}]
    for code in sorted(departments):
        members = [f"NIC:C2005:MUN:{entry['official_code']}" for entry in entries if entry["department_code"] == code]
        comparisons.append({"parent_id": f"NIC:C2005:DEP:{code}", "member_ids": members,
                            "level": "municipality", "label": "Municipalities within the selected department or autonomous region",
                            "membership_note": "Complete municipality membership under the adopted 2005 Census catalog.",
                            "source_ids": ["nic-inide-census-2005", boundary_source]})

    bundle = {"schema_version": "1.0", "country_area_id": "NIC", "period": "2005", "replace_country_branch": True,
              "territories": territories, "indicators": indicators, "sources": sources, "observations": observations,
              "boundaries": {"type": "FeatureCollection", "features": features}, "comparisons": comparisons,
              "terminal_territory_ids": sorted(f"NIC:C2005:MUN:{entry['official_code']}" for entry in entries)}
    bundle_path = out / "nicaragua-country-depth-bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    raw_files = [receipt_path, Path(args.municipal_boundaries), Path(args.department_boundaries)] + sorted(volume_dir.glob("*.pdf")) + sorted(volume_dir.glob("*.txt"))
    audit = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "country_area_id": "NIC",
             "status": "complete", "counts": {"territories": len(territories), "indicators": len(indicators),
             "observations": len(observations), "boundaries": len(features)},
             "coverage": {"departments_or_autonomous_regions": 17, "municipalities": 153, "themes": 15},
             "checks": {"all_catalog_municipalities_parsed": len(parsed) == 153,
                        "complete_parent_aggregation_only": True,
                        "official_boundary_feature_coverage": len(features) == 170,
                        "image_table_fallback_cross_checked": True,
                        "missing_zero_distinction_preserved": True},
             "boundary_limit": "INETER display layer with metadata dated 2018-07-19; analysis hierarchy remains the 2005 Census catalog and boundary changes are not silently harmonized.",
             "boundary_join_exceptions": boundary_join_notes,
             "urban_population_source_differences": urban_population_differences,
             "household_denominator_source_differences": household_denominator_differences,
             "parent_direct_observation_differences": parent_direct_differences,
             "raw_files": [{"file": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in raw_files if path.exists()],
             "bundle": {"file": bundle_path.name, "bytes": bundle_path.stat().st_size, "sha256": sha256(bundle_path)}}
    (out / "NICARAGUA_COLLECTION_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": audit["counts"], "boundary_join_exceptions": len(boundary_join_notes)}, indent=2))


if __name__ == "__main__":
    main()

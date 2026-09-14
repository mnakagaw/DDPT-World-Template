"""Deterministic parsers for adopted Central America census PDF tables."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader


HONDURAS_DEPARTMENTS = {
    "01": "Atlántida",
    "02": "Colón",
    "03": "Comayagua",
    "04": "Copán",
    "05": "Cortés",
    "06": "Choluteca",
    "07": "El Paraíso",
    "08": "Francisco Morazán",
    "09": "Gracias a Dios",
    "10": "Intibucá",
    "11": "Islas de la Bahía",
    "12": "La Paz",
    "13": "Lempira",
    "14": "Ocotepeque",
    "15": "Olancho",
    "16": "Santa Bárbara",
    "17": "Valle",
    "18": "Yoro",
}

NICARAGUA_FIRST_ORDER = [
    "Nueva Segovia", "Jinotega", "Madriz", "Estelí", "Chinandega", "León",
    "Matagalpa", "Boaco", "Managua", "Masaya", "Chontales", "Granada",
    "Carazo", "Rivas", "Río San Juan", "R.A.A.N.", "R.A.A.S.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def comma_int(value: str) -> int:
    return int(value.replace(",", ""))


def spaced_int(value: str) -> int | None:
    return None if value == "-" else int(value.replace(" ", ""))


def extract_honduras_tome1(path: Path) -> dict:
    reader = PdfReader(path)
    national = None
    departments = {}
    pattern = re.compile(r"^\s*(\d{2})\s+(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)")
    for page in reader.pages[15:105]:
        for line in (page.extract_text() or "").splitlines():
            if national is None:
                match_national = re.search(r"Total nacional\s+(\d{1,3}(?:,\d{3})+)", line)
                if match_national:
                    national = comma_int(match_national.group(1))
            match = pattern.match(line)
            if not match or match.group(1) not in HONDURAS_DEPARTMENTS:
                continue
            code, name, value = match.group(1), match.group(2).strip(), comma_int(match.group(3))
            if name != HONDURAS_DEPARTMENTS[code]:
                raise ValueError(f"Unexpected Honduras department label {code}: {name}")
            departments.setdefault(code, {"code": code, "name": name, "population": value})
        if national is not None and len(departments) == len(HONDURAS_DEPARTMENTS):
            break
    if national != 8_303_771 or len(departments) != 18:
        raise ValueError(f"Honduras Tome 1 population extraction incomplete: national={national}, departments={len(departments)}")
    department_sum = sum(row["population"] for row in departments.values())
    difference = department_sum - national
    if difference != -1:
        raise ValueError(f"Unexpected Honduras department/national difference: {difference}")
    return {
        "national": national,
        "departments": list(departments.values()),
        "department_sum": department_sum,
        "department_sum_difference": difference,
    }


def _extract_honduras_municipal_pdf(root: Path, entry: dict, department_totals: dict) -> dict:
    file = root.joinpath(*entry["filename"].split("/"))
    if sha256(file) != entry["sha256"]:
        raise ValueError(f"Honduras municipal receipt hash mismatch: {entry['filename']}")
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        completed = subprocess.run(
            [pdftotext, "-f", "1", "-l", "25", "-layout", str(file), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        full_text = completed.stdout.decode("utf-8", errors="replace")
        first_text = full_text.split("\f", 1)[0]
    else:
        reader = PdfReader(file)
        extracted_pages = [(page.extract_text() or "") for page in reader.pages[:min(25, len(reader.pages))]]
        first_text = extracted_pages[0]
        full_text = "\n".join(extracted_pages)
    # Some INE cover PDFs concatenate the municipality name and code
    # (for example ``Santa Lucía10-15``), so a leading word boundary is unsafe.
    code_match = re.search(r"(\d{2}-\d{2})\b", first_text)
    if not code_match:
        raise ValueError(f"Municipal code not found: {entry['filename']}")
    code = code_match.group(1)
    name = None
    for line in first_text.splitlines():
        if code not in line or "Municipio" not in line:
            continue
        prefix = line[:line.index(code)].strip()
        name = re.sub(r"^.*?Municipio(?:\s+de|\s+del)?\s+", "", prefix, flags=re.IGNORECASE).strip(" ,.-")
        if name:
            break
    if not name:
        raise ValueError(f"Municipal name not found: {entry['filename']}")
    population = department_value = None
    metric_line = None
    position = full_text.find("Población total por sexo")
    if position >= 0:
        chunk = " ".join(full_text[position:position + 1000].splitlines())
        # Municipality totals can be below 1,000. Requiring a comma silently
        # skipped those values and shifted the sex subtotals into this pair.
        values = re.findall(r"(?<!\d)\d{1,3}(?:,\d{3})*(?!\d)", chunk)
        if len(values) >= 2:
            department_value, population = comma_int(values[0]), comma_int(values[1])
            metric_line = chunk[:500]
    department_code = code[:2]
    if population is None or department_code not in department_totals:
        raise ValueError(f"Municipal population not found: {entry['filename']}")
    if department_value != department_totals[department_code]:
        raise ValueError(f"Department total mismatch in {code}: {department_value} != {department_totals[department_code]}")
    return {
        "code": code,
        "name": name,
        "department_code": department_code,
        "population": population,
        "pdf_url": entry["final_url"],
        "post_url": entry["post_url"],
        "source_sha256": entry["sha256"],
        "metric_excerpt": metric_line,
    }


def extract_honduras_municipal_reports(root: Path, receipt: dict, departments: list[dict]) -> list[dict]:
    entries = receipt.get("entries", [])
    if len(entries) != 298 or any(entry.get("status") != "acquired" for entry in entries):
        raise ValueError("Honduras municipal receipt must contain 298 acquired reports")
    department_totals = {row["code"]: row["population"] for row in departments}
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda entry: _extract_honduras_municipal_pdf(root, entry, department_totals), entries))
    rows.sort(key=lambda row: row["code"])
    if len({row["code"] for row in rows}) != 298:
        raise ValueError("Honduras municipal codes are not unique and complete")
    # The official Esparta PDF prints 14,559, identical to San Francisco, and
    # using it leaves Atlántida 3,890 below its official department total. The
    # cover and table identity disagree with the table contents, so preserve
    # the published candidate for audit but do not expose it as an observation.
    esparta = next(row for row in rows if row["code"] == "01-03")
    san_francisco = next(row for row in rows if row["code"] == "01-06")
    if esparta["population"] != 14_559 or san_francisco["population"] != 14_559:
        raise ValueError("The documented Esparta/San Francisco source conflict changed and needs review")
    esparta["published_population"] = esparta["population"]
    esparta["population"] = None
    esparta["adoption_status"] = "withheld_source_identity_and_reconciliation_conflict"
    unexpected = []
    for code, total in department_totals.items():
        subtotal = sum(row["population"] for row in rows if row["department_code"] == code and row["population"] is not None)
        if code == "01":
            if total - subtotal != 18_449:
                unexpected.append((code, subtotal, total))
            continue
        if abs(subtotal - total) > 2:
            unexpected.append((code, subtotal, total))
    if unexpected:
        raise ValueError(f"Honduras municipality subtotals need review: {unexpected}")
    return rows


def extract_nicaragua_table5(path: Path) -> dict:
    reader = PdfReader(path)
    text = "\n".join(reader.pages[index].extract_text() or "" for index in range(6, 11))
    integer = r"(?:\d{1,3}(?: \d{3})*|-)"
    ratio = r"(?:\d+(?:\.\d+)?|-)"
    pattern = re.compile(rf"^(?P<name>.+?)\s+(?P<n95>{integer})\s+(?P<m95>{integer})\s+(?P<f95>{integer})\s+(?P<r95>{ratio})\s+(?P<n05>{integer})\s+(?P<m05>{integer})\s+(?P<f05>{integer})\s+(?P<r05>{ratio})\s*$")
    national = None
    departments = []
    municipalities = []
    current = None
    unseen_departments = list(NICARAGUA_FIRST_ORDER)
    for raw in text.splitlines():
        match = pattern.match(raw.strip())
        if not match:
            continue
        name = match.group("name").strip()
        value = spaced_int(match.group("n05"))
        if name == "LA REPÚBLICA":
            national = value
            continue
        if unseen_departments and name == unseen_departments[0]:
            current = {"name": name, "population": value, "municipalities": []}
            departments.append(current)
            unseen_departments.pop(0)
            continue
        if current is not None and value is not None:
            clean_name = name.removesuffix("*").strip()
            row = {"name": clean_name, "published_name": name, "population": value}
            current["municipalities"].append(row)
            municipalities.append(row)
    if national != 5_142_098 or unseen_departments or len(departments) != 17 or len(municipalities) != 153:
        raise ValueError(f"Nicaragua Table 5 extraction incomplete: national={national}, departments={len(departments)}, municipalities={len(municipalities)}, unseen={unseen_departments}")
    if sum(row["population"] for row in departments) != national or sum(row["population"] for row in municipalities) != national:
        raise ValueError("Nicaragua department or municipality totals do not reconcile to the national total")
    for department in departments:
        subtotal = sum(row["population"] for row in department["municipalities"])
        if subtotal != department["population"]:
            raise ValueError(f"Nicaragua municipality subtotal does not reconcile for {department['name']}: {subtotal} != {department['population']}")
    return {"national": national, "departments": departments, "municipalities": municipalities}

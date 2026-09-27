"""Build an unpublished Brunei BPP 2021 census candidate from pinned DEPS PDFs.

This adopts published reporting names only. It does not join the 2011
geoBoundaries shapes to the 2021 census or assert unpublished official codes.
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/brunei-bpp2021-source-manifest.json"
SOURCE_A = "brn-deps-bpp2021-annex-a"
SOURCE_B = "brn-deps-bpp2021-annex-b"
SOURCE_C = "brn-deps-bpp2021-annex-c"
DISTRICTS = ("Brunei Muara", "Belait", "Tutong", "Temburong")
MUKIM_COUNTS = (18, 8, 8, 5)
BOUNDARY = "DEPS BPP 2021 reporting geography; official codes and polygons pending"
NUM = re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}(?:,\d{3})+|\d+)(?![A-Za-z0-9])")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_pages(path):
    result = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                            capture_output=True, check=True)
    return result.stdout.decode("utf-8", errors="replace").split("\f")


def pinned(project):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = {}
    for source in manifest["sources"]:
        path = project / source["raw_path"]
        require(path.is_file(), f"Missing PDF: {path}")
        body = path.read_bytes()
        require(body.startswith(b"%PDF") and len(body) == source["bytes"],
                f"Not pinned PDF bytes: {path}")
        require(hashlib.sha256(body).hexdigest() == source["sha256"],
                f"PDF hash changed: {path}")
        sources[source["id"]] = path
    require(len(sources) == 6, "Source manifest count changed")
    return manifest, sources


def numbered_line(line, count):
    tokens = list(NUM.finditer(line))
    if len(tokens) != count:
        return None
    name = line[:tokens[0].start()].strip()
    if not name or not name[0].isalpha():
        return None
    return name, [int(m.group().replace(",", "")) for m in tokens]


def page_rows(page, count):
    return [value for line in page.splitlines()
            if (value := numbered_line(line, count)) is not None]


def read_tables(a_pages, b_pages, c_pages):
    b1 = page_rows(b_pages[2], 10)
    require([n for n, _ in b1] == [*DISTRICTS, "BRUNEI DARUSSALAM"], "B1 roster changed")
    district_b = {n: values for n, values in b1}
    mukims = {}
    b2_parents = {}
    for index, district in enumerate(DISTRICTS):
        rows = page_rows(b_pages[index + 3], 10)
        require(rows[0][0] == district and len(rows) == MUKIM_COUNTS[index] + 1,
                f"B2 roster changed: {district}")
        require(rows[0][1] == district_b[district], f"B1/B2 mismatch: {district}")
        b2_parents[district] = rows[0][1]
        mukims[district] = dict(rows[1:])
        require(len(mukims[district]) == MUKIM_COUNTS[index], f"Duplicate mukim {district}")
    c1 = {}
    for index, district in enumerate(DISTRICTS):
        rows = page_rows(c_pages[index + 4], 12)
        require(rows[0][0] == district and len(rows) == MUKIM_COUNTS[index] + 1,
                f"C1 roster changed: {district}")
        require(set(dict(rows[1:])) == set(mukims[district]), f"B2/C1 mukim mismatch: {district}")
        c1[district] = dict(rows)
    a1 = {}
    for line in a_pages[2].splitlines():
        for label in ("Brunei Citizens", "Permanent Residents", "Temporary Residents"):
            if line.lstrip().startswith(label):
                parsed = numbered_line(line, 15)
                require(parsed is not None and parsed[0] == label, f"A1 row changed: {label}")
                a1[label] = parsed[1]
    require(len(a1) == 3, "A1 status rows missing")
    a2 = []
    for line in a_pages[3].splitlines():
        match = re.match(r"^\s*(\d{2}-\d{2}|85\+)\s+(.+)$", line)
        if match:
            values = [int(m.group().replace(",", "")) for m in NUM.finditer(match[2])]
            if len(values) == 15:
                a2.append((match[1], values))
    require(len(a2) == 18 and a2[0][0] == "00-04" and a2[-1][0] == "85+",
            "A2 age bands changed")
    return district_b, mukims, c1, a1, a2


def audit(district_b, mukims, c1, a1, a2):
    checks = defaultdict(int)
    country = district_b["BRUNEI DARUSSALAM"]
    for i in range(10):
        require(sum(district_b[d][i] for d in DISTRICTS) == country[i],
                f"B1 district sum column {i}")
        checks["b1_national_column_sums"] += 1
    for district in DISTRICTS:
        parent = district_b[district]
        for i in range(10):
            require(sum(values[i] for values in mukims[district].values()) == parent[i],
                    f"B2 mukim sum {district} column {i}")
            checks["b2_district_column_sums"] += 1
        for name, values in [(district, parent), *mukims[district].items()]:
            for offset in (0, 5):
                require(values[offset] == values[offset + 1] + values[offset + 2],
                        f"B1/B2 sex sum {district}/{name}/{offset}")
                checks["b_sex_sums"] += 1
            c = c1[district][name]
            require(c[:3] == parent[5:8] if name == district else c[:3] == values[5:8],
                    f"C1/B2 population mismatch {district}/{name}")
            for sex in range(3):
                require(c[sex] == c[sex + 3] + c[sex + 6] + c[sex + 9],
                        f"C1 status sum {district}/{name}/{sex}")
                checks["c1_status_sums"] += 1
            for offset in (0, 3, 6, 9):
                require(c[offset] == c[offset + 1] + c[offset + 2],
                        f"C1 sex sum {district}/{name}/{offset}")
                checks["c1_sex_sums"] += 1
    for status_index, label in enumerate(("Brunei Citizens", "Permanent Residents", "Temporary Residents")):
        a = a1[label]
        for geo_index, district in enumerate((None, *DISTRICTS)):
            triple = a[geo_index * 3:geo_index * 3 + 3]
            require(triple[0] == triple[1] + triple[2], f"A1 sex sum {label}/{district}")
            if district:
                require(triple == c1[district][district][3 + status_index * 3:6 + status_index * 3],
                        f"A1/C1 mismatch {label}/{district}")
            else:
                require(sum(a[i * 3] for i in range(1, 5)) == triple[0],
                        f"A1 national mismatch {label}")
            checks["a1_status_geographies"] += 1
    for geo_index, district in enumerate((None, *DISTRICTS)):
        expected = country[5:8] if district is None else district_b[district][5:8]
        for sex in range(3):
            require(sum(values[geo_index * 3 + sex] for _, values in a2) == expected[sex],
                    f"A2 age sum {district}/{sex}")
            checks["a2_age_sums"] += 1
    for name, values in a2:
        for sex in range(3):
            require(values[sex] == sum(values[i * 3 + sex] for i in range(1, 5)),
                    f"A2 district total {name}/{sex}")
            checks["a2_band_district_sums"] += 1
    checks["b1_rows"] = 5
    checks["b2_mukim_rows"] = 39
    checks["c1_district_and_mukim_rows"] = 43
    checks["a1_status_rows"] = 3
    checks["a2_age_band_rows"] = 18
    checks["audited_numeric_cells"] = 5 * 10 + 4 * 10 + 39 * 10 + 43 * 12 + 3 * 15 + 18 * 15
    return dict(checks)


def table_inventory(a_pages, b_pages, c_pages):
    selected = {
        "A1": ("all 15 geography/sex columns audited; Persons by status adopted; sex cells used for validation",
               "2021 national and district residential-status persons"),
        "A2": ("all 15 geography/sex columns and 18 age rows audited; Persons bands summed into 0–14, 15–64, 65+; sex cells used for validation",
               "2021 national and district age groups"),
        "B1": ("all ten 2011/2021 columns audited; five 2021 columns adopted; five 2011 columns withheld pending boundary comparability",
               "2021 national and district population/households/occupied quarters"),
        "B2": ("all ten 2011/2021 columns audited; five 2021 mukim columns adopted; 2011 withheld pending boundary comparability",
               "2021 39 mukim population/households/occupied quarters"),
        "C1": ("all 12 sex/status columns audited; three residential-status Persons cells adopted; total and sex cells validate B1/B2 and A1",
               "2021 district and mukim residential-status persons"),
    }
    inventory = []
    for prefix, pages in (("A", a_pages), ("B", b_pages), ("C", c_pages)):
        seen = set()
        for page in pages[:4]:
            lines = page.splitlines()
            for index, line in enumerate(lines):
                match = re.match(r"^\s*(" + prefix + r"\d+)\s+", line)
                if not match or match[1] in seen:
                    continue
                seen.add(match[1])
                title = next((candidate.strip() for candidate in lines[index + 1:index + 4]
                              if candidate.strip().startswith(("Population by", "Total Population,"))),
                             line.strip())
                decision = selected.get(match[1])
                inventory.append({"table": match[1], "title": title,
                    "assessment": "selected_columns_audited" if decision else "priority_unassessed",
                    "numeric_columns": decision[0] if decision else "unassessed",
                    "adopted_scope": decision[1] if decision else "none; numeric columns and denominators unassessed"})
        expected = {"A": 12, "B": 6, "C": 10}[prefix]
        require(len(seen) == expected, f"Annex {prefix} index changed: {sorted(seen)}")
    return inventory


def slug(name):
    return re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")


def district_id(name):
    return "BRN:DEPS:BPP2021:DISTRICT:" + slug(name)


def mukim_id(district, name):
    return "BRN:DEPS:BPP2021:MUKIM:" + slug(district) + ":" + slug(name)


def build(project, manifest, district_b, mukims, c1, a1, a2, checks, inventory):
    path = project / "data/dashboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data["country"]["id"] == "BRN", "Wrong country candidate")
    data["country"]["geography_note"] = (
        "DEPS 2021 census has four district and 39 mukim reporting rows. Source-derived IDs are provisional, "
        "not official geographic codes. Official codes and 2021-compatible polygons remain pending. "
        "The initial geoBoundaries 2011 polygons are removed. Census counts and World Bank annual estimates remain separate.")
    national = next(t for t in data["territories"] if t["id"] == "BRN")
    national.update({"source_id": SOURCE_B, "boundary_version": BOUNDARY})
    territories = [national]
    for district in DISTRICTS:
        territories.append({"id": district_id(district), "name": district, "level": "adm1",
                            "type": "district", "parent_id": "BRN", "official_code": None,
                            "code_system": "DEPS BPP 2021 reporting name; official code pending",
                            "boundary_version": BOUNDARY, "source_id": SOURCE_B,
                            "reconciliation_status": "Census district row; official code and exact polygon pending"})
        for mukim in mukims[district]:
            territories.append({"id": mukim_id(district, mukim), "name": mukim,
                                "level": "adm2", "type": "mukim", "parent_id": district_id(district),
                                "official_code": None,
                                "code_system": "DEPS BPP 2021 district plus mukim reporting name; official code pending",
                                "boundary_version": BOUNDARY, "source_id": SOURCE_B,
                                "reconciliation_status": "Census mukim row; official code, polygon and kampung crosswalk pending"})
    data["territories"] = territories
    data["boundaries"] = {"type": "FeatureCollection", "features": []}
    source_meta = {
        "brn-deps-bpp2021-report": ("DEPS BPP 2021 demographic, household and housing report", "DEPS", "2021 census", "national to kampung"),
        SOURCE_A: ("DEPS BPP 2021 demographic Annex A", "DEPS", "2021 census", "nation and district"),
        SOURCE_B: ("DEPS BPP 2021 geography Annex B", "DEPS", "2011 and 2021 census columns", "nation, district, mukim and kampung"),
        SOURCE_C: ("DEPS BPP 2021 demographic Annex C", "DEPS", "2021 census", "district, mukim and kampung"),
        "brn-agc-cap248-2022": ("Town and Country Planning Act, Cap. 248, revised 2022", "Attorney General's Chambers", "2022 revised edition", "planning area and development plans"),
        "brn-mof-rkn12-en": ("Twelfth National Development Plan 2024–2029", "Ministry of Finance and Economy", "2024–2029", "national investment programme"),
    }
    sources = {s["id"]: s for s in data["sources"] if s["id"] != "geoboundaries-adm1"}
    for source in manifest["sources"]:
        name, publisher, period, level = source_meta[source["id"]]
        sources[source["id"]] = {"id": source["id"], "name": name, "url": source["url"],
            "catalogue_url": source.get("catalogue_url", manifest["catalogue_url"]),
            "publisher": publisher, "reference_period": period, "geographic_level": level,
            "status": "ready", "retrieved_at": manifest["retrieved_at"],
            "raw_path": source["raw_path"], "sha256": source["sha256"],
            "license": "Official public PDF; redistribution terms to confirm",
            "note": "Original byte length and SHA-256 pinned; acquisition is distinct from table adoption."}
    sources["brn-jpbd-district-plan-catalogue"] = {
        "id": "brn-jpbd-district-plan-catalogue", "name": "JPBD development-plan catalogue",
        "url": "https://www.jpbd.gov.bn/buku-garispanduan-dan-master-plan/",
        "publisher": "Town and Country Planning Department, Ministry of Development",
        "reference_period": "Catalogue checked 2026-09-27; listed plan periods and approval unverified",
        "geographic_level": "nation and four districts", "status": "not_collected",
        "retrieved_at": manifest["retrieved_at"],
        "license": "Link only; book or map body not acquired",
        "note": "Lists one national land-use master plan and four district plans; cover images are not the plan bodies."}
    sources["brn-survey-geoportal"] = {
        "id": "brn-survey-geoportal", "name": "Survey Department Geoportal",
        "url": "https://geoportal.survey.gov.bn/start",
        "publisher": "Survey Department, Ministry of Development",
        "reference_period": "Portal checked 2026-09-27; compatible boundary edition unverified",
        "geographic_level": "national geographic portal; district/mukim codes and polygons unverified",
        "status": "not_collected", "retrieved_at": manifest["retrieved_at"],
        "license": "Portal location only; downloadable geometry and terms not confirmed",
        "note": "Official portal location, not a census-boundary join or acquired code/shape release."}
    data["sources"] = list(sources.values())
    prefix = "BRN_BPP2021_"
    data["indicators"] = [i for i in data["indicators"] if not i["id"].startswith(prefix)]
    data["observations"] = [o for o in data["observations"] if not o["indicator_id"].startswith(prefix)]
    specs = [
        ("POP_TOTAL", "2021 census population", "Population", "people", "All persons enumerated in BPP 2021; distinct from WDI estimates", "B1/B2 2021 Persons"),
        ("POP_MALE", "2021 census males", "Population", "people", "Males enumerated in BPP 2021", "B1/B2 2021 Males"),
        ("POP_FEMALE", "2021 census females", "Population", "people", "Females enumerated in BPP 2021", "B1/B2 2021 Females"),
        ("HOUSEHOLDS", "2021 census households", "Housing", "households", "Households enumerated in BPP 2021", "B1/B2 2021 Households"),
        ("OCCUPIED_QUARTERS", "2021 occupied living quarters", "Housing", "living quarters", "Occupied living quarters enumerated in BPP 2021", "B1/B2 2021 Occupied Living Quarters"),
        ("BRUNEI_CITIZENS", "2021 Brunei citizens", "Residential status", "people", "Brunei citizens in BPP 2021; this is a residential-status category", "A1/C1 Brunei Citizens Persons"),
        ("PERMANENT_RESIDENTS", "2021 permanent residents", "Residential status", "people", "Permanent residents in BPP 2021", "A1/C1 Permanent Residents Persons"),
        ("TEMPORARY_RESIDENTS", "2021 temporary residents", "Residential status", "people", "Temporary residents in BPP 2021", "A1/C1 Temporary Residents Persons"),
        ("AGE_0_14", "2021 population aged 0–14", "Age", "people", "Sum of A2 00–04, 05–09, 10–14 person cells", "Derived from A2 Persons"),
        ("AGE_15_64", "2021 population aged 15–64", "Age", "people", "Sum of A2 15–19 through 60–64 person cells", "Derived from A2 Persons"),
        ("AGE_65_PLUS", "2021 population aged 65+", "Age", "people", "Sum of A2 65–69 through 85+ person cells", "Derived from A2 Persons"),
    ]
    for key, name, theme, unit, population, definition in specs:
        data["indicators"].append({"id": prefix + key, "name": name, "theme": theme,
            "unit": unit, "definition": definition, "population": population,
            "source_id": SOURCE_A if key.startswith("AGE_") else SOURCE_C if key in (
                "BRUNEI_CITIZENS", "PERMANENT_RESIDENTS", "TEMPORARY_RESIDENTS") else SOURCE_B,
            "aggregation": "none", "measurement_method": "DEPS BPP 2021 table cell" if not key.startswith("AGE_") else "sum of published DEPS A2 age-band cells"})
    observations = []
    def add(tid, key, value, source, locator, derived=False):
        observations.append({"territory_id": tid, "indicator_id": prefix + key,
            "period": "2021", "value": value, "status": "observed", "source_id": source,
            "provenance": "calculated" if derived else "source_reported",
            "population_scope": "BPP 2021 enumerated population" if key not in ("HOUSEHOLDS", "OCCUPIED_QUARTERS") else "BPP 2021 housing units",
            "measurement_method": "sum of published DEPS A2 age-band cells" if derived else "DEPS BPP 2021 table cell",
            "boundary_version": BOUNDARY, "source_locator": locator,
            **({"footnote": "AreaData sum of the specified published DEPS Annex A2 Persons age bands; the grouped total is not a separately published table cell."} if derived else {})})
    by_territory = [("BRN", district_b["BRUNEI DARUSSALAM"], "B1 row BRUNEI DARUSSALAM, printed p.109")]
    for district in DISTRICTS:
        by_territory.append((district_id(district), district_b[district], f"B1 row {district}, printed p.109"))
        for mukim, values in mukims[district].items():
            by_territory.append((mukim_id(district, mukim), values,
                                 f"B2 {district}, row {mukim}, printed p.{110 + DISTRICTS.index(district)}"))
    for tid, values, locator in by_territory:
        for key, value, column in zip(("POP_TOTAL", "POP_MALE", "POP_FEMALE", "HOUSEHOLDS", "OCCUPIED_QUARTERS"),
                                      values[5:10], ("Persons", "Males", "Females", "Households", "Occupied Living Quarters")):
            add(tid, key, value, SOURCE_B, f"{locator}, 2021 {column}")
    for district in DISTRICTS:
        for name, values in c1[district].items():
            tid = district_id(district) if name == district else mukim_id(district, name)
            for index, key in enumerate(("BRUNEI_CITIZENS", "PERMANENT_RESIDENTS", "TEMPORARY_RESIDENTS")):
                add(tid, key, values[3 + index * 3], SOURCE_C,
                    f"C1 {district}, row {name}, printed p.{153 + DISTRICTS.index(district)}, {key} Persons")
    for index, (label, key) in enumerate((("Brunei Citizens", "BRUNEI_CITIZENS"),
                                          ("Permanent Residents", "PERMANENT_RESIDENTS"),
                                          ("Temporary Residents", "TEMPORARY_RESIDENTS"))):
        add("BRN", key, a1[label][0], SOURCE_A, f"A1 row {label}, national Persons, printed p.80")
    age_slices = (("AGE_0_14", 0, 3), ("AGE_15_64", 3, 13), ("AGE_65_PLUS", 13, 18))
    for geo_index, tid in enumerate(["BRN", *(district_id(d) for d in DISTRICTS)]):
        for key, start, end in age_slices:
            add(tid, key, sum(values[geo_index * 3] for _, values in a2[start:end]),
                SOURCE_A, f"A2 age bands {a2[start][0]}–{a2[end - 1][0]}, {tid} Persons, printed p.81", True)
    require(len(observations) == 44 * 8 + 5 * 3, "Adopted observation count changed")
    data["observations"].extend(observations)
    data["documents"] = [d for d in data["documents"] if not d["id"].startswith("brn-")]
    data["documents"].extend([
        {"id":"brn-bpp2021-census","territory_id":"BRN","category":"reference","kind":"census_report",
         "title":"BPP 2021 demographic, household and housing report with Annexes A–C",
         "url":manifest["catalogue_url"],"source_id":"brn-deps-bpp2021-report","period":"2021",
         "availability":"body_acquired","official_status":"unverified",
         "note":"Annexes A1/A2, B1/B2 and C1 are audited for selected columns; 23 other annex tables and the main report remain unassessed for adoption."},
        {"id":"brn-cap248-planning-law","territory_id":"BRN","category":"reference","kind":"planning_law",
         "title":"Town and Country Planning Act, Cap. 248, revised 2022",
         "url":sources["brn-agc-cap248-2022"]["url"],"source_id":"brn-agc-cap248-2022","period":"2022 revised edition",
         "availability":"body_acquired","official_status":"unverified",
         "note":"Sections 8–19 establish Planning Authority and Master, District and Local Plans; applicability and later amendments require legal review."},
        {"id":"brn-rkn12-national","territory_id":"BRN","category":"plan","kind":"national_development_plan",
         "title":"RKN12 national development plan 2024–2029",
         "url":sources["brn-mof-rkn12-en"]["url"],"source_id":"brn-mof-rkn12-en","period":"2024–2029",
         "availability":"body_acquired","official_status":"unverified",
         "note":"PDF p.114 lists National Land Use Masterplan and four District Plans for 2026–2045 as projects; planned project listing does not prove approval or completion."},
    ])
    for district in DISTRICTS:
        data["documents"].append({"id":"brn-jpbd-plan-" + slug(district).lower(),
            "territory_id":district_id(district),"category":"plan","kind":"district_plan_catalogue_entry",
            "title":district + " District Plan — JPBD catalogue entry",
            "url":sources["brn-jpbd-district-plan-catalogue"]["url"],
            "source_id":"brn-jpbd-district-plan-catalogue","period":"catalogue period unverified",
            "availability":"link_verified","official_status":"unverified",
            "note":"JPBD describes a district plan, but only a cover image/location was verified. Full text, map, period, approval and relationship to RKN12 2026–2045 project are pending."})
        for mukim in mukims[district]:
            data["documents"].append({"id":"brn-jpbd-parent-plan-" + slug(district).lower() + "-" + slug(mukim).lower(),
                "territory_id":mukim_id(district, mukim),"category":"plan",
                "kind":"parent_district_plan_catalogue_entry",
                "title":district + " District Plan — parent planning area catalogue",
                "url":sources["brn-jpbd-district-plan-catalogue"]["url"],
                "source_id":"brn-jpbd-district-plan-catalogue","period":"catalogue period unverified",
                "availability":"link_verified","official_status":"unverified",
                "note":mukim + " is an internal census diagnosis area within " + district +
                  ". This is the parent district's JPBD catalogue entry, not a mukim plan. Full plan body, map, period and approval are pending."})
    analysis = data["analysis"]
    analysis["default_indicator_id"] = prefix + "POP_TOTAL"
    analysis["latest_values_only"] = True
    analysis["terminal_territory_ids"] = [mukim_id(d, m) for d in DISTRICTS for m in mukims[d]]
    analysis["comparisons"] = [{"parent_id":"BRN","member_ids":[district_id(d) for d in DISTRICTS],
        "label":"Four DEPS 2021 census districts", "membership_note":"Complete B1 national partition; source names only, no polygon join.",
        "source_ids":[SOURCE_B]}]
    analysis["comparisons"].extend({"parent_id":district_id(d),
        "member_ids":[mukim_id(d, m) for m in mukims[d]],
        "label":d + " DEPS 2021 mukims",
        "membership_note":"Complete B2 and C1 census mukim roster; official codes and geometry pending.",
        "source_ids":[SOURCE_B,SOURCE_C]} for d in DISTRICTS)
    data["planning"] = {"title":"District planning source evidence",
        "purpose":"Use district and mukim census baselines to review each district plan's content, approval, budget, execution and evaluation separately.",
        "system":{"label":"Town and Country Planning Act development plans",
            "scope":"Cap. 248 assigns draft Master, District and Local Plans to the Planning Authority, with Minister approval. A district name is the plan geography, not proof that its District Office approves the plan.",
            "cycle":"JPBD catalogue says district plans cover 15–20 years; RKN12 lists 2026–2045 plan projects. Current adopted editions and approval dates are unverified.",
            "source_ids":["brn-agc-cap248-2022","brn-jpbd-district-plan-catalogue","brn-mof-rkn12-en"]},
        "sections":[{"id":"plan","label":"District plan and approval"},
                    {"id":"budget","label":"Allocation and budget"},
                    {"id":"implementation","label":"Execution"},
                    {"id":"evaluation","label":"Official evaluation"},
                    {"id":"reference","label":"Census and planning law"}]}
    data["collection"]["status"] = "partial"
    adapter = "deps-bpp2021-partial-2026-09-27"
    data["collection"]["adapters"] = [a for a in data["collection"]["adapters"] if a != adapter] + [adapter]
    notes = [n for n in data["collection"]["notes"] if not n.startswith((
        "Six official PDFs hash-pinned", "2021 census has 4 districts", "JPBD lists district plans"))]
    data["collection"]["notes"] = notes + [
        "Six official PDFs hash-pinned; DEPS Annex A1/A2, B1/B2 and C1 audited. Twenty-three other Annex A–C tables and main-report tables remain priority_unassessed.",
        "2021 census has 4 districts and 39 mukims; 2011 B1/B2 columns audited but not adopted as comparable time series. No 2011 shape is joined to a 2021 census row.",
        "JPBD lists district plans, but full plan bodies, periods and approvals remain unverified. RKN12 p.114 lists proposed 2026–2045 plan projects, not their completion or spending."]
    data["gaps"] = [g for g in data["gaps"] if g.get("category") not in (
        "boundary_reconciliation", "subnational_statistics", "official_geography",
        "census_table_coverage", "planning_documents")]
    data["gaps"].extend([
        {"category":"official_geography","status":"partial","detail":"Official 2021 district/mukim codes, compatible polygons and village crosswalk not acquired; 2011 geoBoundaries shapes removed.","next_action":"Request Survey Department/DEPS code and dated boundary releases; audit B3–B6 and C2–C10 kampung rows."},
        {"category":"census_table_coverage","status":"partial","detail":"Selected A1/A2/B1/B2/C1 columns are audited; 23 other annex tables and main-report tables are priority_unassessed.","next_action":"Inventory and assess every remaining numeric column by theme and geography before national completion."},
        {"category":"planning_documents","status":"partial","detail":"JPBD catalogue gives four plan locations, but no complete district plan body or approval evidence acquired.","next_action":"Acquire editions, maps, Minister approval notices, district allocations, actual spending and evaluations separately."}])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_path = project / "evidence/BRUNEI_BPP2021_TABLE_AUDIT.json"
    audit_path.write_text(json.dumps({"source_manifest":"config/brunei-bpp2021-source-manifest.json",
        "checked_at":"2026-09-27","selected_tables":["A1","A2","B1","B2","C1"],
        "priority_unassessed_tables":[*(f"A{i}" for i in range(3,13)),
            *(f"B{i}" for i in range(3,7)),*(f"C{i}" for i in range(2,11))],
        "checks":checks,"table_inventory":inventory,"territories":44,"indicators":11,
        "adopted_observations":len(observations),"source_reported_observations":44*8,
        "derived_age_observations":15,"warnings":[
            "The main report's full table inventory and the 23 unselected annex tables remain unassessed.",
            "Official codes, compatible polygons, plan bodies and approval are not acquired."]},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit_path, len(observations)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    manifest, sources = pinned(project)
    a_pages, b_pages, c_pages = (text_pages(sources[source]) for source in
                                (SOURCE_A, SOURCE_B, SOURCE_C))
    tables = read_tables(a_pages, b_pages, c_pages)
    checks = audit(*tables)
    inventory = table_inventory(a_pages, b_pages, c_pages)
    audit_path, count = build(project, manifest, *tables, checks, inventory)
    print(json.dumps({"country":"BRN","territories":44,"adopted_observations":count,
                      "checks":checks,"audit":str(audit_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

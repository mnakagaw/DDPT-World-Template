#!/usr/bin/env python3
"""Rebuild the Philippine candidate's source and geography inventories from local originals."""
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'generated/philippines-areadata-20260929').resolve()
data = json.loads((root / 'data/dashboard.json').read_text(encoding='utf-8'))
raw = root / 'raw'
out = root / 'evidence'
out.mkdir(exist_ok=True)
checked_at = datetime.now(timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
json_write = lambda name, obj: (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if data['country']['id'] != 'PHL':
    raise ValueError('Expected PHL data')
territories = data['territories']
territory_types = dict(Counter(t['type'] for t in territories))
by_id = {t['id']: t for t in territories}
observations = data['observations']
sources = {s['id']: s for s in data['sources']}

for s in sources.values():
    if s.get('raw_path') and s.get('sha256'):
        source_file = root / s['raw_path']
        if not source_file.is_file() or sha(source_file) != s['sha256']:
            raise ValueError(f'Original absent or hash changed: {s["id"]}')

api_dispositions = {
    'popcen-households-2024': ('adopted_partial', 'Three household measures adopted for 136 exact or explicit-code-crosswalk targets; SGA aggregate excluded.'),
    'sdg-education-completion': ('adopted_partial', '2024 both-sexes three school levels, national and all 18 current regions. Other sexes and unavailable 2025 cells remain source-only.'),
    'sdg-under-five-mortality': ('adopted_partial', '2025 NDHS rate at national and 18 regions; 2024 cells are unpublished.'),
    'sdg-basic-drinking-water': ('adopted_partial', '2024 provisional national family rate only; NIR is unpublished, other regional values withheld pending geography review.'),
    'sdg-electricity-access': ('acquired_not_adopted', 'Selected 2024/2025 cells are unpublished and the candidate geography excludes NIR.'),
    'sdg-unemployment': ('acquired_not_adopted', 'Selected 2024/2025 cells are unpublished and the candidate geography excludes NIR.'),
    'poverty-incidence-2023': ('acquired_not_adopted', '2023 province/region geography and Sulu/BARMM/NIR treatment are not proven comparable to 2025 PSGC.'),
    'grdp-2025': ('adopted', '2025 current and constant-2018 price values for nation and 18 current regions; rounding reconciled.'),
}
table_rows = []
inventory_rows = []
for stem, (decision, reason) in api_dispositions.items():
    base = raw / ('psa-openstat-' + stem)
    metadata_file = Path(str(base) + '-metadata.json')
    data_file = Path(str(base) + '-data.json')
    receipt_file = Path(str(base) + '-receipt.json')
    receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
    if sha(metadata_file) != receipt['metadata_sha256'] or sha(data_file) != receipt['data_sha256']:
        raise ValueError('OpenSTAT receipt mismatch: ' + stem)
    metadata = json.loads(metadata_file.read_text(encoding='utf-8-sig'))
    response = json.loads(data_file.read_text(encoding='utf-8-sig'))
    values = [v for row in response['data'] for v in row['values']]
    numeric = sum(bool(re.fullmatch(r'-?(?:\d+\.?\d*|\.\d+)', v)) for v in values)
    table_rows.append({
        'id': stem, 'source_url': receipt['source_url'], 'metadata_sha256': receipt['metadata_sha256'],
        'data_sha256': receipt['data_sha256'], 'data_rows': len(response['data']),
        'value_cells': len(values), 'numeric_cells': numeric,
        'unpublished_or_non_numeric_cells': len(values) - numeric,
        'dimensions': [{'code': v['code'], 'label': v['text'], 'member_count': len(v['values'])} for v in metadata['variables']],
        'disposition': decision, 'reason': reason,
    })
    for var in metadata['variables']:
        inventory_rows.append({
            'source_id': 'psa-openstat-' + stem, 'source_hash': receipt['data_sha256'],
            'table_or_sheet': metadata['title'], 'column_or_variable': var['code'],
            'original_label': var['text'], 'unit': 'as published in OpenSTAT table',
            'universe': 'see source metadata and table footnotes', 'period': 'query values in receipt',
            'geography_type': 'source geography codes',
            'role': 'dimension', 'indicator_id': '', 'decision': 'retained in raw',
            'reason': reason, 'locator': f'{metadata_file.name}: variables.{var["code"]}'
        })
    inventory_rows.append({
        'source_id': 'psa-openstat-' + stem, 'source_hash': receipt['data_sha256'],
        'table_or_sheet': metadata['title'], 'column_or_variable': 'data.values[0]',
        'original_label': metadata['title'], 'unit': 'as published in OpenSTAT table',
        'universe': 'see source metadata and table footnotes', 'period': 'query values in receipt',
        'geography_type': 'source geography codes', 'role': 'source value',
        'indicator_id': ','.join(sorted({o['indicator_id'] for o in observations if o['source_id'].startswith('psa-openstat-') and sources.get(o['source_id'], {}).get('url') == receipt['source_url']})),
        'decision': decision, 'reason': reason,
        'locator': f'{data_file.name}: data.values[0] ({len(values)} cells; {numeric} numeric)'
    })

json_write('SOURCE_TABLE_INVENTORY.json', {
    'checked_at': checked_at,
    'scope': 'All dimensions and value columns in eight locally acquired PSA OpenSTAT query slices, plus PSGC rendered extracts. This is not the full PSA catalogue.',
    'all_expected_resources_dispositioned': False,
    'all_psa_catalogue_tables_checked': False,
    'acquired_openstat_tables_checked': len(table_rows) == 8,
    'tables': table_rows,
    'psgc_rendered_extracts': [
        {'id': 'regions', 'rows': 18}, {'id': 'provinces', 'rows': 82},
        {'id': 'cities', 'rows': 149}, {'id': 'municipalities', 'rows': 1493},
        {'id': 'city classifications', 'huc': 33, 'icc': 5, 'cc': 111},
    ],
})
with (out / 'INDICATOR_INVENTORY.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(inventory_rows[0]))
    writer.writeheader(); writer.writerows(inventory_rows)

official = [s for s in data['sources'] if s['publisher'].lower().startswith(('philippine statistics authority', 'davao city', 'olongapo city', 'iloilo city', 'official gazette'))]
resources = [{
    'id': s['id'], 'url': s['url'], 'source_status': s['status'],
    'acquisition': 'original bytes locally hash-checked' if s.get('raw_path', '').endswith(('.json', '.pdf')) and s.get('sha256') else
                   'rendered web excerpt locally hash-checked' if s.get('raw_path') and s.get('sha256') else 'location/link only',
    'raw_path': s.get('raw_path'), 'sha256': s.get('sha256'), 'adopted_observation_count': sum(o['source_id'] == s['id'] for o in observations),
    'adopted_document_count': sum(d['source_id'] == s['id'] for d in data['documents']),
} for s in official]
resources.extend([
    {'id': 'psa-popcen-table-b-xlsx', 'url': 'https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president',
     'source_status': 'failed', 'acquisition': 'linked XLSX direct fetch blocked by site challenge', 'adopted_observation_count': 0},
    {'id': 'psa-psgc-masterlist', 'url': 'https://psa.gov.ph/classification/psgc',
     'source_status': 'not_collected', 'acquisition': 'original masterlist unavailable; rendered lists used', 'adopted_observation_count': 0},
    {'id': 'dilg-cdp-guide', 'url': 'https://region12.dilg.gov.ph/sites/default/files/reportsresources/knowledge-materials/961-illustrative-guide-v4b.pdf',
     'source_status': 'failed', 'acquisition': 'official indexed link returned 404', 'adopted_observation_count': 0},
    {'id': 'current-authoritative-polygons', 'url': 'https://geoportal.gov.ph/',
     'source_status': 'not_collected', 'acquisition': 'current 2025/2026 PSGC-aligned dated downloadable polygons not verified', 'adopted_observation_count': 0},
])
json_write('SOURCE_RESOURCE_INVENTORY.json', {'checked_at': checked_at,
    'scope': 'Confirmed Philippine official leads and this candidate; not an exhaustive national catalogue.',
    'all_expected_resources_dispositioned': False, 'resources': resources})

with (out / 'CODE_CROSSWALK.csv').open('w', encoding='utf-8-sig', newline='') as f:
    fields = ['territory_id','territory_name','level','psgc_10_digit','psgc_edition','parent_id','source_id','provider_shape_id','boundary_match_status']
    writer = csv.DictWriter(f, fields); writer.writeheader()
    for t in territories:
        writer.writerow({'territory_id':t['id'],'territory_name':t['name'],'level':t['type'],
            'psgc_10_digit':t.get('official_code') or '', 'psgc_edition':t.get('code_edition') or '',
            'parent_id':t.get('parent_id') or '', 'source_id':t.get('source_id') or '',
            'provider_shape_id':'', 'boundary_match_status':'no current polygon joined'})

themes = [
    ('population', ['PHL_POPCEN_2024_DOMESTIC','PHL_POPCEN_2024_HOUSEHOLD_POP'], 'Complete 2024 POPCEN domestic counts at country, 18 regions, 82 provinces, 149 cities and 1,493 municipalities; household population at a 136-target subset.'),
    ('education', ['PHL_EDU_COMPLETION_ELEMENTARY_2024','PHL_EDU_COMPLETION_JHS_2024','PHL_EDU_COMPLETION_SHS_2024'], '2024 school-completion rates at nation and all 18 regions; no province/city series adopted.'),
    ('health_nutrition', ['PHL_NDHS_UNDER5_MORTALITY_2025'], '2025 NDHS under-five mortality at nation and all 18 regions; 2024 unpublished.'),
    ('water_sanitation_housing_energy', ['PHL_POPCEN_2024_HOUSEHOLDS','PHL_POPCEN_2024_AVG_HH_SIZE','PHL_BASIC_DRINKING_WATER_FAMILIES_2024P'], 'Household count/size for 136 targets. Basic water provisional national only; electricity candidate cells unpublished.'),
    ('livelihoods_poverty_economy', ['PHL_GRDP_2025_CURRENT','PHL_GRDP_2025_CONSTANT2018'], '2025 GRDP nation plus all 18 regions; 2023 poverty table acquired but not joined across historic geography; unemployment candidate cells unpublished.'),
    ('access_infrastructure_environment', [], 'No verified local indicator from the acquired slices; source discovery remains open.'),
]
coverage=[]
for theme, ids, note in themes:
    rows=[o for o in observations if o['indicator_id'] in ids and o.get('status')=='observed']
    coverage.append({'theme':theme,'indicator_ids':ids,'observed_values':len(rows),
        'by_territory_type':dict(Counter(by_id[o['territory_id']]['type'] for o in rows)),
        'status':'partial_adopted' if rows else 'not_adopted', 'note':note})
json_write('THEME_COVERAGE.json', {'checked_at':checked_at,'coverage':coverage})

dataset_sha = sha(root / 'data/dashboard.json')
(out / 'SOURCE_PREFLIGHT_RECHECK.md').write_text(f'''# Philippines official-source recheck — 2026-09-29

- Current candidate: {len(territories)} territories, {len(observations)} observations, {len(data['indicators'])} indicators, {len(data['documents'])} local documents; dataset SHA-256 `{dataset_sha}`.
- PSA PSGC: rendered official region/province/city/municipality lists, city classification and 2024 POPCEN values are joined and reconciled. The original masterlist and Table B XLSX are still unacquired.
- PSA OpenSTAT: eight original API query slices and metadata with SHA-256 receipts are inventoried in `SOURCE_TABLE_INVENTORY.json`; acquired-slice field audit is separate from a full PSA catalogue audit.
- National planning law: RA 7160 sections 106/109 located; current amendments and 2024 joint planning harmonization circular PDF are not fully reviewed. DILG Region 1 2022 CDP Toolkit original is private and its regional applicability must not be generalized.
- Local documents: Davao City CDP and Olongapo revised AIP bodies checked; Iloilo City CDP link only. Planned investment, expenditure and evaluation are distinct.
- Current polygons: no verified 2025/2026 PSGC-aligned authoritative geometry joined; 2020 geoBoundaries shapes remain raw-only.
- Public release and independent acceptance: pending. Source location, acquisition, code join and adopted value remain separate stages.
''', encoding='utf-8')
(out / 'GEOGRAPHY_REVIEW.md').write_text(f'''# Philippine geography review — 2026-09-29

The rendered PSA PSGC region and local tables state 31 July 2025; the province table captured on 29 September 2026 does not display an edition for its rows. The assembled reporting hierarchy has {territory_types['region']} regions, {territory_types['province']} provinces, {territory_types['city']} cities and {territory_types['municipality']} municipalities. A single common PSGC edition is unverified. Their 2024 POPCEN domestic values reconcile to 112,727,776 people. ICCs remain independent city planning authorities while their populations are included in province census totals. HUCs, NCR Pateros, City of Isabela and the eight BARMM SGA municipalities require their recorded region or special-parent treatment; the SGA aggregate itself is withheld as a legal local authority.

`CODE_CROSSWALK.csv` has {len(territories)} IDs with type, PSGC code and parent; no polygon ID is asserted. The 2020 geoBoundaries ADM1 edition predates Negros Island Region and the 2025 Sulu transfer, and is not joined to current values. NAMRIA/Geoportal leads and FOI responses have not produced a verified current dated layer with a complete code crosswalk and redistribution terms. A map fallback explains the missing shape and keeps selection, statistics, documents and exports accessible.

The PSA OpenSTAT 2023 poverty slice is retained without adoption because its historic NIR/Sulu/BARMM and province/HUC coverage is not proven comparable to this register. The 2024 water table's NIR regional cell is unpublished; 17 other regional rows are withheld pending the source's post-NIR scope check. Published 2024 education and 2025 NDHS/GRDP series explicitly include 18 region labels and were adopted at that level.
''', encoding='utf-8')
(out / 'GAPS.md').write_text('''# Philippines gaps and next actions — 2026-09-29

1. **Original register and census workbook:** PSGC masterlist and 2024 POPCEN Table B direct downloads were blocked. Retain rendered official excerpts, obtain originals through authorized ordinary access, and compare every adopted code/count and column.
2. **Current boundaries:** no dated authoritative 18-region/local polygon edition with rights and code join was verified. Keep map fallback; obtain and audit one edition before a map is released.
3. **Thematic coverage:** 2024 local POPCEN covers all registered local units; other themes have regional or 136-target household coverage. Poverty, electricity and unemployment candidate values were not adopted for the stated period/geography reasons. Finish the broader official catalogue and indicator-by-indicator definitions.
4. **Planning system and documents:** Davao CDP and Olongapo AIP are checked originals; Iloilo is link-only. DILG Region 1 toolkit is regional and reproduction-restricted, and the 2024 harmonization circular original remains blocked. Verify the current country/local forms and acquire more matched plans, budgets, actual spending and evaluations without mixing their meanings.
5. **Acceptance and release:** finish the 42 scenarios, 12 country lesson checks, independent review, hosting destination and post-release readback. Current local browser evidence is representative, not comprehensive acceptance.
''', encoding='utf-8')
(root / 'HANDOFF.md').write_text(f'''# Philippines AreaData handoff — 2026-09-29

## State

- Local project: `{root}` (ignored from Git). Dataset SHA-256 `{dataset_sha}`.
- {len(territories)} territories, {len(data['indicators'])} indicators, {len(observations)} observations, {len(data['documents'])} area-specific documents, zero adopted polygons.
- Candidate only. No independent `ACCEPT`, no specified AreaData hosting destination, no public release.
- Git-tracked producer scripts and research summary are in the AreaData repository; original PSA API bytes, rendered excerpts and three official PDFs remain private `raw/` with hashes.

## Reproduce from saved raw originals

1. Use the generated project's `raw/` exact bytes and `data/dashboard.json` baseline or a fresh `create-country` project with the same input register and source captures. Raw files are intentionally not in Git; ordinary code checkout alone is not a complete replay.
2. `node scripts/adapt-philippines-psa-regions.mjs --project generated/philippines-areadata-20260929`
3. `node scripts/adapt-philippines-openstat-households.mjs --project generated/philippines-areadata-20260929`
4. `node scripts/adapt-philippines-openstat-themes.mjs --project generated/philippines-areadata-20260929`
5. `node scripts/adapt-philippines-local-plans.mjs --project generated/philippines-areadata-20260929`
6. `python scripts/refresh-philippines-evidence.py generated/philippines-areadata-20260929`
7. `node scripts/validate-country.mjs --project generated/philippines-areadata-20260929`; `node scripts/build-country.mjs --project generated/philippines-areadata-20260929`; `npm run check`; `npm test`.

The adapters replace their own records on rerun but cannot recreate missing raw originals. Preserve a known-good copy before future source refresh; a failed refresh must not replace the built site.

## Evidence and next work

- `evidence/SOURCE_RESOURCE_INVENTORY.json`, `SOURCE_TABLE_INVENTORY.json`, `INDICATOR_INVENTORY.csv`, `THEME_COVERAGE.json`, `CODE_CROSSWALK.csv`, `GEOGRAPHY_REVIEW.md`, `GAPS.md` record present coverage and gaps.
- Browser checks: city/parent selection and history, Olongapo/Davao document isolation, representative downloads, Bulacan 600-row CSV and 212-page HTML print PDF were exercised in a separate headless Chrome. Full acceptance and an independent reviewer remain pending.
- Next: original PSA masterlist/Table B, dated current official polygons, post-NIR thematic crosswalk, Philippine planning manual/form applicability, more local documents, full acceptance and independent decision. Hosting/publication require a separate scoped destination and `ACCEPT`.
''', encoding='utf-8')

print(json.dumps({'territories':len(territories),'types':territory_types,'observations':len(observations),
    'indicators':len(data['indicators']),'documents':len(data['documents']),
    'openstat_tables':len(table_rows),'inventory_fields':len(inventory_rows)}, indent=2))

"""Add visually verified INSD 2019 regional tables to the Burkina Faso bundle.

The row vectors are transcribed from the cited printed pages, then cross-checked
against the PDF text and expected row counts. Rates retain the census definition.
"""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/dashboard.json'
TABLES = ROOT / 'raw/insd-rgph-2019/statistical_tables.pdf'
LOCALITIES = json.loads((ROOT / 'raw/parsed-localities.json').read_text(encoding='utf-8'))
base = json.loads(DATA.read_text(encoding='utf-8'))


def key(value):
    return re.sub(r'[^A-Z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().upper())


regions = {key(t['name']): t for t in base['territories'] if t['level'] == 'adm1'}
assert len(regions) == 13
assert not any(i['id'].startswith('BFA_RGPH2019_') and i['id'].endswith('_REGIONAL') for i in base['indicators'])

# The source uses both "Hauts-Bassins" and "Hauts Bassins"; both refer to the
# same 2019 census region. No 2025 geographic remapping is performed.
rows = [
    # region, literacy, infant mortality (per 1,000), mean household size,
    # borehole as principal drinking-water source, SONABEL-grid main light,
    # bush/nature toilet category, occupied among all 15+ residents.
    ('Boucle du Mouhoun', 22.5, 53.5, 5.3, 16.0, 10.1, 31.4, 51.9),
    ('Cascades', 24.9, 65.2, 5.6, 33.0, 19.1, 22.7, 52.3),
    ('Centre', 57.0, 49.3, 4.2, 9.9, 38.2, 3.2, 49.3),
    ('Centre-Est', 22.1, 56.8, 5.4, 57.0, 10.1, 46.4, 40.2),
    ('Centre-Nord', 19.5, 50.2, 5.9, 46.0, 8.1, 43.9, 34.3),
    ('Centre-Ouest', 28.7, 58.4, 5.7, 32.0, 11.8, 38.9, 44.3),
    ('Centre-Sud', 25.5, 56.6, 5.4, 52.0, 7.8, 60.9, 42.8),
    ('Est', 18.0, 55.4, 6.1, 58.0, 5.7, 61.2, 41.3),
    ('Hauts-Bassins', 35.4, 58.5, 5.0, 12.0, 33.3, 12.8, 48.7),
    ('Nord', 23.4, 48.0, 5.8, 17.0, 12.8, 35.6, 27.6),
    ('Plateau Central', 22.5, 50.6, 5.8, 51.0, 5.8, 41.5, 34.6),
    ('Sahel', 12.5, 72.7, 4.5, 51.0, 7.0, 52.6, 22.8),
    ('Sud-Ouest', 21.8, 70.6, 5.0, 42.0, 7.2, 55.7, 53.2),
]
assert {key(r[0]) for r in rows} == set(regions)

source_id = 'bfa-insd-rgph2019-statistical-tables'
assert not any(s['id'] == source_id for s in base['sources'])
base['sources'].append({
    'id': source_id,
    'name': 'Résultats du 5e RGPH: volume des tableaux statistiques',
    'url': 'https://web2.insd.bf/sites/default/files/2024-06/Volume%20des%20tableaux%20statistiques_%205e%20RGPH.pdf',
    'publisher': 'Institut national de la statistique et de la démographie (INSD)',
    'reference_period': '2019 census; 2022 publication',
    'status': 'ready', 'retrieved_at': '2026-09-24',
    'sha256': sha256(TABLES.read_bytes()).hexdigest(),
    'raw_path': 'raw/insd-rgph-2019/statistical_tables.pdf',
    'note': 'Selected printed tables were visually checked. The PDF contains many additional tables; a selected set does not constitute a full numeric-column inventory.'
})

specs = [
    ('LITERACY_15PLUS', 'Literacy rate, age 15+', 'Education', '%',
     'Census literacy rate among residents aged 15 or above; table VIII.7, overall column.',
     'VIII.7', 'Ensemble', 157, 29.7),
    ('INFANT_MORTALITY_1Q0', 'Infant mortality quotient (1q0)', 'Health and nutrition', 'per 1,000',
     'Estimated infant mortality quotient (1q0) per 1,000; not a direct death count or child-mortality prevalence.',
     'III.9', 'Ensemble', 45, 55.9),
    ('MEAN_HOUSEHOLD_SIZE', 'Average household size', 'Housing, water, sanitation and energy', 'people per household',
     'Mean household size; table VII.11, overall column.', 'VII.11', 'Ensemble', 126, 5.2),
    ('WATER_BOREHOLE_SOURCE', 'Households using a borehole as main drinking-water source',
     'Housing, water, sanitation and energy', '%',
     'Percentage of households reporting a borehole (forage) as their principal drinking-water source. This is a source category, not the SDG safely managed drinking-water indicator.',
     'VII.50', 'Forage', 141, 30.8),
    ('SONABEL_MAIN_LIGHT', 'Households using SONABEL grid electricity as main lighting source',
     'Housing, water, sanitation and energy', '%',
     'Percentage of households whose principal lighting source is SONABEL grid electricity. This is not total electricity access; solar and other sources are separate.',
     'VII.55', 'Électricité du réseau SONABEL', 143, 17.6),
    ('BUSH_TOILET_CATEGORY', 'Households reporting bush or nature as toilet type',
     'Housing, water, sanitation and energy', '%',
     'Percentage of households in the source category Brousse/nature. This is not the SDG safely managed sanitation rate.',
     'VII.65', 'Brousse/nature', 147, 32.8),
    ('EMPLOYED_SHARE_15PLUS', 'Employed among residents aged 15+',
     'Livelihoods, poverty and economy', '%',
     'Percentage of all residents aged 15 or above classified as employed. The unemployed share in the same table is not an unemployment rate.',
     'IX.1', 'Occupés', 182, 42.9),
]
for suffix, label, theme, unit, definition, table, column, printed_page, national_value in specs:
    indicator_id = 'BFA_RGPH2019_' + suffix + '_REGIONAL'
    base['indicators'].append({
        'id': indicator_id, 'name': label, 'theme': theme, 'unit': unit,
        'definition': definition, 'source_id': source_id, 'aggregation': 'none',
        'measurement_method': 'INSD published 2019 census table; rate or quotient as defined in the source',
        'series_family': 'census', 'display_role': 'primary', 'period_policy': 'source_year',
        'upstream_source_id': source_id, 'upstream_table': f'Tableau {table}, printed p. {printed_page}',
        'upstream_column': column,
    })
    values = [('BFA', national_value)] + [(regions[key(r[0])]['id'], r[specs.index((suffix, label, theme, unit, definition, table, column, printed_page, national_value)) + 1]) for r in rows]
    for territory_id, value in values:
        base['observations'].append({
            'territory_id': territory_id, 'indicator_id': indicator_id,
            'period': '2019', 'value': value, 'status': 'observed',
            'source_id': source_id, 'value_origin': 'source_reported_table',
            'source_locator': f'Tableau {table}, printed p. {printed_page}, {column}',
        })

# Region totals in the locality volume are checked against the complete set of
# 45 province totals. Store the exact 2019 region observations, never 2025 values.
province_by_region = defaultdict(list)
for item in LOCALITIES['provinces']:
    province_by_region[key(item['region'])].append(item)
assert set(province_by_region) == set(regions)
for rkey, province_items in province_by_region.items():
    assert province_items
    for suffix, column in [('POP_TOTAL', 'total'), ('POP_MALE', 'male'), ('POP_FEMALE', 'female')]:
        base['observations'].append({
            'territory_id': regions[rkey]['id'],
            'indicator_id': 'BFA_RGPH2019_' + suffix,
            'period': '2019', 'value': sum(item[column] for item in province_items),
            'status': 'observed', 'source_id': 'bfa-insd-rgph2019-localities',
            'value_origin': 'complete_province_sum_reconciled_to_INSD_region_total',
            'source_locator': 'Fichier des localités, printed pp. 1-3 and province pages',
        })

base['collection']['adapters'].append('insd-rgph-2019-regional-tables')
base['collection']['notes'].append('Seven selected INSD regional indicators use exact 2019 census definitions. Province/commune data for these topics are not inferred from the region value.')
DATA.write_text(json.dumps(base, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'new_indicators': len(specs), 'new_observations': len(specs)*14+39, 'regions': len(regions)}))

"""Sum complete RGPH 2019 locality age columns into five explicit age bands."""
from collections import defaultdict
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/dashboard.json'
LINES = (ROOT/'raw/insd-rgph-2019/localities.txt').read_text(encoding='utf-8').split('\n')
LOCALITIES = json.loads((ROOT/'raw/parsed-localities.json').read_text(encoding='utf-8'))
base = json.loads(DATA.read_text(encoding='utf-8'))


def key(value):
    return re.sub(r'[^A-Z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().upper())


def age_values(line_number):
    fields = re.split(r'\s{2,}', LINES[line_number-1].strip())
    assert len(fields) == 20, (line_number, len(fields))
    numbers = [int(x.replace(' ', '')) for x in fields[1:]]
    assert numbers[0] + numbers[1] == numbers[2]
    ages = numbers[3:]
    assert len(ages) == 16 and sum(ages) == numbers[2], line_number
    return ages, numbers[2]


def broad(ages):
    # Source groups: ages 0,1,2,3,4,5,6-11,12-14,15,16,17,18-19,
    # 20-24,25-35,36-64,65+. No unreported finer age band is inferred.
    return [sum(ages[:5]), sum(ages[5:8]), sum(ages[8:13]),
            sum(ages[13:15]), ages[15]]


national_ages, national_total = age_values(163)
assert national_total == 20505155
province_ages = {}
for p in LOCALITIES['provinces']:
    ages, total = age_values(p['line'])
    assert total == p['total']
    province_ages[p['name']] = ages

commune_ages = {}
for c in LOCALITIES['communes']:
    lines = c.get('derived_from_arrondissement_lines') or c.get('derived_from_parts') or [c['line']]
    value_rows = [age_values(n) for n in lines]
    assert sum(total for _, total in value_rows) == c['total'], c['name']
    ages = [sum(row[i] for row, _ in value_rows) for i in range(16)]
    commune_ages[(c['province'], key(c['name']))] = ages

region_ages = defaultdict(lambda: [0]*16)
for p in LOCALITIES['provinces']:
    row = region_ages[key(p['region'])]
    for i, n in enumerate(province_ages[p['name']]):
        row[i] += n
assert all(sum(row[i] for row in region_ages.values()) == national_ages[i] for i in range(16))

specs = [
    ('AGE_0_4', 'Residents age 0–4', '0–4'),
    ('AGE_5_14', 'Residents age 5–14', '5–14'),
    ('AGE_15_24', 'Residents age 15–24', '15–24'),
    ('AGE_25_64', 'Residents age 25–64', '25–64'),
    ('AGE_65_PLUS', 'Residents age 65+', '65+'),
]
for suffix, name, band in specs:
    indicator_id = 'BFA_RGPH2019_' + suffix
    assert not any(i['id'] == indicator_id for i in base['indicators'])
    base['indicators'].append({
        'id': indicator_id, 'name': name, 'theme': 'Population and demography',
        'unit': 'people',
        'definition': f'Resident population in age band {band}; complete sum of published finer age columns in the INSD locality volume. No sex split is available from this table.',
        'source_id': 'bfa-insd-rgph2019-localities', 'aggregation': 'none',
        'measurement_method': 'complete_sum_of_source_age_columns',
        'series_family': 'census', 'display_role': 'supplementary',
        'period_policy': 'source_year', 'upstream_source_id': 'bfa-insd-rgph2019-localities',
        'upstream_table': 'Population résidente par sexe et par groupe d’âge selon la localité',
        'upstream_column': band,
    })

province_to_region = {key(p['name']): key(p['region']) for p in LOCALITIES['provinces']}
observed_areas = set()
for t in base['territories']:
    if t['level'] == 'national':
        ages = national_ages
    elif t['level'] == 'adm1':
        ages = region_ages[key(t['name'])]
    elif t['level'] == 'adm2':
        ages = province_ages[next(p['name'] for p in LOCALITIES['provinces'] if key(p['name']) == key(t['name']))]
    elif t['level'] == 'adm3':
        province_key = t['parent_id'].split(':')[-1]
        province_name = next(p['name'] for p in LOCALITIES['provinces'] if key(p['name']) == province_key)
        ages = commune_ages[(province_name, key(t['name']))]
    else:
        raise AssertionError(t['level'])
    bands = broad(ages)
    assert sum(bands) == sum(ages)
    observed_areas.add(t['id'])
    for (suffix, _, _), value in zip(specs, bands):
        base['observations'].append({
            'territory_id': t['id'], 'indicator_id': 'BFA_RGPH2019_' + suffix,
            'period': '2019', 'value': value, 'status': 'observed',
            'source_id': 'bfa-insd-rgph2019-localities',
            'value_origin': 'complete_age_column_sum',
            'source_locator': 'Fichier des localités, resident population by age and locality',
        })
assert len(observed_areas) == len(base['territories']) == 410
base['collection']['adapters'].append('insd-rgph2019-age-bands')
DATA.write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'territories':len(observed_areas),'age_indicators':len(specs),'new_observations':len(observed_areas)*len(specs)}))

"""Add verified 2019 INSD census geography and population to the initial AreaData dataset."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import re
import unicodedata
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/dashboard.json'
CENSUS_URL = 'https://microdata.insd.bf/index.php/catalog/69/download/270'
BOUNDARY_URL = 'https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BFA/ADM2/geoBoundaries-BFA-ADM2_simplified.geojson'


def key(text):
    value = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', value)


ALIASES = {'BALES': 'BALE', 'KOMANDJOARI': 'KOMONJDJARI'}
base = json.loads(DATA.read_text(encoding='utf-8'))
census = json.loads((ROOT / 'raw/parsed-localities.json').read_text(encoding='utf-8'))
adm2 = json.loads((ROOT / 'raw/geoboundaries-adm2.geojson').read_text(encoding='utf-8'))

assert len(base['territories']) == 14 and len(base['boundaries']['features']) == 13
assert len(census['provinces']) == 45 and len(census['communes']) == 351
assert len(adm2['features']) == 45

region_by_key = {key(t['name']): t for t in base['territories'] if t['level'] == 'adm1'}
assert len(region_by_key) == 13
region_aliases = {'CENTRESUD': 'CENTRESUD', 'PLATEAUCENTRAL': 'PLATEAUCENTRAL'}
province_by_name = {key(p['name']): p for p in census['provinces']}
shape_by_province = {}
for feature in adm2['features']:
    bkey = key(feature['properties']['shapeName'])
    matches = [p for p in census['provinces'] if ALIASES.get(key(p['name']),key(p['name'])) == bkey]
    assert len(matches) == 1, (bkey,matches)
    shape_by_province[matches[0]['name']] = feature
assert len(shape_by_province) == 45

source_id = 'bfa-insd-rgph2019-localities'
for existing in base['sources']:
    assert existing['id'] != source_id
raw = ROOT / 'raw/insd-rgph-2019/localities.pdf'
base['sources'].append({
    'id': source_id, 'name': 'Fichier des localités du 5e RGPH (2019)',
    'url': CENSUS_URL, 'publisher': 'Institut national de la statistique et de la démographie (INSD)',
    'reference_period': '2019 census; June 2022 publication', 'status': 'ready',
    'retrieved_at': '2026-09-24', 'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
    'raw_path': 'raw/insd-rgph-2019/localities.pdf',
    'note': 'Resident population; 2019 13-region/45-province/351-commune geography. Some security-affected communes were partly or wholly estimated by INSD. Commune records without a direct total are derived only where the entire arrondissement set reconciles to the province.'
})
geo_source = 'geoboundaries-adm2'
base['sources'].append({
    'id': geo_source, 'name': 'geoBoundaries Burkina Faso ADM2 reference geometry',
    'url': BOUNDARY_URL, 'publisher': 'geoBoundaries / World Bank source',
    'reference_period': '2017 reference; not 2025/2026 administrative geography',
    'status': 'ready', 'retrieved_at': '2026-09-24',
    'sha256': hashlib.sha256((ROOT/'raw/geoboundaries-adm2.geojson').read_bytes()).hexdigest(),
    'raw_path': 'raw/geoboundaries-adm2.geojson',
    'note': 'Provider reference geometry, name matched to the 2019 INSD province list; not an official administrative code or legal boundary certification.'
})

specs = [
    ('BFA_RGPH2019_POP_TOTAL', 'Census population, total (2019)', 'Total resident population recorded or estimated by INSD in the fifth census.'),
    ('BFA_RGPH2019_POP_MALE', 'Male resident population, 2019 census', 'Male resident population recorded or estimated by INSD in the fifth census.'),
    ('BFA_RGPH2019_POP_FEMALE', 'Female resident population, 2019 census', 'Female resident population recorded or estimated by INSD in the fifth census.'),
]
for indicator_id, name, definition in specs:
    base['indicators'].append({
        'id': indicator_id, 'name': name, 'theme': 'Population and demography',
        'unit': 'people', 'definition': definition,
        'source_id': source_id, 'aggregation': 'none',
        'measurement_method': 'INSD published census count, including source-noted estimates in security-affected areas',
        'series_family': 'census', 'display_role': 'primary', 'period_policy': 'source_year',
        'upstream_source_id': source_id,
        'upstream_table': 'Resident population by sex, age and locality',
        'upstream_column': {'BFA_RGPH2019_POP_TOTAL':'Ensemble','BFA_RGPH2019_POP_MALE':'Homme','BFA_RGPH2019_POP_FEMALE':'Femme'}[indicator_id],
    })


def observe(territory_id, total, male, female, provenance, line=None):
    assert total == male + female
    for indicator_id, value in zip((x[0] for x in specs),(total,male,female)):
        base['observations'].append({
            'territory_id': territory_id, 'indicator_id': indicator_id,
            'period': '2019', 'value': value, 'status': 'observed',
            'source_id': source_id, 'value_origin': provenance,
            'source_line_in_extracted_text': line,
        })


observe('BFA', 20505155, 9900847, 10604308, 'source_reported_national', 163)

province_ids = {}
province_spatial = []
for item in census['provinces']:
    rid = region_by_key.get(key(item['region']))
    assert rid, item['region']
    province_id = 'BFA:RGPH2019:ADM2:' + key(item['name'])
    province_ids[item['name']] = province_id
    feature = shape_by_province[item['name']]
    geom = shape(feature['geometry'])
    parent_geom = next(shape(f['geometry']) for f in base['boundaries']['features'] if f['properties']['territory_id']==rid['id'])
    overlap = geom.intersection(parent_geom).area / geom.area
    province_spatial.append({'province':item['name'],'region':rid['name'],'within_parent_fraction':round(overlap,5)})
    base['territories'].append({
        'id': province_id, 'name': item['name'].title(), 'level': 'adm2',
        'type': 'province', 'parent_id': rid['id'], 'official_code': None,
        'code_system': None, 'provider_code': feature['properties']['shapeID'],
        'boundary_version': 'geoBoundaries BFA ADM2, 2017 reference',
        'source_id': source_id, 'reconciliation_status': 'name_and_parent_geometry_checked',
    })
    observe(province_id,item['total'],item['male'],item['female'],'source_reported_province',item['line'])
    feature['properties'] = {
        'territory_id': province_id, 'name': item['name'].title(),
        'provider_shape_id': feature['properties']['shapeID'],
        'boundary_version': 'geoBoundaries BFA ADM2, 2017 reference',
        'source_id': geo_source,
    }
    base['boundaries']['features'].append(feature)

assert min(x['within_parent_fraction'] for x in province_spatial) > .90, province_spatial
(ROOT/'evidence/PROVINCE_BOUNDARY_JOIN.json').write_text(json.dumps(province_spatial,indent=2)+'\n',encoding='utf-8')

for item in census['communes']:
    territory_id = 'BFA:RGPH2019:ADM3:' + key(item['province']) + ':' + key(item['name'])
    base['territories'].append({
        'id': territory_id, 'name': item['name'].title(), 'level': 'adm3',
        'type': 'commune', 'parent_id': province_ids[item['province']],
        'official_code': None, 'code_system': None, 'boundary_version': None,
        'source_id': source_id,
        'reconciliation_status': 'INSD locality hierarchy; no verified commune polygon join',
        'census_estimated_marker': item['estimated_marker'],
    })
    provenance = 'complete_arrondissement_sum' if 'derived_from_arrondissement_lines' in item else ('source_reported_estimated_commune' if item['estimated_marker'] else 'source_reported_commune')
    observe(territory_id,item['total'],item['male'],item['female'],provenance,item['line'])

base['analysis']['default_indicator_id'] = 'BFA_RGPH2019_POP_TOTAL'
base['analysis']['latest_values_only'] = True
base['collection']['adapters'].append('insd-rgph-2019-localities')
base['collection']['notes'].extend([
    '2019 INSD fifth census: 13 regions, 45 provinces and 351 communes; all published locality totals reconciled from commune to province to country.',
    'Population values for security-affected communes can contain INSD estimation, not direct enumeration in all places.',
    '2019 census geography is distinct from the 2025/2026 17-region/47-province reform. The reference province map is not a legal boundary certification.',
    'Commune polygons are intentionally withheld: the geoBoundaries ADM3 file failed spatial name-to-province checks. No unrelated polygon is substituted.',
])
base['collection']['status'] = 'partial'
DATA.write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'territories':len(base['territories']), 'observations':len(base['observations']),
                  'indicators':len(base['indicators']), 'province_min_parent_overlap':min(x['within_parent_fraction'] for x in province_spatial)},ensure_ascii=False))

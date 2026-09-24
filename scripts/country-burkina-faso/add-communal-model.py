"""Adopt only unambiguous provincial/communal INSD contraceptive model rows.

The 2023 study models a 2015 outcome from EMDS 2015 and RGPH 2019 covariates.
The appendix does not give parent provinces for homonymous communes, so those
rows stay unresolved; it is unsafe to attach a modeled value by name alone.
"""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/dashboard.json'
RAW = ROOT / 'raw/insd-rgph-2019/communal_disparities.pdf'
TEXT = (ROOT / 'raw/insd-rgph-2019/communal_disparities.txt').read_text(encoding='utf-8')
base = json.loads(DATA.read_text(encoding='utf-8'))


def key(value):
    return re.sub(r'[^A-Z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().upper())


def value(text):
    return float(text.replace(',', '.'))


province_section = TEXT.split('Annexe 1 : Estimation de la prévalence contraceptive moderne par province', 1)[1].split('Annexe 2: Estimation', 1)[0]
commune_section = TEXT.split('Annexe 2: Estimation de la prévalence (%) contraceptive moderne par commune', 1)[1]
pattern = re.compile(r'^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ \-\'’]+?)\s{2,}(\d{1,2},\d{2})\s+(\d{1,2},\d{2})\s+(\d{1,2},\d{2})\s*$', re.M)
provinces = pattern.findall(province_section)
communes = pattern.findall(commune_section)
assert len(provinces) == 45, len(provinces)
assert len(communes) == 342, len(communes)
assert len({key(n) for n, *_ in communes}) == 341

province_ids = {key(t['name']): t['id'] for t in base['territories'] if t['level'] == 'adm2'}
assert len(province_ids) == 45
province_ids['BALE'] = province_ids['BALES']  # singular annex name, same source province
commune_ids = defaultdict(list)
for t in base['territories']:
    if t['level'] == 'adm3':
        commune_ids[key(t['name'])].append(t['id'])
assert sum(map(len, commune_ids.values())) == 351

source_id = 'bfa-insd-communal-contraceptive-model-2023'
indicator_id = 'BFA_INSD_MODELED_MODERN_CONTRACEPTIVE_PREVALENCE_2015'
assert not any(s['id'] == source_id for s in base['sources'])
base['sources'].append({
    'id': source_id,
    'name': 'Disparités communales de la pratique contraceptive au Burkina Faso',
    'url': 'https://microdata.insd.bf/index.php/catalog/69/download/272',
    'publisher': 'Institut national de la statistique et de la démographie (INSD)',
    'reference_period': '2015 outcome model, 2019 census covariates; August 2023 report',
    'status': 'ready', 'retrieved_at': '2026-09-24',
    'sha256': sha256(RAW.read_bytes()).hexdigest(),
    'raw_path': 'raw/insd-rgph-2019/communal_disparities.pdf',
    'note': 'Small-area modeled contraceptive prevalence for women aged 15–49 in union, not a direct census observation. Homonymous appendix entries without province identifiers are withheld.'
})
base['indicators'].append({
    'id': indicator_id,
    'name': 'Modern contraceptive use among women 15–49 in union (modeled)',
    'theme': 'Health and nutrition', 'unit': '%',
    'definition': 'Modeled prevalence of modern contraception among women aged 15–49 in union. An INSD small-area estimate of the 2015 outcome, using 2015 survey and 2019 census inputs. Not a directly enumerated 2019 census value.',
    'source_id': source_id, 'aggregation': 'none',
    'measurement_method': 'INSD ELL small-area prediction from EMDS 2015 and RGPH 2019',
    'series_family': 'survey', 'display_role': 'supplementary',
    'period_policy': '2015 modeled outcome', 'upstream_source_id': source_id,
    'upstream_table': 'Annexes 1–2, printed pp. vi–xiv', 'upstream_column': 'Prévalence (%)',
})


def adopt(territory_id, item, locator):
    name, estimate, lower, upper = item
    estimate, lower, upper = map(value, (estimate, lower, upper))
    assert 0 <= lower <= estimate <= upper <= 100, item
    base['observations'].append({
        'territory_id': territory_id, 'indicator_id': indicator_id,
        'period': '2015', 'value': estimate, 'status': 'observed',
        'source_id': source_id, 'value_origin': 'INSD_model_prediction_not_direct_observation',
        'source_locator': locator, 'source_label': name,
        'lower_95_confidence': lower, 'upper_95_confidence': upper,
    })


for row in provinces:
    assert key(row[0]) in province_ids, row
    adopt(province_ids[key(row[0])], row, 'Annexe 1, province model table')

name_counts = Counter(key(row[0]) for row in communes)
unresolved = []
adopted_communes = 0
for row in communes:
    ids = commune_ids[key(row[0])]
    if len(ids) != 1 or name_counts[key(row[0])] != 1:
        unresolved.append({'name': row[0], 'value': row[1], 'candidate_ids': ids,
                           'reason': 'homonymous or no unique 2019 commune match; appendix lacks province code'})
        continue
    adopt(ids[0], row, 'Annexe 2, commune model table')
    adopted_communes += 1
assert adopted_communes == 339 and len(unresolved) == 3
(ROOT / 'evidence/COMMUNAL_MODEL_UNRESOLVED.json').write_text(json.dumps(unresolved, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
base['collection']['adapters'].append('insd-communal-contraceptive-model')
base['collection']['notes'].append('INSD modeled 2015 modern contraceptive prevalence: 45 provinces and 339 uniquely matched communes; 3 homonymous appendix rows are withheld. It is not a direct 2019 census count.')
DATA.write_text(json.dumps(base, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'provinces': len(provinces), 'communes': adopted_communes, 'unresolved': unresolved}, ensure_ascii=False))

"""Import RGPH 2019 Table I.20 age-sex counts for country and 13 regions."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
data_path = root / 'data/dashboard.json'
text_path = root / 'raw/insd-rgph-2019/statistical_tables.txt'
data = json.loads(data_path.read_text(encoding='utf-8'))
text = text_path.read_text(encoding='utf-8')
section = text.rsplit('Tableau I.20: Effectif', 1)[1].split('Tableau I.21 :', 1)[0]
expected_ages = [f'{age}-{age+4}' for age in range(0, 85, 5)] + ['85+']
blocks = []
current = []
for line in section.splitlines():
    age = re.match(r'^\s*(\d{1,2}-\d{1,2}|85\+)\s+(.*)$', line)
    if age:
        values = [int(value) for value in re.findall(r'\d+', age[2])]
        assert len(values) == 9, (age[1], line)
        assert values[0] == values[1] + values[2], (age[1], values)
        current.append((age[1], values[0], values[1], values[2]))
    elif re.match(r'^\s*Total\s+', line) and current:
        tokens = re.findall(r'\d{1,3}(?: \d{3})+', line) if len(blocks) == 0 else re.findall(r'\d+', line)
        values = [int(value.replace(' ', '')) for value in tokens]
        assert len(values) == 9, line
        assert [item[0] for item in current] == expected_ages, current
        assert sum(item[1] for item in current) == values[0]
        assert sum(item[2] for item in current) == values[1]
        assert sum(item[3] for item in current) == values[2]
        blocks.append((current, values[:3]))
        current = []
assert len(blocks) == 14 and not current, len(blocks)

population = {
    row['territory_id']: row['value']
    for row in data['observations']
    if row['indicator_id'] == 'BFA_RGPH2019_POP_TOTAL' and row['period'] == '2019' and row['status'] == 'observed'
}
male = {
    row['territory_id']: row['value']
    for row in data['observations']
    if row['indicator_id'] == 'BFA_RGPH2019_POP_MALE' and row['period'] == '2019' and row['status'] == 'observed'
}
female = {
    row['territory_id']: row['value']
    for row in data['observations']
    if row['indicator_id'] == 'BFA_RGPH2019_POP_FEMALE' and row['period'] == '2019' and row['status'] == 'observed'
}
areas = [area for area in data['territories'] if area['level'] in ('national', 'adm1')]
profiles = {}
matches = []
for rows, totals in blocks:
    match = [area for area in areas if
             population.get(area['id']) == totals[0] and
             male.get(area['id']) == totals[1] and
             female.get(area['id']) == totals[2]]
    assert len(match) == 1, totals
    area = match[0]
    key = f"{area['id']}@2019"
    profiles[key] = {
        'period': '2019', 'ages': expected_ages,
        'male': [item[2] for item in rows],
        'female': [item[3] for item in rows],
        'source_id': 'bfa-insd-rgph2019-statistical-tables',
        'table': 'Table I.20', 'unit': 'people',
        'geography_note': 'RGPH 2019 geography; no province or commune profiles inferred.'
    }
    matches.append({'territory_id': area['id'], 'name': area['name'],
                    'total': totals[0], 'male': totals[1], 'female': totals[2]})
assert len(profiles) == 14
data.setdefault('analysis', {})['census_population_pyramids'] = profiles
data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(root / 'evidence/AGE_SEX_TABLE_I20.json').write_text(
    json.dumps({'source_id': 'bfa-insd-rgph2019-statistical-tables',
                'table': 'I.20', 'year': 2019, 'age_bands': len(expected_ages),
                'matched_areas': matches,
                'validation': 'Each age row male + female = total; age sums equal Table I.20 totals and separate RGPH locality observations.'},
               ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Validated {len(profiles)} census population pyramids')

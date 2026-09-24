"""Audit joins of INSD 2019 areas to geoBoundaries reference shapes."""
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import json
import re
import unicodedata
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'raw/parsed-localities.json').read_text(encoding='utf-8'))
adm2 = json.loads((ROOT / 'raw/geoboundaries-adm2.geojson').read_text(encoding='utf-8'))['features']
adm3 = json.loads((ROOT / 'raw/geoboundaries-adm3.geojson').read_text(encoding='utf-8'))['features']


def key(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', name)


ALIAS = {'BALES': 'BALE', 'KOMANDJOARI': 'KOMONJDJARI', 'KOULPELOGO': 'KOULPELOGO'}
province_by_shape = {}
provinces_by_key = {key(x['name']): x for x in data['provinces']}
for feature in adm2:
    shape_name = feature['properties']['shapeName']
    result = [p for p in data['provinces'] if ALIAS.get(key(p['name']), key(p['name'])) == key(shape_name)]
    assert len(result) == 1, shape_name
    province_by_shape[feature['properties']['shapeID']] = result[0]

communes_by_province = defaultdict(dict)
for commune in data['communes']:
    code = key(commune['name'])
    assert code not in communes_by_province[commune['province']], (commune['province'], code)
    communes_by_province[commune['province']][code] = commune

assigned = defaultdict(list)
for feature in adm3:
    geom = shape(feature['geometry'])
    point = geom.representative_point()
    possible = [p for p in adm2 if shape(p['geometry']).contains(point)]
    if not possible:
        possible = sorted(adm2, key=lambda p: shape(p['geometry']).intersection(geom).area, reverse=True)[:1]
    pname = province_by_shape[possible[0]['properties']['shapeID']]['name']
    assigned[pname].append(feature)

crosswalk = []
unmatched = []
for province in data['provinces']:
    pname = province['name']
    remaining = dict(communes_by_province[pname])
    for feature in assigned[pname]:
        bname = feature['properties']['shapeName']
        bkey = key(bname)
        census = remaining.pop(bkey, None)
        if census:
            crosswalk.append({'province': pname, 'census_name': census['name'], 'boundary_name': bname,
                              'shape_id': feature['properties']['shapeID'], 'status': 'exact_normalized'})
        else:
            unmatched.append({'province': pname, 'boundary_name': bname,
                              'shape_id': feature['properties']['shapeID'], 'candidates':
                              sorted([{'name': x['name'], 'similarity': round(SequenceMatcher(None,bkey,k).ratio(),3)}
                                      for k,x in remaining.items()],key=lambda x:-x['similarity'])[:3]})
    for census in remaining.values():
        unmatched.append({'province': pname, 'census_name': census['name'], 'status': 'unmatched_census'})

out = {'adm2_features': len(adm2), 'adm3_features': len(adm3), 'exact_matches': len(crosswalk),
       'crosswalk': crosswalk, 'unmatched': unmatched,
       'assigned_counts': [{'province': x['name'], 'census': len(communes_by_province[x['name']]),
                            'boundary': len(assigned[x['name']])} for x in data['provinces']]}
(ROOT / 'raw/boundary-match-candidates.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'exact_matches':len(crosswalk),'unmatched':len(unmatched),
                  'count_mismatches':[x for x in out['assigned_counts'] if x['census']!=x['boundary']]},ensure_ascii=False))
print(json.dumps(unmatched[:25],ensure_ascii=False))

#!/usr/bin/env python3
"""Collect official USA ACS 2023 state/county tables and Census boundaries.

The Census Data API requires a key in the current environment, so this collector
uses the Bureau's public table-based Summary File. It stores an exact source
prefix through summary level 050 and records that this is a partial byte-range
acquisition of each much larger all-geography table.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,os,sys,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

ACS_ROOT="https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData"
ACS_GEOS="https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/documentation/Geos20235YR.txt"
META_ROOT="https://api.census.gov/data/2023/acs/acs5/groups"
BOUNDARY_ROOT="https://www2.census.gov/geo/tiger/GENZ2023/shp"
TABLES=['B01003','B01001','B11001','B25001','B25047','B15003','B23025','C18108','B05002','B03003','B27010','B17001','B22003','B28002']
EXCLUDED_STATE_CODES={'60','66','69','72','78'}

def sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AreaData/0.10.2 source collector'}),timeout=120)

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with request(url) as r,path.open('wb') as out:
        while True:
            block=r.read(1024*1024)
            if not block:break
            out.write(block)
        headers=dict(r.headers.items())
    return {'url':url,'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'headers':{k:headers.get(k) for k in ['Content-Length','ETag','Last-Modified'] if headers.get(k)}}

def acquire_prefix(url,path):
    path.parent.mkdir(parents=True,exist_ok=True);headers={};rows=0;county_rows=0;stop=''
    with request(url) as r,path.open('wb') as out:
        headers=dict(r.headers.items())
        first=True;geo_index=0
        for raw in r:
            if first:
                out.write(raw);first=False
                header=raw.rstrip(b'\r\n').split(b'|');geo_index=header.index(b'GEO_ID')
                continue
            fields=raw.split(b'|');gid=fields[geo_index].decode('ascii','ignore') if len(fields)>geo_index else ''
            summary=gid[:3]
            if county_rows and summary.isdigit() and int(summary)>50:
                stop=summary;break
            out.write(raw);rows+=1
            if gid.startswith('0500000US'):county_rows+=1
    if not county_rows:raise RuntimeError(f'No county rows acquired from {url}')
    return {'url':url,'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'partial_acquisition':True,'retained_through_summary_level':'050','stopped_before_summary_level':stop,'retained_rows':rows,'county_rows':county_rows,'upstream_headers':{k:headers.get(k) for k in ['Content-Length','ETag','Last-Modified'] if headers.get(k)}}

def selected_geo(gid):
    if gid=='0100000US':return ('USA','country','')
    if gid.startswith('0400000US'):
        state=gid[-2:]
        if state in EXCLUDED_STATE_CODES:return None
        return (f'USA:ACS2023:STATE:{state}','state',state)
    if gid.startswith('0500000US'):
        fips=gid[-5:];state=fips[:2]
        if state in EXCLUDED_STATE_CODES:return None
        return (f'USA:ACS2023:COUNTY:{fips}','county',fips)
    return None

def load_geos(path):
    areas={}
    with path.open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f,delimiter='|'):
            info=selected_geo(row['GEO_ID'])
            if info:areas[row['GEO_ID']]={'id':info[0],'level':info[1],'code':info[2],'name':row['NAME'],'state':row.get('STATE',''),'county':row.get('COUNTY','')}
    return areas

def load_table(path,areas):
    rows={}
    with path.open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f,delimiter='|'):
            if row['GEO_ID'] in areas:rows[row['GEO_ID']]=row
    if len(rows)!=len(areas):raise RuntimeError(f'{path.name}: expected {len(areas)} selected geographies, got {len(rows)}')
    return rows

def num(row,key):
    try:
        value=float(row[key])
        return value if value>=0 else None
    except (KeyError,TypeError,ValueError):return None

def total(row,keys):
    values=[num(row,key) for key in keys]
    return None if any(value is None for value in values) else sum(values)

def ratio(numerator,denominator):
    return None if numerator is None or denominator is None or denominator<=0 else round(numerator/denominator*100,4)

def field(table,n):return f'{table}_E{n:03d}'

SPECS=[
 ('USA_ACS_POP_TOTAL','Population, ACS 5-year estimate','Population','people','B01003',lambda r:num(r,field('B01003',1)),[1],None,'Resident population estimate.'),
 ('USA_ACS_FEMALE_PCT','Female population','Population','%','B01001',lambda r:ratio(num(r,field('B01001',26)),num(r,field('B01001',1))),[26],[1],'Female population as a share of the total population.'),
 ('USA_ACS_AGE_0_14_PCT','Population aged 0–14','Population','%','B01001',lambda r:ratio(total(r,[field('B01001',i) for i in [3,4,5,27,28,29]]),num(r,field('B01001',1))),[3,4,5,27,28,29],[1],'Population aged 0–14 as a share of the total population.'),
 ('USA_ACS_HOUSEHOLDS_TOTAL','Households','Households and housing','households','B11001',lambda r:num(r,field('B11001',1)),[1],None,'Total households.'),
 ('USA_ACS_HOUSING_UNITS_TOTAL','Housing units','Households and housing','housing units','B25001',lambda r:num(r,field('B25001',1)),[1],None,'Total housing units.'),
 ('USA_ACS_LACKING_PLUMBING_PCT','Occupied housing units lacking complete plumbing facilities','Water and sanitation','% of occupied housing units','B25047',lambda r:ratio(num(r,field('B25047',3)),num(r,field('B25047',1))),[3],[1],'Occupied housing units lacking complete plumbing facilities; this combined plumbing measure is not a separate drinking-water or sewer-access measure.'),
 ('USA_ACS_HIGH_SCHOOL_OR_HIGHER_PCT','Population age 25+ with high school credential or higher','Education','% of population age 25+','B15003',lambda r:ratio(total(r,[field('B15003',i) for i in range(17,26)]),num(r,field('B15003',1))),list(range(17,26)),[1],'Population age 25+ with a regular high school diploma, GED or higher attainment.'),
 ('USA_ACS_LABOR_FORCE_PCT','Population age 16+ in the labor force','Employment','% of population age 16+','B23025',lambda r:ratio(num(r,field('B23025',2)),num(r,field('B23025',1))),[2],[1],'Population age 16+ in the labor force.'),
 ('USA_ACS_DISABILITY_PCT','Civilian noninstitutionalized population with a disability','Disability','%','C18108',lambda r:ratio(total(r,[field('C18108',i) for i in [3,4,7,8,11,12]]),num(r,field('C18108',1))),[3,4,7,8,11,12],[1],'Civilian noninstitutionalized population reporting one or more disability types.'),
 ('USA_ACS_FOREIGN_BORN_PCT','Foreign-born population','Migration','%','B05002',lambda r:ratio(num(r,field('B05002',13)),num(r,field('B05002',1))),[13],[1],'Foreign-born population as a share of total population.'),
 ('USA_ACS_HISPANIC_LATINO_PCT','Hispanic or Latino population','Race and ethnicity','%','B03003',lambda r:ratio(num(r,field('B03003',3)),num(r,field('B03003',1))),[3],[1],'Hispanic or Latino population of any race as a share of total population.'),
 ('USA_ACS_UNINSURED_PCT','Civilian noninstitutionalized population without health insurance','Health','%','B27010',lambda r:ratio(total(r,[field('B27010',i) for i in [17,33,50,66]]),num(r,field('B27010',1))),[17,33,50,66],[1],'Civilian noninstitutionalized population without health insurance coverage.'),
 ('USA_ACS_POVERTY_PCT','Population below the poverty level','Poverty','%','B17001',lambda r:ratio(num(r,field('B17001',2)),num(r,field('B17001',1))),[2],[1],'Population for whom poverty status is determined with income below the poverty level.'),
 ('USA_ACS_SNAP_HOUSEHOLDS_PCT','Households receiving SNAP benefits','Food assistance','% of households','B22003',lambda r:ratio(num(r,field('B22003',2)),num(r,field('B22003',1))),[2],[1],'Households receiving Food Stamps/SNAP in the past 12 months; this is a program-participation measure, not a nutrition outcome.'),
 ('USA_ACS_BROADBAND_PCT','Households with broadband Internet subscription','Connectivity','% of households','B28002',lambda r:ratio(num(r,field('B28002',4)),num(r,field('B28002',1))),[4],[1],'Households with broadband Internet subscription of any type.')
]

def shp_features(zip_path,kind,areas):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.work'/'python-packages'))
    import shapefile
    extracted=zip_path.parent/(zip_path.stem+'-extracted');extracted.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:z.extractall(extracted)
    shp=next(extracted.glob('*.shp'));reader=shapefile.Reader(str(shp));features=[]
    for record,shape in zip(reader.records(),reader.shapes()):
        data=record.as_dict();code=str(data['STATEFP']) if kind=='state' else str(data['GEOID'])
        gid=('0400000US'+code) if kind=='state' else ('0500000US'+code)
        if gid not in areas:continue
        features.append({'type':'Feature','properties':{'territory_id':areas[gid]['id'],'source_id':'usa-census-cartographic-boundaries-2023','official_code':code,'code_system':'Census ANSI/FIPS','geometry_edition':'2023 Census cartographic boundary 1:5,000,000','join_method':'Exact Census GEOID/FIPS join','reference_only':True},'geometry':shape.__geo_interface__})
    return features

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--raw-dir',required=True);args=ap.parse_args()
    out=Path(args.out).resolve();raw=Path(args.raw_dir).resolve();out.mkdir(parents=True,exist_ok=True);raw.mkdir(parents=True,exist_ok=True);receipts=[]
    geo_path=raw/'Geos20235YR-through-county.txt';receipts.append(acquire_prefix(ACS_GEOS,geo_path));areas=load_geos(geo_path)
    tables={};metadata={}
    for table in TABLES:
        meta=raw/f'{table}-variables.json';receipts.append(download(f'{META_ROOT}/{table}.json',meta));metadata[table]=json.loads(meta.read_text(encoding='utf-8'))
        target=raw/f'acsdt5y2023-{table.lower()}-through-county.dat';receipts.append(acquire_prefix(f'{ACS_ROOT}/acsdt5y2023-{table.lower()}.dat',target));tables[table]=load_table(target,areas)
    state_zip=raw/'cb_2023_us_state_5m.zip';county_zip=raw/'cb_2023_us_county_5m.zip'
    receipts.append(download(f'{BOUNDARY_ROOT}/{state_zip.name}',state_zip));receipts.append(download(f'{BOUNDARY_ROOT}/{county_zip.name}',county_zip))
    territories=[]
    for gid,area in areas.items():
        if area['level']=='country':continue
        parent='USA' if area['level']=='state' else f"USA:ACS2023:STATE:{area['code'][:2]}"
        territories.append({'id':area['id'],'country_id':'USA','name':area['name'],'level':area['level'],'type':area['level'],'parent_id':parent,'official_code':area['code'],'code_system':'Census ANSI/FIPS','boundary_version':'2023 Census cartographic boundary 1:5,000,000','valid_from':'2023-01-01'})
    indicators=[];observations=[];sources=[]
    retrieved=datetime.now(timezone.utc).date().isoformat()
    for iid,name,theme,unit,table,calc,numerator,denominator,definition in SPECS:
        source_id=f'usa-acs-2023-{table.lower()}'
        formula=f"{'+'.join(field(table,i) for i in numerator)}"+(f" / {field(table,denominator[0])} * 100" if denominator else '')
        concept=metadata[table].get('variables',{}).get(f'{table}_{numerator[0]:03d}E',{}).get('concept',definition)
        indicators.append({'id':iid,'name':name,'theme':theme,'unit':unit,'definition':definition,'definition_id':f'ACS5-2023-{table}','population':concept,'measurement_method':'source_reported' if denominator is None else 'derived_from_source_counts','aggregation':'sum' if denominator is None else 'none','period_policy':'fixed_source_period','series_family':'census','display_role':'primary','source_id':source_id,'source_locator':f'{table}: {formula}'})
        if not any(source['id']==source_id for source in sources):sources.append({'id':source_id,'name':f'2023 ACS 5-year Detailed Table {table}','publisher':'United States Census Bureau','url':f'https://data.census.gov/table/ACSST5Y2023.{table}','status':'ready','retrieved_at':retrieved,'reference_period':'2019–2023 ACS 5-year estimate','geographic_level':'United States, state and county','license':'United States Government public data; verify Census terms','license_url':'https://www.census.gov/about/policies/open-gov/open-data.html','source_locator':f'{table}: retained fields and formulas listed on each indicator','note':'AreaData acquired the official table-based Summary File prefix through summary level 050 and retained the exact rows used. Margins of error remain in the archived source rows; this dashboard currently displays estimates.'})
        for gid,area in areas.items():
            value=calc(tables[table][gid]);row=tables[table][gid]
            observations.append({'territory_id':area['id'],'indicator_id':iid,'period':'2023','value':value,'status':'observed' if value is not None else 'missing','source_id':source_id,'definition':definition,'definition_id':f'ACS5-2023-{table}','unit':unit,'population':concept,'measurement_method':'source_reported' if denominator is None else 'derived_from_source_counts','source_locator':f'{table}: {formula}','formula':formula,'numerator':None if denominator is None else total(row,[field(table,i) for i in numerator]),'denominator':None if denominator is None else num(row,field(table,denominator[0]))})
    boundary_source={'id':'usa-census-cartographic-boundaries-2023','name':'2023 Census cartographic boundary files, 1:5,000,000','publisher':'United States Census Bureau','url':'https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html','status':'ready','retrieved_at':retrieved,'reference_period':'2023','geographic_level':'state and county','license':'United States Government public data; cartographic boundaries are reference geometry','license_url':'https://www.census.gov/about/policies/open-gov/open-data.html','note':'Official Census cartographic boundary files joined by exact FIPS/GEOID. Reference geometry is not a legal boundary certification.'}
    sources.append(boundary_source);features=shp_features(state_zip,'state',areas)+shp_features(county_zip,'county',areas)
    states=[row['id'] for row in territories if row['level']=='state'];comparisons=[{'parent_id':'USA','member_ids':states,'label':'States and District of Columbia','membership_note':'2023 ACS state geography; Puerto Rico is a separate UN M49 AreaData entry.','source_ids':['usa-acs-2023-b01003','usa-census-cartographic-boundaries-2023']}]
    for state in states:
        members=[row['id'] for row in territories if row['parent_id']==state]
        comparisons.append({'parent_id':state,'member_ids':members,'label':f"Counties and county equivalents in {next(row['name'] for row in territories if row['id']==state)}",'membership_note':'2023 ACS county geography joined by exact five-digit FIPS code.','source_ids':['usa-acs-2023-b01003','usa-census-cartographic-boundaries-2023']})
    bundle={'schema_version':'1.0','country_area_id':'USA','period':'2023','territories':territories,'terminal_territory_ids':[row['id'] for row in territories if row['level']=='county'],'comparisons':comparisons,'indicators':indicators,'observations':observations,'sources':sources,'boundaries':{'type':'FeatureCollection','features':features},'receipt':{'generated_at':datetime.now(timezone.utc).isoformat(),'collector':'collect-usa-census.py','selected_geography_count':len(areas),'state_count':len(states),'county_count':len([r for r in territories if r['level']=='county']),'indicator_count':len(indicators),'observation_count':len(observations),'boundary_feature_count':len(features),'receipts':receipts}}
    (out/'usa-census-bundle.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'collection-receipt.json').write_text(json.dumps(bundle['receipt'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:bundle['receipt'][k] for k in ['selected_geography_count','state_count','county_count','indicator_count','observation_count','boundary_feature_count']},indent=2))

if __name__=='__main__':main()

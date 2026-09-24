"""Add checked national planning-law/guidance locations without inventing local plans."""
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/dashboard.json'
RAW = ROOT / 'raw/planning'
base = json.loads(DATA.read_text(encoding='utf-8'))
checked_at = '2026-09-24'

specs = [
    ('bfa-mef-pcd-guide-2024', 'Guide méthodologique de planification locale: PCD (December 2024)',
     'https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/GMPL_PCD_Version_definitive_1.pdf',
     'Ministère de l’Économie et des Finances', 'pcd-guide.pdf', '2024-12', 'reference'),
    ('bfa-mef-prd-guide-2024', 'Guide méthodologique de planification locale: PRD (December 2024)',
     'https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/GMPL_PRD_Version_definitive_1.pdf',
     'Ministère de l’Économie et des Finances', 'prd-guide.pdf', '2024-12', 'reference'),
    ('bfa-collectivities-code-2025', 'Loi n°024-2025/ALT portant Code général des collectivités territoriales',
     'https://www.academiedepolice.bf/index.php/telechargement/category/25-deconcentration-et-decentralisation?download=226:code-general-des-colectivite',
     'Assemblée législative de transition / Académie de Police du Burkina Faso',
     'collectivities-code-2025.pdf', '2025-12-30', 'reference'),
    ('bfa-pld-monitoring-2024', 'Rapport national 2024 sur les plans locaux de développement',
     'https://www.finances.gov.bf/fileadmin/user_upload/storage/fichiers/MEF_RAPPORT_NATIONAL_2024_SUIVI_PLD_FINAL.pdf',
     'Ministère de l’Économie et des Finances, DGDT', 'pld-monitoring-2024.pdf',
     '2024 reporting; November 2025 publication', 'implementation'),
]
for sid, name, url, publisher, file, period, category in specs:
    path = RAW/file
    assert path.read_bytes().startswith(b'%PDF-'), path
    assert not any(s['id']==sid for s in base['sources'])
    base['sources'].append({
        'id':sid,'name':name,'url':url,'publisher':publisher,
        'reference_period':period,'status':'ready','retrieved_at':checked_at,
        'sha256':sha256(path.read_bytes()).hexdigest(),
        'raw_path':'raw/planning/'+file,
        'note':'Official body acquired. Applicability, administrative edition, any area-specific legal status and source redistribution terms need separate review.'
    })
    base['documents'].append({
        'id':'doc-'+sid,'territory_id':'BFA','title':name,'url':url,
        'source_id':sid,'availability':'body_acquired',
        'official_status':'unverified','category':category,'period':period,
        'note':'Country-level reference. Its presence does not establish any selected commune’s approved plan or current status.'
    })

other_links = [
    ('INSD RGPH 2019 source catalogue', 'https://microdata.insd.bf/index.php/catalog/69/related-materials'),
    ('INSD 2019 locality file', 'https://microdata.insd.bf/index.php/catalog/69/download/270'),
    ('INSD 2019 statistical tables', 'https://web2.insd.bf/sites/default/files/2024-06/Volume%20des%20tableaux%20statistiques_%205e%20RGPH.pdf'),
    ('2025 administrative reform notice: 17 regions / 47 provinces', 'https://www.presidencedufaso.bf/conseil-des-ministres-du-2-juillet-2025/'),
    ('ALT adoption notice for the 2025 local-government code', 'https://alt.bf/535'),
]
base['planning'] = {
    'title':'Planning materials and links',
    'purpose':'Review the legal and methodological sources alongside the 2019 census evidence. Local plan status is shown only when an area-specific record has been verified.',
    'sections':[
        {'id':'plan','label':'Area plans','empty_message':'No area-specific PCD or PRD body has been verified for this area.'},
        {'id':'budget','label':'Budgets','empty_message':'No area-specific budget was acquired.'},
        {'id':'implementation','label':'Implementation reports','empty_message':'No area-specific implementation report was acquired.'},
        {'id':'evaluation','label':'Evaluations','empty_message':'No area-specific evaluation was acquired.'},
        {'id':'reference','label':'Legal, census and methodological references','empty_message':'Use the country-wide references below; no area-specific reference was acquired.'},
    ],
    'system':{
        'label':'Burkina Faso local development planning (PCD / PRD)',
        'scope':'The December 2024 MEF guides address communal development plans (PCD) and regional development plans (PRD). They predate the 2025 administrative reform and the December 2025 territorial-collectivities code. The 2019 census geography here is historic and does not identify a current legal planning authority for each old region or commune.',
        'cycle':'The 2024 guides describe five-year planning horizons; current application to each selected post-reform authority must be checked against the 2025 code and actual plan.',
        'source_ids':['bfa-mef-pcd-guide-2024','bfa-mef-prd-guide-2024','bfa-collectivities-code-2025'],
    },
    'outputs':['markdown','html','evidence_csv','documents_csv'],
    'related_links':[
        *[{'label':name,'url':url} for name,url in other_links],
        *[{'label':name,'url':url} for _,name,url,*_ in specs],
    ],
    'update':{'status':'current','checked_at':checked_at,
              'message':'Source locations and national bodies checked. Area-specific plans, budgets and legal unit correspondence remain unverified.'},
}
base['collection']['adapters'].append('bfa-local-planning-source-catalogue')
base['collection']['notes'].append('2024 PCD/PRD methodology and 2025 territorial code are linked separately; no historic census region is declared a current legal plan authority by inference.')
DATA.write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sources':len(specs),'documents':len(base['documents']),'related_links':len(base['planning']['related_links'])}))

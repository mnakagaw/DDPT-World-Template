import test from 'node:test';
import assert from 'node:assert/strict';
import {discoverHondurasMunicipalReports,normalizeHondurasPdfUrl} from '../lib/honduras-municipal-census.mjs';

test('Honduras municipal PDF URLs are restricted to the official HTTPS host',()=>{
  assert.equal(
    normalizeHondurasPdfUrl('https://temp.ine.gob.hn/documentos/2013/municipio.pdf'),
    'https://ine.gob.hn/documentos/2013/municipio.pdf'
  );
  assert.throws(()=>normalizeHondurasPdfUrl('https://example.org/municipio.pdf'),/Unapproved Honduras municipal PDF URL/);
  assert.throws(()=>normalizeHondurasPdfUrl('http://ine.gob.hn/municipio.pdf'),/Unapproved Honduras municipal PDF URL/);
});

test('Honduras discovery deduplicates duplicate post aliases by normalized PDF URL',async()=>{
  const categories=[{id:101,name:'Atlántida',slug:'atlantida',count:2},{id:102,name:'Colón',slug:'colon',count:1}];
  const posts={
    101:[
      {id:1,link:'https://ine.gob.hn/a',title:{rendered:'Esparta – Año 2013'},content:{rendered:'<a href="https://temp.ine.gob.hn/reports/esparta.pdf">PDF</a>'}},
      {id:2,link:'https://ine.gob.hn/b',title:{rendered:'Esparta (copia) – Año 2013'},content:{rendered:'<a href="https://ine.gob.hn/reports/esparta.pdf">PDF</a>'}}
    ],
    102:[
      {id:3,link:'https://ine.gob.hn/c',title:{rendered:'Trujillo – Año 2013'},content:{rendered:'<a href="https://ine.gob.hn/reports/trujillo.pdf">PDF</a>'}},
      {id:4,link:'https://ine.gob.hn/old',title:{rendered:'Trujillo – Año 2001'},content:{rendered:'<a href="https://ine.gob.hn/reports/old.pdf">PDF</a>'}}
    ]
  };
  const fetchImpl=async url=>({
    ok:true,
    json:async()=>String(url).includes('/categories?')?categories:posts[Number(new URL(url).searchParams.get('categories'))]
  });
  const index=await discoverHondurasMunicipalReports({fetchImpl,expectedCount:2});
  assert.equal(index.report_count,2);
  assert.deepEqual(index.reports.map(row=>row.pdf_url).sort(),[
    'https://ine.gob.hn/reports/esparta.pdf',
    'https://ine.gob.hn/reports/trujillo.pdf'
  ]);
  const esparta=index.reports.find(row=>row.pdf_url.endsWith('/esparta.pdf'));
  assert.equal(esparta.discovery_aliases.length,1);
  assert.equal(esparta.discovery_aliases[0].post_id,2);
});

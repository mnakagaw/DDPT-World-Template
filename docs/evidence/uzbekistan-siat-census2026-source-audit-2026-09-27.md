# Uzbekistan 2026 SIAT・国勢調査速報 原本／採否監査

2026-09-27 JST。独立・ignored候補 `generated/uzbekistan-areadata-20260927` は未公開。9原本のURL、byte長、SHA-256は[manifest](../../config/uzbekistan-2026-source-manifest.json)に固定した。全系列・表・sheetの棚卸しは[機械監査JSON](uzbekistan-siat-census2026-table-audit-2026-09-27.json)を参照。初期`SOURCE_PREFLIGHT`は国内source所在未調査だったため、国内公式資料から探索した。国際共通sourceのUZB×テーマ×年×地方粒度は未確認。

## 取得原本、全項目と採否

| source | 原本の棚卸し・採否 |
|---|---|
| [SIAT permanent population total](https://siat.stat.uz/data/246/?lang=en) 2.01.02.0001 | 221コード行、2010–2026の17年、3,757数値セル。2026列の全国＋14州級＋206地区／市のみ採用。単位は千人、参照日は1月1日。 |
| [SIAT female](https://siat.stat.uz/data/244/?lang=en) 2.01.02.0003 | 221行、2014–2026の13年、2,873数値セル。2026列のみ採用。 |
| [SIAT male](https://siat.stat.uz/data/245/?lang=en) 2.01.02.0002 | 221行、2010–2026、3,757数値セル。2026列のみ採用。 |
| [SIAT rural](https://siat.stat.uz/data/247/?lang=en) 2.01.02.0005 | 221行、2010–2026、3,757数値セル。2026列のみ採用。公表0は0として保持。 |
| [SIAT urban](https://siat.stat.uz/data/248/?lang=en) 2.01.02.0004 | 221行、2010–2026、3,757数値セル。2026列のみ採用。 |
| [NSC 2026-01-27人口リリース](https://stat.uz/img/news/demografiya-press-reliz-en_p24116.pdf) | 7 PDF頁。全国＋14州級の2026年1月1日人口をSIAT総数と照合、15行一致。詳細本文の別数値を新指標として採用しない。 |
| [2026年国勢調査速報報告](https://aholi.stat.uz/en/64-news-eng/6232-preliminary-results-of-population-and-agriculture-census-conducted-in-the-republic-of-uzbekistan-in-2026) | 90 PDF頁、本文印刷67頁。印刷p.4の総数・男女とp.5の都市・農村、全国＋14州級の150数値欄を確認して5×15＝75公表値を別系列に採用。p.4–5の画像を目視照合。報告書で列挙した他25表は`priority_unassessed`で、地区級人口の不存在とは断定しない。参照瞬間は2026年1月15日、**速報**。 |
| [国勢調査速報Excel](https://aholi.stat.uz/en/64-news-eng/6260-preliminary-results-of-the-2026-population-census) | `Contents`＋1.1–1.11の12 sheet、230数値セル、dash 6を棚卸し。11番号表は農業の全国表であり、地区級人口Excelではない。農業の数値欄は意味・期間・母集団の採用審査待ち。 |
| [MOF地方予算表](https://gov.uz/en/imv/sections/view/190028) | 取得HTMLの全国計＋14州級行、6数値列＝90セルを確認。Revenue/Transfer/Expenditureの三つ組が2組あり、各組の四半期・予算/実績の意味を原本だけで確定できない。**数値は不採用**。州級の予算資料所在としてのみ表示し、執行実績・承認を示さない。 |

5 SIAT CSVの全17,901数値セルは機械的に読み、2026年の1,105セルだけを採用した。2026年の男女計・都市農村計は221行ずつ一致し、14親×5指標の70親子和と5指標の全国和も一致する。過去年には設置前を含む0が計1,128セルあり、8セルに浮動小数点の桁ノイズがある。旧年を現行COATOへ無条件に接続した時系列は作らない。

全国SIAT推計は**38,236.7千人**（2026-01-01）、国勢調査速報は**39,047,321人**（2026-01-15）。時点・方法・単位が異なるため差を人口増加と解釈しない。WDIの年央推計も全国参考の別系列。国勢調査報告の州級行にはコードが印刷されていないため、SIATの14件と一意の名称・行政型で暫定対応し、コード同一の証明とはしない。

## 地理と計画

SIAT CSVのCOATO/MHOBTコード列から、全国1・第一階層14（Karakalpakstan共和国、Tashkent市、12州）・地区／市206（市31・地区175）の階層を固定した。同名のTashkent州`1727`とTashkent市`1726`を分離。2017年geoBoundariesの初期図形は2026年のコード・境界と照合できず削除した。地図は図形欠測を示し、階層selectorと各指標下の全件表で代替する。法定の地域計画主体と内部診断の地区／市は同一視しない。

[ASDRの2030年地域戦略準備課題](https://asdr.gov.uz/en/tasks-set-for-the-development-of-regional-strategies/)は14州級の策定作業についての公式所在であり、各地域計画の本文・承認の証拠ではない。[PF-21の法令所在](https://test.lex.uz/docs/8050769)は全国戦略としてのみ参照し、法令本文の現行効力・地域別適用・地方の様式は未監査。地区／市の計画主体、州別計画本文、予算見込・実支出・実施・公式評価も未確認。MOF表は期間不明のまま採用しない。

## 制作者側の検証と閉鎖条件

dataset SHA-256 `f2a65f3fc267661a8634ca5079a5e70eb8c2220875e2116fe4cd2442b28eff2f`。schema 0.2、国内10指標・直接1,180観測。全国14/14、Karakalpakstan地区17/17、Tashkent市地区12/12の同条件比較。9代表地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVにおける180値／欠測セルを、独立転記した原表値と照合。ブラウザーで全国→Karakalpakstan→Nukus市→同じ親全体、Tashkent州とTashkent市の識別、Yangikhayot地区→市全体、計画資料の地域限定を確認。上部の全国人口はSIATと速報を別カードにした。validator 0 errors/warnings、build、`npm run check` 166件、`npm test` 219/219。これらは42シナリオ全件合格や独立`ACCEPT`ではない。

残件は(1)速報PDFの他25表・農業11 sheetの全数値欄と母集団の意味監査、確報版の追跡、(2)過去年の行政変更と公式現行コード台帳・同版図形・国勢調査行の対照、(3)14地域の計画本文・承認・地方制度と地区適用、期間を確定した予算/支出/評価、(4)二次利用条件、現地利用、狭幅/全頁印刷、42シナリオ、独立完成監査。候補は部分成果・未公開。

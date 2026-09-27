# Kazakhstan BNS 2026／2021 census 原本・採否監査

2026-09-27 JST。独立・ignored候補 `generated/kazakhstan-areadata-20260927` は未公開。初期 `SOURCE_PREFLIGHT` に国内の具体的source事前台帳はなく、BNS・Adilet・gov.kz・NSDIを調査した。9取得原本のURL、byte長、SHA-256は[manifest](../../config/kazakhstan-2026-source-manifest.json)、表・数値列・コード照合は[機械監査JSON](kazakhstan-bns2026-table-audit-2026-09-27.json)に固定した。初期WDI全国系列以外、国際共通sourceのKAZ×テーマ×年×国内粒度のavailabilityは未確認。

## 取得原本と採否

| 原本 | 棚卸し、採用と未監査 |
|---|---|
| [BNS 2026年7月人口・男女・都市農村](https://stat.gov.kz/en/industries/social-tatistics/demography/spreadsheets/) | 6 sheet、数値風セル6,917。sheet 2の全国＋20第一階層＋228第二階層の249行×9列＝2,241直接値を採用。sheet 1の180第一階層セルは重複照合のみ。sheet 3の地区中心・集落行4,491数値風セルは重複範囲と地理型が未整理で `priority_unassessed`。公表0は0。 |
| [BNS 2026年8月人口・変動](https://stat.gov.kz/en/industries/social-tatistics/demography/spreadsheets/) | 4 sheet、数値風セル423。全国＋20第一階層の8月1日総人口、年初からの総変化・自然変化・純移動、4列84直接値を採用。都市・農村ブロック、率等は意味監査待ち。8月の地区値を7月値で埋めない。 |
| [BNS 2026年7月行政単位](https://stat.gov.kz/en/industries/social-tatistics/demography/spreadsheets/) | 24 sheet、数値風セル1,331。17 oblast＋3 republican cityと階層件数を照合。行政数は人口indicatorにしない。他の列は未監査。 |
| [BNS KATO 2026-09-18](https://stat.gov.kz/ru/classifiers/statistical/21/) | 15,586コード行。7月人口の20第一階層と228第二階層を親・行順・名称で全件対応。Oskemen／Ust-Kamenogorsk別名を照合記録に明示。分類版は人口参照日より後で、7月時点のコードの同一性は未証明。 |
| [BNS 2021国勢調査 Volume I](https://stat.gov.kz/en/national/2021/) | PDF物理228頁。目次の18表見出しを記録。印刷p.5の全国総数19,186,015・都市11,741,342・農村7,444,673、p.29の男性9,324,840・女性9,861,175の5値のみ採用。該当頁を画像でも照合。その他の数値列・地方表は未監査。2021地域は2022年分割前で2026 KATOへ接続しない。 |
| [Adilet国家計画制度決定790](https://old.adilet.zan.kz/rus/docs/P1700000790) | 2026-07-14改正を含む本文。第7章66–79項でoblast／republican cityとdistrict／regional cityの計画主体、maslikhat承認、5年計画の3年ごとの策定、投資計画とモニタリングを確認。個別計画の承認・執行は推定しない。 |
| [Ulytau oblast 2026–2030計画](https://www.gov.kz/memleket/entities/ulytau/documents/details/1017009?lang=ru) | 本文HTML取得、5表・数字を含む欄1,179を機械棚卸し。承認文書と目標・基準・財源・実績の意味監査が未了で数値不採用。Ulytauの計画本文のみ表示。 |
| [Burabay district 2026–2030計画](https://www.gov.kz/memleket/entities/aqmola-burabay/press/news/details/1135605) | 本文HTML取得、7表・数字を含む欄448を機械棚卸し。冒頭は2025-12-19の地区maslikhat決定`8C-39/3`による承認と記載。Burabay限定で表示。目標値を実績にしない。決定原本と現在効力は追加確認。 |
| [NSDI Geoportal WFS](https://map.gov.kz/) | `geonode:border_districts`の属性だけ取得。254 feature、KATO固有コード211、コード欠落1、admin_level欠落40、重複コード14種、候補248地方ID中37未出現。layer日付、完全な図形と権利は未確認。図形0件採用。 |

別に[Akmola oblast計画](https://www.gov.kz/memleket/entities/aqmola/documents/details/951803?lang=kk)、[Almaty oblast計画](https://www.gov.kz/memleket/entities/almobl/documents/details/1015736?lang=ru)、[Akmola 2026年7月予算執行報告](https://www.gov.kz/memleket/entities/aqmola/documents/details/1039733?lang=ru)の公式所在を確認した。前2件の取得HTMLは約2.7KBの表示shellで本文とは扱わない。予算報告も本文・金額未取得。いずれも選択地域限定の `link_verified` で、計画承認・支出実績は断定しない。

## 値、地理、残る作業

7月全国20,590,589人は行内1,245、地域子合計180、全国合計9、sheet 1対2の第一階層180セルで検算。8月全国20,604,819人は別参照日で、行内120・全国5の検算を通した。2021国勢調査、7月・8月推計、WDI年央推計は別indicatorとし、差を人口増加率にしない。

候補は全国1＋17 oblast＋3 republican city＋228 district／city akimat／都市内district＝249地域、国内18指標・2,330直接観測。親自身の公表値を使い、不完全な子の小計は親の観測にしない。全国20、Abay12、Akmola20、Astana6の比較対象を保持。初期2017年geoBoundaries図形16件は同版照合できないため外し、図形欠測と階層選択・全件表で代替する。

原資料のsheet／表ごとの数値風セルと列は機械的に棚卸した。**全列の意味監査が済んだという記録ではない。** 7月sheet 3、8月の未採用列、行政24表、2021国勢調査地方表、計画本文の数値、他の国勢調査巻、地方計画・予算・実績・評価は `priority_unassessed` または未取得。未取得を制度上の不存在としない。原本別再配布条件も未確認。

9原本のhash不一致ならimportは停止する。validator 0 errors/warnings、build成功、11代表地域の診断CSV/HTML/Markdown・計画HTML・根拠CSVの401値／欠測セルを原Excel等と照合。2021全国5値も別年出力で確認。ブラウザーで全国→Akmola→Burabay→Akmola全体の再選択と計画資料の地域分離を確認。全頁印刷、狭幅、42シナリオ全件、現地担当、独立監査は未実施。次は国勢調査歴史境界と全表の意味、KATOの日付差、NSDI完全図形・利用条件、地方計画本文・承認・投資計画・予算執行・公式評価、共通sourceのavailabilityを確認する。**独立 `ACCEPT` 前に公開しない。**

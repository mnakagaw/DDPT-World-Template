# Singapore SingStat 2026・URA MP2025 原本／採否監査

2026-09-27 JST。対象は独立・ignored候補 `generated/singapore-areadata-20260927`。公開していない。公式原本7件のbyte長とSHA-256は [manifest](../../config/singapore-population2026-source-manifest.json) に固定し、機械的な全sheet・数値欄・注記は候補内 `evidence/SGP_POPULATION2026_AUDIT.json` に保存した。取得済みと国別完成を区別する。

## 原本と系列

| 原本 | 所在、版、採否 |
|---|---|
| [SingStat Population Trends 2026 geospatial ZIP](https://www.singstat.gov.sg/publication-resources/population-trends-2026) | 2026-09-25公表、June 2026住民人口。3 XLSX・7 sheetから選定6指標を採用。ZIP内の各表はMaster Plan **2025**の区域。 |
| [同報告書PDF](https://www.singstat.gov.sg/publication-resources/population-trends-2026) | 54 PDF頁。printed p.15は55 Planning AreaとMP2025を明記、Tampines 296,060人。統計上の居民は国民と永住者で、12か月以上継続して国外にいた者を除く。全表の意味監査は未完了。 |
| [URA MP2025 Planning Area Boundary (No Sea)](https://data.gov.sg/datasets/d_2cc750190544007400b2cfd5d7f53209/view) | 2025-12版の**表示用の参考図形**55件。`PLN_AREA_N`全55名称が2026 SingStatのPlanning Area 55名称と一致。`PLN_AREA_C`をURAコードとして採用。法定境界の証明とはしない。 |
| [URA MP2025 Region Boundary (No Sea)](https://data.gov.sg/datasets/d_4ce0038f7ac689652350bb91b7fb92ed/view) | 5件を原本保存。2026 ZIPに同じ版の地域別直接人口がなく、5 Regionを分析対象・人口集計値にしていない。 |
| [URA MP2025 Written Statement](https://www.ura.gov.sg/land-planning/master-plan/) | 26 PDF頁。本文・区域目録を取得。URAの[2025-12-01官報化の通知](https://www.ura.gov.sg/guidelines/circulars/ppg25-12/)で国全体の法定土地利用Master Planとして扱う。本文全章の数値・事業・実施は意味監査未了。 |
| [2020 Census age-sex-by-planning-area CSV](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view) | 388行・61列、15,906数値セル、7,374 `-` セルを棚卸し。全国居民4,044,210人。**MP2019**の区域であり、MP2025の現行区域へ値を自動移管しない。 |
| [URA MP2019 Subzone Boundary](https://data.gov.sg/datasets/d_8594ae9ff96d0c708bc2af633048edfb/view) | 332図形を歴史版として保存。2026年のSubzone表示に流用していない。 |

[Planning Act 1998](https://sso.agc.gov.sg/Act/PA1998?ValidDate=20251001) Part 2のMaster Plan関連条文は公式所在を確認したが、現行適用・手続の全条文監査は未了。[URAのMP2025紹介](https://www.ura.gov.sg/land-planning/master-plan/)は5年ごとの見直しを説明する。Planning Area/Subzoneは地方政府と同義ではない。計画区域ごとの実施計画、予算、実支出、公式評価は未取得で、国のMP2025を各区域の独立した承認済み計画とは記録していない。2020 Census詳細Statistical Release 1/2の検索上の旧PDF URLはこの環境で404を返し、未取得として残す。

## 全表の機械的棚卸しと採用条件

2026 ZIPの3冊7sheetは、データ行456,288・数値セル244,240・`-`（nil/negligible）212,048。巻末のMP2025版、長期国外不在者除外、10人単位への丸め、住宅分類の脚注も別欄へ保存した。単一年齢・性別表1sheetから年齢`Total`・性別`Total/Males/Females`を、年齢階級・住宅型表の`2026(Total)` sheetから年齢`Total`・`Total HDB^`、`Condominiums and Other Apartments`、`Landed Properties`を選んだ。全388地理行で、2表の総人口`Total`直接セルは一致する。床面積表3sheetとその他の年齢・住宅型・男女別の細分セルは **`priority_unassessed`**。床面積表の`Total*`は床面積情報のない居民を除くため総居民と同じ分母にしない。

採用は全国1、Planning Area 55、Subzone 332の計388統計地域に6指標・2,328 source slots。内訳は**観測1,489、`-`に由来する明示欠測839**。総居民人口は全国直接4,231,520人、Planning Area 48/55観測・7欠測、Subzone 281/332観測・51欠測。Tampines 296,060人。数値のあるPlanning Areaだけを足すと4,231,550人で全国より30人多く、男子2,055,410＋女子2,176,120＝4,231,530人は全国総数より10人多い。各直接値は独立に10人単位へ丸められ、`-`も存在するため、子の合計や男女の和で親の公表値を置き換えない。`-`は厳密な0ではない。

55区域はMP2025名称とURAコード・図形を照合済み。Subzone 332件はSingStatの**Planning Area＋Subzone名の原表キー**を使い、公式SubzoneコードとMP2025図形は未取得。2016年の初期geoBoundaries 5 Region図形は削除した。2020 CensusのMP2019→2026 MP2025の時点付き対照は未作成で、変化率や同名区域の継続を推定しない。WDI全国総人口はSingStatの居民人口と母集団・年が違い、画面では別指標・参考系列として扱う。

## 検証・残件

2026-09-27のdataset SHA-256は `286785d5f0b0368093beefebbdb35f4e148fbd3df1c7ed29efb1587e403aee26`。`validate-country`は0 error/warning、build成功。原本ZIPの全国、Tampines、Tampines East、Ang Mo Kio、Changi Bayの各6セルと、診断CSV/HTML/Markdown・計画HTML・根拠CSVを照合し、全国比較55行を確認した。ブラウザーでは全国比較48/55、Tampines→Tampines East→Tampines全体の再選択、Changi Bay欠測維持、全国MP2025文書と区域文書の分離、比較内Tampines注目時の全国分析対象維持を確認した。共有 `npm run check` 163 JavaScript/JSON、`npm test` 219/219。**42シナリオ全件と独立監査 `ACCEPT`、公開画面の検証ではない。**

残件は(1)2026 ZIP全寸法・2020 Census詳細2冊の意味監査、(2)MP2025 Subzoneコード・図形および2019→2025対照、(3)区域に関係する具体的な計画本文・予算見込・実支出・実施・評価の別々の証拠、(4)再配布条件と現地運用者・言語/端末/回線、(5)42シナリオと独立`ACCEPT`。HDX/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPORのSGP×年×テーマ×粒度は未調査であり、今回の取得や国別統計採用として数えない。

# 実行テンプレート0.6 検証記録

## 対象

- 検証対象commit: `ba6719356c052eeb4b5bc2795207e22691adb4b0`（ベリーズ・グアテマラ国勢調査の収集・抽出・表示実装）
- 検証日: 2026-09-15 JST
- 環境: Windows、Node.js 24.11.1、Python 3.12.14、openpyxl 3.1.5、Codex in-app browser
- データschema: 0.2。国勢調査正規化中間データ: 1.0
- 実取得原本: `.work/census-acquisition-2026-09-15-belize-guatemala/`
- 生成案件: `.work/areadata-ca-v0.6-census-final/`

この版は中米7か国の完成データ版ではない。公式国勢調査人口の最初の2か国アダプターと、残る5か国が欠けても中米全体値を作らない動作を検証する版である。

## 原本取得

`npm run collect:census:central-america -- --out <new-directory>`で、manifestに登録した公式HTTPS URLだけを取得した。取得先は新規ディレクトリに限定し、既存原本を上書きしない。レスポンス容量、リダイレクト先host、XLSXのZIP署名を検査した後、SHA-256と最終URLを`receipt.json`へ保存する。

| ID | 国・年 | 役割 | bytes | SHA-256 | 結果 |
|---|---|---|---:|---|---|
| `BLZ_C2022_POP_SETTLEMENT_SEX` | Belize 2022 | 市・町・村・community候補 | 31,021 | `c7be751b1ef0aaf09da65df90413bd4e12272676622a82bffb29fc686543b4ea` | 取得 |
| `BLZ_C2022_GENERAL_CHARACTERISTICS` | Belize 2022 | 全国・district、変数候補 | 69,401 | `8d649118178f8cc01f9188c049489a9e02817439cdaf78dfe704cd254bf3cdfc` | 取得 |
| `BLZ_C2022_HOUSING` | Belize 2022 | 住宅変数候補 | 79,758 | `caa94f3f50ec43906dba2f59ec4f4a9eb99e8281379a4e927bef6c0bfc65eaa0` | 取得 |
| `GTM_C2018_POP_SEX_AGE_AREA` | Guatemala 2018 | 全国・department・municipality・集落 | 4,072,815 | `b4dfbc6a0373373e8f35827ef5a8d5ed07db5d035225a271061b1869769e96d9` | 取得 |
| `GTM_C2018_POPULATED_PLACE_CENTROIDS` | Guatemala 2018 | 集落centroid照合 | 1,105,747 | `b8ea8fea33e6d606e102e8d96ed692deacec660c028ffcf673f84459bcafe14e` | 取得 |

結果は5件要求、5件取得、失敗0件。`scripts/inspect-census-workbooks.py`は全5原本を読取専用の分析対象として開き、検査前後のhash一致を確認した。原本と正規化JSONはリポジトリへ収録していない。

公式掲載先:

- Belize Statistical Institute: [2022 Population and Housing Census](https://sib.org.bz/census/2022-census/)
- Belize Statistical Institute: [2022 Census Key Findings Report](https://sib.org.bz/wp-content/uploads/CensusKeyFindingsReport_2022.pdf)
- Guatemala INE: [Censo 2018 - Lugares Poblados](https://datos.ine.gob.gt/dataset/censo-2018-lugares-poblados)

## 表・地域の採否

### Belize

- 採用: 2022年全国人口1件、6 district人口。原値はウェイト調整後の小数値を保持し、画面上の人数だけ整数表示に丸める。
- 全国原値: `397483.45623886667`。6 district合計との差は`-0.000000698259100317955`で、浮動小数点精度の範囲だった。
- 監査のみ: 221の個別locality行。公式code列、法定種別列、確認済みpolygonがない。
- 不一致: locality表のStann Creek合計は採用district表より`-1820.1687755472449`、Toledoは`+1820.168775551283`。差が相殺する事実だけを記録し、転記修正や地域の入替えを推定していない。
- 判定: localityはこの版の地域・集計に使わず、districtで停止する。

### Guatemala

- 採用: 2018年全国1件、22 department、340 municipality。追加観測は合計363件。
- 全国人口: `14,901,286`。22 department合計、340 municipality合計、各department内municipality合計はすべて該当する上位値と一致した。
- 監査のみ: 人口表の20,036 populated place行とcentroid台帳をcode・名称の行順で全件照合し、20,036件が一致した。313件は経度・緯度の一方または両方が欠ける。
- 判定: municipalityをterminal analysis levelにし、populated placeはこの版の地図・比較地域に使わない。

2か国合計で、既存7か国に368地域を追加し、国勢調査人口370観測を追加した。生成datasetは376地域、5指標、534観測、13 source、9 gapを持つ。

## 集計・年・欠測

- 指標`CENSUS_POP_TOTAL`を`series_family: census`、`display_role: primary`として追加した。
- 国別の最新利用可能年を使うため`period_policy: latest_available_by_component`を明示した。
- Belizeは2022、Guatemalaは2018と、比較表・地図ラベル・ランキング・CSV・診断出力に各観測の実年を渡す。
- El Salvador、Honduras、Nicaragua、Costa Rica、Panamaは未収録を維持する。
- 中米7か国の国勢調査人口は`No data / incomplete coverage`とし、全体値を生成しない。
- 収録済み2か国の`15,298,769`は`covered subtotal`だけに表示し、7か国合計または同一年人口として扱わない。
- World Bank等の人口・保健・電力・Internetは`international_reference / context`のまま保持し、国勢調査と合算しない。

## 自動検証

| 検証 | 結果 |
|---|---|
| `npm run check` | 48 JavaScript module・JSONを構文確認、合格 |
| `npm test` | 135件中135件合格 |
| Python `py_compile` | 2 script合格 |
| `node scripts/create-central-america.mjs ... --census-data ...` | 248 country/area、3,544国際参照値から再生成成功 |
| `node scripts/validate-country.mjs --project .work/areadata-ca-v0.6-census-final` | error 0 |
| `git diff --check` | 合格 |

validator警告は次の3件だった。

1. Belize General Characteristicsのsource terms要確認。
2. Belize Population by City, Town, Village or Community and Sexのsource terms要確認。
3. 確認済み国別planning documentがない。

## 実画面確認

`http://127.0.0.1:4176/`の生成サイトをデスクトップのin-app browserで確認した。

- 中米地域診断: 7か国を全件表示し、Belize `397,483 / 2022`、Guatemala `14,901,286 / 2018`、他5か国は`No data`。covered subtotalと混合基準年注記を表示。
- Belize: 全国`397,483 / 2022`、6 districtを表示。Corozalを選ぶと`45,310`。その後、上位dropdownでBelizeを選び直すとdistrictが解除され、全国値へ即時復帰。指標と`latest-available`を保持。
- Guatemala: 全国`14,901,286 / 2018`、22 department、340 municipalityへ移動可能。Guatemala departmentは`3,015,081`、municipality code 101は`923,392`。municipality選択後に上位dropdownで国のGuatemalaを選び直すとdepartment・municipalityが解除され、全国値へ即時復帰。指標と期間を保持。
- テーマ診断: country比較は`2 observed / 7 comparable areas`。1位Guatemala `14,901,286 / 2018`、2位Belize `397,483 / 2022`、未順位5件。
- database: 収録済み2か国、未収録5か国、国際参照系列との分離を現在段階として表示。

## 未実施・次工程

- El Salvador、Honduras、Nicaragua、Costa Rica、Panamaの公式国勢調査原本の取得・全表棚卸し・採用。
- Belizeのlocality表不一致、地域code、法定分類、利用条件の確認。
- Belize districtとGuatemala department・municipalityの公式または採用可能な境界版の結合。
- 取得済みBelize住宅表とGuatemalaの性別・年齢・都市農村列を指標化するための分母・定義・全地域整合検査。
- 7か国の計画法、計画主体、既存計画、予算・実績資料の国別アダプター。
- モバイル、出力ファイルの全行印刷、自治体職員による実利用試験。
- MariaDBへのimport、性能試験、FTP公開、`areadata.net`の公開確認。

中米全体として未完成であり、公開済みサイトをこの部分収録版へ置き換えていない。

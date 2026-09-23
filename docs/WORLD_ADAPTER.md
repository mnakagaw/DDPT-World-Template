# 世界入口の収集アダプター

世界から大陸・広域・国へ探索する初期データを作る。schema 0.2の任意`analysis.kind: world`を使い、国内行政階層を扱う国別datasetとは分ける。国別の既存収集器・成果を上書きしない。

```sh
node scripts/create-world.mjs --out generated/world
node scripts/serve.mjs --dir generated/world/site --port 4173
```

Node 22以降、外部npm依存・APIキーなし。既存出力は拒否。既定は実行年と直前5年の年次系列、`--start-year`と`--end-year`で最大21年を指定する。失敗した応答も原本・取得日時・SHA-256・理由を保存する。国台帳を完全取得できなければ停止し、指標・境界の部分失敗は不足を記録して続行。数値が0件の生成は成功としない。公開・hostingは行わない。

## 一次資料と範囲

| 入力 | 採用・留保 |
|---|---|
| [UN M49英語台帳](https://unstats.un.org/unsd/methodology/m49/overview/) | 全country/area行のISO-alpha2・alpha3・M49と元のRegion/Sub-region/Intermediate membershipを保存。統計上の区分であり主権・法定行政区分の認定ではない。HTMLヘッダー変更・重複IDを拒否 |
| [World Bank API](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures) | WDIの人口、出生時平均余命、電力アクセス、インターネット利用。ページ数と件数を検証。非aggregate economyとUNのISO2/ISO3が厳密一致した国値、および公式`WLD`系列だけ採用 |
| [Natural Earth配布元](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/) | 110m Admin-0 **map units**を[固定commit](https://github.com/nvkelso/natural-earth-vector/tree/f1890d9f152c896d250a77557a5751a93d494776/geojson)で取得。repository release v5.1.2、commit `f1890d9f152c896d250a77557a5751a93d494776`。公式ページのcountries層v5.1.1表示と、リポジトリ全体のrelease名を区別する |

国所属・指標・境界設定は`config/world-membership.json`。M49の5 Region（Africa/Americas/Asia/Europe/Oceania）を大陸入口とし、AntarcticaはUN台帳でRegion未所属のためWorld直下のcountry/areaに残す。取得時の台帳の追加・削除は原本と抽出台帳で記録し、特定国数を固定しない。

Americasの画面階層はNorthern America・South America・独自**Central America + Caribbean**。独自広域はUN 013＋029の結合で、013に含まれるMexicoも所属する。国は一つの親にだけ登録する。UN 419 Latin America and the Caribbeanの公式階層をそのまま表示したものではなく、各国の`m49_membership`に元の全階層を残す。他大陸は元のM49下位区分を保持する。この独自広域をUN/WB/OWIDの既存集計と同一視しない。

## 値・比較・地図の意味

- `WLD`の値はWorld Bankの公表World系列。その内訳が画面の全M49 country/areaと厳密一致すると主張しない。
- 大陸・小区分・独自広域について厳密同一範囲の公式集計を取得していなければ`missing/null`。国人口の足し算や率の平均で埋めない。
- 国の欠測とゼロを分離し、未公表の年を前の年で埋めない。各指標の定義・単位・原資料機関・API更新日・脚注を保存する。APIの単位欄が空のときは明示した指標別単位表を使い、その由来を記録する。
- 比較の母集団は`analysis.comparisons`の`parent_id/member_ids/membership_note/source_ids`で明示。混在する大陸・国を一つの順位集合にしない。
- 境界はNatural Earth `ISO_A3`＋`ISO_N3`がUN ISO3＋M49の両方と厳密一致する図形だけ結合。名前、`-99`、拡張コードの推測置換を使わない。同一キー複数図形は未結合に戻す。小島・係争地・コード不一致は台帳から消さず不足へ残す。
- 国を別々に照合するためmap units層を使う（countries層ではFrench Guiana等が他国形状に含まれる場合がある）。110mの省略・政治的なde facto範囲は残る。図形があることは統計境界の一致を意味しない。
- 大陸・広域の選択図形は、同一版・同一sourceの照合済み国ポリゴンをMultiPolygonに連結した表示専用。欠けたmember IDを記録する。法定境界・面積計算・値集計には使わない。
- 統計地域の`boundary_version`は未確認のためnull。図形版はfeatureの`geometry_edition`とNatural Earth sourceへ分離する。

Natural Earthは[public domain](https://www.naturalearthdata.com/about/terms-of-use/)。WDIは[World Bank利用条件](https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets)と原機関の留保を参照。UN表の再利用条件は要確認としてsourceに記録し、独自の権利許諾を付与しない。

## 証拠の保存とオフライン再生成

`raw/`へ取得原本、各requestのreceipt、M49抽出JSON、`collection-receipt.json`を保存する。全体receiptは要求年、設定SHA、除外したWBコード、未結合図形、地図の不足、取得件数を持つ。`evidence/validation.json`と`TEMPLATE_REFERENCE.json`は検証結果とテンプレート参照commit/dirty状態を分けて記録する。

```sh
node scripts/create-world.mjs --source-dir generated/world/raw --out generated/world-replay
```

外部取得なしで、設定SHA・要求URL・SHA・bytes・元のUTC取得日時を照合して再生成する。年指定を省略すると元receiptの要求年を使う。原本がない・改変された場合や設定が異なる場合は停止し、ネット取得で密かに補わない。元の収集で失敗したrequestはその失敗を再現する。既存出力は変更しない。生成器の版が変わればHTML等は変わるため、正確なコード再現には`TEMPLATE_REFERENCE.json`の参照とdirty状態も確認する。

国版への接続は、収集済み国版のISO3と相対URLを確認して`analysis.country_sites`へ後から設定する。国内行政階層・国勢調査・計画資料・法的承認状態の確認は各国アダプターの作業であり、世界系列から補間しない。AreaDataの派生広域試作で集計を明示的に採用する場合も、この世界収集datasetは変更せず、別datasetの`analysis.aggregation`に完全範囲・方法・期間方針を記録する。国勢調査の異なる年を使う集計は[国勢調査系列契約](CENSUS_SERIES_CONTRACT.md)に従い、同一年の国際系列とは分ける。

## アメリカ大陸版

世界datasetのUN M49 Americas（019）だけを切り出し、57のcountry/areaと3つの探索入口を持つ別成果物を作る。UN WPP 2024原本からは行が確認できる55 country/areaだけを取り込み、BVTとSGSは欠測として残す。検証済みの中米7か国成果を指定すると、その7か国に限って国勢調査と国内階層を再利用する。残りの国・地域へCensus値をコピーせず、全大陸のCensus合計も完全被覆になるまで出さない。

```sh
node scripts/create-americas.mjs \
  --source-dir generated/world/raw \
  --central-america-project generated/central-america \
  --central-america-raw acquired/central-america-census \
  --un-wpp-file acquired/WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx \
  --un-population-data data/international/un-wpp2024-americas-population.json \
  --out generated/americas
node scripts/serve.mjs --dir generated/americas/site --port 4173
node scripts/verify-regional-delivery.mjs --project generated/americas
```

`--central-america-raw`と`--un-wpp-file`は、採用した正規化値から元payloadと取得receiptまで候補内で追跡するための入力である。原本は公開サイトへ入れず、案件の`raw/`と`evidence/`へ複製し、source recordへ相対`raw_path`、SHA-256、receiptを記録する。再配布条件が未確認の原本はGitや公開ディレクトリへ置かない。

生成時に地域版の受入票、納品状態、独立監査票を`evidence/`へ置く。制作担当が実画面と出力を確認して受入票を閉じた後、別タスクが修正せずに監査する。`ACCEPT`前は次の公開ゲートが失敗する。

```sh
node scripts/verify-regional-delivery.mjs --project generated/americas --require-publishable
```

[地域版受入条件](../templates/REGIONAL_ACCEPTANCE.md)は分類・集計・国別値の分離・階層リセット・3言語・CSVを対象にする。[地域版独立監査](../templates/REGIONAL_INDEPENDENT_AUDIT.md)はKitの制作後監査と同様に、テストや自己申告ではなく原資料・dataset・実画面・取得物を別担当が追跡する。大陸・広域は法定計画主体ではないため、国別Wordや共通計画様式を受取条件にしない。

世界・大陸・広域のカバー範囲を拡張し、公開公式sourceの確認結果をcommitした後は、`npm run export:kit-source-feedback`でKit向けbundleを更新する。bundleに入れるのは国別に特定できる公式・国際機関sourceの所在と再利用注意だけで、集計値、観測値、raw原本、資格情報を含めない。bundle commitとpathをKit担当へ通知し、Kit側のdry-run後に取り込む。

## 実取得の検証記録

2026-09-13 10:24 UTCの取得版は、UN 248 country/area、276選択地域、Worldを含む216のWB economy対応、4分野3,544公表値。原本11応答を保存し、図形は169国・25広域、79 country/areaは未結合。統計の実測年は人口・Internetが2021–2025、Health・Electricityが2021–2024。2026の値を推定補完していない。

初回とオフライン再生成のdatasetはバイト一致し、SHA-256は`fa94e6b1d817eff18f0415d3865c984c7efea58bd574a04468eb8d9e0628b4b5`。検証は0 errors、国別計画資料未収集のwarning。小さな取得URL・SHA・時点・件数の[receipt](../config/world-verification-receipt.json)を保存した。これはこの取得版の収集検証であり、将来の値・UI受入完了を示さない。

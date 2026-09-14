# v0.4.1 共通source・国別所在台帳の検証

## 対象

- 基点commit：`3cebaa33f356482dde873feec711ed9c0a574258`
- 実施日：2026-09-14
- 環境：Windows、Node.js
- 変更範囲：国際・複数国の地域別source台帳、国別の国勢調査・計画制度等の所在台帳、国別source preflight生成、Good Governmentのサービス・保存方針
- 実行テンプレート：0.4.1。dataset schema 0.2と共通UX 0.4 candidateは変更していない。

## 実装した範囲

| 対象 | 結果 |
|---|---|
| 共通source台帳 | 10 source。provider、テーマ、地理、coverage、availability確認方法、access、cache、再配布確認、注意点を必須化 |
| 国別所在台帳 | 21か国。既存ラテンアメリカ20か国を重複保存せず読み込み、ウガンダを追加 |
| 国別初期生成 | `evidence/SOURCE_PREFLIGHT.json`と`.md`を自動作成 |
| 調査済み国 | 国勢調査・計画法等の所在と証拠段階を提示。ラテンアメリカ調査は`desk_research_location`から自動昇格しない |
| 未調査国 | `source_locations_not_pre_researched`を明示し、国別5区分の所在調査を最初の作業に設定 |
| 共通候補 | 対象国でのavailabilityを常に`availability_not_checked_for_country`から開始 |
| CLI | ISO3／登録国名と任意themeから調査開始票を表示 |
| 引継ぎ | 生成案件へ台帳運用・保存方針とサービス構成を同梱 |

## 公式仕様・所在の確認

2026-09-14に各providerの公開ページを確認した。これは個別country extractの取得試験ではない。

| Source | 確認した内容 |
|---|---|
| [HDX HAPI metadata](https://hdx-hapi.readthedocs.io/en/latest/data_usage_guides/metadata/) | country、admin1、admin2、data availability、元HDX resourceへの追跡 |
| [UNHCR Refugee Statistics API](https://api.unhcr.org/docs/refugee-statistics.html) | 難民・避難民等のAPIとdemographics/locationの存在 |
| [IOM DTM API](https://dtm.iom.int/data-and-analysis/dtm-api) | country、Admin 1、Admin 2の非機微な集計、v3のsubscription key |
| [IPC Public API](https://docs.api.ipcinfo.org/) | analysis、area、point、人口・GeoJSONの公開／developer endpoint |
| [WorldPop API](https://www.worldpop.org/sdi/introapi/) | productとISO3による人口等の格子データ探索 |
| [EC JRC GHSL](https://ghsl.jrc.ec.europa.eu/download.php) | 人口・建築域・settlementの世界格子product |
| [UN SALB](https://salb.un.org/en/data) | Member State別の機関、履歴、ADM1・ADM2データ有無と期間 |
| [FAO WaPOR](https://www.fao.org/in-action/remote-sensing-for-water-productivity/wapor-data-access/en) | global／regional解像度とAPI・download経路 |
| [UNICEF MICS](https://mics.unicef.org/surveys) | 国・round別の調査、報告・datasetの所在 |
| [DHS Program](https://dhsprogram.com/data/available-datasets.cfm) | 国・survey別の報告、aggregate tool、登録データの所在 |

ウガンダは[UBOS NPHC 2024](https://statistics.ubos.org/nphc/)でsubcounty Excel、sub-regional profile、microdata catalogue等の所在、[NPA地方計画ページ](https://npa.go.ug/local-government-development-plans/)でdistrict・city・municipalityの計画とcode、[Local Governments Act](https://ulii.org/en/akn/ug/act/1997/5/eng%402023-12-31)でdistrict planning authorityとlower local-government planの統合を確認した。UN SALBのUgandaページは2026-09-14時点でdownload可能なgeospatial datasetなしと記録し、他の公式境界探索を止める根拠にはしていない。

## 自動検査

- `npm run check`：38 JavaScript moduleとJSON templateの構文確認に合格。
- `npm test`：119件合格、失敗・skip 0。新規5件は台帳統合、ウガンダの計画／内部分析粒度、ラテンアメリカ調査の証拠段階、未調査国、theme絞込を検査。
- `npm run sources:plan -- --country DOM --theme refugees --format json`：国別sourceとUNHCR候補を分けて出力し、共通候補を未確認状態に保持。
- country fixtureによる`create-country`：SOURCE_PREFLIGHT 2形式と引継ぎ資料を生成し、acquired件数0を保持。
- `git diff --check`：合格。

## 未実施・限界

- 共通10 sourceの全データ一括取得、全対象国のcoverage照会、国別アダプター、地理照合、Atlasへの指標採用は未実施。
- 21か国以外の国勢調査・計画制度・境界の事前所在調査は未実施。
- 大容量原本・ラスタ用のData Commons object storage、Data Portal、公開API、サブドメイン配備は設計のみで未実装。
- MICS、DHS等の制限付き個票・空間データは取得・保存・再配布していない。
- 今回はデータ台帳と生成工程の変更で、公開画面の操作・表示、dataset schema、DDPT本体、ウガンダ本番サイトは変更していない。
- リポジトリはPrivateのままで、Public化とOSS licenseの選定・付与は未実施。

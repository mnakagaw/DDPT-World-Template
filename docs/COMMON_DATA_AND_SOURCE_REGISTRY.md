# 共通データと国別情報源の事前台帳

国名だけを受け取ったAIが毎回ゼロから探索しないよう、二つの台帳をテンプレートで管理する。

- `config/country-source-registry.json`：国勢調査、計画法、計画手引き、既存計画、公式地域コード・境界の所在。ラテンアメリカ20か国の既存調査を読み込み、ウガンダの確認先を追加している。
- `config/common-subnational-sources.json`：複数国で再利用できる国際機関・国際事業の地域別、地点別、格子別データ源。
- `config/external-source-registries.json`：Public [Census Dashboard Kit](https://github.com/mnakagaw/Census-Dashboard-Kit) v1.8.1の世界250国・地域source preflight、JICA対象142か国preflight、4参照国台帳を、上流commit・件数・SHA-256付きで参照する。
- `data/census/world-census-listings-v1.8.1.json`：固定した世界preflightからISO3で正規化したUNSD Census所在台帳。国別値ではなく、調査開始時の所在情報である。

台帳にURLがあることは、その国の数値を取得済み、地理を照合済み、DDPTへ採用済みという意味ではない。次の段階を順に記録する。

1. `catalogued`：資料やAPIの所在と仕様を確認した。
2. `country_availability_checked`：対象国・テーマ・年・粒度で利用可能か確認した。
3. `data_acquired`：許可された原本を取得し、要求・応答・取得日時・hashを保存した。
4. `geography_matched`：統計コード、地域型、境界版、有効期間を照合した。
5. `indicator_accepted`：定義、単位、母集団、分子分母、期間と採用理由を確定した。

UNSD Census所在台帳では、`latest_un_census_listing`（UNSDが掲載する最新の実施済み調査）と`latest_un_census_linked_listing`（そのうちUNSDリンクがある最新調査）を分ける。各掲載には `link_status`、`acquisition_status`、`content_verification_status`、`adoption_status` を別々に持たせる。リンクの存在を資料取得、本文確認、数値採用へ自動昇格しない。

アルジェリアでは、最新掲載は2020 round／2022年9月25日でUNSDリンクなし、リンク付き最新掲載は2010 round／2008年4月16～30日である。AreaDataの国内Census系列には確認済み2008年データだけを使い、2022年掲載を2022年データへ読み替えない。2022年等の国際推計は別系列として保持する。

## 国別作成で自動生成するもの

`create-country.mjs`はWDI全国値と参照境界を収集した後、対象国について次を生成する。

- `evidence/SOURCE_PREFLIGHT.json`：AIや処理プログラムが読む構造化された調査開始票。
- `evidence/SOURCE_PREFLIGHT.md`：人が確認できる国別情報源と共通候補の一覧。

既存の所在調査がある国では、その国の国勢調査・計画制度・境界の候補を先に示す。未調査国では`source_locations_not_pre_researched`を明示し、国別の所在調査を最初の作業にする。どちらの場合も、リンクの有効性、新版、法令改正、機関改編、データ内容を案件時点で再確認する。

サイトを生成せずに台帳を確認する場合は次を使う。

```sh
npm run sources:plan -- --country UGA
npm run sources:plan -- --country DOM --theme refugees
npm run sources:plan -- --country JPN --format json
```

未調査国はISO 3166 alpha-3で指定する。調査済み国は台帳にある国名でも検索できる。

## 計画単位と内部分析単位

所在調査では、法定の計画策定単位と、その計画のために内部を診断する統計単位を別に記録する。ウガンダでDistrictの計画を作る場合、District全体の値に加えて、県内の格差や優先地域を見るSubcounty／Division／Town Council等の統計と境界が必要になる。下位資料があるだけで、その単位を法定計画主体に変更しない。

## 初期登録した共通候補

| 分野 | 主な候補 | 地理 |
|---|---|---|
| 人道・人口・貧困・施設等 | OCHA HDX HAPI | 国、ADM1、ADM2（国・分野別に変動） |
| 難民・避難民・無国籍 | UNHCR Refugee Data Finder | 国、報告地点・地域 |
| 国内避難・帰還・移動 | IOM DTM | 国、ADM1、ADM2 |
| 食料不安・栄養 | IPC-CH | 分析区域、地点、GeoJSON |
| 子ども・女性・WASH等 | UNICEF MICS | 調査報告領域、許可された地理情報 |
| 保健・人口・栄養 | DHS Program | 調査地域、許可された地理情報 |
| 人口分布 | WorldPop | 格子、指定ポリゴン |
| 人口・建築域・都市 | EC JRC GHSL | 格子、都市域、指定ポリゴン |
| 行政境界・履歴 | UN SALB | ADM1、ADM2（提供国・期間のみ） |
| 農業・水生産性 | FAO WaPOR | 格子、流域、灌漑地区等 |

正確な対象範囲、アクセス、保存、再配布、注意事項はJSON台帳を正とする。共通候補は国勢調査の穴を同じ意味の数字で埋めるものではない。国勢調査、標本調査、人道調査、登録統計、モデル推計、リモートセンシングを別の`source`と測定方法で保持する。

## 保存と再利用

Gitには台帳、アダプター、スキーマ、取得手順、小規模で再配布可能な検証資料を保存する。大きな原本・ラスタ・取得応答は、将来のData Commonsの版管理されたオブジェクト保管へ置く。各原本にはsource ID、取得要求、最終URL、取得日時、hash、利用条件、上流版を付ける。

正規化済みデータは原本を上書きせず、処理版、入力hash、地域対応、指標定義を付けて別に保存する。Atlasへは対象国・対象機能で採用した派生bundleだけを渡す。更新失敗で最後の正常bundleを置き換えない。

再配布できない個票・空間ファイルはGitや公開オブジェクト保管へ複製しない。許可されたメタデータ、取得手順、版、必要な申請・認証と、生成可能な派生物の条件を残す。APIキーや認証情報は台帳、ログ、成果物へ保存しない。

## Census Dashboard Kitへのsource feedback

国別または地域別のカバー範囲を広げ、公開公式sourceの確認結果をcommitした後、次を実行する。

```sh
npm run export:kit-source-feedback
```

`evidence/KIT_SOURCE_FEEDBACK.json`はKit v1.9.0のschema 1.0に適合し、生成時の`origin_commit`に存在する証拠pathだけを含む。同一国・role・URLは一件へまとめ、公開HTTP(S)の公式機関・国際機関source以外、未確認candidate、観測値、raw原本、資格情報、秘密query、ローカルURLを拒否する。`origin_commit`は証拠とexporterを先にcommitしたHEADとし、bundleは次のcommitで保存する。

bundle commitと絶対pathをKit担当へ通知し、Kit側で同じbundleをdry-runしてからimportする。Kitで取り込んだ版は、そのKit commitを`config/external-source-registries.json`へ再固定する。AreaDataでの高い証拠段階はKit側の取得・採用状態を自動的に引き継がない。

## 国を追加する手順

1. 国勢調査の公式入口、表・API・報告書、調査票・辞書、公開粒度を確認する。
2. 計画法・自治体法・州法、現行改正、所管、作成・協議・承認主体、計画手引き・様式、公開済み計画を確認する。
3. 計画策定単位、その上位、および内部分析に必要な下位単位の公式コードと境界候補を確認する。
4. 国別sourceをregistryへ追加し、`checked_at`と証拠段階を記録する。
5. 共通候補の対象国availabilityを照会し、採用・非採用と理由を案件側の台帳へ保存する。
6. 実取得と変換を再実行できるアダプターにし、代表地域で画面・表・出力まで照合する。
7. 確認した公開公式sourceとcommit済み証拠をfeedback bundleへ反映し、Kit担当へbundle commitとpathを通知する。

現在の事前所在調査は22か国（ラテンアメリカ20か国、ウガンダ、ベリーズ）。ベリーズは国勢調査所在のみ確認済みで、計画制度は未調査として保持する。その他の国も共通候補は抽出できるが、国勢調査・計画制度の所在は未調査として出力される。全世界の所在調査と全sourceの収集アダプター完成は、この版の完了範囲ではない。

別途、Public Kitには世界250国・地域の国別統計局・UNSD Census所在台帳と、JICA対象142か国の発見用アドレスがある。JICA対象142件は、UNSD、FAOLEX、JICA／外務省、geoBoundaries、SALB／HDX、WDI等から探索を始めるためのpreflightである。本リポジトリの22か国の詳細な所在調査件数へ加算せず、国別案件で最新版、原本、本文、地域粒度、地理対応を再確認する。固定参照版とhashは `config/external-source-registries.json` を正とする。

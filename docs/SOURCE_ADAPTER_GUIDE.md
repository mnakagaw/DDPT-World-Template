# 国別の公式資料を追加する手順

目的は、初期収集に現地の地方統計・地域対応・計画資料を追加し、次の更新でも再現できるようにすること。World Bank全国値とgeoBoundaries参照境界は出発点であり、地方資料の調査を代替しない。

ランタイム契約は[IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md)、計画資料の任意拡張は[PLANNING_DATA_CONTRACT.md](PLANNING_DATA_CONTRACT.md)を正とし、変更前に`lib/collect.mjs`、`lib/validate.mjs`、`lib/generate.mjs`と対象テストを読む。以下の補助台帳やアダプター配置は案件側の作業規約で、既に実装された自動plugin読込を意味しない。

## 1. 取得前に資料を特定する

1. 公式機関のページから資料・APIを辿り、発行機関、資料名、観測期間、公表日、地理粒度、利用条件、ファイル形式を確認する。
2. 国内公式値と国際データを比べる場合は、指標定義、単位、母集団、期間、境界版を照合する。同条件なら国内の一次資料を優先し、差のある値を同じ系列へ無言で混ぜない。
3. 元の国・地域コードの体系と根拠を確認する。URLの名前や地図の見た目だけで行政単位や公式性を判定しない。
4. 公開範囲内で必要な原本を`raw/`へ保存し、取得時刻と実バイト列のSHA-256を記録する。ページURLと実ダウンロードURLを分けて台帳へ残す。
5. HTMLのエラー画面、ログイン画面、ファイル以外の応答を成功原本として受け入れない。取得失敗・要認証・未確認を区別する。

APIのページ分割・取得制限を確認し、最初のページだけを全件と報告しない。公式Excel・PDFでは該当スキルと利用可能な同梱ツールを使い、表の見出し・単位・注記・ページを一緒に確認する。Word COMを使わない。新しい有料契約、秘密情報の取得、アクセス制御の回避を前提にしない。

## 2. 案件側に取得と変換を実装する

```text
adapters/<source-id>.mjs       公開API等の取得・正規化
scripts/update-data.mjs       取得、既存データとの統合、検証、保存
raw/<source-id>/<file>        取得した原本
evidence/SOURCES.md           資料・抽出位置・変換・実行コマンド
evidence/CODE_CROSSWALK.csv    コード体系と境界の対応根拠
evidence/GAPS.md              未取得・未結合・次の行動
data/dashboard.json          検証して表示するdataset
```

これは推奨配置。既存の案件規則があれば同じ責務を持つ場所を使う。PDF・Excel用の変換が別言語や同梱ツールに依存する場合は、その実行環境と正確な再実行コマンドを記録する。テンプレートが外部npm依存なしで動くことと、追加資料の抽出環境を区別する。

アダプターには取得と変換の境界を設け、保存済み原本から変換だけを再実行できるようにする。手で画面を見て採録した場合も、抽出位置と照合記録を残し、自動取得済みとは表現しない。再取得失敗時は最後に検証したデータを保持して失敗を記録する。

## 3. dataset 0.2のフィールドを使う

トップレベル名は次のとおり。`country-profile.json`の設計用フィールド一覧を、そのままランタイムdatasetとして読み込ませない。

| フィールド | 必要な対応 |
|---|---|
| `schema_version` | 文字列`"0.2"` |
| `generated_at` | このdatasetの生成日時。観測年や公表日に代用しない |
| `country` | `id`, `iso2`, `name`, `requested_name`, `locale`, `national_territory_id`, `geography_note` |
| `territories` | 各行に`id`, `name`, `level`, `type`, `parent_id`, `official_code`, `code_system`, `boundary_version` |
| `indicators` | 各行に`id`, `name`, `theme`, `unit`, `definition`, `source_id`, `aggregation`, `measurement_method` |
| `observations` | 各行に`territory_id`, `indicator_id`, `period`, `value`, `status`, `source_id` |
| `sources` | 各行に`id`, `name`, `url`, `publisher`, `retrieved_at`, `reference_period`, `status`, `sha256`, `raw_path`, `license`, `note` |
| `boundaries` | GeoJSON `FeatureCollection`。各Featureの`properties.territory_id`は`territories[].id`を参照 |
| `documents` | 従来の主要項目は`id`, `territory_id`, `title`, `url`, `period`, `kind`, `availability`, `official_status`, `source_id`。`category`・`target_period`等の任意拡張と項目間の条件は計画資料データ契約を参照 |
| `planning` | 任意。国別の制度説明・資料区分・出力・地図・関連リンク・更新状態。正確な属性と既定動作は計画資料データ契約を参照 |
| `gaps` | 各行に`category`, `status`, `detail`, `next_action`。地域・資料に固有なら任意の`territory_id`・`source_id`で範囲を明示 |
| `collection` | `status`, `adapters`, `notes`。利用したアダプターと収集範囲を説明 |

IDは資料・指標・地域を区別できる安定した文字列を使う。新しい公式指標を既存WDI IDへ割り当てる場合は、定義と表示上の出典参照が一致するかコードで確認する。確認できなければ別ID・別系列を作る。

`value`は検証した数値または`null`とし、欠測を0へ変えない。数値状態の意味は[国別データ規則](03_COUNTRY_AND_DATA.md)を参照する。現実装のschema 0.2で使う値は次のとおり。実装更新時はvalidatorとrendererも確認する。

| 項目 | schema 0.2の許容値 |
|---|---|
| `observations[].status` | `observed / missing / not_applicable / suppressed`。`observed`は有限数値、その他は`value: null` |
| `sources[].status` | `ready / partial / failed / unavailable / not_collected` |
| `indicators[].aggregation` | `none / sum / weighted_rate / official_only` |
| `collection.status` | `complete / partial / failed`。成功した取得先の数だけで`complete`を選ばない |

意味を増やす必要がある場合は検証・表示・出力を一緒に実装し、未対応値を黙って渡さない。URLは現validatorがHTTPSを要求するため、実在・到達を確認したURLを使う。資料がHTTPのみなら文字列だけをHTTPSへ書き換えず、取得方針と契約の対応を確認する。

観測行が参照する地域・指標・出典は必ず存在させる。`indicators[].source_id`と`observations[].source_id`が異なる場合は、画面・出力が各値の実出典を誤表示しないことを確認する。

原本が保存済みなら`raw_path`は案件ルート基準の相対パス、`sha256`はそのファイルのhashとする。存在しない原本や未取得資料へ架空のhashを付けない。既存collectorのページ別`raw_files`と取得receiptも保持し、代表ファイル1件のhashで全ページ取得を証明したことにしない。抽出したPDFページ、Excelシート・範囲、APIクエリ、コード対応根拠、観測単位の細分類・追加の版情報は`evidence/SOURCES.md`等で追跡する。追加属性が必要なら、0.2で自動表示・保存されると想定せず契約を拡張して検証する。

文書の`availability: "link_verified"`はリンクを確認した状態で、本文取得・全文抽出・公式承認とは別である。`official_status`は公式の根拠を確認するまで`"unverified"`とする。旧形式の状態文字列が残る場合も、確認済みに格上げしない。

### 計画・予算・実施・評価資料の追加

1. ４区分は資料探索の観点として調べる。対象階層、発行・承認主体、正式な資料名、計画周期、会計年度、更新頻度、公開・認証・利用条件をsourceごとに記録する。国際的に同じ章立て・周期・評価尺度があると仮定しない。
2. 優先する公開資料の本文を実際に取得する。APIはクエリとページ分割、Excelはシート・セル範囲、PDFは頁・表・注記、HTMLは見出し・表を記録し、保存原本から再抽出できるアダプターを作る。OCRや手採録は原図と照合するまで内容確認済みにしない。
3. 以下の地域結合手順に加え、`documents[].territory_match`へ照合した内部`territory_id`、国・地域型・コード体系・公式コード・境界版・照合方法・資料箇所・確認日を保存する。照合した内部IDは文書の`territory_id`と完全一致させ、公式コードが双方nullでも別地域への割当を許さない。この内部IDは公式コードの代用ではない。公式コードが未確認なら新しいコードを作らない。旧計画は適合する当時の地域台帳と期間を使い、同名の現地域へ強制結合しない。
4. `target_period`に原資料のラベルと種類を保存する。会計年度、四半期、複数年計画、基準日時点を統計の単年へ変換しない。旧`period`を併記する場合は同じラベルにする。範囲日付を持つ場合は順序と地域の有効期間を検証する。
5. 取得進捗は`availability`の１軸で記録する。`body_acquired / content_extracted / content_verified`には参照する`sources`の実原本`raw_path`と`sha256`が必要。本文を確認してから、出典箇所付き`content`や`findings`を作る。公式状態を採用する根拠は別の`official_evidence`へ置く。本文・所見・公式根拠を追加する文書は地域同定根拠も必須になる。
6. `findings`の予算・歳入・歳出・実施結果・公式評価・予算執行・計画達成を混同しない。定義・対象・資料期間・根拠箇所を付け、数値なら単位と状態も必要とする。得点は尺度を確認し、欠測はnull、実測ゼロは0を保つ。文書をまたぐ合計や比率を自動で作らない。
7. 調査した制度と採用判断を設計profileへ記録し、実際に提供する設定だけ`dataset.planning`へ変換する。`sections`の外の資料も到達可能にし、４区分を必須ページ化しない。地図を公式状態表示にする場合は資料区分・正確な資料期間・状態定義を設定し、欠落・矛盾のある証拠を未確認とする。既存の投資・財政から同じ資料IDを参照できる経路と必要な出力だけを採用する。

フィールドの条件・許容値は[計画資料データ契約](PLANNING_DATA_CONTRACT.md)で確認する。検証器が通っただけでは、原本の内容・公式性・地域同定が正しいことの証明にはならない。取得不能時は`gaps`に地域・source・試行結果・次の操作を残し、取得済みの原資料や根拠付き整理欄を使える代替を仕上げる。

## 4. 地域結合の前にコードと出典を検証する

1. 元統計のコード列、桁、先頭ゼロ、地域型、親地域、対象年を原表と説明資料で確認する。コードは数値化して先頭ゼロを落とさない。
2. 地図側の発行元、対象階層、境界版、ID体系を確認する。geoBoundariesのshapeIDを`official_code`へ入れず、`code_system`にはproviderの体系名を記す。
3. 公式コードが確認できた地域だけ`official_code`に格納する。未照合なら`null`のまま、内部`id`とprovider IDで区別する。世界銀行のeconomy codeも国内行政コードとは別に扱う。
4. 対応表に双方のID・コード体系・境界版・出典・判定を記録する。名前で候補を探すことは可能だが、名前の類似度だけで確定結合しない。
5. 同名地域、独立市、分割・統合、統計区分と行政区分の違いを確認する。多対多は、公式の対応・再集計根拠がない限り値を割り振らない。
6. 結合数、未結合数、重複候補、範囲外、親不一致を報告する。結合できない地方値も、根拠付き一覧として利用できるか検討する。

全国の観測行は`country.national_territory_id`のみへ置く。全国値の人口按分、古い境界の無根拠補間、未配属事業の架空地域への割当てでデータを埋めない。

`territories[].parent_id`は検証した地理的所属を表す。市から親を選び直した際、画面は親IDの観測を使用する。地域台帳を追加しただけで親の値を自動生成したり、最後に見た子の値を親へ表示したりしない。親の値は公式値、または定義・期間・境界版・重複しない完全な所属集合と正確な分子分母を確認した再集計値として登録する。割合の単純平均、丸め率からの分母逆算はしない。

上位集計の分母が初期Excelにない場合も、国勢調査PDF等の取得可能な一次資料を確認する。元の率と新たな分子分母に差があれば、上書きで隠さず出典頁・範囲・差を記録する。全国公式系列と地方合計系列は丸め値が一致しても同一化しない。

## 5. 統合と検証を再現可能にする

1. 既存`data/dashboard.json`を読み、追加原本を変換した候補版を別に作る。実行のたびに同じ観測行を追加し続けない。
2. `territory_id + indicator_id + period`等、rendererが実際に一意とみなすキーをコードで確認する。性別・年齢・単位・出典違いを重複として上書きしない。現契約で区別できない細分類は別指標か契約拡張で扱う。
3. `validateDataset(dataset)`を呼び、`errors`は保存・生成前に解消する。`warnings`は影響と処置を記録する。件数、代表値、地域総数、分子分母、単位を原表と別途照合する。
4. 検証済み候補だけを`data/dashboard.json`へ反映する。原本・既存版・変換コマンドから復元できる状態を残す。
5. 次のコマンドで再生成し、実データが画面と取得物へ反映されたことを確認する。

```sh
node <template>/scripts/build-country.mjs --project <country-project>
node <template>/scripts/serve.mjs --dir <country-project>/site --port 4173
```

`<template>`と`<country-project>`は実際のパスへ置き換える。`generateSite({dataset, outDir})`を直接使う場合も、先に同じデータ検証を行う。生成器へファイルを置くだけで読まれる自動アダプター機構があるとは想定しない。

資料更新では、前版との文書ID・地域対応・期間・件数・代表的な本文／数値・公式根拠の差も照合する。取得不能・抽出失敗・検証不合格の候補は正常版へ昇格しない。最後の正常データを保持し、元資料更新の停止は`planning.update`の`status: "stopped"`、確認日時、最終成功日時、理由で説明する。失敗した候補の証拠と再試行コマンドを`HANDOFF.md`へ残す。サイト生成・配備の失敗は別の記録で扱い、データ収集が成功したと偽らない。

## 6. 収集を止める前の確認

- 調査した公式資料、採用・不採用の理由、実際に取得した範囲が台帳にある。
- 取得可能な優先地方資料を組み込み、コード・期間・単位・境界の照合がある。
- `gaps`と`evidence/GAPS.md`が対応し、`next_action`が資料URL・取得方法・確認事項まで具体的である。
- `collection.status`は実際の範囲を表す。原本取得だけや全国初期データだけの状態を全分野収集完了に変えない。
- 地域操作と採用出力を実際に検証し、未検証・アクセス制約・残る国別作業を`HANDOFF.md`へ残している。

テンプレートに追加した取得処理が全ての国で通用するとは宣言しない。次回更新時は同じ原本による再現と、新しい資料の列・コード・定義・境界変更の双方を確認する。

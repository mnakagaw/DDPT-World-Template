# 実行テンプレート0.5の実装契約

ユーザー指示に基づき、Private GitHubを参照した国名からの収集・サイト作成に加え、世界→大陸→広域→国の探索入口と、地域診断の各指標の内部比較・診断出力を実装する。上部で範囲を選ぶと直ちに全体を診断し、国から国内行政階層へは別の国別datasetを接続する。世界共通UX v1.0の採用判定とは別に扱う。

## 共通インターフェース（0.5実装、データschema 0.2）

実行パッケージ0.5.0でもデータschemaは0.2を維持する。複数階層の所属は既存の`territories[].parent_id`から読み、国名・階層数を固定しない。地域診断・計画資料の上位再選択は、同じ所属先を選び直した場合も下位の選択を解除し、最後に明示選択した親IDを表示・URL・出力で共有する。指標・年は保持する。親自身の観測を最優先し、任意の集計契約がない指標は従来どおり観測または欠測を使う。同名の地域は選択肢に型・コード等を付ける。

上部の位置図・階層選択・基本情報と、下部の各指標の内部比較地図・全件表を分離する。内部比較の地図・行への注目は同じ指標内だけで対応させ、上部の対象・見出し・他指標・資料・URL・出力先を変えない。地域を変更すると全指標の比較対象も更新する。取得済みの推移、親の公式値、子の分布は別の意味で表示する。

### 任意の分析拡張と世界・国内の接続

`dataset.analysis`は任意。省略した旧datasetでは登録済みの直下地域を比較候補とし、従来のURL・統計CSV・計画資料の採用出力を保つ。世界や深い階層、明示した比較集合を扱う場合は次を使う。

| 項目 | 契約 |
|---|---|
| `analysis.kind` | `country`、`regional`または`world`。worldは`country.id`・`national_territory_id`とも`WLD`、rootは`level:national/type:exploration_scope/parent_id:null` |
| `analysis.terminal_territory_ids` | 内部比較を細分しない地域ID。国別に確認した基礎自治体等を設定し、ADM番号や子が存在することだけで計画主体を推定しない。世界datasetは国・地域で停止する |
| `analysis.comparisons[]` | 既知の`parent_id`、下位の重複しない`member_ids`、`label`、`membership_note`、取得済みの分類根拠`source_ids`。親子が重複する母集団は拒否。任意`color_scale`は`within_selection`または`fixed`、固定は昇順の4閾値 |
| `territories[].country_id` | 世界内の`type:country`にはISO3を必須とする。M49の国・地域分類は主権国・法定計画主体の認定ではない |
| `analysis.country_sites[]` | 接続元`territory_id`、接続元のISO3と一致する`country_id`、安全なHTTPSまたは`./`子パスの`url`。任意`target_territory_id`は省略時その国ID。`indicator_map`は意味を確認した指標対応だけを明示する |
| 観測の意味 | 任意の`definition_id/definition/unit/population/method/measurement_method/boundary_version`で指標の既定と異なる意味を保持。異定義・異母集団・異単位・異方法・境界版差は元値と理由を残し、共通の比較色・数値比較から除く |
| `analysis.aggregation` | 任意。`policy:exact_then_complete_cover`と指標別ruleを指定した場合だけ上位集計する。親自身の観測を優先し、完全・非重複・根拠付き被覆だけを計算する。不完全時は全体値nullと監査小計・不足IDを出す |
| `analysis.aggregation.coverage_sets[]` | 任意。比較表が国単位でも、集計には直接の広域区分を使う場合、指標・親ID・**全直下地域**・所属出典を明示する。比較対象の粒度は変えない。親の公式観測を優先し、各子の公式値または完全被覆計算値で全域を埋めた場合だけ合計する |

国際指標と国内統計は同じ名称・IDだけで対応付けない。国版への接続は別datasetの国・対象IDと明示した指標対応を確認し、対応がなければ国版の既定指標と未対応の説明を使う。統計年を保つ場合も、その年の欠測を別年で補わない。資料独自の計画期間・会計年度を統計年に置き換えない。

全国sourceは対応する国の全体値だけに使う。世界収集の`geographic_level:world_country_series`は公式WLDまたは国の公表値として保存し、大陸・国内地域の直接観測へ転用しない。地域台帳の全件を比較分母とし、欠測・0・非該当・秘匿・比較不可を分ける。計算値は別の`analysis.aggregation`規則で作り、出典公表値と区別する。率平均、不完全被覆の全体値化は行わない。

境界ID・国・型・コード・境界版の明示不一致は拒否する。Natural Earthの図形固有版は`geometry_edition`とsourceに置き、未確認の統計境界版と同一化しない。上位の位置図に使うMultiPolygonは、同じsource・版の照合済み国図形を表示専用に連結し、欠ける構成国を記録する。法定境界・数値集計の根拠にはしない。

`analysis.mjs`が比較集合・意味・境界・色を扱い、`diagnostic.mjs`が指標別内部比較と診断Markdown/HTML/全件CSVを生成する。診断出力は検索・折畳み・スクロールで隠れた行も含む選択年の全指標・内部全行・状態・意味・出典を保持する。HTMLの地図・取得済み推移図、印刷の全行を実際に確認する。

### 任意の計画拡張と互換性

`dataset.planning`、documentsの資料分類・対象期間・照合根拠・内容・所見、地域を指定したgapsを実装した。型・検証条件は[PLANNING_DATA_CONTRACT.md](PLANNING_DATA_CONTRACT.md)を正本とする。未指定の旧datasetは既定表示と従来3形式で動作し、旧URL・統計CSVの列・保存ファイル名を維持する。旧資料の自由記述状態を新たな確認済み根拠へ格上げしない。国別の作業メモ保存機能は追加も削除もしていない。

`scaffold/site/planning.mjs`は資料選択・地図状態・任意設定、`planning-view.mjs`は内容優先の表示、`model.mjs`は根拠を含むMarkdown/HTMLと採用時の資料CSVを扱う。統計期間は従来のURLで保持し、資料の計画期間・会計年度・四半期は各資料の値をそのまま表示・出力する。計画本文がなくても予算・実績・評価・公式一覧・統計を使用できる。国別区分に列挙しなかった取得資料も追加資料として残す。

### 更新失敗と復旧

`build-country.mjs`は候補データを検証し、管理下の`.build-*`で生成を終えてから`site/`を置き換える。従来siteの独自ファイルは引き継ぐ。旧siteは`.build-backups/`へ残し、自動削除しない。原本・バックアップの保存期間は国別運用で決める。symlink/junctionを含むsiteは外部ファイルへの書込みを避けるため再構築を拒否する。

失敗時は既存`site/data/dashboard.json`を維持し、`evidence/validation.json`と独立した`site/data/update-status.json`で停止を記録する。0.3以降で生成した画面はこの停止を表示する。それ以前の生成HTML自体は新しいsidecarを読まないため、表示機能の導入には旧datasetを対応版で一度正常に再生成する。正常に再構築するとbuild停止markerは解消し、`planning.update`で別途記録した情報源の停止は勝手に解消しない。無人の定期収集・再配備は追加していない。

- Node.js 22以降、ES modules、実行時の外部npm依存なし。
- `scripts/create-country.mjs --country <name-or-ISO> --out <new-directory>` が国解決・収集・検証・生成を行う。出力先既存なら上書きしない。
- 0.4.1は国別生成時に`evidence/SOURCE_PREFLIGHT.json`と`.md`を追加する。これはruntime dataset schema外の調査開始資料で、所在・取得・地理照合・採用の状態を混同しない。
- `scripts/create-world.mjs --out <new-directory>` が世界台帳・国際系列・参照図形を収集し、同じ検証器・生成器で作成する。`--start-year/--end-year`で期間、`--source-dir <previous-project/raw>`で外部取得なしの原本再実行を指定する。
- `scripts/build-country.mjs --project <directory>` は `data/dashboard.json` を検証して `site/` を再生成する。
- `scripts/serve.mjs --dir <project/site> --port 4173` は127.0.0.1のみで配信する。
- `lib/collect.mjs` が `collectCountry({country, rawDir, fetchImpl = fetch, onProgress = () => {}})` をexportし、下記datasetをreturn。補助exportは自由。
- `lib/collect-world.mjs` が `collectWorld({rawDir, fetchImpl = fetch, onProgress = () => {}, sourceDir, startYear, endYear})` をexport。設定は`config/world-membership.json`。原本再実行は設定SHA・URL・bytes・SHA・取得日時を照合し、不一致時は停止する。
- `lib/generate.mjs` が `generateSite({dataset, outDir})` をexportし、完成した `outDir/site` と引継ぎ資料を作る。dataset原本の保存はCLIが担当。
- `lib/validate.mjs` が `validateDataset(dataset)` をexportし、`{errors:[],warnings:[]}` をreturn。
- 収集障害・未提供はdataset.gapsとsource.statusへ記録する。国の特定不能と必須契約違反は失敗終了。全国統計だけの生成を地方計画完成と報告しない。

## dataset schema_version = 0.2

```json
{
  "schema_version": "0.2",
  "generated_at": "ISO datetime",
  "country": {"id":"UGA", "iso2":"UG", "name":"Uganda", "requested_name":"ウガンダ", "locale":"en", "national_territory_id":"UGA", "geography_note":"..."},
  "territories": [{"id":"UGA", "name":"Uganda", "level":"national", "type":"country", "parent_id":null, "official_code":null, "code_system":"World Bank economy code", "boundary_version":null}],
  "indicators": [{"id":"SP.POP.TOTL", "name":"Population, total", "theme":"Population", "unit":"people", "definition":"...", "source_id":"wb-SP.POP.TOTL", "aggregation":"none", "measurement_method":"source_reported"}],
  "observations": [{"territory_id":"UGA", "indicator_id":"SP.POP.TOTL", "period":"2024", "value":1, "status":"observed", "source_id":"wb-SP.POP.TOTL"}],
  "sources": [{"id":"wb-SP.POP.TOTL", "name":"World Bank WDI", "url":"https://api.worldbank.org/...", "publisher":"World Bank", "retrieved_at":"ISO datetime", "reference_period":"2000:2026", "status":"ready", "sha256":"...", "raw_path":"raw/example.json", "license":"source terms URL", "note":"..."}],
  "boundaries": {"type":"FeatureCollection", "features":[]},
  "documents": [{"id":"doc-1", "territory_id":"UGA", "title":"...", "url":"https://...", "period":"...", "kind":"published-plan", "availability":"link_verified", "official_status":"unverified", "source_id":"..."}],
  "gaps": [{"category":"subnational_statistics", "status":"not_collected", "detail":"...", "next_action":"..."}],
  "collection": {"status":"partial", "adapters":["world-bank","geoboundaries"], "notes":[]}
}
```

例の人口値1はスキーマ説明用。実収集・成果物に流用しない。boundary feature.propertiesは`territory_id`必須、geoBoundaries shapeIDは公式行政コードと表示しない。別途検証した公式コード対応表を使うまでcode_systemはproviderと明示する。国別datasetの全国値は全国のterritory_idだけに格納する。任意の`analysis`・`planning`を使わない旧schema 0.2 datasetの再生成も検証する。

## 世界入口の取得範囲

[世界アダプター](WORLD_ADAPTER.md)はUN M49の全country/area台帳と5 Region、WDIの人口・保健・電力・Internetを既定6年分、Natural Earthの固定版110m map unitsを取得する。2026-09-13の取得版は248国・地域、3,544公表値、国169＋広域25図形で、79国・地域の図形が未結合。台帳・数値・境界の取得範囲は別に記録する。

Worldは公式WLD系列を採用し、画面の国台帳の合計とは主張しない。大陸・広域に厳密同一範囲の公式系列がなければ欠測。Americasの独自Central America + CaribbeanはUN 013＋029（Mexicoを含む）を単一親としてまとめ、Northern America・South Americaと並べる。UN 419やWB/OWID集計と同一化しない。各国には元のM49全階層を残す。他大陸は元の下位区分を使い、AntarcticaはRegion未所属としてWorld直下に保持する。

取得原本・receiptは案件出力に保存し、テンプレートには設定・変換器・小さな検証receiptを置く。世界の初期収集で国別の国内統計・計画資料が揃ったとは扱わない。

## 自動収集とAIによる国別作業

実行スクリプトはWorld Bankの全国系列とgeoBoundariesの参照境界を収集する初期実装。新規案件のAIはその後、現地統計局・国勢調査・計画機関・予算・投資・計画様式を一次資料から調べ、取得・正規化した地方値と資料を契約へ追加する。公式コードの未照合、原資料不足、公開制限、データなしを明記し、取得できる範囲で動作するサイトと受入記録まで進める。

APIキー・有料エージェントの新規契約・無人のAI API呼出しを前提にしない。新しいCodex案件がこのリポジトリを参照する方式を主な入口とする。公開先未指定の国別案件はローカル生成・検証までを既定にする。

国勢調査・地方計画の方法と[ラテンアメリカ20か国調査](research/latin-america-2026/REPORT.md)は既存の研究成果として保持する。世界の国際系列の収集やレポートの存在を、20か国の国内数値アダプター実装完了と報告しない。

[42の受入シナリオ](../templates/ACCEPTANCE.md)の採用範囲を確認し、A35～A42では配置、比較母集団、世界・国内接続、基礎自治体停止、対象を変えない内部注目、数値の意味、診断出力・全表印刷、旧dataset互換を検証する。実施結果・対象版・未実施は[0.4検証記録](VALIDATION_v0.4.md)へ記録し、仕様への追記を合格やUX v1.0採用と扱わない。

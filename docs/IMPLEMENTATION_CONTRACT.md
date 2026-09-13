# 実行テンプレート0.3の実装契約

現在のユーザー指示は、Private GitHubリポジトリを新設し、新しい案件のAIが国名だけを受け取って取得可能なデータの収集・サイト作成を進められるようにすること。既存0.1の「ローカル仕様のみ」という納品範囲を今回の実装・GitHub公開まで更新する。世界共通UX v1.0の採用判定とは別に扱う。

## 共通インターフェース（0.3実装、データschema 0.2）

実行パッケージ0.3.0でもデータschemaは0.2を維持する。複数階層の所属は既存の`territories[].parent_id`から読み、国名・階層数を固定しない。地域診断・計画資料の上位再選択は下位の選択を解除し、最後に明示選択した親IDを表示・URL・出力で共有する。親の値の自動集計は行わず、登録された観測または欠測を使う。同名の地域は選択肢に型・コード等を付ける。

### 任意の計画拡張と互換性

`dataset.planning`、documentsの資料分類・対象期間・照合根拠・内容・所見、地域を指定したgapsを実装した。型・検証条件は[PLANNING_DATA_CONTRACT.md](PLANNING_DATA_CONTRACT.md)を正本とする。未指定の旧datasetは既定表示と従来3形式で動作し、旧URL・統計CSVの列・保存ファイル名を維持する。旧資料の自由記述状態を新たな確認済み根拠へ格上げしない。国別の作業メモ保存機能は追加も削除もしていない。

`scaffold/site/planning.mjs`は資料選択・地図状態・任意設定、`planning-view.mjs`は内容優先の表示、`model.mjs`は根拠を含むMarkdown/HTMLと採用時の資料CSVを扱う。統計期間は従来のURLで保持し、資料の計画期間・会計年度・四半期は各資料の値をそのまま表示・出力する。計画本文がなくても予算・実績・評価・公式一覧・統計を使用できる。国別区分に列挙しなかった取得資料も追加資料として残す。

### 更新失敗と復旧

`build-country.mjs`は候補データを検証し、管理下の`.build-*`で生成を終えてから`site/`を置き換える。従来siteの独自ファイルは引き継ぐ。旧siteは`.build-backups/`へ残し、自動削除しない。原本・バックアップの保存期間は国別運用で決める。symlink/junctionを含むsiteは外部ファイルへの書込みを避けるため再構築を拒否する。

失敗時は既存`site/data/dashboard.json`を維持し、`evidence/validation.json`と独立した`site/data/update-status.json`で停止を記録する。0.3で生成した画面はこの停止を表示する。旧版の生成HTML自体は新しいsidecarを読まないため、表示機能の導入には旧datasetを0.3で一度正常に再生成する。正常に再構築するとbuild停止markerは解消し、`planning.update`で別途記録した情報源の停止は勝手に解消しない。無人の定期収集・再配備は追加していない。

- Node.js 22以降、ES modules、実行時の外部npm依存なし。
- `scripts/create-country.mjs --country <name-or-ISO> --out <new-directory>` が国解決・収集・検証・生成を行う。出力先既存なら上書きしない。
- `scripts/build-country.mjs --project <directory>` は `data/dashboard.json` を検証して `site/` を再生成する。
- `scripts/serve.mjs --dir <project/site> --port 4173` は127.0.0.1のみで配信する。
- `lib/collect.mjs` が `collectCountry({country, rawDir, fetchImpl = fetch, onProgress = () => {}})` をexportし、下記datasetをreturn。補助exportは自由。
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

例の人口値1はスキーマ説明用。実収集・成果物に流用しない。boundary feature.propertiesは`territory_id`必須、geoBoundaries shapeIDは公式行政コードと表示しない。別途検証した公式コード対応表を使うまでcode_systemはproviderと明示する。全国値は全国のterritory_idだけに格納する。

## 自動収集とAIによる国別作業

実行スクリプトはWorld Bankの全国系列とgeoBoundariesの参照境界を収集する初期実装。新規案件のAIはその後、現地統計局・国勢調査・計画機関・予算・投資・計画様式を一次資料から調べ、取得・正規化した地方値と資料を契約へ追加する。公式コードの未照合、原資料不足、公開制限、データなしを明記し、取得できる範囲で動作するサイトと受入記録まで進める。

APIキー・有料エージェントの新規契約・無人のAI API呼出しを前提にしない。新しいCodex案件がこのリポジトリを参照する方式を主な入口とする。公開先未指定の国別案件はローカル生成・検証までを既定にする。

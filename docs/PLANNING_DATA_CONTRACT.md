# 計画・資料の国別データ契約

実行テンプレート0.3の任意拡張。`dataset.schema_version`は`0.2`のままとする。旧データの`documents`、選択地域、統計期間、既存の出力は利用できる。拡張を加えたことだけで、旧資料の内容・制度状態を確認済みに変更しない。

国による違いは、資料の分類・取得段階、計画制度の出典、対象期間、地域照合、確認した内容、採用する出力で表現する。計画・予算・実績・評価を一つの達成率へまとめない。

## 1. 任意の `dataset.planning`

すべて省略可能。未取得の制度情報を埋めるために仮の機関や法定周期を作らない。

| フィールド | 型・条件 | 意味 |
|---|---|---|
| `title`, `purpose` | 非空文字列 | ページ名と利用目的 |
| `sections` | `[{id,label,empty_message?}]` | 採用する分類の順序・表示名。`id`は後述の5分類、重複不可 |
| `system` | `{label,scope,cycle,source_ids}` | 出典で確認した国別制度。各文字列は非空、`source_ids`は1件以上の登録済み出典 |
| `outputs` | 形式IDの配列、重複不可 | `markdown`, `html`, `evidence_csv`, `documents_csv`から採用するもの |
| `map` | 後述 | 資料参照の有無、または根拠のある制度状態の表示 |
| `related_links` | `[{label,url,territory_id?}]` | 既存の投資・財政等への導線。任意地域IDは地域台帳への参照 |
| `update` | `{status,checked_at,last_success_at?,message}` | 資料更新の状態。`status`は`current`または`stopped` |

`outputs`の省略時は従来の`markdown`, `html`, `evidence_csv`を保つ。`[]`も有効であり、画面は出典の取得や現地での作業等の代替を説明する。DOCX・PDF・AI文章生成を新たな必須条件にしない。

`sections`にない分類の取得済み資料も、選択地域の「その他の取得資料」から到達可能にする。設定の変更で資料を黙って削除しない。

`related_links.url`は資格情報を含まないHTTPS URLか、サイト基点に対する`./investment/`等の相対パスとする。`../`、先頭`/`、`//`、バックスラッシュ、制御文字、スキーム付き相対文字列、符号化した親ディレクトリへの移動は禁止。内部リンクへ現在の地域・条件を渡す。安全な形式であることと、実際のリンク先が存在することは別に確認する。

`update`の日付はISO日付またはタイムゾーン付きISO日時。`last_success_at`は`checked_at`より後にしない。取得更新の停止と、サイトの公開版・配備状態は別記録とする。停止しても、以前に確認した資料とその確認日は残す。

## 2. 資料の分類と対象期間

既存`documents`の各レコードに次の任意フィールドを追加する。

| `category` | 内容 |
|---|---|
| `plan` | 開発計画・計画本体 |
| `budget` | 予算・年次計画・財政資料 |
| `implementation` | 実施結果・収支・執行の報告 |
| `evaluation` | 公表された公式評価・評価結果 |
| `reference` | 指針・様式・その他の参照資料 |

`category`省略時は既知の`kind`だけを保守的に分類する。例えば`published-plan`は`plan`、`budget`・`annual-plan`は`budget`、`execution-report`・`performance-report`は`implementation`、`evaluation`は`evaluation`。未知の`kind`は`reference`として残す。

```json
{
  "period": "2025/26",
  "target_period": {
    "label": "2025/26",
    "kind": "fiscal_year",
    "start": "2025-07-01",
    "end": "2026-06-30"
  }
}
```

例は形式説明であり、特定国の正式な会計年度を定めない。`kind`は`calendar_year`, `fiscal_year`, `quarter`, `multi_year`, `as_of`, `other`。

- `label`を文字どおり保持する。旧`period`も記録する場合、両者は完全一致させる。
- `start`・`end`は任意のISO暦日。実在する日付か、開始が終了より後でないかを検査する。
- 統計指標の選択年を資料の会計年度・計画期間へ流用しない。`2025/26`を`2025`へ変換して照合しない。
- 異なる期間の計画・予算・累計収支・評価は各自の期間を表示する。統計年が違うという理由で資料を隠さない。

## 3. 地域の厳密な照合

`territory_match`は資料と既存`territory_id`を結ぶ確認記録。

```json
{
  "territory_match": {
    "territory_id": "test-city",
    "country_id": "TST",
    "type": "city",
    "code_system": "Synthetic test register",
    "official_code": "test-city",
    "boundary_version": "test-edition-1",
    "valid_from": "2020-01-01",
    "valid_to": "2030-12-31",
    "method": "Exact source code and entity-type match",
    "source_id": "identity-register",
    "locator": "Registry row test-city",
    "checked_at": "2026-09-13T00:00:00Z"
  }
}
```

この例の国・コード・版は合成識別子。実資料へ流用しない。

- `territory_id`は必須の非空文字列で、資料の`document.territory_id`および照合した登録地域IDに完全一致する。公式コードが両地域とも`null`でも、内部IDの不一致を許さない。
- `country_id`は対象国、`type`と`code_system`は選択された地域台帳に完全一致する。
- `official_code`と`boundary_version`は明示的な文字列または`null`。`null`は地域台帳にもその値がない場合だけ認める。欠落フィールドを`null`扱いしない。
- 同名の市・県、旧版・新版を名称だけで結合しない。照合不一致は検証エラーとする。
- 地域台帳にも任意の`valid_from`・`valid_to`を記録できる。照合記録と両方に日付がある場合、一致を求める。
- 資料の対象期間と照合した地域の有効期間が両方とも開始・終了を持ち、全く重ならない場合はエラー。過去の計画には根拠のある歴史的地域レコードを使う。
- 親地域への選択変更では、子の資料や子の値を親の資料・合計へ流用しない。親資料未取得は親自身の未取得として残す。

## 4. 取得段階と制度状態は別の軸

`availability`を唯一の取得段階として使用する。別の`extraction_status`・`extraction_stage`を併設しない。

| `availability` | 確認した範囲 |
|---|---|
| `link_verified` | リンクの参照確認 |
| `body_acquired` | 本文取得 |
| `content_extracted` | 本文からの抽出 |
| `content_verified` | 出典箇所と内容の照合 |
| `not_collected` | 未取得 |
| `unavailable` | 利用不可 |
| `not_applicable` | 非該当 |
| `unverified` | 未確認 |
| `failed` | 取得失敗 |

本文取得以降の3段階は、資料の`source_id`で参照する出典に安全な相対`raw_path`と64桁の`sha256`を要求する。検証器はメタデータを検査するもので、原資料ファイルの存在・hash一致・読解の正しさを代行しない。取得工程と内容照合の記録で確かめる。

旧データの`downloaded`, `extracted`等や未知の文字列は互換のため残すが、警告を出し、確認済みの段階へ自動昇格させない。

`official_status`は国固有の制度状態文字列。`unverified`・`unknown`以外を拡張レコードで主張する場合、`official_evidence`を必須とする。旧レコードの根拠なしの状態表記は警告付きの未確認情報として残せるが、制度状態地図の色には使わない。

### 共通の根拠オブジェクト

`official_evidence`、`content.evidence`、各`findings[].evidence`は以下を持つ。

- `source_id`: 登録済み出典。根拠確認時の出典状態は`ready`または`partial`。
- `locator`: 原典ページ・表・段落・セル・決定記録等の非空文字列。
- `checked_at`: ISO日付またはタイムゾーン付きISO日時。
- `authority`: 任意。資料で確認した機関名等の非空文字列。

`failed`・`not_collected`等の出典から内容や制度状態を確認済みにしない。過去の成功資料を継続使用する場合は、その成功資料の出典レコードと確認日を保持し、最新の取得停止を`planning.update`等へ別記する。

`official_evidence`、`content`、`findings`のいずれかを持つ資料には`territory_match`が必要。リンク確認だけで承認・住民合意を作らない。

## 5. 読み取った内容と所見

`content`は次のオブジェクト。`availability: "content_verified"`が必要。

```json
{
  "summary": "原典の確認箇所に基づく要約",
  "priorities": ["確認した重点項目"],
  "objectives": ["確認した目標"],
  "evidence": {"source_id":"plan-body","locator":"PDF pages 5–7","checked_at":"2026-09-13T00:00:00Z"}
}
```

`summary`は非空文字列、`priorities`・`objectives`は任意の文字列配列。自由なAI提案をこの「資料内容」の欄へ混入しない。職員提案・住民提案・審議結果・公式決定は出典上の区別を保つ。

`findings`も`content_verified`が必要。各所見は以下を持つ。

| フィールド | 要件 |
|---|---|
| `kind` | `budget`, `revenue`, `expenditure`, `implementation_result`, `official_evaluation`, `budget_execution`, `plan_achievement` |
| `label`, `definition`, `scope` | 非空文字列。原典の定義・対象範囲を保つ |
| `period` | 第2節と同じ期間オブジェクト。資料全体と異なる集計期間も明示して保持する |
| `evidence` | 原典位置と確認日を持つ根拠 |
| `statement` | 任意の定性的説明。数値を持たない所見には必要 |
| `value`, `value_status` | 数値欄を持つ場合は状態を明示する |
| `unit` | 数値がある場合は必須 |
| `scale` | 任意の`{min,max,label}`。原典の尺度を表す |

`value_status`は`observed`, `missing`, `not_applicable`, `unverified`, `failed`。`observed`は有限の数値を要求し、**0も観測値**とする。それ以外で`value`を持つ場合は`null`。文字列の数値を暗黙に変換しない。

予算執行率、計画達成率、公式評価は異なる`kind`を保つ。率の分母・対象期間は`definition`へ記録し、率を自動計算・文書間合算しない。予算執行率が原典で100を超える場合、根拠なく100へ切り詰めない。公式評価の数値に`scale`を付す場合は有限かつ`min < max`とし、原典尺度外の値は確認を要するエラーとする。尺度や定義の意味の正しさは原典照合で確認する。

## 6. 地図・不足・出力

既定の`map.mode: "coverage"`は資料参照の有無を示す。本文の有無・抽出段階・内容確認・制度状態を、単一の完了数にしない。`category`・`period`を指定した場合は、その分類と文書期間を対象として明示する。

`official_status`地図は`category`、完全一致する文書`period`、国固有の`statuses: [{id,label,color}]`を必須とする。`color`は16進色、状態IDは重複不可。`unverified`・`unknown`・`conflict`は予約状態であり、国固有の確認済み状態として再定義しない。根拠のある状態だけを参加させ、根拠欠落・非一致はunknown、異なる根拠付き状態の競合はconflictとして表示する。件数から承認を推定しない。

`gaps`には任意の`territory_id`と`source_id`を追加でき、どちらも登録済みIDへの参照とする。選択地域の出力へ入れるのはその地域の不足と全体共通の不足。別の市・県の不足を混ぜない。

選択地域の資料・概要・所見・不足・出典は、画面、採用したMarkdown／HTML／CSVで照合する。国別の出力を採用しない場合でも、取得済み原典への到達と次の作業を残す。

## 7. 検証と合成ケース

検証入口は`validateDataset(dataset)`。任意拡張は`lib/planning-validation.mjs`の`validatePlanning`へ分離してあり、型が壊れた入力にも例外で落ちず、`{errors,warnings}`を返す。必須の基本スキーマ検査は`validateDataset`が担当する。

`tests/planning-fixture.mjs`は`planningFixture('integrated'|'scattered'|'partial')`または`planningScenarios()`を提供する。いずれも**完全な合成資料**であり、実国の承認・予算・評価の証拠ではない。

- A: 統合された制度・資料。5分類、7種類の所見、0の執行、別尺度の評価、根拠付きの状態。
- B: 分散した資料・異なる取得段階。採用分類外の資料も「その他」へ残し、取得停止と過去の確認を区別。
- C: 部分的な資料、unknown／unavailable、`outputs: []`、不足と代替作業。

同名のCity／Districtを別ID・型・コードで持ち、North親地域には資料を置かない。市から同じ親へ戻したときに、市の計画・財政数値・制度状態が親へ残らないことを実操作でも確認する。自動テスト成功だけで原典確認・公開検証・実利用者の受入を完了扱いにしない。

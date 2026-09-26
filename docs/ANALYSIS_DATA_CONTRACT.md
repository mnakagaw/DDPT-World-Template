# 内部比較のデータ契約（schema 0.2 の任意拡張）

更新対象は共通テンプレートの内部比較。`dataset.analysis` がない既存国版も有効。
上部の位置確認・地域選択と、下部の各指標に含まれる内部比較は役割が異なる。
内部比較の行や図形を確認しても、上部の選択地域・指標・期間を変更しない。
親の全体値は親IDの同範囲観測を最優先する。任意`analysis.aggregation`がなければ従来どおり親IDの観測だけを使う。設定がある指標に限り、根拠付き所属の完全・非重複被覆から上位値を計算できる。内部比較の表示だけを集計根拠にせず、率の単純平均・不完全な小計の全体値化・全国値の地方配分は行わない。

```json
{
  "analysis": {
    "kind": "regional",
    "terminal_territory_ids": [],
    "comparisons": [{
      "parent_id": "WLD",
      "member_ids": ["TST", "OTH"],
      "label": "Registered test countries",
      "membership_note": "Fictional membership declaration; synthetic QA only.",
      "source_ids": ["membership-source"],
      "color_scale": {"mode": "within_selection"}
    }],
    "country_sites": [{
      "territory_id": "TST",
      "country_id": "TST",
      "url": "./countries/TST/",
      "target_territory_id": "TST",
      "indicator_map": {"people": "population"}
    }],
    "aggregation": {
      "policy": "exact_then_complete_cover",
      "rules": [{
        "indicator_id": "people",
        "method": "sum",
        "completeness": "full_cover",
        "label": "AreaData calculated population",
        "note": "Exact higher-area observations first; otherwise a complete non-overlapping cover."
      }]
    }
  }
}
```

## 地理の範囲・所属

- `kind` は `world` / `regional` / `country`。`terminal_territory_ids` と `comparisons` は配列で必須。
- 世界の探索rootは `country.id = country.national_territory_id = "WLD"`、地域レコードは `id:WLD, level:national, type:exploration_scope, parent_id:null`。
  これは探索範囲の識別子であり、世界を行政上の国として扱う宣言ではない。
- 世界内の国は `type:country` と明示 `country_id`（3文字の国識別子）が必須。同じ国IDの国レコードを重複させない。
  `level` や途中の階層数、国名、continent/macroregionの名称は固定しない。
  地区に `country_id` を追加するときは最寄りの国祖先と一致させる。
- 明示比較は親ごとに1件。全 `member_ids` は登録済みの親の子孫で、重複・他branch・親自身・同じ比較内の祖先/子孫の重複所属を許さない。
  途中の階層を飛ばした国一覧や自治体一覧を指定できる。順序を保持し、件数で切り捨てない。
- `label` と `membership_note` は空でない文字列、`source_ids` は1件以上の登録済み出典。所属根拠の取得状態は `ready` / `partial`。
  明示設定は異なる行政種別や境界版を含める場合の比較対象集団の宣言でもある。編集者は所属・同等性を出典で確認する。
- 明示設定がない親は `parent_id` が一致する直接の子を全件使う。
  この既定集団で `type` / `level` / 同一国内の `boundary_version` が混在すれば、値と全行を残して色・数値比較を停止する。
  国同士はそれぞれ独自の境界版を持つため、版の文字列が異なることだけで除外しない。
- `city, municipality, municipio, municipalidad, commune, comuna, municipal_district, distrito_municipal, town, town_council, village` は `type` または `level` の完全一致で終了地点とする（大小文字・アクセント・空白/ハイフンを正規化）。
  下位ward等が登録されていても内部比較を停止する。追加国別終了地点は `terminal_territory_ids` に設定する。
  終了地点の比較設定は拒否する。名称の部分一致で市・地区を統合しない。
- 下位地域へ移動できるが、その下位台帳が親全域を覆わない場合は、任意の `incomplete_child_cover_ids` に親IDを登録する。階層選択は維持し、その親の内部比較を止める。`terminal_territory_ids` や同じ親の明示比較とは併用しない。下位の一部だけを親の全体比較として表示しない。

## 観測・意味・欠測

共通の `indicator_id` は同じ定義・単位・母集団・測定方法を表す。
出典が異なるだけでは比較不能としない。国別adapterは概念が異なる系列を別指標IDに分ける。

| 項目 | 指標の基準 | 観測に明示された場合 |
|---|---|---|
| `definition_id` | 省略時は `indicator.id` | 完全一致を比較条件とする |
| `definition` | 既存必須の定義文字列 | 完全一致を比較条件とする |
| `unit` | 既存必須の単位 | 実際の単位を保持し、異なれば比較から除外 |
| `population` | 任意の母集団の文字列 | 基準が未宣言または異なれば比較から除外 |
| `measurement_method` | 任意の方法の文字列 | 基準が未宣言または異なれば比較から除外 |
| `method` | `measurement_method` の任意alias | 両方記載した場合は完全一致必須 |
| 観測の `boundary_version` | 地域レコードの版 | 異なる場合は値を保持して比較から除外 |

これらの任意文字列は、記載するなら空文字・null・配列・objectを許さない。
ただし `boundary_version` は未確認を表す明示nullを許す。値の換算・定義の翻訳同一視は行わない。
意味の差は検証エラーにせず、行の実際のmetadata・値・除外理由を表示する。
これにより、相違のある取得済み証拠を捨てずに色・格差計算の対象外にできる。

- 通常は地域ID＋指標ID＋**完全に同じ期間文字列**の行を読む。近い年・別期間・別地域に置き換えない。唯一の例外は、明示した国勢調査の混合基準年集計である。
- `observed` の有限数値だけが数値。`0` は有効。`missing / suppressed / not_applicable` はnull。
- 対象系列があるが選択期間行がない場合は `missing`、地域の系列自体がない場合は `not_collected`。
- 取得失敗・未取得の出典を数値比較に採用しない。行の出典は観測の `source_id` を優先し、観測がない場合だけ指標の出典を参照する。
- `geographic_level:national` 出典は国の値だけ。世界版では出典の `country_id` と `type:country` 地域の `country_id` が完全一致必須。
  既存単一国のrootには `source.country_id` 未記載を許容する。国の全国値を地区へ割り当てることは許さない。
- `geographic_level:world_country_series` は公式世界系列または国別系列の出典用。
  数値の `observed` はWLD探索rootまたは `country_id` 付き国だけに許す。
  大陸・地域等の `missing/null` 行は同範囲系列未取得の明示として保持できる。これ自体は集計値にならないが、別途`analysis.aggregation`で許可した指標は国等の取得済み観測から計算できる。

## 上位集計

- `analysis.aggregation.policy`は`exact_then_complete_cover`。対応する`rules[]`がない指標は計算しない。
- `method:sum`は指標側も`aggregation:sum`。人口・世帯・件数等でも、定義・期間・単位・母集団が互換の場合だけ使う。
- 選択範囲自身の互換な観測があれば、下位地域の欠測に関係なくその観測1件を採用する。
- 親観測がない場合のみ、取得済み所属根拠を持つ明示比較集合へ降りる。子の親観測があれば孫へ降りない。これを再帰し、全域を重複なく覆えた場合だけ合計する。
- 一部地域だけ取得できた場合は`status:incomplete`、全体値はnull。取得済み構成地域の`covered_subtotal`、不足ID、構成IDを計算監査として表示・出力する。
- 同時選択に祖先と子孫が含まれる場合や同じ構成観測が重複する場合は`incomparable`とし、合計しない。
- 率は互換な分子合計÷分母合計だけを許す。平均寿命等は検証済みweightを持つ方法以外で平均しない。0は取得値、nullは欠測として別に扱う。

`rules[].period_policy`は省略時または`same_period`なら選択期間の完全一致を求める。`latest_available_by_component`は、[国勢調査系列契約](CENSUS_SERIES_CONTRACT.md)に従う指標だけに明示する。この規則で`latest-available`を選んだ場合、構成地域ごとに最新の確認済み観測を採用し、実際の年を構成表・CSV・文書へ出す。これは同一年集計ではない。異なる年を隠した合計、前年値の持越し、国勢調査と国際参照系列の混合は禁止する。

## 図形の結合と色

- 図形は `properties.territory_id` で結合する。同名の市・地区、隣接地域、近似コードに代替しない。
- `properties.code` / `official_code` / `code_system` / `boundary_version` を提供した場合は、地域登録の対応項目に型も含め厳密一致が必要。
  不一致はvalidatorエラー。runtimeへ直接渡した場合もその図形を結合しない。
- 同一地域IDの複数Featureは拒否。島などの複数領域は1件のMultiPolygonにまとめる。
  図形がない地域・未照合図形の地域も表に残す。境界不足は統計の欠測と区別する。
- 図形固有の制作版を統計対象境界と同一視しない。統計との整合が未確認なら `geometry_edition` と境界出典に制作版を記録できる。
  `boundary_version` を提供したのに一致しない状態を無視するための例外ではない。未確認事項を国の地理注記・取得gapに明記する。
- `color_scale.mode:within_selection` はその選択集団の比較可能な観測値のみから5色の等間隔閾値を作る。
  別の集団を選ぶと閾値が変わる。全値同値なら単色。比較値なしなら動的凡例なし。
- `mode:fixed` は `breaks` に有限・厳密昇順の4閾値が必須。`within_selection` に固定閾値を混在させない。
  任意 `label` で区分根拠を説明する。低い値は1色目、高い値は5色目、閾値と同値は下側区分。
- 欠測・意味差・不適合行は灰色。図形の有無だけで観測値を削除しない。
  色分けは優劣判定や因果診断ではなく数値の分布を示す。

## 国版への接続

`country_sites` は任意。各項目の `territory_id` は世界内の国レコード、`country_id` はその国IDと完全一致。
同じ地域の入口を重複させない。`url` はcredentialsのないHTTPSまたは `./` から始まる子path。
`../`・root相対 `/`・protocol相対 `//`・encoded traversal・制御文字を許さない。
`target_territory_id` は任意の空でないIDで省略時は `country_id`。
`indicator_map` は任意の空でない指標ID同士のdictionary。

接続先は別dataset。画面側は国版リンクのcountry/territoryを接続先のIDに置き換え、選択期間を渡す。
指標は現在のIDに対する明示 `indicator_map` があるときだけ対応IDを渡す。mappingがなければ指標queryを引き継がず、国版の既定指標を使う。
国際系列と国内系列は概念・定義が異なる場合に別IDとして保持し、同名や似たIDから対応を推測しない。
世界版のtype/code/boundaryをコピーしない。リンク先の実在・指標対応・最新公開状態はこのvalidatorだけでは検証できない。
国版から世界への独自戻り設定は未実装。通常のブラウザー戻ると世界版のURL状態復元を使う。

## 純粋helper API

- `comparisonSet(data,parentId)` → `{parent,members,label,note,terminal,source_ids,explicit,color_scale}`。
- `observationMeaning(indicator,observation)` → `{definition_id,definition,unit,population,method,comparable,reason}`。
  `comparable` は意味の一致だけを表す。数値有無・出典取得・地理条件は内部比較が追加判定する。
- `observationContext(data,area,indicator,observation)` → 意味metadataに `{source,meaning_comparable,comparable,reason}` を追加。
  `meaning_comparable` は意味だけ、`comparable` は意味・明示観測境界版・出典の取得状態・出典の地域範囲を合わせた判定。
  `value/status` は上書きしない。版未記録を自動で不一致とみなさず旧データとの互換を保つ。
  明示版の不一致やfailed/error等の出典は履歴線に使わず、履歴表・全体値・診断出力へ元の値と理由を残す。
  数値有無と選択期間の欠測判定は引き続き `observationState` / 内部比較が担う。
- `internalComparison(data,parentId,indicatorId,period)` → `{set,rows,features,scale,reason,indicator,period}`。
  全rowは `{area,observation,value,status,source,definition_id,definition,unit,population,method,meaning_comparable,comparable,reason,boundary,boundary_reason}`。
  `features` は同定一致した境界（欠測行も含む）。`boundary_reason` は図形の欠落・不一致を説明する。
- `scale` は `{mode,breaks,legend,colors,label}`、全値同値時のみ `constant_value` を追加。
  `legend` は `{color,label,lower,upper}` の配列。動的閾値なし・全値同値時は `breaks:[]`。
- `colorForComparison(comparison,row)` は色文字列を返す。比較不能行は `NO_COMPARISON_COLOR`。

helperは元datasetと選択stateを変更しない。画面・診断出力は同じ結果を使う。
合成検証は `tests/analysis-fixture.mjs` と `tests/analysis.test.mjs`。架空の世界→大陸→中間地域→国→地域→県→市、別国branch、親欠測、0、同名市、30自治体を含む。
この契約と自動検証は、所属出典・統計定義・境界の現実との一致や、公開サイトの操作確認を代替しない。

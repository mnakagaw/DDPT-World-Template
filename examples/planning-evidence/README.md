# 公式の計画資料を使ったA・B・C検証例

2026-09-13に限定収集・監査した実資料を、schema 0.2の任意計画契約へ変換するオフラインの例です。国別完成版や最新制度の証明ではありません。地図用境界は未取得で空、地方統計は未取得のままです。合成図形や全国値の地方配分はありません。

| 出力 | 実資料 | 確認範囲 |
|---|---|---|
| `dom` / Moca (A) | SISMAPの自治体ページとPMD 2024–2028 | PMDの短い優先事項、2.02 Plan de Desarrollo Municipalの取得時表示100%。法的承認は未検証 |
| `uga` / Yumbe (B) | 地区サイトの計画、財務省のQ3実績、2018年LGPA | 計画の優先事項、承認予算・修正予算・累積収入、過去のAccountability Requirements評価50%を、それぞれの期間と定義で表示 |
| `uga` / Adjumani (C) | 地区の公式資料一覧 | 計画名と期間の掲載まで確認。本文未取得として公式一覧へリンク |

原本の出典、取得日時、SHA-256、読んだ頁・表、数値の意味は `audited-input.json` に保存しています。この入力は収集時の詳細監査JSONから作った短い抜粋で、要約以外の本文は含めません。元の詳細監査JSONのSHAも記録しています。

## オフラインで再生成

Node.js 22以降。外部npm依存、ネット接続、APIキーは不要です。**監査時と同じバイトの原本を持つ保存ディレクトリ**を指定してください。原本の再取得を自動で要求・実行しません。

```sh
node examples/planning-evidence/build-examples.mjs --source-dir .work/planning-real-sources --out .work/planning-real-qa
```

保存元は `audited-input.json` の `sources[].raw_path` と同じ相対構成にします。この収集では `.work/planning-real-sources/raw/` にPDF・HTML・識別用API JSONを保存しました。ファイル欠落、SHA不一致、既存の出力先があれば、出力を作る前に失敗します。別PCでは既存の原本保存フォルダーを渡せます。原本を持たないGitクローンだけではこの実資料例を生成できません。

生成物は次の構成です。`site/` の生成・公開はこのアダプターの範囲に含みません。

```text
<out>/dom/data/dashboard.json
<out>/dom/data/example-receipt.json
<out>/dom/raw/...
<out>/uga/data/dashboard.json
<out>/uga/data/example-receipt.json
<out>/uga/raw/...
```

`dom` または `uga` が既に存在する場合は上書きしません。再検証は新しい出力先を使います。`generated_at` は固定した証拠版の日時で、同じ入力から同じdatasetを再現します。

```sh
node scripts/validate-country.mjs --project .work/planning-real-qa/dom
node scripts/validate-country.mjs --project .work/planning-real-qa/uga
node scripts/build-country.mjs --project .work/planning-real-qa/dom
node scripts/build-country.mjs --project .work/planning-real-qa/uga
```

## 原本と全国人口

原本PDF・個人メールURLを含むHTMLはGitへ入れません。`raw/` はローカル監査資料です。原本の再配布許諾は未確認であり、そのままWebへ公開しないでください。Adjumaniの具体的な個人メールURLは監査済み入力・datasetから除外し、公式一覧のURLだけを残しています。

`population/` の小さなJSONは今回取得したWorld Bank公式APIの原本とreceiptです。`mrnev=1`で得た最新非nullの全国人口を、各国1件ずつ使います。DOMは2025年11,520,487人、UGAは2025年51,384,894人。取得は2026-09-13、APIの`lastupdated`は2026-07-13です。これらは新しい実行時の最新値を主張しません。人口の定義は原本メタデータの「居住者を数える年央推計」を保持しています。[World Bank指標メタデータ](https://api.worldbank.org/v2/indicator/SP.POP.TOTL?format=json)

人口原本もreceiptのSHAを照合します。更新する場合は原本・receipt・確認内容を新たに監査してください。通常の例生成ではネットワーク通信をしません。

## 混ぜない意味

- MocaのSISMAP organism ID 20913を公式地理コードへ変換しません。計画PDFと同自治体ページの紐付けだけを確認しています。[SISMAP Moca](https://www.sismap.gob.do/municipal/organismoevidenciasmunicipales/id/20913)
- Yumbeの2018年評価Vote 556、2024/25年度財政Vote 934、UBOS 2024国勢調査コード313は別の名前空間です。地域名・district型と発行者を確認し、資料一覧には同じsource-identified districtとして配置します。各時点の境界一致、コード変換、現行境界での集計は未確認です。`official_code:null`、`boundary_version:null`とし、`territory_match.method`、`findings.scope`、不足事項へ区別を残します。監査時の内部地域IDは`territory_match.territory_id`にも固定し、資料の`territory_id`と一致することを生成前に確認します。同型で公式コード未確認のAdjumaniへ、Yumbe資料の割当だけを変えても通りません。この内部IDは公式コードの代用ではありません。
- 計画期間、会計年度、Quarter 3、評価2018年、取得時点の表示値は別の期間として持ちます。Quarter 3の累積収入を単独四半期の収入や年度決算にしません。
- Yumbe Q3 PDF p.2 A1の収入表はUshs 000sです。採用値は承認予算64,846,977、修正予算68,579,647、累積収入53,862,674。p.3のBillion表記と支出額の不一致は不足事項に記録し、支出値を採用していません。[公式Q3原本](https://budget.finance.go.ug/sites/default/files/Indivisual%20LG%20Budgets/934%20Yumbe%20District%20Quarter%203.pdf)
- 承認・修正は財政原本の列名として保持します。別の承認決議や法的行為を認定しません。すべての資料の`official_status`は`unverified`です。
- 2018年評価は過去資料です。地区サイトに2022年評価へのリンクもありますが、本例では本文未確認です。[Yumbe公式資料一覧](https://yumbe.go.ug/yumbe-dlg-information-resource-documents)

## この例の検証

両datasetのschema/計画契約エラー0を確認しました。全国統計だけという警告は想定通りです。オフライン再生成でdatasetのSHA一致、既存出力拒否と元のバイト維持、原本改変の出力前拒否、地方への全国値配分なし、境界0、dataset内の個人メールURLなしを確認しました。画面と実際の取得物の検証は、この例の生成成功とは別に実施します。

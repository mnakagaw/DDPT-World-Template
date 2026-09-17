# AreaData Americas v0.10 制作確認

確認日: 2026-09-17 JST

## 対象

- 範囲: UN M49 Americas (019)
- template commit: `f849460013da2263a36fbaff7d466669d78b586c`
- 生成先: `.work/areadata-americas-v0.10.0-candidate11`
- dataset SHA-256: `72b65552398ada1879009baeda323a23b09967a8ee4acc6a1c306c5a54f43589`
- data edition: `2026-09-13T10:24:18.027Z`
- 生成元: `.work/world-v0.4/new/raw`
- 中米7か国adapter: `.work/areadata-ca-v0.9.0-all-seven-selection`

## 実装範囲

- UN M49 Americasの57 country/areaを台帳に保持した。
- 探索入口はNorthern America 5、South America 16、Central America + Caribbean 36。最後はUN M49 013と029を結合したAreaData独自の表示区分であり、UN公式の一つの地域や法定計画主体として扱わない。
- 2,118地域、6指標、3,107観測、2,828 observed、228 comparison sets、22 sources、4 gapsを収録した。
- Censusと国内階層はBLZ、GTM、SLV、HND、NIC、CRI、PANの7 countryだけ統合した。Census観測2,063件を他の国やAmericas全体へ流用しない。
- 観測に使う15 source recordsはすべて候補内の原payloadへ`raw_path`とSHA-256で追跡できる。中米Census原資料315ファイル、UN WPP原本1ファイル、取得receipt、正規化監査7ファイルは公開site外に保存した。
- 国境参照図形は32/57のexact join。未結合25件も台帳と表に残した。
- Americas全体の同一範囲公表値がない指標は欠測。国値の不完全小計や率の単純平均を表示しない。
- 大陸・広域のPlanningは法的権限を推定せず、国別adapterで法令・計画・予算・評価資料を確認する条件を表示した。

## 自動検証

- `npm run check`: 64 JavaScript modules／JSON templatesを検査、合格。
- `npm test`: 158/158合格。
- `node scripts/validate-country.mjs --project .work/areadata-americas-v0.10.0-candidate11`: errors 0、warnings 10。
- `node scripts/verify-regional-delivery.mjs --project .work/areadata-americas-v0.10.0-candidate11`: `ok: true`、`publishable: false`。制作確認済みで、独立監査待ち。
- `--require-publishable`: exit 1。`Independent audit must be ACCEPT before publication`により意図どおり公開を停止した。

warningsは9 source recordsの利用条件要確認と、国別planning資料未取得である。いずれも未取得を完了扱いせず、画面と受入記録へ残した。

候補9の独立監査で、CensusとUN WPPの採用値を候補内の原payloadまで追跡できない問題が見つかった。候補10では生成器に原資料importを追加し、15/15の使用sourceについてpayload存在とSHA-256一致を再検証した。候補9は公開対象から除外した。

候補10の独立再監査では、通常のホーム導線が広域・国ページへ`period=2025`を渡し、取得済みCensusを0 sourceの`No data`として隠す問題が見つかった。候補11では世界・大陸・広域の入口を`latest-available`にし、各指標を自身の最新実年へ解決するよう修正した。通常導線のCentral America + CaribbeanでCensus 7 sources・covered subtotal 43,883,591、GuatemalaでCensus 2018の14,901,286を実画面確認した。候補10は公開対象から除外した。

## 実画面

Codex in-app Chromiumで英語・スペイン語・日本語、通常幅と390×844を確認した。

- ホーム、地域診断、テーマ診断、Database、Planningの直接URLを表示した。
- Americas→Central America + Caribbean→Guatemala→El Progresoを操作した。
- El Progreso選択後に同じ親Guatemalaをdropdownから再選択すると、見出しとURLはGTMへ戻り、department selectorは空になった。
- 内部比較の行へ注目しても、分析対象のGuatemalaとURLは変わらなかった。
- Census 2018、WDI人口2025、UN WPP人口2026、その他WDI 2024の実期間を画面と出力で確認した。
- 390px viewportではdocument/bodyともclientWidth 375、scrollWidth 375で横あふれなし。
- 地図のキーボード選択、戻る／進む、共有、brand reset、console、404を確認。console warning/errorは0件。

## 出力照合

診断・計画・証拠・資料のCSV／HTML／Markdown 20ファイルを実生成した。`evidence/OUTPUT_VERIFICATION.json`で次を照合した。

| 対象 | 診断CSVデータ行 | 期間の確認 |
|---|---:|---|
| Americas | 348 | WDI実年、Census mixed-year |
| Central America + Caribbean | 222 | WDI実年、Census mixed-year |
| Guatemala | 138 | Census 2018、WDI 2025、UN WPP 2026 |
| El Progreso | 54 | Census 2018、国際系列の地方欠測 |

各CSVの初行・末行、選択ID、単位、status、source URLを確認した。

## 未完了と公開状態

- 独立監査: PENDING
- Hosting: 未実施
- Public: 未公開
- 残る50 country/areaのCensus・国内階層、未結合25 country/areaの表示図形、全57 country/areaの計画法・計画資料は国別adapterで継続する。
- 実務利用者テストと公式機関による受入は未実施。

`templates/REGIONAL_INDEPENDENT_AUDIT.md`の独立監査が実データ、原資料、画面、取得物を確認して `ACCEPT` と記録し、publication gateが通るまで公開しない。

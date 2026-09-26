# AreaData アジア全域の範囲と収録状態

2026-09-26時点の候補版。世界ポートフォリオ（データSHA-256 `77c41cbaaae633b096916b704ae8c3e0ed4cb77e15440618c3f7b266abde2a9b`、edition `2026-09-23T14:27:10.704940Z`）から、UN M49 Asia (142) の全50 country/areaと5 subregionを切り出す。候補固有のデータSHA-256は生成先の `evidence/ASIA_SCOPE.json` に記録する。公開中の世界版と同じ国際統計の版であり、追加取得をした版ではない。

| 広域 | UN M49 | 国・地域数 |
|---|---:|---:|
| 中央アジア | 143 | 5 |
| 東アジア | 030 | 7 |
| 東南アジア | 035 | 11 |
| 南アジア | 034 | 9 |
| 西アジア | 145 | 18 |

アジア候補は56地域、31指標、10,668観測、50参照図形を持つ。国の図形と正確に結合できたのは44/50であり、図形がない6国・地域も台帳と表に残す。31指標の内訳は世界・広域で表示する27の国際ポートフォリオ指標と、従来のWDI 4指標。UN WPP総人口は50/50か国・地域と5/5広域、アジア全体に同じ系列の直接観測がある。UNSD GDP総額・1人当たり・実質GDPは各50/50か国・地域、5/5広域、アジア全体に公表行がある。国際系列の国別被覆は指標ごとに異なり、失業率46/50、若年NEET率38/50、故意の殺人率39/50、IMFインフレ率47/50。IMFの独自地域分類はUN M49のアジア値へ転用しないため、アジア全体と5広域のインフレ率は欠測のままにする。割合を国別値から単純平均しない。

UN WPPのAsiaとEastern Asiaの直接公表値には、WPP location 158（台湾）が含まれる。UN M49の掲載50件（東アジア7件）との比較表には台湾の独立行がない。2026年総人口の公表値と掲載行の合計の差は、東アジアで23,011,292人、アジア全体で23,011,294人（公表値の丸めによる2人差）。画面と診断出力は、この出典側の範囲差を明記し、国別行の合計でWPP公表値を置き換えない。

UNSD AMAの2024年GDPも、Asia/Eastern Asiaの直接公表値とM49掲載50/7件の合計が一致しない。名目GDPでは約7,970億米ドル、実質GDP（2020年価格）では約7,863億米ドルの差があり、原本の公表広域値と国別行を全件再抽出して確認した。取得済み原本だけでは構成や調整の理由を確定できないため、台湾分と断定しない。画面・診断出力で未照合の差を明示し、公表広域値を国別行の合計へ置き換えない。

国勢調査の事前台帳は50件あり、UNSD掲載年は50件、過去回へのUNSDリンク付き掲載は36件。ただし、掲載・リンクは原本取得や数値採用ではない。現候補の国内地域データ枝は0/50、国別の計画法・計画・予算も未統合。ラオス、バングラデシュ等の別案件成果を、この候補の50か国完成数へ足していない。国内版は公式数値・コード・境界・法定計画主体の照合後に接続する。

再生成・収録監査・静的検証:

```sh
npm run create:asia -- --world-portfolio .work/areadata-world-v0.12.1-latest-regions/data/dashboard.json --out .work/areadata-asia-20260926-commit-c6cf9fe
npm run audit:asia -- --project .work/areadata-asia-20260926-commit-c6cf9fe
npm run verify:asia -- --project .work/areadata-asia-20260926-commit-c6cf9fe
npm run verify:asia:m49 -- --project .work/areadata-asia-20260926-commit-c6cf9fe
npm run sources:asia:materialize -- --project .work/areadata-asia-20260926-commit-c6cf9fe --legacy-world-raw .work/world-v0.4/new/raw --wpp-dir .work/un-wpp2024
npm run sources:asia:replay -- --project .work/areadata-asia-20260926-commit-c6cf9fe
```

候補の `evidence/ASIA_SCOPE.json` は世界版入力ファイルの絶対パス・SHAと地域ID、`ASIA_COVERAGE.json` とCSVは指標ごとの被覆・年・国勢調査所在、`ASIA_CANDIDATE_VERIFICATION.json` は照合済み内容と未実施事項を記録する。`ASIA_M49_LIVE_CHECK.json` は現行M49との照合、`ASIA_SOURCE_RAW_MANIFEST.json` は18原本のURL・保存先・SHA・サイズ・候補datasetへの結合を記録する。WPP・SDG・UNSD AMA・IMFの採用9,524観測は原本から再抽出して全件値・状態を突合し、`ASIA_SOURCE_REPLAY.json`へ記録する。WDI 4指標の国別1,000セルも原本API JSONに照合する。広域の欠測144行はAreaData側の明示的な欠測記録であり、WDI原本行とは扱わない。大容量の原本はGitにも公開サイトにも複製しない。

標準データ検証はエラー0、警告5件。うち4件はdatasetの従来source schemaにprivate原本パスがないという警告だが、候補の別manifestで原本とSHAを照合済み。残る国別計画資料は未取得。`npm run check`、`npm test` は通過。国際系列のAsia地域値がない指標は国別比較の件数・年・範囲として表示し、地域全体の値と区別する。

現候補はコード `c6cf9fe26cbdf0c88da8adedeaf84f8f2fb58773` から生成し、dataset SHA-256は `a7097530857c252656b7395c99d2ab97e30188a3dba6f271aca7f1d8cc094a50`。旧候補 `cd8124f` は広域→国の切替で共通GDP指標・期間が戻るため `REJECT`、`4c225d8` は上位再選択時の比較階層の不一致、主要操作の未翻訳、受入証跡の欠落により `REJECT`、`1c92fe3` は中央アジアのテーマ診断の先頭要約にアジア全体の値が出るため `REJECT` となった。現候補は最後の表示不整合を修正し、Edge日本語・スペイン語で中央アジアのGDP要約と詳細が同じ2024年の506,527,657,441米ドルを示すことを確認した。静的CSV/Markdown/HTML照合、clean archiveからの再生成照合、原本18件からの採用9,524セルの再照合を候補の `evidence/` に記録した。`npm run check` 132モジュール、`npm test` 218件が通過している。

ただし、これは制作側の確認であり、独立担当による現候補の監査判定は別に必要。ブラウザーから保存されたファイルのバイト列、狭幅、全50件の国勢調査リンク、国内枝を使う国→市の操作は未確認または未実装である。50件の国際統計入口と国内版50件の完成を区別する。公開ゲートが要求する `ACCEPT` まではFTP・公開サイトへ反映しない。候補の受入票と証跡は `.work/areadata-asia-20260926-commit-c6cf9fe/evidence/` に保存している。

# 実行テンプレート0.9.2 検証記録

## 対象

- Codexタスク `01a0a2b1-7628-74d1-94ca-1c0d8b67066d` の直近の国別制作・独立監査工程
- Public [Census Dashboard Kit](https://github.com/mnakagaw/Census-Dashboard-Kit) の独立監査手順 commit `3f8861637d60481c09f5f2da1ca5f4c33b3082c0`
- フィリピン成果 `★Antigravity/CensusDashBoard/philippines` の `evidence/CODEX_INDEPENDENT_REVIEW_2026-09-17.md`
- AreaDataの調査記録、国別作業手順、開始文、AI依頼文、補助確認票、独立監査票への適用

## フィリピンで確認した差

フィリピン版は国別validatorのerror・warning 0、delivery gateの `ready: true`、自動試験138件合格だったが、独立監査では公開を止める問題が確認された。

- 元変数と表示指標の意味が異なる保健指標が5件あった。
- 古い全国値と新しい地方値が、同じ最新値の約束の下で混在した。
- 算出率をsource reportedと表示し、式・構成値・被覆を示していなかった。
- 行政区分・境界の有効時点と現行構成が一致せず、地域型にも誤分類があった。
- テーマ比較が選択親の子ではなく全国集合を使った。
- 計画法・手引きが境界sourceへ誤接続され、根拠のない期間を持った。
- 取得済み年齢・性別資料が人口ピラミッド等の機能判断へ反映されなかった。
- 生成Wordは13ページ存在したが、指示文・空欄中心で、必要な診断本文・図表・根拠が不足した。
- 不足表示、言語、地域ラベル、地図操作にも実データ・操作との不一致があった。

この結果から、ファイル存在、件数、自己申告boolean、緑のtestだけで完成を判定しない。元データと成果物から意味、最大年、reported／calculated、比較ID集合、source種別、文書内容を導出し、別担当が再確認する。

## 反映した規則

- 制作者の完了後に、別のタスク・会話・担当が読み取り中心の独立監査を行う。
- 監査結果は `evidence/INDEPENDENT_AUDIT.md` に保存し、`ACCEPT / REJECT / INCOMPLETE AUDIT` の一つで終える。
- blockingまたはmajor findingが残る間は公開しない。制作者が実データ・コード・出力を修正し、別監査を再実施する。
- 元fieldとindicatorの意味、観測から再計算した最新年、reported／calculatedの変換根拠、選択親と比較集合を確認する。
- source種別と本文を照合し、境界・統計・法令・手引き・計画を誤接続しない。
- Word／PDFは全ページrenderに加え、地域、値、診断本文、図表、引用、画面との一致を確認する。
- 国別の既定 `/` は全国Territorial Diagnosticとする。独立homeを採用する国だけ、出典付き基本情報・全国人口と年・行政階層・3ページへの経路を要求する。
- Public向けREADMEには利用手順と機能を簡潔に示し、個別失敗の詳細は内部research・evidenceへ保存する。

## 3案件へ同じ監査を適用した結果

フィリピン後に、既存のウガンダ、バングラデシュ、ラオス成果へ同じ独立監査契約を適用した。3件とも `REJECT` で、報告は各案件の `evidence/INDEPENDENT_AUDIT.md` に保存された。

- バングラデシュ：現行Kit 154/154とvalidator error 0でも、地域selectorがURLだけを更新し本文を前地域のまま残すblocking defectを再現した。64 workbookの18～20 sheetをcatch-all一行で全表確認済みとし、District文書の適用法令も未解決だった。
- ラオス：現行Kit 154/154とvalidator error/warning 0でも、OPHI 6 sheetとCOD-PSの数値列をfield単位で閉じていなかった。英語画面の42指標はすべて日英混在し、地方計画manual未確認のままplanning completedとした。
- ウガンダ：15表78数値列、68指標、代表値・算出率・難民数・APAA・地理は独立照合できた。一方、README記載の開発serverはpublic JSON直接importで空白となり、集計回帰testは旧固定件数754に対して実測1,768で1件失敗した。Wordにも孤立した注記頁があった。

この再監査により、元データ自体がよく整っていても、操作、再構築手順、テスト期待値、言語、計画根拠、文書layoutの一つが重大なら完成を受け入れないことを確認した。

## 外部監査手順の固定

`config/external-source-registries.json` へ Public Kitの `docs/INDEPENDENT_AUDIT.md` を登録した。

- commit：`3f8861637d60481c09f5f2da1ca5f4c33b3082c0`
- SHA-256：`e60dec74752a02b09a56f570190f2c2c9fa26a59d8adba7acdcb74fdb10f5225`
- AreaData用の監査票：`templates/INDEPENDENT_AUDIT.md`

## 検証結果

- `git diff --check`：空白エラーなし。
- JSON parse：`config/external-source-registries.json`、`package.json`、`package-lock.json`に合格。
- `npm run check`：58 JavaScript modules／JSON templatesの構文検査に合格。
- `npm test`：150件合格、失敗0件。

## この版で実装していないこと

- フィリピンで必要性が判明したsemantic mapping、最大年再計算、比較ID集合、文書内容の自動gateは規則化した段階で、このリポジトリの実行コードへ未実装である。
- AreaData公開サイト、FTP配置、既存国別datasetは変更していない。
- 独立監査票の追加自体は、既存国別成果が監査済み・合格済みであることを意味しない。
- 現地自治体職員・研究者による実利用試験は実施していない。

したがって0.9.2は、フィリピンの独立監査で判明した完成検査と、制作者→独立監査→修正→再監査→公開の運用をテンプレートへ取り込んだ文書・運用版である。

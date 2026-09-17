# AreaData Americas v0.10 制作・監査記録

確認日: 2026-09-18 JST

## 公開範囲

- 範囲: UN M49 Americas (019) の探索入口
- 国・地域台帳: 57 country/area
- 国内Census・階層を統合した国: BLZ、GTM、SLV、HND、NIC、CRI、PAN（7/57）
- データ版: `2026-09-13T10:24:18.027Z`
- dataset SHA-256: `9e0d08bf13ddf4cce4af923f51bddf43443adb409a59967998cf76b0e38e5322`
- 最終生成先: `.work/areadata-americas-v0.10.0-release-2026-09-18-final3`

この版はアメリカ大陸57件を連続して探索・比較できる地域入口であり、57件すべての国別版が完成したという意味ではない。Censusと国内階層を統合済みの7か国は、国から取得済みの国内地域へ進める。残る50件は国際系列と所在調査を表示し、未取得の国内値を補完しない。

## 収録内容

- 2,118地域、6指標、3,299観測、3,020 observed、228 comparison sets、22 sources、5 gaps。
- 探索区分はNorthern America 5、South America 16、Central America + Caribbean 36。後者はUN M49 013と029を結合したAreaData独自の表示区分であり、UN公式の単一区分や法定計画主体として扱わない。
- UN WPPは55/57地域、2023–2026年の220観測。BVTとSGSは原表に行がなく欠測として保持する。
- Census観測2,063件は統合済み7か国だけに属する。国ごとの調査年を表示し、同一年値や誤差幅として扱わない。
- 国境参照図形は36 feature、country exact joinは32/57。未結合地域も台帳・比較表・欠測表示に残す。
- 同一範囲の公表値がない場合、Americas全体値を直接観測として作らない。計算を許可した加算指標も完全・非重複被覆だけを集計し、率は単純平均しない。

## 原資料と採否

- `SOURCE_PREFLIGHT.json/.md`: 57件。所在確認、アクセス、取得、検査、地理照合、採用を分離。
- `SOURCE_TABLE_INVENTORY.json`: 取得原本とreceiptをファイル単位でhash・bytes・構造まで棚卸し。
- `SOURCE_DISPOSITION.csv`: 79行。WPPの57行は57地域IDと一対一で、`Total Population, as of 1 July (thousands)`、`UN_WPP_POP_TOTAL`、採用55・原表未収録2を記録。
- `GEOGRAPHY_CROSSWALK.csv`: 57行。
- `PLANNING_LEGAL_INVENTORY.csv`: 57行。所在調査と採用済み資料を区別。
- 将来の2030 Censusはscheduled/identifiedとして記録し、結果を取得済み・利用可能とは表示しない。
- 原本は成果物の`raw/`と`evidence/`に保持し、公開用`site/`には置かない。

## 操作と表示

- ホームから大地域、国、取得済み国内地域へ進み、地域診断・テーマ診断・Database・Planningへ同じ選択を引き継ぐ。
- 市・県を選択後、同じ所属先の上位地域を再選択すると、下位選択を解除して上位全体へ即時に戻す。指標と期間は保持する。
- 南米テーマ診断は比較表と同じ16地域だけを比較母集団とし、地図にはそのうち境界をexact joinできた14地域だけを表示する。北米・中米・カリブの図形を混入させない。BVTとSGSは境界未結合の欠測行として表に残る。
- Planningの広域ページは、分析対象が確認済み法定計画主体ではないこと、57国別版完成ではないこと、国別法令・計画・予算・評価資料が未統合であることを英語・スペイン語・日本語で表示する。同じ警告をMarkdown/HTML出力にも各言語で保持する。
- 390px幅、キーボード地図操作、戻る／進む、共有、brand reset、404、consoleを確認する。

## 自動検証

- `npm run check`: JavaScript modules／JSON templatesの構文検査。
- `npm test`: 162/162合格。
- `node scripts/validate-americas-evidence.mjs --project <release>`: 57 WPP行、ID一意性、採用状態、1 July列、指標ID、将来Census表現を検証。
- `node scripts/validate-country.mjs --project <release>`: errors 0。国別planning資料未収集の警告1件は公開画面にも明示。
- `node scripts/verify-regional-delivery.mjs --project <release>`: 制作者確認と独立監査の証拠を照合。

## 独立監査で修正した事項

初回独立監査のREJECTを受け、次の4点を修正して全項目を再監査する。

1. WPP採否台帳の国ID欠落、1 Januaryという誤記、指標ID不一致を修正し、57件一対一検証を追加。
2. 南米テーマ比較の地図を比較母集団で絞り、対象外の全米図形を除外。
3. Planningの法的位置付け・完成範囲・資料未統合警告を英西日へ翻訳し、画面とMarkdown/HTMLへ適用。
4. 将来2030年のCensusを利用可能と読める表現から、予定・結果未取得の表現へ修正。

独立監査報告、出力照合、公開可否は最終成果物の`evidence/`に保存する。公開は独立監査が`ACCEPT`となり、publication gateが合格した版だけを対象にする。

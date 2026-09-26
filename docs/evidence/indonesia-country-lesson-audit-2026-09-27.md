# Indonesia country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/indonesia-areadata-20260927`。dataset SHA-256は `evidence/IDN_IMPORT_RESULT.json`。Windows/PowerShell、Node preview `127.0.0.1:4187`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | BPS公式人口目録5表のうちTable 1全国・34州ページを取得。取得35頁の3数値列・1,749セルを棚卸し。残り4表の本文・数値列は `priority_unassessed`。他テーマも未棚卸し。 |
| UA02 | 制約付き | 35 BPS HTMLと4目録/法令原本のhash固定。省令の表紙・定義/概略条項は確認。国勢調査全表と644頁法令全文は意味監査未完。 |
| UA03 | 制約付き | 2020 BPS国・州・県市のコード・親を照合。同名Bogor 2件を分離。現在のKemendagriコード・法定型・公式図形は未対照。 |
| UA04 | 制約付き | 全549地域×3列、男女合計、県市→州→全国を原表照合。州ページ重複合計102セルを再採用せず、WDI推計と区別。他指標は未監査。 |
| UA05 | 制約付き | 実画面の全国→Jawa Barat→Bogorを確認。全地域・他テーマ・狭画面・現地語は未実施。 |
| UA06 | 制約付き | Bogor `3201`の後に同じJawa Barat全体を階層selectorで再選択し、見出し・URL・人口が州値へ切替。メモ保持は未確認。 |
| UA07 | 制約付き | 全国34、Aceh23、DKI6、Jawa Barat27、Papua29比較行の全件・初末・合計・印刷HTMLを照合。下部行注目の上部不変は未試験。 |
| UA08 | 制約付き | 2020同表の非重複人数を比較。親は直接観測値のみ。WDI別系列。現在のコード・境界へ過去値を自動移植しない。 |
| UA09 | 制約付き | 86/2017法令PDF取得。Jawa Barat RPJMD制定目録は所在確認、本文未取得につき州計画として画面添付しない。予算・執行・評価未取得。 |
| UA10 | 未実施 | 現行改正・州/県市の権限・様式・章立てと公定出力の対応を未監査。汎用出力は承認済み計画ではない。 |
| UA11 | 制約付き | 7例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・2020年・単位・URL・原表値を照合。Word/PDF、狭画面、全地方資料は未実施。 |
| UA12 | 制約付き | 取得→inventory/audit→import→validator→build→verifier、共有check/test合格。Kit feedback、独立監査、Hosting/Publicは別。 |

候補内の原本、全列inventory、数値audit、import result、output verificationが再開用証拠。**42件合格と報告しない。** 公式地理・型/図形、未取得表、地方計画/財政原本、利用条件を閉じる必要がある。

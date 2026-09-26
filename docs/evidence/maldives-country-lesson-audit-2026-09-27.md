# Maldives country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/maldives-areadata-20260927`。dataset SHA-256は `evidence/MDV_IMPORT_RESULT.json`。Windows/PowerShell、Node preview `127.0.0.1:4186`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | MBS公式目録の52番号表・6補助XLSX取得。全冊数値列の機械棚卸し。P4/P5/H2/H7/EC3/ED16選定列のみ意味監査、他52冊・未選定列 `priority_unassessed`。 |
| UA02 | 制約付き | 58 XLSXと計画/制度4原本をhash固定。Fonadhoo PDF表紙・目次を確認。全Dhivehi本文と他51冊の数値意味は未監査。 |
| UA03 | 制約付き | 国、Maale、20環礁相当、186行政島、9首都部分行、非行政島集計を型別で保持。2026 atoll council廃止を統計行へ転写せず、公式同年polygonなし。 |
| UA04 | 制約付き | 全国515,132人口、94,424世帯と親子を原表で照合。P5空欄1、島名差2×2表を保留。H7原区分・EC3 age15+・ED16 Maldivian age10+とWDIを分離。 |
| UA05 | 制約付き | 実画面の全国→L→Fonadhoo、全国と各代表地域の値・資料を確認。全島、全診断頁、狭画面、現地語は未実施。 |
| UA06 | 制約付き | 島選択後に同じLを階層selectorで再選択し、見出し・URL・値・資料がLへ即時切替。メモ保持は未確認。 |
| UA07 | 制約付き | 実出力の国内22、Maale9、HA14、L11比較行の初末・件数・合計・印刷HTML全行を照合。下部行注目の上部不変は未試験。 |
| UA08 | 制約付き | 同年同表の非重複人口を比較。H2/H7世帯母数を確認。WDIと混ぜず、EC3の島名差や欠測親値を補完しない。他指標の比較定義監査は続行。 |
| UA09 | 制約付き | 2026大統領府発表とFonadhoo計画本文取得。計画はFonadhooのみ表示。法文、承認、予算・支出・評価は未取得/未監査。 |
| UA10 | 未実施 | 現行制度・手引き・Council文書欄と公定様式の対応を未監査。汎用出力は承認済み計画でない。 |
| UA11 | 制約付き | ６例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・年・単位・URL・原表値を照合。Word/PDF、狭画面、全資料描画は未実施。 |
| UA12 | 制約付き | 取得→全冊inventory→選定audit→import→validator→build→verifier実施、共有check/test合格。Kit feedback、独立監査、Hosting/Publicは別。 |

候補内のacquisition、inventory、selected audit、import result、output verificationが再開用証拠。**42件合格と報告しない。** 法定地理・図形、未採用数値列、実際の計画・予算・支出・評価、利用条件を閉じる必要がある。

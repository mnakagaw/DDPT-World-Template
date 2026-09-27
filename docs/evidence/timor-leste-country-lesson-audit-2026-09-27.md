# Timor-Leste country lesson audit — 制作者側の部分確認

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/timor-leste-areadata-20260927`、dataset SHA-256 `9b5a0fb1f401e9cbfd53f77d0ff2e29efef170cf87efe6f75f7dc151714a36f9`。Windows/PowerShell、Node、Python 3（pypdf）、Poppler `pdftotext`、ローカルpreview `127.0.0.1:4277` とCodex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に対する**制作者側の部分確認**。対象コードcommitは後続TLS handoffに記録する。

| ID | 判定 | 根拠・不足 |
|---|---|---|
| UA01 | 制約付き | 公式PDF8原本hash固定。報告目次の33番号表を台帳化し、選定4.3/4.11/4.12の数値欄と全行を監査。他30表の列数と意味は `priority_unassessed`。国別事前台帳は未調査から開始し、共通sourceのavailabilityは未確認。 |
| UA02 | 制約付き | 2022報告Main Reportの集計行・年齢行を原PDFに照合。一括表の4.1/4.2が画像であることを確認し、下位表が存在しないと断定しない。Table 4.3男女欄と4.1画像の競合は未採用。 |
| UA03 | 制約付き | 全国＋14報告行を2023法の第一階層名へ対照。AtaúroとOe-Cusseを別類型として保持。公式コード/2022対応境界/下位post・suco照合がないため図形0件。2017年13件の参考図形は外す。 |
| UA04 | 制約付き | 11指標×15地域=165観測。直接135と算出30を区別し、各採用表の全国/地方和・行内算術を確認。全国人口1,341,737、Díli324,738。WDI年央推計は別指標。秘匿9年齢セルを逆算せず、全国を地方へ流用しない。 |
| UA05 | 制約付き | 全国、Díli（計画/予算）、Ataúro（特別類型/草案）、Baucau（男女競合）、Oecusse（特別行政区）の実出力を照合。画面では全国→Díli→Ataúro→全国で見出し・値・URL・資料を確認。狭幅、低帯域、現地利用者、全主要操作の対照は未実施。 |
| UA06 | 制約付き | Ataúroから全国を再選択して主値・見出し・URL・地域文書の解除を確認。二階層目のpost/sucoを作っていないため、市→県→同じ県再選択の固有操作は対象外。メモ/保存の全経路は未確認。 |
| UA07 | 制約付き | 全国の内部比較に第一階層14/14を表示、CSV154行（14×11指標）を確認。図形欠測時も全表を表示。比較行への注目操作、検索/スクロール全行の実印刷は未実施。 |
| UA08 | 制約付き | 2017年参考図形13件は2022年14地域へ結合しない。選択3表の2022値とWDI年次系列を分離。人口密度は原表公表値、割合は同一行の分子分母。過去年同一境界の比較は作成しない。 |
| UA09 | 制約付き | Díli PEDM本文、年間行動計画の予算見込US$19,502,642、Ataúro草案とそれぞれの手続を別資料として接続。画面と5計画HTMLで文書の地域限定を確認。閣議決議・実支出・公式評価は未取得/未確認として表示。 |
| UA10 | 未実施 | 市町村とAtaúroの制度手続の本文所在を確認したが、全章/様式・計画作成権限の現行適用、正式承認決議と各地域の必要出力欄は未監査。汎用計画出力を法定提出物とは扱わない。 |
| UA11 | 制約付き | 5地域の診断CSV/HTML/Markdown・計画HTML・根拠CSVの指標、期間、原表locator、地域と予算資料を照合。全国比較は初行Aileu・末行Viquequeを含む14×11行。Word/PDF、全頁印刷、狭幅視覚確認は未実施。 |
| UA12 | 制約付き | 8原本hash→import→validator 0 errors/warnings→build→原表対実出力verifierを再現。共有check/testは後続handoffの対象commitに記録。Kit独立取込、42件全件、Hosting/Publicは別。 |

全表台帳は候補 `evidence/TLS_PHC2022_AUDIT.json`、出力照合は `evidence/TLS_OUTPUT_VERIFICATION.json`。[原本監査](timor-leste-phc2022-source-audit-2026-09-27.md)が採否と未取得を説明する。Word/PDF出力は採用しておらず隔離renderer試験は対象外。**42件合格とは報告しない。独立完成監査 `ACCEPT` 前に公開しない。**

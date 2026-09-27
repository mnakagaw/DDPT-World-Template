# Myanmar country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/myanmar-areadata-20260927`、dataset SHA-256 `2af0ee9339b8dbc79c40e49a5272cc3d0c8b79a3f5a4ddcf93517622adc8cbe8`。Windows/PowerShell、Node 24、Python 3、ローカルpreview `127.0.0.1:4273` と Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす**制作者側の部分確認**であり、42シナリオ全件や独立監査ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | DOP Excel/本報告PDF/暫定PDF、MOI記事をhash固定。Excel全19 sheet、全数値列・17,081数値セルを機械的棚卸し。A-1とPDF 2表の15指標のみ採用。A-2～A-18は`priority_unassessed`。 |
| UA02 | 制約付き | A-1の12列で全国・15地域・各都市/農村小計と性別・構成内訳を照合し、PDF Tables 2.2/3.1と行別突合。暫定版との差58,571を別版として保留。 |
| UA03 | 制約付き | DOP15報告行を出典行IDで保持。2019 provider境界は14図形のため除去。2024公式コード、District/Township、計画管轄は未照合。 |
| UA04 | 制約付き | 全国＋15地域×15指標＝240観測。実査・統計的推計・合計・率の方法を分離。原表の完全小計を照合したが、親はPDF/Excelの直接値を使用、地域率を平均しない。 |
| UA05 | 制約付き | 全国、Chin、Yangon、Bago、Nay Pyi Tawの帳票を原値照合。ブラウザーでChin→Yangon→全国、地図なし代替と資料分離を確認。全テーマ、狭画面、低帯域/低性能、現地語未実施。 |
| UA06 | 制約付き | Yangon後に全国を実選択し、51,375,327、37.4%、見出し・URLへ戻ることを確認。地域別メモ保持と多階層上位再選択は国別データで未実施。 |
| UA07 | 制約付き | 出典付き明示15地域比較の推計率0～92.2%と15/15順位をブラウザー確認。Chin順位行に注目しても分析対象はMyanmarのまま。全国CSV・印刷HTMLの15×15行、値・locatorを照合。 |
| UA08 | 制約付き | 2024国勢調査とWDI2025を全国でも別表示。旧暫定値、2014、行政登録を混合しない。推計欄ダッシュのゼロ9件は算出来歴を表示。 |
| UA09 | 制約付き | MOI計画調整記事は全国参考、州・地域計画資料は0/15と表示。記事から承認済み計画・実績を作らない。 |
| UA10 | 未実施 | 現行法的権限、州・地域とTownshipの計画主体、現行本文・予算執行・公式評価・様式は未取得。 |
| UA11 | 制約付き | 5例の診断CSV/HTML/Markdown、計画HTML、根拠CSVを原表・地域・期間・出典で照合。Word/PDF、実印刷、狭幅、低性能、全言語の視覚検証は未実施。 |
| UA12 | 制約付き | hash固定→audit→import→validator/build→実出力verifierで候補を再現。共有check/test、Kit取込、独立監査、Hosting/Publicは別記録。 |

ブラウザーで検出した「明示比較集合なのに異なる行政種別として全件比較停止」を既存`docs/ANALYSIS_DATA_CONTRACT.md`へ合わせて修正。共有`tests/generate.test.mjs`は**設定なしでは停止、出典付き明示集合では比較**の双方を確認した。これは比較の契約実装の修正で、DOP報告行を同一の法定計画主体とみなすものではない。

**42件合格とは報告しない。** 他の2024表/州・地域別報告書、公式code/図形、法令・計画/財政原本、利用条件、現地語/端末、独立`ACCEPT`が残る。

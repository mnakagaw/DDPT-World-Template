# Afghanistan country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/afghanistan-areadata-20260927`。dataset SHA-256は候補の `evidence/AFG_IMPORT_RESULT.json`。Windows/PowerShell、Nodeローカルpreview `127.0.0.1:4205`、Codex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md` の12観点を採用。独立42シナリオ、現地受入、国別公開ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | NSIA PDFの76番号付き表を頁・見出し・数値列群で棚卸し。Table 4の1404三列のみ採用、ほか75表と旧年は未意味監査。全数値セル採用とは報告しない。 |
| UA02 | 制約付き | PDF hash固定、Table 4 pp31–32各行/9列を機械照合、p167 Table 76人口34行でクロスチェック。TLS相手認証と原本再取得、ほか表の意味監査が必要。 |
| UA03 | 制約付き | 34州名と親子、定住範囲を分離。PDF通番は公式コードでなく、2007 provider図形・都市計画地理との結合なし。 |
| UA04 | 制約付き | 全国3＋定住範囲/34州各3＝108直接値。女性＋男性、34州→定住、定住＋遊牧→全国が同表内で一致。WDIとNSIA、全国と定住を自動比較・集計しない。 |
| UA05 | 制約付き | ブラウザーで全国、定住範囲、Heratを選択。URL、見出し、WDI欠測、NSIA Herat 2,383,202、境界欠測を確認。7実出力例。全ページ・全州・狭画面は未実施。 |
| UA06 | 制約付き | Herat州→同じ所属の定住範囲「全体」を再選択し、Herat選択解除とURL/見出しを確認。メモ・保存の継続は未確認。 |
| UA07 | 制約付き | WDIは州で欠測、全国参考値として別表示。Table 4定住人口は全国根では欠測。全行表は34州と初末行・合計を出力で確認。下部行クリックと検索は未確認。 |
| UA08 | 制約付き | 2007 provider図形を除外し、地図は境界なしと表示。比較は定住34州のみ同年・同定義。Table 76世帯不一致やTable 2旧年差を指標に採らない。 |
| UA09 | 制約付き | Kabul市法令/古い計画、Herat**市**master plan発表、MoF国予算は所在地のみ。実際の州/市の計画・予算・執行・評価は未取得。 |
| UA10 | 未実施 | 当該行政型の現行権限・公式計画様式・計画本文が未取得。汎用HTMLを公式申請様式とはしない。 |
| UA11 | 制約付き | 7例の診断CSV/HTML/Markdown、計画HTML、根拠CSVを生成して値・原表頁/行/列と対象を照合。印刷HTMLの34行初末行/全件/総和を照合。PDF/Wordと狭画面は未確認。 |
| UA12 | 制約付き | Validator 0 errors/warnings、buildと実出力verifier。共有check/test、Kit feedback、独立監査、Hosting/Publicは各別管理。 |

原本の全表見出しは `AFG_NSIA1404_TABLE_INVENTORY.csv`、採用行と矛盾は `AFG_NSIA1404_AUDIT.json`（いずれもignored候補内）を参照。**42件合格とは報告しない。** PDF再取得、より細かな地方統計・公式コード・対応境界、現行の計画制度と地域資料、利用条件、独立監査が残る。

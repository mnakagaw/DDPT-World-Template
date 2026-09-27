# Cambodia country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/cambodia-areadata-20260927`、dataset SHA-256 `38537521a1e4bc749042d0d52bb7e967d44ff618555d14e4de5a99a82506447f`。14例の出力hash・初末行は候補の `evidence/KHM_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json` に記録。Windows/PowerShell、Node preview `127.0.0.1:49801`、Codex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立監査や42シナリオ完了ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | 304頁NIS PDFとNCDD HTMLをhash固定。25 P表の全1,922行×6数値列を棚卸し、選定表467列エントリ、P表11,532数値セルを記録。報告書の表見出し199出現は機械的抽出であり、他表全列・意味監査は未完。 |
| UA02 | 制約付き | Table 2.1.1全国/25州の男女総数、P表の通常世帯値、PT 01の世帯種別、10.2.1の全国世帯数を原頁照合。PT 01のハイフン8位置は0扱いせず、他の表・年の意味は未確認。 |
| UA03 | 制約付き | NISの25/202/1,646報告階層、`0314`印刷例外とNCDD裏付けを保持。概要204との差2行、法的地域型・全コード/境界版・公式polygonは未解決。 |
| UA04 | 制約付き | NIS 9指標・11,301直接観測。全国全人口15,552,211と通常世帯人口15,184,511を分離。親子28フィールド不一致と保留3郡を記録し、親を子の不完全合計で補填しない。他分野未監査。 |
| UA05 | 制約付き | 全国、Banteay Meanchey、Mongkol Borei、下位Commune、誤値地点、Phnom Penh等14例を出力照合。ブラウザーで地域診断と計画資料、地図なし代替を確認。テーマ診断全域・狭画面は未実施。 |
| UA06 | 制約付き | ブラウザーで全国→Banteay Meanchey→Mongkol Borei→同じBanteay Meanchey全体をselector再選択。見出し、URL、対象が即時に戻り、Mongkol Borei見出しは残らない。メモ保持は未確認。 |
| UA07 | 制約付き | 郡Mongkol Boreiの全人口指標は欠測で全国参考を明示。14例の内部比較で全構成ID・初末行・件数を照合。下部行への注目が上部対象を保持する実操作と全件印刷は未実施。 |
| UA08 | 制約付き | 全人口と通常世帯、WDI推計、都市/農村、4統計Regionを別系列・別範囲に置く。率・世帯規模を単純加算しない。全テーマ・時系列比較は未検証。 |
| UA09 | 制約付き | NCDDの法令/手引き公式目録を `link_verified`・制度 `unverified` と表示。州の計画ページは全資料区分で未収集と記し、国参考を別枠に表示。本文403、現行効力、地方資料・実績は未確認。 |
| UA10 | 未実施 | 地方の現行法令・手引き本文、適用主体、公式様式の章/欄との対応が未確認。汎用計画基礎資料を承認済み計画にしない。 |
| UA11 | 制約付き | 14例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・年・値・PDF頁/URLと全比較行を照合。Word/PDFと実プリンターでの長表全行は未実施。 |
| UA12 | 制約付き | 固定原本hash→audit→import→validator/build→actual-output verifierで再生成。`npm run check` 158、`npm test` 218/218合格。Kit転記、独立監査、Hosting/Publicは別ゲート。 |

候補内に原本、選定表の列台帳、1,848詳細行・74小計行監査、例外、import結果、出力hashを保存した。**42件合格とは報告しない。** 他の国勢調査表、公式対応図形、法令/計画本文、財政実績、利用条件と独立`ACCEPT`が残る。

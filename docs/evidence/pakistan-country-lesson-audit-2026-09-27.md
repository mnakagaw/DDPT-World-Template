# Pakistan country lesson audit — producer-side partial check

2026-09-27 JST、branch`codex/asia-domestic-20260926`、ignored候補`generated/pakistan-areadata-20260927`。dataset SHA-256は候補の`evidence/PAK_IMPORT_RESULT.json`で固定する。Windows/PowerShell、Python 3.14、Node 24、ローカルNode preview `127.0.0.1:4204`、Codex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`に対応する制作者検査であり、42シナリオの独立`ACCEPT`ではない。Pakistanの地方政府実務者による受入なし。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | PBS公式Excel目録33番号付き表・305リンクを棚卸し。Table 1の6 XLSX、11数値列・737報告単位・19,899数値セルを全件走査。Table 10 KPの誤リンクを記録。他32表本文と優先下位表は未取得。 |
| UA02 | 制約付き | 7保存原本をhash固定、receipt・Sheet1セルlocator保持。3,684都市農村、2,210男女等、15全国、75地区→地域、75ファイル間の一致。Topi TehsilのC474誤セルは採用保留。取得原本の全数値を意味的に承認したわけではない。 |
| UA03 | 制約付き | 4州＋ICTの原表対象を国根から分離し、136地区の親子を原表順で識別。地区行に公式コードなし。Census District code、行政District、現在の地方政府、公式polygonは未照合。 |
| UA04 | 制約付き | 6人数指標×141統計対象=846直接観測。4州・136地区と全国Table 1対象の同年・同表を5完全比較集合で使用。AJK/GBを含む値と主張せず、WDI年央推計と混ぜない。Table 4以降の詳細母集団も混ぜない。 |
| UA05 | 制約付き | ブラウザーのテーマ診断でPakistan WDI初期値→Table 1対象→KP/Bajaurを選択し、見出し・URL・値・原表セルの切替を確認。9例の実出力確認。全6指標・全136地区・5ページの網羅確認は未実施。 |
| UA06 | 制約付き | Bajaur都市0からKP州を選び直し、指標保持のまま6,131,296とC7へ切替。追加ズームなし。メモ/保存の継続や他の同一上位再選択経路は未実施。 |
| UA07 | 制約付き | Bajaur都市0、Lahore農村0を原表の観測値としてCSVに出力。欠測・未取得との区別確認。全行の検索・スクロールと他指標の欠測は未実施。 |
| UA08 | 制約付き | 2019 geoBoundaries provider ADM1形状を2023原表へ結合せず、地図は境界未取得の代替を表示。比較は原表親子完全被覆のみ。モバイル/印刷の目視は未実施。 |
| UA09 | 制約付き | 5行政範囲の地方政府法・KP Tehsil規則と連邦PSDP目録を所在地として確認。KP選択の計画画面でKP法令2件を参考として表示し、計画・予算・実施・評価4区分は未取得と表示。現行改正、実計画/予算原本、権限ID対応なし。 |
| UA10 | 未実施 | Pakistan固有の承認済み計画様式と実際の地方計画本文が未取得。汎用HTML/根拠CSVは調査資料であり公式様式ではない。 |
| UA11 | 制約付き | 9例の診断CSV/HTML/Markdown、計画HTML/根拠CSVを生成し、対象名、2023年、人、source cell、比較初末行・全行印刷HTMLを照合。PDF/Word、印刷UI、狭画面は未確認。 |
| UA12 | 制約付き | Validator 0 errors/warnings、build、実出力verifier、共有`npm run check`150 modules/templates、`npm test`218/218に合格。Kit feedback、独立監査、Hosting/Publicは別管理。 |

**42シナリオ合格とは報告しない。** 全表定義、コード・境界、現行法令と地区別計画・財政・評価、利用条件、現地語/端末、独立監査は未解決。総合判定は**部分ローカル候補・未公開**。

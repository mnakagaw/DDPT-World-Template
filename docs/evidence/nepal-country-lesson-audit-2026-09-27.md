# Nepal country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/nepal-areadata-20260927`。dataset SHA-256は候補内 `evidence/NPL_IMPORT_RESULT.json`。Windows/PowerShell、Node preview `127.0.0.1:4183`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照合した制作者確認。独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | 公式目録91件/州。取得28冊の３表群は全採用数値列と重複分母を棚卸し、識字７冊のF:Jを数値列数まで棚卸し。85 XLSX群/州と２報告/州は未取得。国勢調査全体の監査完了とはしない。 |
| UA02 | 制約付き | 28 XLSX、公式目録HTML/JS、コードXLS、４計画PDF/公開頁をhash固定。選択３表群の全行・全列整数値・男女計・カテゴリー計をチェック。識字の年齢/男女階層と残り報告付表は未意味監査。 |
| UA03 | 制約付き | ７州・77郡・753自治体・77施設行の型/親子を維持。2023コードは749名称一致・２軽微表記差・２未解決。施設行は非法定地理、provider polygon不採用。 |
| UA04 | 制約付き | 2021の19指標・16,230直接値、施設私的世帯1,155非該当。全国29,164,578人、施設239,098人。私的世帯6,660,841と全世帯6,666,937の差6,096は施設世帯。WDI/JMP等とは同一化せず率を作らない。 |
| UA05 | 制約付き | 全国、Koshi、Kathmandu郡/市/施設行、コード保留２自治体の８出力例。実画面は州→郡→市、上部対象/URL、計画資料を確認。全行政型・狭画面は未実施。 |
| UA06 | 制約付き | Kathmandu市を選んだ後、同じKathmandu郡を階層selectorで選び直し、市選択解除と見出し/URL/資料切替を確認。メモ保存継続は未実施。 |
| UA07 | 制約付き | WDI全国系列は市町村に複製せず、NSO原表の同年比較を使用。全国７行、Koshi14行、Kathmandu郡12行は出力初末/全件/和を確認。画面内検索・行への注目は未実施。 |
| UA08 | 制約付き | 2020 provider図形を除外。地図なし代替。2021原表の親・全子を直接比較し、不完全小計を親にしない。Ward統計・旧年比較は未取得。 |
| UA09 | 制約付き | NPC手引きとKathmandu市の計画・予算・前年度進捗PDFを取得し、対象市にだけ表示。市→郡で市資料が消えることを画面と計画HTMLで確認。承認、実支出、公式評価は未確認。 |
| UA10 | 未実施 | Local Government Operation Actの現行条文、NPC手引きの必要表、実際の市の全計画頁と出力様式の対応を未監査。一般HTMLを公的様式としない。 |
| UA11 | 制約付き | ８例の診断CSV/HTML/Markdown、計画HTML、根拠CSVの地域・2021年・値・セル出典を照合。全比較行を印刷HTMLで検査。PDF/Word作成と全ページ描画、狭画面は未実施。 |
| UA12 | 制約付き | 原本pin→inventory→import→validator→build→verifierを再現。共有check/test完了。Kit feedback、独立監査、Hosting/Publicは別管理。 |

候補内の `NPL_NSO2021_ACQUIRED_TABLE_INVENTORY.csv`、`NPL_NSO2021_AUDIT.json`、`NPL_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json`を参照。**42件合格と報告しない。** 対応境界・コード履歴、原本の残りの意味監査、計画制度と地域資料、現地利用、独立監査が残る。

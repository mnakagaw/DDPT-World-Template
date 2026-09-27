# Timor-Leste 国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、`TLS`。独立・ignored候補 `generated/timor-leste-areadata-20260927`。**公式国勢調査の地方統計とDíli/Ataúro資料の部分成果・未公開**。[原本監査](timor-leste-phc2022-source-audit-2026-09-27.md)と[Task Contract](timor-leste-task-contract-2026-09-27.md)を参照。

| 項目 | 確認した範囲 | 不足・次の行動 |
|---|---|---|
| 作業・納品 | AreaData `codex/asia-domestic-20260926`に取得・監査・importコード、公開可能な公式source所在を保存。原本・buildはignored候補。参照実装0.4、dataset schema 0.2。 | 独立`ACCEPT`、TLS専用Hosting/Public先、更新担当・利用条件は未設定。 |
| 目的・地域 | 全国と2022年国勢調査の第一階層14地域について、地域診断・テーマ比較・出典付きCSV/HTML/Markdown・資料表示を使う。 | 行政post/sucoの数値全欄、計画の内部診断粒度、正式な現行コードと2022年対応図形は未照合。 |
| 国内統計 | INETL 2022国勢調査Main Reportを取得。目次の番号表33件を登録し、4.3、4.11、4.12の3表の選定列を全国＋14地域に採用。11指標、135直接観測・30同一行からの算出率。 | 他30表は数値列・意味の審査待ち。4.1/4.2の行政post/suco表は画像でセル照合待ち。秘匿9セルを復元しない。 |
| 地理 | [Law 19/2023](https://www.mj.gov.tl/jornal/public/docs/2023/serie_1/SERIE_I_NO_45_D.pdf)の第一階層名と14の2022報告行を照合。2023法でAtaúroとOe-Cusseは特別な別類型。 | 正式コード・図形・2022→現行下位階層の対照なし。初期の2017年参照図形13件は外した。2023年の461 sucoと2022年報告の452 sucoを同一台帳に混ぜない。 |
| 計画・予算 | 市町村の2024年手続、Ataúroの2025年手続、Díliの2026–2030年計画・2026年年間行動計画、Ataúroの2026–2030年草案を取得。Díliの予算見込総額US$19,502,642を計画値としてのみ表示。 | 閣議承認決議、他地域の資料、実支出・実施・公式評価、全章の意味審査は未確認。 |
| 国際source | 初期WDI全国系列は年次・母集団が異なる参考系列として保持。 | HDX/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPORのTLS×年×テーマ×粒度は未調査。 |
| 利用条件 | 公式PDF8原本のbyte長・SHA-256を固定。Gitには大きなPDF原本を含めない。 | 国勢調査、官報、自治体PDFそれぞれの再配布条件を確認。 |

代表確認は全国、Díli（計画・予算）、Ataúro（特別類型・草案）、Baucau（原表の男女数競合）、Oecusse（特別行政区）。5地域の実出力と全国比較14地域×11指標を原PDFの選定セルに照合した。画面は全国→Díli→Ataúro→全国の切替と資料分離を確認。Word/PDF出力、全頁印刷、狭幅・低帯域、現地担当者、42シナリオ全件は未実施。全国値を地方へ配分しない。
